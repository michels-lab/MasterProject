#!/usr/bin/env python3
"""Read-only native FS-C07 phase-volume diagnostic from 20 true saved snapshots.

Physically suspect alpha.metal.solid > alpha.metal MUST remain visible.
Calculate raw integrals and the signed/unphysical allocation residuals,
without modifying, clipping or "correcting" any OpenFOAM field.
This script does not accept shrinkage, feeding or conservation claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import read_mesh, cell_volume_m3
from stage_fs_c06_vof_solidification import (
    FLUID_CELLS, MODEL_FIELD, read_native_solid_fraction,
    read_native_metal_temperature,
)
from diagnose_fs_c07_phase_allocation import classify_allocation
from inspect_existing_fs_c07 import inspect, native_time_dirs


LIQUIDUS_SCREEN_K = 1473.0  # C14 numerical reference; not user's JMatPro


def sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or unsafe native field: " + str(path))
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for b in iter(lambda: inp.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def raw_phase_volume_diagnostics(
    volumes: list[float], metal: list[float], solid: list[float],
    T: list[float], liquidus_K: float = LIQUIDUS_SCREEN_K,
) -> dict:
    """Independent, non-clipped integrals; marked NOT physically accepted."""
    if not volumes or len(volumes) != len(metal) or len(metal) != len(solid) or len(solid) != len(T):
        raise ValueError("Mesh and native fluid fields must have matching nonzero cell counts")
    if not math.isfinite(liquidus_K) or liquidus_K <= 0:
        raise ValueError("Invalid screening liquidus")
    if any(not math.isfinite(v) or v <= 0 for v in volumes):
        raise ValueError("Nonpositive cell volume")
    if any(not math.isfinite(v) for v in metal + solid + T) or any(v <= 0 for v in T):
        raise ValueError("Nonfinite native phase data or invalid Kelvin field")

    v_metal = math.fsum(v * a for v, a in zip(volumes, metal))
    v_solid_raw = math.fsum(v * s for v, s in zip(volumes, solid))
    v_liquid_raw = math.fsum(v * (a-s) for v, a, s in zip(volumes, metal, solid))
    v_excess_solid_over_metal = math.fsum(
        v * max(s-a, 0.0) for v, a, s in zip(volumes, metal, solid))
    v_negative_solid = math.fsum(v * max(-s, 0.0) for v, s in zip(volumes, solid))
    v_negative_metal = math.fsum(v * max(-a, 0.0) for v, a in zip(volumes, metal))
    v_metal_over_one = math.fsum(v * max(a-1.0, 0.0)
                                for v, a in zip(volumes, metal))
    core = [(v, a, s, temp)
            for v, a, s, temp in zip(volumes, metal, solid, T)
            if a >= 0.5]
    below_liq = [(v, a, s, temp) for v, a, s, temp in core
                 if temp <= liquidus_K]
    liquidus_contact_volume = math.fsum(v*a for v, a, s, temp in below_liq)
    core_metal_volume = math.fsum(v*a for v, a, s, temp in core)
    max_solid_positive = max(solid)
    if v_metal <= 0:
        raise ValueError("Integrated native metal volume nonpositive")
    return {
        "native_raw_volIntegrate_alpha_metal_m3": v_metal,
        "native_raw_volIntegrate_alpha_metal_solid_m3": v_solid_raw,
        "native_raw_liquid_difference_m3": v_liquid_raw,
        "positive_solid_count_all_cells_including_traces":
            sum(s > 0 for s in solid),
        "native_solid_max_absolute_cell_volume_fraction": max_solid_positive,
        "core_metal_cells_alpha_at_least_0p5": len(core),
        "core_metal_temperature_min_K": min((t for _, _, _, t in core), default=None),
        "core_metal_temperature_max_K": max((t for _, _, _, t in core), default=None),
        "core_metal_cells_below_C14_screen_liquidus": len(below_liq),
        "core_metal_volume_below_screen_liquidus_m3": liquidus_contact_volume,
        "core_metal_volume_m3": core_metal_volume,
        "core_metal_fraction_below_screen_liquidus_by_alpha_volume":
            (liquidus_contact_volume/core_metal_volume
             if core_metal_volume > 0 else None),
        "core_metal_raw_solid_integral_m3": math.fsum(
            v*s for v, a, s, t in core),
        "raw_solid_over_raw_metal_ratio_diagnostic_only":
            v_solid_raw/v_metal,
        "positive_violation_volume_integral_solid_exceeds_metal_m3":
            v_excess_solid_over_metal,
        "relative_positive_violation_vs_raw_metal_volume":
            v_excess_solid_over_metal/v_metal,
        "negative_solid_volume_magnitude_m3": v_negative_solid,
        "negative_metal_volume_magnitude_m3": v_negative_metal,
        "metal_fraction_above_one_volume_magnitude_m3": v_metal_over_one,
        "raw_fields_clipped_or_modified": False,
        "raw_solid_integral_is_not_accepted_solid_volume": True,
        "mass_balance_or_shrinkage_verified": False,
    }


def load_native_vol_field_monitor(case: Path, name: str) -> list[tuple[float, float]]:
    """Optional independent Foundation14 volFieldValue .dat cross-check."""
    root = case / "postProcessing"
    if not root.is_dir():
        return []
    matches = sorted(p for p in root.rglob("volFieldValue.dat")
                     if name in p.parts and p.is_file() and not p.is_symlink())
    if not matches:
        return []
    if len(matches) > 1:
        raise ValueError("Multiple ambiguous native monitor files: " + name)
    rows = []
    for line in matches[0].read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split()
        if len(cols) != 2:
            raise ValueError("Expected time and one scalar in " + name)
        t, value = map(float, cols)
        if not math.isfinite(t) or not math.isfinite(value):
            raise ValueError("Nonfinite native volume monitor record " + name)
        rows.append((t, value))
    if not rows:
        raise ValueError("Monitor exists but has zero rows: " + name)
    return rows


def nearest_monitor_value(samples: list[tuple[float, float]], time_s: float,
                          tol_time: float = 2e-6) -> float | None:
    if not samples:
        return None
    t, value = min(samples, key=lambda row: abs(row[0]-time_s))
    return value if abs(t-time_s) <= tol_time else None


def evaluate(case: Path) -> dict:
    base = inspect(case)
    case = Path(base["case"])
    if base["solver_end_marker_in_recent_log_tail"] is not True or not math.isclose(
        base["latest_log_Time_s"] or -1, 1.0, abs_tol=1e-9
    ):
        raise ValueError("Native solver completion at 1 s not supported by log")

    # Mesh geometry is loaded once; no post-processing writes.
    mesh = read_mesh(case / "constant/fluid/polyMesh", FLUID_CELLS)
    volumes = [cell_volume_m3(mesh, celli) for celli in range(FLUID_CELLS)]
    initial = read_alpha(case / "0/fluid/alpha.metal", expected_cells=FLUID_CELLS)
    initial_volume = math.fsum(v*a for v, a in zip(volumes, initial))
    if initial_volume <= 0:
        raise ValueError("Source initial metal volume missing")
    monitor_metal = load_native_vol_field_monitor(case, "FS_C06_metalVoFVolume")
    monitor_solid = load_native_vol_field_monitor(case, "FS_C06_solidMetalVolume")
    snapshots = []
    for time_s, folder in native_time_dirs(case):
        if time_s <= 0:
            continue
        fluid = folder / "fluid"
        fields = [fluid / name for name in ("alpha.metal", MODEL_FIELD, "T.metal")]
        if not all(f.is_file() and not f.is_symlink() for f in fields):
            continue
        a = read_alpha(fields[0], expected_cells=FLUID_CELLS)
        s = read_native_solid_fraction(fields[1], expected_cells=FLUID_CELLS)
        T = read_native_metal_temperature(fields[2], expected_cells=FLUID_CELLS)
        allocation = classify_allocation(a, s, limit_examples=1)
        metrics = raw_phase_volume_diagnostics(volumes, a, s, T)
        native_metal_m3 = nearest_monitor_value(monitor_metal, time_s)
        native_solid_m3 = nearest_monitor_value(monitor_solid, time_s)
        # Independent comparison against native volFieldValue, not tolerance
        # adjustment. Some time matching may be unsupported or absent.
        snaps = {
            "time_s": time_s,
            **metrics,
            "strict_allocation_pass": allocation["strict_0_le_s_le_a_le_1_pass"],
            "allocation_1e8_tolerance_pass":
                allocation["validation_pass_with_original_tolerance_1e-8"],
            "strict_violation_cells": allocation["strict_invalid_cells"],
            "violation_cells_above_1e8":
                allocation["violating_cells_above_tolerance"][str(1e-8)],
            "max_fraction_violation": allocation["max_physical_constraint_violation"],
            "native_monitor_metal_m3": native_metal_m3,
            "native_monitor_solid_m3": native_solid_m3,
            "raw_metal_minus_monitor_m3": (
                metrics["native_raw_volIntegrate_alpha_metal_m3"]-native_metal_m3
                if native_metal_m3 is not None else None),
            "raw_solid_minus_monitor_m3": (
                metrics["native_raw_volIntegrate_alpha_metal_solid_m3"]-native_solid_m3
                if native_solid_m3 is not None else None),
            "SHA256_native_fields": {f.name: sha256(f) for f in fields},
        }
        snapshots.append(snaps)

    if not snapshots or not math.isclose(snapshots[-1]["time_s"], 1.0, abs_tol=1e-9):
        raise ValueError("No complete native 1 s phase snapshots; do not invent missing results")
    return {
        "schema": "masterproject-fs-c07-native-raw-phase-volume-recovery-v1",
        "original_case": str(case),
        "native_solved_to_time_s": base["latest_log_Time_s"],
        "native_solver_completed": True,
        "original_report_last_error": base["report_last_error"],
        "original_0_metal_volume_m3": initial_volume,
        "complete_saved_native_phase_snapshots": len(snapshots),
        "all_saved_snapshots_physically_bounded": all(
            x["strict_allocation_pass"] for x in snapshots),
        "all_saved_snapshots_pass_prior_1e8_tolerance": all(
            x["allocation_1e8_tolerance_pass"] for x in snapshots),
        "native_volFieldValue_metal_monitor_found": bool(monitor_metal),
        "native_volFieldValue_solid_monitor_found": bool(monitor_solid),
        "time_series": snapshots,
        "read_only": True,
        "any_native_field_edited": False,
        "native_solver_was_reexecuted": False,
        "raw_integrals_without_clipping_not_physical_acceptance": True,
        "globally_conservative_shrinkage_or_feeding_validated": False,
        "experimental_validation": False,
        "next_model_action": (
            "Investigate why alpha.metal.solid can exceed alpha.metal between "
            "native correct() updates (relative to advected VOF); enforce "
            "conservative solid/metal consistency in a new solver/model, "
            "not by masking or clipping archived simulation data."
        ),
    }


def compact_result(result: dict) -> dict:
    rows = result["time_series"]
    result = dict(result)
    result["time_series"] = [{
        "time_s": row["time_s"],
        "raw_metal_volume_m3": row["native_raw_volIntegrate_alpha_metal_m3"],
        "raw_solid_volume_m3": row["native_raw_volIntegrate_alpha_metal_solid_m3"],
        "raw_solid_over_metal_diagnostic": row["raw_solid_over_raw_metal_ratio_diagnostic_only"],
        "solid_excess_integral_m3":
            row["positive_violation_volume_integral_solid_exceeds_metal_m3"],
        "relative_solid_excess_integral":
            row["relative_positive_violation_vs_raw_metal_volume"],
        "invalid_cells_gt_1e8": row["violation_cells_above_1e8"],
        "core_cells_below_screen_liquidus":
            row["core_metal_cells_below_C14_screen_liquidus"],
        "core_metal_temp_min_K": row["core_metal_temperature_min_K"],
        "native_monitor_metal_minus_raw_m3": row["raw_metal_minus_monitor_m3"],
        "native_monitor_solid_minus_raw_m3": row["raw_solid_minus_monitor_m3"],
    } for row in rows]
    final = rows[-1]
    worst = max(rows, key=lambda x: x["positive_violation_volume_integral_solid_exceeds_metal_m3"])
    result["final_snapshot_diagnostic"] = final
    result["worst_allocation_excess_by_volume"] = {
        "time_s": worst["time_s"],
        "positive_violation_volume_integral_solid_exceeds_metal_m3":
            worst["positive_violation_volume_integral_solid_exceeds_metal_m3"],
        "max_fraction_violation": worst["max_fraction_violation"],
        "violation_cells_above_1e8": worst["violation_cells_above_1e8"],
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--compact", action="store_true")
    args = ap.parse_args()
    try:
        result = evaluate(args.case)
        if args.compact:
            result = compact_result(result)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print("FS-C07 READ-ONLY RAW PHASE RECOVERY BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
