#!/usr/bin/env python3
"""Read an existing FS-C07 WSL native run without running CFD or modifying files.

The caller must supply the exact *existing* isolated case. A preserved
incomplete report is evidence of an interrupted or failed runner, not proof
that the OpenFOAM solver itself failed. Distinguish explicit report last_error,
the saved native log and actual native saved time directories.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys


_TIME_RE = re.compile(
    r"(?m)^\s*Time\s*=\s*([0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)\s*s?\s*$"
)
_END_RE = re.compile(r"(?m)^\s*End\s*$")
_ERROR_RE = re.compile(
    r"(?:FOAM FATAL ERROR|FOAM FATAL IO ERROR|Floating point exception|"
    r"Segmentation fault|foamMultiRun returned|Traceback|Killed|"
    r"out of memory|No space left on device|Time limit exceeded)",
    re.I,
)


def read_tail(path: Path, max_bytes: int = 1_000_000) -> tuple[str, int]:
    with path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        return f.read().decode("utf-8", errors="replace"), size


def parse_times(text: str) -> list[float]:
    times = []
    for token in _TIME_RE.findall(text):
        val = float(token)
        if math.isfinite(val):
            times.append(val)
    return times


def native_time_dirs(case: Path) -> list[tuple[float, Path]]:
    result = []
    for p in case.iterdir():
        if not p.is_dir():
            continue
        try:
            t = float(p.name)
        except ValueError:
            continue
        if math.isfinite(t) and t >= 0:
            result.append((t, p))
    return sorted(result)


def inspect(case: Path) -> dict:
    case = case.expanduser().resolve()
    if not case.is_dir() or not case.name.startswith("FS_C07_THERMAL_"):
        raise ValueError("Must provide an existing FS_C07_THERMAL_* isolated case")
    report_path = case / "FS_C07_REPORT.json"
    if not report_path.is_file():
        raise ValueError("FS_C07_REPORT.json missing; preserve the case")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    log = case / "log.FS_C07_foamMultiRun"
    tail, log_bytes = read_tail(log) if log.is_file() else ("", 0)
    found_times = native_time_dirs(case)
    complete = []
    for t, p in found_times:
        if all((p / "fluid" / name).is_file()
               for name in ("alpha.metal", "alpha.metal.solid", "T.metal")):
            complete.append(t)
    latest_log_times = parse_times(tail)
    warnings = _ERROR_RE.findall(tail)
    selected_lines = [
        line.strip() for line in tail.splitlines()
        if ("FOAM FATAL" in line or "Error" in line or "error" in line
            or "ExecutionTime =" in line or "deltaT =" in line
            or line.lstrip().startswith("Time =")
            or "Segmentation fault" in line
            or "Floating point exception" in line)
    ]
    last_error = report.get("last_error")
    if not last_error:
        last_error = report.get("failure")
    return {
        "case": str(case),
        "report_status": report.get("status", "UNSPECIFIED"),
        "report_last_error": last_error,
        "native_cfd_executed_reported": report.get("native_cfd_executed", None),
        "log_file_exists": log.is_file(),
        "log_size_bytes": log_bytes,
        "solver_end_marker_in_recent_log_tail": bool(_END_RE.search(tail)),
        "latest_log_Time_s": latest_log_times[-1] if latest_log_times else None,
        "max_time_directory_s": found_times[-1][0] if found_times else None,
        "time_directories_count": len(found_times),
        "last_saved_complete_phase_fields_s":
            complete[-1] if complete else None,
        "complete_phase_field_directories_count": len(complete),
        "log_error_token_count_in_tail": len(warnings),
        "selected_recent_log_lines": selected_lines[-18:],
        "last_25_native_log_lines": tail.splitlines()[-25:],
        "interpretation": (
            "Report has last_error; inspect it with the native log to separate "
            "solver/runtime from postprocess failure."
            if last_error else
            "No explicit report last_error: native log and process state must "
            "be inspected before concluding completion or failure."
        ),
        "this_diagnostic_executed_solver": False,
        "this_diagnostic_modified_case": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="Existing absolute FS-C07 isolated case")
    args = parser.parse_args(argv)
    try:
        result = inspect(args.case)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("FS-C07 READ-ONLY DIAGNOSTIC BLOCKED:", exc, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
