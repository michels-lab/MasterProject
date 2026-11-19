#!/usr/bin/env python3
"""Condensed report of one existing C3D-04 V4 trial, based on real checkMesh logs.

Read-only. Missing data are NA rather than invented successes. Called by the
single-shot sweep launcher after each isolated native Allmesh invocation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FIELDS = (
    "trial", "mode", "value", "runner_rc", "status",
    "parent_mesh_ok", "metal_mesh_ok", "mold_mesh_ok",
    "parent_under_cells", "metal_under_cells", "mold_high_skew_faces",
    "parent_max_nonorth_deg", "metal_max_nonorth_deg",
    "mold_max_nonorth_deg", "mold_max_skewness", "interface_area_mm2",
)


def first(pattern: str, text: str, default="NA"):
    result = re.search(pattern, text, flags=re.I)
    return result.group(1) if result else default


def extract(case: Path, trial: str, mode: str, value: str, rc: str):
    values = {
        "trial": trial, "mode": mode, "value": value,
        "runner_rc": rc,
    }
    status_file = case / "NATIVE_BUILD_STATUS.txt"
    status = status_file.read_text(errors="replace") if status_file.is_file() else ""
    values["status"] = first(
        r"(MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED|REJECTED|RUNNING|PREFLIGHT_COMPLETE)",
        status, default="MISSING",
    )
    for region in ("parent", "metal", "mold"):
        file = case / f"log.checkMesh.{region}"
        text = file.read_text(errors="replace") if file.is_file() else ""
        values[f"{region}_mesh_ok"] = (
            "YES" if re.search(r"\bMesh OK\b", text) and
            not re.search(r"Failed\s+[1-9]\d*\s+mesh\s+checks?", text, re.I)
            else ("NO" if text else "NA")
        )
        if region in ("parent", "metal"):
            values[f"{region}_under_cells"] = first(
                r"Cells with small determinant.*?number of cells:\s*(\d+)", text,
                default=("0" if "Cell determinant check OK" in text else "NA")
            )
        if region == "mold":
            values["mold_high_skew_faces"] = first(
                r"(\d+)\s+highly skew faces detected", text,
                default=("0" if "Max skewness" in text and
                         not re.search(r"highly skew", text, re.I) else "NA")
            )
            values["mold_max_skewness"] = first(
                r"Max skewness\s*=\s*([\d.eE+-]+)", text
            )
        values[f"{region}_max_nonorth_deg"] = first(
            r"Mesh non-orthogonality Max:\s*([\d.eE+-]+)", text
        )
    area_file = case / "CONTACT_AREA_REPORT.json"
    area = "NA"
    if area_file.is_file():
        try:
            data = json.loads(area_file.read_text(encoding="utf-8"))
            area = f"{data['metal_to_mold']['area_mm2']:.6f}"
        except (OSError, KeyError, ValueError, TypeError):
            pass
    if area == "NA":
        diag = case / "C3D04_V4_DIAGNOSTIC.txt"
        t = diag.read_text(errors="replace") if diag.is_file() else ""
        area = first(r"metal_to_mold:\s+\d+\s+faces,\s+([\d.]+)\s+mm2", t)
    values["interface_area_mm2"] = area
    return values


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case", nargs="?", type=Path)
    p.add_argument("--trial")
    p.add_argument("--mode")
    p.add_argument("--value")
    p.add_argument("--rc", default="NA")
    p.add_argument("--header", action="store_true")
    args = p.parse_args()
    if args.header:
        print("\t".join(FIELDS))
        return
    if not (args.case and args.trial and args.mode and args.value):
        p.error("case, --trial, --mode and --value are required")
    values = extract(args.case, args.trial, args.mode, args.value, args.rc)
    print("\t".join(str(values.get(k, "NA")) for k in FIELDS))


if __name__ == "__main__":
    main()
