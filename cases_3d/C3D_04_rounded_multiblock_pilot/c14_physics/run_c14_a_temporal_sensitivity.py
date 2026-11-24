#!/usr/bin/env python3
"""C14 A temporal sensitivity, fixed accepted V4/T02 geometry and physics.
Two new independent CFD runs. Reuses the existing reference, never overwrites
it. Exact common-time comparisons and 3-level convergence diagnostics.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
import subprocess

import run_c14_a_faithful_runtime as faithful
import stage_c14_3d_case_a as stage
import c14_3d_postprocess_parity as vol
import analyze_existing_c14_3d_results as native

HOME=Path.home()/"OpenFOAM"
REF=faithful.OUT
ROOT=HOME/"C3D04_A_C14_TEMPORAL_SENSITIVITY_01"
LEVELS=(("dt_0001",.001,100),("dt_00005",.0005,200),("dt_000025",.00025,400))
TIMES=[i/10 for i in range(101)]
LABELS=[format(t,"g") for t in TIMES]
DICTS=("functions","researchDiagnostics","lineProfiles","additional3DProfiles")
FIELDS={"metal":("T","U","phaseChangeSource:alpha1","p","p_rgh"),"mold":("T",)}
COUNTS={"metal":8960,"mold":12352}
REPORT="C14_A_TEMPORAL_RUN_REPORT.json"
SUMMARY="C14_A_TEMPORAL_SENSITIVITY_REPORT.json"
need=faithful.need
sha=faithful.sha

def load(p):return json.loads(p.read_text(encoding="utf-8"))
def save(p,obj):
    tmp=p.with_name("."+p.name+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(p)
def tree_hash(root,folders):
    return {str(p.relative_to(root)):sha(p) for folder in folders for p in (root/folder).rglob("*") if p.is_file()}
def primary_hashes(root):
    return {f"{t}/{r}/{f}":sha(root/t/r/f) for t in LABELS for r,fields in FIELDS.items() for f in fields}
def control(source,dt,interval):
    need(math.isclose(dt*interval,.1,abs_tol=1e-14),"same physical write times required")
    s=faithful.same_once(source,r"(?m)^(\s*deltaT\s+)0\.001\s*;",f"deltaT          {dt:.8g};")
    return faithful.same_once(s,r"(?m)^(\s*writeInterval\s+)100\s*;",f"writeInterval   {interval};")
def times(dt):return [i*dt for i in range(round(10/dt)+1)]
def verify_ref(ref):
    r=load(ref/faithful.REPORT)
    need(r["status"]=="FAITHFUL_C14_RUNTIME_READY" and r["native_diagnostic_parity"] and r["solver_completed"],"accepted reference required")
    need(sha(ref/"log.foamMultiRun")==r["solver"]["log_sha256"],"reference log changed")
    for k,h in r["input_sha256"].items():need(sha(ref/k)==h,"reference input drift "+k)
    need((ref/"system/controlDict").read_bytes()==(faithful.physics.C14/"system/controlDict").read_bytes(),"reference controlDict drift")
    return r

def run_level(ref,ref_report,source,out,dt,interval,tools):
    expected=times(dt);original=faithful.read(ref/"system/controlDict")
    changed=control(original,dt,interval)
    if out.exists():
        p=out/REPORT
        need(p.is_file(),"existing incomplete case preserved "+str(out))
        r=load(p)
        need(r.get("status")=="TEMPORAL_NATIVE_READY" and r.get("dt_s")==dt and r.get("reference_log_sha256")==ref_report["solver"]["log_sha256"],"existing incomplete or different temporal case preserved "+str(out))
        need(sha(out/"log.foamMultiRun")==r["solver"]["log_sha256"],"existing temporal log drift")
        need(tree_hash(out,("constant","system"))==r["input_sha256"],"existing temporal inputs drift")
        need(primary_hashes(out)==r["primary_sha256"],"existing temporal fields drift")
        return r
    stage.stage(source,out,smoke=False)
    r={"status":"PREPARED_NOT_EXECUTED","case":str(out),"dt_s":dt,"writeInterval":interval,"write_period_s":.1,
       "reference_log_sha256":ref_report["solver"]["log_sha256"],"solver_completed":False}
    try:
        need(faithful.mesh_hashes(out)==faithful.mesh_hashes(ref),"different mesh")
        for k in stage.input_files(8960,smoke=False,existing_zone=True):
            if k.startswith(("constant/","system/")):
                need((out/k).read_bytes()==(ref/k).read_bytes(),"physical dictionary drift "+k)
        for name in DICTS:shutil.copy2(ref/"system"/name,out/"system"/name)
        (out/"system/controlDict").write_bytes(changed.encode("utf-8"))
        stage.native([tools["foamDictionary"],str(out/"system/controlDict")],out,"log.dict.temporalControl",60)
        tracked=tree_hash(out,("constant","system"))
        r["input_sha256"]=tracked
        r["status"]="RUNNING_TEMPORAL_NATIVE"
        save(out/REPORT,r)
        # Proven faithful runner checks actual step sequence and full profiles.
        # Only its expected cadence is adjusted for this isolated invocation.
        old=faithful.PROBE_TIMES
        try:
            faithful.PROBE_TIMES=expected
            print(f"=== Caso A: deltaT={dt:g}, {len(expected)-1} pasos ===",flush=True)
            r["solver"]=faithful.stream_solver(out,tools["foamMultiRun"])
            r["solver_completed"]=True
            r["coverage"]=faithful.audit_outputs(out,ref_report["sampling"])
        finally:faithful.PROBE_TIMES=old
        need(r["coverage"]["native_diagnostic_parity"],"native diagnostic coverage incomplete")
        need(tree_hash(out,("constant","system"))==tracked,"inputs changed during run")
        tool=shutil.which("foamLog")
        need(tool is not None,"foamLog unavailable")
        with (out/"log.foamLog").open("x",encoding="utf-8") as f:
            rc=subprocess.run([tool,"log.foamMultiRun"],cwd=out,stdout=f,stderr=subprocess.STDOUT).returncode
        need(rc==0 and (out/"logs").is_dir(),"foamLog failed")
        r["primary_sha256"]=primary_hashes(out)
        (out/"C14_3D_A_temporal.foam").touch(exist_ok=False)
        r["status"]="TEMPORAL_NATIVE_READY"
        return r
    except BaseException as e:
        r["status"]="TEMPORAL_RUN_PRESERVED_INCOMPLETE";r["error"]=str(e);raise
    finally:save(out/REPORT,r)

def read_rows(path):
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):continue
        # Ignore optional locations/labels in extrema tables. No such tables
        # are used in this analysis; scalar and vector probes only.
        v=[float(x) for x in line.replace("("," ").replace(")"," ").split()]
        need(all(map(math.isfinite,v)),"nonfinite data "+str(path));rows.append(v)
    return rows
def aligned(case,field,dt):
    p=case/"postProcessing/metal/temperatureProbe/0"/field
    rows=read_rows(p)
    need(faithful.exact_times([r[0] for r in rows],times(dt)),"probe time grid drift "+str(p))
    stride=round(.001/dt)
    a=rows[::stride]
    need(len(a)==10001,"probe common time count")
    return [math.hypot(*r[1:]) if field=="U" else r[1] for r in a]
def reduction(case,name,col=1,surface=False):
    p=case/"postProcessing/metal"/name/"0"/("surfaceFieldValue.dat" if surface else "volFieldValue.dat")
    r=read_rows(p);need(faithful.exact_times([x[0] for x in r],TIMES),"native reduction cadence drift "+str(p))
    return [x[col] for x in r]
def stats(a,b):
    d=[y-x for x,y in zip(a,b)]
    return {"rmse":math.sqrt(math.fsum(x*x for x in d)/len(d)),"bias":math.fsum(d)/len(d),
            "max_abs":max(map(abs,d)),"final_delta":d[-1]}
def order(a,b,c):
    # An apparent order for a scalar at a common instant is meaningful only
    # for monotone convergence and nonzero differences. Not a proof of
    # asymptotic range, not a spatial GCI.
    d1=a-b;d2=b-c
    if d1*d2<=0 or abs(d2)<1e-15:return None
    p=math.log(abs(d1/d2),2)
    return p if math.isfinite(p) and p>0 else None
def csvout(path,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def crossing(values,threshold,dt=.001):
    i=next((i for i,v in enumerate(values) if v<threshold),None)
    return None if i is None else [max(0,i-1)*dt,i*dt]
def analyze(ref,cases,out):
    out.mkdir()
    probe={f:[aligned(case,f,dt) for case,(_,dt,_) in zip(cases,LEVELS)] for f in ("T","U","phaseChangeSource:alpha1","p_rgh","rho")}
    prows=[{"time_s":i/1000,**{f"{name}_{tag}":probe[name][j][i] for name in probe for j,(tag,_,_) in enumerate(LEVELS)}} for i in range(10001)]
    csvout(out/"probe_common_10001.csv",prows)
    native_cross={}
    for case,(tag,dt,_) in zip(cases,LEVELS):
        T=read_rows(case/"postProcessing/metal/temperatureProbe/0/T")
        A=read_rows(case/"postProcessing/metal/temperatureProbe/0/phaseChangeSource:alpha1")
        native_cross[tag]={"first_T_below_liquidus_interval_s":crossing([r[1] for r in T],1473,dt),
                           "first_alpha_below_one_interval_s":crossing([r[1] for r in A],1,dt)}
    reductions={"H_J":("metalSensibleEnthalpy",1,False),"alphaL":("metalMeanLiquidFraction",1,False),
                "latent_W":("metalLatentHeatPower",1,False),"cooling_K_s":("metalMeanCoolingRate",1,False),
                "solidification_s_inv":("metalMeanSolidificationRate",1,False),
                "metal_total_out_W":("metalBoundaryEnergyPower",3,True),
                "metal_contact_out_W":("metalMoldEnergyPower",3,True),"metal_top_out_W":("metalTopEnergyPower",3,True)}
    red={key:[reduction(case,*spec) for case in cases] for key,spec in reductions.items()}
    V=4.7921447006662436e-5;capacity=6820*827*V;latent_capacity=6820*228600*V
    red["T_mean_reconstructed_K"]=[[1500+(v[i]-v[0])/capacity for i in range(101)] for v in red["H_J"]]
    red["solid_fraction"]=[[1-x for x in v] for v in red["alphaL"]]
    rows=[{"time_s":t,**{f"{name}_{tag}":red[name][j][i] for name in red for j,(tag,_,_) in enumerate(LEVELS)}} for i,t in enumerate(TIMES)]
    csvout(out/"thermal_common_101.csv",rows)
    # Compare internal fields at same cells and same physical times.
    w={r:vol.cell_volumes(ref,r,n) for r,n in COUNTS.items()}
    field_rows=[]
    for t in LABELS:
        for r,fields in FIELDS.items():
            for f in fields:
                vector=f=="U"
                vals=[vol.vector_field(case/t/r/f,COUNTS[r]) if vector else native.scalar_field_values(case/t/r/f,COUNTS[r]) for case in cases]
                for k in (0,1):
                    d=[math.dist(x,y) for x,y in zip(vals[k],vals[k+1])] if vector else [y-x for x,y in zip(vals[k],vals[k+1])]
                    field_rows.append({"time_s":float(t),"region":r,"field":f,"pair":f"{LEVELS[k][0]}_vs_{LEVELS[k+1][0]}",
                                       "rmse_volume":math.sqrt(vol.weighted([x*x for x in d],w[r])),"max_abs":max(map(abs,d))})
    csvout(out/"cellwise_common_101.csv",field_rows)
    metrics={}
    for name,levels in {**{f"probe_{k}":v for k,v in probe.items()},**red}.items():
        a,b,c=levels
        metrics[name]={"coarse_to_medium":stats(a,b),"medium_to_fine":stats(b,c),"final_values":[a[-1],b[-1],c[-1]],
                       "apparent_final_order_if_monotone":order(a[-1],b[-1],c[-1])}
    balances={}
    for j,(tag,_,_) in enumerate(LEVELS):
        H,F,Q,P=(red[k][j] for k in ("H_J","alphaL","metal_total_out_W","latent_W"))
        for start in (0,1):
            integ=lambda x:math.fsum((x[i]+x[i-1])*.05 for i in range(start+1,101))
            q,p=integ(Q),integ(P);h=H[start]-H[-1];l=latent_capacity*(F[start]-F[-1])
            balances[tag+f"_from_{TIMES[start]:g}s"]={"Q_out_J":q,"sensible_release_J":h,"latent_inventory_J":l,"latent_power_integral_J":p,
                                                        "inventory_residual_J":q-h-l,"power_residual_J":q-h-p}
    # Engineering screening thresholds, proposed rather than claimed
    # scientific acceptance; absolute units and two refinement pairs.
    thresholds={"probe_T":{"rmse":.5,"max_abs":1.},"T_mean_reconstructed_K":{"rmse":.25,"max_abs":.5},
                "solid_fraction":{"rmse":.001,"max_abs":.002},"probe_U":{"rmse":.00025,"max_abs":.001}}
    screen={k:all(metrics[k]["medium_to_fine"][m]<=v for m,v in limits.items()) for k,limits in thresholds.items()}
    summary={"status":"TEMPORAL_THREE_LEVEL_RESULTS_READY_NOT_VALIDATION","same_mesh":True,"native_crossings":native_cross,
             "common_probe_times":10001,"common_saved_states":101,"metrics":metrics,"metal_saved_state_energy":balances,
             "field_maxima":{r+"/"+f:{pair:max(x["rmse_volume"] for x in field_rows if x["region"]==r and x["field"]==f and x["pair"]==pair)
                 for pair in (field_rows[0]["pair"],field_rows[1]["pair"])} for r,fields in FIELDS.items() for f in fields},
             "proposed_medium_fine_screen_thresholds":thresholds,"screen_results":screen,
             "screen_pass":all(screen.values()),"reference_time_step_independent":False,"spatial_independence_verified":False,
             "discrete_energy_conservation_verified":False,"experimental_validation":False,
             "limits":["Fixed spatial mesh; native reduction write interval 0.1s retained.",
                       "Probe comparison at exact common 0.001s instants, no interpolation.",
                       "Apparent scalar order only when monotone and positive; not proof of asymptotic range.",
                       "Screening tolerances are provisional engineering criteria, not approved thesis acceptance.",
                       "Energy diagnostic integrates saved rates, not all solver-step terms."]}
    save(out/SUMMARY,summary);return summary

def execute(ref,source,root):
    ref,source,root=(p.expanduser().resolve() for p in (ref,source,root))
    need(root.parent==HOME.resolve() and root not in (ref,source),"isolated study root required")
    r=verify_ref(ref);before=tree_hash(ref,("constant","system"));fields_before=primary_hashes(ref)
    tools=stage.environment()
    root.mkdir(exist_ok=True)
    cases=[ref]
    # Each run is sequential to avoid multiplying memory load.
    for name,dt,interval in LEVELS[1:]:
        out=root/name
        run_level(ref,r,source,out,dt,interval,tools);cases.append(out)
    dest=root/"analysis_results"
    if dest.exists():
        summary=load(dest/SUMMARY)
    else:
        with tempfile.TemporaryDirectory(prefix=".analysis.",dir=root) as tmp:
            candidate=Path(tmp)/"result";summary=analyze(ref,cases,candidate)
            candidate.rename(dest)
    need(tree_hash(ref,("constant","system"))==before and primary_hashes(ref)==fields_before,"reference changed")
    summary={**summary,"reference_unchanged":True,"output":str(dest)}
    save(dest/SUMMARY,summary)
    return summary
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reference",type=Path,default=REF)
    p.add_argument("--source",type=Path,default=stage.SOURCE)
    p.add_argument("--out",type=Path,default=ROOT)
    a=p.parse_args()
    try:
        r=execute(a.reference,a.source,a.out);print(json.dumps(r,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,subprocess.SubprocessError) as e:
        print("A_TEMPORAL_SENSITIVITY_BLOCKED:",e,file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
