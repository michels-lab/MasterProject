#!/usr/bin/env python3
"""FS-C02 RAS/damping-vs-laminar 0.01s A/B: READ ONLY saved OpenFOAM fields.

Both reference and laminar runs must have successfully completed Foundation14
0.01s Courant gates. Exactly two generated inputs may differ:
constant/momentumTransport and constant/fvModels. Compare all archived
alpha.metal/T snapshots at matching saved times. No CFD or file writes.

This quantifies an A/B *model-package* dependence of gas temperatures.
It does NOT prove a kEpsilon-only effect, physically correct thermal
transport, a phase-wise energy budget, solidification or contraction.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from audit_fs_c02_local import (
    CELL_VOLUME, INITIAL_VOLUME, SCHEMA, digest, read_alpha, read_temperature,
    read_volume, require, log_courant,
)
from inspect_fs_c02_thermal import snapshots
from run_fs_c02_laminar_control import BASE_PROFILE, LAMINAR_PROFILE

ALPHA_GAS_MAX = 1e-6
ALPHA_METAL_MIN = .99
END_TIME = .01
ACCEPT_CO = .20
ALLOWED_DIFF = frozenset(("constant/momentumTransport", "constant/fvModels"))


def completed_run(root: Path, expected_profile: str) -> dict:
    root = root.expanduser().resolve()
    expected_prefix = "FS-C02_EXTENDED_" if expected_profile == BASE_PROFILE \
                      else "FS-C02_LAMINAR_"
    case = root / "FS-C02"
    require(root.name.startswith(expected_prefix) and
            case.is_dir() and not case.is_symlink(),
            "incorrect experiment namespace or missing FS-C02 case")
    state_file = root / "FS-C02_RUN_STATUS.json"
    manifest_file = case / "FS-C02_MANIFEST.json"
    require(state_file.is_file() and not state_file.is_symlink() and
            manifest_file.is_file() and not manifest_file.is_symlink(),
            "missing experiment status/manifest")
    state = json.loads(state_file.read_text())
    manifest = json.loads(manifest_file.read_text())
    require(state.get("case_id") == "FS-C02" and
            state.get("solver_tested_on_real_openfoam") is True and
            state.get("status") == "PROBE_COURANT_SCREEN_PASSED" and
            state.get("extended_probe") is True,
            "case did not complete the Courant screen")
    steps = state.get("stages")
    require(isinstance(steps, list) and len(steps) == 3 and
            [s.get("stage") for s in steps] ==
            ["blockMesh", "checkMesh", "foamRun"] and
            all(s.get("returncode") == 0 and s.get("gate_passed") is True
                for s in steps),
            "blockMesh/checkMesh/foamRun success not recorded")
    require(bool(state.get("laminar_control", False)) ==
            (expected_profile == LAMINAR_PROFILE),
            "laminar-control status mismatches required experiment")
    require(manifest.get("schema") == SCHEMA and
            manifest.get("execution_profile") == expected_profile and
            manifest.get("physical_assumptions", {}).get("solidification") is False and
            manifest.get("physical_assumptions", {}).get("contraction") is False,
            "incorrect physics or profile")
    control = manifest.get("time_controls", {})
    require(control == state.get("time_controls") and
            math.isclose(control.get("endTime_s", -1), END_TIME) and
            math.isclose(control.get("maxCo", -1), .15) and
            math.isclose(control.get("maxAlphaCo", -1), .15) and
            math.isclose(control.get("acceptance_maxCo", -1), ACCEPT_CO),
            "time/Co controls are not matched")
    inventory = manifest.get("generated_input_sha256")
    require(isinstance(inventory, dict) and len(inventory) == 20,
            "expected 20 traced inputs")
    for filename, sha in inventory.items():
        rel = Path(filename)
        require(not rel.is_absolute() and ".." not in rel.parts and
                rel.parts[0] in ("0", "constant", "system") and
                (case / rel).is_file() and not (case / rel).is_symlink(),
                "untrusted input path " + filename)
        require(digest(case / rel) == sha,
                "altered original input " + filename)
    if expected_profile == LAMINAR_PROFILE:
        require(set(manifest.get("changed_input_files_vs_extended_reference", []))
                == ALLOWED_DIFF,
                "laminar manifest does not identify exact two modified inputs")
    log_file = root / "logs" / "FS-C02_foamRun.log"
    require(log_file.is_file() and not log_file.is_symlink(),
            "missing original solver log")
    co = log_courant(log_file.read_text(encoding="utf-8", errors="replace"))
    require(co["max_courant_over_log"] is not None and
            co["max_interface_courant_over_log"] is not None and
            co["max_courant_over_log"] <= ACCEPT_CO and
            co["max_interface_courant_over_log"] <= ACCEPT_CO,
            "original solver log exceeds common Co acceptance")
    volume = read_volume(case / "postProcessing/metalVolume/0/volFieldValue.dat")
    require(abs(volume[0][0]) < 1e-7 and abs(volume[-1][0]-END_TIME)<1e-6,
            "volume series must cover original 0 to 0.01 s interval")
    max_vol_drift = max(abs(v - volume[0][1]) / INITIAL_VOLUME
                        for _, v in volume)
    return {
        "run": root, "case": case, "manifest": manifest,
        "manifest_sha256": digest(manifest_file),
        "volume_series_sha256":
            digest(case / "postProcessing/metalVolume/0/volFieldValue.dat"),
        "max_volume_drift_fraction": max_vol_drift,
        "courant": co,
    }


def read_snapshot(case: Path, folder: Path) -> dict:
    a_file, t_file = folder / "alpha.metal", folder / "T"
    alpha = read_alpha(a_file)
    T = read_temperature(t_file)
    require(all(math.isfinite(x) and -1e-6 <= x <= 1+1e-6
                for x in alpha), "VOF fractions unbounded")
    require(all(math.isfinite(t) and t > 0 for t in T),
            "invalid temperature")
    gas = [t for a,t in zip(alpha,T) if a <= ALPHA_GAS_MAX]
    metal = [t for a,t in zip(alpha,T) if a >= ALPHA_METAL_MIN]
    require(gas and metal, "near-pure gas or metal is absent")
    return {
        "saved_T_sha256": digest(t_file),
        "saved_alpha_sha256": digest(a_file),
        "near_pure_air_cells": len(gas),
        "near_pure_air_mean_T_K": sum(gas)/len(gas),
        "near_pure_air_hot_above_1000K_cells": sum(t>1000 for t in gas),
        "near_pure_air_max_T_K": max(gas),
        "metal_like_cells": len(metal),
        "metal_like_mean_T_K": sum(metal)/len(metal),
        "alpha_integrated_metal_volume_m3": sum(alpha)*CELL_VOLUME,
    }


def compare(ras_run: Path, laminar_run: Path) -> dict:
    ras = completed_run(ras_run, BASE_PROFILE)
    lam = completed_run(laminar_run, LAMINAR_PROFILE)
    require(ras["run"] != lam["run"], "must be distinct completed cases")
    a, b = ras["manifest"]["generated_input_sha256"],\
           lam["manifest"]["generated_input_sha256"]
    require(a.keys() == b.keys(), "input inventories do not match")
    changed = frozenset(path for path in a if a[path] != b[path])
    require(changed == ALLOWED_DIFF,
            "ablation MUST change only constant/momentumTransport + constant/fvModels")
    require(ras["manifest"]["b14_material_sha256"] ==
            lam["manifest"]["b14_material_sha256"] and
            ras["manifest"]["source_fs_c01_manifest_sha256"] ==
            lam["manifest"]["source_fs_c01_manifest_sha256"],
            "different upstream B14/FS-C01 provenance")

    a_times, b_times = snapshots(ras["case"]), snapshots(lam["case"])
    require(len(a_times) == len(b_times), "different time-snapshot counts")
    records = []
    for (ta, fa), (tb, fb) in zip(a_times, b_times):
        require(abs(ta-tb) < 1e-8,
                "saved times not aligned: no interpolation/fabricated comparison")
        ar, bl = read_snapshot(ras["case"], fa), read_snapshot(lam["case"], fb)
        gas_delta = ar["near_pure_air_mean_T_K"] - bl["near_pure_air_mean_T_K"]
        delta_ref = ar["near_pure_air_mean_T_K"] - 300.
        delta_lam = bl["near_pure_air_mean_T_K"] - 300.
        records.append({
            "time_s": ta,
            "RAS_damping": ar,
            "laminar_no_damping": bl,
            "near_pure_air_mean_T_reduction_RAS_minus_laminar_K": gas_delta,
            "gas_mean_rise_RAS_above_initial_300K": delta_ref,
            "gas_mean_rise_laminar_above_initial_300K": delta_lam,
            "reduction_in_apparent_gas_mean_heating_fraction":
                ((delta_ref-delta_lam)/delta_ref
                 if delta_ref > 0 else None),
            "difference_in_hot_gas_cell_count":
                (ar["near_pure_air_hot_above_1000K_cells"] -
                 bl["near_pure_air_hot_above_1000K_cells"]),
        })
    final=records[-1]
    return {
        "schema":"masterproject-fs-c02-ras-laminar-paired-audit-v1",
        "status":"PAIRED_NUMERICAL_COMPARISON_NO_THERMAL_VALIDATION",
        "reference_run":str(ras["run"]),
        "laminar_run":str(lam["run"]),
        "reference_manifest_sha256":ras["manifest_sha256"],
        "laminar_manifest_sha256":lam["manifest_sha256"],
        "changed_input_files":sorted(changed),
        "unchanged_input_count":len(a)-len(changed),
        "matched_time_samples":len(records),
        "final_time_s":final["time_s"],
        "maximum_Courant_RAS":ras["courant"]["max_courant_over_log"],
        "maximum_Courant_laminar":lam["courant"]["max_courant_over_log"],
        "max_volume_drift_fraction_RAS":ras["max_volume_drift_fraction"],
        "max_volume_drift_fraction_laminar":lam["max_volume_drift_fraction"],
        "final_near_pure_gas_mean_T_RAS_K":
            final["RAS_damping"]["near_pure_air_mean_T_K"],
        "final_near_pure_gas_mean_T_laminar_K":
            final["laminar_no_damping"]["near_pure_air_mean_T_K"],
        "final_gas_temperature_difference_RAS_minus_laminar_K":
            final["near_pure_air_mean_T_reduction_RAS_minus_laminar_K"],
        "final_relative_reduction_in_apparent_gas_heating":
            final["reduction_in_apparent_gas_mean_heating_fraction"],
        "model_effect_only_package_not_kEpsilon_or_damping_separately":True,
        "gas_cell_sets_identical_across_simulations":False,
        "energy_balance_verified":False,
        "metal_air_thermophysical_parameters_validated":False,
        "solidification_or_shrinkage_modelled":False,
        "times":records,
    }


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ras",type=Path,required=True,
                    help="original FS-C02_EXTENDED RAS run directory")
    ap.add_argument("--laminar",type=Path,required=True,
                    help="new FS-C02_LAMINAR run directory")
    ap.add_argument("--brief",action="store_true",
                    help="print first, middle and last time only (full audit still performed)")
    args=ap.parse_args(argv)
    try:
        report=compare(args.ras,args.laminar)
        if args.brief:
            records=report["times"]
            report["times"]=[records[i] for i in
                             sorted({0,len(records)//2,len(records)-1})]
            report["brief_three_times_only"]=True
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as ex:
        print("FS-C02 PAIR AUDIT BLOCKED: "+str(ex),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
