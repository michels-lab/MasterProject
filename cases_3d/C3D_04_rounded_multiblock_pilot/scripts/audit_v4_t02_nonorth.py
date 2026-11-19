#!/usr/bin/env python3
"""C3D-04 Caso A: non-orthogonality review of PRESERVED accepted V4/T02.

Read-only native log inspection and pre-existing VTK spatial VERTEX extents.
No blockMesh, checkMesh, CFD, patch modification or threshold relaxation.
Passing the native gates does NOT demonstrate numerical stability or accuracy.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import tempfile
from pathlib import Path

from diagnose_existing_defects import vtk_summary, STATIONS_MM

EXPECTED_CELLS = {"parent": 21312, "metal": 8960, "mold": 12352}
CASE_DEFAULT = Path.home() / "OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02"
OUTPUT_DEFAULT = Path.home() / "OpenFOAM/C3D04_V4_T02_NONORTH_AUDIT_01"
SOURCE_VTK = {
    "parent": "postProcessing/checkMesh/constant/nonOrthoFaces.vtk",
    "metal": "postProcessing/metal/checkMesh/constant/nonOrthoFaces.vtk",
    "mold": "postProcessing/mold/checkMesh/constant/nonOrthoFaces.vtk",
}


def extract(pattern: str, text: str, convert=float):
    match = re.search(pattern, text, re.I | re.M)
    if not match:
        return None
    return convert(match.group(1).rstrip("."))


def parse_native(log: Path, region: str) -> dict:
    if not log.is_file():
        raise FileNotFoundError(f"Missing native evidence: {log}")
    body = log.read_text(encoding="utf-8", errors="replace")
    cells = extract(r"^\s*cells:\s*(\d+)\s*$", body, int)
    faces = extract(r"^\s*faces:\s*(\d+)\s*$", body, int)
    max_nonorth = extract(
        r"Mesh non-orthogonality Max:\s*([\d.eE+-]+)", body
    )
    severe = extract(
        r"Number of severely non-orthogonal[^\n]*faces:\s*(\d+)", body, int
    )
    min_det = extract(
        r"Cell determinant\s*\(wellposedness\)\s*:\s*minimum:\s*([\d.eE+-]+)",
        body
    )
    mesh_ok = bool(re.search(r"^\s*Mesh OK\.\s*$", body, re.M))
    failed = [int(n) for n in re.findall(
        r"Failed\s+(\d+)\s+mesh checks?", body, re.I
    )]
    if not mesh_ok or any(n > 0 for n in failed):
        raise ValueError(f"Native {region} mesh quality has NOT passed: {log}")
    if cells != EXPECTED_CELLS[region]:
        raise ValueError(f"Wrong {region} cell count {cells}; expected {EXPECTED_CELLS[region]}")
    if max_nonorth is None or min_det is None:
        raise ValueError(f"Native {region} quality metrics missing: {log}")
    if not all(math.isfinite(x) for x in (min_det, max_nonorth)):
        raise ValueError("Nonfinite native mesh quality metric")
    if min_det < 0.001:
        raise ValueError(f"{region} determinant minimum below native gate")
    if max_nonorth < 0 or max_nonorth > 180:
        raise ValueError("Unphysical non-orthogonality angle")
    if severe is not None and (severe < 0 or (faces is not None and severe > faces)):
        raise ValueError(f"Invalid severe face count in {region}")
    return {
        "native_mesh_ok_from_saved_log": True,
        "native_cells": cells,
        "native_total_faces": faces,
        "native_min_determinant": min_det,
        "native_max_nonorthogonality_deg": max_nonorth,
        "severely_nonorthogonal_faces_above_70deg": severe,
        "severe_fraction_of_all_faces_percent": (
            100.0 * severe / faces
            if severe is not None and faces is not None and faces > 0 else None
        ),
        "severity_count_verified_from_log": severe is not None,
    }


def verify_saved_contact(case: Path) -> dict:
    path = case / "CONTACT_AREA_REPORT.json"
    if not path.is_file():
        raise FileNotFoundError(f"Contact report missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    m = data.get("metal_to_mold", {})
    s = data.get("mold_to_metal", {})
    sides = data.get("difference_between_coupled_sides_relative")
    if not (
        data.get("contact_gate") is True
        and m.get("faces") == s.get("faces") == 2496
        and isinstance(sides, (int, float))
        and 0 <= sides <= 0.001
        and isinstance(data.get("contact_area_error_percent_vs_STL"), (int, float))
        and abs(data["contact_area_error_percent_vs_STL"]) <= 3
        and isinstance(data.get("top_area_error_percent_vs_STL"), (int, float))
        and abs(data["top_area_error_percent_vs_STL"]) <= 3
    ):
        raise ValueError("Saved metal/mold area gate is NOT accepted")
    status = (case / "NATIVE_BUILD_STATUS.txt")
    if not status.is_file() or not status.read_text(encoding="utf-8").startswith(
        "MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED"
    ):
        raise ValueError("Native V4 acceptance status missing or rejected")
    return {
        "accepted_contact_gate_from_saved_report": True,
        "faces_per_contact_side": 2496,
        "metal_to_mold_area_mm2": m.get("area_mm2"),
        "mold_to_metal_area_mm2": s.get("area_mm2"),
        "coupled_side_relative_mismatch": sides,
    }


def spatial_vtk(case: Path, region: str) -> dict:
    candidate = case / SOURCE_VTK[region]
    if not candidate.is_file():
        return {
            "vtk_present": False,
            "expected_path": str(candidate),
            "limitation": "No existing VTK: geometry location not known, no new utilities run",
        }
    report = vtk_summary(candidate)
    histogram = {}
    for k, n in sorted(report["bins"].items(), key=lambda item: str(item[0])):
        if k == "OUTSIDE":
            label = "OUTSIDE_DEFINED_Y_STATIONS"
        else:
            label = f"{STATIONS_MM[k]:.4f}..{STATIONS_MM[k+1]:.4f}_mm"
        histogram[label] = n
    return {
        "vtk_present": True,
        "path": str(candidate),
        "surface_vertex_occurrences": report["count"],
        "XYZ_min_mm": report["lower"],
        "XYZ_max_mm": report["upper"],
        "Y_section_histogram_of_vertex_occurrences": histogram,
        "critical_warning": (
            "VTK vertex occurrences are not distinct mesh faces, nor face "
            "centroids; severe FACE counts come only from native checkMesh logs"
        ),
    }


def audit(case: Path) -> dict:
    if not case.is_dir():
        raise FileNotFoundError(f"Case does not exist: {case}")
    contact = verify_saved_contact(case)
    quality = {}
    for region in EXPECTED_CELLS:
        quality[region] = {
            **parse_native(case / f"log.checkMesh.{region}", region),
            "existing_nonOrthoFaces_VTK": spatial_vtk(case, region),
        }
    if quality["metal"]["native_cells"] + quality["mold"]["native_cells"] != quality["parent"]["native_cells"]:
        raise ValueError("Native parent/regional cell counts inconsistent")
    return {
        "case": str(case),
        "status": "NATIVE_ACCEPTANCE_RECONFIRMED_READONLY_NONORTH_AUDIT_ONLY",
        "contact": contact,
        "regions": quality,
        "interpretation": (
            "All saved parent/regional and contact gates checked read-only. "
            "Severe face counts and max angles do NOT prove solver stability. "
            "No CFD, no mesh independence, no approved numerical scheme. "
            "Spatial VTK distribution reports vertex occurrences, never face counts."
        ),
        "no_remesh_no_checkMesh_no_CFD": True,
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        for region, count in EXPECTED_CELLS.items():
            content = (
                f"    cells: {count}\n"
                "    faces: 200000\n"
                "    Mesh non-orthogonality Max: 82.92036178 average: 25\n"
                "    *Number of severely non-orthogonal (> 70 degrees) faces: 26.\n"
                "    Cell determinant (wellposedness) : minimum: 0.001566024926\n"
                "    Max skewness = 2.84 OK.\nMesh OK.\n"
            )
            path = folder / f"log.checkMesh.{region}"
            path.write_text(content, encoding="utf-8")
            check = parse_native(path, region)
            assert check["severely_nonorthogonal_faces_above_70deg"] == 26
            assert check["native_mesh_ok_from_saved_log"]
            path.write_text(content.replace("Mesh OK.", "Failed 1 mesh checks."), encoding="utf-8")
            try:
                parse_native(path, region)
            except ValueError:
                pass
            else:
                raise AssertionError("Rejected mesh incorrectly passed")
        vtk = folder / "nonOrthoFaces.vtk"
        vtk.write_text(
            "# vtk DataFile Version 3.0\nSynthetic\nASCII\nDATASET POLYDATA\n"
            "POINTS 2 float\n0 -0.04 0\n0.01 -0.0398 0.01\nPOLYGONS 0 0\n",
            encoding="ascii"
        )
        assert vtk_summary(vtk)["count"] == 2
    print("SELF_TEST_OK: real checkMesh count patterns, failed-gate rejection, VTK spatial parser")
    print("STATIC_ONLY: no OpenFOAM or CFD executed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=CASE_DEFAULT)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    source = args.case.expanduser().resolve(strict=True)
    dest = args.output.expanduser()
    if dest.exists() or dest.is_symlink():
        parser.error(f"Preserving existing nonorth evidence: {dest}")
    report = audit(source)
    dest.mkdir(parents=True, exist_ok=False)
    out = dest / "C3D04_V4_T02_NONORTH_REPORT.json"
    with out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    for region, row in report["regions"].items():
        print(
            f"{region.upper()}: native Mesh OK, cells={row['native_cells']}, "
            f"nonorth_max={row['native_max_nonorthogonality_deg']}deg, "
            f"faces>70deg={row['severely_nonorthogonal_faces_above_70deg']}, "
            f"total_faces={row['native_total_faces']}, "
            f"VTK_vertex_spatial_info={'YES' if row['existing_nonOrthoFaces_VTK']['vtk_present'] else 'MISSING'}"
        )
        if row["existing_nonOrthoFaces_VTK"]["vtk_present"]:
            v = row["existing_nonOrthoFaces_VTK"]
            print("  VTK Y bounds mm:", v["XYZ_min_mm"][1], "..", v["XYZ_max_mm"][1])
            print("  Y bins (VERTEX occurrences only):",
                  json.dumps(v["Y_section_histogram_of_vertex_occurrences"]))
    print("CONTACT: passed saved strict reciprocal face/area gate")
    print("NUMERICAL STABILITY: UNVERIFIED / NO CFD / NO MESH INDEPENDENCE")
    print(f"Read-only evidence stored separately: {out}")


if __name__ == "__main__":
    main()
