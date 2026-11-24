#!/usr/bin/env python3
"""Native bilateral C14 A heat-flux recovery from 101 archived states; no CFD."""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import continue_c14_stage07_grouped_evidence as evidence
import run_c14_stage07_grouped_native_recovery as grouped
import run_c14_stage07_solver_backed_recovery as recovery

HERE=Path(__file__).resolve().parent
PATCHES={("metal","metalTop"),("metal","metal_to_mold"),("mold","mold_to_metal"),
         *[("mold",n) for n in ("moldTop","moldExterior","moldBottom","moldRecessWall","moldRecessRoof")]}
INTERFACE={("metal","metal_to_mold"),("mold","mold_to_metal")}
REPORT="C3D04_A_C14_BILATERAL_NATIVE_Q_REPORT.json"

def need(ok,msg):
    if not ok:
        raise ValueError(msg)

def overlay(text):
    matches=list(re.finditer(r"\binterpolationSchemes\s*\{([^{}]*)\}",text,re.S))
    need(len(matches)==1,"unique mold interpolationSchemes required")
    b=matches[0]
    body=re.sub(r"/\*.*?\*/|//[^\n]*","",b.group(1),flags=re.S)
    direct=re.findall(r"\binterpolate\(kappa\)\s+(\w+)\s*;",body)
    if direct:
        need(direct==["harmonic"],"unexpected explicit kappa interpolation")
        return text
    need(re.search(r"\binterpolate\(\(kappa\|Cv\)\)\s+harmonic\s*;",body) is not None,
         "original harmonic kappa/Cv intent absent")
    i=b.end()-1
    return text[:i]+"\n    interpolate(kappa) harmonic; // isolated offline q only\n"+text[i:]

def invoke(args,cwd,log,env):
    with log.open("x",encoding="utf-8") as f:
        rc=subprocess.run(args,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,check=False).returncode
    if rc or recovery.fatal_openfoam_log(log)["foam_fatal_present"]:
        print("\n".join(log.read_text(errors="replace").splitlines()[-65:]),file=sys.stderr)
        raise ValueError("native command failed; preserved log: "+str(log))

def csv_rows(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def analyze(sums,faces,work,continuation,out):
    by={}
    for r in csv_rows(sums):
        t=float(r["time_s"])
        i=round(10*t)
        k=(r["region"],r["patch"])
        n=int(r["nFaces"])
        area,power,gross=(float(r[x]) for x in ("area_m2","q_out_W","gross_abs_face_power_W"))
        need(0<=i<=100 and abs(t-i/10)<1e-8 and k in PATCHES and n>0
             and all(math.isfinite(x) for x in (area,power,gross))
             and area>0 and gross+1e-7>=abs(power),"invalid native q row")
        need(k not in INTERFACE or n==2496,"interface count differs")
        need((i,k) not in by,"duplicate patch/time")
        by[i,k]=(n,area,power,gross)
    need(set(by)=={(i,k) for i in range(101) for k in PATCHES},"incomplete 101x8 native patch timeline")
    for k in PATCHES:
        need(all(by[i,k][0]==by[0,k][0] and math.isclose(by[i,k][1],by[0,k][1],rel_tol=1e-9)
                 for i in range(101)),"patch geometry changes")
    final={}
    pairs={}
    for r in csv_rows(faces):
        k=(r["region"],r["patch"])
        need(k in PATCHES and abs(float(r["time_s"])-10)<1e-8,"invalid final face identity")
        n=int(r["face_local"])
        area,q,power=(float(r[x]) for x in ("area_m2","q_out_W_m2","q_out_face_W"))
        xyz=tuple(float(r["center_"+x+"_m"]) for x in "xyz")
        normal=tuple(float(r["normal_"+x]) for x in "xyz")
        need(all(math.isfinite(x) for x in (area,q,power,*xyz,*normal))
             and area>0 and math.isclose(area*q,power,rel_tol=1e-8,abs_tol=1e-10)
             and math.isclose(sum(x*x for x in normal),1,abs_tol=1e-7),"invalid face q")
        block=final.setdefault(k,{})
        need(0<=n<by[100,k][0] and n not in block,"duplicate/invalid face")
        block[n]=(area,power)
        if k in INTERFACE:
            pos=tuple(round(x,8) for x in xyz)
            d=pairs.setdefault(k,{})
            need(pos not in d,"duplicate interface centre")
            d[pos]=(area,power,normal)
    for k in PATCHES:
        d=final.get(k,{})
        n,area,power,gross=by[100,k]
        need(len(d)==n and all(math.isclose(x,y,rel_tol=1e-8,abs_tol=1e-8) for x,y in
             ((math.fsum(v[0] for v in d.values()),area),(math.fsum(v[1] for v in d.values()),power),
              (math.fsum(abs(v[1]) for v in d.values()),gross))),"face/integral mismatch")
    a,b=(pairs[k] for k in (("metal","metal_to_mold"),("mold","mold_to_metal")))
    common=a.keys()&b.keys()
    paired=sum(math.isclose(a[k][0],b[k][0],rel_tol=1e-6,abs_tol=1e-12)
               and sum(x*y for x,y in zip(a[k][2],b[k][2]))<-.99 for k in common)
    def q(k):return [by[i,k][2] for i in range(101)]
    mc,sc,mt=q(("metal","metal_to_mold")),q(("mold","mold_to_metal")),q(("metal","metalTop"))
    exterior=[math.fsum(by[i,k][2] for k in PATCHES if k[0]=="mold" and k not in INTERFACE) for i in range(101)]
    oldroot=work/"postProcessing/metal"
    oldmc=grouped.scalar_table(oldroot/"metalMoldEnergyPower/0/surfaceFieldValue.dat","sum(heatFlux)",grouped.TIMES)
    oldmt=grouped.scalar_table(oldroot/"metalTopEnergyPower/0/surfaceFieldValue.dat","sum(heatFlux)",grouped.TIMES)
    integrals={k:evidence.integrate(grouped.TIMES,v)[-1] for k,v in
               (("metal_contact",mc),("mold_contact",sc),("metal_top",mt),("mold_exterior",exterior))}
    prior=recovery.read_json(continuation/evidence.REPORT)
    f=prior["energy"]["final_terms"]
    dH=f["metal_native_enthalpy_delta_since_0p1s_J"]
    dL=f["metal_nominal_liquid_latent_inventory_delta_J"]
    dM=f["mold_nominal_sensible_inventory_delta_J"]
    def mismatch(a,b):return max(abs(x-y)/max(1,abs(x),abs(y)) for x,y in zip(a,b))
    return {"saved_times":101,"patch_rows":len(by),"interface_faces_each":2496,
            "paired_geometry_faces_at_10s":paired,
            "matched_face_abs_interface_power_residual_W":math.fsum(abs(a[k][1]+b[k][1]) for k in common),
            "max_metal_contact_relative_difference_vs_grouped_heatFlux":mismatch(mc,oldmc),
            "max_metal_top_relative_difference_vs_grouped_heatFlux":mismatch(mt,oldmt),
            "final_patch_q_out_W":{"/".join(k):by[100,k][2] for k in sorted(PATCHES)},
            "integrals_since_0p1s_J":integrals,
            "interface_signed_integral_J":integrals["metal_contact"]+integrals["mold_contact"],
            "nominal_mold_inventory_plus_outward_q_J":dM+integrals["mold_contact"]+integrals["mold_exterior"],
            "nominal_combined_inventory_plus_exterior_q_J":dH+dL+dM+integrals["metal_top"]+integrals["mold_exterior"],
            "global_energy_conservation_verified":False,"native_dt_latent_source_verified":False,
            "limitations":"Independent q reconstruction and saved-time trapezoids; nominal inventory, not discrete solver energy closure."}

def execute(source,work,continuation,out):
    source,work,continuation=(p.expanduser().resolve() for p in (source,work,continuation))
    out=out.expanduser().absolute()
    need(out.parent.resolve()==source.parent and not out.exists() and not out.is_symlink()
         and not out.is_relative_to(HERE.parents[2]),"fresh external sibling output required")
    evidence.evidence_gate(source,work)
    prev=recovery.read_json(continuation/evidence.REPORT)
    need(prev["source"]==str(source) and prev["grouped_input"]==str(work)
         and prev["source_hashes_unchanged"] and prev["grouped_input_hashes_unchanged"]
         and prev["energy"]["saved_states"]==101,"missing real integrated energy evidence")
    before=grouped.snapshot_hashes(source)
    prevsha=recovery.sha(continuation/evidence.REPORT)
    need(os.getenv("WM_PROJECT_VERSION")=="14" and shutil.which("wmake"),"source Foundation14 environment")
    out.mkdir()
    try:
        build=out/"build"
        shutil.copytree(HERE/"native_bilateral_flux",build)
        binpath=out/"bin"
        binpath.mkdir()
        env=os.environ.copy()
        env["FOAM_USER_APPBIN"]=str(binpath)
        invoke(["wmake",str(build)],out,out/"log.wmake",env)
        binary=binpath/"c3d04C14FluidSolidFlux"
        need(binary.is_file() and os.access(binary,os.X_OK),"native binary absent")
        copy=out/"q_case"
        copy.mkdir()
        for n in ("constant","system",*evidence.NAMES):
            shutil.copytree(source/n,copy/n)
        schemes=copy/"system/mold/fvSchemes"
        original=schemes.read_text(encoding="utf-8")
        amended=overlay(original)
        schemes.write_text(amended,encoding="utf-8")
        sums,faces=out/"integrated.csv",out/"last_faces.csv"
        invoke([str(binary),"-case",str(copy),"-time","0:10","-outIntegrated",str(sums),
                "-outLastFaces",str(faces)],out,out/"log.native_q",env)
        result=analyze(sums,faces,work,continuation,out)
        result["status"]="BILATERAL_NATIVE_Q_DIAGNOSTIC_COMPLETE_NOT_CLOSURE"
        result["isolated_mold_scheme_overlay_applied"]=amended!=original
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        result={"status":"BLOCKED_PRESERVED","error":str(exc),"global_energy_conservation_verified":False}
    result["original_source_hashes_unchanged"]=grouped.snapshot_hashes(source)==before
    result["previous_report_hash_unchanged"]=recovery.sha(continuation/evidence.REPORT)==prevsha
    result["stage"]="07/10"
    result["milestones_done"]="6/10"
    result["source_solver_rerun"]=False
    result["report"]=str(out/REPORT)
    (out/REPORT).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    h=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,default=h/"C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    p.add_argument("--grouped",type=Path,default=h/"C3D04_A_C14_GROUPED_NATIVE_RECOVERY_01")
    p.add_argument("--continuation",type=Path,default=h/"C3D04_A_C14_ENERGY_VERTICAL_01")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        r=execute(a.case,a.grouped,a.continuation,a.out)
        print(json.dumps(r,indent=2))
        return 0 if r["status"].startswith("BILATERAL_NATIVE_Q_DIAGNOSTIC_COMPLETE") and r["original_source_hashes_unchanged"] and r["previous_report_hash_unchanged"] else 3
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print("C3D04_A_NATIVE_Q_BLOCKED:",exc,file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
