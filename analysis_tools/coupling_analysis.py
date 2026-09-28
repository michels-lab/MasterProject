#!/usr/bin/env python3
from __future__ import annotations
import csv, math, re, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CASES=ROOT/"cases_controlled_buoyancy"
OUT=ROOT/"analysis_results"/"coupling"
OUT.mkdir(parents=True,exist_ok=True)

CASE_NAMES=[
"B3_reference","B4_energy2","B5_outer3","B6_adaptiveDt","B7_outer4",
"C3_reference","C4_energy2","C5_outer3","C6_adaptiveDt","C7_outer4",
]

def read_series(path):
    d={}
    if not path.exists(): return d
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s: continue
        p=s.split()
        if len(p)<2: continue
        try:
            t=float(p[0].rstrip("s"))
            v=float(p[1])
            d[t]=v
        except ValueError: pass
    return d

def indexed(logdir,prefix):
    arr=[]
    for p in logdir.glob(prefix+"_*"):
        m=re.fullmatch(re.escape(prefix)+r"_(\d+)",p.name)
        if m: arr.append((int(m.group(1)),p))
    return [p for _,p in sorted(arr)]

def percentile(vals,q):
    s=sorted(vals)
    if not s: return float("nan")
    x=(len(s)-1)*q
    i=int(math.floor(x)); j=int(math.ceil(x))
    return s[i] if i==j else s[i]+(s[j]-s[i])*(x-i)

def med(vals): return statistics.median(vals) if vals else float("nan")
def mean(vals): return statistics.fmean(vals) if vals else float("nan")

rows=[]
summary=[]
for case in CASE_NAMES:
    c=CASES/case
    logs=c/"logs"
    fv=(c/"system"/"fvSolution").read_text()
    mo=re.search(r"nOuterCorrectors\s+(\d+)\s*;",fv)
    me=re.search(r"nEnergyCorrectors\s+(\d+)\s*;",fv)
    nouter=int(mo.group(1)) if mo else 1
    nenergy=int(me.group(1)) if me else 1

    pfiles=indexed(logs,"p_rgh")
    pfinal=indexed(logs,"p_rghFinalRes")
    hfiles=indexed(logs,"h")
    hfinal=indexed(logs,"hFinalRes")
    efiles=indexed(logs,"e")
    efinal=indexed(logs,"eFinalRes")
    contfiles=indexed(logs,"contCumulative")

    ps=[read_series(x) for x in pfiles]
    pfs=[read_series(x) for x in pfinal]
    hs=[read_series(x) for x in hfiles]
    hfs=[read_series(x) for x in hfinal]
    es=[read_series(x) for x in efiles]
    efs=[read_series(x) for x in efinal]

    # Pressure solves are distributed evenly across root-level outer correctors.
    p_per_outer=(len(ps)//nouter) if nouter and len(ps)%nouter==0 else None
    last_outer_first=(nouter-1)*p_per_outer if p_per_outer else None

    sets=[set(x) for x in ps+hs+es if x]
    times=sorted(set.intersection(*sets)) if sets else []
    for t in times:
        if t<0.1: continue
        p0=ps[0][t] if ps else float("nan")
        plo=ps[last_outer_first][t] if last_outer_first is not None else float("nan")
        rp=plo/p0 if p0 else float("nan")
        h0=hs[0][t] if hs else float("nan")
        hl=hs[-1][t] if hs else float("nan")
        rh=hl/h0 if h0 else float("nan")
        e0=es[0][t] if es else float("nan")
        el=es[-1][t] if es else float("nan")
        re_=el/e0 if e0 else float("nan")
        lastpf=pfs[-1].get(t,float("nan")) if pfs else float("nan")
        lasthf=hfs[-1].get(t,float("nan")) if hfs else float("nan")
        lastef=efs[-1].get(t,float("nan")) if efs else float("nan")
        rows.append({
            "case":case,"time_s":t,"nOuterCorrectors":nouter,"nEnergyCorrectors":nenergy,
            "p_solves_per_timestep":len(ps),"h_solves_per_timestep":len(hs),"e_solves_per_timestep":len(es),
            "p_first_outer_initial":p0,"p_last_outer_first_initial":plo,"R_p_outer":rp,
            "h_first_initial":h0,"h_last_initial":hl,"R_h_total":rh,
            "e_first_initial":e0,"e_last_initial":el,"R_e_total":re_,
            "p_last_linear_final":lastpf,"h_last_linear_final":lasthf,"e_last_linear_final":lastef,
        })

    grp=[r for r in rows if r["case"]==case]
    def vals(k): return [r[k] for r in grp if math.isfinite(r[k])]
    rp=vals("R_p_outer"); rh=vals("R_h_total"); re_=vals("R_e_total")
    pfin=vals("p_last_linear_final"); hfin=vals("h_last_linear_final"); efin=vals("e_last_linear_final")
    courant=read_series(logs/"CourantMax_0")
    clock=read_series(logs/"clockTime_0")
    cont=read_series(contfiles[-1]) if contfiles else {}
    summary.append({
        "case":case,"nOuterCorrectors":nouter,"nEnergyCorrectors":nenergy,
        "p_solves_per_timestep":len(ps),"h_solves_per_timestep":len(hs),"e_solves_per_timestep":len(es),
        "median_R_p_outer":med(rp),"p95_R_p_outer":percentile(rp,.95),
        "fraction_R_p_outer_gt1":sum(v>1 for v in rp)/len(rp) if rp else float("nan"),
        "median_R_h_total":med(rh),"p95_R_h_total":percentile(rh,.95),
        "fraction_R_h_total_gt1":sum(v>1 for v in rh)/len(rh) if rh else float("nan"),
        "median_R_e_total":med(re_),"p95_R_e_total":percentile(re_,.95),
        "fraction_R_e_total_gt1":sum(v>1 for v in re_)/len(re_) if re_ else float("nan"),
        "median_p_last_linear_final":med(pfin),"p95_p_last_linear_final":percentile(pfin,.95),
        "median_h_last_linear_final":med(hfin),"median_e_last_linear_final":med(efin),
        "max_Courant":max(courant.values()) if courant else float("nan"),
        "final_abs_cumulative_continuity":abs(cont[max(cont)]) if cont else float("nan"),
        "clockTime_s":clock[max(clock)] if clock else float("nan"),
        "n_compared_timesteps":len(grp),
    })

with (OUT/"coupling_time_series.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with (OUT/"coupling_summary.csv").open("w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0].keys())); w.writeheader(); w.writerows(summary)

def fmt(x,n=4):
    return "n/a" if not math.isfinite(x) else f"{x:.{n}g}"

md=[
"# Coupling analysis",
"",
"Definitions:",
"- R_p_outer = initial residual of the first p_rgh solve in the last outer corrector / corresponding initial residual in the first outer corrector. Lower is stronger typical outer-loop contraction; R>1 means the pressure initial residual increased across the outer loop.",
"- R_h_total and R_e_total compare the last and first initial residuals of the energy solves within the timestep. They include both outer and energy-corrector effects.",
"- Linear final residuals evaluate the individual linear solves and are not the same as multi-equation coupling.",
"",
"| Case | outer | energy | median Rp | p95 Rp | Rp>1 | median Rh | median Re | continuity | max Co | clock s |",
"|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for r in summary:
    md.append(
        f"| {r['case']} | {r['nOuterCorrectors']} | {r['nEnergyCorrectors']} | "
        f"{fmt(r['median_R_p_outer'])} | {fmt(r['p95_R_p_outer'])} | {100*r['fraction_R_p_outer_gt1']:.2f}% | "
        f"{fmt(r['median_R_h_total'])} | {fmt(r['median_R_e_total'])} | "
        f"{fmt(r['final_abs_cumulative_continuity'])} | {fmt(r['max_Courant'])} | {fmt(r['clockTime_s'])} |"
    )
md += [
"",
"Interpretation rule:",
"A numerically preferable coupling configuration should reduce outer-loop and energy coupling residuals without increasing continuity error or linear-solver residuals, while preserving the physical solution. Additional correctors that only increase cost without materially changing these metrics or the physical fields are diminishing returns.",
]
(OUT/"coupling_summary.md").write_text("\n".join(md)+"\n")
print("Wrote coupling analysis outputs")
