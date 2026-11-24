#!/usr/bin/env python3
"""C14 3D-A faithful runtime replica, same V4/T02 mesh and original CFD inputs.

New out-of-tree run from t=0, original functionObjects enabled at native
cadence. Only coordinates of sampling change; researchDiagnostics and
controlDict remain byte-identical. Never overwrite previous CFD results.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import shutil
import sys

import stage_c14_3d_case_a as stage
import c14_source_fidelity as physics
import compare_c14_2d_3d_a as cmp

HOME=Path.home()/"OpenFOAM"
BASE=HOME/"C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01"
OUT=HOME/"C3D04_A_C14_FAITHFUL_RUNTIME_10S_01"
REPORT="C14_A_FAITHFUL_RUNTIME_REPORT.json"
NATIVE_FIELDS=("T","U","p_rgh","rho","phaseChangeSource:alpha1")
DERIVED=("dTdt","coolingRate","dAlphaLdt","solidificationRate","latentHeatRateVol",
         "gradT","magGradT","gradRho","magGradRho","CoCell","vorticity","flowType",
         "magSqrDevGradU","phaseChangeDarcyCoeff","phaseChangeBuoyancyAcceleration")
REDUCTIONS=("metalTopPhiSum","metalTopEnergyPower","metalMoldEnergyPower","metalBoundaryEnergyPower",
            "metalSensibleEnthalpy","metalMeanLiquidFraction","metalLatentHeatPower",
            "metalMeanCoolingRate","metalMeanSolidificationRate","metalMaxCourant",
            "metalMaxThermalGradient","metalMaxDensityGradient")
TIMES=[i/10 for i in range(101)]
PROBE_TIMES=[i/1000 for i in range(10001)]

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def read(p):
    return p.read_bytes().decode("utf-8")
def write(p,s):
    with p.open("x",encoding="utf-8",newline="") as f:f.write(s)
def vec(p):
    return "("+" ".join(format(x,".12g") for x in p)+")"
def same_once(body,pattern,replacement):
    text,n=re.subn(pattern,lambda _:replacement,body)
    need(n==1,"expected one original coordinate: "+pattern)
    return text
def dump(out,report):
    p=out/REPORT
    tmp=out/("."+REPORT+".tmp")
    tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(p)
def mesh_hashes(case):
    names=("points","faces","owner","neighbour","boundary","cellZones")
    return {str(Path("constant")/region/"polyMesh"/name):sha(case/"constant"/region/"polyMesh"/name)
            for region in ("metal","mold") for name in names
            if (case/"constant"/region/"polyMesh"/name).is_file()}
def native_timing(path):
    times=[]
    for line in path.read_text(encoding="utf-8",errors="strict").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):continue
        m=re.match(r"\s*([-+0-9.eE]+)\s+",line)
        need(m is not None,"invalid native table row: "+str(path))
        t=float(m.group(1));need(math.isfinite(t),"nonfinite time")
        times.append(t)
    return times
def exact_times(actual,expected):
    return len(actual)==len(expected) and all(abs(a-b)<1e-8 for a,b in zip(actual,expected))
def xy_rows(path):
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):continue
        v=[float(x) for x in line.split()]
        need(len(v)==27 and all(math.isfinite(x) for x in v),"invalid C14 profile column count/values: "+str(path))
        rows.append(v)
    need(len(rows)>=2 and all(b[0]>a[0] for a,b in zip(rows,rows[1:])),"invalid profile support "+str(path))
    return rows

def sampling_dicts(out,g):
    root=physics.C14/"system"
    f0,r0,l0=(read(root/n) for n in ("functions","researchDiagnostics","lineProfiles"))
    cx,cz=g["cx"],g["cz"]
    y0=g["lo"][1]
    # Bottom-relative mapping, same physical heights and physical lengths
    # as original C14. Outside-metal samples are not extrapolated.
    probe=(cx,y0+.02,cz)
    f=same_once(f0,r"\(\s*0\.02\s+0\.02\s+0\.005\s*\)",vec(probe))
    lines={}
    l=l0
    for h in (10,20,30):
        y=y0+h/1000
        start=(cx-.01975,y,cz);end=(cx+.01975,y,cz)
        l=same_once(l,r"\(\s*0\.00025\s+0\.0"+str(h)+r"\s+0\.005\s*\)",vec(start))
        l=same_once(l,r"\(\s*0\.03975\s+0\.0"+str(h)+r"\s+0\.005\s*\)",vec(end))
        lines["line_y"+str(h)+"mm"]={"axis":"x","start":start,"end":end,"points":80}
    start=(cx,y0+.00025,cz);end=(cx,y0+.03975,cz)
    l=same_once(l,r"\(\s*0\.020\s+0\.00025\s+0\.005\s*\)",vec(start))
    l=same_once(l,r"\(\s*0\.020\s+0\.03975\s+0\.005\s*\)",vec(end))
    lines["line_x20mm"]={"axis":"y","start":start,"end":end,"points":80}
    # Supplementary 3D-only profiles, kept separate from C14's original
    # output families. Same fields/interpolation/write cadence as lineProfiles.
    template=l0[:l0.index("    sets\n")]
    template=template.replace("horizontalProfiles","additional3DProfiles",1)
    extra={}
    for h in (10,20,30):
        for angle in (45,90,135):
            rad=math.radians(angle);ux=math.cos(rad);uz=math.sin(rad)
            if angle==135:ux,uz=-ux,-uz
            if abs(ux)<1e-12:ux=0.
            if abs(uz)<1e-12:uz=0.
            y=y0+h/1000
            p=(cx-.01975*ux,y,cz-.01975*uz);q=(cx+.01975*ux,y,cz+.01975*uz)
            extra[f"height{h}_angle{angle}"]={"axis":"z" if angle==90 else "x","start":p,"end":q,"points":80}
    for name,x,z in (("vertical_xplus10",cx+.01,cz),("vertical_xminus10",cx-.01,cz),
                     ("vertical_zplus10",cx,cz+.01),("vertical_zminus10",cx,cz-.01)):
        extra[name]={"axis":"y","start":(x,y0+.00025,z),"end":(x,y0+.03975,z),"points":80}
    block=template+"    sets\n    {\n"
    for name,s in extra.items():
        block+="        "+name+"\n        {\n            type lineUniform;\n            axis "+s["axis"]+";\n            start "+vec(s["start"])+";\n            end "+vec(s["end"])+";\n            nPoints 80;\n        }\n"
    block+="    }\n}\n"
    # Add include after original two includes without changing their order.
    f=same_once(f,r'#include "lineProfiles"','#include "lineProfiles"\n#include "additional3DProfiles"')
    for name,body in (("functions",f),("researchDiagnostics",r0),("lineProfiles",l),("additional3DProfiles",block)):
        write(out/"system"/name,body)
    need((out/"system/researchDiagnostics").read_bytes()==(root/"researchDiagnostics").read_bytes(),
         "researchDiagnostics must be byte-identical")
    return {"probe_xyz_m":probe,"original_profiles":lines,"additional_3D_profiles":extra,
            "source_hashes":{n:sha(root/n) for n in ("functions","researchDiagnostics","lineProfiles","controlDict")},
            "runtime_hashes":{n:sha(out/"system"/n) for n in ("functions","researchDiagnostics","lineProfiles","additional3DProfiles","controlDict")},
            "diagonal_axis_note":"45/135 degree raw coordinate is global X projection; 90 is global Z; actual endpoints in manifest. 135 oriented increasing X."}

def stream_solver(out,tool):
    path=out/"log.foamMultiRun"
    with path.open("x",encoding="utf-8") as log:
        process=subprocess.Popen([tool,"-case",str(out)],cwd=out,stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,text=True,errors="replace",bufsize=1)
        try:
            assert process.stdout is not None
            for line in process.stdout:
                log.write(line)
                m=re.match(r"^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$",line)
                if m:
                    t=float(m.group(1))
                    if abs(t-round(t))<1e-9 or abs(t-.001)<1e-9:
                        print("Tiempo CFD: "+format(t,"g")+" / 10 s",flush=True);log.flush()
                if "FOAM FATAL" in line or "FOAM Warning" in line:print(line.rstrip(),flush=True)
            rc=process.wait()
        except BaseException:
            if process.poll() is None:process.terminate();process.wait()
            raise
    body=path.read_text(encoding="utf-8",errors="replace")
    need(rc==0 and "FOAM FATAL" not in body,"solver failed; log.foamMultiRun preserved")
    need(re.search(r"(?m)^\s*End\s*$",body) is not None,"solver did not reach End")
    for marker in ("Selecting solver fluid","Selecting solver solid","Selecting solidificationMeltingSource with name phaseChangeSource","Solving for h","Solving for e","Solving for p_rgh"):
        need(marker in body,"missing native model evidence "+marker)
    actual=[float(m) for m in re.findall(r"(?m)^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$",body)]
    need(exact_times(actual,PROBE_TIMES[1:]),"native solver step sequence differs from C14")
    return {"native_solver_steps":len(actual),"last_time_s":actual[-1],"log_sha256":sha(path),"rc":rc}

def audit_outputs(out,mapping):
    pp=out/"postProcessing/metal"
    missing=[];probe={};tables={};profiles={};fields={}
    canonical_columns="U_x U_y U_z T p_rgh rho phaseChangeSource:alpha1 vorticity_x vorticity_y vorticity_z flowType magSqrDevGradU gradT_x gradT_y gradT_z magGradT dTdt coolingRate gradRho_x gradRho_y gradRho_z magGradRho dAlphaLdt solidificationRate latentHeatRateVol CoCell"
    canonical_count=0
    for field in NATIVE_FIELDS:
        path=pp/"temperatureProbe/0"/field
        if not path.is_file():missing.append(str(path.relative_to(out)));continue
        observed=native_timing(path)
        expected_width=4 if field=="U" else 2
        values_ok=True
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#"):continue
            try:
                vals=[float(x) for x in line.replace("("," ").replace(")"," ").split()]
                values_ok=values_ok and len(vals)==expected_width and all(math.isfinite(x) for x in vals)
            except ValueError:values_ok=False
        probe[field]={"samples":len(observed),"first_time_s":observed[0] if observed else None,
                      "last_time_s":observed[-1] if observed else None,"exact_native_cadence":exact_times(observed,PROBE_TIMES),"finite_native_values":values_ok}
        if not probe[field]["exact_native_cadence"] or not values_ok:missing.append("native probe cadence "+field)
    for name in REDUCTIONS:
        root=pp/name
        paths=sorted(root.glob("0/*.dat"))
        if len(paths)!=1:missing.append("missing/ambiguous reduction "+name);continue
        observed=native_timing(paths[0])
        tables[name]={"rows":len(observed),"exact_saved_cadence":exact_times(observed,TIMES)}
        if not tables[name]["exact_saved_cadence"]:missing.append("reduction cadence "+name)
    for name,group in (("horizontalProfiles",list(mapping["original_profiles"])[:3]),
                       ("verticalProfiles",["line_x20mm"]),
                       ("additional3DProfiles",list(mapping["additional_3D_profiles"]))):
        for line in group:
            counts=[]
            for t in TIMES:
                path=pp/name/format(t,"g")/(line+".xy")
                if not path.is_file():continue
                rows=xy_rows(path);counts.append(len(rows))
                header=path.read_text(encoding="utf-8").splitlines()[0].lstrip("#").split()
                need(len(header)==27 and header[0] in ("x","y","z") and header[1:7]==["U_x","U_y","U_z","T","p_rgh","rho"] and header[7].startswith("phaseChang") and header[13:17]==["gradT_x","gradT_y","gradT_z","magGradT"],"unexpected native C14 raw header "+str(path))
                target=pp/"C14CanonicalProfiles"/name/format(t,"g")/path.name
                target.parent.mkdir(parents=True,exist_ok=True)
                # Raw writer abbreviates long column names; keep original and
                # emit exact-name alias from same rows, no reinterpolation.
                raw=path.read_text(encoding="utf-8").splitlines(keepends=True)
                write(target,"# "+header[0]+" "+canonical_columns+"\n"+"".join(raw[1:]))
                canonical_count+=1
            profiles[name+"/"+line]={"time_files":len(counts),"min_points":min(counts,default=0),"max_points":max(counts,default=0),
                                      "requested_points":80,"partial_spatial_coverage":any(n<80 for n in counts)}
            if len(counts)!=101:missing.append("profile temporal coverage "+name+"/"+line)
    for name in DERIVED:
        saved=[t for t in TIMES if (out/format(t,"g")/"metal"/name).is_file()]
        fields[name]={"saved_times":len(saved),"missing_times":[t for t in TIMES if t not in saved]}
        # Some runtime diagnostics may only be available once solver starts.
        # Do not silently certify parity for missing t=0.
        if len(saved)!=101:missing.append("derived field coverage "+name)
    for t in TIMES:
        for region,names in (("metal",("T","U","p","p_rgh","phaseChangeSource:alpha1")),("mold",("T",))):
            for name in names:
                if not (out/format(t,"g")/region/name).is_file():missing.append("saved field "+format(t,"g")+"/"+region+"/"+name)
    top=pp/"topFlow"
    top_files=[p for p in top.rglob("*") if p.is_file()] if top.is_dir() else []
    if not top_files:missing.append("topFlow native output")
    return {"probe":probe,"reductions":tables,"profiles":profiles,"derived_fields":fields,
            "canonical_profile_files":canonical_count,"topFlow_native_files":len(top_files),
            "missing_or_incomplete":missing,"native_diagnostic_parity":not missing}

def execute(source,base,out):
    source,base=source.expanduser().resolve(),base.expanduser().resolve()
    out=out.expanduser().absolute()
    need(out.parent.resolve()==HOME.resolve(),"isolated OpenFOAM sibling required")
    stage.protect_source(source,out);stage.protect_source(base,out)
    tools=stage.environment()
    original=json.loads((base/stage.REPORT).read_text())
    need(original.get("native_solver_run") is True and original.get("full_10s_original_controlDict_unchanged") is True,
         "accepted real original 10-second run required")
    baseline_hash=mesh_hashes(base)
    need(len(baseline_hash)>=11,"accepted mesh manifest incomplete")
    baseline_files={str(p.relative_to(base)):sha(p) for p in (base/"system").rglob("*") if p.is_file()}
    baseline_files.update({stage.REPORT:sha(base/stage.REPORT),"log.foamMultiRun":sha(base/"log.foamMultiRun")})
    for p in ("10/metal/T","10/metal/U","10/metal/phaseChangeSource:alpha1","10/mold/T"):baseline_files[p]=sha(base/p)
    print("Preparando copia independiente de la malla V4/T02, sin remallar.",flush=True)
    stage.stage(source,out,smoke=False)
    report={"status":"PREPARED_NOT_EXECUTED","case":str(out),"base_run_preserved":str(base),
            "geometry_source":str(source),"controlDict_byte_identical":False,
            "solver_completed":False,"native_diagnostic_parity":False,"grid_independence_verified":False,
            "experimental_validation":False,"stage":"09/10","operational_hitos":"8/10"}
    try:
        need(mesh_hashes(out)==baseline_hash,"new mesh differs from accepted CFD baseline")
        need((out/"system/controlDict").read_bytes()==(physics.C14/"system/controlDict").read_bytes()==(base/"system/controlDict").read_bytes(),"controlDict drift")
        report["controlDict_byte_identical"]=True
        # All existing physical dictionaries must remain identical to prior run.
        expected=stage.input_files(8960,smoke=False,existing_zone=True)
        for rel in expected:
            if rel.startswith(("system/","constant/")):
                need((out/rel).read_bytes()==(base/rel).read_bytes(),"physics/numerical dictionary drift "+rel)
        g=cmp.mesh(out)
        need(g["n"]==8960,"unexpected accepted metal mesh")
        mapping=sampling_dicts(out,g);report["sampling"]=mapping
        stage.native([tools["foamDictionary"],str(out/"system/functions")],out,"log.dict.fullRuntimeFunctions",60)
        tracked={str(p.relative_to(out)):sha(p) for folder in ("constant","system") for p in (out/folder).rglob("*") if p.is_file()}
        report["input_sha256"]=tracked
        report["status"]="RUNNING_NATIVE_C14_RUNTIME"
        dump(out,report)
        print("Ejecutando C14 3D con registros originales: dt=0.001 s, fin=10 s.",flush=True)
        report["solver"]=stream_solver(out,tools["foamMultiRun"])
        report["solver_completed"]=True
        report["input_hashes_unchanged"]=all(sha(out/k)==v for k,v in tracked.items())
        need(report["input_hashes_unchanged"],"native input modified during run")
        foamlog=shutil.which("foamLog")
        if foamlog:
            with (out/"log.foamLog").open("x",encoding="utf-8") as fl:
                result=subprocess.run([foamlog,"log.foamMultiRun"],cwd=out,stdout=fl,stderr=subprocess.STDOUT,check=False)
            report["foamLog"]={"returncode":result.returncode,"logs_directory_exists":(out/"logs").is_dir()}
        else:report["foamLog"]={"available":False,"raw_solver_log_preserved":True}
        report["coverage"]=audit_outputs(out,mapping)
        report["native_diagnostic_parity"]=report["coverage"]["native_diagnostic_parity"]
        report["status"]="FAITHFUL_C14_RUNTIME_READY" if report["native_diagnostic_parity"] else "SOLVER_COMPLETE_DIAGNOSTIC_COVERAGE_PARTIAL"
        (out/"C3D04_A_C14_FAITHFUL.foam").touch(exist_ok=False)
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError) as e:
        report["status"]="SOLVER_COMPLETE_DIAGNOSTIC_AUDIT_BLOCKED" if report["solver_completed"] else "NATIVE_RUN_BLOCKED_PRESERVED"
        report["error"]=str(e)
    finally:
        report["base_evidence_unchanged"]=mesh_hashes(base)==baseline_hash and all(sha(base/k)==v for k,v in baseline_files.items())
        dump(out,report)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=stage.SOURCE)
    p.add_argument("--base",type=Path,default=BASE)
    p.add_argument("--out",type=Path,default=OUT)
    a=p.parse_args()
    try:
        r=execute(a.source,a.base,a.out)
        print(json.dumps({k:v for k,v in r.items() if k!="input_sha256"},indent=2))
        return 0 if r["status"]=="FAITHFUL_C14_RUNTIME_READY" and r["base_evidence_unchanged"] else 3
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as e:
        print("C14_FAITHFUL_RUNTIME_BLOCKED:",e,file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
