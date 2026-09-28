#!/usr/bin/env python3
from __future__ import annotations
import bisect, math, re, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"v8_comprehensive"
OUT.mkdir(parents=True,exist_ok=True)

PROFILES={
    "y20mm":("horizontalProfiles","momentumHorizontalProfiles","line_y20mm.xy"),
    "y30mm":("horizontalProfiles","momentumHorizontalProfiles","line_y30mm.xy"),
    "vertical_x20mm":("verticalProfiles","momentumVerticalProfiles","line_x20mm.xy"),
}

FAMILIES={
    "B":{"fixed":"B5_outer3","adaptive3":"B6_adaptiveDt","adaptive4":"B8_adaptiveOuter4"},
    "C":{"fixed":"C5_outer3","adaptive3":"C6_adaptiveDt","adaptive4":"C8_adaptiveOuter4"},
}

def ndirs(path):
    out=[]
    if not path.exists(): return out
    for p in path.iterdir():
        if p.is_dir():
            try: out.append((float(p.name),p))
            except ValueError: pass
    return sorted(out)

def read_rows(path):
    rows=[]
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s or s.startswith("#"): continue
        rows.append([float(x) for x in s.split()])
    return rows

def load(case,folder,file):
    root=BASE/case/"postProcessing"/"metal"/folder
    return {t:read_rows(p/file) for t,p in ndirs(root) if (p/file).is_file()}

def same_grid(a,b,tol=1e-12):
    return len(a)==len(b) and all(abs(x[0]-y[0])<=tol for x,y in zip(a,b))

def interp(series,t):
    times=sorted(series)
    if not times or t<times[0]-1e-12 or t>times[-1]+1e-12: return None
    i=bisect.bisect_left(times,t)
    if i<len(times) and abs(times[i]-t)<=1e-10: return series[times[i]]
    if i>0 and abs(times[i-1]-t)<=1e-10: return series[times[i-1]]
    if i==0 or i==len(times): return None
    t0,t1=times[i-1],times[i]
    a,b=series[t0],series[t1]
    if not same_grid(a,b): raise RuntimeError("spatial grid mismatch during interpolation")
    w=(t-t0)/(t1-t0)
    return [[ra[j] if j==0 else ra[j]+w*(rb[j]-ra[j]) for j in range(len(ra))] for ra,rb in zip(a,b)]

def corr(a,b):
    aa=sum(x*x for x in a); bb=sum(x*x for x in b)
    den=math.sqrt(aa*bb)
    return sum(x*y for x,y in zip(a,b))/den if den else float("nan")

def scalar_metric(ref,test,idx,absolute_rmse=False):
    a=[r[idx] for r in ref]; b=[r[idx] for r in test]
    n=len(a); rmse=math.sqrt(sum((y-x)**2 for x,y in zip(a,b))/n)
    rms=math.sqrt(sum(x*x for x in a)/n)
    return {
        "rmse":rmse,
        "nrmse":100*rmse/rms if rms else float("nan"),
        "corr":corr(a,b),
    }

def mag_metric(ref,test,start):
    a=[math.sqrt(sum(r[j]*r[j] for j in range(start,start+3))) for r in ref]
    b=[math.sqrt(sum(r[j]*r[j] for j in range(start,start+3))) for r in test]
    n=len(a); rmse=math.sqrt(sum((y-x)**2 for x,y in zip(a,b))/n)
    rms=math.sqrt(sum(x*x for x in a)/n)
    return {"rmse":rmse,"nrmse":100*rmse/rms if rms else float("nan"),"corr":corr(a,b)}

def flow_class(v):
    return 1 if v>0.2 else (-1 if v<-0.2 else 0)

def flow_metric(ref,test):
    a=[r[11] for r in ref]; b=[r[11] for r in test]
    return {
        "mae":sum(abs(x-y) for x,y in zip(a,b))/len(a),
        "class_disagree":sum(flow_class(x)!=flow_class(y) for x,y in zip(a,b))/len(a),
        "corr":corr(a,b),
    }

def crossings(rows,idx,val):
    xs=[]
    for i in range(len(rows)-1):
        x0,x1=rows[i][0],rows[i+1][0]
        y0,y1=rows[i][idx],rows[i+1][idx]
        if y0==val: xs.append(x0)
        elif (y0-val)*(y1-val)<0:
            w=(val-y0)/(y1-y0)
            xs.append(x0+w*(x1-x0))
    return xs

def profile_last_geometry(rows):
    out={}
    for val in (0.05,0.5,0.95):
        out[val]=crossings(rows,7,val)
    return out

def fmt(v,n=3):
    return "n/a" if not math.isfinite(v) else f"{v:.{n}f}"

def read_log_series(path):
    d={}
    if not path.exists(): return d
    for line in path.read_text().splitlines():
        p=line.split()
        if len(p)>=2:
            try:d[float(p[0].rstrip("s"))]=float(p[1])
            except ValueError:pass
    return d

def indexed(logdir,prefix):
    out=[]
    for p in logdir.glob(prefix+"_*"):
        m=re.fullmatch(re.escape(prefix)+r"_(\d+)",p.name)
        if m: out.append((int(m.group(1)),p))
    return [p for _,p in sorted(out)]

def coupling(case):
    c=BASE/case; logs=c/"logs"
    fv=(c/"system"/"fvSolution").read_text()
    nouter=int(re.search(r"nOuterCorrectors\s+(\d+)\s*;",fv).group(1))
    ps=[read_log_series(p) for p in indexed(logs,"p_rgh")]
    pfs=[read_log_series(p) for p in indexed(logs,"p_rghFinalRes")]
    per=len(ps)//nouter
    last_first=(nouter-1)*per
    times=sorted(set(ps[0]) & set(ps[last_first]))
    ratios=[]
    for t in times:
        if t<0.1: continue
        a=ps[0][t]; b=ps[last_first][t]
        if a: ratios.append(b/a)
    contfiles=indexed(logs,"contCumulative")
    cont=read_log_series(contfiles[-1]) if contfiles else {}
    co=read_log_series(logs/"CourantMax_0")
    clock=read_log_series(logs/"clockTime_0")
    pfin=pfs[-1] if pfs else {}
    return {
        "median_Rp":statistics.median(ratios),
        "p95_Rp":sorted(ratios)[int(round(0.95*(len(ratios)-1)))],
        "Rp_gt1":sum(x>1 for x in ratios)/len(ratios),
        "continuity":abs(cont[max(cont)]) if cont else float("nan"),
        "maxCo":max(co.values()) if co else float("nan"),
        "clock":clock[max(clock)] if clock else float("nan"),
        "median_last_p_final":statistics.median(pfin.values()) if pfin else float("nan"),
    }

lines=["# V8 comprehensive comparison","",
"All comparisons use the native V8 stored physical times. Reference profiles are linearly interpolated in physical time. No timestep-index matching is used.",""]

for fam,cases in FAMILIES.items():
    test=cases["adaptive4"]
    refs=[("adaptive3",cases["adaptive3"]),("fixed",cases["fixed"])]
    lines += [f"## Family {fam}",""]
    coup={k:coupling(v) for k,v in cases.items()}
    lines += ["### Coupling / cost","",
        "| case | median Rp | p95 Rp | Rp>1 | continuity | max Co | clock s |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for k in ("fixed","adaptive3","adaptive4"):
        x=coup[k]
        lines.append(f"| {cases[k]} | {x['median_Rp']:.4f} | {x['p95_Rp']:.4f} | {100*x['Rp_gt1']:.2f}% | {x['continuity']:.3e} | {x['maxCo']:.4f} | {x['clock']:.1f} |")
    lines.append("")

    for pname,(ofolder,mfolder,file) in PROFILES.items():
        testO=load(test,ofolder,file); testM=load(test,mfolder,file)
        times=sorted(set(testO)&set(testM))
        lines += [f"### {pname}",""]
        for label,refcase in refs:
            refO=load(refcase,ofolder,file); refM=load(refcase,mfolder,file)
            rec=[]
            for t in times:
                ro=interp(refO,t); rm=interp(refM,t)
                if ro is None or rm is None: continue
                to=testO[t]; tm=testM[t]
                if not same_grid(ro,to) or not same_grid(rm,tm): raise RuntimeError("grid mismatch")
                rec.append({
                    "t":t,
                    "Uy":scalar_metric(ro,to,2),
                    "T":scalar_metric(ro,to,4),
                    "alpha":scalar_metric(ro,to,7),
                    "vort":scalar_metric(ro,to,10),
                    "flow":flow_metric(ro,to),
                    "DarcyMag":scalar_metric(rm,tm,13),
                    "pMag":scalar_metric(rm,tm,15),
                })
            if not rec:
                lines.append(f"- vs {refcase}: no comparable samples")
                continue
            last=rec[-1]
            medUy=statistics.median(r["Uy"]["nrmse"] for r in rec if math.isfinite(r["Uy"]["nrmse"]))
            medV=statistics.median(r["vort"]["nrmse"] for r in rec if math.isfinite(r["vort"]["nrmse"]))
            peakUy=max(rec,key=lambda r:r["Uy"]["nrmse"])
            peakV=max(rec,key=lambda r:r["vort"]["nrmse"])
            lines += [
                f"#### {test} vs {refcase}",
                f"- compared samples: {len(rec)}; last shared V8 time: {last['t']:.6f} s",
                f"- Uy: median NRMSE {medUy:.2f}%; last {last['Uy']['nrmse']:.2f}%, corr {last['Uy']['corr']:.4f}; peak {peakUy['Uy']['nrmse']:.2f}% at {peakUy['t']:.6f} s",
                f"- T: last RMSE {last['T']['rmse']:.3f} K",
                f"- alphaL: last RMSE {last['alpha']['rmse']:.5f}; NRMSE {last['alpha']['nrmse']:.2f}%",
                f"- vorticity_z: median NRMSE {medV:.2f}%; last {last['vort']['nrmse']:.2f}%, corr {last['vort']['corr']:.4f}; peak {peakV['vort']['nrmse']:.2f}% at {peakV['t']:.6f} s",
                f"- flowType: last MAE {last['flow']['mae']:.4f}; class disagreement {100*last['flow']['class_disagree']:.1f}%",
                f"- |Darcy acceleration|: last NRMSE {last['DarcyMag']['nrmse']:.2f}%",
                f"- |p_rgh acceleration|: last NRMSE {last['pMag']['nrmse']:.2f}%",
            ]
            if pname=="vertical_x20mm":
                ro=interp(refO,last["t"]); to=testO[last["t"]]
                gr=profile_last_geometry(ro); gt=profile_last_geometry(to)
                lines += [
                    f"- vertical alphaL=0.05 crossings mm: ref {[round(x*1000,3) for x in gr[0.05]]}; V8 {[round(x*1000,3) for x in gt[0.05]]}",
                    f"- vertical alphaL=0.50 crossings mm: ref {[round(x*1000,3) for x in gr[0.5]]}; V8 {[round(x*1000,3) for x in gt[0.5]]}",
                    f"- vertical alphaL=0.95 crossings mm: ref {[round(x*1000,3) for x in gr[0.95]]}; V8 {[round(x*1000,3) for x in gt[0.95]]}",
                ]
            lines.append("")
    lines.append("")

(OUT/"summary.md").write_text("\n".join(lines)+"\n")
print((OUT/"summary.md").read_text())
