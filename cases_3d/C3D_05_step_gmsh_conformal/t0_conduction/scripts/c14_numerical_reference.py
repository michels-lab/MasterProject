#!/usr/bin/env python3
"""Build a reproducible C14-ARCHIVED numerical-only T0 candidate for Case B.

No JMatPro data are implied. C14 metal Cp is explicitly used as an
incompressible-equivalent Cv hypothesis, k= Cp*mu/Pr is derived, and the
3D experiment is two idealized adiabatic SOLIDS (not C14's fluid+solid CHT).
Never executes OpenFOAM or edits the original case, geometry or C14.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

T0 = Path(__file__).resolve().parents[1]
REPO = T0.parents[2]
C14 = Path("cases_controlled_buoyancy/C14_topFixedFlux_explicitRef")
FILES = {
    "metal": C14 / "constant/metal/materials/castIron",
    "mold": C14 / "constant/mold/materials/silica",
    "metal_T": C14 / "0/metal/T",
    "mold_T": C14 / "0/mold/T",
    "control": C14 / "system/controlDict",
}
PROFILE = "C14_ARCHIVED_NUMERICAL_REFERENCE_NOT_JMATPRO_NOT_PHYSICAL_VALIDATION"
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def clean(text: str) -> str:
    return re.sub(r"//[^\n]*", "", re.sub(r"/\*[\s\S]*?\*/", "", text))


def scalar(text: str, key: str) -> float:
    found = re.findall(r"(?m)^\s*" + re.escape(key) + r"\s+(" + NUM + r")\s*;", text)
    if len(found) != 1:
        raise ValueError(f"{key}: expected exactly one unambiguous source value, got {len(found)}")
    value = float(found[0])
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{key}: must be finite and positive")
    return value


def initial_temperature(text: str) -> float:
    found = re.findall(r"(?m)^\s*internalField\s+uniform\s+(" + NUM + r")\s*;", text)
    if len(found) != 1:
        raise ValueError("expected exactly one uniform initial temperature in archived 0/T")
    value = float(found[0])
    if not math.isfinite(value) or value <= 0:
        raise ValueError("invalid archived initial temperature")
    return value


def require_model(src: str, tags: tuple[str, ...], label: str):
    for token in tags:
        if not re.search(r"\b" + re.escape(token) + r"\s*;", src):
            raise ValueError(f"{label}: archived thermophysical model drifted ({token})")


def get_originals(root: Path):
    contents, hashes = {}, {}
    for key, relative in FILES.items():
        path = root / relative
        raw = path.read_bytes()
        hashes[str(relative)] = hashlib.sha256(raw).hexdigest()
        contents[key] = clean(raw.decode("utf-8"))
    return contents, hashes


def load_preparer():
    source = T0 / "scripts/prepare_t0.py"
    spec = importlib.util.spec_from_file_location("c3d05_prepare_t0_for_numerical_reference", source)
    assert spec is not None and spec.loader is not None
    instance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(instance)
    return instance


def build(root: Path = REPO) -> dict:
    sources, hashes = get_originals(root)
    require_model(sources["metal"], ("heRhoThermo", "hConst", "rhoConst", "sensibleEnthalpy"), "metal")
    require_model(sources["mold"], ("heSolidThermo", "eConst", "constIsoSolid", "sensibleInternalEnergy"), "mold")
    cp = scalar(sources["metal"], "Cp")
    mu = scalar(sources["metal"], "mu")
    pr = scalar(sources["metal"], "Pr")
    derived_k = cp * mu / pr
    if not math.isfinite(derived_k) or derived_k <= 0:
        raise ValueError("invalid conductivity Cp*mu/Pr")
    original_dt = scalar(sources["control"], "deltaT")
    original_end = scalar(sources["control"], "endTime")
    original_write = scalar(sources["control"], "writeInterval")
    if not original_write.is_integer():
        raise ValueError("C14 writeInterval not integer")
    # The short 100-step horizon is an EXPLICIT NUMERICAL SHAKEDOWN, not
    # the full C14 10-s case or a substitute for observed QuickCup cooling.
    steps = 100
    timestep = original_dt
    duration = steps * timestep
    if duration > original_end:
        raise ValueError("numerical diagnostic horizon exceeds original C14")
    out = json.loads((T0 / "T0_INPUTS.json").read_text(encoding="utf-8"))
    def cite(which: str, meaning: str) -> str:
        rel = str(FILES[which])
        return f"C14_VERSIONED_BASELINE:{rel}; sha256={hashes[rel]}; {meaning}"
    out["metal"].update({
        "rho_kg_m3": scalar(sources["metal"], "rho"),
        "Cv_J_kg_K": cp,
        "kappa_W_m_K": derived_k,
        "molWeight_g_mol": scalar(sources["metal"], "molWeight"),
        "T_initial_K": initial_temperature(sources["metal_T"]),
        "source_rho": cite("metal", "C14 rhoConst; archived model, not new JMatPro data"),
        "source_Cv": cite("metal", "Cp approximated as Cv for fixed-volume two-solid numerical trial, NOT a measured Cv"),
        "source_kappa": cite("metal", "k= Cp*mu/Pr in archived C14 metal hConst model, NOT independently measured k"),
        "source_molWeight": cite("metal", "specie bookkeeping convention, not composition"),
        "source_T_initial": cite("metal_T", "archived C14 starting field, not experimental pouring measurement"),
    })
    out["mold"].update({
        "rho_kg_m3": scalar(sources["mold"], "rho"),
        "Cv_J_kg_K": scalar(sources["mold"], "Cv"),
        "kappa_W_m_K": scalar(sources["mold"], "kappa"),
        "molWeight_g_mol": scalar(sources["mold"], "molWeight"),
        "T_initial_K": initial_temperature(sources["mold_T"]),
        "source_rho": cite("mold", "archived silica density, not a measured QuickCup mold"),
        "source_Cv": cite("mold", "archived silica eConst Cv, not measured"),
        "source_kappa": cite("mold", "archived silica k, not measured"),
        "source_molWeight": cite("mold", "specie bookkeeping convention"),
        "source_T_initial": cite("mold_T", "archived C14 mold starting field, not measured"),
    })
    out["simulation"].update({
        "deltaT_s": timestep,
        "endTime_s": duration,
        "writeEverySteps": 20,
        "source_time_choices": cite("control", "use C14 dt but only 100 steps for early numerical shakedown; write every 20; NO physical time calibration"),
    })
    out["reference_profile"] = PROFILE
    out["reference_source_sha256"] = hashes
    out["reference_hypotheses"] = {
        "metal_heat_capacity": "Assume Cv=archived Cp for an idealized fixed-density solid; not thermodynamic validation",
        "metal_conductivity": "k = Cp*mu/Pr from archived C14 fluid formula, not measured k(T)",
        "model": "Two uniform-parameter SOLIDS; adiabatic exterior and perfect interface; NOT C14 fluid+solid nor real casting",
        "time": "100 C14-sized steps for an isolated diagnostic, not a validated cooling history",
    }
    errors = load_preparer().validate(out)
    if errors:
        raise ValueError("generated T0 parameters violate validator: " + "; ".join(errors))
    return out


def validate_reference(cfg: dict, root: Path = REPO) -> list[str]:
    """Reconstruct source values and all assumptions; reject any change in the candidate."""
    if cfg.get("reference_profile") != PROFILE:
        return ["incorrect C14 numerical reference profile"]
    try:
        expected = build(root)
    except (OSError, ValueError) as exc:
        return [f"cannot verify C14 numerical reference: {exc}"]
    return [] if cfg == expected else ["C14 reference has missing, altered or unjustified fields relative to its original SHA sources"]


def write_exclusive(out: Path, cfg: dict) -> str:
    target = out.expanduser().resolve()
    data = json.dumps(cfg, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if target.exists() or target.is_symlink():
        if target.is_file() and target.read_text(encoding="utf-8") == data:
            return "ALREADY_GENERATED_IDENTICAL"
        raise FileExistsError(f"Refusing to overwrite existing input: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as f:
        f.write(data)
    return "CREATED_NUMERICAL_REFERENCE_NOT_PHYSICAL_VALIDATION"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path.home() / "OpenFOAM/C3D05_T0_C14_NUMERICAL_INPUTS.json")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    config = build()
    if args.check_only:
        print("C14_ARCHIVED_REFERENCE_VERIFIED_NO_WRITE_NO_CFD")
        print("METAL rho=", config["metal"]["rho_kg_m3"], "Cv~Cp=", config["metal"]["Cv_J_kg_K"],
              "kappa=", config["metal"]["kappa_W_m_K"])
        print("MOLD rho=", config["mold"]["rho_kg_m3"], "Cv=", config["mold"]["Cv_J_kg_K"],
              "kappa=", config["mold"]["kappa_W_m_K"])
        return 0
    print(write_exclusive(args.out, config), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
