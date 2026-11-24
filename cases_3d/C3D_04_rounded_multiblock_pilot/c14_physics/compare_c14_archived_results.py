#!/usr/bin/env python3
"""Compare real archived C14 2D outputs against existing A sweeps. No CFD or sampling."""
from __future__ import annotations
import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import shutil

ROOT=Path(__file__).resolve().parents[3]
REF=ROOT/"cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
TIMES=[i/10 for i in range(101)]
VARS=("T_K","alphaL","U_mag_m_s","gradT_mag_K_m")
FULL=("T_K","alphaL","Ux_m_s","Uy_m_s","Uz_m_s","U_mag_m_s","gradTx_K_m","gradTy_K_m","gradTz_K_m","gradT_mag_K_m")
HEIGHTS=(10,20,30)
ANGLES=(0,45,90,135)

def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def time_label(t):return format(t,"g")
def number(v):
    if v is None or v=="":return None
    n=float(v)
    need(math.isfinite(n),"nonfinite data")
    return n
def readcsv(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def writecsv(p,rows):
    need(rows,"empty CSV "+str(p))
    with p.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def read_table(p,width=None):
    data=[]
    for l in p.read_text(encoding="utf-8").splitlines():
        if not l.strip() or l.lstrip().startswith("#"):continue
        row=[float(x) for x in l.split()]
        need((width is None or len(row)==width) and all(math.isfinite(x) for x in row),"invalid archived data "+str(p))
        data.append(row)
    need(data,"empty archive "+str(p))
    return data
def index_series(p,expected,width):
    rows=read_table(p,width)
    need(len(rows)==len(expected) and all(abs(r[0]-t)<1e-8 for r,t in zip(rows,expected)),"time coverage mismatch: "+str(p))
    return dict(zip(expected,rows))
def group(rows,keys):
    out={}
    for r in rows:out.setdefault(tuple(r[k] for k in keys),[]).append(r)
    return out
def archive_profile(p):
    # Validate column order against actual archived C14 header (truncated
    # phase name is known from original lineProfiles dictionary).
    h=p.read_text(encoding="utf-8").splitlines()[0].lstrip("#").split()
    need(h[0] in ("x","y") and h[1:7]==["U_x","U_y","U_z","T","p_rgh","rho"]
         and h[7].startswith("phaseChang") and h[13:17]==["gradT_x","gradT_y","gradT_z","magGradT"],"unexpected C14 profile schema "+str(p))
    raw=read_table(p,len(h))
    need(len(raw)==80 and all(abs(r[0]-(.00025+i*.0005))<1e-8 for i,r in enumerate(raw)),"unexpected C14 profile axis "+str(p))
    return [{"position_mm":r[0]*1000,"T_K":r[4],"alphaL":r[7],"Ux_m_s":r[1],"Uy_m_s":r[2],"Uz_m_s":r[3],
             "U_mag_m_s":math.sqrt(sum(x*x for x in r[1:4])),"gradTx_K_m":r[13],"gradTy_K_m":r[14],
             "gradTz_K_m":r[15],"gradT_mag_K_m":r[16]} for r in raw]
def interp(rows,x,k,step):
    xs=[float(r["position_mm"]) for r in rows]
    i=bisect.bisect_left(xs,x)
    if i<len(xs) and abs(xs[i]-x)<1e-7:return number(rows[i].get(k))
    if i>0 and abs(xs[i-1]-x)<1e-7:return number(rows[i-1].get(k))
    if i==0 or i==len(xs) or xs[i]-xs[i-1]>step+1e-6:return None
    a,b=number(rows[i-1].get(k)),number(rows[i].get(k))
    if a is None or b is None:return None
    return a+(b-a)*(x-xs[i-1])/(xs[i]-xs[i-1])
def metrics(pairs):
    d=[b-a for a,b in pairs if a is not None and b is not None]
    return {"n":len(d),"bias":math.fsum(d)/len(d) if d else None,
            "RMSE":math.sqrt(math.fsum(x*x for x in d)/len(d)) if d else None,
            "max_abs":max(map(abs,d),default=None)}
def first_change(rows,k,threshold,below=True):
    prev=None
    for r in rows:
        v=r.get(k)
        if v is not None and (v<threshold if below else v>threshold):
            return [prev,r["time_s"]]
        prev=r["time_s"] if v is not None else None
    return None

def execute(ref,vis,sweeps,out):
    ref,vis,sweeps=(p.expanduser().resolve() for p in (ref,vis,sweeps))
    out=out.expanduser().absolute()
    need(out.parent.resolve()==(vis/"analysis").resolve() and not out.exists(),"fresh analysis subdirectory required")
    sr=json.loads((sweeps/"C3D04_A_MULTIDIRECTIONAL_REPORT.json").read_text())
    need(sr["status"]=="MULTIDIRECTIONAL_3D_READY" and sr["saved_times"]==101 and Path(sr["source"]).resolve()==vis,
         "successful existing 3D sweep archive required; do not rerun it")
    vr=json.loads((vis/"C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json").read_text())
    need(vr["status"]=="VISUALIZATION_AND_SOLIDIFICATION_READY","verified visual case required")
    pp=ref/"postProcessing/metal"
    tprobe=pp/"temperatureProbe/0/T"
    aprobe=pp/"temperatureProbe/0/phaseChangeSource:alpha1"
    vphase=pp/"metalMeanLiquidFraction/0/volFieldValue.dat"
    enthalpy=pp/"metalSensibleEnthalpy/0/volFieldValue.dat"
    top=pp/"metalTopEnergyPower/0/surfaceFieldValue.dat"
    contact=pp/"metalMoldEnergyPower/0/surfaceFieldValue.dat"
    p2=[tprobe,aprobe,vphase,enthalpy,top,contact]
    # Exact physical values taken from the canonical reference dictionaries.
    mat=ref/"constant/metal/materials/castIron"
    phase=ref/"constant/metal/fvModels"
    import re
    def prop(path,key):
        raw=re.sub(r"/\*.*?\*/|//[^\n]*","",path.read_text(),flags=re.S)
        m=re.search(r"\b"+re.escape(key)+r"\s+([0-9.eE+-]+)\s*;",raw)
        need(m is not None,"missing physical property "+key)
        return float(m.group(1))
    rho,cp,latent=prop(mat,"rho"),prop(mat,"Cp"),prop(phase,"L")
    need((rho,cp,latent)==(6820,827,228600),"unexpected reference physical values")
    p2.extend([mat,phase])
    probe_times=[i/1000 for i in range(10001)]
    tp=index_series(tprobe,probe_times,2);ap=index_series(aprobe,probe_times,2)
    va=index_series(vphase,TIMES,2);hh=index_series(enthalpy,TIMES,2)
    qtop=index_series(top,TIMES,4);qc=index_series(contact,TIMES,4)
    # 2D native reduction geometry, not guessed from cell count.
    def header(p,key):
        m=re.search(r"(?m)^#\s*"+key+r"\s*:\s*([0-9.eE+-]+)",p.read_text())
        need(m is not None,"missing reduction geometry "+str(p))
        return float(m.group(1))
    V2=header(vphase,"Volume");A2=header(contact,"Area");At2=header(top,"Area")
    need(abs(V2-1.6e-5)<1e-10 and abs(A2-.0012)<1e-9,"unexpected C14 reduction geometry")
    p3=[sweeps/"diameters_101.csv",sweeps/"vertical_lines_101.csv",
        sweeps/"C3D04_A_MULTIDIRECTIONAL_REPORT.json",vis/"analysis/solidification_101.csv",
        vis/"analysis/boundary_native_q_101.csv",vis/"analysis/energy_inventory_101.csv",
        vis/"C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json"]
    d=group(readcsv(p3[0]),("time_s","height_mm","angle_deg"))
    v=group(readcsv(p3[1]),("time_s","line"))
    def normalized_groups(raw):
        return {(float(k[0]),*k[1:]):sorted(rows,key=lambda r:float(r["position_mm"])) for k,rows in raw.items()}
    d=normalized_groups(d);v=normalized_groups(v)
    solid={float(r["time_s"]):r for r in readcsv(p3[3])}
    need(sorted(solid)==TIMES,"missing 3D solidification states")
    qr=readcsv(p3[4]);q={(float(r["time_s"]),r["region"],r["patch"]):r for r in qr}
    need(len(q)==808,"unexpected 3D patch records")
    # Match volume to original accepted A geometry, already audited in WSL.
    V3=.000047921447006662436  # audited native V4/T02 metal volume; scope restricted by visual report and area check
    A3=number(q[(0.0,"metal","metal_to_mold")]["area_m2"])
    At3=number(q[(0.0,"metal","metalTop")]["area_m2"])
    need(abs(A3-.006343771874)<1e-8,"wrong 3D interface area")
    profiles=[];pm=[];curves=[];globalrows=[]
    for t in TIMES:
        l=time_label(t)
        for h in HEIGHTS:
            p=pp/"horizontalProfiles"/l/("line_y"+str(h)+"mm.xy")
            p2.append(p);r2=archive_profile(p)
            for a in ANGLES:
                r3=d[(t,str(h),str(a))]
                # 2D absolute x becomes center-relative; 3D already signed.
                block=[]
                for row in r2:
                    x=row["position_mm"]-20
                    z={"time_s":t,"station":"horizontal"+str(h),"angle_deg":a,"position_mm":row["position_mm"]}
                    for k in FULL:
                        # Rotated diameters compare scalar quantities only;
                        # global vector components are direct only at 0°.
                        aa=row[k] if a==0 or k in VARS else None
                        bb=interp(r3,x,k,.5) if aa is not None else None
                        z[k+"_2D"]=aa;z[k+"_3D"]=bb;z[k+"_delta"]=bb-aa if aa is not None and bb is not None else None
                    block.append(z)
                profiles.extend(block)
                for k in FULL:
                    if a!=0 and k not in VARS:continue
                    pm.append({"time_s":t,"station":"horizontal"+str(h),"angle_deg":a,"variable":k,**metrics([(r[k+"_2D"],r[k+"_3D"]) for r in block])})
            r3=d[(t,str(h),"0")]
            # 20 mm is a genuine native 2D probe; the other heights are
            # interpolated between 2D archived profile points. 3D is center
            # lineUniform cellPoint sample, not necessarily same probe scheme.
            r={"time_s":t,"station":"center"+str(h),
               "T_K_2D":tp[t][1] if h==20 else interp(r2,20,"T_K",.5),
               "T_K_3D":interp(r3,0,"T_K",.5),
               "alphaL_2D":ap[t][1] if h==20 else interp(r2,20,"alphaL",.5),
               "alphaL_3D":interp(r3,0,"alphaL",.5),
               "T_delta_K":None,"alphaL_delta":None,"cooling_K_s_2D":None,"cooling_K_s_3D":None}
            for k,delta in (("T_K","T_delta_K"),("alphaL","alphaL_delta")):
                if r[k+"_3D"] is not None and r[k+"_2D"] is not None:r[delta]=r[k+"_3D"]-r[k+"_2D"]
            if curves:
                old=next((x for x in reversed(curves) if x["station"]==r["station"]),None)
                if old:
                    for dim in ("2D","3D"):
                        a0,b0=old["T_K_"+dim],r["T_K_"+dim]
                        if a0 is not None and b0 is not None:r["cooling_K_s_"+dim]=(a0-b0)/(t-old["time_s"])
            curves.append(r)
        p=pp/"verticalProfiles"/l/"line_x20mm.xy";p2.append(p)
        r2=archive_profile(p);r3=v[(t,"v_center")];block=[]
        for row in r2:
            z={"time_s":t,"station":"vertical","angle_deg":"","position_mm":row["position_mm"]}
            for k in FULL:
                aa=row[k];bb=interp(r3,row["position_mm"],k,.5)
                z[k+"_2D"]=aa;z[k+"_3D"]=bb;z[k+"_delta"]=bb-aa if bb is not None else None
            block.append(z)
        profiles.extend(block)
        for k in FULL:pm.append({"time_s":t,"station":"vertical","angle_deg":"","variable":k,**metrics([(r[k+"_2D"],r[k+"_3D"]) for r in block])})
        row={"time_s":t,"T_mean_2D_reconstructed_K":1500+(hh[t][1]-hh[0][1])/(rho*cp*V2),
             "T_mean_3D_K":number(solid[t]["metal_T_volume_mean_K"]),
             "solid_fraction_2D":1-va[t][1],"solid_fraction_3D":number(solid[t]["solid_fraction_volume_mean"]),
             "q_contact_2D_W":qc[t][2],"q_contact_3D_W":number(q[(t,"metal","metal_to_mold")]["q_out_W"]),
             "q_top_2D_W":qtop[t][2],"q_top_3D_W":number(q[(t,"metal","metalTop")]["q_out_W"])}
        for dim,V,A,At in (("2D",V2,A2,At2),("3D",V3,A3,At3)):
            row["q_contact_per_volume_"+dim+"_W_m3"]=row["q_contact_"+dim+"_W"]/V
            row["q_contact_per_area_"+dim+"_W_m2"]=row["q_contact_"+dim+"_W"]/A
            row["q_top_per_area_"+dim+"_W_m2"]=row["q_top_"+dim+"_W"]/At
            row["nominal_latent_release_per_volume_"+dim+"_J_m3"]=rho*latent*row["solid_fraction_"+dim]
        row["T_mean_delta_K"]=row["T_mean_3D_K"]-row["T_mean_2D_reconstructed_K"]
        globalrows.append(row)
    summaries=[]
    for h in HEIGHTS:
        rr=[r for r in curves if r["station"]=="center"+str(h)]
        summaries.append({"station":"center"+str(h),"T_metrics":metrics([(r["T_K_2D"],r["T_K_3D"]) for r in rr]),
                          "alpha_metrics":metrics([(r["alphaL_2D"],r["alphaL_3D"]) for r in rr]),
                          "first_below_Tliq_2D_interval_s":first_change(rr,"T_K_2D",1473),
                          "first_below_Tliq_3D_interval_s":first_change(rr,"T_K_3D",1473),
                          "final":rr[-1]})
    need(summaries[1]["T_metrics"]["n"]>=2,"no common central curve")
    need(all(any(r["station"]==station and r["variable"]=="T_K" and r["n"]>=2 for r in pm) for station in ("horizontal10","horizontal20","horizontal30","vertical")),"missing common spatial support")
    out.parent.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".C14_compare_",dir=out.parent))
    try:
        for name,rs in (("cooling_curves_101.csv",curves),("global_thermal_101.csv",globalrows),
                        ("spatial_profiles_common_grid.csv",profiles),("profile_metrics.csv",pm)):
            writecsv(temp/name,rs)
        report={"status":"ARCHIVED_C14_2D_3D_COMPARISON_READY","case_2D":str(ref),"case_3D":str(vis),
                "saved_times":101,"native_2D_center_probe_samples":10001,
                "center_curves":summaries,"final_global":globalrows[-1],
                "area_volume":{"2D_m_inv":A2/V2,"3D_m_inv":A3/V3,"ratio":(A3/V3)/(A2/V2)},
                "final_T_profile_metrics":[r for r in pm if r["time_s"]==10 and r["variable"]=="T_K"],
                "source_sha256":{str(p):sha(p) for p in p2+p3},
                "limits":["2D mean T inferred from constant rho/Cp and native enthalpy delta",
                          "2D center 20 mm uses native probe; other center data interpolated from archived line profiles; 3D uses cellPoint line center",
                          "3D diameters interpolated only between neighboring valid 0.5 mm samples, no extrapolation",
                          "rotated diameters compare scalar quantities, not global vector components",
                          "2D flux t=0 is zero as archived; no initial-flux equivalence or energy integration claimed",
                          "different geometry, no grid independence or validation claim"],
                "solver_rerun":False,"native_sampling_rerun":False,"grid_independence_verified":False,"quickcup_validated":False}
        (temp/"C14_ARCHIVED_COMPARISON_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
        need(not out.exists(),"output appeared; preserved")
        temp.rename(out)
        return report
    finally:
        if temp.exists():shutil.rmtree(temp)

def main():
    home=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ref",type=Path,default=REF)
    p.add_argument("--case",type=Path,default=home/"C3D04_A_C14_VISUALIZATION_01")
    p.add_argument("--sweeps",type=Path,default=home/"C3D04_A_C14_MULTIDIRECTIONAL_01")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    try:
        out=a.out or a.case/"analysis/C14_2D_3D_ARCHIVED_COMPARISON_01"
        r=execute(a.ref,a.case,a.sweeps,out)
        print(json.dumps({k:v for k,v in r.items() if k!="source_sha256"},indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print("ARCHIVED_C14_COMPARISON_BLOCKED:",e,file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
