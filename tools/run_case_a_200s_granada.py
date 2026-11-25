#!/usr/bin/env python3
"""Case A only: preserve uncapped failure, reuse matching MPI evidence,
run authorized capped pilot then 200 s, analyze and publish completed run.
No B/2D runs; no changes to previous inputs or results.
"""
from __future__ import annotations
import argparse
import csv
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

import run_adaptive_campaign_200s as adaptive
import run_adaptive_mpi_campaign as mpi
import transfer_campaign_200s as transfer

NAME="C14-3DA-200s"
REPORT=adaptive.REPORT
HOME=adaptive.HOME
OLD=adaptive.ROOT/NAME
OUT=HOME/"C3D04_A_GRANADA_200S_01"
need=adaptive.need
read=adaptive.read
dump=adaptive.dump
NUM=adaptive.NUM
RHO,CP,L,V=6820.,827.,228600.,4.7921447006662436e-5

def failure(case):
    p=case/"log.foamMultiRun"
    report=read(case/REPORT) if (case/REPORT).is_file() else {}
    data={"case":str(case),"status":report.get("status"),"report_error":report.get("error"),
          "solver_completed":report.get("solver_completed",False),"log_exists":p.is_file()}
    if not p.is_file():return data
    t=dt=co=None;fatal=[];negative=[];n=0
    with p.open(errors="replace") as f:
        for line in f:
            m=re.match(r"^\s*Time\s*=\s*("+NUM+r")\s*s?\s*$",line)
            if m:t=float(m[1]);n+=1
            m=re.search(r"deltaT\s*=\s*("+NUM+r")",line)
            if m:dt=float(m[1])
            m=re.search(r"Courant Number.*?max:\s*("+NUM+r")",line)
            if m:co=float(m[1])
            if "FOAM FATAL" in line:
                fatal.append({"time_s":t,"deltaT_s":dt,"max_Courant":co,"line":line.strip()})
            m=re.search(r"Negative initial temperature T0:\s*("+NUM+r")",line)
            if m:negative.append({"T0_K":float(m[1]),"time_s":t,"deltaT_s":dt,"max_Courant":co})
    return {**data,"log_sha256":transfer.sha(p),"reported_steps":n,"last_reported_time_s":t,
            "last_deltaT_s":dt,"last_max_Courant":co,"fatal_markers":fatal,
            "negative_thermo_initial_temperature":negative,
            "interpretation":"Negative thermo inversion initial temperature is a failure symptom, not proof of a specific cause or measured cell temperature. Courant control alone does not ensure thermal/source convergence."}

def matching(r,ranks,cap,end):
    return (r.get("validation_class")==mpi.EXPERIMENT and r.get("mpi_ranks")==ranks
            and r.get("max_co")==.25 and r.get("max_dt_s")==cap and r.get("target_time_s")==end)

def existing(ranks,cap,end):
    hits=[]
    for p in sorted(mpi.ROOT.glob("*/"+NAME+"/"+REPORT)):
        r=read(p)
        if matching(r,ranks,cap,end):hits.append((p.parent,r))
    return hits

def pick_or_run(url,ranks,cap,end,retry):
    hits=existing(ranks,cap,end)
    success="MPI_PILOT_PASS" if end==3 else "SOLVER_COMPLETE_ADAPTIVE_AUDITED"
    ready=[(p,r) for p,r in hits if r.get("status")==success and r.get("solver_completed")
           and abs(r.get("final_time_s",-1)-end)<1e-7 and r.get("observed_mpi_ranks")==ranks]
    if ready:
        p,r=ready[-1]
        need((p/"log.foamMultiRun").is_file(),"completed run log missing")
        print("REUSE_COMPLETE",p,flush=True);return p,r
    # A complete solver with a pending/failed audit must not trigger a rerun.
    complete=[(p,r) for p,r in hits if r.get("solver_completed")]
    if complete:
        p,r=complete[-1];dump(OUT/"existing_solver_audit_pending.json",failure(p))
        raise RuntimeError("existing completed solver requires audit recovery, no new CFD: "+str(p))
    if hits and not retry:
        p,r=hits[-1];dump(OUT/"preserved_matching_attempt.json",failure(p))
        raise RuntimeError("existing matching attempt preserved; inspect "+str(p)+" before explicit retry")
    tag=format(cap,".15g").replace(".","p")
    parent=Path(tempfile.mkdtemp(prefix=f"granada-A-r{ranks}-{end}s-dt{tag}-",dir=mpi.ROOT))
    case=parent/NAME;case.mkdir()
    print("NEW_ISOLATED_A",case,flush=True)
    try:
        r=mpi.prepare(case,url,ranks,end,cap)
        mpi.run(case,r,ranks,end)
    except BaseException:
        dump(OUT/f"failure_{end}s_{parent.name}.json",failure(case));raise
    r=read(case/REPORT);need(r["status"]==success,"native audit incomplete")
    return case,r

def series(case,name,filename,width):
    p=case/"postProcessing/metal"/name/"0"/filename
    rows=list(adaptive.rows(p))
    need(len(rows)==2001 and all(len(v)==width and abs(v[0]-i/10)<5e-5 for i,v in enumerate(rows)),"native series mismatch "+str(p))
    return p,rows

def analyze(case,r):
    need(r["status"]=="SOLVER_COMPLETE_ADAPTIVE_AUDITED" and r["runtime_audit"]["native_runtime_coverage_complete"],"complete audited 200s CFD required")
    loghash=transfer.sha(case/"log.foamMultiRun")
    dest=case/"analysis_results"/"granada_A_200s"
    if dest.exists():
        saved=read(dest/"REPORT.json")
        need(saved["solver_log_sha256"]==loghash and all(transfer.sha(dest/k)==v for k,v in saved["derived_sha256"].items()),"existing analysis differs")
        return dest,saved
    names={"alpha":("metalMeanLiquidFraction","volFieldValue.dat",2),
           "H":("metalSensibleEnthalpy","volFieldValue.dat",2),
           "latent":("metalLatentHeatPower","volFieldValue.dat",2),
           "Q":("metalBoundaryEnergyPower","surfaceFieldValue.dat",4),
           "top":("metalTopEnergyPower","surfaceFieldValue.dat",4),
           "contact":("metalMoldEnergyPower","surfaceFieldValue.dat",4),
           "cooling":("metalMeanCoolingRate","volFieldValue.dat",2)}
    sources={};s={}
    for k,args in names.items():
        p,s[k]=series(case,*args);sources[str(p.relative_to(case))]=transfer.sha(p)
    pp=case/"postProcessing/metal/temperatureProbe/0"
    probes={k:list(adaptive.rows(pp/k)) for k in ("T","U","phaseChangeSource:alpha1","rho","p_rgh")}
    for k in probes:sources[str((pp/k).relative_to(case))]=transfer.sha(pp/k)
    n=r["solver_steps"]+1
    need(all(len(v)==n for v in probes.values()),"native probe count mismatch")
    # Align on the actual recorded adaptive time series, never interpolate.
    need(all(all(abs(a[0]-b[0])<=5.1e-4 for a,b in zip(probes["T"],v)) for v in probes.values()),"probe alignment mismatch")
    need(all(len(row)==2 and row[1]>0 for row in probes["T"]),"invalid probe T")
    need(all(len(row)==4 for row in probes["U"]),"invalid U width")
    need(all(-1e-6<=row[1]<=1+1e-6 for row in s["alpha"]),"mean alpha outside bounds")
    rows=[];balances={}
    for start in (0,1):
        q=p=0.
        for i in range(start,2001):
            if i>start:
                q+=.05*(s["Q"][i-1][3]+s["Q"][i][3]);p+=.05*(s["latent"][i-1][1]+s["latent"][i][1])
            h=s["H"][start][1]-s["H"][i][1]
            l=RHO*L*V*(s["alpha"][start][1]-s["alpha"][i][1])
            row={"start_s":start/10,"time_s":i/10,"T_mean_reconstructed_K":1500+(s["H"][i][1]-s["H"][0][1])/(RHO*CP*V),
                 "solid_fraction_mean":1-s["alpha"][i][1],"latent_power_W":s["latent"][i][1],
                 "contact_power_W":s["contact"][i][3],"top_power_W":s["top"][i][3],"cooling_mean_K_s":s["cooling"][i][1],
                 "outward_energy_J":q,"sensible_release_J":h,"latent_inventory_release_J":l,"latent_power_integral_J":p,
                 "inventory_residual_J":q-h-l,"power_residual_J":q-h-p}
            rows.append(row)
        balances[str(start/10)]=rows[-1]
    def cross(rows,threshold):
        i=next((i for i,x in enumerate(rows) if x[1]<threshold),None)
        return None if i is None else [rows[max(i-1,0)][0],rows[i][0]]
    T=probes["T"];A=probes["phaseChangeSource:alpha1"]
    peak=max(s["latent"],key=lambda x:x[1])
    dest.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".analysis-",dir=dest.parent) as tmp:
        work=Path(tmp)/"result";work.mkdir()
        with (work/"thermal_energy_2001.csv").open("x",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        with (work/"probe_native.csv").open("x",newline="") as f:
            w=csv.writer(f);w.writerow(("recorded_time_s","T_K","Ux_m_s","Uy_m_s","Uz_m_s","speed_m_s","alphaL","rho_kg_m3","p_rgh_Pa"))
            for i,t in enumerate(T):
                u=probes["U"][i][1:];w.writerow((t[0],t[1],*u,math.hypot(*u),A[i][1],probes["rho"][i][1],probes["p_rgh"][i][1]))
        result={"status":"A_200S_NATIVE_SCIENTIFIC_ANALYSIS_READY","solver_log_sha256":loghash,
                "solver_steps":r["solver_steps"],"final_time_s":200,"probe_native_samples":n,"volume_states":201,
                "diagnostic_states":2001,"source_sha256":sources,"final_probe_T_K":T[-1][1],
                "final_probe_alphaL":A[-1][1],"final_volume_solid_fraction":1-s["alpha"][-1][1],
                "first_probe_below_liquidus_interval_s":cross(T,1473),"first_probe_below_solidus_interval_s":cross(T,1423),
                "first_probe_alpha_below_one_interval_s":cross(A,1),"peak_saved_latent_power_W":peak[1],
                "peak_saved_latent_time_s":peak[0],"metal_saved_state_energy_by_start":balances,
                "derived_sha256":{p.name:transfer.sha(p) for p in work.iterdir()},
                "discrete_energy_conservation_verified":False,"experimental_validation":False,
                "limitations":["Adaptive actual probe times retained; no fixed-grid interpolation.",
                    "Reconstructed mean T and nominal inventory use constant C14 properties; not cellwise T.",
                    "Saved .1s trapezoids, not complete discrete energy or bilateral mold balance.",
                    "Solidus crossing does not prove complete solidification."]}
        dump(work/"REPORT.json",result);work.rename(dest)
    return dest,result

def publish(case,r,analysis,url,ranks,cap):
    tag=format(cap,".15g").replace(".","p")
    branch=f"results/campaign-200s-adaptive-mpi-r{ranks}-Co025-dt{tag}-granada-v1/{NAME}"
    existing_manifest=transfer.complete_manifest(url,branch)
    loghash=transfer.sha(case/"log.foamMultiRun")
    if existing_manifest is not None:
        need(existing_manifest["solver_log_sha256"]==loghash,"published branch belongs to different CFD")
        return branch
    with tempfile.TemporaryDirectory(prefix="archive-A-",dir=OUT) as tmp:
        p=Path(tmp);archive=p/"result.tar.gz"
        with transfer.deterministic_tar(archive) as tar:
            for name in ("postProcessing","logs",REPORT,adaptive.TIMELINE,"log.foamMultiRun","log.foamLog","log.decomposePar","log.reconstructPar"):
                q=case/name
                if q.exists():transfer.add(tar,q,NAME+"/"+name)
            transfer.add(tar,analysis,NAME+"/analysis_results/granada_A_200s")
        transfer.publish(url,branch,archive,{"kind":"adaptive_scientific_results","case":NAME,
            "time_mode":"adaptive_capped","mpi_ranks":ranks,"max_co":.25,"max_dt_s":cap,
            "validation_class":mpi.EXPERIMENT,"physical_validation":False,"solver_steps":r["solver_steps"],
            "final_time_s":200,"solver_log_sha256":loghash,"report_sha256":transfer.sha(case/REPORT),
            "analysis_report_sha256":transfer.sha(analysis/"REPORT.json"),"native_runtime_coverage_complete":True,
            "volume_fields_included":False},p/"git",case=case)
    m=transfer.complete_manifest(url,branch)
    need(m is not None and m["solver_log_sha256"]==loghash,"remote archive verification failed")
    return branch

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo",type=Path,default=HOME/"MasterProject")
    ap.add_argument("--ranks",type=int,choices=(1,8,10),default=8)
    ap.add_argument("--max-dt",type=float,default=.025)
    ap.add_argument("--retry-preserved",action="store_true",help="explicitly permit a fresh attempt after a matching failed run")
    ap.add_argument("--inspect-only",action="store_true")
    ap.add_argument("--publish",action="store_true")
    a=ap.parse_args()
    need(math.isfinite(a.max_dt) and .001<=a.max_dt<=1,"invalid cap")
    need(not OUT.is_symlink() and not mpi.ROOT.is_symlink() and not adaptive.ROOT.is_symlink(),"unsafe root")
    OUT.mkdir(exist_ok=True);mpi.ROOT.mkdir(exist_ok=True);adaptive.ROOT.mkdir(exist_ok=True)
    evidence=failure(OLD);dump(OUT/"uncapped_failure.json",evidence)
    print(json.dumps(evidence,indent=2),flush=True)
    if a.inspect_only:
        for end in (3,200):
            for p,r in existing(a.ranks,a.max_dt,end):print(json.dumps(failure(p),indent=2))
        return
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(a.ranks<=len(os.sched_getaffinity(0)),"insufficient available logical CPUs")
    url=transfer.root_url(a.repo)
    with (adaptive.ROOT/".execution.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        summary={"case":NAME,"status":"EXPERIMENTAL_CAPPED_200S_PENDING","maxCo":.25,"maxDeltaT_s":a.max_dt,
                 "mpi_ranks":a.ranks,"uncapped_failure":evidence,"physical_validation":False}
        try:
            # A valid full run needs no new pilot or CFD.
            full=existing(a.ranks,a.max_dt,200)
            if not any(r.get("status")=="SOLVER_COMPLETE_ADAPTIVE_AUDITED" for _,r in full):
                pilot,pr=pick_or_run(url,a.ranks,a.max_dt,3,a.retry_preserved)
                summary["pilot"]={"path":str(pilot),"status":pr["status"],"steps":pr["solver_steps"],
                                  "statistics":pr.get("adaptive_statistics")}
                dump(OUT/"GRANADA_A_STATUS.json",summary)
            case,r=pick_or_run(url,a.ranks,a.max_dt,200,a.retry_preserved)
            summary["full_case"]=str(case);summary["solver_completed"]=True
            summary["status"]="SOLVER_COMPLETE_ANALYSIS_PENDING";dump(OUT/"GRANADA_A_STATUS.json",summary)
            dest,analysis=analyze(case,r)
            summary.update(status="A_200S_ANALYZED",analysis=str(dest),final=analysis)
            if a.publish:summary["published_branch"]=publish(case,r,dest,url,a.ranks,a.max_dt)
        except BaseException as e:
            summary["error"]=str(e) or type(e).__name__
            summary["status"]="A_GRANADA_BLOCKED_PRESERVED";raise
        finally:
            dump(OUT/"GRANADA_A_STATUS.json",summary)
            print(json.dumps(summary,indent=2),flush=True)
if __name__=="__main__":main()
