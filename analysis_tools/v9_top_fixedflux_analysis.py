#!/usr/bin/env python3
from __future__ import annotations
import bisect, csv, math, re, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"v9_top_fixedflux"
OUT.mkdir(parents=True,exist_ok=True)

PAIRS={
    "B":("B5_outer3","B9_topFixedFlux"),
    "C":("C5_outer3","C9_topFixedFlux"),
}
PROFILES={
    "y20mm":("horizontalProfiles","momentumHorizontalProfiles","line_y20mm.xy"),
    "y30mm":("horizontalProfiles","momentumHorizontalProfiles","line_y30mm.xy"),
    "vertical_x20mm":("verticalProfiles","momentumVerticalProfiles","line_x20mm.xy"),
}

def numeric_dirs(path):
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

def load_profile(case,folder,file):
    root=BASE/case/"postProcessing"/"metal"/folder
    return {t:read_rows(d/file) for t,d in numeric_dirs(root) if (d/file).is_file()}

def interp(series,t):
    ts=sorted(series)
    if not ts or t<ts[0]-1e-12 or t>ts[-1]+1e-12: return None
    i=bisect.bisect_left(ts,t)
    if i<len(ts) and abs(ts[i]-t)<1e-10: return series[ts[i]]
    if i>0 and abs(ts[i-1]-t)<1e-10: return series[ts[i-1]]
    if i==0 or i==len(ts): return None
    t0,t1=ts[i-1],ts[i]
    a,b=series[t0],series[t1]
    if len(a)!=len(b): raise RuntimeError("profile length mismatch")
    w=(t-t0)/(t1-t0)
    return [[ra[j] if j==0 else ra[j]+w*(rb[j]-ra[j]) for j in range(len(ra))] for ra,rb in zip(a,b)]

def corr(a,b):
    aa=sum(x*x for x in a); bb=sum(x*x for x in b)
    den=math.sqrt(aa*bb)
    return sum(x*y for x,y in zip(a,b))/den if den else float("nan")

def scalar_metric(ref,test,idx):
    a=[r[idx] for r in ref]; b=[r[idx] for r in test]
    rmse=math.sqrt(sum((y-x)**2 for x,y in zip(a,b))/len(a))
    rms=math.sqrt(sum(x*x for x in a)/len(a))
    return {"rmse":rmse,"nrmse":100*rmse/rms if rms else float("nan"),"corr":corr(a,b),
            "ref_min":min(a),"ref_max":max(a),"test_min":min(b),"test_max":max(b)}

def mag_metric(ref,test,idx):
    a=[r[idx] for r in ref]; b=[r[idx] for r in test]
    rmse=math.sqrt(sum((y-x)**2 for x,y in zip(a,b))/len(a))
    rms=math.sqrt(sum(x*x for x in a)/len(a))
    return {"rmse":rmse,"nrmse":100*rmse/rms if rms else float("nan"),"corr":corr(a,b)}

def cls(v):
    return 1 if v>0.2 else (-1 if v<-0.2 else 0)

def flow_metric(ref,test):
    a=[r[11] for r in ref]; b=[r[11] for r in test]
    return {"mae":sum(abs(x-y) for x,y in zip(a,b))/len(a),
            "disagree":sum(cls(x)!=cls(y) for x,y in zip(a,b))/len(a),
            "corr":corr(a,b)}

def crossings(rows,idx,val):
    xs=[]
    for a,b in zip(rows[:-1],rows[1:]):
        x0,x1=a[0],b[0]; y0,y1=a[idx],b[idx]
        if y0==val: xs.append(x0)
        elif (y0-val)*(y1-val)<0:
            xs.append(x0+(val-y0)/(y1-y0)*(x1-x0))
    return xs

def read_table(path):
    return read_rows(path)

def trapz(rows,col):
    return sum(0.5*(rows[i][col]+rows[i-1][col])*(rows[i][0]-rows[i-1][0]) for i in range(1,len(rows)))

def energy(case):
    b=BASE/case/"postProcessing"/"metal"
    top=read_table(b/"metalTopEnergyPower"/"0"/"surfaceFieldValue.dat")
    mold=read_table(b/"metalMoldEnergyPower"/"0"/"surfaceFieldValue.dat")
    bd=read_table(b/"metalBoundaryEnergyPower"/"0"/"surfaceFieldValue.dat")
    lat=read_table(b/"metalLatentHeatPower"/"0"/"volFieldValue.dat")
    hs=read_table(b/"metalSensibleEnthalpy"/"0"/"volFieldValue.dat")
    return {
        "top_adv":trapz(top,1),"top_diff":trapz(top,2),
        "mold_adv":trapz(mold,1),"mold_diff":trapz(mold,2),
        "bd_adv":trapz(bd,1),"bd_diff":trapz(bd,2),"bd_total":trapz(bd,3),
        "latent":trapz(lat,1),"dH":hs[-1][1]-hs[0][1],
        "top_adv_max":max(abs(r[1]) for r in top),
        "top_diff_final":top[-1][2],"mold_diff_final":mold[-1][2],
    }

def phi_stats(case):
    p=BASE/case/"postProcessing"/"metal"/"metalTopPhiSum"/"0"/"surfaceFieldValue.dat"
    if not p.exists(): return None
    rows=read_table(p)
    return {"max_abs":max(abs(r[1]) for r in rows),"final":rows[-1][1],
            "integral":trapz(rows,1)}

def read_series(path):
    d={}
    if not path.exists(): return d
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s: continue
        p=s.split()
        if len(p)<2: continue
        try: d[float(p[0].rstrip("s"))]=float(p[1])
        except ValueError: pass
    return d

def indexed(logdir,prefix):
    z=[]
    for p in logdir.glob(prefix+"_*"):
        m=re.fullmatch(re.escape(prefix)+r"_(\d+)",p.name)
        if m:z.append((int(m.group(1)),p))
    return [p for _,p in sorted(z)]

def coupling(case):
    c=BASE/case; logs=c/"logs"
    root=(c/"system"/"fvSolution").read_text()
    nouter=int(re.search(r"nOuterCorrectors\s+(\d+)",root).group(1))
    ps=[read_series(p) for p in indexed(logs,"p_rgh")]
    per=len(ps)//nouter
    a,b=ps[0],ps[(nouter-1)*per]
    ts=sorted(set(a)&set(b))
    ratios=[b[t]/a[t] for t in ts if t>=0.1 and a[t]!=0]
    conts=indexed(logs,"contCumulative")
    globals_=indexed(logs,"contGlobal")
    cont=read_series(conts[-1]) if conts else {}
    glob=read_series(globals_[-1]) if globals_ else {}
    co=read_series(logs/"CourantMax_0")
    clock=read_series(logs/"clockTime_0")
    return {
        "median_Rp":statistics.median(ratios),
        "p95_Rp":sorted(ratios)[round(.95*(len(ratios)-1))],
        "Rp_gt1":sum(x>1 for x in ratios)/len(ratios),
        "final_cumulative":cont[max(cont)] if cont else float("nan"),
        "max_abs_global":max(abs(x) for x in glob.values()) if glob else float("nan"),
        "median_abs_global":statistics.median(abs(x) for x in glob.values()) if glob else float("nan"),
        "maxCo":max(co.values()) if co else float("nan"),
        "clock":clock[max(clock)] if clock else float("nan"),
    }

def probe(case):
    p=BASE/case/"postProcessing"/"metal"/"temperatureProbe"/"0"/"T"
    rows=read_table(p)
    return {r[0]:r[1] for r in rows}

def series_compare(a,b):
    ts=sorted(set(a)&set(b))
    d=[b[t]-a[t] for t in ts]
    return {"rmse":math.sqrt(sum(x*x for x in d)/len(d)),
            "max_abs":max(abs(x) for x in d),
            "final_diff":d[-1],"final_ref":a[ts[-1]],"final_test":b[ts[-1]]}

summary=["# V9 metalTop fixedFluxPressure comparison","",
"V9 changes metalTop p_rgh from totalPressure to fixedFluxPressure while keeping U=slip and the same thermal boundary condition. B9 additionally required a diagnostic linear extension of the rho(T) table above 1773.15 K after an early table-range failure. Therefore B9-vs-B5 is not a perfectly single-change comparison after that extension; C9-vs-C5 remains a clean single-BC comparison.",""]

detail_rows=[]

for fam,(refcase,testcase) in PAIRS.items():
    ec0,ec1=energy(refcase),energy(testcase)
    cp0,cp1=coupling(refcase),coupling(testcase)
    ph0,ph1=phi_stats(refcase),phi_stats(testcase)
    pr=series_compare(probe(refcase),probe(testcase))
    summary += [f"## Family {fam}: {testcase} vs {refcase}","",
        "### Boundary transport / energy","",
        f"- reference integrated top advective energy: {ec0['top_adv']:.3f} J",
        f"- V9 integrated top advective energy: {ec1['top_adv']:.3e} J",
        f"- reference integrated total boundary advective energy: {ec0['bd_adv']:.3f} J",
        f"- V9 integrated total boundary advective energy: {ec1['bd_adv']:.3e} J",
        f"- reference integrated top diffusive energy: {ec0['top_diff']:.3f} J",
        f"- V9 integrated top diffusive energy: {ec1['top_diff']:.3f} J",
        f"- reference integrated mold diffusive energy: {ec0['mold_diff']:.3f} J",
        f"- V9 integrated mold diffusive energy: {ec1['mold_diff']:.3f} J",
        f"- reference integrated boundary total energy: {ec0['bd_total']:.3f} J",
        f"- V9 integrated boundary total energy: {ec1['bd_total']:.3f} J",
    ]
    if ph1:
        summary += [
            f"- V9 max |sum(phi)_metalTop|: {ph1['max_abs']:.3e}",
            f"- V9 time-integrated signed sum(phi)_metalTop: {ph1['integral']:.3e}",
        ]
    summary += ["","### Coupling / continuity / cost","",
        "| case | median Rp | p95 Rp | Rp>1 | final cumulative | max |global| | median |global| | max Co | clock s |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {refcase} | {cp0['median_Rp']:.4f} | {cp0['p95_Rp']:.4f} | {100*cp0['Rp_gt1']:.2f}% | {cp0['final_cumulative']:.6g} | {cp0['max_abs_global']:.3e} | {cp0['median_abs_global']:.3e} | {cp0['maxCo']:.4f} | {cp0['clock']:.1f} |",
        f"| {testcase} | {cp1['median_Rp']:.4f} | {cp1['p95_Rp']:.4f} | {100*cp1['Rp_gt1']:.2f}% | {cp1['final_cumulative']:.6g} | {cp1['max_abs_global']:.3e} | {cp1['median_abs_global']:.3e} | {cp1['maxCo']:.4f} | {cp1['clock']:.1f} |",
        "",
        "### Center temperature probe","",
        f"- RMSE(V9-reference): {pr['rmse']:.4f} K",
        f"- max |difference|: {pr['max_abs']:.4f} K",
        f"- final reference: {pr['final_ref']:.3f} K; V9: {pr['final_test']:.3f} K; difference {pr['final_diff']:+.3f} K",
        "",
        "### Spatial profiles",""
    ]

    for pname,(pfolder,mfolder,file) in PROFILES.items():
        ro=load_profile(refcase,pfolder,file); to=load_profile(testcase,pfolder,file)
        rm=load_profile(refcase,mfolder,file); tm=load_profile(testcase,mfolder,file)
        times=sorted(set(to)&set(tm))
        rec=[]
        for t in times:
            rr=interp(ro,t); rrm=interp(rm,t)
            if rr is None or rrm is None: continue
            tt,ttm=to[t],tm[t]
            x={
                "t":t,
                "Uy":scalar_metric(rr,tt,2),
                "T":scalar_metric(rr,tt,4),
                "alpha":scalar_metric(rr,tt,7),
                "wz":scalar_metric(rr,tt,10),
                "flow":flow_metric(rr,tt),
                "Darcy":mag_metric(rrm,ttm,13),
                "pRgh":mag_metric(rrm,ttm,15),
            }
            rec.append(x)
            detail_rows.append({"family":fam,"reference":refcase,"test":testcase,"profile":pname,"time_s":t,
                "Uy_nrmse_pct":x["Uy"]["nrmse"],"Uy_corr":x["Uy"]["corr"],
                "T_rmse_K":x["T"]["rmse"],"alpha_rmse":x["alpha"]["rmse"],
                "wz_rmse":x["wz"]["rmse"],"wz_nrmse_pct":x["wz"]["nrmse"],"wz_corr":x["wz"]["corr"],
                "flowType_class_disagreement":x["flow"]["disagree"],
                "Darcy_nrmse_pct":x["Darcy"]["nrmse"],"pRghAccel_nrmse_pct":x["pRgh"]["nrmse"]})
        validuy=[r["Uy"]["nrmse"] for r in rec if math.isfinite(r["Uy"]["nrmse"])]
        validw=[r["wz"]["nrmse"] for r in rec if math.isfinite(r["wz"]["nrmse"])]
        last=rec[-1]
        peak=max((r for r in rec if math.isfinite(r["Uy"]["nrmse"])),key=lambda r:r["Uy"]["nrmse"])
        summary += [
            f"#### {pname}",
            f"- samples: {len(rec)}; time range {rec[0]['t']:.3f}–{rec[-1]['t']:.3f} s",
            f"- Uy median NRMSE: {statistics.median(validuy):.2f}%; final {last['Uy']['nrmse']:.2f}%; peak {peak['Uy']['nrmse']:.2f}% at {peak['t']:.3f} s; final corr {last['Uy']['corr']:.4f}",
            f"- final T RMSE: {last['T']['rmse']:.3f} K",
            f"- final alphaL RMSE: {last['alpha']['rmse']:.5f}",
            f"- vorticity_z median NRMSE: {statistics.median(validw):.2f}%; final absolute RMSE {last['wz']['rmse']:.4g} 1/s; final corr {last['wz']['corr']:.4f}",
            f"- final flowType class disagreement: {100*last['flow']['disagree']:.1f}%",
            f"- final |Darcy acceleration| NRMSE: {last['Darcy']['nrmse']:.2f}%",
            f"- final |p_rgh acceleration| NRMSE: {last['pRgh']['nrmse']:.2f}%",
        ]
        if pname=="vertical_x20mm":
            rr=interp(ro,last["t"]); tt=to[last["t"]]
            vals={}
            for a in (0.05,0.5,0.95):
                vals[a]=(crossings(rr,7,a),crossings(tt,7,a))
                summary.append(f"- alphaL={a:.2f} crossing(s), mm: ref {[round(x*1000,3) for x in vals[a][0]]}; V9 {[round(x*1000,3) for x in vals[a][1]]}")
            if all(vals[a][0] and vals[a][1] for a in (0.05,0.95)):
                wr=(vals[0.95][0][0]-vals[0.05][0][0])*1000
                wt=(vals[0.95][1][0]-vals[0.05][1][0])*1000
                summary.append(f"- vertical mushy width (0.05->0.95): ref {wr:.3f} mm; V9 {wt:.3f} mm; change {wt-wr:+.3f} mm ({100*(wt/wr-1):+.2f}%)")
        summary.append("")
    summary.append("")

with (OUT/"profile_comparison.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(detail_rows[0].keys())); w.writeheader(); w.writerows(detail_rows)
(OUT/"summary.md").write_text("\n".join(summary)+"\n")
print((OUT/"summary.md").read_text())
