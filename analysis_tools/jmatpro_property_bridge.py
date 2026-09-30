#!/usr/bin/env python3
"""
Bridge JMatPro numeric exports to the QuickCup OpenFOAM validation workflow.

Expected CSV columns (minimum):
    T_K

Optional:
    rho_kg_m3
    Cp_J_kgK
    k_W_mK
    fL

This script does NOT modify any OpenFOAM case.
It produces a reproducible audit summary and processed CSV.
"""

from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for row in rows:
        if not row.get("T_K"):
            continue
        rec = {}
        for key, val in row.items():
            if val is None or str(val).strip() == "":
                rec[key] = None
            else:
                try:
                    rec[key] = float(val)
                except ValueError:
                    rec[key] = val
        out.append(rec)
    out.sort(key=lambda r: r["T_K"])
    return out


def linear_fit(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs)/n
    my = sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs)
    if sxx == 0:
        return None
    slope = sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sxx
    intercept = my - slope*mx
    pred = [intercept+slope*x for x in xs]
    ss_res = sum((y-p)**2 for y,p in zip(ys,pred))
    ss_tot = sum((y-my)**2 for y in ys)
    r2 = 1-ss_res/ss_tot if ss_tot else 1.0
    return slope, intercept, r2


def interp(rows, key, T):
    pts = [(r["T_K"], r.get(key)) for r in rows if isinstance(r.get(key), (int,float))]
    if not pts:
        return None
    if T <= pts[0][0]:
        return pts[0][1]
    if T >= pts[-1][0]:
        return pts[-1][1]
    for (t0,v0),(t1,v1) in zip(pts,pts[1:]):
        if t0 <= T <= t1:
            w = (T-t0)/(t1-t0)
            return v0 + w*(v1-v0)
    return None


def of_equilibrium_branch(T, Tsol, Tliq, alpha1e):
    if T < Tsol:
        return 0.0
    if T >= Tliq:
        return 1.0
    if Tliq <= Tsol:
        return 1.0
    # Upper equilibrium branch implied by the model relation.
    # At Tsol the eutectic plateau makes alpha non-unique in the actual
    # enthalpy iteration; alpha1e is the upper end of that plateau.
    return alpha1e + (1-alpha1e)*(T-Tsol)/(Tliq-Tsol)


def stats(vals):
    vals = [v for v in vals if isinstance(v,(int,float)) and math.isfinite(v)]
    if not vals:
        return None
    return min(vals), max(vals), sum(vals)/len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, default=Path("analysis_results/jmatpro_openfoam_audit/processed"))
    ap.add_argument("--rho-ref-T", type=float, default=1473.15)
    ap.add_argument("--beta-min-T", type=float, default=1473.15)
    ap.add_argument("--beta-max-T", type=float, default=1773.15)
    ap.add_argument("--Tsol", type=float, default=1423.0)
    ap.add_argument("--Tliq", type=float, default=1473.0)
    ap.add_argument("--alpha1e", type=float, default=0.8)
    args = ap.parse_args()

    rows = read_csv(args.csv)
    if not rows:
        raise SystemExit("No numeric rows found.")

    args.out.mkdir(parents=True, exist_ok=True)
    stem = args.csv.stem

    summary = []
    summary.append(f"# JMatPro -> OpenFOAM audit: {stem}")
    summary.append("")
    summary.append(f"Source CSV: {args.csv}")
    summary.append(f"Temperature rows: {len(rows)}")
    summary.append(f"Temperature range: {rows[0]['T_K']:.6g} to {rows[-1]['T_K']:.6g} K")
    summary.append("")

    rho_rows = [r for r in rows
                if isinstance(r.get("rho_kg_m3"),(int,float))
                and args.beta_min_T <= r["T_K"] <= args.beta_max_T]
    if len(rho_rows) >= 2:
        fit = linear_fit([r["T_K"] for r in rho_rows],[r["rho_kg_m3"] for r in rho_rows])
        rho_ref = interp(rows,"rho_kg_m3",args.rho_ref_T)
        if fit and rho_ref:
            slope, intercept, r2 = fit
            beta = -slope/rho_ref
            summary += [
                "## Density -> Boussinesq bridge",
                f"- rhoRef({args.rho_ref_T:g} K) = {rho_ref:.10g} kg/m3",
                f"- fit range = {args.beta_min_T:g} to {args.beta_max_T:g} K",
                f"- drho/dT = {slope:.10g} kg/(m3 K)",
                f"- fit R2 = {r2:.10g}",
                f"- beta = {beta:.10g} 1/K",
                "",
            ]
    else:
        summary += ["## Density -> Boussinesq bridge","- rho(T) data unavailable in requested fit range.",""]

    for key, label, unit in [
        ("Cp_J_kgK","Cp","J/(kg K)"),
        ("k_W_mK","k","W/(m K)"),
        ("rho_kg_m3","rho","kg/m3"),
        ("fL","fL","-"),
    ]:
        st = stats([r.get(key) for r in rows])
        if st:
            summary.append(f"- {label}: min={st[0]:.10g}, max={st[1]:.10g}, mean={st[2]:.10g} {unit}")
    summary.append("")

    comp = []
    if any(isinstance(r.get("fL"),(int,float)) for r in rows):
        for r in rows:
            if not isinstance(r.get("fL"),(int,float)):
                continue
            T = r["T_K"]
            ofa = of_equilibrium_branch(T,args.Tsol,args.Tliq,args.alpha1e)
            comp.append({
                "T_K":T,
                "fL_JMatPro":r["fL"],
                "fL_OF_equilibrium_branch":ofa,
                "difference_OF_minus_JMatPro":ofa-r["fL"],
            })
        rmse = math.sqrt(sum(r["difference_OF_minus_JMatPro"]**2 for r in comp)/len(comp))
        mae = sum(abs(r["difference_OF_minus_JMatPro"]) for r in comp)/len(comp)
        summary += [
            "## Liquid-fraction comparison",
            f"- OpenFOAM audit parameters: Tsol={args.Tsol:g} K, Tliq={args.Tliq:g} K, alpha1e={args.alpha1e:g}",
            f"- samples = {len(comp)}",
            f"- RMSE (equilibrium branch vs JMatPro) = {rmse:.10g}",
            f"- MAE = {mae:.10g}",
            "",
            "Note: alpha1e creates an eutectic plateau at Tsol; the actual enthalpy iteration is not a simple instantaneous algebraic fL(T) law. The exported branch is a diagnostic target relation, not a replacement for the solver state.",
            "",
        ]
        out_csv = args.out/f"{stem}_fL_comparison.csv"
        with out_csv.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(comp[0]))
            w.writeheader()
            w.writerows(comp)

    out_md = args.out/f"{stem}_summary.md"
    out_md.write_text("\n".join(summary),encoding="utf-8")
    print(out_md)
    print("\n".join(summary))


if __name__ == "__main__":
    main()
