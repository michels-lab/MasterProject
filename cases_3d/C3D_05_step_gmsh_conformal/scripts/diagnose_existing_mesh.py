#!/usr/bin/env python3
"""Read-only diagnosis of PRESERVED C3D-05 Gmsh/OpenFOAM 14 mesh evidence.

Never calls Gmsh, OpenFOAM, or a solver. Never modifies the original case,
STL/STEP files or logs. Prints the exact reasons for the existing Allmesh
checkMesh gate's YES/NO predicate; native geometry errors are distinguished
from reporting/parser mismatch. Optionally emits a NEW JSON report with 'x'.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CAD_VOLUME_M3 = {"metal": 4.7987697e-5, "mold": 1.02843333e-4}
IMPORTANT = re.compile(
    r"\*\*\*|\b(?:fail(?:ed|ure)?|error|illegal|invalid|negative|degenerate|"
    r"concav\w*|determinant\w*|orthogon\w*|skew\w*|volume\w*|face\s+tets|"
    r"region\w*|connected|disconnected|mesh\s+ok|severe|warning\w*|"
    r"tetra\w*|quality|aspect|flat|bad\w*|zero\s+area)\b",
    re.IGNORECASE,
)


def check_one(log: Path, region: str | None) -> dict:
    if not log.is_file():
        return {"path": str(log), "exists": False, "status": "LOG_MISSING"}
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    data = "\n".join(lines)
    counts = re.findall(r"(?m)^\s*cells:\s*(\d+)\s*$", data)
    volumes = re.findall(
        r"Total\s+volume\s*=\s*"
        r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)", data
    )
    matches = re.findall(r"Failed\s+(\d+)\s+mesh\s+checks?", data, re.I)
    connectivity = re.findall(r"Number\s+of\s+regions\s*:\s*(\d+)", data, re.I)
    mesh_ok = bool(re.search(r"\bMesh\s+OK\b", data))
    cells = int(counts[0]) if counts else None
    volume = float(volumes[0]) if volumes else None
    fail_checks = int(matches[-1]) if matches else None
    n_regions = int(connectivity[-1]) if connectivity else None
    accepted = {
        "native_mesh_OK_marker": mesh_ok,
        "native_failed_checks_not_positive": fail_checks in (None, 0),
    }
    if region is not None:
        ref = CAD_VOLUME_M3[region]
        accepted.update(
            {
                "cell_count_positive": cells is not None and cells > 0,
                "volume_present": volume is not None,
                "volume_within_CAD_2percent": volume is not None
                and abs(volume / ref - 1) <= 0.02,
                "one_connected_region_reported": n_regions == 1,
            }
        )
    critical = [
        {"line": i + 1, "message": line.strip()}
        for i, line in enumerate(lines)
        if IMPORTANT.search(line)
    ]
    return {
        "path": str(log),
        "exists": True,
        "status": "GATE_PASSED" if all(accepted.values()) else "GATE_REJECTED",
        "checks": accepted,
        "cells": cells,
        "total_volume_m3": volume,
        "cad_volume_m3": CAD_VOLUME_M3.get(region) if region else None,
        "volume_deviation_percent": (
            100 * (volume / CAD_VOLUME_M3[region] - 1)
            if region and volume is not None
            else None
        ),
        "failed_checks_reported": fail_checks,
        "connected_regions_reported": n_regions,
        "evidence_lines": critical[-90:],
        "final_lines": [
            {"line": max(1, len(lines) - 11) + i, "message": text}
            for i, text in enumerate(lines[-12:])
        ],
    }


def patch_summaries(path: Path) -> list[dict]:
    if not path.is_file():
        return [{"error": f"Boundary not found: {path}"}]
    text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for match in re.finditer(
        r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n\s*\{([^}]*)\}",
        text,
        re.S,
    ):
        name, contents = match.groups()
        def entry(field: str) -> str:
            found = re.search(r"\b" + re.escape(field) + r"\s+([^;\s]+)\s*;", contents)
            return found.group(1) if found else "-"
        rows.append(
            {
                "patch": name,
                "type": entry("type"),
                "nFaces": entry("nFaces"),
                "neighbourRegion": entry("neighbourRegion"),
                "neighbourPatch": entry("neighbourPatch"),
            }
        )
    return rows


def main() -> None:
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("case", type=Path, help="Preserved C3D-05 output (absolute path)")
    arg.add_argument("--json-out", type=Path, help="Optional NEW path for JSON report, never overwritten")
    args = arg.parse_args()
    case = args.case.expanduser().resolve()
    if not case.is_dir():
        arg.error(f"Missing mesh evidence directory: {case}")
    checks = {
        "parent": check_one(case / "log.checkMesh.parent", None),
        "metal": check_one(case / "log.checkMesh.metal", "metal"),
        "mold": check_one(case / "log.checkMesh.mold", "mold"),
    }
    report = {
        "case": str(case),
        "type": "POSTMORTEM_READ_ONLY_NO_CFD_NO_REMESH",
        "checks": checks,
        "patches": {
            region: patch_summaries(case / "constant" / region / "polyMesh" / "boundary")
            for region in ("metal", "mold")
        },
        "files": {
            name: (case / name).is_file()
            for name in (
                "log.gmsh3d", "log.gmshToFoam", "log.splitMeshRegions",
                "STEP_CAD_AUDIT.json", "CONTACT_AREA_REPORT.json",
                "PILOT_INTERFACE_REPORT.txt", "PILOT_MESH_REPORT.tsv",
            )
        },
    }
    print("C3D-05 PRESERVED MESH POSTMORTEM — NO CFD, NO RE-MESH")
    print(f"Output: {case}")
    for region, item in checks.items():
        print(f"\n=== {region.upper()}: {item['status']} ===")
        if not item.get("exists"):
            print(f"MISSING: {item['path']}")
            continue
        print(
            f"cells={item['cells']}, volume_m3={item['total_volume_m3']}, "
            f"regions={item['connected_regions_reported']}, "
            f"failed_mesh_checks={item['failed_checks_reported']}"
        )
        print("Exact gate predicates:")
        for criterion, value in item["checks"].items():
            print(f"  {'PASS' if value else 'FAIL'}: {criterion}")
        print("Relevant original log lines (last 90 matching):")
        for line in item["evidence_lines"]:
            print(f"  L{line['line']}: {line['message']}")
        print("Log tail:")
        for line in item["final_lines"]:
            print(f"  L{line['line']}: {line['message']}")
    print("\n=== PRESERVED REGIONAL PATCHES ===")
    for region, patches in report["patches"].items():
        print(region)
        for patch in patches:
            print("  " + " ".join(f"{k}={v}" for k, v in patch.items()))
    print("\n=== EVIDENCE PRESENT ===")
    for name, exists in report["files"].items():
        print(f"{name}: {'YES' if exists else 'NO'}")
    print("\nDo NOT classify the exact mesh failure until the log predicates and native diagnostics are read.")
    if args.json_out:
        destination = args.json_out.expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as out:
            json.dump(report, out, indent=2, ensure_ascii=False)
            out.write("\n")
        print(f"New non-overwriting report: {destination}")


if __name__ == "__main__":
    main()
