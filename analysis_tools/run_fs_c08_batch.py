#!/usr/bin/env python3
"""Run independent real FS-C08 CFD variants concurrently with a single build.
Each worker is serial OpenFOAM, not MPI decomposition. Fixed time step only.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import sys

from run_fs_c08_real_cfd import (
    BASE_MODULE, build_native_library, execute, native_library_lock, write_report,
)

VARIANTS = (
    ("legacy_separate", "legacy", "separate", "incremental"),
    ("refresh_separate", "refreshBeforePressure", "separate", "incremental"),
    ("legacy_weighted", "legacy", "phaseWeighted", "incremental"),
    ("refresh_weighted", "refreshBeforePressure", "phaseWeighted", "incremental"),
)

FLUX_VARIANTS = (
    ("refresh_reference", "refreshBeforePressure", "separate", "incremental"),
    ("refresh_total_upwind", "refreshBeforePressure", "separate", "totalUpwind"),
    ("refresh_no_ddt_corr", "refreshBeforePressure", "separate", "incrementalNoDdtCorr"),
    ("refresh_total_no_ddt_corr", "refreshBeforePressure", "separate", "totalUpwindNoDdtCorr"),
)

ENERGY_VARIANTS = (
    ("energy_reference", "refreshBeforePressure", "separate", "incremental", "legacy"),
    ("energy_old_gas", "refreshBeforePressure", "separate", "incremental", "oldGas"),
    ("energy_current_liquid", "refreshBeforePressure", "separate", "incremental", "currentLiquid"),
    ("energy_old_gas_current_liquid", "refreshBeforePressure", "separate", "incremental", "oldGasCurrentLiquid"),
)

SUPPORT_VARIANTS = tuple(
    ("support_"+mode, "refreshBeforePressure", "separate", "incremental", "legacy", mode)
    for mode in ("trial","oldLiquid","oldGas","oldBoth")
)

TEMPORAL_VARIANTS = tuple(
    ("temporal_"+name, "refreshBeforePressure", "separate", "incremental", "legacy", "trial")
    for name in ("double_dt","reference","half_dt","quarter_dt")
)
TEMPORAL_FACTORS = {"temporal_double_dt":2.0,"temporal_reference":1.0,
                    "temporal_half_dt":0.5,"temporal_quarter_dt":0.25}

EOS_REFERENCE_K=109.7e9/(1+9e-5*1.9*1811)
EOS_MODULI={"eos_incompressible":0.0,"eos_half_K":0.5*EOS_REFERENCE_K,
            "eos_reference_K":EOS_REFERENCE_K,"eos_double_K":2*EOS_REFERENCE_K}
EOS_VARIANTS=tuple((name,"refreshBeforePressure","separate","incremental","legacy","trial")
                   for name in EOS_MODULI)

EOS_TEMPORAL_VARIANTS=tuple(
    ("eos_"+v[0], *v[1:]) for v in TEMPORAL_VARIANTS
)
EOS_TEMPORAL_FACTORS={"eos_"+name:factor for name,factor in TEMPORAL_FACTORS.items()}

ENERGY_RESIDUAL_TOLERANCES={"thermal_native":0.0,"thermal_tol10":1e-10,
                           "thermal_tol12":1e-12,"thermal_tol14":1e-14}
THERMAL_VARIANTS=tuple((name,"refreshBeforePressure","separate","incremental","legacy","trial")
                       for name in ENERGY_RESIDUAL_TOLERANCES)

def bulk_modulus(name):
    return EOS_REFERENCE_K if name in EOS_TEMPORAL_FACTORS or name in ENERGY_RESIDUAL_TOLERANCES else EOS_MODULI.get(name,0.0)

METRICS = (
    "maxU_m_s", "pMax_Pa", "metalVolume_m3", "solidMass_kg",
    "metalMassResidual_kg", "gasContinuityDefect_kg",
    "totalInternalEnergyEquationBalance_J", "localEnergyRelativeL1",
    "pressureVolumeRate_m3_s", "thermalVolumeRate_m3_s", "phaseVolumeRate_m3_s", "pMin_Pa",
)

def numeric(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None

def summarize(name, coupling, mobility, flux_mode, energy_mode, support_mode, report, case_dt, case_steps, compact=False):
    ledger=report.get("transient_ledger", {})
    last=ledger.get("last_complete_state") or {}
    return {
        "variant": name, "matrix": coupling, "phase_mobility": mobility,
        "momentum_flux_mode": flux_mode,
        "energy_donor_mode": energy_mode,
        "pressure_transport_support": support_mode,
        "metal_bulk_modulus_pa":report.get("metal_bulk_modulus_pa",bulk_modulus(name)),
        "metal_eos_records":report.get("metal_eos_records",[]),
        "energy_linear_tolerance":ENERGY_RESIDUAL_TOLERANCES.get(name,0.0),
        "thermal_residual_first2":report.get("thermal_residual_control_records",[])[:2],
        "thermal_residual_last3":report.get("thermal_residual_control_records",[])[-3:],
        "caloric_pressure_dependence_validated":False,
        "fixed_dt_s": case_dt, "scheduled_steps": case_steps,
        "requested_end_time_s": case_dt*case_steps,
        "momentum_force_first4": report.get("momentum_force_records", [])[:4],
        "momentum_force_last4": report.get("momentum_force_records", [])[-4:],
        "momentum_consistency_first2": report.get("momentum_consistency_records", [])[:2],
        "momentum_consistency_last2": report.get("momentum_consistency_records", [])[-2:],
        "startup_pressure_attribution_records": report.get("startup_pressure_attribution_records", []),
        "initial_projection_jacobian_records": report.get("initial_projection_jacobian_records", []),
        "native_diagnostic_tail_on_failure": report.get("native_diagnostic_tail", [])[-10:] if not report.get("real_CFD_completed") else [],
        "pressure_transport_support_records_first5": report.get("pressure_transport_support_records", [])[:5],
        "pressure_transport_support_records_last3": report.get("pressure_transport_support_records", [])[-3:],
        "phase_energy_split_records_last3": report.get("phase_energy_split_records", [])[-3:],
        "phase_energy_split_records_first3": report.get("phase_energy_split_records", [])[:3],
        "interface_transport_records": (report.get("interface_transport_records", [])[:2]+report.get("interface_transport_records", [])[-2:] if compact else report.get("interface_transport_records", [])),
        "status": report.get("status", "UNKNOWN"),
        "completed": bool(report.get("real_CFD_completed")),
        "accepted_pressure_records": report.get("accepted_pressure_records", 0),
        "complete_ledger_steps": ledger.get("complete_native_ledger_times", 0),
        "saved_steps": len(report.get("saved_positive_times_s", [])),
        "saved_positive_times_s": report.get("saved_positive_times_s", []),
        "last_saved_time_s": report.get("latest_saved_time_s"),
        "last_ledger_time_s": last.get("time_s"),
        **{key: last.get(key) for key in METRICS},
        "max_accepted_volume_residual": report.get("native_coupled_volume_gate", {}).get("max_accepted_volume_residual"),
        "error": report.get("first_run_error") or report.get("budget_gate_error")
                 or report.get("first_compiler_error") or report.get("batch_worker_error"),
        "ledger_issues": ledger.get("issues", []),
        "diagnostics": report.get("diagnostics"),
        "case": report.get("output_case"),
        "ledger_csv": ledger.get("csv"),
        "global_energy_verified": False, "physical_shrinkage_validated": False,
    }

def common_time_comparison(rows, dt):
    """Compare only complete ledgers at times actually saved by every case.
    Include no interpolation, no missing data imputation.
    """
    histories=[]
    for row in rows:
        file=row.get("ledger_csv")
        by_step={}
        saved={round(t/dt) for t in row["saved_positive_times_s"]
               if abs(t-round(t/dt)*dt)<=max(1e-14,dt*1e-6)}
        if file and Path(file).is_file():
            with Path(file).open(newline="",encoding="utf-8") as fp:
                for rec in csv.DictReader(fp):
                    t=numeric(rec.get("time_s"))
                    if t is None or rec.get("all_native_ledgers_present")!="True":
                        continue
                    step=round(t/dt)
                    if step<1 or step not in saved or abs(t-step*dt)>max(1e-14,dt*1e-6):
                        continue
                    by_step[step]={key:numeric(rec.get(key)) for key in METRICS}
        histories.append(by_step)
    shared=set.intersection(*(set(h) for h in histories)) if histories else set()
    return [{"step": step, "comparison_tick":step, "time_s": step*dt,
             "actual_steps":{row["variant"]:round(step*dt/row["fixed_dt_s"]) for row in rows},
             "variants": {row["variant"]: h[step] for row,h in zip(rows,histories)}}
            for step in sorted(shared)]

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=Path.home()/"OpenFOAM/FS_C07_RUNS/FS_C07_THERMAL_20261123T183217Z_72da1bf4")
    parser.add_argument("--material",type=Path,default=BASE_MODULE.parent/"materials/B14_reference/fsC08Material")
    parser.add_argument("--jobs",type=int,default=2,choices=(1,2,3,4))
    parser.add_argument("--steps",type=int,default=10)
    parser.add_argument("--dt",type=float,default=1e-6)
    parser.add_argument("--timeout-minutes",type=int,default=120)
    parser.add_argument("--suite",choices=("mobility","flux","energy","support","temporal","eos","eos_temporal","thermal_residual"),default="support")
    parser.add_argument("--compact-output",action="store_true",help="Print concise clipboard report; full JSON/CSV and native logs remain on disk")
    args=parser.parse_args(argv)
    variants=SUPPORT_VARIANTS if args.suite=="support" else tuple(v+("trial",) for v in (ENERGY_VARIANTS if args.suite=="energy" else tuple(v+("legacy",) for v in (FLUX_VARIANTS if args.suite=="flux" else VARIANTS))))
    if not 1<=args.steps<=1000 or not math.isfinite(args.dt) or args.dt<=0 or args.timeout_minutes<1:
        parser.error("invalid fixed-step controls or timeout")
    if args.suite in ("temporal","eos_temporal"):
        if args.steps%2 or args.steps*4>1000:
            parser.error("temporal suite requires an even reference step count <=250")
        variants=EOS_TEMPORAL_VARIANTS if args.suite=="eos_temporal" else TEMPORAL_VARIANTS
    if args.suite=="eos":
        variants=EOS_VARIANTS
    if args.suite=="thermal_residual":
        variants=THERMAL_VARIANTS
    def controls(name):
        factor=TEMPORAL_FACTORS.get(name,EOS_TEMPORAL_FACTORS.get(name,1.0))
        return args.dt*factor, int(args.steps/factor)
    comparison_dt=min(controls(v[0])[0] for v in variants)
    source=args.source.expanduser().resolve()
    material=args.material.expanduser().resolve()
    if not source.is_dir() or not material.is_file():
        parser.error(f"source/material missing: {source} | {material}")
    if os.environ.get("WM_PROJECT_VERSION")!="14" or not shutil.which("foamMultiRun"):
        parser.error("load OpenFOAM Foundation14 in WSL")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+secrets.token_hex(4)
    root=Path.home()/"OpenFOAM/FS_C08_DIAGNOSTICS"/("FS_C08_BATCH_"+stamp)
    cases=Path.home()/"OpenFOAM/FS_C08_COUPLED_RUNS"
    root.mkdir(parents=True,exist_ok=False)
    summary_path=root/"FS_C08_BATCH_SUMMARY.json"
    batch={"schema":"fs-c08-native-batch-v1","status":"BUILDING","dt_s":args.dt,
           "steps":args.steps,"requested_parallel_jobs":args.jobs,"suite":args.suite,
           "reference_dt_s":args.dt,"reference_steps":args.steps,
           "common_target_time_s":args.dt*args.steps,
           "comparison_tick_s":comparison_dt,
           "per_variant_controls":{v[0]:{"dt_s":controls(v[0])[0],"steps":controls(v[0])[1]} for v in variants},
           "adaptive_timestep":False,
           "per_variant_bulk_modulus_pa":{v[0]:bulk_modulus(v[0]) for v in variants},
           "global_energy_verified":False,"physical_shrinkage_validated":False,
           "variants":[]}
    write_report(summary_path,batch)
    print("FS-C08 BATCH:",root,flush=True)
    try:
        with native_library_lock():
            receipt=build_native_library(root/"native_wmake.log")
            batch["build"]=receipt
            if not receipt["verified"]:
                batch["status"]="BUILD_FAILED"
                write_report(summary_path,batch)
                print(json.dumps(batch,indent=2),flush=True)
                return 2
            batch["status"]="RUNNING"
            write_report(summary_path,batch)
            def worker(variant):
                name,coupling,mobility,flux_mode,energy_mode,support_mode=variant
                case_dt,case_steps=controls(name)
                output=cases/("FS_C08_COUPLED_"+stamp+"_"+name)
                diag=root/name
                print("START",name,flush=True)
                try:
                    report=execute(source,material,output,diag,args.timeout_minutes,
                        True,case_dt,case_steps,"linear",coupling,mobility,flux_mode,energy_mode,support_mode,bulk_modulus(name),ENERGY_RESIDUAL_TOLERANCES.get(name,0.0),
                        verified_batch_build=receipt)
                except Exception as exc:
                    # One failed variant must not cancel the remaining cases.
                    report_file=diag/"FS_C08_REAL_CFD_REPORT.json"
                    try:
                        report=json.loads(report_file.read_text(encoding="utf-8"))
                    except (OSError,ValueError):
                        report={}
                    report.update(status="FS_C08_BATCH_WORKER_ERROR",
                        real_CFD_completed=False,batch_worker_error=str(exc),
                        diagnostics=str(diag),output_case=str(output))
                    write_report(report_file,report)
                result=summarize(name,coupling,mobility,flux_mode,energy_mode,support_mode,report,case_dt,case_steps,args.suite in ("temporal","eos","eos_temporal","thermal_residual"))
                print("FINISH",name,result["status"],
                      "saved steps",result["saved_steps"],flush=True)
                return result
            finished={}
            with ThreadPoolExecutor(max_workers=args.jobs) as pool:
                futures={pool.submit(worker,v):v[0] for v in variants}
                for future in as_completed(futures):
                    row=future.result()
                    finished[row["variant"]]=row
                    batch["variants"]=[finished[v[0]] for v in variants if v[0] in finished]
                    write_report(summary_path,batch)
            batch["common_saved_time_comparison"]=common_time_comparison(batch["variants"],comparison_dt)
            completed=[row for row in batch["variants"] if row["completed"]]
            batch["completed_variants_common_saved_time_comparison"]=common_time_comparison(completed,comparison_dt)
            batch["completed_variants_compared"]=[row["variant"] for row in completed]
            # Preserve peaks even if a case is rejected before the target.
            # These are maxima/minima over saved complete accepted ledgers,
            # not over rejected trials, or an estimate of continuous peaks.
            batch["accepted_history_extrema"]={}
            for row in batch["variants"]:
                hist=common_time_comparison([row],comparison_dt)
                name=row["variant"]
                extrema={}
                for key,mode in (("maxU_m_s",max),("pMax_Pa",max),("pMin_Pa",min),
                                 ("localEnergyRelativeL1",max)):
                    valid=[(h["variants"][name][key],h["time_s"]) for h in hist
                           if h["variants"][name].get(key) is not None]
                    if valid:
                        value,t=mode(valid,key=lambda pair:pair[0])
                        extrema[key]={"value":value,"time_s":t}
                batch["accepted_history_extrema"][name]=extrema
            if args.suite=="eos_temporal":
                shared=batch["common_saved_time_comparison"] or batch["completed_variants_common_saved_time_comparison"]
                target=batch["common_target_time_s"]
                batch["milestone_comparison_scope"]=("all_variants" if batch["common_saved_time_comparison"]
                    else "completed_variants_only")
                batch["milestone_comparison"]=[h for h in shared if any(
                    abs(h["time_s"]-fraction*target)<=max(1e-14,comparison_dt*1e-6)
                    for fraction in (0.1,0.2,0.5,1.0))]

            batch["status"]="COMPLETED_ALL_VARIANTS" if all(r["completed"] for r in batch["variants"]) else "COMPLETED_WITH_REJECTED_VARIANTS"
            batch["passed_variants"]=sum(r["completed"] for r in batch["variants"])
            write_report(summary_path,batch)
    except (RuntimeError,OSError,ValueError) as exc:
        batch.update(status="BATCH_ERROR",error=str(exc))
        write_report(summary_path,batch)
        print("FS-C08 BATCH ERROR:",exc,file=sys.stderr)
        return 2
    with (root/"FS_C08_BATCH_SUMMARY.csv").open("w",newline="",encoding="utf-8") as fp:
        writer=csv.DictWriter(fp,fieldnames=list(batch["variants"][0]))
        writer.writeheader()
        writer.writerows(batch["variants"])
    print("FS-C08 BATCH SUMMARY:",summary_path,flush=True)
    # Keep terminal output compact, while the report retains all time histories.
    excluded={"common_saved_time_comparison","completed_variants_common_saved_time_comparison"}
    printable={key:value for key,value in batch.items() if key not in excluded}
    if args.compact_output:
        # This is a presentation filter only, not an acceptance test.
        keys=("variant","fixed_dt_s","scheduled_steps","metal_bulk_modulus_pa",
              "metal_eos_records","energy_linear_tolerance","thermal_residual_first2","thermal_residual_last3","status","completed","saved_steps","complete_ledger_steps",
              "last_saved_time_s","max_accepted_volume_residual","error","ledger_issues",
              "diagnostics","case","ledger_csv","native_diagnostic_tail_on_failure",
              *METRICS)
        printable["variants"]=[{k:row.get(k) for k in keys} for row in batch["variants"]]
        printable["completed_variant_common_times_count"]=len(batch["completed_variants_common_saved_time_comparison"])
    print(json.dumps(printable,indent=2),flush=True)
    if batch["common_saved_time_comparison"]:
        print("LAST COMMON SAVED TIME:",json.dumps(batch["common_saved_time_comparison"][-1]),flush=True)
    if batch["completed_variants_common_saved_time_comparison"] and not batch["common_saved_time_comparison"]:
        print("LAST COMMON TIME OF COMPLETED VARIANTS ONLY:",json.dumps(batch["completed_variants_common_saved_time_comparison"][-1]),flush=True)
    return 0 if batch["passed_variants"]==len(variants) else 2

if __name__=="__main__":
    raise SystemExit(main())
