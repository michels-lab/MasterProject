#!/usr/bin/env python3
"""FS-C06: isolated Foundation14 VoFSolidificationMelting numerical smoke.

This is NOT a shrinkage/feeding solver: no rho_solid != rho_liquid, no
volume-loss continuity, no graphite expansion and no mass/enthalpy closure.
The only optional CFD operation is TWO 1e-7 s steps in a NEW copy.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import FLUID_CELLS
from run_fs_c05_native_smoke import (
    preflight as preflight_c05,
    short_control, validate_run_log, MAX_NATIVE_SECONDS,
)
from stage_fs_c05_vof_cht import ensure_compressible_kepsilon_divergence
from stage_fs_c04_initial_alpha import digest

PREFIX = "FS_C06_VOF_SOLID_SMOKE_"
C14_FVMODELS = Path("cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant/metal/fvModels")
MODEL_FIELD = "alpha.metal.solid"
TIMES = ("1e-07", "2e-07")


def read_c14_reference(project: Path) -> dict:
    """Trace C14 numbers; do not claim JMatPro or transfer alpha1e."""
    source = project / C14_FVMODELS
    require(source.is_file() and not source.is_symlink(), "C14 model source absent")
    text = source.read_text()
    require(re.search(r"\btype\s+solidificationMeltingSource\s*;", text),
            "C14 reference fvModel changed")
    values = {}
    for field in ("Tsol", "Tliq", "L", "relax", "Cu", "q"):
        matches = re.findall(
            rf"(?m)^\s*{field}\s+([0-9.+\-eE]+)\s*;", text
        )
        require(len(matches) == 1, "C14 coefficient missing or duplicated: " + field)
        values[field] = float(matches[0])
        require(math.isfinite(values[field]), "nonfinite C14 coefficient " + field)
    require(0 < values["Tsol"] < values["Tliq"]
            and values["L"] > 0 and 0 < values["relax"] <= 1
            and values["Cu"] > 0 and values["q"] > 0,
            "invalid C14 numeric reference")
    return {"values": values, "original_sha256": digest(source),
            "relative_source": str(C14_FVMODELS),
            "alpha1e_transferred": False,
            "physical_calibration_validated": False}


def model_text(reference: dict) -> str:
    v = reference["values"]
    def number(x: float) -> str:
        return format(x, ".12g")
    return ("""/* FS-C06 numerical Foundation14 COMPATIBILITY candidate only.
 * alpha.metal = VoF metal/air fraction.
 * alpha.metal.solid = absolute solid-metal fraction (0 <= solid <= metal).
 * THIS MODEL DOES NOT CREATE SHRINKAGE OR FEEDING.
 * C14 coefficients are numerical references, not measured material data.
 */
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    location "constant/fluid";
    object fvModels;
}
FS_C06_vof_phase_change
{
    type VoFSolidificationMelting;
    cellZone all;
    alphaSolidT table
    (
"""
            + "        (" + number(v["Tsol"]) + " 1)\n"
            + "        (" + number(v["Tliq"]) + " 0)\n"
            + "    );\n"
            + "    L " + number(v["L"]) + ";\n"
            + "    relax " + number(v["relax"]) + ";\n"
            + "    Cu " + number(v["Cu"]) + ";\n"
            + "    q " + number(v["q"]) + ";\n"
            + "}\n")


def check_solid_fraction(metal: list[float], solid: list[float]) -> dict:
    require(len(metal) == len(solid) == FLUID_CELLS,
            "VOF/solid cell count mismatch")
    require(all(math.isfinite(v) for v in metal + solid),
            "nonfinite VOF or solid fraction")
    errors = sum(1 for a, s in zip(metal, solid)
                 if a < -1e-8 or a > 1+1e-8 or s < -1e-8 or s > a+1e-8)
    require(errors == 0, "solid fraction exceeds metal VOF or is negative")
    return {"cells": len(solid), "solid_fraction_min": min(solid),
            "solid_fraction_max": max(solid), "solid_fraction_sum": sum(solid),
            "solid_fraction_within_metal_vof": True,
            "mass_shrinkage_or_feeding_validated": False}


def read_native_fraction(case: Path) -> dict:
    snapshots = []
    for time in TIMES:
        fluid = case / time / "fluid"
        # OpenFOAM uses the native time directory as written; no invented data.
        if not fluid.is_dir():
            matches = [p / "fluid" for p in case.iterdir()
                       if p.is_dir() and _same_time(p.name, float(time))]
            require(len(matches) == 1, "native time folder missing or ambiguous " + time)
            fluid = matches[0]
        metal = read_alpha(fluid / "alpha.metal", expected_cells=FLUID_CELLS)
        solid = read_alpha(fluid / MODEL_FIELD, expected_cells=FLUID_CELLS)
        snapshots.append({"time_s": float(time), **check_solid_fraction(metal, solid),
                          "alpha_metal_sha256": digest(fluid / "alpha.metal"),
                          "alpha_metal_solid_sha256": digest(fluid / MODEL_FIELD)})
    return {"snapshots": snapshots, "native_solid_fraction_observed": True,
            "physical_solidification_validated": False}


def _same_time(name: str, value: float) -> bool:
    try:
        return math.isclose(float(name), value, rel_tol=1e-9, abs_tol=1e-16)
    except ValueError:
        return False


def stage(source: Path, dest: Path, project: Path, native: bool = False) -> dict:
    source, dest, project = (p.expanduser().resolve()
                              for p in (source, dest, project))
    require(dest.name.startswith(PREFIX) and not dest.exists()
            and not dest.is_symlink(), "FS-C06 requires a NEW isolated destination")
    require(source != dest and dest not in source.parents
            and source not in dest.parents, "source and output must not overlap")
    evidence = preflight_c05(source)
    reference = read_c14_reference(project)
    original_models = source / "constant/fluid/fvModels"
    require(original_models.is_file() and not original_models.is_symlink()
            and not re.search(r"\b(?:VoFSolidificationMelting|solidificationMeltingSource)\b",
                              original_models.read_text()),
            "FS-C05 already contains another solidification source")
    if native:
        require(os.environ.get("WM_PROJECT_VERSION") == "14",
                "native mode requires Foundation OpenFOAM 14")
        require(shutil.which("foamMultiRun") is not None,
                "foamMultiRun executable not available")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, symlinks=False)
    control = dest / "system/controlDict"
    control.write_text(short_control(control.read_text()))
    schemes = dest / "system/fluid/fvSchemes"
    modified, added = ensure_compressible_kepsilon_divergence(schemes.read_text())
    schemes.write_text(modified)
    candidate = dest / "constant/fluid/fvModels"
    candidate.write_text(model_text(reference))
    result = {
        "schema": "masterproject-fs-c06-vof-phase-change-smoke-v1",
        "status": "FS_C06_STAGED_NO_CFD",
        "source": evidence, "output": str(dest),
        "foundation14_vof_model": "VoFSolidificationMelting",
        "model_field_expected": MODEL_FIELD,
        "C14_numerical_reference_NOT_physical_calibration": reference,
        "control_sha256": digest(control),
        "fvSchemes_sha256": digest(schemes),
        "fvModels_sha256": digest(candidate),
        "rhoPhi_schemes_added_in_copy": added,
        "native_cfd_executed": False,
        "model_loaded_native": False,
        "solid_fraction_fields_measured": False,
        "phase_density_change_implemented": False,
        "volumetric_shrinkage_implemented": False,
        "feeding_implemented": False,
        "mass_energy_validated": False,
    }
    report = dest / "FS_C06_REPORT.json"
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if not native:
        return result
    cmd = ["foamMultiRun", "-case", str(dest)]
    log = dest / "log.FS_C06_foamMultiRun"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           errors="replace", check=False,
                           timeout=MAX_NATIVE_SECONDS)
        log.write_text("COMMAND: " + " ".join(cmd) + "\nEXIT: " +
                       str(p.returncode) + "\n" + p.stdout + "\n" + p.stderr)
        result["native_cfd_executed"] = True
        require(p.returncode == 0, "native foamMultiRun failed")
        result["native_solver_log"] = validate_run_log(p.stdout + "\n" + p.stderr)
        fraction = read_native_fraction(dest)
        result["solid_fraction_fields_measured"] = True
        result["model_loaded_native"] = True
        result["native_fraction_diagnostics"] = fraction
        result["status"] = "FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE"
    except (OSError, ValueError, KeyError, TypeError,
            subprocess.TimeoutExpired) as exc:
        result["status"] = "FS_C06_NATIVE_BLOCKED_PRESERVE_LOGS"
        result["failure"] = str(exc)
        result["native_log_sha256"] = digest(log) if log.is_file() else None
        report.write_text(json.dumps(result, indent=2) + "\n")
        raise
    result["native_log_sha256"] = digest(log)
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--native", action="store_true",
                        help="two-step actual Foundation14 solver on NEW copy only")
    a = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    out = a.out or (Path.home() / "OpenFOAM" / "FS_C06_RUNS" /
                    (PREFIX + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                     + "_" + uuid.uuid4().hex[:8]))
    try:
        r = stage(a.source, out, root, a.native)
        print("FS-C06:", r["status"])
        print("ISOLATED CASE:", r["output"])
        print("NO PHYSICAL SHRINKAGE/FEEDING OR GLOBAL MASS/ENERGY CLOSURE.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("FS-C06 BLOCKED:", exc, file=sys.stderr)
        print("ISOLATED EVIDENCE:", out, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
