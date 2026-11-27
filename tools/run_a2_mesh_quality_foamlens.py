#!/usr/bin/env python3
"""A2 interior-only mesh pilot + native OpenFOAM diagnostic views for FoamLens.
No solver. Preserve A and all previous mesh trials. Never select on Mesh OK alone.
"""
from pathlib import Path
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HOME = Path.home() / "OpenFOAM"
REPO = Path(__file__).resolve().parents[1]
A = REPO / "cases_3d/C3D_04_rounded_multiblock_pilot"
V4 = A / "candidates/C3D04_V4_TRANSITION_REPAIR"
sys.path.insert(0, str(A / "scripts"))
from audit_v4_t02_nonorth import audit, SOURCE_VTK
from audit_v4_t02_face_identity import read_native, map_vtk
from measure_interface_area import payload

BASE = HOME / "C3D04_V4_TRANSITION_REPAIR_01/T02"
SOURCE = HOME / "C3D04_V3_BASAL_SWEEP_01/T06/system/blockMeshDict"
REGIONS = ("metal", "mold")
TRIALS = [("A2Y08", .08), ("A2Y10", .10), ("A2Y14", .14), ("A2Y16", .16), ("A2Y18", .18), ("A2Y19", .19)]

def need(ok, message):
    if not ok:
        raise ValueError(message)

def labels(p):
    n, body = payload(p)
    vals = [int(x) for x in body.split()]
    need(len(vals) == n and all(v >= 0 for v in vals), "Invalid labels " + str(p))
    return vals

def patch_names(p):
    n, body = payload(p)
    names = re.findall(r"(?m)^\s*([^\s{};]+)\s*\n\s*\{", body)
    need(len(names) == n, "Boundary parse mismatch " + str(p))
    need(all(re.fullmatch(r"[A-Za-z0-9_.:-]+", x) for x in names), "Unsupported patch name")
    return names

def quality(case):
    evidence = audit(case)
    output = {}
    for region in REGIONS:
        q = evidence["regions"][region]
        maxangle = q["native_max_nonorthogonality_deg"]
        count = q["severely_nonorthogonal_faces_above_70deg"]
        if count is None and maxangle <= 70:
            count = 0
        need(count is not None, "Missing native severe-face count " + region)
        log = (case / ("log.checkMesh." + region)).read_text(errors="replace")
        def value(pattern):
            m = re.search(pattern, log, re.I)
            need(m is not None, "Missing quality metric " + region + " " + pattern)
            x = float(m[1])
            need(math.isfinite(x), "Nonfinite metric")
            return x
        output[region] = {
            "cells": q["native_cells"], "severe_faces": count,
            "max_nonorth_deg": maxangle,
            "min_determinant": q["native_min_determinant"],
            "max_aspect_ratio": value(r"Max aspect ratio\s*=\s*([\d.eE+-]+)"),
            "max_skewness": value(r"Max skewness\s*=\s*([\d.eE+-]+)")
        }
    return output

def cell_counts(owner, neighbour, face_ids, n):
    need(len(neighbour) <= len(owner), "Invalid neighbour list")
    need(set(owner + neighbour) == set(range(n)), "Cell labels not contiguous")
    counts = [0] * n
    for face in face_ids:
        need(0 <= face < len(owner), "Face outside mesh")
        counts[owner[face]] += 1
        if face < len(neighbour):
            counts[neighbour[face]] += 1
    return counts

def field(path, region, name, values, patches):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ('FoamFile\n{\n    version 2.0;\n    format ascii;\n'
              '    class volScalarField;\n    location "0/' + region + '";\n'
              '    object ' + name + ';\n}\n'
              'dimensions [0 0 0 0 0 0 0];\ninternalField nonuniform List<scalar>\n'
              + str(len(values)) + '\n(\n')
    boundary = '\n);\nboundaryField\n{\n'
    for patch in patches:
        boundary += '    ' + patch + '\n    {\n        type calculated;\n        value uniform 0;\n    }\n'
    path.write_text(header + '\n'.join(map(str, values)) + boundary + '}\n')

def export_view(case, target, q):
    target.mkdir()
    result = {}
    for region in REGIONS:
        idx, mesh = read_native(case, region)
        owner, neighbour = labels(mesh / "owner"), labels(mesh / "neighbour")
        need(len(owner) == len(idx.faces), "Owner/face count mismatch")
        expected = q[region]["severe_faces"]
        ids = map_vtk(idx, case / SOURCE_VTK[region], expected) if expected else set()
        counts = cell_counts(owner, neighbour, ids, q[region]["cells"])
        dst = target / "constant" / region / "polyMesh"
        dst.parent.mkdir(parents=True)
        shutil.copytree(mesh, dst)
        patches = patch_names(mesh / "boundary")
        for name, values in [("severeNonOrthoFaceCount", counts),
                             ("severeNonOrthoAdjacent", [int(v > 0) for v in counts])]:
            field(target / "0" / region / name, region, name, values, patches)
        result[region] = {"severe_faces": len(ids), "adjacent_cells": sum(v > 0 for v in counts),
                          "native_face_ids": sorted(ids)}
    (target / "case.foam").touch()
    (target / "QUALITY_VIEW.json").write_text(json.dumps({
        "source": str(case), "regions": result,
        "fields": {"severeNonOrthoFaceCount": "count of native >70 degree checkMesh faces incident to each cell",
                   "severeNonOrthoAdjacent": "1 if incident to any native severe face, otherwise 0"},
        "boundary_values": "placeholder zero for display; only internalField values meaningful",
        "physical_validation": False, "solver_ready": False, "not_a_CFD_case": True
    }, indent=2) + "\n")
    return result

def improved(base, candidate):
    lower = ("severe_faces", "max_nonorth_deg", "max_aspect_ratio", "max_skewness")
    not_worse = all(candidate[r][k] <= base[r][k] + 1e-9 for r in REGIONS for k in lower)
    not_worse &= all(candidate[r]["min_determinant"] >= base[r]["min_determinant"] - 1e-12 for r in REGIONS)
    better = any(candidate[r][k] < base[r][k] - 1e-9 for r in REGIONS for k in lower)
    better |= any(candidate[r]["min_determinant"] > base[r]["min_determinant"] + 1e-12 for r in REGIONS)
    return not_worse and better

def main():
    need(BASE.is_dir() and SOURCE.is_file(), "Missing preserved V4/T02 or V3/T06 on this WSL")
    subprocess.run(["bash", str(V4 / "tests/test_v4_static.sh")], check=True)
    assert cell_counts([0, 0, 1], [1], {0, 2}, 2) == [1, 2]
    baseline = quality(BASE)
    root = Path(tempfile.mkdtemp(prefix="C3D04_A2_QUALITY_", dir=HOME))
    views = root / "FoamLens"
    views.mkdir()
    summary = {"baseline": baseline, "trials": {}, "CFD_executed": False,
               "selection_policy": "No degradation in either region across listed native quality metrics; at least one improvement"}
    print("OUTPUT", root, flush=True)
    try:
        export_view(BASE, views / "A_original", baseline)
    except Exception as exc:
        summary["baseline_view_error"] = str(exc)
    for name, value in TRIALS:
        case = root / name
        env = {**os.environ, "C3D04_V4_OUT": str(case), "C3D04_V4_MODE": "inner_y",
               "C3D04_V4_VALUE": str(value), "C3D04_V4_BASE_DICT": str(SOURCE)}
        print("MESH", name, value, flush=True)
        with (root / ("log.runner." + name)).open("x") as log:
            rc = subprocess.run(["bash", str(V4 / "Allmesh")], env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        row = {"inner_y_mm": value, "native_rc": rc, "status": "REJECTED_OR_BLOCKED"}
        if rc == 0:
            try:
                q = quality(case)
                row.update(quality=q, status="NATIVE_GATE_PASS",
                           pareto_improvement_over_A=improved(baseline, q))
                try:
                    export_view(case, views / name, q)
                    row["foamlens_view"] = str(views / name)
                except Exception as exc:
                    row["view_error"] = str(exc)
            except Exception as exc:
                row["audit_error"] = str(exc)
        summary["trials"][name] = row
        print(json.dumps(row, indent=2), flush=True)
        (root / "A2_QUALITY_REPORT.json").write_text(json.dumps(summary, indent=2) + "\n")
    summary["eligible_candidates"] = [k for k,v in summary["trials"].items() if v.get("pareto_improvement_over_A")]
    (root / "A2_QUALITY_REPORT.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("FINAL", json.dumps(summary, indent=2))
    print("FoamLens views:", views)
    print("NO CFD; no automatic selection; original A preserved")

if __name__ == "__main__":
    main()
