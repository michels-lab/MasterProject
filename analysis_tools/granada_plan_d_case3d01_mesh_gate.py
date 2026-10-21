#!/usr/bin/env python3
"""PLAN D case3d-01: independent, read-only OpenFOAM14 3D mesh evidence gate.

The legacy input directory is C3D_01_metal_mold until overlapping PRs
are reconciled. It is NEVER edited by this tool. All measured quantities
require source files and all positive runtime claims require original logs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

CANONICAL_CASE_ID = "case3d-01"
LEGACY_SOURCE = Path("cases_3d/C3D_01_metal_mold")
EXPECTED_BASE_CELLS = 30276
EXPECTED_BOUNDS_M = ((-.003, -.069, -.003), (.055, .003, .055))
REQUIRED_REGIONS = ("metal", "mold")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(file):
    require(file.is_file() and not file.is_symlink(), f"source not a regular file: {file}")
    return hashlib.sha256(file.read_bytes()).hexdigest()


def raw_source(path, manifest, source_root):
    require(path.is_file() and not path.is_symlink(), f"missing input source: {path}")
    manifest.append({"path": path.relative_to(source_root).as_posix(), "sha256": digest(path)})
    return path.read_text(encoding="utf-8")


def mesh_background(dictionary, reference):
    # Static audit of the one-block mesh, not a substitute for blockMesh/checkMesh.
    require(re.search(r"\bunits\s*\[\s*mm\s*\]\s*;", dictionary) is not None,
            "source mesh must explicitly use Foundation14 units [mm]")
    require("convertToMeters" not in dictionary and "scale 0.001" not in dictionary,
            "double or ambiguous geometric scaling")
    clean = re.sub(r"/\*.*?\*/|//[^\n]*", "", dictionary, flags=re.S)
    block = re.search(r"\bvertices\s*\((.*?)\)\s*;", clean, re.S)
    require(block is not None, "missing vertices in blockMeshDict")
    triples = re.findall(r"\(\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s+([-+\d.eE]+)\s*\)", block.group(1))
    require(len(triples) == 8, "expected 8 vertices for one hexahedral box")
    vert = [tuple(float(x) for x in row) for row in triples]
    require(all(math.isfinite(x) for v in vert for x in v), "nonfinite mesh vertex")
    h = re.search(r"\bhex\s*\(\s*([0-7](?:\s+[0-7]){7})\s*\)\s*\(\s*(\d+)\s+(\d+)\s+(\d+)\s*\)", clean)
    require(h is not None, "missing or unsupported block cell decomposition")
    vi = [int(x) for x in h.group(1).split()]
    cells = tuple(int(x) for x in h.group(2, 3, 4))
    require(len(set(vi)) == 8 and min(cells) > 0, "bad vertex or cell indices")
    require(len(re.findall(r"\bhex\s*\(", clean)) == 1, "unexpected multiple mesh blocks")
    bounds = (
        tuple(min(p[i] for p in vert) / 1000 for i in range(3)),
        tuple(max(p[i] for p in vert) / 1000 for i in range(3)),
    )
    ref_bounds = (tuple(reference["background_mesh"]["bounds_min_m"]),
                  tuple(reference["background_mesh"]["bounds_max_m"]))
    for actual, declared, expected in zip((*bounds[0], *bounds[1]),
                                          (*ref_bounds[0], *ref_bounds[1]),
                                          (*EXPECTED_BOUNDS_M[0], *EXPECTED_BOUNDS_M[1])):
        require(math.isclose(actual, declared, abs_tol=1e-9)
                and math.isclose(actual, expected, abs_tol=1e-9),
                "blockMesh bounds differ from source geometry reference")
    require(list(cells) == reference["background_mesh"]["cells_nxyz"],
            "block mesh cell subdivision differs from reference")
    require(math.prod(cells) == EXPECTED_BASE_CELLS,
            "unexpected source background cell count")
    require(re.search(r"\bouterBox\s*\{[\s\S]*?\btype\s+patch\s*;", clean) is not None,
            "missing preliminary outerBox boundary")
    span = tuple(bounds[1][i] - bounds[0][i] for i in range(3))
    spacing = [1000*span[i]/cells[i] for i in range(3)]
    require(all(math.isclose(s, 2, abs_tol=1e-8) for s in spacing),
            "background spacing is not 2 mm")
    return {"bounds_m": [list(bounds[0]), list(bounds[1])],
            "cells_nxyz": list(cells), "total_background_cells": math.prod(cells),
            "spacing_mm": spacing,
            "status": "INPUT_GEOMETRY_CONSISTENT_NOT_CHECKMESH"}


def stl_metadata(reference, stl_dir, manifests):
    outcomes = {}
    boxvolume = math.prod(EXPECTED_BOUNDS_M[1][i] - EXPECTED_BOUNDS_M[0][i] for i in range(3))
    for region in REQUIRED_REGIONS:
        data = reference[region]
        expected = data["original_sha256"]
        require(isinstance(expected, str) and re.fullmatch(r"[a-f0-9]{64}", expected),
                f"{region}: missing valid SHA256 reference")
        lo, hi = data["bounds_m"]
        require(len(lo) == len(hi) == 3 and data["stl_volume_m3"] > 0,
                f"{region}: invalid bounding envelope/volume")
        for axis in range(3):
            require(EXPECTED_BOUNDS_M[0][axis] < lo[axis] < hi[axis] < EXPECTED_BOUNDS_M[1][axis],
                    f"{region}: STL bounds not inside background mesh")
        require(data["stl_volume_m3"] < boxvolume,
                f"{region}: reference STL volume exceeds background")
        filename = data["original_filename"]
        outcome = {"status": "PRIVATE_STL_NOT_PROVIDED", "expected_sha256": expected,
                   "reference_volume_m3": data["stl_volume_m3"],
                   "reference_triangle_count": data["triangle_count"],
                   "bounds_m": data["bounds_m"]}
        if stl_dir is not None:
            file = stl_dir / filename
            require(file.is_file() and not file.is_symlink(),
                    f"{region}: private STL not found: {file}")
            actual = digest(file)
            require(actual == expected, f"{region}: original SolidWorks STL SHA256 mismatch")
            manifests.append({"path": f"private-stl/{filename}", "sha256": actual})
            outcome["status"] = "SOURCE_BYTES_MATCH_REFERENCE_NOT_SURFACE_CHECKED"
        outcomes[region] = outcome
    require(reference["stl_original_units"] == "mm",
            "SolidWorks coordinate unit must remain native mm")
    require(reference["sampled_seed_points_m"]["metal"] != reference["sampled_seed_points_m"]["mold"],
            "the phase seed points cannot be identical")
    # Bounding-box checks are insufficient to establish whether a seed is
    # inside its complex STL. That must be checked with surfaceCheck/mesh.
    return outcomes


def parse_checkmesh_log(block_file, check_file):
    block = block_file.read_text(encoding="utf-8", errors="replace")
    check = check_file.read_text(encoding="utf-8", errors="replace")
    errors = []
    if re.search(r"FOAM FATAL ERROR|FOAM FATAL IO ERROR|Segmentation fault", block + check, re.I):
        errors.append("foam fatal error/segmentation found in supplied logs")
    if not re.search(r"(?m)^\s*End\s*$", block):
        errors.append("blockMesh log lacks normal End marker")
    if not re.search(r"(?m)^\s*Mesh OK\.\s*$", check):
        errors.append("checkMesh log lacks Mesh OK. marker")
    matches = re.findall(r"(?m)^\s*cells:\s*(\d+)\s*$", check)
    if not matches or int(matches[-1]) != EXPECTED_BASE_CELLS:
        errors.append("checkMesh reported cell count missing or wrong")
    bb = re.search(r"Overall domain bounding box\s*\(([^()]+)\)\s*\(([^()]+)\)", check)
    if bb is None:
        errors.append("checkMesh bounding box not observed")
    else:
        try:
            a = [float(x) for x in bb.group(1).split()]
            b = [float(x) for x in bb.group(2).split()]
            if len(a) != 3 or len(b) != 3 or any(
                not math.isfinite(v) or not math.isclose(v, expected, abs_tol=1e-6)
                for v, expected in zip(a + b, EXPECTED_BOUNDS_M[0] + EXPECTED_BOUNDS_M[1])
            ):
                errors.append("checkMesh reported wrong bounding box")
        except ValueError:
            errors.append("invalid checkMesh bounding box")
    return {"status": ("SUPPLIED_LOG_SCREEN_PASSED_NOT_INDEPENDENT_MESH_CHECK"
                       if not errors else "SUPPLIED_LOG_REVIEW"),
            "errors": errors, "screened_background_cells": EXPECTED_BASE_CELLS,
            "log_sha256": {"blockMesh": digest(block_file), "checkMesh": digest(check_file)}}


def nominal_refinement(reference):
    vols = {name: reference[name]["stl_volume_m3"] for name in REQUIRED_REGIONS}
    out = []
    for spacing_mm in (2.0, 1.0, 0.5, 0.25):
        vcell = (spacing_mm * .001)**3
        out.append({"nominal_cell_edge_mm": spacing_mm,
                    "ideal_uniform_volume_cells": {
                        n: math.ceil(vols[n] / vcell) for n in REQUIRED_REGIONS},
                    "combined_ideal_uniform_cells": math.ceil(sum(vols.values()) / vcell),
                    "limitations": "estimate only: excludes snapping, outside air, transition cells, interface, mesh quality"})
    return out


def inspect(root, stl_dir=None, log_blockmesh=None, log_checkmesh=None):
    case = root / LEGACY_SOURCE
    manifest = []
    reference = json.loads(raw_source(case/"geometry_reference.json", manifest, root))
    mesh_text = raw_source(case/"system/blockMeshDict", manifest, root)
    geometry = mesh_background(mesh_text, reference)
    private_stls = stl_metadata(reference, stl_dir, manifest)
    logs = {"status": "NOT_RUN_LOGS_NOT_SUPPLIED",
            "errors": ["OpenFOAM blockMesh/checkMesh original logs unavailable"]}
    if (log_blockmesh is None) != (log_checkmesh is None):
        raise ValueError("both blockMesh and checkMesh logs are required together")
    if log_blockmesh is not None:
        require(log_blockmesh.is_file() and log_checkmesh.is_file()
                and not log_blockmesh.is_symlink() and not log_checkmesh.is_symlink(),
                "supplied logs are missing or not regular files")
        logs = parse_checkmesh_log(log_blockmesh, log_checkmesh)
        manifest.extend([
            {"path": "supplied-logs/log.blockMesh", "sha256": digest(log_blockmesh)},
            {"path": "supplied-logs/log.checkMesh.background", "sha256": digest(log_checkmesh)},
        ])
    return {"schema": "quickcup-plan-d-case3d-01-mesh-gate-v1",
            "case_id": CANONICAL_CASE_ID,
            "source_directory_legacy_until_open_PRs_resolved": LEGACY_SOURCE.as_posix(),
            "no_OpenFOAM_commands_executed": True,
            "global_CFD_validation": "NOT_VALIDATED",
            "background_input": geometry,
            "private_stl_provenance": private_stls,
            "mesh_log_screen": logs,
            "nominal_resolution_options": nominal_refinement(reference),
            "mesh_resolution_decision": "OPEN_0.5MM_NOT_AUTOMATICALLY_APPROVED",
            "scientific_gates": {"interface_patches": "NOT_VALIDATED",
                                 "snappyHexMesh": "NOT_EXECUTED_BY_THIS_TOOL",
                                 "thermal_CHT": "NOT_VALIDATED",
                                 "JMatPro_J0": "OPEN", "experiment_G1": "OPEN"},
            "source_manifest": sorted(manifest, key=lambda x: x["path"])}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--stl-dir", type=Path, default=None)
    p.add_argument("--log-blockmesh", type=Path, default=None)
    p.add_argument("--log-checkmesh", type=Path, default=None)
    p.add_argument("--require-stls", action="store_true")
    p.add_argument("--require-mesh-logs", action="store_true")
    args = p.parse_args(argv)
    root, out = args.root.resolve(), args.out.resolve()
    require(not out.exists(), "refusing to overwrite existing output")
    require(out != root and root not in out.parents and out not in root.parents,
            "report output must be independent of source checkout")
    report = inspect(root, args.stl_dir, args.log_blockmesh, args.log_checkmesh)
    out.mkdir(parents=True)
    (out/"case3d-01-mesh-readiness.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    with (out/"case3d-01-nominal-resolution.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(("case_id", "nominal_cell_edge_mm", "metal_ideal_cells", "mold_ideal_cells",
                    "combined_ideal_cells", "status"))
        for x in report["nominal_resolution_options"]:
            n = x["ideal_uniform_volume_cells"]
            w.writerow((CANONICAL_CASE_ID, x["nominal_cell_edge_mm"],
                        n["metal"], n["mold"], x["combined_ideal_uniform_cells"],
                        "ESTIMATE_NOT_A_MESH_RESULT"))
    missing_stls = any(x["status"] == "PRIVATE_STL_NOT_PROVIDED"
                       for x in report["private_stl_provenance"].values())
    good_logs = report["mesh_log_screen"]["status"] == "SUPPLIED_LOG_SCREEN_PASSED_NOT_INDEPENDENT_MESH_CHECK"
    print(f"Plan D {CANONICAL_CASE_ID}: background input consistent; "
          f"private_STLs_missing={missing_stls}; supplied_mesh_log_screen_passed={good_logs}")
    print("No blockMesh/checkMesh/snappyHexMesh/CFD executed here; scientific validation OPEN")
    return int((args.require_stls and missing_stls) or (args.require_mesh_logs and not good_logs))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, json.JSONDecodeError, TypeError) as exc:
        raise SystemExit(f"ERROR: {exc}")
