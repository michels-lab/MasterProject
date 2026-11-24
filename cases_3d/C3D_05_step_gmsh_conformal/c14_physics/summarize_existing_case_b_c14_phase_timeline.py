#!/usr/bin/env python3
"""Source-verified Case B C14 alpha1(t) phase timeline from EXISTING 101-state CSV.

NEVER starts OpenFOAM, edits the CFD case or changes its existing native
postrun. Only derives 0.1s snapshot event windows, cell-mean rates and CSV/JSON
in an isolated, previously NONEXISTENT analysis directory. Not latent heat
balance, volume weighting, QuickCup validation or a new CFD result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze_existing_case_b_c14 as base

SOURCE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01"
DEST=Path.home()/"OpenFOAM/C3D05_B_C14_PHASE_TIMELINE_01"
NAME="C3D05_B_C14_PHASE_TIMELINE_101_STATES.json"
RATES="C3D05_B_C14_PHASE_INTERVALS.csv"
STATUS="C3D05_B_C14_ARCHIVED_PHASE_TIMELINE_NUMERICAL_ONLY"
FLOATS=("time_s","metal_T_min_K","metal_T_mean_K","metal_T_max_K",
        "mold_T_min_K","mold_T_mean_K","mold_T_max_K",
        "alpha1_min","alpha1_mean","alpha1_max")
COUNTS=("alpha1_below_0_999_cells","metal_T_below_Tliq_cells",
        "metal_T_below_Tsol_cells")


def require(ok,why):
    if not ok:
        raise ValueError("CASE_B_C14_EXISTING_PHASE_TIMELINE_BLOCKED: "+why)


def sha(path):
    require(path.is_file() and not path.is_symlink(),"missing/unsafe file: "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as stream:
        while chunk:=stream.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def load_native(source):
    require(source.is_dir() and not source.is_symlink() and source.name==SOURCE.name,
            "requires only real existing Case B 10s native analysis")
    csvpath=source/base.CSV
    jpath=source/base.JSON
    manifest=json.loads((source/base.MANIFEST).read_text(encoding="utf-8"))
    require(manifest.get("analysis_csv_sha256")==sha(csvpath)
            and manifest.get("analysis_json_sha256")==sha(jpath),
            "native source SHA mismatch, refuse re-analysis")
    doc=json.loads(jpath.read_text(encoding="utf-8"))
    require(doc.get("status")==base.STATUS
            and doc.get("native_CFD_solved_full_10s") is True
            and doc.get("native_C14_solidificationMeltingSource_selected") is True
            and doc.get("phase_field_mean_is_cell_based_unweighted") is True
            and doc.get("JMatPro_QuickCup_physical_validation") is False,
            "native postrun is not completed C14 original source")
    require(doc.get("native_original_C14_metadata",{}).get("metal_cells")==92200,
            "wrong metal cell count")
    require(doc.get("native_original_C14_metadata",{}).get("mold_cells")==178588,
            "wrong mold cell count")
    with csvpath.open(encoding="utf-8",newline="") as stream:
        data=list(csv.DictReader(stream))
    require(len(data)==101 and doc.get("saved_states")==101,
            "must have 101 complete native 0-10s states")
    rows=[]
    for i,source_row in enumerate(data):
        row={}
        for key in FLOATS:
            val=float(source_row[key])
            require(math.isfinite(val),"nonfinite field "+str(i)+":"+key)
            row[key]=val
        for key in COUNTS:
            val=int(source_row[key])
            require(0<=val<=92200 and str(val)==source_row[key].strip(),
                    "invalid native count "+str(i)+":"+key)
            row[key]=val
        require(0<=row["alpha1_min"]<=row["alpha1_mean"]<=row["alpha1_max"]<=1,
                "alpha1 not a valid liquid fraction")
        require(row["metal_T_min_K"]<=row["metal_T_mean_K"]<=row["metal_T_max_K"]
                and row["mold_T_min_K"]<=row["mold_T_mean_K"]<=row["mold_T_max_K"],
                "temperature extrema invalid")
        require(row["metal_T_below_Tsol_cells"]<=row["metal_T_below_Tliq_cells"],
                "solidus count exceeds liquidus count")
        require(i==0 or row["time_s"]>rows[-1]["time_s"],
                "nonascending saved timestamps")
        rows.append(row)
    require(rows[0]["time_s"]==0 and rows[-1]["time_s"]==10
            and [r["time_s"] for r in rows]==doc["saved_times_s"],
            "native time axis not complete and source-verified")
    for time_index,source_key in ((0,"initial_native_fields_unweighted"),
                                  (-1,"final_native_fields_unweighted")):
        for var in ("alpha1_mean","alpha1_min","metal_T_mean_K"):
            require(math.isclose(rows[time_index][var],doc[source_key][var],
                                 rel_tol=1e-12,abs_tol=1e-10),
                    "source field values disagree with archived certified JSON "+var)
    return rows,doc,{"csv_sha256":sha(csvpath),"json_sha256":sha(jpath),
                     "manifest_sha256":sha(source/base.MANIFEST)}


def first(rows,predicate):
    for index,row in enumerate(rows):
        if predicate(row):
            return {"first_saved_s":row["time_s"],
                    "previous_saved_s":rows[index-1]["time_s"] if index else None,
                    "exact_onset_unknown":True}
    return None


def describe(rows,doc):
    require(len(rows)==101 and rows[-1]["time_s"]==10,
            "invalid real native 101 snapshots")
    events={
        "first_any_cell_T_below_C14_Tliq":first(
            rows,lambda r:r["metal_T_below_Tliq_cells"]>0),
        "first_any_cell_T_below_C14_Tsol":first(
            rows,lambda r:r["metal_T_below_Tsol_cells"]>0),
        "first_any_cell_alpha1_below_0_999":first(
            rows,lambda r:r["alpha1_below_0_999_cells"]>0),
        "first_mean_alpha1_below_0_999":first(
            rows,lambda r:r["alpha1_mean"]<.999),
        "first_any_cell_alpha1_zero":first(
            rows,lambda r:r["alpha1_min"]<=1e-12),
        "first_cell_mean_solid_complement_above_5pct":first(
            rows,lambda r:1-r["alpha1_mean"]>.05),
        "first_cell_mean_solid_complement_above_10pct":first(
            rows,lambda r:1-r["alpha1_mean"]>.10),
        "first_cell_mean_solid_complement_above_20pct":first(
            rows,lambda r:1-r["alpha1_mean"]>.20),
    }
    old=doc["first_saved_alpha1_cell_below_0_999"]
    if old is None:
        require(events["first_any_cell_alpha1_below_0_999"] is None,
                "source postrun reports no alpha1 onset but CSV has one")
    else:
        require(events["first_any_cell_alpha1_below_0_999"]["first_saved_s"]
                ==old["first_observed_saved_time_s"]
                and events["first_any_cell_alpha1_below_0_999"]["previous_saved_s"]
                ==old["previous_saved_time_s"],
                "computed alpha1 onset disagrees with source native audit")
    intervals=[]
    for a,b in zip(rows,rows[1:]):
        dt=b["time_s"]-a["time_s"]
        require(dt>0,"invalid time interval")
        intervals.append({
            "start_s":a["time_s"],"end_s":b["time_s"],"interval_s":dt,
            "metal_mean_cooling_K_per_s":(a["metal_T_mean_K"]-b["metal_T_mean_K"])/dt,
            "mold_mean_heating_K_per_s":(b["mold_T_mean_K"]-a["mold_T_mean_K"])/dt,
            "mean_alpha1_decrease_per_s":(a["alpha1_mean"]-b["alpha1_mean"])/dt,
            "end_mean_liquid_fraction_unweighted":b["alpha1_mean"],
            "end_mean_solid_complement_unweighted":1-b["alpha1_mean"],
            "end_cells_with_alpha1_below_0_999":b["alpha1_below_0_999_cells"],
        })
    result={
        "schema":"C3D05_B_C14_EXISTING_NATIVE_PHASE_TIMELINE_V1",
        "status":STATUS,
        "real_C14_B_native_CFD_10s_completed":True,
        "saved_snapshots":len(rows),
        "first_observed_events_only_bracketed_by_saved_states":events,
        "original_C14_phase_reference":doc["original_C14_phase_parameters_reference"],
        "alpha1_final_unweighted_cell_mean":rows[-1]["alpha1_mean"],
        "one_minus_alpha1_final_unweighted_cell_mean":1-rows[-1]["alpha1_mean"],
        "minimum_saved_alpha1":min(x["alpha1_min"] for x in rows),
        "max_cells_below_alpha1_0_999":max(x["alpha1_below_0_999_cells"] for x in rows),
        "max_Courant_over_original_full_native_log":doc["max_saved_metal_Courant"],
        "peak_saved_mean_alpha1_drop_per_s":max(
            x["mean_alpha1_decrease_per_s"] for x in intervals),
        "peak_saved_mean_metal_cooling_K_per_s":max(
            x["metal_mean_cooling_K_per_s"] for x in intervals),
        "notes":[
            "This is C14 ORIGINAL numerical phase evolution, NOT real QuickCup calibration.",
            "First event is bracketed within a saved interval, never precise onset.",
            "Cell-unweighted 1-mean(alpha1) is NOT volume/mass-weighted solid fraction.",
            "Rates are finite differences across saved 0.1s states, NOT true latent heat rate.",
            "No CFD solver, no remesh, no source modification or synthetic alpha1.",
        ],
        "physical_volume_weighted_fraction_verified":False,
        "latent_heat_energy_and_interface_flux_verified":False,
        "QuickCup_JMatPro_validation":False,
        "grid_time_convergence":False,
        "contraction_feeding_verified":False,
    }
    return result,intervals


def execute(source,out):
    source=source.expanduser().absolute()
    out=out.expanduser().absolute()
    require(out!=source and out not in source.parents and source not in out.parents,
            "do not write within source or CFD folder")
    require(not out.exists() and not out.is_symlink(),
            "existing analysis preserved: "+str(out))
    rows,doc,hashes=load_native(source)
    report,intervals=describe(rows,doc)
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(out.parent),
                                     prefix="."+out.name+".staging.") as temp:
        candidate=Path(temp)/"candidate"
        candidate.mkdir()
        with (candidate/RATES).open("x",encoding="utf-8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=list(intervals[0]))
            writer.writeheader()
            writer.writerows(intervals)
        (candidate/NAME).write_text(json.dumps(
            report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        (candidate/"SOURCE_SHA256.json").write_text(json.dumps({
            "input_source_read_only":str(source),"verified_source":hashes,
            "derivative_json_sha256":sha(candidate/NAME),
            "interval_csv_sha256":sha(candidate/RATES)
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "output appeared while processing; refusing overwrite")
        candidate.rename(out)
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--analysis",type=Path,default=SOURCE)
    ap.add_argument("--out",type=Path,default=DEST)
    opts=ap.parse_args()
    try:
        doc=execute(opts.analysis,opts.out)
        print(json.dumps({
            "status":doc["status"],
            "out":str(opts.out),
            "saved_states":doc["saved_snapshots"],
            "first_alpha1_below_0_999":doc[
                "first_observed_events_only_bracketed_by_saved_states"][
                    "first_any_cell_alpha1_below_0_999"],
            "first_any_cell_fully_solid_by_model":doc[
                "first_observed_events_only_bracketed_by_saved_states"][
                    "first_any_cell_alpha1_zero"],
            "mean_solid_complement_unweighted":doc[
                "one_minus_alpha1_final_unweighted_cell_mean"],
            "latent_heat_balance_verified":False,
            "physical_validation":False,
            "NO_CFD_RUN":True,
        },indent=2,ensure_ascii=False))
        return 0
    except (ValueError,TypeError,KeyError,OSError,UnicodeError) as exc:
        print("C3D05_B_C14_PHASE_TIMELINE_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
