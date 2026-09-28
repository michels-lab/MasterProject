#!/usr/bin/env python3
"""
Pressure-velocity coupling audit for every controlled B/C case.

Permanent review rule:
Every controlled case with foamLog outputs must be evaluated using the complete
p_rgh initial-residual and p_rghFinalRes evolution, not only a final scalar.

Outputs:
  analysis_results/pressure_stagnation/all_pressure_solves.csv
  analysis_results/pressure_stagnation/timestep_pressure_summary.csv
  analysis_results/pressure_stagnation/case_pressure_summary.csv
  analysis_results/pressure_stagnation/summary.md
  analysis_results/pressure_stagnation/<case>_pressure_residuals.png (if matplotlib exists)

Interpretation:
- p_rgh_* = initial residual of each pressure linear solve.
- p_rghFinalRes_* = final residual of the same pressure linear solve.
- linear_contraction = p_rghFinal / p_rghInitial.
- R_p_outer compares the first pressure solve of the final outer corrector
  against the first pressure solve of the first outer corrector.
- A "plateau candidate" is a descriptive heuristic, not a convergence verdict.
  It means the typical pressure residual changes by less than 0.25 decades over
  the final 25% of available samples. The raw curves and residual magnitudes
  must still be inspected.
"""

from __future__ import annotations

import csv
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cases_controlled_buoyancy"
OUT = ROOT / "analysis_results" / "pressure_stagnation"
OUT.mkdir(parents=True, exist_ok=True)

CASE_RE = re.compile(r"^[BC]\d")


def read_series(path: Path):
    data = {}
    if not path.is_file():
        return data
    for raw in path.read_text(errors="replace").splitlines():
        s = raw.strip()
        if not s:
            continue
        parts = s.split()
        if len(parts) < 2:
            continue
        try:
            t = float(parts[0].rstrip("s"))
            v = float(parts[1])
        except ValueError:
            continue
        data[t] = v
    return data


def indexed(logdir: Path, prefix: str):
    arr = []
    for p in logdir.glob(prefix + "_*"):
        m = re.fullmatch(re.escape(prefix) + r"_(\d+)", p.name)
        if m:
            arr.append((int(m.group(1)), p))
    return [p for _, p in sorted(arr)]


def percentile(vals, q):
    vals = sorted(v for v in vals if math.isfinite(v))
    if not vals:
        return float("nan")
    x = (len(vals)-1)*q
    i, j = math.floor(x), math.ceil(x)
    if i == j:
        return vals[i]
    return vals[i] + (vals[j]-vals[i])*(x-i)


def finite_median(vals):
    vals = [v for v in vals if math.isfinite(v)]
    return statistics.median(vals) if vals else float("nan")


def log10safe(v):
    return math.log10(v) if v > 0 and math.isfinite(v) else float("nan")


def plateau_metric(times, vals):
    pairs = [(t, v) for t, v in zip(times, vals) if v > 0 and math.isfinite(v)]
    if len(pairs) < 8:
        return {
            "window_samples": len(pairs),
            "log10_shift_decades": float("nan"),
            "plateau_candidate": False,
        }

    start = max(0, int(math.floor(0.75*len(pairs))))
    tail = pairs[start:]
    if len(tail) < 4:
        tail = pairs

    n = len(tail)
    q = max(1, n//4)
    first = [log10safe(v) for _, v in tail[:q]]
    last = [log10safe(v) for _, v in tail[-q:]]
    first_med = finite_median(first)
    last_med = finite_median(last)
    shift = last_med-first_med if math.isfinite(first_med) and math.isfinite(last_med) else float("nan")

    return {
        "window_samples": n,
        "log10_shift_decades": shift,
        "plateau_candidate": math.isfinite(shift) and abs(shift) < 0.25,
    }


def parse_controls(case_dir: Path):
    fv = case_dir/"system"/"fvSolution"
    text = fv.read_text(errors="replace") if fv.is_file() else ""
    mo = re.search(r"nOuterCorrectors\s+(\d+)\s*;", text)
    me = re.search(r"nEnergyCorrectors\s+(\d+)\s*;", text)

    cd = case_dir/"system"/"controlDict"
    ctext = cd.read_text(errors="replace") if cd.is_file() else ""
    dt = re.search(r"(?m)^\s*deltaT\s+([^;]+);", ctext)
    adj = re.search(r"(?m)^\s*adjustTimeStep\s+([^;]+);", ctext)

    return {
        "nOuterCorrectors": int(mo.group(1)) if mo else 1,
        "nEnergyCorrectors": int(me.group(1)) if me else 1,
        "deltaT": dt.group(1).strip() if dt else "",
        "adjustTimeStep": adj.group(1).strip() if adj else "",
    }


cases = sorted(
    p for p in BASE.iterdir()
    if p.is_dir() and CASE_RE.match(p.name) and (p/"logs").is_dir()
)

all_rows = []
step_rows = []
case_rows = []

for case_dir in cases:
    case = case_dir.name
    logs = case_dir/"logs"
    controls = parse_controls(case_dir)

    initials = [read_series(p) for p in indexed(logs, "p_rgh")]
    finals = [read_series(p) for p in indexed(logs, "p_rghFinalRes")]
    iters = [read_series(p) for p in indexed(logs, "p_rghIters")]

    nsolves = min(len(initials), len(finals))
    if not nsolves:
        continue

    # Use only times available in both initial and final residual for every paired solve.
    time_sets = []
    for i in range(nsolves):
        time_sets.append(set(initials[i]) & set(finals[i]))
    times = sorted(set.intersection(*time_sets)) if time_sets else []

    nouter = controls["nOuterCorrectors"]
    per_outer = nsolves//nouter if nouter and nsolves % nouter == 0 else None

    for step_index, t in enumerate(times):
        init_vals = []
        final_vals = []
        contractions = []

        for solve_index in range(nsolves):
            ri = initials[solve_index][t]
            rf = finals[solve_index][t]
            ctr = rf/ri if ri else float("nan")
            nit = iters[solve_index].get(t, float("nan")) if solve_index < len(iters) else float("nan")

            outer_index = solve_index//per_outer if per_outer else -1
            within_outer = solve_index % per_outer if per_outer else solve_index

            all_rows.append({
                "case": case,
                "time_s": t,
                "step_index": step_index,
                "solve_index": solve_index,
                "outer_index": outer_index,
                "solve_within_outer": within_outer,
                "p_rgh_initial": ri,
                "p_rgh_final": rf,
                "linear_contraction_final_over_initial": ctr,
                "linear_iterations": nit,
                **controls,
            })

            init_vals.append(ri)
            final_vals.append(rf)
            contractions.append(ctr)

        rp_outer = float("nan")
        if per_outer:
            first = init_vals[0]
            last_outer_first = init_vals[(nouter-1)*per_outer]
            rp_outer = last_outer_first/first if first else float("nan")

        step_rows.append({
            "case": case,
            "time_s": t,
            "step_index": step_index,
            "n_pressure_solves": nsolves,
            "median_p_rgh_initial": finite_median(init_vals),
            "median_p_rgh_final": finite_median(final_vals),
            "max_p_rgh_initial": max(init_vals),
            "max_p_rgh_final": max(final_vals),
            "median_linear_contraction": finite_median(contractions),
            "R_p_outer": rp_outer,
            **controls,
        })

    grp = [r for r in step_rows if r["case"] == case]
    ti = [r["time_s"] for r in grp]
    vi = [r["median_p_rgh_initial"] for r in grp]
    vf = [r["median_p_rgh_final"] for r in grp]
    pi = plateau_metric(ti, vi)
    pf = plateau_metric(ti, vf)

    contractions = [r["median_linear_contraction"] for r in grp]
    rpvals = [r["R_p_outer"] for r in grp if math.isfinite(r["R_p_outer"])]

    case_rows.append({
        "case": case,
        **controls,
        "n_pressure_solves_per_timestep": nsolves,
        "n_timesteps_compared": len(grp),
        "t_start_s": ti[0] if ti else float("nan"),
        "t_end_s": ti[-1] if ti else float("nan"),
        "median_p_rgh_initial": finite_median(vi),
        "p95_p_rgh_initial": percentile(vi, 0.95),
        "median_p_rgh_final": finite_median(vf),
        "p95_p_rgh_final": percentile(vf, 0.95),
        "median_linear_contraction": finite_median(contractions),
        "p95_linear_contraction": percentile(contractions, 0.95),
        "median_R_p_outer": finite_median(rpvals),
        "p95_R_p_outer": percentile(rpvals, 0.95),
        "fraction_R_p_outer_gt1": (
            sum(v > 1 for v in rpvals)/len(rpvals) if rpvals else float("nan")
        ),
        "initial_tail_shift_decades": pi["log10_shift_decades"],
        "final_tail_shift_decades": pf["log10_shift_decades"],
        "initial_plateau_candidate": pi["plateau_candidate"],
        "final_plateau_candidate": pf["plateau_candidate"],
    })


def write_csv(path, data):
    if not data:
        path.write_text("")
        return
    fields = list(data[0].keys())
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(data)


write_csv(OUT/"all_pressure_solves.csv", all_rows)
write_csv(OUT/"timestep_pressure_summary.csv", step_rows)
write_csv(OUT/"case_pressure_summary.csv", case_rows)

# Optional figures. The CSV outputs remain authoritative if matplotlib is unavailable.
try:
    import matplotlib.pyplot as plt

    for case_dir in cases:
        case = case_dir.name
        grp = [r for r in step_rows if r["case"] == case]
        if not grp:
            continue

        t = [r["time_s"] for r in grp]
        ini = [r["median_p_rgh_initial"] for r in grp]
        fin = [r["median_p_rgh_final"] for r in grp]

        fig, ax = plt.subplots()
        ax.semilogy(t, ini, label="median p_rgh initial")
        ax.semilogy(t, fin, label="median p_rgh final")
        ax.set_xlabel("Physical time [s]")
        ax.set_ylabel("Pressure residual")
        ax.set_title(case + " - p_rgh residual evolution vs physical time")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT/(case+"_pressure_residuals_vs_time.png"), dpi=180)
        plt.close(fig)

        fig, ax = plt.subplots()
        step = [r["step_index"] for r in grp]
        ax.semilogy(step, ini, label="median p_rgh initial")
        ax.semilogy(step, fin, label="median p_rgh final")
        ax.set_xlabel("Stored timestep index")
        ax.set_ylabel("Pressure residual")
        ax.set_title(case + " - p_rgh residual evolution vs timestep index")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT/(case+"_pressure_residuals_vs_step.png"), dpi=180)
        plt.close(fig)
except Exception as exc:
    print("Plot generation skipped:", exc)

lines = [
    "# Pressure residual / coupling stagnation audit",
    "",
    "This is a permanent case-review rule for the controlled B/C family.",
    "Every case with foamLog pressure outputs is reviewed using both p_rgh initial",
    "residuals and p_rghFinalRes, over physical time and timestep index.",
    "",
    "A plateau flag is only a screening heuristic: the median residual changes by",
    "less than 0.25 log10 decades over the final 25% of available samples. It is",
    "not by itself proof of acceptable or unacceptable convergence.",
    "",
    "| case | dt | adjust | outer | p solves/step | median p init | median p final | median final/init | median Rp outer | init plateau | final plateau |",
    "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
]

for r in case_rows:
    def f(v, n=4):
        return "n/a" if not isinstance(v, (int, float)) or not math.isfinite(v) else f"{v:.{n}g}"
    lines.append(
        f"| {r['case']} | {r['deltaT']} | {r['adjustTimeStep']} | "
        f"{r['nOuterCorrectors']} | {r['n_pressure_solves_per_timestep']} | "
        f"{f(r['median_p_rgh_initial'])} | {f(r['median_p_rgh_final'])} | "
        f"{f(r['median_linear_contraction'])} | {f(r['median_R_p_outer'])} | "
        f"{r['initial_plateau_candidate']} | {r['final_plateau_candidate']} |"
    )

lines += [
    "",
    "## Required interpretation for every new case",
    "",
    "1. Inspect p_rgh initial residual evolution versus physical time.",
    "2. Inspect p_rghFinalRes evolution versus physical time.",
    "3. Inspect the same two quantities versus timestep index.",
    "4. Evaluate final/initial residual contraction for each pressure solve.",
    "5. Evaluate R_p_outer to determine whether the pressure-velocity outer loop contracts.",
    "6. Compare continuity error, Courant number, computational cost, and physical fields before declaring a numerical configuration preferable.",
    "7. A small timestep is not considered beneficial merely because it is smaller; check whether residuals stagnate while cost increases.",
    "",
]

(OUT/"summary.md").write_text("\n".join(lines)+"\n")
print((OUT/"summary.md").read_text())
