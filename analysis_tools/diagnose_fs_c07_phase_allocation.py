#!/usr/bin/env python3
"""Forensic, read-only audit of saved *native* FS-C07 metal/solid phase fields.

Reads all complete native time folders of one existing isolated FS-C07 run.
Does not execute OpenFOAM, modify the case, clip fields or call source models.
Prints maximum physical-allocation violations with offending cell indices.
No result is called physically accepted until constraints are verified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from audit_fs_c02_local import read_alpha
from stage_fs_c06_vof_solidification import (
    FLUID_CELLS, MODEL_FIELD, read_native_solid_fraction,
    read_native_metal_temperature,
)
from inspect_existing_fs_c07 import inspect, native_time_dirs

TOLERANCES = (1e-12, 1e-10, 1e-8)
LIQUIDUS_K_SCREEN_ONLY = 1473.0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify_allocation(metal: list[float], solid: list[float],
                        limit_examples: int = 3) -> dict:
    """No clipping: compare exact values against 0<=s<=metal<=1."""
    if not metal or len(metal) != len(solid):
        raise ValueError("Incomplete native metal/solid allocation")
    if any(not math.isfinite(v) for v in metal + solid):
        raise ValueError("Native field contains NaN or infinity")
    categories = ("metal_negative", "metal_above_1", "solid_negative",
                  "solid_above_metal")
    counts = {n: 0 for n in categories}
    worst = {n: {"overshoot": 0.0, "cell": None,
                  "metal": None, "solid": None} for n in categories}
    samples = {n: [] for n in categories}
    invalid_at_tolerances = {str(t): 0 for t in TOLERANCES}
    negative_solid_while_metal_negative = 0
    exact_invalid_cells = 0
    min_a, max_a, min_s, max_s = (
        min(metal), max(metal), min(solid), max(solid))
    for i, (a, s) in enumerate(zip(metal, solid)):
        vals = {
            "metal_negative": max(0.0, -a),
            "metal_above_1": max(0.0, a-1),
            "solid_negative": max(0.0, -s),
            "solid_above_metal": max(0.0, s-a),
        }
        for name, magnitude in vals.items():
            if magnitude > 0:
                counts[name] += 1
                if len(samples[name]) < limit_examples:
                    samples[name].append({"cell": i, "alpha_metal": a,
                                          "alpha_metal_solid": s,
                                          "violation": magnitude})
                if magnitude > worst[name]["overshoot"]:
                    worst[name] = {"overshoot": magnitude, "cell": i,
                                   "metal": a, "solid": s}
        actual_violation = max(vals.values())
        if actual_violation > 0:
            exact_invalid_cells += 1
        for tol in TOLERANCES:
            if actual_violation > tol:
                invalid_at_tolerances[str(tol)] += 1
        if a < 0 and s < 0:
            negative_solid_while_metal_negative += 1
    return {
        "cells": len(metal),
        "alpha_metal_min": min_a,
        "alpha_metal_max": max_a,
        "alpha_metal_solid_min": min_s,
        "alpha_metal_solid_max": max_s,
        "positive_solid_cell_count_exact": sum(v > 0 for v in solid),
        "max_physical_constraint_violation": max(
            v["overshoot"] for v in worst.values()),
        "strict_invalid_cells": exact_invalid_cells,
        "violating_cells_above_tolerance": invalid_at_tolerances,
        "count_by_constraint": counts,
        "worst_by_constraint": worst,
        "first_examples_by_constraint": samples,
        "native_fields_were_modified_or_clipped": False,
        "validation_pass_with_original_tolerance_1e-8":
            invalid_at_tolerances[str(1e-8)] == 0,
        "strict_0_le_s_le_a_le_1_pass": exact_invalid_cells == 0,
    }


def inspect_saved_phases(case: Path, max_examples: int = 3) -> dict:
    base = inspect(case)
    case = Path(base["case"])
    snapshots = []
    for t, p in native_time_dirs(case):
        if t <= 0:
            continue
        fluid = p / "fluid"
        inputs = {field: fluid / field
                  for field in ("alpha.metal", MODEL_FIELD, "T.metal")}
        if not all(path.is_file() for path in inputs.values()):
            continue
        metal = read_alpha(inputs["alpha.metal"], expected_cells=FLUID_CELLS)
        solid = read_native_solid_fraction(
            inputs[MODEL_FIELD], expected_cells=FLUID_CELLS)
        T = read_native_metal_temperature(
            inputs["T.metal"], expected_cells=FLUID_CELLS)
        result = classify_allocation(metal, solid, max_examples)
        core_T = [temp for alpha, temp in zip(metal, T) if alpha >= 0.5]
        result.update({
            "time_s": t,
            "metal_temperature_min_K_alpha_at_least_0p5":
                min(core_T) if core_T else None,
            "metal_temperature_max_K_alpha_at_least_0p5":
                max(core_T) if core_T else None,
            "metal_core_cells_below_C14_liquidus_count":
                sum(temp <= LIQUIDUS_K_SCREEN_ONLY
                    for alpha, temp in zip(metal, T) if alpha >= 0.5),
            "native_field_sha256": {name: sha256(path)
                                    for name, path in inputs.items()},
        })
        snapshots.append(result)
    if not snapshots:
        raise ValueError("No completed native FS-C07 phase field snapshots found")
    first_failed = next((s for s in snapshots
                         if not s["validation_pass_with_original_tolerance_1e-8"]),
                        None)
    final = snapshots[-1]
    return {
        "schema": "masterproject-fs-c07-native-phase-allocation-forensic-v1",
        "case": str(case),
        "solver_reached_time_s": base["latest_log_Time_s"],
        "solver_end_marker": base["solver_end_marker_in_recent_log_tail"],
        "previous_report_status": base["report_status"],
        "previous_report_last_error": base["report_last_error"],
        "complete_native_phase_snapshots_inspected": len(snapshots),
        "first_snapshot_failing_original_tolerance": (
            first_failed["time_s"] if first_failed else None),
        "final_snapshot_s": final["time_s"],
        "final_snapshot_max_constraint_violation":
            final["max_physical_constraint_violation"],
        "any_positive_solid_cells_in_saved_fields": any(
            s["positive_solid_cell_count_exact"] > 0 for s in snapshots),
        "any_core_metal_below_screen_liquidus": any(
            s["metal_core_cells_below_C14_liquidus_count"] > 0
            for s in snapshots),
        "all_snapshots_pass_original_tolerance": all(
            s["validation_pass_with_original_tolerance_1e-8"]
            for s in snapshots),
        "all_snapshots_pass_strict_allocation": all(
            s["strict_0_le_s_le_a_le_1_pass"] for s in snapshots),
        "native_snapshots": snapshots,
        "read_only": True,
        "postprocess_only": True,
        "no_solver_or_mesh_change": True,
        "C14_liquidus_K_screen_not_JMatPro": LIQUIDUS_K_SCREEN_ONLY,
        "global_mass_energy_conservation_accepted": False,
        "physical_volume_shrinkage_implemented": False,
        "feeding_implemented": False,
        "scientific_conclusion": (
            "Native solver finished; actual phase fields require numeric "
            "constraint assessment. Count/tolerance violations are printed "
            "without modifying saved fields. Positive solid or crossing here "
            "is raw-field evidence, not validation of physical shrinkage."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--examples", type=int, default=2)
    args = parser.parse_args()
    if not 0 <= args.examples <= 10:
        parser.error("--examples must be 0..10")
    try:
        result = inspect_saved_phases(args.case, args.examples)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as e:
        print("FS-C07 PHASE FORENSIC BLOCKED:", e, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
