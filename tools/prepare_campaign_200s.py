#!/usr/bin/env python3
"""Six independent 200-s B14/C14 cases. Prepare only by default; explicit --run.

No solver in CI. No writes in source cases or existing CFD. Foundation 14 WSL.
"""
from __future__ import annotations
import argparse
import hashlib
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home()/"OpenFOAM"
A=ROOT/"cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
B=ROOT/"cases_3d/C3D_05_step_gmsh_conformal/c14_physics"
sys.path[:0]=[str(A),str(B)]
import stage_c14_3d_case_a as sa
import stage_c14_3d_case_b as sb
import run_c14_a_faithful_runtime as runtime
import compare_c14_2d_3d_a as geometry

FAMILIES=("C14","B14")
GEOMETRIES=("2D","3DA","3DB")
CASES=tuple(f"{f}-{g}-200s" for g in GEOMETRIES for f in FAMILIES)
PHYSICS=("constant/metal/materials/castIron","constant/metal/fvModels")
INITIAL=("metal/T","metal/U","metal/p","metal/p_rgh","metal/phaseChangeSource:alpha1",
         "metal/alphat","metal/epsilon","metal/k","metal/nut","metal/omega","mold/T")
MESH_NAMES=("points","faces","owner","neighbour","boundary","cellZones")
STEPS=200000
TIMES=[i/10 for i in range(2001)]
PROBES=[i/1000 for i in range(STEPS+1)]
REPORT="CAMPAIGN_200S_REPORT.json"
BASELINES={"3DA":HOME/"C3D04_A_C14_FAITHFUL_RUNTIME_10S_01",
           "3DB":HOME/"C3D05_B_C14_FLUID_SOLID_FULL_10S_01"}
CELLS={"3DA":21312,"3DB":270788}
CANON="U_x U_y U_z T p_rgh rho phaseChangeSource:alpha1 vorticity_x vorticity_y vorticity_z flowType magSqrDevGradU gradT_x gradT_y gradT_z magGradT dTdt coolingRate gradRho_x gradRho_y gradRho_z magGradRho dAlphaLdt solidificationRate latentHeatRateVol CoCell".split()

def need(ok,msg):
    if not ok: raise ValueError(msg)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1048576),b""):h.update(x)
    return h.hexdigest()
def write_json(p,obj):
    tmp=p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj,indent=2)+"\n")
    tmp.replace(p)
def src(f):
    return ROOT/"cases_controlled_buoyancy"/(f+"_topFixedFlux_explicitRef")
def source_files(p):
    return {str(x.relative_to(p)):sha(x) for d in ("constant","system") for x in (p/d).rglob("*")
            if x.is_file() and "polyMesh" not in x.parts}
def verify_family():
    b,c=(source_files(src(f)) for f in ("B14","C14"))
    need(b.keys()==c.keys(),"source file sets differ; inspect new family differences")
    need({p for p in b if b[p]!=c[p]}==set(PHYSICS),"B/C physics differences changed; review before transplant")
    for p in INITIAL:
        need(sha(src("B14")/"0"/p)==sha(src("C14")/"0"/p),"initial condition difference "+p)
    return {"B14":b,"C14":c}
def edit_end(path):
    raw=path.read_bytes()
    out,n=re.subn(rb"(?m)^([ \t]*endTime[ \t]+)10([ \t]*;)",rb"\g<1>200\2",raw)
    need(n==1,"unexpected endTime")
    for key,val in (("deltaT","0.001"),("startTime","0"),("writeInterval","100"),
                    ("adjustTimeStep","no"),("purgeWrite","0")):
        need(re.search(rb"(?m)^[ \t]*"+key.encode()+rb"[ \t]+"+re.escape(val.encode())+rb"[ \t]*;",out),"control drift "+key)
    path.write_bytes(out)
def run_cmd(case,name,args):
    with (case/name).open("x") as log:
        rc=subprocess.run(args,cwd=case,stdout=log,stderr=subprocess.STDOUT).returncode
    text=(case/name).read_text(errors="replace")
    need(rc==0 and "FOAM FATAL" not in text,f"{name} failed; inspect preserved log")
def mesh_hashes(case):
    return {str(p.relative_to(case)):sha(p) for r in ("metal","mold")
            for n in MESH_NAMES if (p:=case/"constant"/r/"polyMesh"/n).is_file()}
def bytes_tree(p):
    return sum(x.stat().st_size for x in p.rglob("*") if x.is_file() and not x.is_symlink()) if p.is_dir() else 0
def estimate(g,case):
    if g=="3DA":
        # Estimate from the actual A geometry/full diagnostic reference only.
        a=BASELINES["3DA"]
        need((a/"10/metal/T").is_file() and (a/"postProcessing/metal/temperatureProbe").is_dir(),"faithful A 10s baseline required")
        per=max(bytes_tree(a/t) for t in ("0.1","5","10"))
        pp=bytes_tree(a/"postProcessing")
        log=bytes_tree(a/"logs")+(a/"log.foamMultiRun").stat().st_size
        need(per>0 and pp>0 and log>0,"missing actual A storage baseline")
        field_bytes=per*len(TIMES)
        diag_bytes=20*(pp+log)
        return {"cells":CELLS[g],"field_estimate_bytes":field_bytes,"diagnostic_estimate_bytes":diag_bytes,
                "projected_bytes_with_50pct_margin":math.ceil(1.5*(field_bytes+diag_bytes)),
                "method":"A faithful actual maximum sampled snapshot size; 2001 states and 20x postProcessing/logs; 50% margin; not guaranteed bound"}
    # Empirical local 10s runs: maximum saved-state size per cell, plus logs and
    # all postProcessing. A faithful run is the required full diagnostics proxy.
    a,b=BASELINES["3DA"],BASELINES["3DB"]
    need((a/"10/metal/T").is_file() and (a/"postProcessing/metal/temperatureProbe").is_dir(),
         "faithful 3DA 10s baseline required for disk estimate")
    rates=[]
    for name,p in BASELINES.items():
        if (p/"10/metal/T").is_file():
            per=max(bytes_tree(p/t) for t in ("0.1","5","10"))
            rates.append(per/CELLS[name])
    need(rates and max(rates)>0,"no real volume field baseline")
    if g=="2D":
        # Use actual native owner/neighbour counts, not CAD assumptions.
        n=0
        for r in ("metal","mold"):
            p=case/"constant"/r/"polyMesh"
            # stage parser returns (number of labels, maximum label).
            o=sa.read_labels(p/"owner")[1];q=sa.read_labels(p/"neighbour")[1]
            n+=max(o,q)+1
        need(n>0,"2D cells unavailable")
    else:n=CELLS[g]
    field_bytes=math.ceil(max(rates)*n*2001)
    # Scaling postProcessing by max(1,n/A) conservatively allows for face data;
    # not a precise upper bound. Include raw solver logs and parser products.
    pp=bytes_tree(a/"postProcessing")
    log=bytes_tree(a/"logs")+(a/"log.foamMultiRun").stat().st_size
    need(pp>0 and log>0,"10s native diagnostics baseline missing")
    diag_bytes=math.ceil((pp+log)*20*max(1,n/CELLS["3DA"]))
    return {"cells":n,"field_estimate_bytes":field_bytes,"diagnostic_estimate_bytes":diag_bytes,
            "projected_bytes_with_50pct_margin":math.ceil(1.5*(field_bytes+diag_bytes)),
            "method":"local empirical 10s snapshots; scale 2001 writes and 20x diagnostics; 50% margin; not guaranteed bound"}
def map_auxiliary(source,dest,g):
    # Apply the same bottom-relative mapping to every original momentum line
    # and near-top sampling line. Avoid the previous out-of-domain 3D mistake.
    def map_text(text):
        def transform(m):
            x,y,z=(float(m[i]) for i in (1,2,3))
            return runtime.vec((g["cx"]+x-.02,g["lo"][1]+y,g["cz"]+z-.005))
        return re.sub(r"\(\s*(0\.(?:00025|03975|020))\s+(0\.(?:010|020|030|00025|03975))\s+(0\.005)\s*\)",transform,text)
    momentum=(source/"system/momentumPostProcessing").read_text()
    top=(ROOT/"analysis_tools/topSurfaceFlowPostProcessing").read_text()
    mapped_momentum=map_text(momentum);mapped_top=map_text(top)
    need(mapped_momentum!=momentum and mapped_top!=top,"auxiliary 3D mapping missing")
    (dest/"system/momentumPostProcessing").write_text(mapped_momentum)
    (dest/"system/topSurfaceFlowPostProcessing").write_text(mapped_top)
def prepare(name,dest,hashes):
    f,g,_=name.split("-")
    need(not dest.exists() and not dest.is_symlink(),"existing case; no overwrite "+str(dest))
    source=src(f)
    if g=="2D":
        dest.mkdir()
        for d in ("constant","system"):
            shutil.copytree(source/d,dest/d,ignore=shutil.ignore_patterns("polyMesh"))
        for rel in INITIAL:
            p=dest/"0"/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/"0"/rel,p)
        run_cmd(dest,"log.blockMesh",["blockMesh"])
        run_cmd(dest,"log.splitMeshRegions",["splitMeshRegions","-cellZones","all"])
        shutil.copy2(ROOT/"analysis_tools/topSurfaceFlowPostProcessing",dest/"system/topSurfaceFlowPostProcessing")
        mapping={"probe_xyz_m":[.02,.02,.005],"original_profiles":{"line_y10mm":{},"line_y20mm":{},"line_y30mm":{},"line_x20mm":{}},"additional_3D_profiles":{}}
    else:
        stage=sa if g=="3DA" else sb
        if g=="3DA":stage.stage(stage.SOURCE,dest,smoke=False)
        else:stage.stage(stage.SOURCE,dest)
        # Accepted C14 stage has all common inputs and geometry-only adaptations.
        # Verified above: B/C differ only in these two model/material files.
        for rel in PHYSICS:shutil.copy2(source/rel,dest/rel)
        geo=geometry.mesh(dest)
        need(geo["n"]==(8960 if g=="3DA" else 92200),"unexpected metal cells")
        mapping=runtime.sampling_dicts(dest,geo)
        map_auxiliary(source,dest,geo)
        need(mesh_hashes(dest)==mesh_hashes(BASELINES[g]),"accepted mesh differs from original completed CFD")
    for rel in PHYSICS:need(sha(dest/rel)==hashes[f][rel],"material transplant mismatch "+rel)
    # Check identical original 2D system diagnostics before geometry mapping.
    need(sha(dest/"system/researchDiagnostics")==hashes[f]["system/researchDiagnostics"],"diagnostic drift")
    edit_end(dest/"system/controlDict")
    for rel in ("system/controlDict","system/functions","system/momentumPostProcessing","system/topSurfaceFlowPostProcessing","constant/metal/physicalProperties","constant/metal/fvModels"):
        run_cmd(dest,"log.campaign.parse."+rel.replace("/","."),["foamDictionary",str(dest/rel)])
    tracked={str(p.relative_to(dest)):sha(p) for d in ("0","constant","system") for p in (dest/d).rglob("*") if p.is_file()}
    report={"status":"PREPARED_NOT_RUN","case":name,"formulation":f,"geometry":g,
            "purpose":"solidification" if f=="C14" else "shrinkage research reference, not a validated shrinkage solver",
            "source_sha256":hashes[f],"input_sha256":tracked,"mesh_sha256":mesh_hashes(dest),
            "sampling":mapping,"end_s":200,"dt_s":.001,"saved_dt_s":.1,
            "solver_completed":False,"physical_validation":False}
    report["status"]="PREPARED_RESOURCE_AUDIT_PENDING"
    write_json(dest/REPORT,report)
    (dest/(name+".foam")).touch()
    report["disk_projection"]=estimate(g,dest)
    report["status"]="PREPARED_NOT_RUN"
    write_json(dest/REPORT,report)
    return report
def data_rows(p):
    with p.open() as f:
        for line in f:
            if not line.strip() or line.lstrip().startswith("#"):continue
            vals=[float(x) for x in line.replace("("," ").replace(")"," ").split()]
            need(all(math.isfinite(v) and abs(v)<1e100 for v in vals),"invalid sentinel "+str(p))
            yield vals
def cadence(p,expected,width=None):
    i=0
    for r in data_rows(p):
        need(i<len(expected) and abs(r[0]-expected[i])<1e-7 and (width is None or len(r)==width),"bad cadence/width "+str(p))
        i+=1
    need(i==len(expected),"incomplete cadence "+str(p))
    return i
def audit(case,report):
    pp=case/"postProcessing/metal";errors=[];counts={}
    def guarded(key,fn):
        try:counts[key]=fn()
        except (ValueError,OSError,IndexError) as e:errors.append(key+": "+str(e))
    for field in runtime.NATIVE_FIELDS:
        guarded("probe/"+field,lambda field=field:cadence(pp/"temperatureProbe/0"/field,PROBES,4 if field=="U" else 2))
    for group in runtime.REDUCTIONS:
        def reduction(group=group):
            files=list((pp/group/"0").glob("*.dat"))
            need(len(files)==1,"missing/ambiguous reduction")
            return cadence(files[0],TIMES)
        guarded("reduction/"+group,reduction)
    groups={"horizontalProfiles":["line_y10mm","line_y20mm","line_y30mm"],"verticalProfiles":["line_x20mm"]}
    extra=report["sampling"]["additional_3D_profiles"]
    if extra:groups["additional3DProfiles"]=list(extra)
    for group,lines in groups.items():
        for line in lines:
            def profiles(group=group,line=line):
                ns=[]
                for t in TIMES:
                    p=pp/group/format(t,"g")/(line+".xy")
                    with p.open() as f:header=f.readline().lstrip("#").split()
                    need(len(header)==len(CANON)+1 and header[0] in ("x","y","z") and header[1:7]==CANON[:6],"unexpected profile header "+str(p))
                    for a,b in zip(header[1:],CANON):
                        need(a==b or (a.endswith("...") and b.startswith(a[:-3])),"column mismatch "+str(p))
                    rows=list(data_rows(p))
                    need(1<len(rows)<=80 and all(len(r)==len(header) for r in rows),"missing/invalid spatial coverage")
                    ns.append(len(rows))
                    target=pp/("C14Canonical"+group)/format(t,"g")/p.name
                    target.parent.mkdir(parents=True,exist_ok=True)
                    with p.open() as original,target.open("x") as dest:
                        next(original);dest.write("# "+header[0]+" "+" ".join(CANON)+"\n");shutil.copyfileobj(original,dest)
                return {"times":len(ns),"min_points":min(ns),"max_points":max(ns)}
            guarded(group+"/"+line,profiles)
    for field in runtime.DERIVED:
        n=sum((case/format(t,"g")/"metal"/field).is_file() for t in TIMES)
        counts["derived/"+field]=n
        if n!=len(TIMES):errors.append("derived coverage "+field)
    for r,fields in (("metal",("T","U","p","p_rgh","phaseChangeSource:alpha1")),("mold",("T",))):
        for f in fields:
            n=sum((case/format(t,"g")/r/f).is_file() for t in TIMES)
            counts["saved/"+r+"/"+f]=n
            if n!=len(TIMES):errors.append("saved coverage "+r+"/"+f)
    top_times=[t for t in TIMES[1:] if (p:=pp/"topFlow"/format(t,"g")/"patch(metalTop).xy").is_file() and p.stat().st_size>0]
    counts["topFlow_positive_saved_times"]=len(top_times)
    if len(top_times)!=2000:errors.append("topFlow positive saved-time coverage")
    return {"counts":counts,"errors":errors,"native_runtime_coverage_complete":not errors}
def execute(case,*,offline=True):
    r=json.loads((case/REPORT).read_text())
    need(r["status"]=="PREPARED_NOT_RUN" and not (case/"log.foamMultiRun").exists(),"case already attempted; do not overwrite")
    need(all(sha(case/p)==h for p,h in r["input_sha256"].items()),"prepared inputs changed")
    projection=estimate(r["geometry"],case);free=shutil.disk_usage(case).free
    reserve=10*1024**3
    need(free>=projection["projected_bytes_with_50pct_margin"]+reserve,
         f"disk gate: free {free}, estimated {projection['projected_bytes_with_50pct_margin']} + reserve {reserve}; no CFD")
    r.update(status="RUNNING",disk_projection=projection,free_bytes_at_start=free)
    write_json(case/REPORT,r)
    try:
        n=0;last=0;fatal=False;end=False
        with (case/"log.foamMultiRun").open("x") as log:
            p=subprocess.Popen(["foamMultiRun","-case",str(case)],cwd=case,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
            try:
                for line in p.stdout:
                    log.write(line)
                    fatal|="FOAM FATAL" in line
                    end|=line.strip()=="End"
                    m=re.match(r"^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$",line)
                    if m:
                        n+=1;last=float(m[1])
                        need(abs(last-n*.001)<1e-7,"unexpected solver time sequence")
                        if n%1000==0:
                            print(f"{r['case']}: {last:g}/200 s",flush=True);log.flush()
                            need(shutil.disk_usage(case).free>reserve,"free disk reserve reached; preserved incomplete run")
                rc=p.wait()
            except BaseException:
                if p.poll() is None:p.terminate();p.wait()
                raise
        need(rc==0 and not fatal and end and n==STEPS and abs(last-200)<1e-7,"solver incomplete; preserve logs")
        r.update(solver_completed=True,solver_steps=n,final_time_s=last,status="SOLVER_COMPLETE_AUDIT_PENDING")
        write_json(case/REPORT,r)
        run_cmd(case,"log.foamLog",["foamLog","log.foamMultiRun"])
        # Original native runtime outputs first; offline momentum/topSurface products
        # are separate from solver acceptance and may be unavailable.
        r["runtime_audit"]=audit(case,r)
        r["optional_offline_postprocessing"]={"momentum":"pending","topSurfaceFlow":"pending"} if offline else {"status":"not requested; native runtime diagnostics preserved"}
        for key,dct,fields in (
          ("momentum",case/"system/momentumPostProcessing","(phaseChangeSolidFraction phaseChangeDarcyCoeff phaseChangeModelDeltaT phaseChangeDarcyAcceleration phaseChangeBuoyancyAcceleration pRghAcceleration magPhaseChangeDarcyAcceleration magPhaseChangeBuoyancyAcceleration magPRghAcceleration phaseChangeDragToBuoyancy phaseChangeDragToPressure)"),
          ("topSurfaceFlow",case/"system/topSurfaceFlowPostProcessing","(U T p_rgh rho phi phaseChangeSource:alpha1)")):
            if not offline:break
            try:
                run_cmd(case,"log.campaign."+key,["foamPostProcess","-region","metal","-dict",str(dct),"-time","0.1:200","-fields",fields])
                r["optional_offline_postprocessing"][key]="process completed; output coverage not certified"
            except (ValueError,OSError) as e:r["optional_offline_postprocessing"][key]=str(e)
        r["status"]="SOLVER_COMPLETE_NATIVE_DIAGNOSTICS_AUDITED" if r["runtime_audit"]["native_runtime_coverage_complete"] else "SOLVER_COMPLETE_PARTIAL_DIAGNOSTICS"
    except BaseException as e:
        r["status"]="SOLVER_COMPLETE_AUDIT_BLOCKED" if r["solver_completed"] else "RUN_INCOMPLETE_PRESERVED"
        r["error"]=str(e);raise
    finally:write_json(case/REPORT,r)
def a_reference():
    ref=BASELINES["3DA"]
    r=json.loads((ref/runtime.REPORT).read_text())
    need(r["status"]=="FAITHFUL_C14_RUNTIME_READY" and r["solver_completed"] and r["native_diagnostic_parity"],"accepted faithful 10s reference required")
    need(sha(ref/"log.foamMultiRun")==r["solver"]["log_sha256"],"reference solver log drift")
    for rel,h in r["input_sha256"].items():
        need(sha(ref/rel)==h,"reference inputs changed "+rel)
    need((ref/"system/controlDict").read_bytes()==(src("C14")/"system/controlDict").read_bytes(),"reference controlDict not original C14")
    return ref,r

def a_expected_control(ref):
    old=(ref/"system/controlDict").read_bytes()
    new,n=re.subn(rb"(?m)^([ \t]*endTime[ \t]+)10([ \t]*;)",rb"\g<1>200\2",old)
    need(n==1,"reference endTime not 10")
    return new

def a_fidelity(case,ref,r):
    need(mesh_hashes(case)==mesh_hashes(ref),"A mesh differs from faithful 10s reference")
    need((case/"system/controlDict").read_bytes()==a_expected_control(ref),"only endTime 10->200 is allowed")
    for rel,h in r["input_sha256"].items():
        if rel=="system/controlDict":continue
        need((case/rel).is_file() and sha(case/rel)==h,"A physical or diagnostic input drift "+rel)

def prepare_a_priority(case,ref,r):
    need(not case.exists() and not case.is_symlink(),"existing A case preserved")
    sa.stage(sa.SOURCE,case,smoke=False)
    # Use the exact proven 10s runtime dictionaries, no new spatial mapping.
    for name in ("functions","researchDiagnostics","lineProfiles","additional3DProfiles"):
        shutil.copy2(ref/"system"/name,case/"system"/name)
    edit_end(case/"system/controlDict")
    a_fidelity(case,ref,r)
    for rel in ("system/controlDict","system/functions"):
        run_cmd(case,"log.campaign.parse."+rel.replace("/","."),["foamDictionary",str(case/rel)])
    tracked={str(p.relative_to(case)):sha(p) for d in ("0","constant","system") for p in (case/d).rglob("*") if p.is_file()}
    result={"status":"PREPARED_NOT_RUN","case":"C14-3DA-200s","formulation":"C14","geometry":"3DA",
            "purpose":"solidification","source_sha256":source_files(src("C14")),"input_sha256":tracked,
            "mesh_sha256":mesh_hashes(case),"sampling":r["sampling"],"end_s":200,"dt_s":.001,"saved_dt_s":.1,
            "solver_completed":False,"physical_validation":False,
            "reference_10s_log_sha256":r["solver"]["log_sha256"],"only_control_change":"endTime 10 -> 200",
            "disk_projection":estimate("3DA",case)}
    write_json(case/REPORT,result)
    (case/"C14-3DA-200s.foam").touch(exist_ok=False)
    return result

def priority_a(root):
    # Share the campaign lock even if only A is prepared. Never create or run
    # B14, 2D, 3DB or FS variants from this entrypoint.
    root.mkdir(exist_ok=True)
    with (root/".execution.lock").open("a") as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError("another campaign run holds the disk reservation; no concurrent A")
        ref,reference=a_reference()
        case=root/"C14-3DA-200s"
        need(not case.is_symlink(),"unsafe A destination")
        if not case.exists():
            report=prepare_a_priority(case,ref,reference)
        else:
            need((case/REPORT).is_file(),"existing incomplete A preparation preserved")
            report=json.loads((case/REPORT).read_text())
        need(report["case"]=="C14-3DA-200s" and report["geometry"]=="3DA" and report["formulation"]=="C14","wrong prepared case")
        a_fidelity(case,ref,reference)
        need(report["sampling"]==reference["sampling"] or report["sampling"].get("probe_xyz_m")==reference["sampling"]["probe_xyz_m"],"sampling provenance differs")
        if report.get("solver_completed"):
            print(json.dumps({"status":report["status"],"case":str(case),"existing_completed_solver_preserved":True,
                              "solver_steps":report.get("solver_steps"),"final_time_s":report.get("final_time_s"),
                              "runtime_audit":report.get("runtime_audit")},indent=2));return
        need(report["status"]=="PREPARED_NOT_RUN","existing attempted/incomplete A run preserved")
        projection=estimate("3DA",case)
        print(json.dumps({"case":str(case),"reference":str(ref),"projection":projection,
                          "free_bytes":shutil.disk_usage(case).free,"reserve_bytes":10*1024**3},indent=2),flush=True)
        execute(case,offline=False)
        # Check reference's original input/log identity again.
        a_reference()
        a_fidelity(case,ref,reference)
        result=json.loads((case/REPORT).read_text())
        print(json.dumps({"status":result["status"],"case":str(case),"solver_steps":result.get("solver_steps"),
                          "final_time_s":result.get("final_time_s"),"runtime_audit":result.get("runtime_audit"),
                          "reference_inputs_and_log_unchanged":True},indent=2),flush=True)
        if result["status"]!="SOLVER_COMPLETE_NATIVE_DIAGNOSTICS_AUDITED":sys.exit(3)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=HOME/"CAMPAIGN_200S_01")
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument("--run",choices=CASES,help="explicitly run one already prepared case")
    mode.add_argument("--prepare-run",choices=("C14-3DA-200s",),help="prepare/run only priority C14 A, reuse matching prepared case")
    args=ap.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION")=="14","source Foundation14 environment")
    root=args.root.expanduser().absolute()
    need(root.parent.resolve()==HOME.resolve() and not root.is_symlink(),"isolated campaign sibling under ~/OpenFOAM required")
    need(not root.exists() or root.is_dir(),"invalid campaign root")
    if args.prepare_run:
        priority_a(root);return
    if args.run:
        need(root.is_dir(),"campaign not prepared")
        with (root/".execution.lock").open("a") as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise ValueError("another campaign run holds the disk reservation; run sequentially")
            execute(root/args.run)
        return
    need(not root.exists(),"campaign already exists; preserve it")
    hashes=verify_family()
    root.mkdir()
    result={}
    for name in CASES:
        try:result[name]=prepare(name,root/name,hashes)
        except (ValueError,OSError,subprocess.SubprocessError) as e:
            result[name]={"status":"PREPARATION_BLOCKED_PRESERVED","error":str(e)}
        write_json(root/"CAMPAIGN_INDEX.json",result)
        print(name,result[name]["status"],flush=True)
    ready={k:r["disk_projection"]["projected_bytes_with_50pct_margin"] for k,r in result.items() if r["status"]=="PREPARED_NOT_RUN"}
    free=shutil.disk_usage(root).free
    summary={"prepared_cases":len(ready),"expected_cases":len(CASES),"per_case_projected_bytes":ready,
             "projected_total_bytes":sum(ready.values()),"free_bytes":free,
             "all_six_fit_estimate":len(ready)==6 and free>=sum(ready.values())+10*1024**3,
             "solver_executed":False,"note":"Empirical planning estimate, not guaranteed upper bound. Serial run checks disk again."}
    write_json(root/"CAMPAIGN_RESOURCES.json",summary)
    print(json.dumps(summary,indent=2),flush=True)
    if len(ready)!=6:sys.exit(2)
    print("ALL_SIX_PREPARED_NO_CFD",flush=True)
if __name__=="__main__":main()
