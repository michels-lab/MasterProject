#!/usr/bin/env python3
from __future__ import annotations
import csv, math, bisect
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"v8_outer4_comparison"
OUT.mkdir(parents=True,exist_ok=True)

PROFILES={
 "y20mm":("horizontalProfiles","line_y20mm.xy"),
 "y30mm":("horizontalProfiles","line_y30mm.xy"),
 "vertical_x20mm":("verticalProfiles","line_x20mm.xy"),
}

SETS=[
 ("B8_vs_B6","B6_adaptiveDt","B8_adaptiveOuter4","adaptive_exact"),
 ("B8_vs_B5","B5_outer3","B8_adaptiveOuter4","ref_interp"),
 ("C8_vs_C6","C6_adaptiveDt","C8_adaptiveOuter4","adaptive_exact"),
 ("C8_vs_C5","C5_outer3","C8_adaptiveOuter4","ref_interp"),
]

def numeric_dirs(path):
    out=[]
    if not path.exists(): return out
    for p in path.iterdir():
        if p.is_dir():
            try: out.append((float(p.name),p))
            except ValueError: pass
    return sorted(out)

def read_profile(path):
    rows=[]
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s or s.startswith("#"): continue
        rows.append([float(x) for x in s.split()])
    return rows

def load(case,pkey):
    folder,file=PROFILES[pkey]
    root=BASE/case/"postProcessing"/"metal"/folder
    d={}
    for t,p in numeric_dirs(root):
        f=p/file
        if f.is_file(): d[t]=read_profile(f)
    return d

def same_grid(a,b,tol=1e-12):
    return len(a)==len(b) and all(abs(x[0]-y[0])<=tol for x,y in zip(a,b))

def interp_series(series,t):
    times=sorted(series)
    if not times or t<times[0]-1e-12 or t>times[-1]+1e-12: return None
    for tt in times:
        if abs(tt-t)<=1e-10: return series[tt]
    i=bisect.bisect_left(times,t)
    if i==0 or i==len(times): return None
    t0,t1=times[i-1],times[i]
    a,b=series[t0],series[t1]
    if not same_grid(a,b): raise RuntimeError("Spatial grids differ during interpolation")
    w=(t-t0)/(t1-t0)
    out=[]
    for ra,rb in zip(a,b):
        out.append([ra[j] if j==0 else ra[j]+w*(rb[j]-ra[j]) for j in range(len(ra))])
    return out

def uy_metrics(ref,other):
    a=[r[2] for r in ref]; b=[r[2] for r in other]
    n=len(a)
    se=sum((y-x)**2 for x,y in zip(a,b))
    rmse=math.sqrt(se/n)
    rms=math.sqrt(sum(x*x for x in a)/n)
    dot=sum(x*y for x,y in zip(a,b))
    den=math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    corr=dot/den if den else float("nan")
    sign=sum(1 for x,y in zip(a,b) if abs(x)>1e-8 and abs(y)>1e-8 and math.copysign(1,x)!=math.copysign(1,y))
    return rmse,100*rmse/rms if rms else float("nan"),corr,sign,min(a),max(a),min(b),max(b)

rows=[]
cache={}
for _,a,b,_ in SETS:
    for p in PROFILES:
        cache.setdefault((a,p),load(a,p))
        cache.setdefault((b,p),load(b,p))

for label,ref_case,test_case,mode in SETS:
    for p in PROFILES:
        ref=cache[(ref_case,p)]; test=cache[(test_case,p)]
        if not test:
            continue
        if mode=="adaptive_exact":
            times=[t for t in sorted(test) if any(abs(t-r)<=1e-10 for r in ref)]
        else:
            rt=sorted(ref)
            times=[t for t in sorted(test) if rt and rt[0]-1e-12<=t<=rt[-1]+1e-12]
        for t in times:
            other=test[t]
            rr=interp_series(ref,t)
            if rr is None: continue
            if not same_grid(rr,other): raise RuntimeError(f"Grid mismatch {label} {p} {t}")
            rmse,nrmse,corr,sign,rmin,rmax,omin,omax=uy_metrics(rr,other)
            rows.append({
                "comparison":label,"profile":p,"time_s":t,
                "rmse_Uy":rmse,"nrmse_rms_Uy_pct":nrmse,"corr_Uy":corr,
                "sign_diff_points":sign,
                "ref_Uy_min":rmin,"ref_Uy_max":rmax,
                "test_Uy_min":omin,"test_Uy_max":omax,
            })

if rows:
    with (OUT/"uy_comparison.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)

summary=["# V8 adaptive + 4 outer correctors comparison",""]
if not rows:
    summary.append("No B8/C8 postProcessing profiles were found yet.")
else:
    for label,_,_,_ in SETS:
        summary += [f"## {label}",""]
        for p in PROFILES:
            g=[r for r in rows if r["comparison"]==label and r["profile"]==p]
            if not g:
                summary.append(f"- {p}: no comparable samples")
                continue
            peak=max(g,key=lambda r:r["nrmse_rms_Uy_pct"])
            last=max(g,key=lambda r:r["time_s"])
            summary += [
                f"- {p}: samples={len(g)}, last t={last['time_s']:g} s, "
                f"last NRMSE={last['nrmse_rms_Uy_pct']:.2f}%, last corr={last['corr_Uy']:.4f}, "
                f"peak NRMSE={peak['nrmse_rms_Uy_pct']:.2f}% at {peak['time_s']:g} s"
            ]
        summary.append("")

(OUT/"summary.md").write_text("\n".join(summary)+"\n")
print("Wrote V8 comparison outputs")
