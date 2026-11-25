#!/usr/bin/env python3
"""Compact six-case campaign: independent 1 s volume / 0.1 s tables / 1 ms probes.
Foundation14 WSL only; source preparation and previous CFD are never modified.
Run only after prepare, with explicit --run NAME. No solver in prepare.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HOME=Path.home()/"OpenFOAM"
SOURCE=HOME/"CAMPAIGN_200S_01"
TARGET=HOME/"CAMPAIGN_200S_COMPACT_01"
REPORT="CAMPAIGN_200S_REPORT.json"
CASES=tuple(f"{f}-{g}-200s" for g in ("2D","3DA","3DB") for f in ("C14","B14"))
STEPS=200000
VOLUME_TIMES=list(range(201))
TABLE_TIMES=[i/10 for i in range(2001)]
PROBE_TIMES=[i/1000 for i in range(200001)]
RESERVE=10*1024**3
PROBES=("T","U","p_rgh","rho","phaseChangeSource:alpha1")
REDUCTIONS=("metalTopPhiSum","metalTopEnergyPower","metalMoldEnergyPower","metalBoundaryEnergyPower",
            "metalSensibleEnthalpy","metalMeanLiquidFraction","metalLatentHeatPower","metalMeanCoolingRate",
            "metalMeanSolidificationRate","metalMaxCourant","metalMaxThermalGradient","metalMaxDensityGradient")
PRODUCERS=("vorticityField","flowTopology","energyAdvectiveFlux","heatFlux","energyFlux",
           "temperatureGradient","temperatureGradientMagnitude","densityGradient","densityGradientMagnitude",
           "temperatureTimeDerivative","coolingRate","liquidFractionTimeDerivative","solidificationRate",
           "latentHeatField","latentHeatRateDensity","cellCourantNumber")
MOMENTUM="solidificationMeltingMomentumDiagnostics"
DERIVED=("dTdt","coolingRate","dAlphaLdt","solidificationRate","latentHeatRateVol","gradT","magGradT",
         "gradRho","magGradRho","CoCell","vorticity","flowType","magSqrDevGradU",
         "phaseChangeDarcyCoeff","phaseChangeBuoyancyAcceleration")
CANON="U_x U_y U_z T p_rgh rho phaseChangeSource:alpha1 vorticity_x vorticity_y vorticity_z flowType magSqrDevGradU gradT_x gradT_y gradT_z magGradT dTdt coolingRate gradRho_x gradRho_y gradRho_z magGradRho dAlphaLdt solidificationRate latentHeatRateVol CoCell".split()
NEAR="U_x U_y U_z T p_rgh rho phaseChangeSource:alpha1".split()

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def json_out(p,x):
    tmp=p.with_name("."+p.name+".tmp")
    tmp.write_text(json.dumps(x,indent=2)+"\n");tmp.replace(p)
def inputs(p):
    result={}
    for d in ("0","constant","system"):
        for q in (p/d).rglob("*"):
            need(not q.is_symlink(),"linked input refused "+str(q))
            if q.is_file():result[str(q.relative_to(p))]=sha(q)
    return result
def exact_replace(s,pattern,replacement):
    x,n=re.subn(pattern,replacement,s,flags=re.M)
    need(n==1,"expected one match: "+pattern);return x
def set_key(s,key,value,expected=None):
    p=r"(?m)^([ \t]+)"+re.escape(key)+r"[ \t]+([^;\n]+);"
    matches=list(re.finditer(p,s))
    need(len(matches)<=1,"ambiguous key "+key)
    if matches:
        if expected is not None:need(matches[0][2].strip()==expected,"unexpected "+key)
        return re.sub(p,lambda m:m[1]+key+" "+value+";",s)
    need(expected is None,"missing expected "+key)
    return exact_replace(s,r"(?m)^(\w+\s*\n\{)",lambda m:m[1]+"\n    "+key+" "+value+";")
def blocks(s):
    # Native dictionaries use unindented object headers, including the coded
    # object whose C++ payload is indented. Preserve all original block bodies.
    matches=[m for m in re.finditer(r"(?m)^(\w+)[ \t]*\n\{",s) if m[1]!="FoamFile"]
    need(matches,"no native objects")
    result={}
    for i,m in enumerate(matches):
        key=m[1];end=matches[i+1].start() if i+1<len(matches) else len(s)
        need(key not in result,"duplicate object "+key)
        result[key]=(m.start(),end,s[m.start():end])
    return result
def transform(s,producer_names,table_names,leave=()):
    b=blocks(s)
    need(set(b)==set(producer_names)|set(table_names)|set(leave),"unexpected object set: "+str(list(b)))
    out=s[:next(iter(b.values()))[0]]
    for name,(_,_,body) in b.items():
        if name in leave:out+=body;continue
        # calculate at 0.1s; only volumetric producers write at global 1s.
        body=set_key(body,"executeControl","timeStep")
        body=set_key(body,"executeInterval","100")
        if name in table_names:
            body=set_key(body,"writeControl","timeStep","writeTime")
            body=set_key(body,"writeInterval","100")
        else:
            need(re.search(r"(?m)^[ \t]+writeControl[ \t]+writeTime;",body),"producer writeTime absent "+name)
        out+=body
    return out
def config(case,geometry):
    changes={}
    def edit(rel,fn):
        p=case/rel;before=p.read_bytes()
        after=fn(before.decode("utf-8").replace("\r\n","\n")).encode("utf-8")
        need(before!=after,"no change "+rel);p.write_bytes(after)
        changes[rel]={"old_sha256":hashlib.sha256(before).hexdigest(),"new_sha256":sha(p)}
    def control(s):
        for k,v in (("endTime","200"),("deltaT","0.001"),("startTime","0"),("adjustTimeStep","no"),
                    ("writeControl","timeStep"),("writeFormat","ascii"),("purgeWrite","0")):
            need(re.search(r"(?m)^"+k+r"[ \t]+"+re.escape(v)+r"[ \t]*;",s),"control drift "+k)
        return exact_replace(s,r"^(writeInterval[ \t]+)100([ \t]*;)",r"\g<1>1000\2")
    edit("system/controlDict",control)
    edit("system/researchDiagnostics",lambda s:transform(s,PRODUCERS,REDUCTIONS,(MOMENTUM,)))
    edit("system/functions",lambda s:transform(s,(),("topFlow",),("temperatureProbe",)))
    edit("system/lineProfiles",lambda s:transform(s,(),("horizontalProfiles","verticalProfiles")))
    if geometry!="2D":edit("system/additional3DProfiles",lambda s:transform(s,(),("additional3DProfiles",)))
    # Near-top native line at 0.1s, from already geometry-mapped auxiliary dict.
    top=(case/"system/topSurfaceFlowPostProcessing").read_text()
    b=blocks(top);need("nearTopInternalLine" in b,"nearTop source missing")
    near=b["nearTopInternalLine"][2]
    near=set_key(near,"executeControl","timeStep")
    near=set_key(near,"executeInterval","100")
    near=set_key(near,"writeInterval","100")
    # Original auxiliary line was already timeStep-controlled.
    need(re.search(r"(?m)^[ \t]+writeControl[ \t]+timeStep;",near),"nearTop control drift")
    p=case/"system/compactNearTop";p.write_text(near)
    changes["system/compactNearTop"]={"new_sha256":sha(p)}
    p=case/"system/functions";p.write_text(p.read_text()+'\n#include "compactNearTop"\n')
    changes["system/functions"]["new_sha256"]=sha(p)
    return changes
def check_native(case,name,args):
    with (case/name).open("x") as log:
        rc=subprocess.run(args,cwd=case,stdout=log,stderr=subprocess.STDOUT).returncode
    with (case/name).open(errors="replace") as f:fatal=any("FOAM FATAL" in l for l in f)
    need(rc==0 and not fatal,"native command failed: "+str(case/name))
def numeric_time(p):
    try:return float(p.name)
    except ValueError:return None
def unrun(case):
    r=json.loads((case/REPORT).read_text())
    need(r["status"]=="PREPARED_NOT_RUN" and not r.get("solver_completed"),"source not unrun: "+str(case))
    need(not (case/"log.foamMultiRun").exists() and not (case/"postProcessing").exists(),
         "source solver/diagnostic evidence exists: "+str(case))
    need(not any(p.is_dir() and (v:=numeric_time(p)) is not None and v>0 for p in case.iterdir()),"positive CFD time exists")
    need(inputs(case)==r["input_sha256"],"source input drift "+str(case))
    return r
def estimate(old):
    # Retain all prior log/table budget; volume estimate uses exact 201/2001.
    f=old["field_estimate_bytes"];d=old["diagnostic_estimate_bytes"]
    # Allow additional canonical aliases/nearTop tables within a separate
    # 10% diagnostic allowance, plus original 50% safety margin.
    fnew=math.ceil(f*201/2001);dnew=math.ceil(d*1.1)
    return {"field_estimate_bytes":fnew,"diagnostic_estimate_bytes":dnew,
            "projected_bytes_with_50pct_margin":math.ceil(1.5*(fnew+dnew)),
            "prior_projected_bytes":old["projected_bytes_with_50pct_margin"],
            "method":"201/2001 prior volume bytes; retain all diagnostics/logs +10%, 50% margin; not a guaranteed bound"}
def prepare_case(src,dst):
    r=unrun(src);need(r["case"]==dst.name,"case name mismatch")
    need(not dst.exists() and not dst.is_symlink(),"compact case already exists")
    tmp=Path(tempfile.mkdtemp(prefix="."+dst.name+".staging.",dir=dst.parent))
    for d in ("0","constant","system"):shutil.copytree(src/d,tmp/d)
    need(inputs(tmp)==r["input_sha256"],"copy differs")
    changes=config(tmp,r["geometry"])
    changed=inputs(tmp)
    diff={k for k in set(changed)|set(r["input_sha256"]) if changed.get(k)!=r["input_sha256"].get(k)}
    need(diff==set(changes),"unexpected changed inputs "+str(diff))
    for rel in changes:
        if rel!="system/compactNearTop":need(changes[rel]["old_sha256"]==r["input_sha256"][rel],"old hash mismatch "+rel)
        need(changes[rel]["new_sha256"]==changed[rel],"new hash mismatch "+rel)
    for rel in ("system/controlDict","system/functions"):
        check_native(tmp,"log.compact.parse."+rel.replace("/","."),["foamDictionary",str(tmp/rel)])
    need(inputs(src)==r["input_sha256"],"source changed during preparation")
    report={**r,"status":"PREPARED_COMPACT_NOT_RUN","source_dense_case":str(src),
            "source_dense_report_sha256":sha(src/REPORT),"source_input_sha256":r["input_sha256"],
            "input_sha256":changed,"changed_io_files":changes,"saved_dt_s":1.0,"volume_saved_dt_s":1.0,
            "profile_and_reduction_dt_s":.1,"probe_dt_s":.001,"momentum_volume_dt_s":1.0,
            "volume_states_target":201,"profile_states_target":2001,"probe_samples_target":200001,
            "disk_projection":estimate(r["disk_projection"]),"original_dense_case_preserved":True,
            "implementation_sha256":sha(Path(__file__).resolve()),"solver_completed":False}
    json_out(tmp/REPORT,report);(tmp/(dst.name+".foam")).touch()
    tmp.rename(dst);return report
def lock(root):
    f=(root/".execution.lock").open("a")
    try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        f.close();raise ValueError("active campaign; no concurrent operation: "+str(root))
    return f
def prepare():
    need(SOURCE.is_dir() and not SOURCE.is_symlink(),"original six prepared cases required")
    need(not TARGET.is_symlink(),"unsafe compact root")
    TARGET.mkdir(exist_ok=True)
    with lock(SOURCE),lock(TARGET):
        reports={}
        for name in CASES:
            try:
                dst=TARGET/name
                if dst.exists():
                    r=json.loads((dst/REPORT).read_text())
                    need(r["case"]==name and r["status"]=="PREPARED_COMPACT_NOT_RUN" and inputs(dst)==r["input_sha256"],"existing compact case preserved; not an unrun matching preparation")
                    reports[name]=r
                else:reports[name]=prepare_case(SOURCE/name,dst)
            except (ValueError,OSError,KeyError,subprocess.SubprocessError) as e:
                reports[name]={"status":"BLOCKED_PRESERVED","error":str(e)}
            print(name,reports[name]["status"],flush=True)
            json_out(TARGET/"CAMPAIGN_INDEX.json",reports)
        ready={k:r["disk_projection"] for k,r in reports.items() if r["status"]=="PREPARED_COMPACT_NOT_RUN"}
        total=sum(r["projected_bytes_with_50pct_margin"] for r in ready.values())
        old=sum(r["prior_projected_bytes"] for r in ready.values())
        summary={"prepared":len(ready),"expected":6,"previous_projected_bytes":old,
                 "compact_projected_bytes":total,"projected_reduction_percent":100*(1-total/old) if old else None,
                 "free_bytes_WSL":shutil.disk_usage(TARGET).free,"per_case":ready,
                 "all_fit_WSL_estimate":len(ready)==6 and shutil.disk_usage(TARGET).free>=total+RESERVE,
                 "windows_physical_capacity_verified":False,"solver_executed":False}
        json_out(TARGET/"CAMPAIGN_RESOURCES.json",summary);print(json.dumps(summary,indent=2),flush=True)
        need(len(ready)==6,"some cases blocked; preserve originals and inspect CAMPAIGN_INDEX.json")
        print("ALL_SIX_COMPACT_PREPARED_NO_CFD",flush=True)
def rows(p):
    with p.open() as f:
        for l in f:
            if not l.strip() or l.lstrip().startswith("#"):continue
            v=[float(x) for x in l.replace("("," ").replace(")"," ").split()]
            need(all(math.isfinite(x) and abs(x)<1e100 for x in v),"invalid value "+str(p))
            yield v
def cadence(p,expected,width=None):
    n=0
    for v in rows(p):
        need(n<len(expected) and abs(v[0]-expected[n])<1e-7 and (width is None or len(v)==width),"cadence/width "+str(p));n+=1
    need(n==len(expected),"incomplete "+str(p));return n
def xy(p,columns,canonical=None):
    with p.open() as f:h=f.readline().lstrip("#").split()
    need(len(h)==len(columns)+1 and h[0] in ("x","y","z"),"header "+str(p))
    for x,y in zip(h[1:],columns):
        need(x==y or (x.endswith("...") and y.startswith(x[:-3])),"column mismatch "+str(p))
    data=list(rows(p));need(1<len(data)<=80 and all(len(v)==len(h) for v in data),"coverage "+str(p))
    need(all(b[0]>a[0] for a,b in zip(data,data[1:])),"nonmonotone coordinate "+str(p))
    if canonical:
        canonical.parent.mkdir(parents=True,exist_ok=True)
        with p.open() as raw,canonical.open("x") as out:
            next(raw);out.write("# "+h[0]+" "+" ".join(columns)+"\n");shutil.copyfileobj(raw,out)
    return len(data)
def profile_groups(report):
    g={"horizontalProfiles":["line_y10mm","line_y20mm","line_y30mm"],"verticalProfiles":["line_x20mm"]}
    if report["sampling"]["additional_3D_profiles"]:g["additional3DProfiles"]=list(report["sampling"]["additional_3D_profiles"])
    return g
def noninteger_volumes(case):
    ans=[]
    for p in case.iterdir():
        t=numeric_time(p)
        if p.is_dir() and t is not None and t>0 and abs(t-round(t))>1e-8:
            if any((p/r).is_dir() and any(q.is_file() for q in (p/r).iterdir()) for r in ("metal","mold")):ans.append(p.name)
    return ans
def early_gate(case,r):
    pp=case/"postProcessing/metal"
    for g,ls in profile_groups(r).items():
        for name in ls:xy(pp/g/"0.1"/(name+".xy"),CANON)
    xy(pp/"nearTopInternalLine/0.1/line_y39p75mm.xy",NEAR)
    need((pp/"topFlow/0.1/patch(metalTop).xy").is_file(),"0.1s topFlow missing")
    for region in ("metal","mold"):need((case/"1"/region/"T").is_file(),"1s volume missing "+region)
    need(not noninteger_volumes(case),"unexpected noninteger volume writes")
def audit(case,r):
    pp=case/"postProcessing/metal";results={};errors=[]
    def guard(k,fn):
        try:results[k]=fn()
        except (ValueError,OSError,IndexError) as e:errors.append(k+": "+str(e))
    for f in PROBES:guard("probe/"+f,lambda f=f:cadence(pp/"temperatureProbe/0"/f,PROBE_TIMES,4 if f=="U" else 2))
    for key in REDUCTIONS:
        def table(key=key):
            p=list((pp/key/"0").glob("*.dat"));need(len(p)==1,"missing/ambiguous table")
            return cadence(p[0],TABLE_TIMES)
        guard("reduction/"+key,table)
    for g,ls in {**profile_groups(r),"nearTopInternalLine":["line_y39p75mm"]}.items():
        for name in ls:
            def all_xy(g=g,name=name):
                counts=[]
                for t in TABLE_TIMES:
                    p=pp/g/format(t,"g")/(name+".xy")
                    cols=NEAR if g=="nearTopInternalLine" else CANON
                    counts.append(xy(p,cols,pp/("CompactCanonical"+g)/format(t,"g")/p.name))
                return {"times":len(counts),"min_points":min(counts),"max_points":max(counts)}
            guard(g+"/"+name,all_xy)
    for region,fields in (("metal",("T","U","p","p_rgh","phaseChangeSource:alpha1")+DERIVED),("mold",("T",))):
        for f in fields:
            # t0 is audited too; report any actual missing derived field
            # rather than declaring complete based on later times.
            n=sum((case/str(t)/region/f).is_file() for t in VOLUME_TIMES)
            results["volume/"+region+"/"+f]=n
            if n!=len(VOLUME_TIMES):errors.append("volume coverage "+region+"/"+f)
    results["topFlow_positive_times"]=sum((pp/"topFlow"/format(t,"g")/"patch(metalTop).xy").is_file() for t in TABLE_TIMES[1:])
    if results["topFlow_positive_times"]!=2000:errors.append("topFlow coverage")
    unexpected=noninteger_volumes(case)
    if unexpected:errors.append("unexpected noninteger volume writes")
    return {"coverage":results,"errors":errors,"unexpected_volume_times":unexpected,
            "native_runtime_coverage_complete":not errors}
def execute(name):
    need(TARGET.is_dir() and not TARGET.is_symlink(),"compact campaign not prepared")
    with lock(SOURCE),lock(TARGET):
        case=TARGET/name;r=json.loads((case/REPORT).read_text())
        original=unrun(SOURCE/name)
        need(original["input_sha256"]==r["source_input_sha256"],"dense source changed since compact preparation")
        need(r["status"]=="PREPARED_COMPACT_NOT_RUN" and not (case/"log.foamMultiRun").exists(),"already attempted; preserve")
        need(inputs(case)==r["input_sha256"],"compact inputs changed")
        need(shutil.disk_usage(case).free>=r["disk_projection"]["projected_bytes_with_50pct_margin"]+RESERVE,"insufficient WSL free disk")
        r["status"]="RUNNING_COMPACT";json_out(case/REPORT,r)
        try:
            n=0;last=0;end=False;fatal=False
            with (case/"log.foamMultiRun").open("x") as log:
                p=subprocess.Popen(["foamMultiRun","-case",str(case)],cwd=case,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
                try:
                    for line in p.stdout:
                        log.write(line);fatal|="FOAM FATAL" in line;end|=line.strip()=="End"
                        m=re.match(r"^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$",line)
                        if not m:continue
                        n+=1;last=float(m[1])
                        need(abs(last-n*.001)<1e-7,"solver step drift")
                        if n==1002:
                            early_gate(case,r);r["early_split_cadence_gate"]="PASS"
                            json_out(case/REPORT,r);print("Split cadence verified on actual CFD: .1s profiles / 1s volumes",flush=True)
                        if n%1000==0:
                            print(f"{name}: {last:g}/200 s",flush=True);log.flush()
                            need(shutil.disk_usage(case).free>RESERVE,"disk reserve reached")
                    rc=p.wait()
                except BaseException:
                    if p.poll() is None:p.terminate();p.wait()
                    raise
            need(rc==0 and not fatal and end and n==STEPS,"incomplete solver")
            r.update(solver_completed=True,solver_steps=n,final_time_s=last,status="SOLVER_COMPLETE_AUDIT_PENDING")
            json_out(case/REPORT,r)
            check_native(case,"log.foamLog",["foamLog","log.foamMultiRun"])
            r["runtime_audit"]=audit(case,r)
            # Momentum and full surface fields at native 1s checkpoints only;
            # topFlow and nearTop at .1s already captured online.
            r["offline_momentum_and_face_fields"]="not run; optional 1s-only native postprocessing, no .1s reconstruction"
            r["status"]="SOLVER_COMPLETE_COMPACT_AUDITED" if r["runtime_audit"]["native_runtime_coverage_complete"] else "SOLVER_COMPLETE_PARTIAL_DIAGNOSTICS"
        except BaseException as e:
            r["status"]="SOLVER_COMPLETE_AUDIT_BLOCKED" if r["solver_completed"] else "RUN_INCOMPLETE_PRESERVED"
            r["error"]=str(e);raise
        finally:
            json_out(case/REPORT,r)
            idx=TARGET/"CAMPAIGN_INDEX.json";allr=json.loads(idx.read_text());allr[name]=r;json_out(idx,allr)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",choices=CASES)
    a=p.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION")=="14","source Foundation14")
    if a.run:execute(a.run)
    else:prepare()
if __name__=="__main__":main()
