#!/usr/bin/env python3
"""
Exhaustive temporal analysis of the vertical velocity component Uy for the
controlled QuickCup cases.

Reads existing sampled profiles only. It never modifies OpenFOAM cases.

Outputs:
  analysis_results/uy_temporal/uy_temporal_metrics.csv
  analysis_results/uy_temporal/uy_temporal_summary.md
"""

from __future__ import annotations

import bisect
import csv
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases_controlled_buoyancy"
OUT = ROOT / "analysis_results" / "uy_temporal"
OUT.mkdir(parents=True, exist_ok=True)

PROFILES = {
    "y20mm": ("horizontalProfiles", "line_y20mm.xy"),
    "y30mm": ("horizontalProfiles", "line_y30mm.xy"),
    "vertical_x20mm": ("verticalProfiles", "line_x20mm.xy"),
}

COMPARISONS = [
    # Fixed numerical sensitivity
    ("B4_vs_B3", "B3_reference", "B4_energy2", "exact"),
    ("B5_vs_B3", "B3_reference", "B5_outer3", "exact"),
    ("B7_vs_B3", "B3_reference", "B7_outer4", "exact"),
    ("C4_vs_C3", "C3_reference", "C4_energy2", "exact"),
    ("C5_vs_C3", "C3_reference", "C5_outer3", "exact"),
    ("C7_vs_C3", "C3_reference", "C7_outer4", "exact"),

    # Adaptive timestep sensitivity: adaptive times define the comparison grid;
    # the fixed reference is linearly interpolated in physical time.
    ("B6_vs_B5", "B5_outer3", "B6_adaptiveDt", "adaptive"),
    ("C6_vs_C5", "C5_outer3", "C6_adaptiveDt", "adaptive"),

    # Physical formulation contrast
    ("C3_vs_B3", "B3_reference", "C3_reference", "exact"),
]

THRESHOLDS = (5.0, 10.0, 25.0, 50.0)


def numeric_dirs(path: Path) -> list[tuple[float, Path]]:
    out = []
    if not path.is_dir():
        return out
    for p in path.iterdir():
        if not p.is_dir():
            continue
        try:
            t = float(p.name)
        except ValueError:
            continue
        out.append((t, p))
    return sorted(out)


def read_uy_file(path: Path) -> tuple[list[float], list[float]]:
    x, uy = [], []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            cols = s.split()
            if len(cols) < 3:
                continue
            x.append(float(cols[0]))
            uy.append(float(cols[2]))  # coordinate, Ux, Uy, Uz, ...
    if not x:
        raise ValueError(f"No numeric profile data in {path}")
    return x, uy


def load_series(case: str, profile_key: str) -> dict[float, tuple[list[float], list[float]]]:
    folder, filename = PROFILES[profile_key]
    root = CASES / case / "postProcessing" / "metal" / folder
    data = {}
    for t, d in numeric_dirs(root):
        p = d / filename
        if p.is_file():
            data[t] = read_uy_file(p)
    return data


def same_grid(a: list[float], b: list[float], tol: float = 1e-10) -> bool:
    return len(a) == len(b) and all(abs(x-y) <= tol for x, y in zip(a, b))


def interp_profile(series: dict[float, tuple[list[float], list[float]]], t: float):
    times = sorted(series)
    if not times or t < times[0] - 1e-12 or t > times[-1] + 1e-12:
        return None, None, None

    # exact/near-exact match
    for tt in times:
        if abs(tt - t) <= 1e-10:
            x, uy = series[tt]
            return x, uy, f"native:{tt:g}"

    i = bisect.bisect_left(times, t)
    if i == 0 or i == len(times):
        return None, None, None
    t0, t1 = times[i-1], times[i]
    x0, y0 = series[t0]
    x1, y1 = series[t1]
    if not same_grid(x0, x1):
        raise ValueError(f"Spatial grids differ during temporal interpolation: {t0} vs {t1}")
    w = (t - t0) / (t1 - t0)
    y = [a + w*(b-a) for a, b in zip(y0, y1)]
    return x0, y, f"interp:{t0:g},{t1:g}"


def metrics(ref: list[float], other: list[float]) -> dict[str, float | int]:
    if len(ref) != len(other):
        raise ValueError("Profile lengths differ")

    n = len(ref)
    diffs = [b-a for a, b in zip(ref, other)]
    rmse = math.sqrt(sum(d*d for d in diffs) / n)
    mae = sum(abs(d) for d in diffs) / n
    max_abs = max(abs(d) for d in diffs)
    ref_rms = math.sqrt(sum(a*a for a in ref) / n)
    ref_mean_abs = sum(abs(a) for a in ref) / n
    other_rms = math.sqrt(sum(b*b for b in other) / n)

    dot = sum(a*b for a, b in zip(ref, other))
    denom = math.sqrt(sum(a*a for a in ref) * sum(b*b for b in other))
    corr = dot / denom if denom > 0 else float("nan")

    sign_diff = sum(
        1 for a, b in zip(ref, other)
        if abs(a) > 1e-8 and abs(b) > 1e-8 and math.copysign(1.0, a) != math.copysign(1.0, b)
    )

    return {
        "n_points": n,
        "rmse": rmse,
        "mae": mae,
        "max_abs_diff": max_abs,
        "ref_rms": ref_rms,
        "other_rms": other_rms,
        "ref_mean_abs": ref_mean_abs,
        "nrmse_rms_pct": 100.0 * rmse / ref_rms if ref_rms > 0 else float("nan"),
        "nrmse_mean_abs_pct": 100.0 * rmse / ref_mean_abs if ref_mean_abs > 0 else float("nan"),
        "corr": corr,
        "sign_diff_points": sign_diff,
        "ref_min": min(ref),
        "ref_max": max(ref),
        "other_min": min(other),
        "other_max": max(other),
    }


def exact_common_times(a: dict, b: dict) -> list[float]:
    bt = sorted(b)
    out = []
    for t in sorted(a):
        if any(abs(t-u) <= 1e-10 for u in bt):
            out.append(t)
    return out


rows = []

# Cache all required case/profile series once.
needed_cases = sorted({c for _, a, b, _ in COMPARISONS for c in (a, b)})
cache = {
    (case, profile): load_series(case, profile)
    for case in needed_cases
    for profile in PROFILES
}

for label, ref_case, other_case, mode in COMPARISONS:
    for profile in PROFILES:
        ref_series = cache[(ref_case, profile)]
        other_series = cache[(other_case, profile)]

        if mode == "exact":
            times = exact_common_times(ref_series, other_series)
        else:
            # Adaptive case defines physical-time comparison samples.
            rtimes = sorted(ref_series)
            times = [
                t for t in sorted(other_series)
                if rtimes and rtimes[0] - 1e-12 <= t <= rtimes[-1] + 1e-12
            ]

        for t in times:
            if mode == "exact":
                xr, yr, ref_source = interp_profile(ref_series, t)
                xo, yo, other_source = interp_profile(other_series, t)
            else:
                xr, yr, ref_source = interp_profile(ref_series, t)
                xo, yo = other_series[t]
                other_source = f"native:{t:g}"

            if xr is None or xo is None:
                continue
            if not same_grid(xr, xo):
                raise ValueError(
                    f"Spatial coordinate mismatch: {label} {profile} t={t}"
                )

            m = metrics(yr, yo)
            rows.append({
                "comparison": label,
                "reference_case": ref_case,
                "other_case": other_case,
                "mode": mode,
                "profile": profile,
                "time_s": t,
                "reference_source": ref_source,
                "other_source": other_source,
                **m,
            })

csv_path = OUT / "uy_temporal_metrics.csv"
fieldnames = list(rows[0].keys()) if rows else []
with csv_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)


def finite(vals):
    return [v for v in vals if isinstance(v, (int, float)) and math.isfinite(v)]


def fmt(v, digits=3):
    if v is None or not math.isfinite(v):
        return "n/a"
    return f"{v:.{digits}f}"


def first_threshold(grp, threshold):
    for r in sorted(grp, key=lambda x: x["time_s"]):
        if math.isfinite(r["nrmse_rms_pct"]) and r["nrmse_rms_pct"] >= threshold:
            return r["time_s"]
    return None


def peak_record(grp, key, largest=True):
    valid = [r for r in grp if math.isfinite(r[key])]
    if not valid:
        return None
    return (max if largest else min)(valid, key=lambda r: r[key])


summary_lines = [
    "# Exhaustive temporal Uy profile analysis",
    "",
    "This analysis reads every stored sampled profile available in the controlled cases.",
    "Fixed-vs-fixed comparisons use exact common physical times. Adaptive-vs-fixed",
    "comparisons use every stored adaptive physical time and linearly interpolate the",
    "fixed reference in physical time. Uy is the second velocity component from the",
    "sampled U vector.",
    "",
]

for label, ref_case, other_case, mode in COMPARISONS:
    summary_lines += [f"## {label}", ""]
    for profile in PROFILES:
        grp = [
            r for r in rows
            if r["comparison"] == label and r["profile"] == profile
        ]
        if not grp:
            summary_lines += [f"### {profile}", "", "No comparable samples.", ""]
            continue

        nrmse = finite([r["nrmse_rms_pct"] for r in grp])
        corrs = finite([r["corr"] for r in grp])
        peak = peak_record(grp, "nrmse_rms_pct", True)
        mincorr = peak_record(grp, "corr", False)
        peak_sign = max(grp, key=lambda r: r["sign_diff_points"])

        summary_lines += [
            f"### {profile}",
            "",
            f"- samples compared: **{len(grp)}**",
            f"- physical-time range: **{min(r['time_s'] for r in grp):g}–{max(r['time_s'] for r in grp):g} s**",
            f"- median NRMSE/RMS(Uy): **{fmt(statistics.median(nrmse))}%**",
            f"- mean NRMSE/RMS(Uy): **{fmt(statistics.fmean(nrmse))}%**",
            f"- peak NRMSE/RMS(Uy): **{fmt(peak['nrmse_rms_pct'])}% at {peak['time_s']:g} s**",
            f"- minimum profile correlation: **{fmt(mincorr['corr'], 4)} at {mincorr['time_s']:g} s**",
            f"- largest sign disagreement: **{peak_sign['sign_diff_points']}/{peak_sign['n_points']} points at {peak_sign['time_s']:g} s**",
        ]
        for th in THRESHOLDS:
            tt = first_threshold(grp, th)
            summary_lines.append(
                f"- first time NRMSE/RMS(Uy) >= {th:g}%: **{tt:g} s**" if tt is not None
                else f"- first time NRMSE/RMS(Uy) >= {th:g}%: not reached"
            )
        summary_lines += [""]

# Compact cross-comparison conclusion section.
summary_lines += [
    "## Interpretation guide",
    "",
    "- NRMSE/RMS(Uy) normalizes profile RMSE by the RMS magnitude of the reference profile.",
    "- Correlation near 1 means the spatial pattern is preserved; values near 0 indicate",
    "  weak shape agreement; negative values indicate an approximately inverted pattern.",
    "- Sign-disagreement counts are only evaluated where both |Uy| > 1e-8 m/s.",
    "- Adaptive comparisons are aligned by physical time, never by timestep index.",
    "",
]

summary_path = OUT / "uy_temporal_summary.md"
summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

print(f"Wrote {csv_path.relative_to(ROOT)} with {len(rows)} comparison rows")
print(f"Wrote {summary_path.relative_to(ROOT)}")
