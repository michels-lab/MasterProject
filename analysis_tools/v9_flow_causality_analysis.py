#!/usr/bin/env python3
from __future__ import annotations
import csv, math, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"v9_flow_causality"
OUT.mkdir(parents=True,exist_ok=True)

CASES={
    "B9": "B9_topFixedFlux",
    "C9": "C9_topFixedFlux",
}
PROFILES={
    "y20mm": ("horizontalProfiles","momentumHorizontalProfiles","line_y20mm.xy",0.020),
    "y30mm": ("horizontalProfiles","momentumHorizontalProfiles","line_y30mm.xy",0.030),
    "vertical_x20mm": ("verticalProfiles","momentumVerticalProfiles","line_x20mm.xy",None),
}
SELECTED=(0.1,1.0,2.5,5.0,7.5,10.0)
UY_RESOLVED=1e-4

# Base profile columns:
# 0 coord; 1:4 U; 4 T; 5 p_rgh; 6 rho; 7 alphaL;
# 8:11 vorticity; 11 flowType; 13:16 gradT; 16 magGradT;
# 19:22 gradRho; 22 magGradRho.
# Momentum profile columns:
# 0 coord; 1 solidFraction; 2 DarcyCoeff; 3 modelDeltaT;
# 4:7 DarcyAcceleration; 7:10 phaseChangeBuoyancyAcceleration;
# 10:13 pRghAcceleration; 13 magDarcy; 14 magPhaseChangeBuoyancy;
# 15 magPRgh; 16 dragToBuoyancy; 17 dragToPressure.

def numeric_dirs(path:Path):
    out=[]
    if not path.exists(): return out
    for p in path.iterdir():
        if p.is_dir():
            try: out.append((float(p.name),p))
            except ValueError: pass
    return sorted(out)

def read_rows(path:Path):
    rows=[]
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s or s.startswith("#"): continue
        rows.append([float(x) for x in s.split()])
    return rows

def interp_row(rows,x):
    if x<=rows[0][0]: return rows[0]
    if x>=rows[-1][0]: return rows[-1]
    for a,b in zip(rows[:-1],rows[1:]):
        if a[0] <= x <= b[0]:
            if b[0]==a[0]: return a
            w=(x-a[0])/(b[0]-a[0])
            return [a[j]+w*(b[j]-a[j]) for j in range(len(a))]
    raise ValueError("x outside rows")

def crossings(rows):
    out=[]
    for a,b in zip(rows[:-1],rows[1:]):
        ua,ub=a[2],b[2]
        # Ignore sign flips that are entirely in tiny numerical velocities.
        if max(abs(ua),abs(ub)) < UY_RESOLVED:
            continue
        if ua==0:
            out.append(a[0])
        elif ua*ub<0:
            out.append(a[0]+(-ua)/(ub-ua)*(b[0]-a[0]))
    # Merge nearly duplicate crossings within 0.25 mm.
    merged=[]
    for x in out:
        if not merged or abs(x-merged[-1])>2.5e-4: merged.append(x)
    return merged

def vecmag(v): return math.sqrt(sum(x*x for x in v))

def phase(alpha):
    if alpha < 0.05: return "solid-dominated"
    if alpha < 0.95: return "mushy"
    return "liquid-dominated"

def load(case,profile):
    pf,mf,name,_=PROFILES[profile]
    br=BASE/case/"postProcessing"/"metal"/pf
    mr=BASE/case/"postProcessing"/"metal"/mf
    bd={t:d/name for t,d in numeric_dirs(br) if (d/name).exists()}
    md={t:d/name for t,d in numeric_dirs(mr) if (d/name).exists()}
    return {t:(read_rows(bd[t]),read_rows(md[t])) for t in sorted(set(bd)&set(md))}

def crossing_record(label,case,profile,t,x,base,mom):
    br=interp_row(base,x); mr=interp_row(mom,x)
    if profile=="vertical_x20mm":
        y=x
    else:
        y=PROFILES[profile][3]
    rho=br[6]
    gh=-9.81*y
    gradRho=(br[19],br[20],br[21])
    # Exact continuum acceleration-scale counterpart of the -gh*grad(rho)
    # term appearing beside grad(p_rgh), divided by rho.
    aRho=tuple(-(gh/rho)*g for g in gradRho)
    darcy=(mr[4],mr[5],mr[6])
    phaseB=(mr[7],mr[8],mr[9])
    pacc=(mr[10],mr[11],mr[12])
    actual_buoy=aRho if label=="B9" else phaseB
    driveY=actual_buoy[1]+pacc[1]+darcy[1]
    mags={"buoy":vecmag(actual_buoy),"pressure":vecmag(pacc),"darcy":vecmag(darcy)}
    dominant=max(mags,key=mags.get)
    return {
        "case":label,"profile":profile,"time_s":t,"coord_m":x,"coord_mm":1000*x,
        "Uy":br[2],"Ux":br[1],"T_K":br[4],"rho":rho,"alphaL":br[7],
        "phase_zone":phase(br[7]),"vorticity_z":br[10],"flowType":br[11],
        "magGradT":br[16],"gradRho_x":br[19],"gradRho_y":br[20],
        "magGradRho":br[22],
        "aBuoy_x":actual_buoy[0],"aBuoy_y":actual_buoy[1],"aBuoy_mag":mags["buoy"],
        "aPressure_x":pacc[0],"aPressure_y":pacc[1],"aPressure_mag":mags["pressure"],
        "aDarcy_x":darcy[0],"aDarcy_y":darcy[1],"aDarcy_mag":mags["darcy"],
        "resolved_drive_y":driveY,
        "dominant_accel_scale":dominant,
        "pressure_to_buoy":mags["pressure"]/(mags["buoy"]+1e-12),
        "darcy_to_buoy":mags["darcy"]/(mags["buoy"]+1e-12),
        "darcy_to_pressure":mags["darcy"]/(mags["pressure"]+1e-12),
    }

all_cross=[]
count_rows=[]
series_cache={}
for label,case in CASES.items():
    for profile in PROFILES:
        data=load(case,profile)
        series_cache[(label,profile)]=data
        for t,(base,mom) in data.items():
            xs=crossings(base)
            count_rows.append({"case":label,"profile":profile,"time_s":t,"resolved_Uy_crossings":len(xs)})
            for x in xs:
                all_cross.append(crossing_record(label,case,profile,t,x,base,mom))

with (OUT/"crossing_diagnostics.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(all_cross[0].keys())); w.writeheader(); w.writerows(all_cross)
with (OUT/"crossing_counts.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(count_rows[0].keys())); w.writeheader(); w.writerows(count_rows)

def nearest_time(data,target):
    return min(data,key=lambda t:abs(t-target))

def fmt(v,n=3):
    return f"{v:.{n}g}"

lines=[
"# V9 flow-reversal causality analysis","",
"Purpose: test whether Uy sign reversals are spatially associated with liquid/mushy structure, density-gradient buoyancy, pressure, Darcy resistance and vorticity.","",
"Important model distinction:",
"- B9 has beta=0 in solidificationMeltingSource. Its thermal buoyancy is represented by the variable-density solver term -gh*grad(rho), not by phaseChangeBuoyancyAcceleration.",
"- For B9 this analysis reconstructs the corresponding acceleration scale as a_rho=-(gh/rho)*grad(rho), with hRef=0 and gh=-9.81*y.",
"- C9 uses rhoConst and beta=1.13e-4 1/K; for C9 the sampled phaseChangeBuoyancyAcceleration is used.",
"- p_rgh acceleration is -grad(p_rgh)/rho. Darcy acceleration is -D*U.",
"- These are source/acceleration scales. They do not include viscous diffusion or material acceleration, so 'dominant' below is descriptive, not a proof of causal sufficiency.",
"- A Uy sign crossing alone does not prove a closed 2-D recirculation cell; only line samples are available in the repository.",
"",
"Resolved crossings ignore sign flips for which both adjacent |Uy| values are below 1e-4 m/s.",
""]

for label in CASES:
    lines += [f"## {label}",""]
    for profile in PROFILES:
        data=series_cache[(label,profile)]
        lines += [f"### {profile}","",
                  "| t s | resolved Uy crossings (mm) | phase zones at crossings | dominant acceleration scale(s) |",
                  "|---:|---|---|---|"]
        for target in SELECTED:
            t=nearest_time(data,target)
            rec=[r for r in all_cross if r["case"]==label and r["profile"]==profile and abs(r["time_s"]-t)<1e-12]
            lines.append(
                f"| {t:g} | "+(", ".join(f"{r['coord_mm']:.2f}" for r in rec) if rec else "none")+" | "+
                (", ".join(r["phase_zone"] for r in rec) if rec else "—")+" | "+
                (", ".join(r["dominant_accel_scale"] for r in rec) if rec else "—")+" |"
            )
        # first time 4 or more resolved crossings, if any
        counts=[r for r in count_rows if r["case"]==label and r["profile"]==profile]
        multi=next((r for r in sorted(counts,key=lambda z:z["time_s"]) if r["resolved_Uy_crossings"]>=4),None)
        if multi:
            lines += ["",f"- first stored time with >=4 resolved Uy crossings: **{multi['time_s']:g} s**"]
        lines.append("")

    lines += ["### Detailed crossings at 10 s",""]
    for profile in PROFILES:
        rec=[r for r in all_cross if r["case"]==label and r["profile"]==profile and abs(r["time_s"]-10)<1e-10]
        lines += [f"#### {profile}","",
                  "| pos mm | alphaL | zone | |grad rho| | omega_z 1/s | flowType | a_b,y | a_p,y | a_D,y | |a_b| | |a_p| | |a_D| | dominant |",
                  "|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
        for r in rec:
            lines.append(
                f"| {r['coord_mm']:.2f} | {r['alphaL']:.3f} | {r['phase_zone']} | {r['magGradRho']:.3g} | "
                f"{r['vorticity_z']:.3g} | {r['flowType']:.3f} | {r['aBuoy_y']:.3g} | {r['aPressure_y']:.3g} | "
                f"{r['aDarcy_y']:.3g} | {r['aBuoy_mag']:.3g} | {r['aPressure_mag']:.3g} | {r['aDarcy_mag']:.3g} | "
                f"{r['dominant_accel_scale']} |"
            )
        if not rec: lines.append("| — | — | — | — | — | — | — | — | — | — | — | — | — |")
        lines.append("")

# Aggregate association statistics for B9 and C9 separately.
lines += ["## Aggregate association of resolved crossings",""]
for label in CASES:
    rr=[r for r in all_cross if r["case"]==label and r["time_s"]>=0.1]
    lines += [f"### {label}",""]
    for profile in PROFILES:
        q=[r for r in rr if r["profile"]==profile]
        if not q: continue
        mush=sum(r["phase_zone"]=="mushy" for r in q)/len(q)
        liq=sum(r["phase_zone"]=="liquid-dominated" for r in q)/len(q)
        dom={k:sum(r["dominant_accel_scale"]==k for r in q)/len(q) for k in ("buoy","pressure","darcy")}
        lines += [
            f"- {profile}: n={len(q)} crossing samples; mushy={100*mush:.1f}%; liquid-dominated={100*liq:.1f}%; "
            f"dominant scale buoy={100*dom['buoy']:.1f}%, pressure={100*dom['pressure']:.1f}%, Darcy={100*dom['darcy']:.1f}%; "
            f"median |omega_z|={statistics.median(abs(r['vorticity_z']) for r in q):.3g} 1/s; "
            f"median |grad rho|={statistics.median(r['magGradRho'] for r in q):.3g} kg/m4."
        ]
    lines.append("")

(OUT/"summary.md").write_text("\n".join(lines)+"\n")
print((OUT/"summary.md").read_text())
