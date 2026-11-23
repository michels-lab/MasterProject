#!/usr/bin/env python3
"""Summarize ALREADY-COMPUTED original C14 3D time-series, without running CFD.

Reads the previously emitted C3D04_A_C14_10S_TIME_SERIES.csv and its audited
diagnostic JSON in WSL. Writes *only* into a NEW separate directory.
First observed events are bounded by the 0.1s snapshot cadence, not claims
of exact solidification onset. Cell means are NOT volume-/mass-weighted.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
CSV="C3D04_A_C14_10S_TIME_SERIES.csv"
JSON="C3D04_A_C14_10S_DIAGNOSTICS.json"
OUT="C3D04_A_C14_PHASE_TIMELINE_AUDIT.json"
METAL_CELLS=8960
C14_TSOL=1423.0
C14_TLIQ=1473.0
AUDITED_STATUS="EXISTING_REAL_V4_T02_C14_10S_FIELDS_AND_LOG_AUDITED_NOT_PHYSICALLY_VALIDATED"

def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("C14_PHASE_TIMELINE_GATE_BLOCKED: "+reason)

def parse_existing(rows_csv: Path, diagnostics_json: Path) -> tuple[list[dict],dict]:
    require(rows_csv.is_file() and diagnostics_json.is_file(),
            "missing existing 101-state analyzed CSV/JSON (do not rerun CFD)")
    doc=json.loads(diagnostics_json.read_text(encoding="utf-8"))
    require(doc.get("status")==AUDITED_STATUS,"wrong science audit source")
    require(doc.get("source_mesh_cells",{}).get("metal")==METAL_CELLS,
            "wrong source mesh metal cells (not C3D04 V4/T02)")
    require(doc.get("F14_native_log",{}).get("time_last_s")==10,
            "original native C14 10-second completion not verified")
    require(doc.get("NOT_A_NEW_CFD") is True and
            doc.get("energy_balance_verified") is False,
            "original postrun scientific status drift")
    with rows_csv.open(encoding="utf-8",newline="") as source:
        reader=csv.DictReader(source)
        rows=list(reader)
    require(rows,"empty native 10s CSV")
    require(len(rows)==doc.get("time_states_count"),
            "CSV rows mismatch original certified 101 states")
    nums=(
        "time_s","metal_T_min_K","metal_T_mean_K","metal_T_max_K",
        "mold_T_min_K","mold_T_mean_K","mold_T_max_K",
        "metal_below_Tliq_cells","metal_below_Tsol_cells",
        "metal_alpha1_min","metal_alpha1_mean","metal_alpha1_max",
        "metal_alpha1_below_0_999_cells",
        "metal_p_rgh_min_Pa","metal_p_rgh_mean_Pa","metal_p_rgh_max_Pa",
    )
    converted=[]
    for i,row in enumerate(rows):
        clean={}
        for key in nums:
            try:
                value=float(row[key])
            except (ValueError,KeyError,TypeError) as exc:
                raise ValueError("CSV invalid numeric field "+str(i)+"."+key) from exc
            require(math.isfinite(value),"non-finite CSV "+str(i)+"."+key)
            clean[key]=value
        t=clean["time_s"]
        require(i==0 or t>converted[-1]["time_s"],
                "native saved timestamps not strictly increasing")
        require(0<=t<=10,"source C14 times outside 0..10")
        require(clean["metal_T_min_K"]<=clean["metal_T_mean_K"]<=clean["metal_T_max_K"],
                "metal T statistics inconsistent")
        require(clean["mold_T_min_K"]<=clean["mold_T_mean_K"]<=clean["mold_T_max_K"],
                "mold T statistics inconsistent")
        require(0<=clean["metal_alpha1_min"]<=clean["metal_alpha1_mean"]<=
                clean["metal_alpha1_max"]<=1,
                "liquid phase fraction outside [0,1] or inconsistent")
        for key in ("metal_below_Tliq_cells","metal_below_Tsol_cells",
                    "metal_alpha1_below_0_999_cells"):
            require(clean[key].is_integer() and 0<=clean[key]<=METAL_CELLS,
                    "invalid metal threshold count "+key)
        require(clean["metal_below_Tsol_cells"]<=clean["metal_below_Tliq_cells"],
                "below-solidus cannot exceed below-liquidus counts")
        converted.append(clean)
    require(math.isclose(converted[0]["time_s"],0,abs_tol=1e-10)
            and math.isclose(converted[-1]["time_s"],10,abs_tol=1e-10),
            "existing native 3D C14 analysis must span t0..10")
    return converted,doc

def observed_event(rows: list[dict], predicate) -> dict|None:
    for index,row in enumerate(rows):
        if predicate(row):
            return {
                "first_saved_time_s":row["time_s"],
                "previous_saved_time_s":rows[index-1]["time_s"] if index else None,
                "interpretation":"FIRST_SAVED_SNAPSHOT_ONLY_NOT_EXACT_PHYSICAL_ONSET",
            }
    return None

def summarize(rows: list[dict],diagnostics: dict)->dict:
    require(len(rows)>=2,"need at least two time points")
    require(rows[0]["metal_alpha1_mean"]>=0.999,
            "initial C14 melt fraction no longer near one")
    require(rows[0]["metal_T_min_K"]>C14_TLIQ,
            "initial metal temperature differs from C14 T0")
    intervals=[]
    for before,after in zip(rows,rows[1:]):
        delta_t=after["time_s"]-before["time_s"]
        require(delta_t>0,"invalid C14 time interval")
        intervals.append({
            "from_s":before["time_s"],"to_s":after["time_s"],
            "metal_mean_cooling_K_per_s":
                (before["metal_T_mean_K"]-after["metal_T_mean_K"])/delta_t,
            "mold_mean_heating_K_per_s":
                (after["mold_T_mean_K"]-before["mold_T_mean_K"])/delta_t,
            "alpha1_mean_change_per_s":
                (after["metal_alpha1_mean"]-before["metal_alpha1_mean"])/delta_t,
        })
    final=rows[-1]
    return {
        "schema":"C3D04_A_EXISTING_10S_C14_PHASE_TIMELINE_V1",
        "status":"POSTRUN_PHASE_TIMELINE_ONLY_NO_NEW_CFD_NO_ENERGY_BALANCE",
        "real_existing_run_source":diagnostics["source_case_read_only"],
        "existing_analysis_source":diagnostics["output_analysis_separate"],
        "original_C14_reference":{"Tsol_K":C14_TSOL,"Tliq_K":C14_TLIQ},
        "native_t_final_s":final["time_s"],
        "saved_time_points":len(rows),
        "first_saved_metal_below_liquidus":
            observed_event(rows,lambda r:r["metal_below_Tliq_cells"]>0),
        "first_saved_metal_below_solidus":
            observed_event(rows,lambda r:r["metal_below_Tsol_cells"]>0),
        "first_saved_any_alpha1_below_0_999":
            observed_event(rows,lambda r:r["metal_alpha1_below_0_999_cells"]>0),
        "first_saved_alpha1_mean_below_0_999":
            observed_event(rows,lambda r:r["metal_alpha1_mean"]<0.999),
        "last_metal_mean_K":final["metal_T_mean_K"],
        "last_metal_below_Tliq_cells":int(final["metal_below_Tliq_cells"]),
        "last_metal_below_Tsol_cells":int(final["metal_below_Tsol_cells"]),
        "last_mean_alpha1_unweighted":final["metal_alpha1_mean"],
        "last_mean_one_minus_alpha1_unweighted":1-final["metal_alpha1_mean"],
        "mean_metal_T_cooling_over_10s_K_per_s":
            (rows[0]["metal_T_mean_K"]-final["metal_T_mean_K"])/10,
        "peak_positive_saved_interval_metal_mean_cooling_K_per_s":
            max(x["metal_mean_cooling_K_per_s"] for x in intervals),
        "peak_saved_interval_alpha1_mean_decrease_per_s":
            max(-x["alpha1_mean_change_per_s"] for x in intervals),
        "native_log_Courant_max_all_steps":
            diagnostics["F14_native_log"]["courant_max_over_all_logged_steps"],
        "energy_balance_verified":False,
        "volume_weighting":False,
        "mesh_time_independence_verified":False,
        "QuickCup_validated":False,
        "physical_validation":False,
        "notes":[
            "First saved event is bounded by neighboring saved t=0.1s states, NOT exact onset.",
            "alpha1 is the source-model liquid fraction field. 1-mean(alpha1) is unweighted cell mean, NOT mass-/volume-integrated solid fraction.",
            "Temporal cell-mean derivatives are numerical summary only; not proof of recalescence or latent-heat release rate.",
            "No new solver run; no source data modified; output is in separate directory."
        ],
        "interval_rates":intervals,
    }

def main()->int:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--analysis",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_ANALYSIS_01")
    a.add_argument("--out",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_PHASE_TIMELINE_01")
    args=a.parse_args()
    analysis=args.analysis.expanduser().resolve()
    out=args.out.expanduser().absolute()
    try:
        require(out!=analysis and out not in analysis.parents
                and analysis not in out.parents,
                "output must remain separate from original analysis")
        require(not out.exists() and not out.is_symlink(),
                "output already exists; preserve earlier timeline audit")
        rows,source=parse_existing(analysis/CSV,analysis/JSON)
        report=summarize(rows,source)
        out.mkdir(parents=True,exist_ok=False)
        (out/OUT).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                             encoding="utf-8")
        condensed={k:v for k,v in report.items() if k!="interval_rates"}
        print(json.dumps({**condensed,"report":str(out/OUT)},indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("C14_PHASE_TIMELINE_GATE_BLOCKED:",exc,file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
