#!/usr/bin/env python3
"""FS-C02: READ-ONLY thermal/VOF spatial diagnostic for existing 0.01s run.

Separate bulk-like gas (alpha.metal<=0.01), interface-like (0.01<alpha<0.99),
and bulk-like metal (alpha>=0.99). Thresholds are numerical diagnostics,
NOT physical interface thickness, solid fraction, or experimental validation.
No solver, mesh generation, file modification, or new CFD is performed.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from audit_fs_c02_local import (
    CELL_VOLUME, EXPECTED_CELLS, SCHEMA, digest, read_alpha, read_temperature,
    require,
)

ALPHA_LOW = .01
ALPHA_HIGH = .99
REFERENCE_END = .01


def mean(numbers: list[float]) -> float | None:
    return sum(numbers) / len(numbers) if numbers else None


def group_stats(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "cell_count": len(values),
        "temperature_mean_K": mean(values),
        "temperature_min_K": ordered[0] if ordered else None,
        "temperature_max_K": ordered[-1] if ordered else None,
        "temperature_median_K": ordered[len(ordered)//2] if ordered else None,
        "cells_over_500K": sum(t > 500 for t in values),
        "cells_over_1000K": sum(t > 1000 for t in values),
    }


def classify(alpha: list[float], temperature: list[float]) -> dict:
    require(len(alpha) == EXPECTED_CELLS
            and len(temperature) == EXPECTED_CELLS,
            "unexpected mesh/temperature/alpha cell counts")
    require(all(math.isfinite(a) and -1e-6 <= a <= 1+1e-6 for a in alpha),
            "nonfinite or unbounded alpha")
    require(all(math.isfinite(t) and t > 0 for t in temperature),
            "invalid temperature <= 0 K or nonfinite")
    # T is one mixture field per computational cell: values at interfaces
    # are not distinct thermodynamic gas and metal temperatures.
    pure_air = [t for a, t in zip(alpha, temperature) if a <= ALPHA_LOW]
    mixed = [t for a, t in zip(alpha, temperature)
             if ALPHA_LOW < a < ALPHA_HIGH]
    pure_metal = [t for a, t in zip(alpha, temperature) if a >= ALPHA_HIGH]
    require(len(pure_air) + len(mixed) + len(pure_metal) == EXPECTED_CELLS,
            "alpha partition does not cover full mesh")
    air_weight = sum(max(0, 1-a) for a in alpha)
    metal_weight = sum(max(0, a) for a in alpha)
    require(air_weight > 0 and metal_weight > 0, "no gas or metal")
    return {
        "alpha_metal_min": min(alpha),
        "alpha_metal_max": max(alpha),
        "volume_metal_from_alpha_m3": sum(alpha)*CELL_VOLUME,
        "alpha_strictly_between_zero_one_count":
            sum(0 < a < 1 for a in alpha),
        "gas_like_alpha_le_0_01": group_stats(pure_air),
        "interface_like_alpha_0_01_to_0_99": group_stats(mixed),
        "metal_like_alpha_ge_0_99": group_stats(pure_metal),
        "T_gas_weighted_mean_K": (
            sum((1-a)*t for a,t in zip(alpha, temperature)) / air_weight
        ),
        "T_metal_weighted_mean_K": (
            sum(a*t for a,t in zip(alpha, temperature)) / metal_weight
        ),
        "T_global_min_K": min(temperature),
        "T_global_max_K": max(temperature),
        "bulk_gas_mean_is_physical_gas_temperature": False,
        "interface_cell_T_represents_both_phase_temperatures": False,
    }


def snapshots(case: Path) -> list[tuple[float, Path]]:
    result = []
    for folder in case.iterdir():
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            t = float(folder.name)
        except ValueError:
            continue
        if math.isfinite(t) and 0 < t <= REFERENCE_END + 1e-6:
            result.append((t, folder))
    result.sort(key=lambda item: item[0])
    require(len(result) >= 3, "need >=3 saved positive-time snapshots")
    require(abs(result[-1][0] - REFERENCE_END) < 1e-5,
            "final snapshot must be 0.01s")
    require(all(a[0]<b[0] for a,b in zip(result,result[1:])),
            "repeated saved times")
    return result


def inspect(run: Path) -> dict:
    root = run.expanduser().resolve()
    case = root / "FS-C02"
    require(root.name.startswith("FS-C02_EXTENDED_") and
            case.is_dir() and not case.is_symlink(),
            "inspect only FS-C02_EXTENDED isolated run")
    statusfile = root / "FS-C02_RUN_STATUS.json"
    manifestfile = case / "FS-C02_MANIFEST.json"
    require(statusfile.is_file() and manifestfile.is_file()
            and not statusfile.is_symlink() and not manifestfile.is_symlink(),
            "case status/manifest missing")
    status = json.loads(statusfile.read_text())
    m = json.loads(manifestfile.read_text())
    require(status.get("case_id") == "FS-C02"
            and status.get("status") == "PROBE_COURANT_SCREEN_PASSED"
            and status.get("solver_tested_on_real_openfoam") is True
            and status.get("extended_probe") is True,
            "extended solver gate not completed")
    require(m.get("schema") == SCHEMA and
            m.get("execution_profile") == "EXTENDED_PROBE_0_01S_TIGHTER_CO"
            and m.get("physical_assumptions", {}).get("solidification") is False
            and m.get("physical_assumptions", {}).get("contraction") is False,
            "invalid or unknown scientific experiment")
    require(m.get("time_controls", {}).get("endTime_s") == REFERENCE_END,
            "unexpected endTime profile")
    manifest_input = m.get("generated_input_sha256", {})
    require(isinstance(manifest_input, dict) and len(manifest_input) == 20,
            "input SHA256 record must have 20 fields")
    for rel, sha in manifest_input.items():
        p = Path(rel)
        require(not p.is_absolute() and ".." not in p.parts
                and p.parts[0] in ("0", "constant", "system")
                and (case/p).is_file() and not (case/p).is_symlink(),
                "invalid solver input path")
        require(digest(case/p) == sha, "modified original solver input: "+rel)
    records = []
    for t, folder in snapshots(case):
        a = folder / "alpha.metal"
        temp = folder / "T"
        # Fail closed if the solver did not save a field: no fabricated data.
        data = classify(read_alpha(a), read_temperature(temp))
        records.append({"time_s": t, "alpha_sha256": digest(a),
                        "T_sha256": digest(temp), **data})
    end = records[-1]
    return {
        "schema": "masterproject-fs-c02-spatial-thermal-trace-v1",
        "status": "DIAGNOSTIC_RECORDED_PHYSICS_UNVERIFIED",
        "source_run": str(root),
        "source_manifest_sha256": digest(manifestfile),
        "snapshots_analyzed": len(records),
        "first_saved_time_s": records[0]["time_s"],
        "last_saved_time_s": records[-1]["time_s"],
        "class_definition":
            "gas-like alpha<=0.01; interface-like 0.01<alpha<0.99; metal-like alpha>=0.99",
        "initial_temperatures_from_manifest_only":
            {"metal_K": 1500, "air_K": 300},
        "final_gas_like_mean_T_K":
            end["gas_like_alpha_le_0_01"]["temperature_mean_K"],
        "final_interface_like_mean_T_K":
            end["interface_like_alpha_0_01_to_0_99"]["temperature_mean_K"],
        "final_metal_like_mean_T_K":
            end["metal_like_alpha_ge_0_99"]["temperature_mean_K"],
        "final_gas_weighted_mean_T_K": end["T_gas_weighted_mean_K"],
        "notes": [
            "Pure-like thresholds are classification choices, not interface thickness measurements",
            "T is a single cell-mixture field, not two thermodynamic phase temperatures",
            "No energy balance, phase mass-flux, solidification, or contraction validation",
            "Input is only original saved OpenFOAM fields; never rewrites case or run",
        ],
        "records": records,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = inspect(args.run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as ex:
        print("FS-C02 TRACE BLOCKED: "+str(ex), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
