#!/usr/bin/env python3
"""Read-only diagnosis of historical FS-C02 Courant spikes.

The closest preceding and following OpenFOAM 'Time = ...' markers bracket each
Courant log line; they are NOT proof that the Courant value belongs to either
exact timestamp. No results are changed and no CFD solver is launched.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
import json
import math
from pathlib import Path
import re
import sys

LOG_FILE = Path("logs/FS-C02_foamRun.log")
COURANT = re.compile(
    r"^Courant Number mean:\s*(\S+)\s+max:\s*(\S+)\s*$"
)
TIME = re.compile(r"^Time\s*=\s*([+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?)\s*s?\s*$")
DELTA_T = re.compile(r"^\s*deltaT\s*=\s*(\S+)\s*$")


def parse_numeric(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("FS-C02 Courant diagnosis: non-finite log value")
    return value


def diagnose_lines(lines: list[str], threshold: float = .25,
                   count: int = 5, context: int = 6) -> dict:
    if not (math.isfinite(threshold) and threshold > 0):
        raise ValueError("FS-C02: invalid threshold")
    if not (1 <= count <= 25 and 0 <= context <= 30):
        raise ValueError("FS-C02: invalid count or context")
    times: list[tuple[int, float]] = []
    steps: list[tuple[int, float]] = []
    events: list[dict] = []
    for index, line in enumerate(lines):
        if (m := TIME.match(line.strip())):
            try:
                times.append((index, parse_numeric(m.group(1))))
            except ValueError:
                continue
        if (m := DELTA_T.match(line.strip())):
            try:
                steps.append((index, parse_numeric(m.group(1))))
            except ValueError:
                continue
        if (m := COURANT.match(line.strip())):
            value = parse_numeric(m.group(2))
            if value < 0:
                raise ValueError("FS-C02: negative Courant max")
            events.append({"line": index, "courant_max": value,
                           "courant_mean": parse_numeric(m.group(1))})
    if not events:
        raise ValueError("FS-C02: no Courant Number measurements found")
    time_lines = [row[0] for row in times]
    step_lines = [row[0] for row in steps]
    spikes = sorted(events, key=lambda event: event["courant_max"], reverse=True)[:count]
    for event in spikes:
        lineno = event["line"]
        pos = bisect_left(time_lines, lineno)
        event["time_before_marker_s"] = times[pos-1][1] if pos else None
        event["time_after_marker_s"] = times[pos][1] if pos < len(times) else None
        step_pos = bisect_left(step_lines, lineno)
        event["deltaT_before_marker_s"] = steps[step_pos-1][1] if step_pos else None
        event["deltaT_after_marker_s"] = steps[step_pos][1] if step_pos < len(steps) else None
        event["line_number_1_based"] = lineno+1
        event["context_lines"] = [
            f"{i+1:>8}: {lines[i]}" for i in
            range(max(0, lineno-context), min(len(lines), lineno+context+1))
        ]
        del event["line"]
    maxima = [event["courant_max"] for event in events]
    return {
        "case_id": "FS-C02",
        "numerical_scope": "read-only historical solver log; not a solver rerun",
        "threshold": threshold,
        "courant_observations": len(events),
        "courant_global_max": max(maxima),
        "courant_last_max": maxima[-1],
        "observations_above_threshold": sum(v > threshold for v in maxima),
        "observations_above_one": sum(v > 1 for v in maxima),
        "observations_above_five": sum(v > 5 for v in maxima),
        "openfoam_time_note": (
            "Time markers before/after bracket a log observation, "
            "but neither is necessarily the exact corresponding time."
        ),
        "largest_spikes": spikes,
        "mass_interface_thermal_and_shrinkage_unverified": True,
    }


def diagnose(run: Path, threshold: float = .25, count: int = 5,
             context: int = 6) -> dict:
    run = run.expanduser().resolve()
    log = run / LOG_FILE
    if not (run.name.startswith("FS-C02_") and
            (run / "FS-C02").is_dir() and
            (run / "FS-C02_RUN_STATUS.json").is_file() and
            log.is_file() and not log.is_symlink()):
        raise ValueError("FS-C02: specify an existing FS-C02 run with original logs")
    status = json.loads((run / "FS-C02_RUN_STATUS.json").read_text())
    if status.get("case_id") != "FS-C02":
        raise ValueError("FS-C02: wrong case id")
    return diagnose_lines(log.read_text(encoding="utf-8", errors="replace").splitlines(),
                          threshold=threshold, count=count, context=context)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--context", type=int, default=6)
    parser.add_argument("--maxCo", type=float, default=.25)
    args = parser.parse_args(argv)
    try:
        report = diagnose(args.run, args.maxCo, args.limit, args.context)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
