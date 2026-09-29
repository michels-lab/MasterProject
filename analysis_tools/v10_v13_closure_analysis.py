#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cases_controlled_buoyancy"
OUT = ROOT / "analysis_results" / "v10_v13_closure"
OUT.mkdir(parents=True, exist_ok=True)

CASES = {
    "B10": "B10_airGapOF14",
    "C10": "C10_airGapOF14",
    "B11": "B11_topFixedFlux_airGapOF14",
    "C11": "C11_topFixedFlux_airGapOF14",
    "B12": "B12_topFixedValue_airGapOF14",
    "C12": "C12_topFixedValue_airGapOF14",
    "B13": "B13_prghPressure_airGapOF14",
    "C13": "C13_prghPressure_airGapOF14",
}

PAIR_SPECS = [
    ("B11_vs_B10", "B10", "B11", "effect of closing metalTop with fixedFluxPressure in B"),
    ("C11_vs_C10", "C10", "C11", "effect of closing metalTop with fixedFluxPressure in C"),
    ("B11_vs_B12", "B11", "B12", "fixedFluxPressure vs fixedValue p_rgh in B"),
    ("B11_vs_B13", "B11", "B13", "fixedFluxPressure vs atmospheric prghPressure in B"),
    ("C11_vs_C12", "C11", "C12", "fixedFluxPressure vs fixedValue p_rgh in C"),
    ("C11_vs_C13", "C11", "C13", "fixedFluxPressure vs atmospheric prghPressure in C"),
    ("B11_vs_C11", "B11", "C11", "B vs C under the same impermeable top and OF14 air gap"),
]

PROFILE_SPECS = {
    "y20mm": ("horizontalProfiles", "line_y20mm.xy"),
    "y30mm": ("horizontalProfiles", "line_y30mm.xy"),
    "x20mm": ("verticalProfiles", "line_x20mm.xy"),
}

PROFILE_COLS = {
    "Uy": 2,
    "T": 4,
    "alphaL": 7,
    "vorticity_z": 10,
    "flowType": 11,
}


def fnum(tok: str) -> float:
    tok = tok.strip()
    if tok.endswith("s"):
        tok = tok[:-1]
    return float(tok)


def rows(path: Path):
    out = []
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        try:
            vals = [fnum(x) for x in parts]
        except ValueError:
            continue
        out.append(vals)
    return out


def scalar_series(path: Path, col=1):
    out = {}
    for r in rows(path):
        if len(r) > col:
            out[r[0]] = r[col]
    return out


def trapz(data, col):
    if len(data) < 2:
        return float("nan")
    total = 0.0
    used = 0
    for i in range(1, len(data)):
        if len(data[i]) > col and len(data[i-1]) > col:
            total += 0.5*(data[i][col]+data[i-1][col])*(data[i][0]-data[i-1][0])
            used += 1
    return total if used else float("nan")


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def fmt(x, n=6):
    return "n/a" if not finite(x) else f"{x:.{n}g}"


def median(xs):
    xs = [x for x in xs if finite(x)]
    return statistics.median(xs) if xs else float("nan")


def percentile(xs, q):
    xs = sorted(x for x in xs if finite(x))
    if not xs:
        return float("nan")
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs)-1)*q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    w = pos-lo
    return xs[lo]*(1-w)+xs[hi]*w


def rmse(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b))/len(a))


def mae(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    return sum(abs(x-y) for x,y in zip(a,b))/len(a)


def pearson(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    ma = sum(a)/len(a)
    mb = sum(b)/len(b)
    aa = [x-ma for x in a]
    bb = [y-mb for y in b]
    den = math.sqrt(sum(x*x for x in aa)*sum(y*y for y in bb))
    return sum(x*y for x,y in zip(aa,bb))/den if den else float("nan")


def compare_series(sa, sb):
    ts = sorted(set(sa) & set(sb))
    if not ts:
        return {}
    a = [sa[t] for t in ts]
    b = [sb[t] for t in ts]
    return {
        "samples": len(ts),
        "start_s": ts[0],
        "end_s": ts[-1],
        "rmse": rmse(a,b),
        "mae": mae(a,b),
        "max_abs_diff": max(abs(x-y) for x,y in zip(a,b)),
        "final_ref": a[-1],
        "final_other": b[-1],
        "final_diff": b[-1]-a[-1],
        "pearson_r": pearson(a,b),
    }


def last_value(path: Path):
    d = rows(path)
    return d[-1][1] if d and len(d[-1]) > 1 else float("nan")


def all_matching(case: Path, pattern: str):
    return sorted((case/"logs").glob(pattern))


def latest_probe_time(case: Path):
    s = scalar_series(case/"postProcessing"/"metal"/"temperatureProbe"/"0"/"T")
    return max(s) if s else float("nan")


def log_end(case: Path):
    p = case/"log.foamMultiRun"
    if not p.is_file():
        return False
    return bool(re.search(r"(?m)^End\s*$", p.read_text(errors="replace")))


def log_has_fatal(case: Path):
    p = case/"log.foamMultiRun"
    if not p.is_file():
        return True
    txt = p.read_text(errors="replace")
    return bool(re.search(r"FOAM FATAL|Floating point exception|Segmentation fault|Killed", txt, re.I))


def pressure_metrics(case: Path):
    p0 = scalar_series(case/"logs"/"p_rgh_0")
    p4 = scalar_series(case/"logs"/"p_rgh_4")
    ts = sorted(set(p0) & set(p4))
    ratios = [p4[t]/p0[t] for t in ts if p0[t] != 0]
    finals = []
    for f in all_matching(case, "p_rghFinalRes_*"):
        finals.extend(scalar_series(f).values())
    return {
        "p0_initial_median": median(p0.values()),
        "Rp_outer_median": median(ratios),
        "Rp_outer_p95": percentile(ratios,0.95),
        "Rp_outer_gt1_frac": (sum(x>1 for x in ratios)/len(ratios)) if ratios else float("nan"),
        "p_final_residual_median": median(finals),
        "p_final_residual_max": max(finals) if finals else float("nan"),
    }


def continuity_metrics(case: Path):
    cum_files = all_matching(case,"contCumulative_*")
    glob_files = all_matching(case,"contGlobal_*")
    def suffix(p):
        try:
            return int(p.name.rsplit("_",1)[1])
        except Exception:
            return -1
    cum_final = last_value(max(cum_files,key=suffix)) if cum_files else float("nan")
    gv = []
    for f in glob_files:
        gv.extend(scalar_series(f).values())
    return {
        "cont_cumulative_final": cum_final,
        "cont_global_max_abs": max((abs(x) for x in gv),default=float("nan")),
        "cont_global_median_abs": median(abs(x) for x in gv),
    }


def courant_metrics(case: Path):
    vals = []
    for f in all_matching(case,"CourantMax_*"):
        vals.extend(scalar_series(f).values())
    return {
        "max_Co": max(vals) if vals else float("nan"),
        "median_Co_max_series": median(vals),
    }


def runtime_metrics(case: Path):
    ex = scalar_series(case/"logs"/"executionTime_0")
    cl = scalar_series(case/"logs"/"clockTime_0")
    return {
        "execution_time_s": ex[max(ex)] if ex else float("nan"),
        "clock_time_s": cl[max(cl)] if cl else float("nan"),
    }


def energy_metrics(case: Path):
    b = case/"postProcessing"/"metal"
    top = rows(b/"metalTopEnergyPower"/"0"/"surfaceFieldValue.dat")
    mold = rows(b/"metalMoldEnergyPower"/"0"/"surfaceFieldValue.dat")
    bd = rows(b/"metalBoundaryEnergyPower"/"0"/"surfaceFieldValue.dat")
    lat = rows(b/"metalLatentHeatPower"/"0"/"volFieldValue.dat")
    hs = rows(b/"metalSensibleEnthalpy"/"0"/"volFieldValue.dat")
    out = {}
    if top:
        out.update({
            "E_top_adv_J": trapz(top,1),
            "E_top_heat_J": trapz(top,2),
            "E_top_total_J": trapz(top,3),
            "top_adv_max_abs_W": max(abs(r[1]) for r in top if len(r)>1),
        })
    if mold:
        out.update({
            "E_mold_adv_J": trapz(mold,1),
            "E_mold_heat_J": trapz(mold,2),
            "E_mold_total_J": trapz(mold,3),
        })
    if bd:
        out.update({
            "E_boundary_adv_J": trapz(bd,1),
            "E_boundary_heat_J": trapz(bd,2),
            "E_boundary_total_J": trapz(bd,3),
        })
    if lat:
        out["E_latent_diagnostic_J"] = trapz(lat,1)
    if hs:
        out["delta_sensible_H_J"] = hs[-1][1]-hs[0][1]
    return out


def phi_metrics(case: Path):
    p = case/"postProcessing"/"metal"/"metalTopPhiSum"/"0"/"surfaceFieldValue.dat"
    d = rows(p)
    if not d:
        return {
            "top_phi_available": False,
            "top_phi_max_abs_kg_s": float("nan"),
            "top_phi_integral_kg": float("nan"),
            "top_phi_final_kg_s": float("nan"),
        }
    return {
        "top_phi_available": True,
        "top_phi_max_abs_kg_s": max(abs(r[1]) for r in d if len(r)>1),
        "top_phi_integral_kg": trapz(d,1),
        "top_phi_final_kg_s": d[-1][1],
    }


def center_probe(case: Path):
    b = case/"postProcessing"/"metal"/"temperatureProbe"/"0"
    T = scalar_series(b/"T")
    A = scalar_series(b/"phaseChangeSource:alpha1")
    R = scalar_series(b/"rho")
    return T,A,R


def mean_alpha(case: Path):
    return scalar_series(case/"postProcessing"/"metal"/"metalMeanLiquidFraction"/"0"/"volFieldValue.dat")


def profile_at(case: Path, folder: str, filename: str, target=None):
    root = case/"postProcessing"/"metal"/folder
    choices = []
    if root.is_dir():
        for d in root.iterdir():
            if not d.is_dir():
                continue
            try:
                t = float(d.name)
            except ValueError:
                continue
            p = d/filename
            if p.is_file():
                choices.append((t,p))
    if not choices:
        return float("nan"),[]
    if target is None:
        t,p = max(choices)
    else:
        t,p = min(choices,key=lambda x: abs(x[0]-target))
    return t,rows(p)


def profile_compare(a,b,idx):
    if not a or not b or len(a)!=len(b) or any(len(r)<=idx for r in a+b):
        return {}
    av=[r[idx] for r in a]
    bv=[r[idx] for r in b]
    e=rmse(av,bv)
    rms_ref=math.sqrt(sum(x*x for x in av)/len(av))
    return {
        "rmse":e,
        "mae":mae(av,bv),
        "nrmse_rms_pct":100*e/rms_ref if rms_ref else float("nan"),
        "pearson_r":pearson(av,bv),
        "max_abs_diff":max(abs(x-y) for x,y in zip(av,bv)),
    }


def flow_class(v):
    if v>0.2:
        return 1
    if v<-0.2:
        return -1
    return 0


def front_crossing(data,threshold,alpha_idx=7):
    pts=[(r[0],r[alpha_idx]) for r in data if len(r)>alpha_idx]
    for (x0,a0),(x1,a1) in zip(pts,pts[1:]):
        if a0==threshold:
            return x0
        if (a0-threshold)*(a1-threshold)<=0 and a1!=a0:
            w=(threshold-a0)/(a1-a0)
            return x0+w*(x1-x0)
    return float("nan")


def mushy_metrics(case: Path):
    t,d=profile_at(case,"verticalProfiles","line_x20mm.xy")
    a05=front_crossing(d,0.05)
    a50=front_crossing(d,0.50)
    a95=front_crossing(d,0.95)
    width=abs(a95-a05) if finite(a05) and finite(a95) else float("nan")
    return {
        "profile_final_time_s":t,
        "front_alpha05_m":a05,
        "front_alpha50_m":a50,
        "front_alpha95_m":a95,
        "mushy_width_m":width,
    }


case_rows=[]
series_cache={}
for label,name in CASES.items():
    case=BASE/name
    T,A,R=center_probe(case)
    AM=mean_alpha(case)
    latest=latest_probe_time(case)
    row={
        "label":label,
        "case":name,
        "latest_probe_time_s":latest,
        "log_has_End":log_end(case),
        "log_has_fatal":log_has_fatal(case),
        "run_complete_10s":finite(latest) and latest>=9.999 and log_end(case) and not log_has_fatal(case),
        "T_center_final_K":T[max(T)] if T else float("nan"),
        "alphaL_center_final":A[max(A)] if A else float("nan"),
        "rho_center_final_kg_m3":R[max(R)] if R else float("nan"),
        "alphaL_mean_final":AM[max(AM)] if AM else float("nan"),
    }
    row.update(phi_metrics(case))
    row.update(energy_metrics(case))
    row.update(pressure_metrics(case))
    row.update(continuity_metrics(case))
    row.update(courant_metrics(case))
    row.update(runtime_metrics(case))
    row.update(mushy_metrics(case))
    case_rows.append(row)
    series_cache[label]={"T":T,"A":A,"AM":AM}

case_fields=sorted({k for r in case_rows for k in r})
with (OUT/"case_metrics.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=case_fields)
    w.writeheader()
    w.writerows(case_rows)

pair_rows=[]
profile_rows=[]
for pname,ref,other,purpose in PAIR_SPECS:
    row={"comparison":pname,"reference":ref,"other":other,"purpose":purpose}
    for key,prefix in (("T","T"),("A","alphaL_center"),("AM","alphaL_mean")):
        m=compare_series(series_cache[ref][key],series_cache[other][key])
        for k,v in m.items():
            row[f"{prefix}_{k}"]=v
    pair_rows.append(row)
    for prof,(folder,filename) in PROFILE_SPECS.items():
        tr,ar=profile_at(BASE/CASES[ref],folder,filename)
        to,ao=profile_at(BASE/CASES[other],folder,filename,tr if finite(tr) else None)
        for var,idx in PROFILE_COLS.items():
            m=profile_compare(ar,ao,idx)
            if not m:
                continue
            rec={"comparison":pname,"profile":prof,"reference_time_s":tr,"other_time_s":to,"variable":var,**m}
            if var=="flowType":
                ac=[flow_class(r[idx]) for r in ar]
                bc=[flow_class(r[idx]) for r in ao]
                rec["class_disagreement_frac"]=sum(x!=y for x,y in zip(ac,bc))/len(ac) if ac else float("nan")
            profile_rows.append(rec)

pair_fields=sorted({k for r in pair_rows for k in r})
with (OUT/"pair_metrics.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=pair_fields)
    w.writeheader()
    w.writerows(pair_rows)

if profile_rows:
    profile_fields=sorted({k for r in profile_rows for k in r})
    with (OUT/"profile_metrics.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=profile_fields)
        w.writeheader()
        w.writerows(profile_rows)

by_label={r["label"]:r for r in case_rows}
by_pair={r["comparison"]:r for r in pair_rows}

lines=[
    "# V10-V13 closure analysis",
    "",
    "**Generated directly from versioned logs/postProcessing.**",
    "",
    "## Run completeness and core diagnostics",
    "",
    "| case | complete | final T K | final mean alphaL | max Co | median Rp_outer | Rp>1 | final cumulative continuity | max abs(phi_top) kg/s | Eadv top J |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for label in CASES:
    r=by_label[label]
    lines.append(
        f"| {label} | {r['run_complete_10s']} | {fmt(r['T_center_final_K'])} | {fmt(r['alphaL_mean_final'])} | "
        f"{fmt(r['max_Co'])} | {fmt(r['Rp_outer_median'])} | {fmt(r['Rp_outer_gt1_frac'])} | "
        f"{fmt(r['cont_cumulative_final'])} | {fmt(r['top_phi_max_abs_kg_s'])} | {fmt(r.get('E_top_adv_J'))} |"
    )

lines += ["","## Controlled comparisons"]
for pname,ref,other,purpose in PAIR_SPECS:
    r=by_pair[pname]
    lines += [
        "",
        f"### {pname}",
        f"- Purpose: {purpose}.",
        f"- Center T: RMSE {fmt(r.get('T_rmse'))} K; MAE {fmt(r.get('T_mae'))} K; max abs dT {fmt(r.get('T_max_abs_diff'))} K; final dT(other-ref) {fmt(r.get('T_final_diff'))} K.",
        f"- Center alphaL: RMSE {fmt(r.get('alphaL_center_rmse'))}; final dAlphaL {fmt(r.get('alphaL_center_final_diff'))}.",
        f"- Mean alphaL: RMSE {fmt(r.get('alphaL_mean_rmse'))}; final dAlphaL {fmt(r.get('alphaL_mean_final_diff'))}.",
    ]
    for prof in PROFILE_SPECS:
        uy=[x for x in profile_rows if x["comparison"]==pname and x["profile"]==prof and x["variable"]=="Uy"]
        if uy:
            x=uy[0]
            lines.append(f"- {prof} Uy at ~{fmt(x['reference_time_s'])} s: NRMSE/RMS {fmt(x['nrmse_rms_pct'])}%; Pearson r {fmt(x['pearson_r'])}.")
        ft=[x for x in profile_rows if x["comparison"]==pname and x["profile"]==prof and x["variable"]=="flowType"]
        if ft:
            x=ft[0]
            lines.append(f"- {prof} flowType class disagreement: {fmt(100*x.get('class_disagreement_frac',float('nan')))}%.")

lines += [
    "",
    "## Boundary-condition closure facts",
    "",
    f"- B11: max abs(sum(phi_top)) = {fmt(by_label['B11']['top_phi_max_abs_kg_s'])} kg/s; integrated top advection = {fmt(by_label['B11'].get('E_top_adv_J'))} J.",
    f"- C11: max abs(sum(phi_top)) = {fmt(by_label['C11']['top_phi_max_abs_kg_s'])} kg/s; integrated top advection = {fmt(by_label['C11'].get('E_top_adv_J'))} J.",
    f"- B12: max abs(sum(phi_top)) = {fmt(by_label['B12']['top_phi_max_abs_kg_s'])} kg/s; integrated top advection = {fmt(by_label['B12'].get('E_top_adv_J'))} J.",
    f"- B13: max abs(sum(phi_top)) = {fmt(by_label['B13']['top_phi_max_abs_kg_s'])} kg/s; integrated top advection = {fmt(by_label['B13'].get('E_top_adv_J'))} J.",
    f"- C12: max abs(sum(phi_top)) = {fmt(by_label['C12']['top_phi_max_abs_kg_s'])} kg/s; integrated top advection = {fmt(by_label['C12'].get('E_top_adv_J'))} J.",
    f"- C13: max abs(sum(phi_top)) = {fmt(by_label['C13']['top_phi_max_abs_kg_s'])} kg/s; integrated top advection = {fmt(by_label['C13'].get('E_top_adv_J'))} J.",
    "",
    "B10/C10 do not contain metalTopPhiSum because that function object was added after those already-running cases. Their top-boundary diagnosis therefore uses the stored energyAdvectiveFlux instead of inventing a retrospective phi value.",
    "",
    "## Interpretation guardrails",
    "",
    "- sum(phi) is a net patch flux. Near-zero net sum alone does not prove face-wise impermeability; non-zero advective enthalpy can reveal cancelling local in/out flux.",
    "- B-family latent-energy reconstruction remains diagnostic because the stored rho*(-ddt(alphaL))*L is not exactly L*ddt(rho*alphaL).",
    "- Small numerical differences are verification evidence, not experimental validation.",
    "- No recalescence mechanism is inferred from a temperature rebound alone; alphaL and boundary energy/mass transport must be checked simultaneously.",
    "",
]

(OUT/"summary.md").write_text("\n".join(lines),encoding="utf-8")
print((OUT/"summary.md").read_text())
