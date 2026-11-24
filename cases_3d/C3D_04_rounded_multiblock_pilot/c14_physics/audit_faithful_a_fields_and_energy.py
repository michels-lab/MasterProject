#!/usr/bin/env python3
"""Read-only comparison of the two existing C14 3D-A runs and bilateral energy audit.
No CFD solve, mesh generation or modification of saved inputs. Reuse previous
reconstructed q only when all relevant saved inputs agree byte-for-byte.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile

import analyze_existing_c14_3d_results as native
import c14_3d_postprocess_parity as vol
import run_c14_stage07_bilateral_native_flux as bilateral

HOME=Path.home()/"OpenFOAM"
BASE=HOME/"C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01"
FAITHFUL=HOME/"C3D04_A_C14_FAITHFUL_RUNTIME_10S_01"
OLD_Q=HOME/"C3D04_A_C14_BILATERAL_NATIVE_Q_01"
TIMES=[i/10 for i in range(101)]
LABELS=[format(t,"g") for t in TIMES]
COUNTS={"metal":8960,"mold":12352}
FIELDS={"metal":("T","U","p","p_rgh","phaseChangeSource:alpha1"),"mold":("T",)}
RHO,CP,L,RHOM,CVM=6820.,827.,228600.,1500.,700.

def need(ok,msg):
    if not ok:raise ValueError(msg)
def read_json(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return native.file_digest(p)
def dump(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def table(p,rows):
    need(bool(rows),"empty output table")
    with p.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def fileset(root,folder):
    return {str(p.relative_to(root)):sha(p) for p in (root/folder).rglob("*") if p.is_file()}
def physical_inputs(root):
    d=fileset(root,"constant")
    for p in ("system/controlDict","system/fvSolution","system/metal/fvSchemes","system/metal/fvSolution","system/mold/fvSchemes","system/mold/fvSolution"):
        d[p]=sha(root/p)
    return d
def saved_hashes(root):
    return {f"{t}/{r}/{f}":sha(root/t/r/f) for t in LABELS for r,fields in FIELDS.items() for f in fields}
def series(root,name,kind,width):
    p=root/"postProcessing/metal"/name/"0"/kind
    rows=[list(map(float,l.split())) for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.lstrip().startswith("#")]
    need(len(rows)==101 and all(len(r)==width and abs(r[0]-t)<1e-8 and all(math.isfinite(x) for x in r) for r,t in zip(rows,TIMES)),"invalid native table "+str(p))
    return rows
def scalar(root,t,r,f):return native.scalar_field_values(root/t/r/f,COUNTS[r])
def values(root,t,r,f):
    return vol.vector_field(root/t/r/f,COUNTS[r]) if f=="U" else scalar(root,t,r,f)
def difference(a,b,w,vector):
    d=[math.sqrt(math.fsum((y-x)**2 for x,y in zip(aa,bb))) for aa,bb in zip(a,b)] if vector else [bb-aa for aa,bb in zip(a,b)]
    need(len(d)==len(w),"cell correspondence mismatch")
    return {"max_abs":max(map(abs,d)),"rmse_volume":math.sqrt(math.fsum(x*x*v for x,v in zip(d,w))/math.fsum(w)),
            "bias_volume":None if vector else vol.weighted(d,w),"different_cells":sum(x!=0 for x in d)}
def inventory(t,fields,w):
    T=fields["metal","T"];A=fields["metal","phaseChangeSource:alpha1"];U=fields["metal","U"];M=fields["mold","T"]
    wm,ws=w["metal"],w["mold"];V=math.fsum(wm);Vs=math.fsum(ws)
    speed=[math.hypot(*v) for v in U]
    return {"time_s":float(t),"metal_T_mean_K":vol.weighted(T,wm),"metal_T_min_K":min(T),"metal_T_max_K":max(T),
            "mold_T_mean_K":vol.weighted(M,ws),"mold_T_min_K":min(M),"mold_T_max_K":max(M),
            "alphaL_mean":vol.weighted(A,wm),"solid_fraction_mean":1-vol.weighted(A,wm),
            "volume_below_Tliq_fraction":math.fsum(v for x,v in zip(T,wm) if x<1473)/V,
            "volume_below_Tsol_fraction":math.fsum(v for x,v in zip(T,wm) if x<1423)/V,
            "volume_alpha_below_0p999999_fraction":math.fsum(v for x,v in zip(A,wm) if x<.999999)/V,
            "speed_mean_m_s":vol.weighted(speed,wm),"speed_max_m_s":max(speed),
            "speed_rms_m_s":math.sqrt(vol.weighted([x*x for x in speed],wm)),
            "p_rgh_min_Pa":min(fields["metal","p_rgh"]),"p_rgh_max_Pa":max(fields["metal","p_rgh"]),
            "metal_sensible_reference_J":RHO*CP*math.fsum((x-1500)*v for x,v in zip(T,wm)),
            "metal_latent_reference_J":RHO*L*math.fsum((x-1)*v for x,v in zip(A,wm)),
            "mold_sensible_reference_J":RHOM*CVM*math.fsum((x-300)*v for x,v in zip(M,ws)),
            "metal_kinetic_inventory_J":.5*RHO*math.fsum(x*x*v for x,v in zip(speed,wm))}
def patch_history(out):
    by={}
    for r in bilateral.csv_rows(out/"integrated.csv"):
        t=float(r["time_s"]);i=round(10*t);k=(r["region"],r["patch"])
        n=int(r["nFaces"]);a,q,g=(float(r[x]) for x in ("area_m2","q_out_W","gross_abs_face_power_W"))
        need(abs(t-i/10)<1e-8 and 0<=i<=100 and k in bilateral.PATCHES and (i,k) not in by and n>0 and a>0 and all(map(math.isfinite,(a,q,g))) and g+1e-7>=abs(q),"invalid patch history")
        need(k not in bilateral.INTERFACE or n==2496,"interface count mismatch")
        by[i,k]=(n,a,q,g)
    need(set(by)=={(i,k) for i in range(101) for k in bilateral.PATCHES},"missing patch history")
    for k in bilateral.PATCHES:
        need(all(by[i,k][0]==by[0,k][0] and math.isclose(by[i,k][1],by[0,k][1],rel_tol=1e-9) for i in range(101)),"patch geometry mismatch")
    rows=[]
    for i,t in enumerate(TIMES):
        get=lambda k:by[i,k][2]
        mc=get(("metal","metal_to_mold"));sc=get(("mold","mold_to_metal"))
        mt=get(("metal","metalTop"))
        ext=math.fsum(get(k) for k in bilateral.PATCHES if k[0]=="mold" and k not in bilateral.INTERFACE)
        rows.append({"time_s":t,"metal_contact_W":mc,"mold_contact_W":sc,"metal_top_W":mt,"mold_exterior_W":ext,"interface_signed_W":mc+sc})
    return rows

def get_q(case,old_q,out,reusable):
    previous=old_q/bilateral.REPORT
    if reusable and previous.is_file():
        r=read_json(previous)
        if r.get("status")=="BILATERAL_NATIVE_Q_DIAGNOSTIC_COMPLETE_NOT_CLOSURE" and r.get("original_source_hashes_unchanged") and r.get("saved_times")==101 and (old_q/"integrated.csv").is_file() and (old_q/"last_faces.csv").is_file():
            for name in ("integrated.csv","last_faces.csv"):shutil.copy2(old_q/name,out/name)
            return {"mode":"REUSE_BASE_RECONSTRUCTED_Q_IDENTICAL_PHYSICAL_INPUTS_AND_SAVED_PRIMARY_FIELDS",
                    "prior_report":str(previous),"prior_report_sha256":sha(previous),
                    "limitation":"Prior native q reconstruction; not solver-step face powers."}
    need(os.environ.get("WM_PROJECT_VERSION")=="14" and shutil.which("wmake"),"OpenFOAM Foundation14 needed for read-only q reconstruction")
    build=out/"build";binpath=out/"bin"
    shutil.copytree(bilateral.HERE/"native_bilateral_flux",build);binpath.mkdir()
    env=os.environ.copy();env["FOAM_USER_APPBIN"]=str(binpath)
    bilateral.invoke(["wmake",str(build)],out,out/"log.wmake",env)
    binary=binpath/"c3d04C14FluidSolidFlux"
    need(binary.is_file() and os.access(binary,os.X_OK),"native flux utility missing")
    # Same proven extraction procedure as stage07. Scratch copy only;
    # original directories never become writable inputs to native utility.
    with tempfile.TemporaryDirectory(prefix="q_scratch_",dir=out) as tmp:
        scratch=Path(tmp)
        for name in ("constant","system",*LABELS):shutil.copytree(case/name,scratch/name)
        schemes=scratch/"system/mold/fvSchemes"
        schemes.write_text(bilateral.overlay(schemes.read_text(encoding="utf-8")),encoding="utf-8")
        bilateral.invoke([str(binary),"-case",str(scratch),"-time","0:10","-outIntegrated",str(out/"integrated.csv"),"-outLastFaces",str(out/"last_faces.csv")],out,out/"log.native_q",env)
    return {"mode":"NEW_READ_ONLY_BILATERAL_Q_RECONSTRUCTION_FROM_FAITHFUL_SAVED_FIELDS",
            "limitation":"Same native thermal transport API and isolated harmonic mold interpolation overlay as stage07; no CFD."}

def execute(base,case,old_q,out):
    base,case,old_q,out=(p.expanduser().resolve() for p in (base,case,old_q,out))
    need(base!=case and out.parent==case/"analysis_results" and not out.exists(),"fresh analysis_results subdirectory required")
    report=read_json(case/"C14_A_FAITHFUL_RUNTIME_REPORT.json")
    need(report["status"]=="FAITHFUL_C14_RUNTIME_READY" and report["solver_completed"] and report["native_diagnostic_parity"],"faithful run not accepted")
    need(sha(case/"log.foamMultiRun")==report["solver"]["log_sha256"],"faithful log changed")
    for k,h in report["input_sha256"].items():need(sha(case/k)==h,"faithful input changed "+k)
    original=read_json(base/"C14_3D_A_NATIVE_STAGE_REPORT.json")
    need(original["native_solver_run"] and original["full_10s_original_controlDict_unchanged"],"base run not accepted")
    pa,pb=physical_inputs(base),physical_inputs(case)
    need(pa==pb,"physical inputs or mesh differ; cannot perform cellwise reproduction check")
    ha,hb=saved_hashes(base),saved_hashes(case)
    for k,h in original.get("full_10s_fields_sha256",{}).items():need(sha(base/k)==h,"baseline final field changed "+k)
    w={r:vol.cell_volumes(case,r,n) for r,n in COUNTS.items()}
    V=math.fsum(w["metal"])
    need(math.isclose(V,4.7921447006662436e-5,rel_tol=1e-8),"unexpected metal volume")
    out.mkdir(parents=True)
    comparisons=[];stats=[];baseline_stats=[]
    for t in LABELS:
        a={};b={}
        for r,fs in FIELDS.items():
            for f in fs:
                k=f"{t}/{r}/{f}"
                x,y=values(base,t,r,f),values(case,t,r,f)
                a[r,f]=x;b[r,f]=y
                comparisons.append({"time_s":float(t),"region":r,"field":f,"file_bytes_identical":ha[k]==hb[k],**difference(x,y,w[r],f=="U")})
        stats.append(inventory(t,b,w));baseline_stats.append(inventory(t,a,w))
    table(out/"field_reproduction_101.csv",comparisons)
    table(out/"faithful_volume_101.csv",stats);table(out/"baseline_volume_101.csv",baseline_stats)
    # Only exact entire physical-input and saved-primary-file identity
    # permits reuse. Numerical closeness alone is not used as proof.
    q_provenance=get_q(case,old_q,out,ha==hb)
    q=patch_history(out)
    H=series(case,"metalSensibleEnthalpy","volFieldValue.dat",2)
    F=series(case,"metalMeanLiquidFraction","volFieldValue.dat",2)
    P=series(case,"metalLatentHeatPower","volFieldValue.dat",2)
    Q=series(case,"metalBoundaryEnergyPower","surfaceFieldValue.dat",4)
    for i,row in enumerate(stats):
        need(abs(row["alphaL_mean"]-F[i][1])<=1e-6,"native alpha reduction inconsistent with saved field")
    balances=[];ends={}
    for start in (0,1):
        acc={k:0. for k in ("metal_contact_W","mold_contact_W","metal_top_W","mold_exterior_W","interface_signed_W","native_metal_total_W","native_latent_W")}
        def power(i):
            return {**{k:q[i][k] for k in acc if k in q[i]},"native_metal_total_W":Q[i][3],"native_latent_W":P[i][1]}
        for i in range(start,101):
            if i>start:
                a,b=power(i-1),power(i)
                for k in acc:acc[k]+=(TIMES[i]-TIMES[i-1])*(a[k]+b[k])/2
            dh=H[i][1]-H[start][1]
            dl=RHO*L*V*(F[i][1]-F[start][1])
            dm=stats[i]["mold_sensible_reference_J"]-stats[start]["mold_sensible_reference_J"]
            dke=stats[i]["metal_kinetic_inventory_J"]-stats[start]["metal_kinetic_inventory_J"]
            row={"start_s":TIMES[start],"time_s":TIMES[i],
                 **{k.removesuffix("_W")+"_integrated_J":v for k,v in acc.items()},
                 "metal_native_sensible_delta_J":dh,"metal_nominal_latent_delta_J":dl,"mold_nominal_sensible_delta_J":dm,
                 "metal_kinetic_delta_J_diagnostic_only":dke,
                 "metal_native_inventory_residual_J":dh+dl+acc["native_metal_total_W"],
                 "metal_native_power_residual_J":dh-acc["native_latent_W"]+acc["native_metal_total_W"],
                 "mold_nominal_residual_J":dm+acc["mold_contact_W"]+acc["mold_exterior_W"],
                 "combined_nominal_residual_J":dh+dl+dm+acc["metal_top_W"]+acc["mold_exterior_W"]}
            balances.append(row)
        ends[str(TIMES[start])]=balances[-1]
    table(out/"bilateral_energy_balance_101.csv",balances)
    result={"status":"FAITHFUL_FIELDS_AND_BILATERAL_ENERGY_DIAGNOSTIC_READY",
            "same_mesh_and_physical_inputs":True,"all_primary_field_files_byte_identical":ha==hb,
            "all_saved_primary_internal_values_identical":all(r["different_cells"]==0 for r in comparisons),
            "field_summary":{r+"/"+f:{"maximum_abs_difference":max(x["max_abs"] for x in comparisons if x["region"]==r and x["field"]==f),
                  "max_volume_RMSE":max(x["rmse_volume"] for x in comparisons if x["region"]==r and x["field"]==f)}
                 for r,fs in FIELDS.items() for f in fs},
            "saved_times":101,"metal_volume_m3":V,"mold_volume_m3":math.fsum(w["mold"]),
            "final":stats[-1],"maximum_saved_speed":max(stats,key=lambda x:x["speed_max_m_s"]),
            "first_saved_alpha_below_0p999999":next((r for r in stats if r["volume_alpha_below_0p999999_fraction"]>0),None),
            "energy_final_by_start":ends,"q_provenance":q_provenance,
            "q_source_sha256":{n:sha(out/n) for n in ("integrated.csv","last_faces.csv")},
            "base_source_unchanged":physical_inputs(base)==pa and saved_hashes(base)==ha,
            "faithful_source_unchanged":physical_inputs(case)==pb and saved_hashes(case)==hb,
            "CFD_rerun":False,"discrete_energy_conservation_verified":False,
            "grid_time_independence_verified":False,"experimental_validation":False,
            "limits":["Saved-state fields and diagnostic rates at 0.1 s, not every solver step.",
                      "Mold sensible energy uses original constant rho/Cv and saved T. Latent inventory uses model alpha1.",
                      "Bilateral native q is reconstructed from archived states and is not a complete discrete equation residual.",
                      "Full-run initial flux convention and 0.1 s integration error are reported, not hidden."]}
    dump(out/"FAITHFUL_FIELDS_AND_ENERGY_REPORT.json",result)
    need(result["base_source_unchanged"] and result["faithful_source_unchanged"],"source modified during audit")
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base",type=Path,default=BASE)
    p.add_argument("--case",type=Path,default=FAITHFUL)
    p.add_argument("--prior-q",type=Path,default=OLD_Q)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    try:
        r=execute(a.base,a.case,a.prior_q,a.out or a.case/"analysis_results/field_and_energy_audit_01")
        print(json.dumps(r,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError,RuntimeError) as e:
        print("FAITHFUL_FIELDS_AND_ENERGY_BLOCKED:",e,file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
