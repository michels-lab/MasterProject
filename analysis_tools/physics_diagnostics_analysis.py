#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases_controlled_buoyancy"
OUT = ROOT / "analysis_results" / "physics_diagnostics"
OUT.mkdir(parents=True, exist_ok=True)

CASE_NAMES = [
    "B3_reference","B4_energy2","B5_outer3","B6_adaptiveDt","B7_outer4",
    "C3_reference","C4_energy2","C5_outer3","C6_adaptiveDt","C7_outer4",
]

PROFILES = {
    "y20mm": ("horizontalProfiles", "line_y20mm.xy"),
    "y30mm": ("horizontalProfiles", "line_y30mm.xy"),
    "vertical_x20mm": ("verticalProfiles", "line_x20mm.xy"),
}

def numeric_dirs(path: Path):
    out=[]
    if not path.is_dir(): return out
    for p in path.iterdir():
        if p.is_dir():
            try: out.append((float(p.name),p))
            except ValueError: pass
    return sorted(out)

def read_profile(path: Path):
    rows=[]
    with path.open() as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            vals=[float(x) for x in s.split()]
            rows.append(vals)
    return rows

def corr(a,b):
    if not a or len(a)!=len(b): return float("nan")
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    xa=[x-ma for x in a]; xb=[x-mb for x in b]
    den=math.sqrt(sum(x*x for x in xa)*sum(x*x for x in xb))
    return sum(x*y for x,y in zip(xa,xb))/den if den else float("nan")

def profile_metrics(rows):
    uy=[r[2] for r in rows]
    wz=[r[10] for r in rows]
    ft=[r[11] for r in rows]
    strength=[r[12] for r in rows]
    n=len(rows)
    rms_w=math.sqrt(sum(x*x for x in wz)/n)
    mean_abs_w=sum(abs(x) for x in wz)/n
    max_abs_w=max(abs(x) for x in wz)
    rot=sum(x>0.2 for x in ft)/n
    shear=sum(abs(x)<=0.2 for x in ft)/n
    deform=sum(x<-0.2 for x in ft)/n
    total_s=sum(strength)
    rot_s=sum(s for s,x in zip(strength,ft) if x>0.2)
    shear_s=sum(s for s,x in zip(strength,ft) if abs(x)<=0.2)
    def_s=sum(s for s,x in zip(strength,ft) if x<-0.2)
    return {
        "n":n,
        "rms_vorticity_z":rms_w,
        "mean_abs_vorticity_z":mean_abs_w,
        "max_abs_vorticity_z":max_abs_w,
        "mean_flowType":sum(ft)/n,
        "rotational_fraction":rot,
        "parallel_shear_fraction":shear,
        "deformation_fraction":deform,
        "rotational_strength_share":rot_s/total_s if total_s else float("nan"),
        "parallel_shear_strength_share":shear_s/total_s if total_s else float("nan"),
        "deformation_strength_share":def_s/total_s if total_s else float("nan"),
        "corr_abs_vorticity_abs_Uy":corr([abs(x) for x in wz],[abs(x) for x in uy]),
    }

profile_rows=[]
for case in CASE_NAMES:
    for pkey,(folder,filename) in PROFILES.items():
        root=CASES/case/"postProcessing"/"metal"/folder
        for t,d in numeric_dirs(root):
            fp=d/filename
            if not fp.is_file(): continue
            m=profile_metrics(read_profile(fp))
            profile_rows.append({"case":case,"profile":pkey,"time_s":t,**m})

with (OUT/"profile_vorticity_flowtype.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(profile_rows[0].keys()))
    w.writeheader(); w.writerows(profile_rows)

def read_table(path: Path):
    rows=[]
    with path.open() as f:
        for line in f:
            s=line.strip()
            if not s or s.startswith("#"): continue
            vals=[float(x) for x in s.split()]
            rows.append(vals)
    return rows

def trapz(times,vals):
    return sum(0.5*(vals[i]+vals[i-1])*(times[i]-times[i-1]) for i in range(1,len(times)))

energy_rows=[]
energy_summary=[]
for case in CASE_NAMES:
    base=CASES/case/"postProcessing"/"metal"
    top=read_table(base/"metalTopEnergyPower"/"0"/"surfaceFieldValue.dat")
    mold=read_table(base/"metalMoldEnergyPower"/"0"/"surfaceFieldValue.dat")
    bd=read_table(base/"metalBoundaryEnergyPower"/"0"/"surfaceFieldValue.dat")
    lat=read_table(base/"metalLatentHeatPower"/"0"/"volFieldValue.dat")
    hs=read_table(base/"metalSensibleEnthalpy"/"0"/"volFieldValue.dat")
    bytime={r[0]:r for r in top}
    mt={r[0]:r for r in mold}; bt={r[0]:r for r in bd}; lt={r[0]:r for r in lat}; ht={r[0]:r for r in hs}
    times=sorted(set(bytime)&set(mt)&set(bt)&set(lt)&set(ht))
    H=[ht[t][1] for t in times]
    dH=[]
    for i,t in enumerate(times):
        if len(times)==1: dh=float("nan")
        elif i==0: dh=(H[1]-H[0])/(times[1]-times[0])
        elif i==len(times)-1: dh=(H[-1]-H[-2])/(times[-1]-times[-2])
        else: dh=(H[i+1]-H[i-1])/(times[i+1]-times[i-1])
        dH.append(dh)
    for i,t in enumerate(times):
        ta,th,tt=bytime[t][1:4]
        ma,mh,mtot=mt[t][1:4]
        ba,bh,btot=bt[t][1:4]
        lp=lt[t][1]
        denom=abs(ba)+abs(bh)
        mold_share=abs(mh)/(abs(mh)+abs(th)) if abs(mh)+abs(th) else float("nan")
        closure=dH[i]+btot-lp
        energy_rows.append({
            "case":case,"time_s":t,
            "top_advective_W":ta,"top_diffusive_W":th,"top_total_W":tt,
            "mold_advective_W":ma,"mold_diffusive_W":mh,"mold_total_W":mtot,
            "boundary_advective_W":ba,"boundary_diffusive_W":bh,"boundary_total_W":btot,
            "latent_power_W":lp,"sensible_enthalpy_J":H[i],"dHsensible_dt_W":dH[i],
            "boundary_advective_abs_fraction":abs(ba)/denom if denom else float("nan"),
            "mold_diffusive_abs_share":mold_share,
            "energy_closure_residual_W":closure,
        })
    def col(src,idx): return [r[idx] for r in src if r[0] in times]
    top_rows=[bytime[t] for t in times]; mold_rows=[mt[t] for t in times]; b_rows=[bt[t] for t in times]; l_rows=[lt[t] for t in times]
    E_top_adv=trapz(times,[r[1] for r in top_rows])
    E_top_diff=trapz(times,[r[2] for r in top_rows])
    E_mold_adv=trapz(times,[r[1] for r in mold_rows])
    E_mold_diff=trapz(times,[r[2] for r in mold_rows])
    E_boundary=trapz(times,[r[3] for r in b_rows])
    E_boundary_adv=trapz(times,[r[1] for r in b_rows])
    E_boundary_diff=trapz(times,[r[2] for r in b_rows])
    E_lat=trapz(times,[r[1] for r in l_rows])
    deltaH=H[-1]-H[0]
    closure=deltaH+E_boundary-E_lat
    energy_summary.append({
        "case":case,"t_end_s":times[-1],
        "E_top_advective_J":E_top_adv,"E_top_diffusive_J":E_top_diff,
        "E_mold_advective_J":E_mold_adv,"E_mold_diffusive_J":E_mold_diff,
        "E_boundary_total_J":E_boundary,"E_boundary_advective_J":E_boundary_adv,
        "E_boundary_diffusive_J":E_boundary_diff,"E_latent_release_J":E_lat,
        "delta_sensible_enthalpy_J":deltaH,
        "integrated_energy_closure_J":closure,
        "mold_share_of_abs_diffusive_energy":abs(E_mold_diff)/(abs(E_mold_diff)+abs(E_top_diff)) if abs(E_mold_diff)+abs(E_top_diff) else float("nan"),
        "advective_share_of_abs_boundary_transport":abs(E_boundary_adv)/(abs(E_boundary_adv)+abs(E_boundary_diff)) if abs(E_boundary_adv)+abs(E_boundary_diff) else float("nan"),
    })

with (OUT/"energy_time_series.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(energy_rows[0].keys()))
    w.writeheader(); w.writerows(energy_rows)

with (OUT/"energy_integrated_summary.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(energy_summary[0].keys()))
    w.writeheader(); w.writerows(energy_summary)

def fmt(x,n=3):
    return "n/a" if not math.isfinite(x) else f"{x:.{n}f}"

lines=["# Physics diagnostics summary","",
"OpenFOAM Foundation v14 flowType convention used here: flowType > 0.2 is classified as rotational-dominated, |flowType| <= 0.2 as near parallel-shear, and flowType < -0.2 as deformation-dominated. These are profile-sample classifications, not volume fractions.",""]

for case in CASE_NAMES:
    lines += [f"## {case}",""]
    es=next(x for x in energy_summary if x["case"]==case)
    lines += [
        f"- time range: 0–{es['t_end_s']:g} s",
        f"- integrated boundary energyFlux: {es['E_boundary_total_J']:.3f} J",
        f"- integrated boundary advective contribution: {es['E_boundary_advective_J']:.3f} J",
        f"- integrated boundary diffusive contribution: {es['E_boundary_diffusive_J']:.3f} J",
        f"- integrated metal-to-mold diffusive contribution: {es['E_mold_diffusive_J']:.3f} J",
        f"- integrated top diffusive contribution: {es['E_top_diffusive_J']:.3f} J",
        f"- mold share of |diffusive| boundary transport: {100*es['mold_share_of_abs_diffusive_energy']:.2f}%",
        f"- |advective| share of boundary advective+diffusive integrated transport: {100*es['advective_share_of_abs_boundary_transport']:.2f}%",
        f"- integrated latent heat release diagnostic: {es['E_latent_release_J']:.3f} J",
        f"- sensible enthalpy change: {es['delta_sensible_enthalpy_J']:.3f} J",
        f"- integrated closure residual (dHs + boundary - latent): {es['integrated_energy_closure_J']:.3f} J",
    ]
    for p in PROFILES:
        grp=[r for r in profile_rows if r["case"]==case and r["profile"]==p]
        if not grp: continue
        peak=max(grp,key=lambda r:r["rms_vorticity_z"])
        med=statistics.median(r["rms_vorticity_z"] for r in grp)
        rot=statistics.median(r["rotational_fraction"] for r in grp)
        rotS=statistics.median(r["rotational_strength_share"] for r in grp if math.isfinite(r["rotational_strength_share"]))
        lines += [
            f"- {p}: median RMS(vorticity_z)={med:.4g} 1/s; peak={peak['rms_vorticity_z']:.4g} 1/s at {peak['time_s']:g} s; median rotational sample fraction={100*rot:.1f}%; median rotational strength share={100*rotS:.1f}%"
        ]
    lines += [""]

(OUT/"physics_diagnostics_summary.md").write_text("\n".join(lines)+"\n")
print("Wrote physics diagnostics outputs")
