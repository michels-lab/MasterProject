#!/usr/bin/env python3
from __future__ import annotations
import math, re, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"v9_velocity_reversal_causality"
OUT.mkdir(parents=True,exist_ok=True)

CASES=["B9_topFixedFlux","C9_topFixedFlux"]
PROFILES={
    "y20mm":("horizontalProfiles","momentumHorizontalProfiles","line_y20mm.xy"),
    "y30mm":("horizontalProfiles","momentumHorizontalProfiles","line_y30mm.xy"),
    "vertical_x20mm":("verticalProfiles","momentumVerticalProfiles","line_x20mm.xy"),
}
SELECTED=[0.1,0.5,1.0,2.5,5.0,7.5,10.0]

# Standard profile indices
UX,UY,T,PRGH,RHO,ALPHA,WZ,FLOW,MAGRHO,CO=1,2,4,5,6,7,10,11,22,26
# Momentum profile indices
MAG_DARCY,MAG_PRGH=13,15

def read_rows(path):
    rows=[]
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s or s.startswith("#"): continue
        rows.append([float(x) for x in s.split()])
    return rows

def ndirs(path):
    out=[]
    for p in path.iterdir():
        if not p.is_dir(): continue
        try: out.append((float(p.name),p))
        except ValueError: pass
    return sorted(out)

def interp_row(rows,x):
    if x<=rows[0][0]: return rows[0]
    if x>=rows[-1][0]: return rows[-1]
    for a,b in zip(rows[:-1],rows[1:]):
        if a[0] <= x <= b[0]:
            w=(x-a[0])/(b[0]-a[0])
            return [x]+[a[j]+w*(b[j]-a[j]) for j in range(1,len(a))]
    raise RuntimeError("x outside profile")

def zero_crossings(rows,idx):
    xs=[]
    for a,b in zip(rows[:-1],rows[1:]):
        ya,yb=a[idx],b[idx]
        if ya==0: xs.append(a[0])
        elif ya*yb<0:
            xs.append(a[0]+(-ya)/(yb-ya)*(b[0]-a[0]))
    return xs

def threshold_crossings(rows,idx,val):
    xs=[]
    for a,b in zip(rows[:-1],rows[1:]):
        ya,yb=a[idx]-val,b[idx]-val
        if ya==0: xs.append(a[0])
        elif ya*yb<0:
            xs.append(a[0]+(-ya)/(yb-ya)*(b[0]-a[0]))
    return xs

def pct_rank(values,v):
    s=sorted(values)
    return 100*sum(x<=v for x in s)/len(s)

def phase(a):
    if a<=0.05: return "solid-like"
    if a>=0.95: return "liquid-like"
    return "mushy"

def nearest_dist_mm(x,xs):
    return min(abs(x-y) for y in xs)*1000 if xs else float("nan")

def symmetry_pair_error(xs,L=0.04):
    if len(xs)<2: return float("nan")
    xs=sorted(xs)
    errs=[]
    for i in range(len(xs)//2):
        errs.append(abs((xs[i]+xs[-1-i])-L)*1000)
    return statistics.mean(errs) if errs else float("nan")

def read_series(path):
    d={}
    if not path.exists(): return d
    for line in path.read_text().splitlines():
        p=line.split()
        if len(p)<2: continue
        try: d[float(p[0].rstrip("s"))]=float(p[1])
        except ValueError: pass
    return d

def indexed(logdir,prefix):
    a=[]
    for p in logdir.glob(prefix+"_*"):
        m=re.fullmatch(re.escape(prefix)+r"_(\d+)",p.name)
        if m:a.append((int(m.group(1)),p))
    return [p for _,p in sorted(a)]

def pearson(x,y):
    if len(x)<3:return float("nan")
    mx=statistics.fmean(x); my=statistics.fmean(y)
    xa=[a-mx for a in x]; ya=[b-my for b in y]
    den=math.sqrt(sum(a*a for a in xa)*sum(b*b for b in ya))
    return sum(a*b for a,b in zip(xa,ya))/den if den else float("nan")

lines=["# V9 velocity-reversal causality analysis","",
"This analysis tests whether Uy sign reversals are spatially associated with the mushy front, density gradients, Darcy resistance, pressure-gradient acceleration, or high vorticity. Reversal locations are linearly interpolated from the sampled profiles.",""]

for case in CASES:
    lines += [f"## {case}",""]
    contfiles=indexed(BASE/case/"logs","contGlobal")
    cont=read_series(contfiles[-1]) if contfiles else {}
    for pname,(pfolder,mfolder,file) in PROFILES.items():
        proot=BASE/case/"postProcessing"/"metal"/pfolder
        mroot=BASE/case/"postProcessing"/"metal"/mfolder
        pdata={t:read_rows(d/file) for t,d in ndirs(proot) if (d/file).exists()}
        mdata={t:read_rows(d/file) for t,d in ndirs(mroot) if (d/file).exists()}
        times=sorted(set(pdata)&set(mdata))
        lines += [f"### {pname}",""]

        all_records=[]
        counts=[]; cont_vals=[]
        for t in times:
            p=pdata[t]; m=mdata[t]
            z=zero_crossings(p,UY)
            counts.append(len(z))
            # logs have millisecond timesteps, exact write-time keys should exist
            if t in cont:
                cont_vals.append((len(z),abs(cont[t])))
            a05=threshold_crossings(p,ALPHA,0.05)
            a50=threshold_crossings(p,ALPHA,0.50)
            a95=threshold_crossings(p,ALPHA,0.95)
            vals_grad=[r[MAGRHO] for r in p]
            vals_w=[abs(r[WZ]) for r in p]
            vals_d=[r[MAG_DARCY] for r in m]
            vals_pr=[r[MAG_PRGH] for r in m]
            for x in z:
                rp=interp_row(p,x); rm=interp_row(m,x)
                rec={
                    "t":t,"x":x,"alpha":rp[ALPHA],"phase":phase(rp[ALPHA]),
                    "T":rp[T],"rho":rp[RHO],"gradRho":rp[MAGRHO],
                    "gradRhoPct":pct_rank(vals_grad,rp[MAGRHO]),
                    "wz":rp[WZ],"wPct":pct_rank(vals_w,abs(rp[WZ])),
                    "flow":rp[FLOW],"darcy":rm[MAG_DARCY],
                    "darcyPct":pct_rank(vals_d,rm[MAG_DARCY]),
                    "pacc":rm[MAG_PRGH],"pPct":pct_rank(vals_pr,rm[MAG_PRGH]),
                    "d05":nearest_dist_mm(x,a05),"d50":nearest_dist_mm(x,a50),"d95":nearest_dist_mm(x,a95),
                }
                all_records.append(rec)

        # overall attribution
        n=len(all_records)
        mush=sum(r["phase"]=="mushy" for r in all_records)
        liq=sum(r["phase"]=="liquid-like" for r in all_records)
        sol=sum(r["phase"]=="solid-like" for r in all_records)
        near95=sum(math.isfinite(r["d95"]) and r["d95"]<=1.0 for r in all_records)
        highgrad=sum(r["gradRhoPct"]>=75 for r in all_records)
        highdarcy=sum(r["darcyPct"]>=75 for r in all_records)
        highp=sum(r["pPct"]>=75 for r in all_records)
        highw=sum(r["wPct"]>=75 for r in all_records)
        lines += [
            f"- total Uy reversals sampled over all stored times: {n}",
            f"- phase location: mushy {100*mush/n:.1f}%, liquid-like {100*liq/n:.1f}%, solid-like {100*sol/n:.1f}%" if n else "- no reversals",
            f"- within 1 mm of alphaL=0.95 front: {100*near95/n:.1f}%" if n else "",
            f"- reversals in top quartile of local profile |gradRho|: {100*highgrad/n:.1f}%" if n else "",
            f"- reversals in top quartile of |Darcy acceleration|: {100*highdarcy/n:.1f}%" if n else "",
            f"- reversals in top quartile of |p_rgh acceleration|: {100*highp/n:.1f}%" if n else "",
            f"- reversals in top quartile of |vorticity_z|: {100*highw/n:.1f}%" if n else "",
        ]
        if cont_vals:
            lines.append(f"- correlation(number of Uy reversals, |final-corrector contGlobal|): {pearson([a for a,b in cont_vals],[b for a,b in cont_vals]):.4f}")
        lines.append("")

        lines += [
            "| t s | reversals mm | mirror-pair error mm | alphaL at reversals | phase | |gradRho| percentile | |Darcy| percentile | |pRghAccel| percentile | |wz| percentile | d(alpha=.95) mm |",
            "|---:|---|---:|---|---|---|---|---|---|---|"
        ]
        for t in SELECTED:
            # exact stored times
            p=pdata[t]; m=mdata[t]; z=zero_crossings(p,UY)
            a95=threshold_crossings(p,ALPHA,0.95)
            vals_grad=[r[MAGRHO] for r in p]; vals_w=[abs(r[WZ]) for r in p]
            vals_d=[r[MAG_DARCY] for r in m]; vals_pr=[r[MAG_PRGH] for r in m]
            rr=[]
            for x in z:
                rp=interp_row(p,x); rm=interp_row(m,x)
                rr.append((x,rp,rm))
            lines.append(
                f"| {t:g} | "
                + (", ".join(f"{x*1000:.2f}" for x,_,_ in rr) if rr else "none")
                + f" | {symmetry_pair_error(z):.3f} | "
                + (", ".join(f"{rp[ALPHA]:.3f}" for _,rp,_ in rr) if rr else "-")
                + " | "
                + (", ".join(phase(rp[ALPHA]) for _,rp,_ in rr) if rr else "-")
                + " | "
                + (", ".join(f"{pct_rank(vals_grad,rp[MAGRHO]):.0f}%" for _,rp,_ in rr) if rr else "-")
                + " | "
                + (", ".join(f"{pct_rank(vals_d,rm[MAG_DARCY]):.0f}%" for _,_,rm in rr) if rr else "-")
                + " | "
                + (", ".join(f"{pct_rank(vals_pr,rm[MAG_PRGH]):.0f}%" for _,_,rm in rr) if rr else "-")
                + " | "
                + (", ".join(f"{pct_rank(vals_w,abs(rp[WZ])):.0f}%" for _,rp,_ in rr) if rr else "-")
                + " | "
                + (", ".join(f"{nearest_dist_mm(x,a95):.2f}" for x,_,_ in rr) if rr else "-")
                + " |"
            )
        lines.append("")

(OUT/"summary.md").write_text("\n".join(x for x in lines if x!="") + "\n")
print((OUT/"summary.md").read_text())
