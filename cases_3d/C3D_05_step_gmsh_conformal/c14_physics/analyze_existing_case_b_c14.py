#!/usr/bin/env python3
"""Read-only postrun audit of REAL Case B C14 10s fluid/solid phase-change CFD.

Uses the source-verified Case A C14 native scalar reader and full-solver-log
audit; DOES NOT run OpenFOAM, alter a time directory, remesh, approximate
JMatPro, infer physical latent heat or certify experiment/grid convergence.

Requires completed original C14 10s run on the 270788-cell authentic C3D-05
HEX8 (metal 92200, mold 178588), all 10s saved native fields, verified log,
and C14 original physical inputs. Writes exactly one NEW separate analysis.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CASE_A=REPO/"cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
sys.path.insert(0,str(CASE_A))
import analyze_existing_c14_3d_results as source_reader
import c14_source_fidelity as physics
import stage_c14_3d_case_a as a
import stage_c14_3d_case_b as b

DEFAULT_CASE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
DEFAULT_OUT=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01"
LOG="log.foamMultiRun.C3D05_B_C14_10S"
REPORT=b.REPORT
SUCCESS="C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED"
STATUS="CASE_B_C14_REAL_10S_POSTRUN_NATIVE_FIELDS_AUDITED_NOT_PHYSICALLY_VALIDATED"
CSV="C3D05_B_C14_REAL_10S_TIME_SERIES.csv"
JSON="C3D05_B_C14_REAL_10S_ANALYSIS.json"
MANIFEST="C3D05_B_C14_REAL_10S_POSTRUN_SHA256.json"
EXPECTED={"metal":92200,"mold":178588}
FIELDS=(
    "time_s","metal_T_min_K","metal_T_mean_K","metal_T_max_K",
    "mold_T_min_K","mold_T_mean_K","mold_T_max_K",
    "metal_T_below_Tliq_cells","metal_T_below_Tsol_cells",
    "metal_T_below_Tliq_percent_cells","metal_T_below_Tsol_percent_cells",
    "alpha1_min","alpha1_mean","alpha1_max",
    "alpha1_below_0_999_cells","alpha1_below_0_999_percent_cells",
    "p_rgh_min_Pa","p_rgh_mean_Pa","p_rgh_max_Pa"
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("C3D05_B_C14_POSTRUN_READONLY_BLOCKED: "+reason)


def hashfile(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(),"source missing or symlink "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as inp:
        while chunk:=inp.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def validated_mesh_and_stage(case: Path) -> tuple[dict,dict]:
    require(case.is_dir() and not case.is_symlink(),"real C14 Case B CFD directory unavailable")
    require(case.name=="C3D05_B_C14_FLUID_SOLID_FULL_10S_01",
            "only accepted isolated C3D05-B C14 native run, never C3D04-A or T0 surrogate")
    physics.verify()
    stage_path=case/REPORT
    meta=json.loads(stage_path.read_text(encoding="utf-8"))
    require(meta.get("schema")=="C3D05_B_C14_EXACT_SOURCE_3D_V1",
            "wrong native stage schema")
    require(meta.get("status")==SUCCESS and meta.get("native_solver_run") is True,
            "native 10s fluid/solid CFD has NOT completed with success report; do not audit in-progress run")
    require(meta.get("original_C14_controlDict_unchanged") is True
            and meta.get("Cp_to_Cv_substitution") is False
            and meta.get("contraction_model_activated") is False
            and meta.get("experimentally_validated") is False,
            "source-faithful C14 status not retained")
    require(meta.get("geometry_gate",{}).get("nCells")==EXPECTED,
            "not native 92200/178588 metal/mold geometry")
    require(meta.get("geometry_gate",{}).get("coupled_faces_each")==12636,
            "not accepted authentic coupled metal/mold contact")
    require(meta.get("source_C14_3D_only_adaptations") is not None,
            "3D-only geometry mappings not documented")
    actual_control=hashfile(case/"system/controlDict")
    require(actual_control==meta.get("original_C14_controlDict_sha256")
            and (case/"system/controlDict").read_bytes()==
                (physics.C14/"system/controlDict").read_bytes(),
            "C14 10-second control differs from exact original")
    require(all(a.region_cells(case,r,EXPECTED[r])["nCells"]==EXPECTED[r]
                for r in ("metal","mold")),
            "real 3D region polyMesh cell count differs from native acceptance")
    expected_hashes=meta.get("five_native_mesh_files_per_region_SHA256")
    require(isinstance(expected_hashes,dict) and len(
        [key for key in expected_hashes if key.startswith("constant/")])==10,
        "10 original copied native polyMesh checksums missing")
    for rel,digest in expected_hashes.items():
        if rel.startswith("constant/"):
            require(hashfile(case/rel)==digest,
                    "original CASE B native polyMesh changed: "+rel)
    require(meta.get("final_10s_native_fields_sha256") is not None,
            "native final snapshot hashes not preserved")
    hashes=meta["final_10s_native_fields_sha256"]
    require(set(hashes)==set(b.FIELDS_10),
            "source native fields manifest mismatches full 10s stage contract")
    for rel,digest in hashes.items():
        require(hashfile(case/rel)==digest,
                "native 10s field changed since solver completion: "+rel)
    return meta,{"status":"NATIVE_C3D05_B_ORIGINAL_C14_3D_10S_SOURCE_VERIFIED",
                 "stage_report_sha256":hashfile(stage_path),
                 "controlDict_sha256":actual_control,
                 "metal_cells":EXPECTED["metal"],"mold_cells":EXPECTED["mold"],
                 "final_native_fields_sha256_verified":hashes,
                 "polyMesh_10_key_files_verified":True}


def saved_times(case: Path) -> list[tuple[float,str]]:
    found=[]
    for path in case.iterdir():
        if not path.is_dir() or path.is_symlink() or not re.fullmatch(
                r"(?:0|[1-9]\d*)(?:\.\d+)?",path.name):
            continue
        found.append((float(path.name),path.name))
    found.sort()
    require(len(found)>=2 and math.isclose(found[0][0],0,abs_tol=1e-11)
            and math.isclose(found[-1][0],10,rel_tol=0,abs_tol=1e-10),
            "native saved time state must cover initial 0 and completed final 10s")
    require(len(set(t for t,name in found))==len(found),
            "duplicate physical times in native folders")
    for (ta,_),(tb,_) in zip(found,found[1:]):
        require(tb>ta,"native time labels must be strictly ascending")
    return found


def triplet(values: list[float]) -> tuple[float,float,float]:
    require(bool(values),"empty native field")
    return min(values),math.fsum(values)/len(values),max(values)


def thresholds() -> tuple[float,float,float]:
    contract=json.loads(physics.CONTRACT.read_text(encoding="utf-8"))
    data=contract["C14_exact_values"]["solidification"]
    return float(data["Tsol_K"]),float(data["Tliq_K"]),float(data["L_J_kg"])


def native_snapshot_row(case: Path, t: float, label: str,
                        tsol: float, tliq: float) -> dict:
    metal=case/label/"metal"
    mold=case/label/"mold"
    temp=source_reader.scalar_field_values(metal/"T",EXPECTED["metal"])
    sand=source_reader.scalar_field_values(mold/"T",EXPECTED["mold"])
    alpha=source_reader.scalar_field_values(metal/"phaseChangeSource:alpha1",
                                             EXPECTED["metal"])
    pressure=source_reader.scalar_field_values(metal/"p_rgh",EXPECTED["metal"])
    require(min(temp)>0 and min(sand)>0,"unphysical non-positive absolute T native field")
    require(min(alpha)>=-1e-8 and max(alpha)<=1+1e-8,
            "phaseChangeSource:alpha1 out of physical fraction [0,1]")
    mt=triplet(temp)
    st=triplet(sand)
    af=triplet(alpha)
    pr=triplet(pressure)
    tl=sum(x<tliq for x in temp)
    ts=sum(x<tsol for x in temp)
    changed=sum(x<0.999 for x in alpha)
    require(ts<=tl,"solidus count greater than liquidus count")
    return {
        "time_s":t,
        "metal_T_min_K":mt[0],"metal_T_mean_K":mt[1],"metal_T_max_K":mt[2],
        "mold_T_min_K":st[0],"mold_T_mean_K":st[1],"mold_T_max_K":st[2],
        "metal_T_below_Tliq_cells":tl,"metal_T_below_Tsol_cells":ts,
        "metal_T_below_Tliq_percent_cells":100*tl/EXPECTED["metal"],
        "metal_T_below_Tsol_percent_cells":100*ts/EXPECTED["metal"],
        "alpha1_min":af[0],"alpha1_mean":af[1],"alpha1_max":af[2],
        "alpha1_below_0_999_cells":changed,
        "alpha1_below_0_999_percent_cells":100*changed/EXPECTED["metal"],
        "p_rgh_min_Pa":pr[0],"p_rgh_mean_Pa":pr[1],"p_rgh_max_Pa":pr[2]
    }


def event_bracket(rows: list[dict], condition) -> dict | None:
    for i,row in enumerate(rows):
        if condition(row):
            return {
                "first_observed_saved_time_s":row["time_s"],
                "previous_saved_time_s":rows[i-1]["time_s"] if i else None,
                "cannot_infer_exact_onset_within_saved_interval":True
            }
    return None


def build_summary(rows: list[dict],log_summary: dict,verified: dict,
                  case: Path,output: Path,tsol:float,tliq:float,L:float)->dict:
    require(rows and rows[0]["time_s"]==0 and rows[-1]["time_s"]==10,
            "missing first or final original 10s saved state")
    final=rows[-1]
    initial=rows[0]
    intervals=[]
    for before,after in zip(rows,rows[1:]):
        dt=after["time_s"]-before["time_s"]
        require(dt>0,"invalid saved snapshot interval")
        intervals.append({
            "from_s":before["time_s"],"to_s":after["time_s"],
            "metal_mean_T_drop_K_per_s":(before["metal_T_mean_K"]-after["metal_T_mean_K"])/dt,
            "alpha1_mean_decrease_per_s":(before["alpha1_mean"]-after["alpha1_mean"])/dt,
        })
    return {
        "schema":"C3D05_B_C14_3D_REAL_10S_READONLY_POSTRUN_V1",
        "status":STATUS,"created_utc":datetime.now(timezone.utc).isoformat(),
        "input_CFD_source_read_only":str(case),
        "output_separate_immutable_directory":str(output),
        "native_original_C14_metadata":verified,
        "original_C14_phase_parameters_reference":{
            "Tsol_K":tsol,"Tliq_K":tliq,"L_J_kg":L,
            "provenance":"unchanged source C14 contract, NOT JMatPro for QuickCup casts"},
        "all_native_log_diagnostics":log_summary,
        "saved_states":len(rows),"saved_times_s":[r["time_s"] for r in rows],
        "initial_native_fields_unweighted":initial,
        "final_native_fields_unweighted":final,
        "first_saved_cell_below_C14_Tliq":event_bracket(
            rows,lambda x:x["metal_T_below_Tliq_cells"]>0),
        "first_saved_cell_below_C14_Tsol":event_bracket(
            rows,lambda x:x["metal_T_below_Tsol_cells"]>0),
        "first_saved_alpha1_cell_below_0_999":event_bracket(
            rows,lambda x:x["alpha1_below_0_999_cells"]>0),
        "first_saved_mean_alpha1_below_0_999":event_bracket(
            rows,lambda x:x["alpha1_mean"]<0.999),
        "min_saved_alpha1":min(r["alpha1_min"] for r in rows),
        "max_saved_metal_Courant":log_summary["courant_max_over_all_logged_steps"],
        "max_saved_interval_mean_T_cooling_K_per_s":max(
            (v["metal_mean_T_drop_K_per_s"] for v in intervals),default=0),
        "max_saved_interval_alpha1_mean_decrease_per_s":max(
            (v["alpha1_mean_decrease_per_s"] for v in intervals),default=0),
        "native_CFD_solved_full_10s":True,
        "native_C14_solidificationMeltingSource_selected":True,
        "any_native_alpha1_cell_below_0_999_at_saved_times":any(
            r["alpha1_below_0_999_cells"]>0 for r in rows),
        "phase_field_mean_is_cell_based_unweighted":True,
        "volume_weighted_solid_fraction_computed":False,
        "latent_heat_energy_balance_computed":False,
        "boundary_heat_flux_and_energy_conservation_verified":False,
        "pressure_momentum_flux_balance_verified":False,
        "grid_time_step_convergence_verified":False,
        "JMatPro_QuickCup_physical_validation":False,
        "recalescence_proven":False,
        "contraction_feeding_physics_enabled":False,
        "safety_notes":[
            "This source-validated original C14 reference on authentic B HEX8 is NOT a real-material JMatPro/QuickCup validation.",
            "alpha1 is the C14 model's computed liquid fraction; physical latent heat and energy conservation cannot be inferred solely from alpha1.",
            "Threshold T < Tliq is NOT independently sufficient to demonstrate phase-change energy release.",
            "First observed phase change is bracketed by SAVED timestamps, not exact continuous onset.",
            "A cell-count mean does not equal a volume-/mass-weighted physical solid fraction on nonuniform HEX8.",
            "Uses real existing model results and solver log only; no new OpenFOAM solver run or mutation of CFD data."
        ],
        "saved_snapshot_interval_rates":intervals
    }


def audit(case:Path,out:Path) -> dict:
    case=case.expanduser().absolute()
    out=out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(),
            "existing analysis destination preserved; no overwrite "+str(out))
    require(out!=case and out not in case.parents and case not in out.parents,
            "analysis output must be separate from immutable CFD directory")
    stage,verified=validated_mesh_and_stage(case)
    native_log=case/LOG
    require(hashfile(native_log)==stage.get("solver_log_sha256"),
            "native solver log SHA256 does not match completed stage report")
    log_data=source_reader.parse_full_log(native_log.read_text(
        encoding="utf-8",errors="replace"))
    require(log_data["time_last_s"]==10.0
            and log_data["native_end_found"] is True
            and log_data["selected_C14_fluid_solid_phase_model"] is True,
            "log does not prove complete 10s original C14 fluid-solid solution")
    time_labels=saved_times(case)
    tsol,tliq,latent=thresholds()
    rows=[]
    for i,(t,label) in enumerate(time_labels,1):
        rows.append(native_snapshot_row(case,t,label,tsol,tliq))
        if i==1 or i%10==0 or i==len(time_labels):
            print(f"C3D05_B_POSTRUN_READONLY_PROGRESS: {i}/{len(time_labels)} "
                  f"saved times audited; latest t={t:g}s; NO_CFD_NO_REWRITE",
                  flush=True)
    report=build_summary(rows,log_data,verified,case,out,tsol,tliq,latent)
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(
            dir=str(out.parent),prefix="."+out.name+".staging.") as temp:
        new=Path(temp)/"complete"
        new.mkdir()
        with (new/CSV).open("x",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        (new/JSON).write_text(json.dumps(report,indent=2,
                                ensure_ascii=False)+"\n",encoding="utf-8")
        manifests={
            "schema":"C3D05_B_C14_3D_REAL_10S_READONLY_POSTRUN_MANIFEST_V1",
            "native_log_sha256":hashfile(native_log),
            "native_stage_report_sha256":hashfile(case/REPORT),
            "analysis_csv_sha256":hashfile(new/CSV),
            "analysis_json_sha256":hashfile(new/JSON),
            "source_CFD_read_only":str(case),
            "cannot_assert_original_field_hashes_for_unlisted_saved_intervals":True
        }
        (new/MANIFEST).write_text(json.dumps(manifests,indent=2)+"\n",
                                 encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "destination appeared concurrently: preserve original")
        new.rename(out)
    return report


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",type=Path,default=DEFAULT_CASE)
    ap.add_argument("--out",type=Path,default=DEFAULT_OUT)
    args=ap.parse_args()
    try:
        report=audit(args.case,args.out)
        print(json.dumps({
            "status":report["status"],
            "out":report["output_separate_immutable_directory"],
            "native_10s_complete":report["native_CFD_solved_full_10s"],
            "saved_snapshots":report["saved_states"],
            "first_C14_Tliq_crossing":report["first_saved_cell_below_C14_Tliq"],
            "first_alpha1_below_0_999":report["first_saved_alpha1_cell_below_0_999"],
            "any_saved_alpha1_change":report["any_native_alpha1_cell_below_0_999_at_saved_times"],
            "final_alpha1_mean_cell_based":report["final_native_fields_unweighted"]["alpha1_mean"],
            "min_saved_alpha1":report["min_saved_alpha1"],
            "max_Courant_all_logged_steps":report["max_saved_metal_Courant"],
            "physical_energy_or_experiment_accepted":False
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        print("C3D05_B_C14_POSTRUN_READONLY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
