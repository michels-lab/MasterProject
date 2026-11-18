#!/usr/bin/env python3
"""C3D-04 Caso A: inspect EXISTING Foundation 14 mesh evidence (read-only).

No blockMesh, checkMesh, OpenFOAM utilities, remeshing or CFD.
Uses actual log.checkMesh.* for counts and pre-existing legacy VTK files
for spatial *surface vertex* bounds, not counts/centroids of defective cells.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import math
import re
import struct
import sys
import tempfile

STATIONS_MM = (-65.5, -56.0, -40.0, -39.8, -39.5, -39.0, -38.5, -38.0, -20.0, 0.0)
TARGETS = ("underdetermined", "skewfaces", "nonorthofaces", "concavecells", "twoconnected", "twointernal")
MAX_VTK_POINTS = 2_000_000


def vtk_vertices(path: Path):
    """Yield XYZ from ASCII / big-endian BINARY legacy VTK POINTS arrays."""
    with path.open("rb") as f:
        if not f.readline().lower().lstrip().startswith(b"# vtk datafile"):
            raise ValueError("Not legacy VTK")
        f.readline()
        mode = f.readline().strip().upper()
        if mode not in (b"ASCII", b"BINARY"):
            raise ValueError("VTK mode must be ASCII or BINARY")
        # Dataset line and optional declarations before POINTS
        while True:
            line = f.readline()
            if not line:
                raise ValueError("VTK POINTS not found")
            m = re.match(rb"^\s*POINTS\s+(\d+)\s+(float|double)\s*$", line, re.I)
            if m:
                n = int(m.group(1))
                width = 4 if m.group(2).lower() == b"float" else 8
                break
        if not 0 < n <= MAX_VTK_POINTS:
            raise ValueError("Unexpected VTK point count")
        if mode == b"BINARY":
            raw = f.read(n * 3 * width)
            if len(raw) != n * 3 * width:
                raise ValueError("Truncated binary VTK points")
            fmt = ">fff" if width == 4 else ">ddd"
            for xyz in struct.iter_unpack(fmt, raw):
                if not all(math.isfinite(x) for x in xyz):
                    raise ValueError("Non-finite VTK coordinate")
                yield xyz
        else:
            # Small defective surface exports expected. Stop after n triplets;
            # do not read the subsequent POLYGONS/CELLS section as coordinates.
            items = []
            seen = 0
            for raw in f:
                items.extend(raw.decode("ascii").split())
                while len(items) >= 3 and seen < n:
                    xyz = tuple(float(x) for x in items[:3])
                    del items[:3]
                    if not all(math.isfinite(x) for x in xyz):
                        raise ValueError("Non-finite VTK coordinate")
                    seen += 1
                    yield xyz
                if seen >= n:
                    break
            if seen != n:
                raise ValueError("Truncated ASCII VTK points")


def vtk_summary(path: Path):
    lower = [float("inf")] * 3
    upper = [float("-inf")] * 3
    histogram = Counter()
    count = 0
    for p in vtk_vertices(path):
        count += 1
        for i, x in enumerate(p):
            lower[i] = min(lower[i], x * 1000.0)
            upper[i] = max(upper[i], x * 1000.0)
        y = p[1] * 1000.0
        slot = next(
            (i for i in range(len(STATIONS_MM) - 1)
             if STATIONS_MM[i] - 1e-7 <= y < STATIONS_MM[i + 1] - 1e-7),
            None,
        )
        if slot is None and abs(y - STATIONS_MM[-1]) <= 1e-7:
            slot = len(STATIONS_MM) - 2
        histogram["OUTSIDE" if slot is None else slot] += 1
    return {"count": count, "lower": lower, "upper": upper, "bins": histogram}


def log_summary(path: Path):
    if not path.is_file():
        return {"present": False}
    log = path.read_text(errors="replace")
    return {
        "present": True,
        "mesh_ok": bool(re.search(r"\bMesh OK\b", log)),
        "failed_checks": [
            int(n) for n in re.findall(r"Failed\s+(\d+)\s+mesh\s+checks?", log, re.I)
        ],
        "small_determinant_cells": [
            int(n) for n in re.findall(
                r"Cells with small determinant.*?number of cells:\s*(\d+)", log, re.I
            )
        ],
        "skew_faces": [
            int(n) for n in re.findall(r"(\d+)\s+highly skew faces detected", log, re.I)
        ],
        "max_non_orthogonality": [
            float(n) for n in re.findall(
                r"Mesh non-orthogonality Max:\s*([\d.eE+-]+)", log
            )
        ],
        "max_skewness": [
            float(n) for n in re.findall(r"Max skewness\s*=\s*([\d.eE+-]+)", log)
        ],
    }


def analyze(base: Path) -> int:
    for name in ("parent", "metal", "mold"):
        log = base / f"log.checkMesh.{name}"
        v = log_summary(log)
        print(f"\n=== {name.upper()} : existing checkMesh log ===")
        if not v["present"]:
            print("LOG MISSING:", log)
            continue
        for key, value in v.items():
            if key != "present":
                print(f"  {key}: {value}")
    print("\n=== EXISTING METAL/MOLD PATCH AREAS (read-only) ===")
    try:
        # Same area routine as Allmesh, without creating the report or
        # changing the preserved case, even though its quality gate failed.
        from measure_interface_area import (
            patch_area, CAD_CONTACT_MM2, CAD_TOP_MM2,
        )
        metal_area, nm = patch_area(base, "metal", "metal_to_mold")
        mold_area, nd = patch_area(base, "mold", "mold_to_metal")
        top_area, nt = patch_area(base, "metal", "metalTop")
        mismatch = 100 * abs(metal_area - mold_area) / max(metal_area, mold_area)
        contact_error = 100 * (metal_area * 1e6 / CAD_CONTACT_MM2 - 1)
        top_error = 100 * (top_area * 1e6 / CAD_TOP_MM2 - 1)
        print(f"  metal_to_mold: {nm} faces, {metal_area * 1e6:.6f} mm2")
        print(f"  mold_to_metal: {nd} faces, {mold_area * 1e6:.6f} mm2")
        print(f"  contact side mismatch: {mismatch:.6f} %")
        print(f"  contact error vs STL reference: {contact_error:+.6f} %")
        print(f"  metalTop: {nt} faces, {top_area * 1e6:.6f} mm2")
        print(f"  metalTop error vs STL reference: {top_error:+.6f} %")
        geometry_gate = (
            nm == nd == 2496 and mismatch <= 0.1
            and abs(contact_error) <= 3 and abs(top_error) <= 3
        )
        print("  area gate ONLY (not mesh quality):", "PASS" if geometry_gate else "FAIL")
    except (OSError, ValueError, IndexError, UnicodeDecodeError) as exc:
        print("  AREA NOT VERIFIED:", exc)
    print("\n=== EXISTING VTK DEFECT GEOMETRY (no utilities executed) ===")
    vtk = sorted(
        p for p in base.rglob("*")
        if p.is_file() and p.suffix.lower() == ".vtk"
        and any(x in p.stem.lower() for x in TARGETS)
    )
    if not vtk:
        print("No legacy VTK defect surfaces found in preserved case.")
        sets = sorted(p for p in base.rglob("*")
                      if p.is_file() and "sets" in p.parts
                      and any(x in p.name.lower() for x in TARGETS))
        for p in sets[:35]:
            print("  Existing native set:", p.relative_to(base))
        print("Cannot locate defects spatially without existing geometry exports.")
        return 2
    for p in vtk:
        print("\nVTK:", p.relative_to(base))
        print("Region identity is inferred ONLY when the directory path names it.")
        region = next((x for x in ("metal", "mold") if x in p.parts), "UNASSIGNED")
        print("  region indicated by path:", region)
        try:
            d = vtk_summary(p)
        except (OSError, ValueError, OverflowError, UnicodeDecodeError) as exc:
            print("  PARSE ERROR:", exc)
            continue
        print("  surface VERTICES (not bad cells):", d["count"])
        for j, axis in enumerate("XYZ"):
            print(f"  {axis} mm: {d['lower'][j]:.6f} .. {d['upper'][j]:.6f}")
        print("  Y section histogram of VERTICES:")
        for slot, n in sorted(d["bins"].items(), key=lambda it: str(it[0])):
            if slot == "OUTSIDE":
                print("    outside documented stations:", n)
            else:
                print(
                    f"    {STATIONS_MM[slot]:.3f} .. "
                    f"{STATIONS_MM[slot + 1]:.3f} mm : {n}"
                )
    print("\nThis report NEVER claims vertex counts are defective cell counts.")
    print("No changes to C3D-04, C14 or the preserved mesh were made.")
    return 0


def self_test() -> None:
    fixtures = (
        b"# vtk DataFile Version 3.0\nsynthetic\nASCII\nDATASET POLYDATA\n"
        b"POINTS 2 float\n0 -0.04 0\n0.01 -0.0395 0.01\nPOLYGONS 0 0\n",
        b"# vtk DataFile Version 3.0\nsynthetic\nBINARY\nDATASET POLYDATA\n"
        b"POINTS 2 float\n" + struct.pack(">ffffff", 0, -0.04, 0, 0.01, -0.0395, 0.01)
        + b"\nPOLYGONS 0 0\n",
    )
    with tempfile.TemporaryDirectory() as folder:
        for i, buf in enumerate(fixtures):
            p = Path(folder) / f"t{i}.vtk"
            p.write_bytes(buf)
            result = vtk_summary(p)
            assert result["count"] == 2
            assert abs(result["lower"][1] + 40.0) < 1e-5
            assert abs(result["upper"][1] + 39.5) < 1e-4
    print("SELF_TEST_OK: legacy ASCII and BINARY VTK points")


def main() -> int:
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument(
        "case", nargs="?", type=Path,
        default=Path.home() / "OpenFOAM/C3D04_ROUNDED_MULTIBLOCK_PILOT_01",
    )
    arg.add_argument("--self-test", action="store_true")
    args = arg.parse_args()
    if args.self_test:
        self_test()
        return 0
    case = args.case.expanduser().resolve()
    if not case.is_dir():
        arg.error(f"Preserved case not found: {case}")
    return analyze(case)


if __name__ == "__main__":
    sys.exit(main())
