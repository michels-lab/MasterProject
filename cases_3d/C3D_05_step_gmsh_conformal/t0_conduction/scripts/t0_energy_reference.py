#!/usr/bin/env python3
"""Case B T0 closed-system energy benchmark from ACTUAL saved native mesh volumes.

A numerical reference target, NOT a computed CFD result or experimentally
validated model. Assumes two stationary constant-property solids, ideal
contact and zero external heat flux.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def native_volume(log: str) -> float:
    match = re.search(r"\bTotal volume\s*=\s*(" + NUM + r")", log)
    if not match:
        raise ValueError("native checkMesh report missing region Total volume")
    value = float(match.group(1))
    if not math.isfinite(value) or value <= 0:
        raise ValueError("native region volume must be finite and positive")
    if not re.search(r"(?m)^\s*Mesh OK\.\s*$", log):
        raise ValueError("native report does not contain Mesh OK")
    return value


def energy_target(params: dict, volumes: dict[str, float]) -> dict:
    out = {}
    for region in ("metal", "mold"):
        cfg = params[region]
        vol = volumes[region]
        rho, cv, t = [cfg[key] for key in ("rho_kg_m3", "Cv_J_kg_K", "T_initial_K")]
        if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in (vol, rho, cv, t)):
            raise ValueError(region + ": nonpositive/nonfinite target input")
        cap = float(vol) * float(rho) * float(cv)
        out[region] = {
            "volume_m3": vol,
            "thermal_capacity_J_per_K": cap,
            "T_initial_K": t,
            "initial_sensible_energy_relative_to_zero_K_J": cap * t,
        }
    c1, c2 = (out[z]["thermal_capacity_J_per_K"] for z in ("metal", "mold"))
    e0 = sum(out[z]["initial_sensible_energy_relative_to_zero_K_J"] for z in ("metal", "mold"))
    teq = e0 / (c1+c2)
    if not min(out["metal"]["T_initial_K"], out["mold"]["T_initial_K"]) < teq < max(
            out["metal"]["T_initial_K"], out["mold"]["T_initial_K"]):
        raise ValueError("equilibrium not bracketed by initial metal/mold temperatures")
    return {
        "model": "T0_CLOSED_TWO_SOLID_CONSTANT_RHO_CV_PERFECT_CONTACT",
        "regions": out,
        "total_initial_sensible_energy_relative_to_zero_K_J": e0,
        "ideal_closed_system_equilibrium_temperature_K": teq,
        "total_thermal_capacity_J_per_K": c1+c2,
        "initial_hot_to_cold_energy_scale_J": c1 * abs(out["metal"]["T_initial_K"]-teq),
        "energy_closure_observed": False,
        "solver_executed_by_this_script": False,
        "model_physical_validation": False,
        "warning": "Expected equilibrium is a mathematical conservation target only; does not show solver stability, interface flux closure, recalescence, mesh independence or observed QuickCup physics",
    }


def make_report(inputs: Path, source: Path) -> dict:
    data = json.loads(inputs.read_text(encoding="utf-8"))
    volumes, reports = {}, {}
    for region in ("metal", "mold"):
        file = source / f"log.checkMesh.{region}"
        raw = file.read_bytes()
        volumes[region] = native_volume(raw.decode("utf-8", errors="replace"))
        reports[region] = {"filename": str(file), "sha256": hashlib.sha256(raw).hexdigest()}
    report = energy_target(data, volumes)
    report["input_file_sha256"] = hashlib.sha256(inputs.read_bytes()).hexdigest()
    report["native_logs"] = reports
    return report


def write_exclusive(target: Path, report: dict) -> str:
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if target.exists() or target.is_symlink():
        if target.is_file() and target.read_text(encoding="utf-8") == text:
            return "ALREADY_PRESENT_IDENTICAL"
        raise FileExistsError("Preserving prior nonmatching energy report: " + str(target))
    with target.open("x", encoding="utf-8") as writer:
        writer.write(text)
    return "REFERENCE_ENERGY_TARGET_WRITTEN_NO_SOLVER"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    result = make_report(args.inputs, args.source)
    print(write_exclusive(args.out, result), args.out)
    print("Ideal adiabatic equilibrium target (K):",
          round(result["ideal_closed_system_equilibrium_temperature_K"], 5))
    print("NO CFD RUN, NO ENERGY CONSERVATION VALIDATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
