#!/usr/bin/env python3
"""Read-only PRE-CFD evidence review of accepted C3D-05 CAD/HEX8 mesh.

Consumes ONLY saved native checkMesh logs, STEP_CAD_AUDIT.json, contact area,
regional patches and status. It does not call Gmsh, gmshToFoam, checkMesh or CFD.
Optional JSON is written exclusively with mode 'x' (no overwriting evidence).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA_METAL = "ea5f65796c5156e4931eaec29ff656c279120925ebc083767a16b80892d0f475"
SHA_MOLD = "fe126d23bb639196258551fd156591d7c9ece47016e8ad08a40c"
VOLUMES_M3 = {"metal": 4.7987697e-5, "mold": 1.02843333e-4}


def number(pattern: str, text: str, kind=float):
    m = re.search(pattern, text, re.I)
    # OpenFOAM often prints a sentence-ending period after numeric fields,
    # e.g. "Total volume = 4.7975e-05. Cell volumes OK.".
    # Strip punctuation but preserve a decimal point inside the number.
    return kind(m.group(1).rstrip(".")) if m else None


def native_quality(path: Path, region: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Missing native log: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    cells = number(r"(?m)^\s*cells:\s*(\d+)\s*$", text, int)
    conn = number(r"Number of regions:\s*(\d+)", text, int)
    vol = number(r"Total volume\s*=\s*([\d.eE+-]+)", text)
    determinant = number(r"Cell determinant \(wellposedness\)\s*:\s*minimum:\s*([\d.eE+-]+)", text)
    max_nonorth = number(r"Mesh non-orthogonality Max:\s*([\d.eE+-]+)", text)
    severe_faces = number(r"Number of severely non-orthogonal[^\n]*faces:\s*(\d+)", text, int)
    skew = number(r"Max skewness\s*=\s*([\d.eE+-]+)", text)
    mesh_ok = bool(re.search(r"(?m)^\s*Mesh OK\.\s*$", text))
    bad_checks = number(r"Failed\s+(\d+)\s+mesh checks", text, int)
    volume_error_pct = (
        100.0 * (vol / VOLUMES_M3[region] - 1)
        if region in VOLUMES_M3 and vol is not None else None
    )
    accepted = (
        mesh_ok and bad_checks in (None, 0) and cells is not None and cells > 0
        and conn == 1 and determinant is not None and determinant >= 0.001
        and vol is not None and vol > 0
        and (volume_error_pct is None or abs(volume_error_pct) <= 2.0)
    )
    if severe_faces is None:
        raise ValueError(f"Cannot read >70 degree nonorthogonality count from {path}")
    if max_nonorth is None or skew is None:
        raise ValueError(f"Cannot read quality metrics from {path}")
    return {
        "region": region,
        "cells": cells, "volume_m3": vol,
        "volume_error_percent": volume_error_pct,
        "connected_components": conn,
        "minimum_cell_determinant": determinant,
        "max_nonorthogonality_degrees": max_nonorth,
        "severely_nonorthogonal_faces_above_70deg": severe_faces,
        "max_skewness": skew,
        "native_checkMesh_OK": mesh_ok,
        "native_failed_checks": bad_checks,
        "native_mesh_gate_passed": accepted,
    }


def boundary_patch(path: Path, name: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Missing native boundary file: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"(?m)^\s*" + re.escape(name) + r"\s*\{([^}]*)\}", text, re.S)
    if m is None:
        raise ValueError(f"Patch {name} absent from {path}")
    def field(key: str):
        z = re.search(r"\b" + re.escape(key) + r"\s+([^;\s]+)\s*;", m.group(1))
        return z.group(1) if z else None
    return {"name": name, "type": field("type"), "nFaces": int(field("nFaces") or 0),
            "neighbourRegion": field("neighbourRegion"),
            "neighbourPatch": field("neighbourPatch")}


def assess(case: Path) -> dict:
    required = [
        "STEP_CAD_AUDIT.json", "CONTACT_AREA_REPORT.json",
        "PILOT_INTERFACE_REPORT.txt", "PILOT_MESH_REPORT.tsv",
        "log.gmsh3d", "log.gmshToFoam", "log.splitMeshRegions",
        "NATIVE_BUILD_STATUS.txt"
    ]
    missing = [name for name in required if not (case / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing preserved evidence in {case}: {missing}")
    cad = json.loads((case / "STEP_CAD_AUDIT.json").read_text(encoding="utf-8"))
    contact = json.loads((case / "CONTACT_AREA_REPORT.json").read_text(encoding="utf-8"))
    status = (case / "NATIVE_BUILD_STATUS.txt").read_text(encoding="utf-8")
    q = {region: native_quality(case / f"log.checkMesh.{region}", region)
         for region in ("parent", "metal", "mold")}
    metal_patch = boundary_patch(case / "constant/metal/polyMesh/boundary", "metal_to_mold")
    mold_patch = boundary_patch(case / "constant/mold/polyMesh/boundary", "mold_to_metal")
    top_patch = boundary_patch(case / "constant/metal/polyMesh/boundary", "metalTop")
    areametal = contact.get("metal_to_mold", {})
    areamold = contact.get("mold_to_metal", {})
    expected_topology = (
        cad.get("mesh_element_topology") == "HEX8_QUAD4_ONLY"
        and cad.get("subdivide_to_hex") is True
        and cad.get("algorithm_3d") == 1
        and cad.get("mesh_size_mm") == 3.6
        and cad.get("source", {}).get("metal_sha256") == SHA_METAL
        and cad.get("source", {}).get("mold_sha256") == SHA_MOLD
        and cad.get("post_subdivision_hex_count") == q["parent"]["cells"]
    )
    reciprocal = (
        metal_patch["type"] == "mappedWall" and mold_patch["type"] == "mappedWall"
        and metal_patch["neighbourRegion"] == "mold"
        and metal_patch["neighbourPatch"] == "mold_to_metal"
        and mold_patch["neighbourRegion"] == "metal"
        and mold_patch["neighbourPatch"] == "metal_to_mold"
        and metal_patch["nFaces"] == mold_patch["nFaces"] > 0
        and areametal.get("faces") == metal_patch["nFaces"]
        and areamold.get("faces") == mold_patch["nFaces"]
        and top_patch["type"] == "patch" and top_patch["nFaces"] > 0
    )
    area_gate = bool(
        contact.get("contact_gate") is True
        and contact.get("difference_between_coupled_sides_relative", 1) <= 0.001
        and abs(contact.get("contact_area_error_percent_vs_STL", 100)) <= 3.0
        and abs(contact.get("top_area_error_percent_vs_STL", 100)) <= 3.0
        and abs(areametal.get("area_mm2", 0) - areamold.get("area_mm2", 0)) < 1e-6
    )
    all_mesh_ok = all(v["native_mesh_gate_passed"] for v in q.values())
    combined_cells_ok = q["metal"]["cells"] + q["mold"]["cells"] == q["parent"]["cells"]
    saved_accepted = status.startswith("MESH_TOPOLOGY_AND_AREA_PRELIMINARILY_ACCEPTED")
    pass_topology = all([expected_topology, reciprocal, area_gate,
                         all_mesh_ok, combined_cells_ok, saved_accepted])
    severe = {region: item["severely_nonorthogonal_faces_above_70deg"]
              for region, item in q.items()}
    coherent_severe = severe["metal"] + severe["mold"] == severe["parent"]
    if not coherent_severe:
        pass_topology = False
    return {
        "case": str(case),
        "source": "PRESERVED_NATIVE_LOGS_AND_CAD_REPORTS_ONLY",
        "no_remesh_no_cfd": True,
        "quality": q,
        "checks": {
            "source_STEP_authentic_and_expected_hex8_topology": expected_topology,
            "native_mesh_OK_all_three": all_mesh_ok,
            "parent_region_cell_count_consistent": combined_cells_ok,
            "reciprocal_mappedWall_contact_faces": reciprocal,
            "contact_area_gate": area_gate,
            "native_runner_status_accepted": saved_accepted,
            "severe_nonorth_face_counts_consistent": coherent_severe,
        },
        "contact_faces_per_side": metal_patch["nFaces"],
        "contact_area_mm2_per_side": areametal.get("area_mm2"),
        "high_nonorthogonality_warning": severe["parent"] > 0,
        "risk_note": (
            f"{severe['parent']} native faces >70deg nonorthogonality "
            "(metal 595 / mold 1231 expected from first accepted run); "
            "checkMesh OK is NOT evidence of solver stability."
        ),
        "geometry_topology_gate_passed": pass_topology,
        "simulation_readiness": "NOT_EVALUATED_NO_3D_THERMAL_BCS_OR_SOLVER_RUN",
        "mesh_independence": "NOT_DEMONSTRATED_COARSE_3P6_MM_BASE",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--out", type=Path,
                    help="Optional new JSON evidence file (exclusive create, never overwrite)")
    a = ap.parse_args()
    case = a.case.expanduser().resolve()
    if not case.is_dir():
        ap.error(f"Case does not exist: {case}")
    result = assess(case)
    print("C3D-05 ACCEPTED CAD HEX8 REVIEW — ONLY SAVED EVIDENCE / NO CFD")
    for region, m in result["quality"].items():
        print(
            f"{region.upper()}: cells={m['cells']} native_OK={m['native_mesh_gate_passed']} "
            f"det_min={m['minimum_cell_determinant']} "
            f"nonorth_max={m['max_nonorthogonality_degrees']}deg "
            f"severe_nonorth_>70deg={m['severely_nonorthogonal_faces_above_70deg']}"
        )
    for key, passed in result["checks"].items():
        print(f"{'PASS' if passed else 'FAIL'}: {key}")
    print(f"OVERALL_GEOMETRY_TOPOLOGY: {'PASSED' if result['geometry_topology_gate_passed'] else 'NOT_PASSED'}")
    print("PHYSICS: NOT RUN | NO GRID INDEPENDENCE | HIGH NONORTHOGONALITY WARNING")
    if a.out is not None:
        path = a.out.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")
        print(f"New evidence written, never overwrites: {path}")
    if not result["geometry_topology_gate_passed"]:
        raise SystemExit("REJECTED: saved accepted mesh evidence failed independent review")


if __name__ == "__main__":
    main()
