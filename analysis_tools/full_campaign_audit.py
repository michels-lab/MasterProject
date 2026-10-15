#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cases_controlled_buoyancy"
OUT = ROOT / "analysis_results" / "full_campaign_audit"
OUT.mkdir(parents=True, exist_ok=True)

CASES = [
    "B3_reference",
    "B4_energy2",
    "B5_airGapOF14",
    "B5_outer3",
    "B6_adaptiveDt",
    "B7_outer4",
    "B8_adaptiveOuter4",
    "B9_airGapOF14",
    "B9_topFixedFlux",
    "B10_airGapOF14",
    "B11_topFixedFlux_airGapOF14",
    "B12_topFixedValue_airGapOF14",
    "B13_prghPressure_airGapOF14",
    "C3_reference",
    "C4_energy2",
    "C5_airGapOF14",
    "C5_outer3",
    "C6_adaptiveDt",
    "C7_outer4",
    "C8_adaptiveOuter4",
    "C9_airGapOF14",
    "C9_topFixedFlux",
    "C10_airGapOF14",
    "C11_topFixedFlux_airGapOF14",
    "C12_topFixedValue_airGapOF14",
    "C13_prghPressure_airGapOF14",
]

BC_PAIRS = [
    ("v3_reference", "B3_reference", "C3_reference"),
    ("v4_energy2", "B4_energy2", "C4_energy2"),
    ("v5_airGapOF14", "B5_airGapOF14", "C5_airGapOF14"),
    ("v5_outer3", "B5_outer3", "C5_outer3"),
    ("v6_adaptiveDt", "B6_adaptiveDt", "C6_adaptiveDt"),
    ("v7_outer4", "B7_outer4", "C7_outer4"),
    ("v8_adaptiveOuter4", "B8_adaptiveOuter4", "C8_adaptiveOuter4"),
    ("v9_airGapOF14", "B9_airGapOF14", "C9_airGapOF14"),
    ("v9_topFixedFlux", "B9_topFixedFlux", "C9_topFixedFlux"),
    ("v10_airGapOF14", "B10_airGapOF14", "C10_airGapOF14"),
    ("v11_topFixedFlux_airGapOF14", "B11_topFixedFlux_airGapOF14", "C11_topFixedFlux_airGapOF14"),
    ("v12_topFixedValue_airGapOF14", "B12_topFixedValue_airGapOF14", "C12_topFixedValue_airGapOF14"),
    ("v13_prghPressure_airGapOF14", "B13_prghPressure_airGapOF14", "C13_prghPressure_airGapOF14"),
]

PROFILE_SPECS = {
    "y10mm": ("horizontalProfiles", "line_y10mm.xy"),
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


def latest_probe_time(case: Path):
    s = scalar_series(case / "postProcessing" / "metal" / "temperatureProbe" / "0" / "T")
    return max(s) if s else float("nan")


def campaign_status():
    path = ROOT / "analysis_results" / "full_campaign_run" / "status.tsv"
    out = {}
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


def log_text(case: Path):
    p = case / "log.foamMultiRun"
    return p.read_text(errors="replace") if p.is_file() else ""


def log_end(case: Path):
    return bool(re.search(r"(?m)^\s*End\s*$", log_text(case)))


def log_available(case: Path):
    return (case / "log.foamMultiRun").is_file()


def log_has_fatal(case: Path):
    txt = log_text(case)
    if not txt:
        return False
    return bool(re.search(
        r"FOAM FATAL(?: IO)? ERROR|Segmentation fault|Killed|Floating point exception \\(core dumped\\)",
        txt,
        re.I,
    ))


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def fmt(x, n=6):
    return "n/a" if not finite(x) else f"{x:.{n}g}"


def all_matching(case: Path, pattern: str):
    return sorted((case / "logs").glob(pattern))


def last_value(path: Path):
    d = rows(path)
    return d[-1][1] if d and len(d[-1]) > 1 else float("nan")


def median(xs):
    xs = sorted(x for x in xs if finite(x))
    if not xs:
        return float("nan")
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else 0.5 * (xs[m - 1] + xs[m])


def trapz(data, col):
    if len(data) < 2:
        return float("nan")
    total = 0.0
    used = 0
    for a, b in zip(data, data[1:]):
        if len(a) > col and len(b) > col:
            total += 0.5 * (a[col] + b[col]) * (b[0] - a[0])
            used += 1
    return total if used else float("nan")


def rmse(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)) / len(a))


def pearson(a, b):
    if not a or len(a) != len(b):
        return float("nan")
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    aa = [x - ma for x in a]
    bb = [x - mb for x in b]
    den = math.sqrt(sum(x*x for x in aa) * sum(y*y for y in bb))
    return sum(x*y for x, y in zip(aa, bb)) / den if den else float("nan")


def compare_series(a, b):
    ts = sorted(set(a) & set(b))
    if not ts:
        return {}
    av = [a[t] for t in ts]
    bv = [b[t] for t in ts]
    return {
        "samples": len(ts),
        "start_s": ts[0],
        "end_s": ts[-1],
        "rmse": rmse(av, bv),
        "max_abs_diff": max(abs(x-y) for x, y in zip(av, bv)),
        "final_ref": av[-1],
        "final_other": bv[-1],
        "final_diff": bv[-1] - av[-1],
        "pearson_r": pearson(av, bv),
    }


def center_probe(case: Path):
    root = case / "postProcessing" / "metal" / "temperatureProbe" / "0"
    return (
        scalar_series(root / "T"),
        scalar_series(root / "phaseChangeSource:alpha1"),
        scalar_series(root / "rho"),
    )


def mean_alpha(case: Path):
    return scalar_series(case / "postProcessing" / "metal" / "metalMeanLiquidFraction" / "0" / "volFieldValue.dat")


def phi_metrics(case: Path):
    d = rows(case / "postProcessing" / "metal" / "metalTopPhiSum" / "0" / "surfaceFieldValue.dat")
    if not d:
        return {
            "top_phi_available": False,
            "top_phi_max_abs_kg_s": float("nan"),
            "top_phi_final_kg_s": float("nan"),
            "top_phi_integral_kg": float("nan"),
        }
    return {
        "top_phi_available": True,
        "top_phi_max_abs_kg_s": max(abs(r[1]) for r in d if len(r) > 1),
        "top_phi_final_kg_s": d[-1][1],
        "top_phi_integral_kg": trapz(d, 1),
    }


def energy_metrics(case: Path):
    root = case / "postProcessing" / "metal"
    top = rows(root / "metalTopEnergyPower" / "0" / "surfaceFieldValue.dat")
    mold = rows(root / "metalMoldEnergyPower" / "0" / "surfaceFieldValue.dat")
    out = {}
    if top:
        out.update({
            "E_top_adv_J": trapz(top, 1),
            "E_top_heat_J": trapz(top, 2),
            "E_top_total_J": trapz(top, 3),
            "top_adv_max_abs_W": max(abs(r[1]) for r in top if len(r) > 1),
        })
    if mold:
        out.update({
            "E_mold_adv_J": trapz(mold, 1),
            "E_mold_heat_J": trapz(mold, 2),
            "E_mold_total_J": trapz(mold, 3),
        })
    return out


def continuity_metrics(case: Path):
    cum = all_matching(case, "contCumulative_*")
    glob = all_matching(case, "contGlobal_*")

    def suffix(p):
        try:
            return int(p.name.rsplit("_", 1)[1])
        except Exception:
            return -1

    gv = []
    for f in glob:
        gv.extend(scalar_series(f).values())
    return {
        "cont_cumulative_final": last_value(max(cum, key=suffix)) if cum else float("nan"),
        "cont_global_max_abs": max((abs(x) for x in gv), default=float("nan")),
    }


def courant_metrics(case: Path):
    vals = []
    for f in all_matching(case, "CourantMax_*"):
        vals.extend(scalar_series(f).values())
    return {
        "max_Co": max(vals) if vals else float("nan"),
        "median_Co_max_series": median(vals),
    }


def pressure_metrics(case: Path):
    p0 = scalar_series(case / "logs" / "p_rgh_0")
    p4 = scalar_series(case / "logs" / "p_rgh_4")
    ts = sorted(set(p0) & set(p4))
    ratios = [p4[t] / p0[t] for t in ts if p0[t] != 0]
    finals = []
    for f in all_matching(case, "p_rghFinalRes_*"):
        finals.extend(scalar_series(f).values())
    return {
        "Rp_outer_median": median(ratios),
        "Rp_outer_gt1_frac": (sum(x > 1 for x in ratios) / len(ratios)) if ratios else float("nan"),
        "p_final_residual_max": max(finals) if finals else float("nan"),
    }


def profile_at(case: Path, folder: str, filename: str, target=None):
    root = case / "postProcessing" / "metal" / folder
    choices = []
    if root.is_dir():
        for d in root.iterdir():
            if not d.is_dir():
                continue
            try:
                t = float(d.name)
            except ValueError:
                continue
            p = d / filename
            if p.is_file():
                choices.append((t, p))
    if not choices:
        return float("nan"), []
    if target is None:
        t, p = max(choices)
    else:
        t, p = min(choices, key=lambda x: abs(x[0] - target))
    return t, rows(p)


def profile_compare(a, b, idx):
    if not a or not b or len(a) != len(b) or any(len(r) <= idx for r in a + b):
        return {}
    av = [r[idx] for r in a]
    bv = [r[idx] for r in b]
    e = rmse(av, bv)
    rms_ref = math.sqrt(sum(x*x for x in av) / len(av))
    return {
        "rmse": e,
        "nrmse_rms_pct": 100 * e / rms_ref if rms_ref else float("nan"),
        "pearson_r": pearson(av, bv),
        "max_abs_diff": max(abs(x-y) for x, y in zip(av, bv)),
    }


case_rows = []
series = {}
profile_inventory = []
status_map = campaign_status()

for name in CASES:
    case = BASE / name
    T, A, R = center_probe(case)
    AM = mean_alpha(case)
    latest = latest_probe_time(case)

    row = {
        "case": name,
        "family": name[0],
        "latest_probe_time_s": latest,
        "log_available": log_available(case),
        "log_has_End": log_end(case),
        "log_has_fatal": log_has_fatal(case),
        "campaign_status": status_map.get(name, "UNKNOWN"),
        "run_complete_10s": finite(latest) and latest >= 9.999
                            and not log_has_fatal(case)
                            and (
                                status_map.get(name) == "COMPLETED"
                                or (status_map.get(name, "UNKNOWN") == "UNKNOWN" and log_end(case))
                            ),
        "T_center_final_K": T[max(T)] if T else float("nan"),
        "alphaL_center_final": A[max(A)] if A else float("nan"),
        "rho_center_final_kg_m3": R[max(R)] if R else float("nan"),
        "alphaL_mean_final": AM[max(AM)] if AM else float("nan"),
    }
    row.update(phi_metrics(case))
    row.update(energy_metrics(case))
    row.update(continuity_metrics(case))
    row.update(courant_metrics(case))
    row.update(pressure_metrics(case))
    case_rows.append(row)
    series[name] = {"T": T, "A": A, "AM": AM}

    for profile, (folder, filename) in PROFILE_SPECS.items():
        t, data = profile_at(case, folder, filename)
        profile_inventory.append({
            "case": name,
            "profile": profile,
            "available": bool(data),
            "latest_time_s": t,
            "points": len(data),
        })

case_fields = sorted({k for r in case_rows for k in r})
with (OUT / "case_metrics.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=case_fields)
    w.writeheader()
    w.writerows(case_rows)

with (OUT / "profile_inventory.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["case", "profile", "available", "latest_time_s", "points"])
    w.writeheader()
    w.writerows(profile_inventory)

pair_rows = []
profile_rows = []
for label, bname, cname in BC_PAIRS:
    rec = {"comparison": label, "B_case": bname, "C_case": cname}
    for key, prefix in (("T", "T"), ("A", "alphaL_center"), ("AM", "alphaL_mean")):
        m = compare_series(series[bname][key], series[cname][key])
        for k, v in m.items():
            rec[f"{prefix}_{k}"] = v
    pair_rows.append(rec)

    for profile, (folder, filename) in PROFILE_SPECS.items():
        tb, pb = profile_at(BASE / bname, folder, filename)
        tc, pc = profile_at(BASE / cname, folder, filename, tb if finite(tb) else None)
        for var, idx in PROFILE_COLS.items():
            m = profile_compare(pb, pc, idx)
            if m:
                profile_rows.append({
                    "comparison": label,
                    "profile": profile,
                    "variable": var,
                    "B_time_s": tb,
                    "C_time_s": tc,
                    **m,
                })

if pair_rows:
    fields = sorted({k for r in pair_rows for k in r})
    with (OUT / "bc_pair_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(pair_rows)

if profile_rows:
    fields = sorted({k for r in profile_rows for k in r})
    with (OUT / "bc_profile_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(profile_rows)

by_case = {r["case"]: r for r in case_rows}
complete = [r["case"] for r in case_rows if r["run_complete_10s"]]
incomplete = [r["case"] for r in case_rows if not r["run_complete_10s"]]
missing_profiles = [r for r in profile_inventory if not r["available"]]

lines = [
    "# Full controlled-buoyancy campaign audit",
    "",
    "**Read-only analysis of the completed 26-case campaign. No solver execution is performed.**",
    "",
    "## Completion",
    "",
    f"- Complete to target time with runner confirmation and no fatal marker: **{len(complete)}/{len(CASES)}**.",
    f"- Incomplete/invalid: **{len(incomplete)}**.",
]
if incomplete:
    lines.append("- Cases requiring inspection: " + ", ".join(incomplete) + ".")
else:
    lines.append("- All 26 cases satisfy the campaign completion criterion.")

lines += [
    "",
    "## Canonical profile availability",
    "",
    f"- Missing profile products: **{len(missing_profiles)}** across y=10, 20, 30 mm and x=20 mm.",
]
if missing_profiles:
    lines.append("- Missing: " + ", ".join(f"{r['case']}:{r['profile']}" for r in missing_profiles) + ".")

lines += [
    "",
    "## Case-level diagnostics",
    "",
    "| case | status.tsv | probe last s | log file | log End | fatal | complete | T final K | mean alphaL final | max Co | cumulative continuity | max abs phi_top kg/s | Eadv top J |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
]
for name in CASES:
    r = by_case[name]
    lines.append(
        f"| {name} | {r['campaign_status']} | {fmt(r['latest_probe_time_s'])} | {r['log_available']} | "
        f"{r['log_has_End']} | {r['log_has_fatal']} | {r['run_complete_10s']} | {fmt(r['T_center_final_K'])} | "
        f"{fmt(r['alphaL_mean_final'])} | {fmt(r['max_Co'])} | {fmt(r['cont_cumulative_final'])} | "
        f"{fmt(r['top_phi_max_abs_kg_s'])} | {fmt(r.get('E_top_adv_J'))} |"
    )

lines += [
    "",
    "## B/C controlled comparisons",
    "",
    "| generation | T RMSE K | T final C-B K | alphaL mean RMSE | alphaL mean final C-B |",
    "|---|---:|---:|---:|---:|",
]
for rec in pair_rows:
    lines.append(
        f"| {rec['comparison']} | {fmt(rec.get('T_rmse'))} | {fmt(rec.get('T_final_diff'))} | "
        f"{fmt(rec.get('alphaL_mean_rmse'))} | {fmt(rec.get('alphaL_mean_final_diff'))} |"
    )

lines += [
    "",
    "## Interpretation guardrails",
    "",
    "- For runner-managed campaigns, completion means the stored temperature probe reaches at least 9.999 s, status.tsv reports COMPLETED, and no fatal marker is detected in log.foamMultiRun when that log exists.",
    "- A missing log.foamMultiRun is reported separately and is not treated as a fatal solver error. If status.tsv is unavailable, log End is used only as a fallback completion signal.",
    "- sum(phi) is a net top-patch mass flux; a near-zero net value does not by itself prove face-wise impermeability.",
    "- The y=10 mm profile is audited explicitly together with y=20 mm, y=30 mm and x=20 mm.",
    "- Numerical agreement is verification evidence, not experimental validation.",
    "- This script does not run blockMesh, foamMultiRun or foamPostProcess.",
    "",
]

(OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
print((OUT / "summary.md").read_text())
