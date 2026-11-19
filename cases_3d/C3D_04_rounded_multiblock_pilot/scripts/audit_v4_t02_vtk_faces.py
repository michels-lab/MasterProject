#!/usr/bin/env python3
"""C3D-04 Caso A: read-only per-FACE VTK geometry audit of preserved V4/T02.

Decodes legacy VTK POLYDATA polygons (ASCII or big-endian BINARY) and reports
actual exported polygon centroids, NOT just vertex occurrence histograms.
Rechecks saved parent/metal/mold and reciprocal contact gates before reporting.
A checkMesh count >70deg and a VTK polygon count are different provenance:
only state they agree if numbers actually match. No remesh, checkMesh or CFD.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import struct
import tempfile
from collections import Counter
from pathlib import Path

from audit_v4_t02_nonorth import audit as verify_native, SOURCE_VTK
from diagnose_existing_defects import STATIONS_MM

DEFAULT_CASE = Path.home() / "OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02"
DEFAULT_OUTPUT = Path.home() / "OpenFOAM/C3D04_V4_T02_NONORTH_FACE_AUDIT_01"
MAX_POINTS = 2_000_000
MAX_POLYGONS = 2_000_000
MAX_CONNECTIVITY = 16_000_000


def next_nonempty_line(stream) -> bytes:
    while True:
        line = stream.readline()
        if not line:
            raise ValueError("Unexpected end of legacy VTK file")
        if line.strip():
            return line.strip()


def ascii_tokens(stream, total: int, label: str) -> list[str]:
    if total < 0 or total > MAX_CONNECTIVITY:
        raise ValueError(f"Excessive {label} token count")
    values: list[str] = []
    while len(values) < total:
        line = next_nonempty_line(stream)
        parts = line.decode("ascii").split()
        if len(values) + len(parts) > total:
            raise ValueError(f"Extra ASCII tokens in {label}; possible layout mismatch")
        values.extend(parts)
    return values


def polygons_from_flat(flat: list[int], count: int, npoints: int):
    cursor = 0
    faces: list[tuple[int, ...]] = []
    for index in range(count):
        if cursor >= len(flat):
            raise ValueError("Truncated polygon connectivity")
        n = flat[cursor]
        cursor += 1
        if n < 3 or n > 1000 or cursor + n > len(flat):
            raise ValueError(f"Invalid polygon size at record {index}: {n}")
        polygon = tuple(flat[cursor:cursor+n])
        cursor += n
        if any(i < 0 or i >= npoints for i in polygon):
            raise ValueError(f"Polygon references unknown point at record {index}")
        if len(set(polygon)) != len(polygon):
            raise ValueError(f"Polygon has repeated vertex at record {index}")
        faces.append(polygon)
    if cursor != len(flat):
        raise ValueError("Unexpected leftover polygon connectivity integers")
    return faces


def parse_legacy_polydata(path: Path):
    """Return (XYZ in m, face vertex indices) from standard legacy VTK."""
    with path.open("rb") as stream:
        if not stream.readline().lower().lstrip().startswith(b"# vtk datafile"):
            raise ValueError("Not a legacy VTK file")
        stream.readline()  # title
        mode = stream.readline().strip().upper()
        if mode not in (b"ASCII", b"BINARY"):
            raise ValueError(f"Unsupported legacy VTK encoding: {mode!r}")
        dataset = next_nonempty_line(stream)
        if dataset.upper() != b"DATASET POLYDATA":
            raise ValueError(f"Unsupported DATASET {dataset!r}: expected POLYDATA")
        header = next_nonempty_line(stream).split()
        if len(header) != 3 or header[0].upper() != b"POINTS":
            raise ValueError("Legacy VTK missing POINTS block")
        npoints = int(header[1])
        kind = header[2].lower()
        if not (0 < npoints <= MAX_POINTS) or kind not in (b"float", b"double"):
            raise ValueError("Invalid VTK points count or scalar type")
        ncoords = 3 * npoints
        if mode == b"ASCII":
            coord = [float(x) for x in ascii_tokens(stream, ncoords, "POINTS")]
        else:
            char = "f" if kind == b"float" else "d"
            width = 4 if kind == b"float" else 8
            data = stream.read(ncoords * width)
            if len(data) != ncoords * width:
                raise ValueError("Truncated binary POINTS")
            coord = list(struct.unpack(f">{ncoords}{char}", data))
        if not all(math.isfinite(x) for x in coord):
            raise ValueError("Nonfinite VTK point coordinate")
        points = [
            (coord[i], coord[i+1], coord[i+2])
            for i in range(0, ncoords, 3)
        ]
        while True:
            line = next_nonempty_line(stream)
            words = line.split()
            if words[0].upper() == b"POLYGONS":
                if len(words) != 3:
                    raise ValueError("Bad POLYGONS header")
                count, total = int(words[1]), int(words[2])
                break
            if words[0].upper() in (b"VERTICES", b"LINES", b"TRIANGLE_STRIPS",
                                   b"CELLS", b"OFFSETS", b"CONNECTIVITY",
                                   b"POINT_DATA", b"CELL_DATA"):
                raise ValueError(f"Unsupported face connectivity: {line!r}")
            raise ValueError(f"Unexpected VTK section after POINTS: {line!r}")
        if count < 1 or count > MAX_POLYGONS or total < count*4 or total > MAX_CONNECTIVITY:
            raise ValueError("Invalid VTK POLYGONS counts")
        if mode == b"ASCII":
            flat = [int(x) for x in ascii_tokens(stream, total, "POLYGONS")]
        else:
            data = stream.read(total*4)
            if len(data) != total*4:
                raise ValueError("Truncated binary POLYGONS")
            flat = list(struct.unpack(f">{total}i", data))
        return points, polygons_from_flat(flat, count, len(points))


def locate_y(y_mm: float) -> str:
    # A tiny float tolerance prevents an exact nominal station from being
    # classified into a previous interval because of binary rounding.
    j = bisect.bisect_right(STATIONS_MM, y_mm + 1e-7) - 1
    if j < 0 or j >= len(STATIONS_MM) - 1:
        if abs(y_mm - STATIONS_MM[-1]) <= 1e-7:
            j = len(STATIONS_MM) - 2
        else:
            return "OUTSIDE_STATIONS"
    return f"{STATIONS_MM[j]:.3f}..{STATIONS_MM[j+1]:.3f}_mm"


def summarize_export(path: Path, native_count: int | None):
    points, faces = parse_legacy_polydata(path)
    buckets = Counter()
    lo = [float("inf")]*3
    hi = [-float("inf")]*3
    samples = []
    for ids in faces:
        centroid = tuple(
            sum(points[i][axis] for i in ids) / len(ids)
            for axis in range(3)
        )
        if not all(math.isfinite(v) for v in centroid):
            raise ValueError("Nonfinite face centroid")
        for k in range(3):
            mm = 1000.0*centroid[k]
            lo[k] = min(lo[k], mm)
            hi[k] = max(hi[k], mm)
        buckets[locate_y(1000*centroid[1])] += 1
        if len(samples) < 8:
            samples.append([round(1000*x, 6) for x in centroid])
    if sum(buckets.values()) != len(faces):
        raise AssertionError("Face spatial bin total mismatch")
    return {
        "vtk_path": str(path),
        "vtk_point_count": len(points),
        "vtk_polygon_face_count": len(faces),
        "native_checkMesh_severe_faces_gt70deg": native_count,
        "vtk_polygon_count_equals_native_severe_count": (
            len(faces) == native_count if native_count is not None else None
        ),
        "vtk_minus_native_face_count": (
            len(faces)-native_count if native_count is not None else None
        ),
        "centroid_XYZ_min_mm": lo,
        "centroid_XYZ_max_mm": hi,
        "centroid_Y_face_count_by_station_mm": dict(sorted(buckets.items())),
        "first_eight_face_centroids_mm_for_debug": samples,
        "limitation": (
            "These are counts/centroids of polygons in the saved VTK export. "
            "They are not necessarily the full set of >70deg faces if the "
            "exporter selected a different subset; only actual equality is reported. "
            "Face angle per polygon is NOT supplied by this VTK decoder."
        ),
    }


def run(case: Path):
    evidence = verify_native(case)  # actual saved logs, patches, area
    regions = {}
    for name, q in evidence["regions"].items():
        vtk = case / SOURCE_VTK[name]
        n = q["severely_nonorthogonal_faces_above_70deg"]
        if not vtk.is_file():
            regions[name] = {
                "status": "VTK_NOT_PRESENT",
                "expected_path": str(vtk),
                "native_checkMesh_severe_faces_gt70deg": n,
            }
            continue
        regions[name] = {
            "status": "VTK_POLYDATA_PARSED",
            **summarize_export(vtk, n),
        }
    parent = evidence["regions"]["parent"]["severely_nonorthogonal_faces_above_70deg"]
    metal = evidence["regions"]["metal"]["severely_nonorthogonal_faces_above_70deg"]
    mold = evidence["regions"]["mold"]["severely_nonorthogonal_faces_above_70deg"]
    return {
        "case": str(case),
        "status": "READONLY_VTK_FACE_CENTROID_AUDIT_NOT_CFD",
        "parent_regional_contact_gates_from_saved_native_data": True,
        "native_nonorth_gt70deg_counts": {
            "parent": parent, "metal": metal, "mold": mold,
            "parent_minus_sum_of_regions": (
                parent-metal-mold
                if None not in (parent, metal, mold) else None
            ),
        },
        "warning_parent_vs_regions": (
            "The 64-face difference observed in saved logs is not explained "
            "by this VTK geometry summary. Do not attribute to a specific "
            "interface without identifying faces in parent and regions."
        ),
        "regions": regions,
        "no_recheckMesh_no_remesh_no_CFD": True,
    }


def self_test():
    with tempfile.TemporaryDirectory() as folder:
        directory = Path(folder)
        # Two polygons with face centroids in different basal Y bands.
        points = [
            (0., -.040, 0.), (.001, -.040, 0.), (0., -.0398, .001),
            (0., -.0395, .001), (.001, -.0395, .001),
        ]
        polygons = [(0,1,2), (2,3,4)]
        flat = [3,0,1,2, 3,2,3,4]
        head = "# vtk DataFile Version 3.0\nSynthetic\n"
        ascii_path = directory/"sample_ascii.vtk"
        ascii_path.write_text(
            head+"ASCII\nDATASET POLYDATA\nPOINTS 5 float\n"
            + " ".join(str(x) for p in points for x in p)+"\n"
            + "POLYGONS 2 8\n"+" ".join(str(i) for i in flat)+"\n",
            encoding="ascii"
        )
        binary_path = directory/"sample_binary.vtk"
        binary_path.write_bytes(
            head.encode("ascii") + b"BINARY\nDATASET POLYDATA\nPOINTS 5 float\n"
            + struct.pack(">15f", *(x for p in points for x in p))
            + b"\nPOLYGONS 2 8\n" + struct.pack(">8i", *flat) + b"\n"
        )
        for path in (ascii_path, binary_path):
            vertices, got = parse_legacy_polydata(path)
            assert len(vertices) == 5 and got == polygons
            report = summarize_export(path, 2)
            assert report["vtk_polygon_face_count"] == 2
            assert report["vtk_polygon_count_equals_native_severe_count"] is True
            assert sum(report["centroid_Y_face_count_by_station_mm"].values()) == 2
            assert report["centroid_XYZ_min_mm"][1] >= -40.0
            mismatch = summarize_export(path, 3)
            assert mismatch["vtk_polygon_count_equals_native_severe_count"] is False
        invalid = directory/"invalid.vtk"
        invalid.write_text(
            head+"ASCII\nDATASET POLYDATA\nPOINTS 3 float\n"
            "0 0 0 1 0 0 0 1 0\nPOLYGONS 1 4\n3 0 1 10\n",
            encoding="ascii"
        )
        try:
            parse_legacy_polydata(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid VTK polygon vertex was accepted")
        assert locate_y(-39.800000000000004) == "-39.800..-39.500_mm"
    print("SELF_TEST_OK: ASCII/BINARY VTK face connectivity, centroid bins, count mismatch and malformed face rejection")
    print("STATIC_ONLY: no mesh or CFD utilities executed")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", type=Path, default=DEFAULT_CASE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    case = args.case.expanduser().resolve(strict=True)
    out_dir = args.out.expanduser()
    if out_dir.exists() or out_dir.is_symlink():
        ap.error(f"Preserving prior VTK-face audit, refusing overwrite: {out_dir}")
    result = run(case)
    out_dir.mkdir(parents=True, exist_ok=False)
    output = out_dir/"C3D04_V4_T02_VTK_FACE_CENTROIDS.json"
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    for region, record in result["regions"].items():
        if record["status"] != "VTK_POLYDATA_PARSED":
            print(f"{region.upper()}: {record['status']}")
        else:
            print(f"{region.upper()}: VTK polygons={record['vtk_polygon_face_count']}, "
                  f"native faces >70deg={record['native_checkMesh_severe_faces_gt70deg']}, "
                  f"counts_equal={record['vtk_polygon_count_equals_native_severe_count']}")
            print("  Y face centroid bands:", json.dumps(record["centroid_Y_face_count_by_station_mm"]))
            print("  centroid Y min/max [mm]:",
                  record["centroid_XYZ_min_mm"][1],
                  record["centroid_XYZ_max_mm"][1])
    print("Native parent/region/contact audit: RECONFIRMED FROM SAVED FILES")
    print(f"Read-only report created: {output}")
    print("Not a checkMesh rerun; no CFD; not a numerical-stability acceptance.")


if __name__ == "__main__":
    main()
