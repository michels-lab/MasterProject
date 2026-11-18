#!/usr/bin/env python3
"""FS-C02 exact shared-cell thermal and alpha-motion diagnostics; NO CFD.

Uses the previously verified pair (same mesh, geometry, phase inputs, times,
only RAS+VOF-damping vs laminar changed). This isolates selection effects from
phase-dependent 'pure gas' populations by requiring gas in *both* simulations
on the same cell index. It tracks alpha evolution relative to the first
saved 0.001s field, NOT initial t=0 or physical free-surface height.

Never writes case files, launches solvers, or evaluates solidification.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

from audit_fs_c02_local import CELL_VOLUME, EXPECTED_CELLS, read_alpha, read_temperature, require
from compare_fs_c02_ras_laminar import BASE_PROFILE, LAMINAR_PROFILE, completed_run, compare
from inspect_fs_c02_thermal import snapshots

GAS_LIMIT = 1e-6
INTERFACE_LOW = 0.01
INTERFACE_HIGH = 0.99


def evaluate_same_cells(a_ras: list[float], t_ras: list[float],
                        a_lam: list[float], t_lam: list[float],
                        first_ras: list[float], first_lam: list[float]) -> dict:
    require(all(len(x) == EXPECTED_CELLS for x in
                (a_ras, t_ras, a_lam, t_lam, first_ras, first_lam)),
            "fields do not match the verified 9600-cell mesh")
    require(all(math.isfinite(a) and -1e-6 <= a <= 1+1e-6
                for values in (a_ras, a_lam, first_ras, first_lam)
                for a in values), "invalid alpha.metal")
    require(all(math.isfinite(t) and t > 0
                for values in (t_ras, t_lam) for t in values),
            "invalid temperature")
    common = [i for i,(a,b) in enumerate(zip(a_ras,a_lam))
              if a <= GAS_LIMIT and b <= GAS_LIMIT]
    ras_only = sum(a <= GAS_LIMIT and b > GAS_LIMIT
                   for a,b in zip(a_ras,a_lam))
    lam_only = sum(b <= GAS_LIMIT and a > GAS_LIMIT
                   for a,b in zip(a_ras,a_lam))
    require(bool(common), "no common nearly pure gas cells")
    deltas = [t_ras[i]-t_lam[i] for i in common]
    mean_ras = sum(t_ras[i] for i in common) / len(common)
    mean_lam = sum(t_lam[i] for i in common) / len(common)
    require(math.isclose(mean_ras - mean_lam,
                         sum(deltas)/len(common),abs_tol=1e-7),
            "unmatched common-gas means")
    def motion(a,initial):
        diffs = [abs(x-y) for x,y in zip(a,initial)]
        return {
            "alpha_abs_change_sum_cells":sum(diffs),
            "alpha_L1_changed_volume_equivalent_m3":sum(diffs)*CELL_VOLUME,
            "alpha_cells_changed_above_1e_minus_6":sum(d>1e-6 for d in diffs),
            "meaningful_interface_cells_0_01_to_0_99":
                sum(INTERFACE_LOW < x < INTERFACE_HIGH for x in a),
        }
    return {
        "same_near_pure_gas_cells_both_models":len(common),
        "near_pure_gas_cells_only_RAS":ras_only,
        "near_pure_gas_cells_only_laminar":lam_only,
        "common_cells_RAS_mean_T_K":mean_ras,
        "common_cells_laminar_mean_T_K":mean_lam,
        "common_cells_RAS_minus_laminar_T_K":mean_ras-mean_lam,
        "common_cells_fraction_RAS_hotter":
            sum(v>0 for v in deltas)/len(deltas),
        "common_cells_RAS_hot_gt_1000K":
            sum(t_ras[i]>1000 for i in common),
        "common_cells_laminar_hot_gt_1000K":
            sum(t_lam[i]>1000 for i in common),
        "RAS_alpha_motion_since_first_saved_time":motion(a_ras,first_ras),
        "laminar_alpha_motion_since_first_saved_time":motion(a_lam,first_lam),
        "cell_index_comparison_assumes_proven_identical_mesh_inputs":True,
        "free_surface_height_or_interface_velocity_measured":False,
        "energy_conservation_physically_verified":False,
    }


def analyze(ras_run: Path, lam_run: Path) -> dict:
    # Strict full-pair audit checks 20 hashes, 18 inputs identical, exactly
    # two turbulence-related changes, Co and all matching time snapshots.
    validated = compare(ras_run,lam_run)
    ras = completed_run(ras_run,BASE_PROFILE)
    lam = completed_run(lam_run,LAMINAR_PROFILE)
    ras_times = snapshots(ras["case"])
    lam_times = snapshots(lam["case"])
    require(len(ras_times)==len(lam_times), "saved times mismatch")
    first_ras = read_alpha(ras_times[0][1]/"alpha.metal")
    first_lam = read_alpha(lam_times[0][1]/"alpha.metal")
    entries=[]
    for (ta,ra), (tb,la) in zip(ras_times,lam_times):
        require(abs(ta-tb)<1e-8,"saved times mismatch")
        fields = evaluate_same_cells(
            read_alpha(ra/"alpha.metal"),read_temperature(ra/"T"),
            read_alpha(la/"alpha.metal"),read_temperature(la/"T"),
            first_ras, first_lam,
        )
        entries.append({"time_s":ta,**fields})
    end=entries[-1]
    return {
        "schema":"masterproject-fs-c02-shared-cell-vof-thermal-audit-v1",
        "status":"COMMON_CELL_COMPARISON_NO_PHYSICAL_THERMAL_VALIDATION",
        "source_RAS":validated["reference_run"],
        "source_laminar":validated["laminar_run"],
        "reference_manifest_sha256":validated["reference_manifest_sha256"],
        "laminar_manifest_sha256":validated["laminar_manifest_sha256"],
        "unchanged_solver_inputs":validated["unchanged_input_count"],
        "changed_solver_inputs":validated["changed_input_files"],
        "snapshots_compared":len(entries),
        "first_time_s":entries[0]["time_s"],
        "final_time_s":end["time_s"],
        "final_common_near_pure_gas_cell_count":
            end["same_near_pure_gas_cells_both_models"],
        "final_common_cells_temperature_gap_K":
            end["common_cells_RAS_minus_laminar_T_K"],
        "final_RAS_interface_cell_count":
            end["RAS_alpha_motion_since_first_saved_time"]
               ["meaningful_interface_cells_0_01_to_0_99"],
        "final_laminar_interface_cell_count":
            end["laminar_alpha_motion_since_first_saved_time"]
               ["meaningful_interface_cells_0_01_to_0_99"],
        "laminar_alpha_unchanged_since_first_saved_step":
            all(e["laminar_alpha_motion_since_first_saved_time"]
                  ["alpha_cells_changed_above_1e_minus_6"]==0
                for e in entries),
        "reference_first_saved_time_is_not_t0":True,
        "model_package_effect_not_individual_RAS_or_damping":True,
        "absence_of_alpha_change_is_not_proof_of_zero_velocity":True,
        "no_solidification_no_shrinkage":True,
        "records":entries,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ras",type=Path,required=True)
    p.add_argument("--laminar",type=Path,required=True)
    p.add_argument("--brief",action="store_true")
    args=p.parse_args(argv)
    try:
        r=analyze(args.ras,args.laminar)
        if args.brief:
            records=r["records"]
            r["records"]=[records[i] for i in sorted({0,len(records)//2,len(records)-1})]
            r["brief_three_times_only"]=True
        print(json.dumps(r,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as ex:
        print("FS-C02 SHARED CELL BLOCKED: "+str(ex),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
