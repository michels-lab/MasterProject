#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cases_controlled_buoyancy"
OUT = ROOT / "analysis_results" / "v10_v11"
OUT.mkdir(parents=True, exist_ok=True)

CASES = {
    "B10": "B10_airGapOF14",
    "C10": "C10_airGapOF14",
    "B11": "B11_topFixedFlux_airGapOF14",
    "C11": "C11_topFixedFlux_airGapOF14",
}

COMPARISONS = [
    ("B11_vs_B10", "B10", "B11"),
    ("C11_vs_C10", "C10", "C11"),
    ("C10_vs_B10", "B10", "C10"),
    ("C11_vs_B11", "B11", "C11"),
]

PROFILES = {
    "y20mm": ("horizontalProfiles", "line_y20mm.xy"),
    "y30mm": ("horizontalProfiles", "line_y30mm.xy"),
    "vertical_x20mm": ("verticalProfiles", "line_x20mm.xy"),
}


def numeric_dirs(path):
    out = []
    if not path.is_dir():
        return out
    for p in path.iterdir():
        if p.is_dir():
            try:
                out.append((float(p.name), p))
            except ValueError:
                pass
    return sorted(out)


def rows(path):
    out = []
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            out.append([float(x) for x in s.split()])
        except ValueError:
            pass
    return out


def trapz(data, col):
    if len(data) < 2:
        return float("nan")
    return sum(
        0.5*(data[i][col] + data[i-1][col])*(data[i][0] - data[i-1][0])
        for i in range(1, len(data))
    )


def rmse(a, b):
    return math.sqrt(sum((y-x)**2 for x, y in zip(a, b))/len(a)) if a and len(a)==len(b) else float("nan")


def cosine(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    den = math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b))/den if den else float("nan")


def pearson(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    aa = [x-ma for x in a]
    bb = [x-mb for x in b]
    den = math.sqrt(sum(x*x for x in aa)*sum(y*y for y in bb))
    return sum(x*y for x, y in zip(aa, bb))/den if den else float("nan")


def fmt(x, n=5):
    return "n/a" if not isinstance(x, (int, float)) or not math.isfinite(x) else f"{x:.{n}g}"


def status(case):
    c = BASE/case
    ts = numeric_dirs(c)
    latest = ts[-1][0] if ts else float("nan")
    log = c/"log.foamMultiRun"
    text = log.read_text(errors="replace") if log.is_file() else ""
    ended = bool(re.search(r"(?m)^End\s*$", text))
    return {
        "latest_time_s": latest,
        "log_has_End": ended,
        "complete_10s": math.isfinite(latest) and abs(latest-10.0) < 1e-9 and ended,
    }


def series_from(path):
    return {r[0]: r[1] for r in rows(path) if len(r) >= 2}


def probe(case):
    return series_from(BASE/case/"postProcessing"/"metal"/"temperatureProbe"/"0"/"T")


def alpha_mean(case):
    base = BASE/case/"postProcessing"/"metal"/"metalMeanLiquidFraction"/"0"
    for name in ("volFieldValue.dat", "volumeFieldValue.dat"):
        s = series_from(base/name)
        if s:
            return s
    return {}


def compare_series(a, b):
    ts = sorted(set(a) & set(b))
    if not ts:
        return {}
    av = [a[t] for t in ts]
    bv = [b[t] for t in ts]
    d = [y-x for x, y in zip(av, bv)]
    return {
        "samples": len(ts),
        "rmse": rmse(av, bv),
        "max_abs": max(abs(x) for x in d),
        "final_ref": av[-1],
        "final_other": bv[-1],
        "final_diff": d[-1],
        "cosine_similarity": cosine(av, bv),
        "pearson_r": pearson(av, bv),
    }


def top_phi(case):
    p = BASE/case/"postProcessing"/"metal"/"metalTopPhiSum"/"0"/"surfaceFieldValue.dat"
    d = rows(p)
    if not d:
        return {}
    return {
        "max_abs": max(abs(r[1]) for r in d),
        "final": d[-1][1],
        "integral": trapz(d, 1),
    }


def energy(case):
    b = BASE/case/"postProcessing"/"metal"
    top = rows(b/"metalTopEnergyPower"/"0"/"surfaceFieldValue.dat")
    mold = rows(b/"metalMoldEnergyPower"/"0"/"surfaceFieldValue.dat")
    bd = rows(b/"metalBoundaryEnergyPower"/"0"/"surfaceFieldValue.dat")
    lat = rows(b/"metalLatentHeatPower"/"0"/"volFieldValue.dat")
    hs = rows(b/"metalSensibleEnthalpy"/"0"/"volFieldValue.dat")
    if not all((top, mold, bd, lat, hs)):
        return {}
    out = {
        "E_top_adv_J": trapz(top, 1),
        "E_top_diff_J": trapz(top, 2),
        "E_mold_adv_J": trapz(mold, 1),
        "E_mold_diff_J": trapz(mold, 2),
        "E_boundary_adv_J": trapz(bd, 1),
        "E_boundary_diff_J": trapz(bd, 2),
        "E_boundary_total_J": trapz(bd, 3),
        "E_latent_diagnostic_J": trapz(lat, 1),
        "delta_sensible_H_J": hs[-1][1]-hs[0][1],
        "top_adv_max_abs_W": max(abs(r[1]) for r in top),
    }
    out["closure_diagnostic_J"] = out["delta_sensible_H_J"] + out["E_boundary_total_J"] - out["E_latent_diagnostic_J"]
    return out


def load_profile(case, folder, filename):
    root = BASE/case/"postProcessing"/"metal"/folder
    return {t: rows(d/filename) for t, d in numeric_dirs(root) if rows(d/filename)}


def profile_metrics(a, b, idx):
    if len(a) != len(b) or not a or any(len(r)<=idx for r in a+b):
        return {}
    av = [r[idx] for r in a]
    bv = [r[idx] for r in b]
    e = rmse(av, bv)
    rms_ref = math.sqrt(sum(x*x for x in av)/len(av))
    return {
        "rmse": e,
        "nrmse_rms_pct": 100*e/rms_ref if rms_ref else float("nan"),
        "cosine_similarity": cosine(av, bv),
        "pearson_r": pearson(av, bv),
    }


status_rows = []
case_rows = []
for label, case in CASES.items():
    st = status(case)
    status_rows.append({"label": label, "case": case, **st})
    p = probe(case)
    a = alpha_mean(case)
    ph = top_phi(case)
    en = energy(case)
    case_rows.append({
        "label": label,
        "case": case,
        **st,
        "T_final_K": p[max(p)] if p else float("nan"),
        "alphaL_final": a[max(a)] if a else float("nan"),
        "top_phi_max_abs": ph.get("max_abs", float("nan")),
        "top_phi_final": ph.get("final", float("nan")),
        **en,
    })

with (OUT/"case_status.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(status_rows[0]))
    w.writeheader()
    w.writerows(status_rows)

case_fields = sorted({k for r in case_rows for k in r})
with (OUT/"case_summary.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=case_fields)
    w.writeheader()
    w.writerows(case_rows)

pair_rows = []
profile_rows = []
for name, ref_label, other_label in COMPARISONS:
    ref_case = CASES[ref_label]
    other_case = CASES[other_label]
    tc = compare_series(probe(ref_case), probe(other_case))
    ac = compare_series(alpha_mean(ref_case), alpha_mean(other_case))
    row = {"comparison": name, "reference": ref_case, "other": other_case}
    row.update({"T_"+k: v for k, v in tc.items()})
    row.update({"alphaL_"+k: v for k, v in ac.items()})
    pair_rows.append(row)

    for profile, (folder, filename) in PROFILES.items():
        pa = load_profile(ref_case, folder, filename)
        pb = load_profile(other_case, folder, filename)
        for t in sorted(set(pa) & set(pb)):
            for variable, idx in (("Uy", 2), ("T", 4), ("alphaL", 7)):
                m = profile_metrics(pa[t], pb[t], idx)
                if m:
                    profile_rows.append({
                        "comparison": name,
                        "profile": profile,
                        "time_s": t,
                        "variable": variable,
                        **m,
                    })

pair_fields = sorted({k for r in pair_rows for k in r})
with (OUT/"pair_summary.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=pair_fields)
    w.writeheader()
    w.writerows(pair_rows)

if profile_rows:
    with (OUT/"profile_metrics.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(profile_rows[0]))
        w.writeheader()
        w.writerows(profile_rows)

lines = [
    "# V10/V11 OpenFOAM 14 air-gap analysis",
    "",
    "## Completeness",
    "",
    "| case | latest time [s] | solver End | complete to 10 s |",
    "|---|---:|---:|---:|",
]
for r in status_rows:
    lines.append(f"| {r['case']} | {fmt(r['latest_time_s'])} | {r['log_has_End']} | {r['complete_10s']} |")

lines += [
    "",
    "## Case diagnostics",
    "",
    "| case | final T [K] | final mean alphaL | max |sum(phi) top| | top advective E [J] | mold diffusive E [J] |",
    "|---|---:|---:|---:|---:|---:|",
]
for r in case_rows:
    lines.append(
        f"| {r['case']} | {fmt(r.get('T_final_K'))} | {fmt(r.get('alphaL_final'))} | "
        f"{fmt(r.get('top_phi_max_abs'))} | {fmt(r.get('E_top_adv_J'))} | {fmt(r.get('E_mold_diff_J'))} |"
    )

for name, ref_label, other_label in COMPARISONS:
    r = next(x for x in pair_rows if x["comparison"] == name)
    lines += [
        "",
        f"## {name}",
        "",
        f"- T RMSE: {fmt(r.get('T_rmse'))} K",
        f"- T max absolute difference: {fmt(r.get('T_max_abs'))} K",
        f"- T final difference: {fmt(r.get('T_final_diff'))} K",
        f"- mean alphaL RMSE: {fmt(r.get('alphaL_rmse'))}",
        f"- mean alphaL final difference: {fmt(r.get('alphaL_final_diff'))}",
    ]
    uy = [x for x in profile_rows if x["comparison"] == name and x["variable"] == "Uy"]
    for profile in PROFILES:
        g = [x for x in uy if x["profile"] == profile and math.isfinite(x["nrmse_rms_pct"])]
        if not g:
            continue
        last = max(g, key=lambda x: x["time_s"])
        peak = max(g, key=lambda x: x["nrmse_rms_pct"])
        lines.append(
            f"- {profile} Uy: final NRMSE/RMS {last['nrmse_rms_pct']:.3f}%; "
            f"peak {peak['nrmse_rms_pct']:.3f}% at {peak['time_s']:g} s; "
            f"final cosine similarity {last['cosine_similarity']:.5f}; "
            f"final Pearson r {last['pearson_r']:.5f}"
        )

lines += [
    "",
    "## Interpretation cautions",
    "",
    "- For B, the stored latent diagnostic rho*(-ddt(alphaL))*L is not the exact variable-density solver source L*ddt(rho*alphaL). B-family energy closure is therefore diagnostic-only.",
    "- Cosine similarity and Pearson r are reported separately.",
    "- Small RMSE means numerical similarity; it is not physical validation.",
    "- Do not draw final V10/V11 conclusions unless all four runs reach 10 s and the solver logs end normally.",
    "",
]

(OUT/"summary.md").write_text("\n".join(lines), encoding="utf-8")
print((OUT/"summary.md").read_text())
