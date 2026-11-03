#!/usr/bin/env python3
"""Validate a numeric JMatPro CSV and generate a source-traceable CFD *diagnostic*.

Never edits OpenFOAM case inputs or claims J0/experimental validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

PROPERTIES = ("rho_kg_m3", "Cp_J_kgK", "k_W_mK", "fL")


def read_csv(path: Path) -> list[dict[str, float | None]]:
    """Reject ambiguous/nonphysical input rather than silently losing rows."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or reader.fieldnames.count("T_K") != 1:
            raise ValueError("CSV requires exactly one T_K column")
        if len(reader.fieldnames) != len(set(reader.fieldnames)) or None in reader.fieldnames:
            raise ValueError("duplicate or unnamed CSV columns")
        rows = []
        for line, original in enumerate(reader, 2):
            if None in original:
                raise ValueError(f"line {line}: extra/unlabelled CSV fields")
            if all(not (value or "").strip() for value in original.values()):
                continue
            row: dict[str, float | None] = {}
            for key in ("T_K", *PROPERTIES):
                if key not in reader.fieldnames:
                    continue
                raw = original.get(key)
                if raw is None or not raw.strip():
                    if key == "T_K":
                        raise ValueError(f"line {line}: missing T_K")
                    row[key] = None
                    continue
                try:
                    value = float(raw)
                except ValueError as exc:
                    raise ValueError(f"line {line}: nonnumeric {key}") from exc
                if not math.isfinite(value):
                    raise ValueError(f"line {line}: nonfinite {key}")
                if key == "T_K" and value <= 0:
                    raise ValueError(f"line {line}: T_K must exceed absolute zero")
                if key in PROPERTIES[:3] and value <= 0:
                    raise ValueError(f"line {line}: {key} must be positive")
                if key == "fL" and not 0 <= value <= 1:
                    raise ValueError(f"line {line}: fL outside [0,1]")
                row[key] = value
            rows.append(row)
    if not rows:
        raise ValueError("CSV contains no numeric temperature rows")
    rows.sort(key=lambda row: row["T_K"])
    if any(current["T_K"] <= previous["T_K"] for previous, current in zip(rows, rows[1:])):
        raise ValueError("duplicate T_K samples: unique temperatures required")
    return rows


def linear_fit(xs: list[float], ys: list[float]):
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = math.fsum(xs) / len(xs)
    mean_y = math.fsum(ys) / len(ys)
    sxx = math.fsum((x - mean_x)**2 for x in xs)
    if sxx <= 0:
        return None
    slope = math.fsum((x - mean_x)*(y - mean_y) for x, y in zip(xs, ys)) / sxx
    intercept = mean_y - slope*mean_x
    residual = math.fsum((y - (intercept + slope*x))**2 for x, y in zip(xs, ys))
    total = math.fsum((y - mean_y)**2 for y in ys)
    return slope, intercept, (1 - residual/total if total else 1.0)


def interp(rows: list[dict], key: str, temperature: float):
    """Only interpolate inside observed property support; never clamp/extrapolate."""
    points = [(row["T_K"], row[key]) for row in rows if row.get(key) is not None]
    if not points or temperature < points[0][0] or temperature > points[-1][0]:
        return None
    for t, value in points:
        if temperature == t:
            return value
    for (low_t, low_v), (high_t, high_v) in zip(points, points[1:]):
        if low_t < temperature < high_t:
            return low_v + (high_v - low_v)*(temperature - low_t)/(high_t - low_t)
    return None


def of_equilibrium_branch(temperature: float, solidus: float, liquidus: float, alpha1e: float):
    if not (0 < solidus < liquidus and 0 <= alpha1e <= 1):
        raise ValueError("require 0 < Tsol < Tliq and 0 <= alpha1e <= 1")
    if temperature < solidus:
        return 0.0
    if temperature >= liquidus:
        return 1.0
    # At Tsol the enthalpy update can span the eutectic plateau; choose its
    # upper equilibrium branch solely as a diagnostic target.
    return alpha1e + (1-alpha1e)*(temperature-solidus)/(liquidus-solidus)


def stats(values):
    numeric = [value for value in values if value is not None and math.isfinite(value)]
    return (min(numeric), max(numeric), math.fsum(numeric)/len(numeric)) if numeric else None


def report(path: Path, rows: list[dict], args):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    properties = {key: {"samples": sum(row.get(key) is not None for row in rows)} for key in PROPERTIES}
    density_rows = [row for row in rows if row.get("rho_kg_m3") is not None and
                    args.beta_min_T <= row["T_K"] <= args.beta_max_T]
    density = {"status": "NOT_EVALUATED_INSUFFICIENT_RANGE_OR_REFERENCE"}
    reference = interp(rows, "rho_kg_m3", args.rho_ref_T)
    fit = (linear_fit([r["T_K"] for r in density_rows],
                      [r["rho_kg_m3"] for r in density_rows])
           if len(density_rows) >= 2 else None)
    if fit and reference is not None:
        slope, intercept, r2 = fit
        beta = -slope/reference
        if not all(map(math.isfinite, (beta, slope, intercept, r2))):
            raise ValueError("nonfinite fit: inspect the original density export")
        density = {"status": "NUMERIC_DIAGNOSTIC_ONLY", "rho_ref_kg_m3": reference,
                   "rho_ref_temperature_K": args.rho_ref_T, "beta_1_K": beta,
                   "slope_kg_m3_K": slope, "intercept_kg_m3": intercept,
                   "fit_R2": r2, "fit_samples": len(density_rows),
                   "fit_temperature_range_K": [args.beta_min_T, args.beta_max_T]}
    comparison = []
    for row in rows:
        if row.get("fL") is None:
            continue
        value = of_equilibrium_branch(row["T_K"], args.Tsol, args.Tliq, args.alpha1e)
        comparison.append({"T_K": row["T_K"], "fL_JMatPro": row["fL"],
                           "fL_OF_equilibrium_branch": value,
                           "difference_OF_minus_JMatPro": value - row["fL"]})
    phase = {"status": "NOT_EVALUATED_NO_FRACTION_SAMPLES"}
    if comparison:
        differences = [r["difference_OF_minus_JMatPro"] for r in comparison]
        phase = {"status": "EQUILIBRIUM_BRANCH_DIAGNOSTIC_ONLY", "samples": len(comparison),
                 "RMSE": math.sqrt(math.fsum(x*x for x in differences)/len(differences)),
                 "MAE": math.fsum(abs(x) for x in differences)/len(differences),
                 "Tsol_K": args.Tsol, "Tliq_K": args.Tliq, "alpha1e": args.alpha1e,
                 "note": "At Tsol this is the upper eutectic branch, not the iterated solver state."}
    summary = {"schema": "quickcup-jmatpro-property-audit-v2",
               "source_name": path.name, "source_sha256": digest,
               "row_count": len(rows),
               "temperature_range_K": [rows[0]["T_K"], rows[-1]["T_K"]],
               "properties": properties, "density": density, "phase": phase,
               "J0_status": "OPEN_NEEDS_RAW_PROVENANCE_AND_COMPOSITION",
               "experimental_validation": False, "CFD_executed": False,
               "caveat": "Source SHA-256 proves file identity, NOT JMatPro provenance, composition, or physical validity."}
    if args.require_density and density["status"] != "NUMERIC_DIAGNOSTIC_ONLY":
        raise ValueError("required density diagnostic unavailable without in-range rho(T)")
    if args.require_phase and not comparison:
        raise ValueError("required fL(T) comparison unavailable")
    return summary, comparison


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=path.parent, prefix=".jmatpro_", delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--out", type=Path, default=Path("analysis_results/jmatpro_openfoam_audit/processed"))
    parser.add_argument("--rho-ref-T", type=float, default=1473.15)
    parser.add_argument("--beta-min-T", type=float, default=1473.15)
    parser.add_argument("--beta-max-T", type=float, default=1773.15)
    parser.add_argument("--Tsol", type=float, default=1423.0)
    parser.add_argument("--Tliq", type=float, default=1473.0)
    parser.add_argument("--alpha1e", type=float, default=0.8)
    parser.add_argument("--require-density", action="store_true")
    parser.add_argument("--require-phase", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.csv.is_file():
            raise ValueError("source CSV not found")
        if not all(map(math.isfinite, (args.rho_ref_T, args.beta_min_T,
                                      args.beta_max_T, args.Tsol, args.Tliq, args.alpha1e))):
            raise ValueError("all numeric parameters must be finite")
        if args.beta_min_T <= 0 or args.beta_max_T <= args.beta_min_T or args.rho_ref_T <= 0:
            raise ValueError("require 0 < beta-min-T < beta-max-T and rho-ref-T > 0")
        if not (0 < args.Tsol < args.Tliq and 0 <= args.alpha1e <= 1):
            raise ValueError("require 0 < Tsol < Tliq and 0 <= alpha1e <= 1")
        if args.out.resolve() == args.csv.resolve() or args.csv.resolve().is_relative_to(args.out.resolve()):
            raise ValueError("output directory must not contain the source CSV")
        rows = read_csv(args.csv)
        summary, comparison = report(args.csv, rows, args)
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(2, f"JMatPro input rejected: {exc}\n")
    stem = args.csv.stem
    md = [f"# JMatPro → OpenFOAM numeric audit: {stem}", "",
          f"Source SHA-256: `{summary['source_sha256']}`",
          f"Rows: {summary['row_count']} | K: {summary['temperature_range_K']}", "",
          "**J0 OPEN; not experimental validation or OpenFOAM CFD.**", "",
          "Density: " + summary["density"]["status"],
          "Phase: " + summary["phase"]["status"], "",
          "The Tsol value uses the upper eutectic branch, not instantaneous solver alphaL.",
          "Missing source provenance, chemistry, latent heat, and experimental checks remain separate gates.", ""]
    if summary["density"]["status"] == "NUMERIC_DIAGNOSTIC_ONLY":
        md += [f"- rhoRef = {summary['density']['rho_ref_kg_m3']:.10g} kg/m³",
               f"- beta = {summary['density']['beta_1_K']:.10g} 1/K",
               f"- density R² = {summary['density']['fit_R2']:.10g}"]
    if comparison:
        md += [f"- phase RMSE = {summary['phase']['RMSE']:.10g}",
               f"- phase MAE = {summary['phase']['MAE']:.10g}"]
    atomic_write(args.out / f"{stem}_summary.md", "\n".join(md) + "\n")
    atomic_write(args.out / f"{stem}_audit.json", json.dumps(summary, indent=2, allow_nan=False) + "\n")
    if comparison:
        from io import StringIO
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(comparison[0]))
        writer.writeheader()
        writer.writerows(comparison)
        atomic_write(args.out / f"{stem}_fL_comparison.csv", buffer.getvalue())
    print(args.out / f"{stem}_audit.json")
    print("NUMERIC AUDIT ONLY; J0 OPEN; NO CFD/EXPERIMENTAL VALIDATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
