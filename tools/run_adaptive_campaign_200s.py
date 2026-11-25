#!/usr/bin/env python3
"""Four-case adaptive time campaign, isolated from fixed-step and lab runs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import fcntl
import sys

import transfer_campaign_200s as transfer

HOME=Path.home()/"OpenFOAM"
ROOT=HOME/"CAMPAIGN_200S_ADAPTIVE_01"
ORDER=("C14-3DA-200s","C14-2D-200s","B14-2D-200s","C14-3DB-200s")
REPORT="CAMPAIGN_200S_REPORT.json"
MAX_DT=.01
MAX_CO=.25
END=200.
RESERVE=10*1024**3
NUM=r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
TIMELINE="adaptive_time_steps.csv"
RESULT_PREFIX="results/campaign-200s-adaptive-v1/"

def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def read(p):return json.loads(p.read_text())
def dump(p,d):
    q=p.with_suffix(".tmp");q.write_text(json.dumps(d,indent=2)+"\n");q.replace(p)
def edit_key(s,k,old,new):
    p=r"(?m)^([ \t]*"+re.escape(k)+r"[ \t]+)"+re.escape(old)+r"([ \t]*;)"
    s,n=re.subn(p,lambda m:m[1]+new+m[2],s)
    need(n==1,"unexpected "+k);return s
def adapt_dicts(case):
    changed={}
    p=case/"system/controlDict";old=p.read_text();s=old
    for k,a,b in (("adjustTimeStep","no","yes"),("writeControl","timeStep","adjustableRunTime"),
                  ("writeInterval","1000","1"),("maxDeltaT","0.1","0.01"),("timePrecision","6","12")):
        s=edit_key(s,k,a,b)
    for k,v in (("deltaT","0.001"),("maxCo","0.25"),("endTime","200"),("writeFormat","ascii"),("writeCompression","off")):
        need(re.search(r"(?m)^[ \t]*"+k+r"[ \t]+"+re.escape(v)+r"[ \t]*;",s),"original control drift "+k)
    p.write_text(s);changed["system/controlDict"]=transfer.sha(p)
    # Match only actual keys, not comments or C++ code. Keep probes timeStep 1
    # and all global-write producers/momentum unchanged. Physical .1s controls
    # use adjustableRunTime to target the same stations despite variable dt.
    for name in ("functions","researchDiagnostics","lineProfiles","additional3DProfiles","compactNearTop"):
        p=case/"system"/name
        if not p.is_file():continue
        s=p.read_text()
        def replace(m):
            prefix=m[2]
            return m[1]+prefix+"Control adjustableRunTime;\n"+m[3]+prefix+"Interval 0.1;"
        new,n=re.subn(r"(?m)^([ \t]*)(execute|write)Control[ \t]+timeStep;[ \t]*\n([ \t]*)\2Interval[ \t]+100[ \t]*;",replace,s)
        need(n>0,"no .1s controls found in "+name)
        need(not re.search(r"(?m)^[ \t]*(?:execute|write)Interval[ \t]+100[ \t]*;",new),"unconverted step cadence "+name)
        p.write_text(new);changed["system/"+name]=transfer.sha(p)
    return changed
def native(case,name,args):
    with (case/name).open("x") as log:
        rc=subprocess.run(args,cwd=case,stdout=log,stderr=subprocess.STDOUT).returncode
    need(rc==0,"native command failed "+str(case/name))
def prepare(repo,url):
    if all((ROOT/n/REPORT).is_file() for n in ORDER):
        print("ADAPTIVE INPUTS EXIST; preserved",flush=True);return
    need(not any((ROOT/n).exists() for n in ORDER),"partial preparation preserved")
    # Download the verified published input archive, not the live fixed cases.
    with tempfile.TemporaryDirectory(prefix="adaptive-input-",dir=ROOT) as tmp:
        p=Path(tmp);archive=p/"input.tar.gz"
        m=transfer.download(url,transfer.INPUT_BRANCH,p/"git",archive)
        need(m["kind"]=="inputs" and m["solver_commit"]==transfer.PIN and set(ORDER)<=set(m["cases"]),"wrong input archive")
        stage=p/"unpacked";stage.mkdir();transfer.extract(archive,stage)
        compact=stage/transfer.COMPACT.name
        for name in ORDER:
            src=compact/name
            r=transfer.untouched(src)
            dst=p/name;dst.mkdir()
            for d in ("0","constant","system"):shutil.copytree(src/d,dst/d)
            need(transfer.input_hashes(dst)==r["input_sha256"],"copy drift")
            changed=adapt_dicts(dst);after=transfer.input_hashes(dst)
            need({k for k in set(after)|set(r["input_sha256"]) if after.get(k)!=r["input_sha256"].get(k)}==set(changed),"unexpected changed file")
            native(dst,"log.adaptive.parse.controlDict",["foamDictionary",str(dst/"system/controlDict")])
            native(dst,"log.adaptive.parse.functions",["foamDictionary",str(dst/"system/functions")])
            report={**r,"status":"ADAPTIVE_PREPARED_NOT_RUN","solver_completed":False,
                    "physical_validation":False,"fixed_input_sha256":r["input_sha256"],"input_sha256":after,
                    "changed_time_control_files":changed,"source_transfer_sha256":m["archive_sha256"],
                    "time_mode":"adaptive","initial_dt_s":.001,"max_dt_s":MAX_DT,"max_co":MAX_CO,
                    "probe_cadence":"every actual solver step","profile_target_interval_s":.1,
                    "volume_target_interval_s":1.0,"solver_steps_target":None,"probe_samples_target":None,
                    "disk_projection_note":"retain fixed estimate as planning reserve, not actual adaptive output estimate"}
            dump(dst/REPORT,report);(dst/(name+".foam")).touch()
        for name in ORDER:(p/name).rename(ROOT/name)
    print("ALL_FOUR_ADAPTIVE_PREPARED_NO_CFD",flush=True)
def rows(p):
    with p.open() as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):continue
            v=[float(x) for x in line.replace("("," ").replace(")"," ").split()]
            need(v and all(math.isfinite(x) and abs(x)<1e100 for x in v),"invalid table "+str(p))
            yield v
def times_table(p,expected,tol):
    actual=[r[0] for r in rows(p)]
    need(len(actual)==len(expected),"count mismatch "+str(p)+": "+str(len(actual))+" vs "+str(len(expected)))
    need(all(abs(a-b)<=tol for a,b in zip(actual,expected)),"time mismatch "+str(p))
    return len(actual)
def directories(p):
    result=[]
    for q in p.iterdir():
        if not q.is_dir():continue
        try:v=float(q.name)
        except ValueError:continue
        if math.isfinite(v):result.append((v,q))
    return sorted(result)
def audit(case,r,steps):
    pp=case/"postProcessing/metal";counts={};errors=[]
    def guard(key,fn):
        try:counts[key]=fn()
        except (RuntimeError,OSError,ValueError,IndexError) as e:errors.append(key+": "+str(e))
    # Native probe timestamps may use 6 significant digits. Match true solver
    # times with rounding tolerance, never interpolate or fabricate samples.
    for f in ("T","U","p_rgh","rho","phaseChangeSource:alpha1"):
        guard("probe/"+f,lambda f=f:times_table(pp/"temperatureProbe/0"/f,[0.]+steps,5.1e-4))
    reductions=("metalTopPhiSum","metalTopEnergyPower","metalMoldEnergyPower","metalBoundaryEnergyPower",
                "metalSensibleEnthalpy","metalMeanLiquidFraction","metalLatentHeatPower","metalMeanCoolingRate",
                "metalMeanSolidificationRate","metalMaxCourant","metalMaxThermalGradient","metalMaxDensityGradient")
    target=[i/10 for i in range(2001)]
    for g in reductions:
        def red(g=g):
            p=list((pp/g/"0").glob("*.dat"));need(len(p)==1,"missing/ambiguous reduction")
            return times_table(p[0],target,5e-5)
        guard("reduction/"+g,red)
    groups={"horizontalProfiles":["line_y10mm","line_y20mm","line_y30mm"],
            "verticalProfiles":["line_x20mm"],"nearTopInternalLine":["line_y39p75mm"]}
    if r["sampling"]["additional_3D_profiles"]:groups["additional3DProfiles"]=list(r["sampling"]["additional_3D_profiles"])
    for g,names in groups.items():
        def profiles(g=g,names=names):
            dirs=directories(pp/g)
            need(len(dirs)==len(target),"profile count mismatch")
            need(all(abs(x-y)<5e-7 for (x,_),y in zip(dirs,target)),"profile cadence differs")
            for _,d in dirs:
                for n in names:
                    v=list(rows(d/(n+".xy")))
                    need(1<len(v)<=80,"missing line "+str(d/n))
            return {"times":len(dirs),"lines":len(names)}
        guard(g,profiles)
    def volume():
        ds=directories(case)
        need(len(ds)==201 and all(abs(t-i)<5e-7 for i,(t,p) in enumerate(ds)),"volume cadence differs")
        for _,p in ds:
            for reg,fields in (("metal",("T","U","p","p_rgh","phaseChangeSource:alpha1")),("mold",("T",))):
                for f in fields:need((p/reg/f).is_file(),"missing "+str(p/reg/f))
        return len(ds)
    guard("volume",volume)
    def top():
        dirs=[(x,p) for x,p in directories(pp/"topFlow") if x>0]
        need(len(dirs)==2000 and all(abs(x-y)<5e-7 for (x,_),y in zip(dirs,target[1:])),"topFlow cadence differs")
        need(all((p/"patch(metalTop).xy").is_file() for _,p in dirs),"missing topFlow file")
        return len(dirs)
    guard("topFlow",top)
    return {"counts":counts,"errors":errors,"native_runtime_coverage_complete":not errors}
def run(case):
    r=read(case/REPORT)
    need(r["status"]=="ADAPTIVE_PREPARED_NOT_RUN" and not (case/"log.foamMultiRun").exists(),"attempted case preserved "+case.name)
    need(transfer.input_hashes(case)==r["input_sha256"],"input hash mismatch")
    need(shutil.disk_usage(case).free>=r["disk_projection"]["projected_bytes_with_50pct_margin"]+RESERVE,"disk reserve")
    r["status"]="RUNNING_ADAPTIVE";dump(case/REPORT,r)
    steps=[];dts=[];co=[];last=0.;end=False;fatal=False;last_print=-1;dt_log=None;co_log=None
    started=time.monotonic()
    try:
        with (case/"log.foamMultiRun").open("x") as log,(case/TIMELINE).open("x") as timeline:
            w=csv.writer(timeline);w.writerow(("step","time_s","deltaT_from_time_s","solver_deltaT_reported_s","maxCourant_reported"))
            p=subprocess.Popen(["foamMultiRun","-case",str(case)],cwd=case,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
            try:
                for line in p.stdout:
                    log.write(line);fatal|="FOAM FATAL" in line;end|=line.strip()=="End"
                    m=re.search(r"deltaT\s*=\s*("+NUM+")",line)
                    if m:dt_log=float(m[1])
                    m=re.search(r"Courant Number.*?max:\s*("+NUM+")",line)
                    if m:co_log=float(m[1]);co.append(co_log)
                    m=re.match(r"^\s*Time\s*=\s*("+NUM+r")s?\s*$",line)
                    if not m:continue
                    t=float(m[1]);dt=t-last
                    need(0<dt<=MAX_DT+1e-7 and t<=END+1e-7,"unexpected adaptive step "+str(dt))
                    steps.append(t);dts.append(dt);w.writerow((len(steps),t,dt,dt_log,co_log))
                    dt_log=co_log=None;last=t
                    if int(t)>last_print:
                        last_print=int(t);log.flush();timeline.flush()
                        print(f"{case.name}: {t:.6g}/200 s | steps {len(steps)} | dt={dt:.6g}",flush=True)
                        need(shutil.disk_usage(case).free>RESERVE,"disk reserve reached")
                rc=p.wait()
            except BaseException:
                if p.poll() is None:p.terminate();p.wait()
                raise
        need(rc==0 and not fatal and end and abs(last-END)<1e-7,"incomplete solver")
        r.update(solver_completed=True,solver_steps=len(steps),final_time_s=last,status="SOLVER_COMPLETE_AUDIT_PENDING",
                 adaptive_statistics={"min_dt_s":min(dts),"max_dt_s":max(dts),"mean_dt_s":sum(dts)/len(dts),
                                      "distinct_dt_rounded":len(set(round(x,10) for x in dts)),
                                      "max_logged_Courant":max(co) if co else None,"wall_seconds":time.monotonic()-started})
        dump(case/REPORT,r)
        native(case,"log.foamLog",["foamLog","log.foamMultiRun"])
        r["runtime_audit"]=audit(case,r,steps)
        r["status"]="SOLVER_COMPLETE_ADAPTIVE_AUDITED" if r["runtime_audit"]["native_runtime_coverage_complete"] else "SOLVER_COMPLETE_PARTIAL_DIAGNOSTICS"
    except BaseException as e:
        r["status"]="SOLVER_COMPLETE_AUDIT_BLOCKED" if r["solver_completed"] else "RUN_INCOMPLETE_PRESERVED"
        r["error"]=str(e) or type(e).__name__;raise
    finally:dump(case/REPORT,r)
def publish(case,url):
    r=read(case/REPORT)
    need(r.get("solver_completed") and r.get("final_time_s")==200,"no complete adaptive CFD")
    branch=RESULT_PREFIX+case.name
    m=transfer.complete_manifest(url,branch)
    if m is not None:
        need(m["solver_log_sha256"]==transfer.sha(case/"log.foamMultiRun"),"remote result differs");return
    with tempfile.TemporaryDirectory(prefix="adaptive-publish-",dir=ROOT) as d:
        p=Path(d);archive=p/"result.tar.gz"
        with transfer.deterministic_tar(archive) as t:
            for n in ("postProcessing","logs",REPORT,TIMELINE,"log.foamMultiRun","log.foamLog"):
                q=case/n
                if q.exists():transfer.add(t,q,case.name+"/"+n)
        transfer.publish(url,branch,archive,{"kind":"adaptive_scientific_results","case":case.name,
            "time_mode":"adaptive","solver_steps":r["solver_steps"],"final_time_s":200,
            "solver_log_sha256":transfer.sha(case/"log.foamMultiRun"),"report_sha256":transfer.sha(case/REPORT),
            "native_runtime_coverage_complete":r.get("runtime_audit",{}).get("native_runtime_coverage_complete",False),
            "volume_fields_included":False},p/"git",case=case)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo",type=Path,default=HOME/"MasterProject")
    ap.add_argument("--prepare-only",action="store_true")
    ap.add_argument("--publish",action="store_true",help="publish completed scientific archives, separate adaptive branches")
    a=ap.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(not ROOT.is_symlink(),"unsafe root");ROOT.mkdir(exist_ok=True)
    url=transfer.root_url(a.repo)
    with (ROOT/".execution.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prepare(a.repo,url)
        if a.prepare_only:return
        summary={}
        for name in ORDER:
            case=ROOT/name
            try:
                r=read(case/REPORT)
                if not r.get("solver_completed"):run(case)
                if a.publish:publish(case,url)
                summary[name]=read(case/REPORT)["status"]
            except (RuntimeError,ValueError,OSError,subprocess.SubprocessError) as e:
                summary[name]="BLOCKED_OR_FAILED_PRESERVED: "+str(e);print(name,summary[name],flush=True)
            dump(ROOT/"ADAPTIVE_CAMPAIGN_INDEX.json",summary)
        print(json.dumps(summary,indent=2),flush=True)
        need(all(read(ROOT/n/REPORT).get("solver_completed") for n in ORDER),"some cases incomplete; preserved")
if __name__=="__main__":main()
