#!/usr/bin/env python3
"""Read-only QuickCup case registry and campaign CSV coverage check.

Run from any working directory:
    python3 analysis_tools/check_run_registry.py
    python3 analysis_tools/check_run_registry.py --require-consolidated

No solver invocation, file writes or cleanup.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "RUN_CASE_REGISTRY.csv"
CASES_DIR = ROOT / "cases_controlled_buoyancy"
CAMPAIGN = ROOT / "analysis_results" / "full_campaign_audit" / "case_metrics.csv"

VALID_STATES = {"PREPARED_NOT_RUN", "RUNNING", "FAILED", "RUN_VERIFIED"}
VALID_ANALYSIS = {"NOT_ANALYZED", "ANALYSIS_VERIFIED"}
VALID_COVERAGE = {"YES", "NO"}


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Missing CSV: {path.relative_to(ROOT)}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-consolidated",
        action="store_true",
        help="Fail when any fully verified case is absent from the historical campaign CSV.",
    )
    args = parser.parse_args()
    try:
        registry = csv_rows(REGISTRY)
        campaign = csv_rows(CAMPAIGN)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    errors: list[str] = []
    info: list[str] = []
    names = [row.get("case", "").strip() for row in registry]
    audited = [row.get("case", "").strip() for row in campaign]
    if not names or not audited or not all(names) or not all(audited):
        errors.append("Registry or campaign CSV has missing/empty case rows.")
    if len(names) != len(set(names)):
        errors.append("Duplicate case names in RUN_CASE_REGISTRY.csv.")
    if len(audited) != len(set(audited)):
        errors.append("Duplicate case names in case_metrics.csv.")
    case_set = set(names)
    audit_set = set(audited)
    disk_set = {p.name for p in CASES_DIR.iterdir() if p.is_dir()} if CASES_DIR.is_dir() else set()
    unregistered = sorted(disk_set - case_set)
    absent_dirs = sorted(case_set - disk_set)
    unregistered_csv = sorted(audit_set - case_set)
    if unregistered:
        errors.append("Case directories not in registry: " + ", ".join(unregistered))
    if absent_dirs:
        errors.append("Registry entries without case directories: " + ", ".join(absent_dirs))
    if unregistered_csv:
        errors.append("Audited cases missing from registry: " + ", ".join(unregistered_csv))

    verified: list[str] = []
    not_run: list[str] = []
    for row in registry:
        name = row.get("case", "").strip()
        state = row.get("run_status", "").strip()
        analysis = row.get("analysis_status", "").strip()
        coverage = row.get("in_full_campaign_audit", "").strip()
        if state not in VALID_STATES or analysis not in VALID_ANALYSIS or coverage not in VALID_COVERAGE:
            errors.append(f"{name}: invalid state/analysis/coverage field.")
        present = name in audit_set
        if (coverage == "YES") != present:
            errors.append(f"{name}: registry campaign-coverage flag disagrees with case_metrics.csv.")
        if state == "RUN_VERIFIED" and analysis == "ANALYSIS_VERIFIED":
            verified.append(name)
        else:
            not_run.append(name)
            if present:
                errors.append(f"{name}: not fully verified but included in campaign CSV.")
        evidence = row.get("evidence_file", "").strip()
        if evidence and not (ROOT / evidence).is_file():
            errors.append(f"{name}: evidence file not found: {evidence}")

    outside = sorted(set(verified) - audit_set)
    info.append(f"Case directories: {len(disk_set)}; registered: {len(names)}; fully verified: {len(verified)}.")
    info.append(f"Campaign CSV rows: {len(audited)}; verified cases absent from CSV: {len(outside)}.")
    if outside:
        info.append("Verified but outside historical campaign: " + ", ".join(outside))
    if not_run:
        info.append("Not fully verified: " + ", ".join(sorted(not_run)))
    for line in info:
        print(line)
    for line in errors:
        print("ERROR:", line)
    if args.require_consolidated and outside:
        print("ERROR: Strict full consolidation failed; missing verified cases:", ", ".join(outside))
        return 1
    if errors:
        return 1
    if outside:
        print("WARNING: Campaign CSV is a historical subset, not a full all-case consolidation.")
    else:
        print("PASS: Registry, case directories and campaign CSV coverage are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
