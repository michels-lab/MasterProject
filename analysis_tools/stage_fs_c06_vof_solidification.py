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
from audit_fs_c02_local import read_alpha, read_temperature
from audit_fs_c04_split_cells import FLUID_CELLS, read_mesh, cell_volume_m3
from run_fs_c05_native_smoke import (
    preflight as preflight_c05,
    short_control, validate_run_log, MAX_NATIVE_SECONDS,
)
from stage_fs_c05_vof_cht import ensure_compressible_kepsilon_divergence
from stage_fs_c04_initial_alpha import digest

PREFIX = "FS_C06_VOF_SOLID_SMOKE_"
C14_FVMODELS = Path("cases_controlled_buoyancy/C14_topFixedFlux_explicitRef/constant/metal/fvModels")
NATIVE_FVMODELS = Path("freesurface/FS-C06_vof_solidification/native/constant/fluid/fvModels")
NATIVE_CONTROL = Path("freesurface/FS-C06_vof_solidification/native/system/controlDict")
NATIVE_FUNCTIONS = Path("freesurface/FS-C06_vof_solidification/native/system/functions")
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


def model_text(reference: dict, inherited_models: str) -> str:
    """Add the native phase-change model without deleting FS-C05 physics.

    The accepted C05 case has compressible::VoFTurbulenceDamping under RAS
    kEpsilon. Replacing the whole fvModels file silently disabled that source.
    Keep the original dictionary intact and append exactly one new fvModel.
    """
    require(isinstance(inherited_models, str)
            and len(re.findall(r"(?m)^\s*FoamFile\s*$", inherited_models)) == 1
            and re.search(r"\bobject\s+fvModels\s*;", inherited_models)
            and re.search(r'\blocation\s+"constant/fluid"\s*;',
                          inherited_models),
            "FS-C05 inherited fvModels header/region is invalid")
    require(len(re.findall(r"(?m)^\s*turbulenceDamping\s*$",
                           inherited_models)) == 1
            and re.search(
                r"\bturbulenceDamping\s*\{[^{}]*"
                r"\btype\s+compressible::VoFTurbulenceDamping\s*;[^{}]*\}",
                inherited_models, re.S),
            "FS-C05 VoF turbulence damping must remain active")
    require(not re.search(
        r"\b(?:VoFSolidificationMelting|solidificationMeltingSource|FS_C06_vof_phase_change)\b",
        inherited_models),
        "FS-C05 already has a phase-change model; refusing duplicate sources")
    v = reference["values"]
    def number(x: float) -> str:
        return format(x, ".12g")
    added = ("""/* FS-C06 numerical Foundation14 COMPATIBILITY candidate only.
 * Retain inherited compressible::VoFTurbulenceDamping / kEpsilon.
 * alpha.metal = VoF metal/air fraction.
 * alpha.metal.solid = absolute solid-metal fraction (0 <= solid <= metal).
 * THIS MODEL DOES NOT CREATE SHRINKAGE OR FEEDING.
 * C14 coefficients are numerical references, not measured material data.
 */
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
    return inherited_models.rstrip("\n") + "\n\n" + added


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


def phase_volume_metrics(
    volumes: list[float],
    metal: list[float],
    solid: list[float],
    temperature: list[float],
    liquidus_K: float,
) -> dict:
    """Measure cell-volume-weighted *geometry*, not shrinkage or mass.

    alpha.metal.solid is absolute solid metal per computational cell,
    not the metal-conditional solid fraction. No rho_s/rho_l or boundary
    flux is supplied, so mass conservation/feeding cannot be inferred.
    """
    require(len(volumes) == len(metal) == len(solid) == len(temperature)
            and len(volumes) > 0, "phase-volume field lengths differ")
    require(math.isfinite(liquidus_K) and liquidus_K > 0,
            "invalid liquidus screening reference")
    require(all(math.isfinite(v) and v > 0 for v in volumes),
            "nonpositive native mesh cell volume")
    require(all(math.isfinite(t) and t > 0 for t in temperature),
            "invalid absolute temperature")
    require(all(math.isfinite(a) and math.isfinite(s)
                and -1e-8 <= a <= 1+1e-8
                and -1e-8 <= s <= a+1e-8
                for a, s in zip(metal, solid)),
            "invalid VOF / absolute-solid phase allocation")
    # The small tolerance is a numerical admission check, not a license to
    # integrate negative phase volumes. Reject any physically negative
    # un-clipped inventory instead of silently fabricating solid or liquid.
    require(all(0 <= a <= 1 and 0 <= s <= a for a, s in zip(metal, solid)),
            "phase-volume integration requires strict 0<=solid<=metal<=1")
    V_metal = math.fsum(v*a for v, a in zip(volumes, metal))
    V_solid = math.fsum(v*s for v, s in zip(volumes, solid))
    V_liquid = math.fsum(v*(a-s)
                         for v, a, s in zip(volumes, metal, solid))
    require(V_metal > 0 and V_liquid >= 0 and V_solid >= 0,
            "metallic phase volume absent or unphysical")
    V_metal_below_liquidus = math.fsum(
        v*a for v, a, t in zip(volumes, metal, temperature)
        if t <= liquidus_K
    )
    return {
        "metal_vof_volume_m3": V_metal,
        "metal_solid_volume_m3": V_solid,
        "metal_liquid_volume_m3": V_liquid,
        "metal_solid_fraction_conditional_volume_weighted": V_solid/V_metal,
        "metal_T_mean_K_alpha_volume_weighted": math.fsum(
            v*a*t for v, a, t in zip(volumes, metal, temperature)
        )/V_metal,
        "metal_vof_volume_below_C14_liquidus_m3": V_metal_below_liquidus,
        "metal_vof_fraction_below_C14_liquidus": V_metal_below_liquidus/V_metal,
        "cell_volume_weighted_not_cell_sum": True,
        "C14_temperature_is_screening_not_JMatPro_calibration": True,
        "rho_liquid_and_rho_solid_verified": False,
        "metal_mass_conservation_verified": False,
        "open_boundary_mass_flux_verified": False,
        "volumetric_shrinkage_or_feeding_verified": False,
    }


def read_native_phase_scalar(path: Path, field_name: str,
                             expected_cells: int = FLUID_CELLS) -> list[float]:
    """Strictly decode native metal-phase scalar data, without object renaming.

    The legacy read_alpha() and read_temperature() validate different names.
    Foundation14 writes alpha.metal.solid and T.metal as distinct objects.
    """
    require(field_name in (MODEL_FIELD, "T.metal"),
            "unsupported metal-phase object name")
    require(expected_cells > 0, "invalid native solid field cell count")
    require(path.is_file() and not path.is_symlink(),
            "missing native phase scalar field")
    raw = path.read_text(encoding="utf-8", errors="strict")
    require(re.search(r"\bformat\s+ascii\s*;", raw[:1000]) is not None,
            "native phase scalar must be ASCII")
    require(re.search(r"\bclass\s+volScalarField\s*;", raw[:1000]) is not None
            and re.search(r"\bobject\s+" + re.escape(field_name) + r"\s*;", raw[:1000]) is not None,
            "native field must be volScalarField object alpha.metal.solid")
    internal = raw.split("boundaryField", 1)[0]
    nonuniform = re.search(
        r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",
        internal, re.S
    )
    if nonuniform:
        require(int(nonuniform.group(1)) == expected_cells,
                "native solid field cell count does not match fluid mesh")
        try:
            values = [float(x) for x in nonuniform.group(2).split()]
        except ValueError as exc:
            raise ValueError("FS-C06: malformed native solid values") from exc
        require(len(values) == expected_cells,
                "native solid field values disagree with declared count")
    else:
        uniform = re.search(
            r"internalField\s+uniform\s+([-+0-9.eE]+)\s*;", internal
        )
        require(uniform is not None,
                "missing or unsupported native solid internalField")
        values = [float(uniform.group(1))] * expected_cells
    require(all(math.isfinite(x) for x in values),
            "nonfinite native solid fraction")
    return values



def read_native_solid_fraction(path: Path, expected_cells: int = FLUID_CELLS) -> list[float]:
    """Read the separate AUTO_WRITE alpha.metal.solid object from Foundation14."""
    return read_native_phase_scalar(path, MODEL_FIELD, expected_cells)


def read_native_metal_temperature(path: Path,
                                  expected_cells: int = FLUID_CELLS) -> list[float]:
    """Metal phase temperature actually used by VoFSolidificationMelting::correct."""
    values = read_native_phase_scalar(path, "T.metal", expected_cells)
    require(all(t > 0 for t in values), "metal phase temperature is not Kelvin")
    return values


def read_native_fraction(case: Path, liquidus_K: float) -> dict:
    mesh = read_mesh(case / "constant/fluid/polyMesh", FLUID_CELLS)
    cell_volumes = [cell_volume_m3(mesh, i) for i in range(FLUID_CELLS)]
    initial_alpha = read_alpha(case / "0/fluid/alpha.metal", expected_cells=FLUID_CELLS)
    initial_vof_volume_m3 = math.fsum(v*a for v, a in zip(cell_volumes, initial_alpha))
    require(initial_vof_volume_m3 > 0, "initial metal volume absent")
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
        solid = read_native_solid_fraction(fluid / MODEL_FIELD, expected_cells=FLUID_CELLS)
        T = read_native_metal_temperature(fluid / "T.metal", expected_cells=FLUID_CELLS)
        phase = phase_volume_metrics(cell_volumes, metal, solid, T, liquidus_K)
        snapshots.append({"time_s": float(time), **check_solid_fraction(metal, solid),
                          **phase,
                          "metal_vof_relative_volume_change_from_t0":
                          (phase["metal_vof_volume_m3"]-initial_vof_volume_m3)/initial_vof_volume_m3,
                          "alpha_metal_sha256": digest(fluid / "alpha.metal"),
                          "alpha_metal_solid_sha256": digest(fluid / MODEL_FIELD),
                          "temperature_sha256": digest(fluid / "T.metal"),
                           "temperature_field_for_solidification": "T.metal"})
    return {"snapshots": snapshots, "native_solid_fraction_observed": True,
            "initial_metal_vof_volume_m3": initial_vof_volume_m3,
            "volumes_from_native_fluid_mesh": True,
            "physical_solidification_validated": False,
            "metal_mass_balance_validated": False,
            "shrinkage_or_feeding_validated": False}


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
    original_short_control = short_control(control.read_text())
    # OPENFOAM NATIVE DICTIONARY owns solver selection and volume monitors.
    native_control_path = project / NATIVE_CONTROL
    require(native_control_path.is_file() and not native_control_path.is_symlink(),
            "tracked Foundation14 controlDict missing")
    native_control_text = native_control_path.read_text(encoding="utf-8")
    # OpenFOAM Foundation14 reads function objects from system/functions,
    # not from an old functions sub-dictionary in controlDict.
    require(native_control_text.strip() == original_short_control.strip(),
            "native OpenFOAM controlDict drifted from accepted FS-C05 solver setup")
    require(re.search(r"(?m)^\\s*functions\\s*$", native_control_text) is None,
            "legacy functions subdictionary in controlDict is not supported")
    native_functions_path = project / NATIVE_FUNCTIONS
    require(native_functions_path.is_file() and not native_functions_path.is_symlink(),
            "Foundation14 system/functions source absent")
    native_functions_text = native_functions_path.read_text(encoding="utf-8")
    require("object      functions;" in native_functions_text
            and 'location    "system";' in native_functions_text
            and native_functions_text.count("// FS-C06_FOUNDATION14_FUNCTION_OBJECTS") == 1
            and not re.search(r"(?m)^\\s*functions\\s*\\{", native_functions_text),
            "native OpenFOAM system/functions header/body invalid")
    for field in ("alpha.metal", "alpha.metal.solid"):
        require(re.search(r"\bfields\s*\(\s*" + re.escape(field) + r"\s*\)\s*;",
                          native_functions_text) is not None,
                "native OpenFOAM volume monitor absent: " + field)
    require(native_functions_text.count("type          volFieldValue;") == 3
            and native_functions_text.count("type          surfaceFieldValue;") == 5
            and native_functions_text.count("type          wallHeatFlux;") == 2
            and native_functions_text.count("region        fluid;") == 9
            and native_functions_text.count("region        mold;") == 1
            and native_functions_text.count("writeFields   false;") == 8,
            "FS-C06 native function-object inventory changed")
    require(re.search(
        r"FS_C06_mixtureMass\s*\{[^{}]*\bfields\s*\(rho\)\s*;",
        native_functions_text, re.S) is not None,
        "native mixture mass inventory is missing")
    for name, selection in (
        ("FS_C06_atmosphereMassFlux", r"patches\s*\(atmosphereTop\s+atmosphereSides\s+atmosphereLowerSides\)"),
        ("FS_C06_atmosphereTopMassFlux", r"patch\s+atmosphereTop"),
        ("FS_C06_atmosphereSidesMassFlux", r"patch\s+atmosphereSides"),
        ("FS_C06_atmosphereLowerSidesMassFlux", r"patch\s+atmosphereLowerSides"),
        ("FS_C06_fluidToMoldMassFlux", r"patch\s+fluid_to_mold"),
    ):
        block = re.search(r"\b" + re.escape(name) +
                          r"\s*\{([^{}]*)\}", native_functions_text, re.S)
        require(block is not None
                and re.search(r"\b" + selection + r"\s*;", block.group(1)) is not None
                and re.search(r"\boperation\s+sum\s*;", block.group(1)) is not None
                and re.search(r"\bfields\s*\(alphaRhoPhi\.metal\s+alphaRhoPhi\.air\s+rhoPhi\)\s*;",
                              block.group(1)) is not None,
                "missing or incorrectly configured native phase mass flux: " + name)
    for name, region, patch in (
        ("FS_C06_wallHeatFluxFluid", "fluid", "fluid_to_mold"),
        ("FS_C06_wallHeatFluxMold", "mold", "mold_to_fluid"),
    ):
        block = re.search(r"\b" + re.escape(name) +
                          r"\s*\{([^{}]*)\}", native_functions_text, re.S)
        require(block is not None
                and re.search(r"\btype\s+wallHeatFlux\s*;", block.group(1)) is not None
                and re.search(r"\bregion\s+" + region + r"\s*;", block.group(1)) is not None
                and re.search(r"\bpatches\s*\(" + patch + r"\)\s*;", block.group(1)) is not None,
                "missing conjugate heat flux native monitor: " + name)
    control.write_text(native_control_text, encoding="utf-8")
    native_functions_dest = dest / "system/functions"
    require(not native_functions_dest.is_symlink(),
            "inherited system/functions symlink not allowed")
    inherited_functions_sha = (digest(native_functions_dest)
        if native_functions_dest.is_file() else None)
    native_functions_dest.write_text(native_functions_text, encoding="utf-8")
    schemes = dest / "system/fluid/fvSchemes"
    modified, added = ensure_compressible_kepsilon_divergence(schemes.read_text())
    schemes.write_text(modified)
    candidate = dest / "constant/fluid/fvModels"
    original_models_text = original_models.read_text()
    # OPENFOAM NATIVE DICTIONARY IS THE SINGLE SOURCE OF EXECUTABLE PHYSICS.
    # Python only checks its provenance and copies it to the isolated case.
    native_path = project / NATIVE_FVMODELS
    require(native_path.is_file() and not native_path.is_symlink(),
            "tracked Foundation14 fvModels dictionary missing")
    native_text = native_path.read_text(encoding="utf-8")
    require(native_text == model_text(reference, original_models_text),
            "native OpenFOAM fvModels drifted from C14 or inherited FS-C05 sources")
    candidate.write_text(native_text, encoding="utf-8")
    result = {
        "schema": "masterproject-fs-c06-vof-phase-change-smoke-v1",
        "status": "FS_C06_STAGED_NO_CFD",
        "source": evidence, "output": str(dest),
        "foundation14_vof_model": "VoFSolidificationMelting",
        "model_field_expected": MODEL_FIELD,
        "C14_numerical_reference_NOT_physical_calibration": reference,
        "control_sha256": digest(control),
        "native_functions_sha256": digest(native_functions_dest),
        "native_functions_source": str(NATIVE_FUNCTIONS),
        "native_functions_source_sha256": digest(native_functions_path),
        "native_functions_copied_verbatim": True,
        "inherited_functions_sha256": inherited_functions_sha,
        "fvSchemes_sha256": digest(schemes),
        "fvModels_sha256": digest(candidate),
        "native_controlDict_source": str(NATIVE_CONTROL),
        "native_controlDict_source_sha256": digest(native_control_path),
        "native_controlDict_copied_verbatim": True,
        "native_openfoam_phase_volume_monitors": [
            "FS_C06_metalVoFVolume", "FS_C06_solidMetalVolume"
        ],
        "native_openfoam_conjugate_wall_heat_flux_monitors": [
            "FS_C06_wallHeatFluxFluid", "FS_C06_wallHeatFluxMold",
        ],
        "native_openfoam_mass_inventory_monitor": "FS_C06_mixtureMass",
        "native_openfoam_phase_boundary_mass_flux_monitors": [
            "FS_C06_atmosphereMassFlux",
            "FS_C06_atmosphereTopMassFlux",
            "FS_C06_atmosphereSidesMassFlux",
            "FS_C06_atmosphereLowerSidesMassFlux",
            "FS_C06_fluidToMoldMassFlux",
        ],
        "phase_mass_flux_fields": [
            "alphaRhoPhi.metal", "alphaRhoPhi.air", "rhoPhi"
        ],
        "open_boundary_mass_balance_verified": False,
        "native_fvModels_source": str(NATIVE_FVMODELS),
        "native_fvModels_source_sha256": digest(native_path),
        "native_fvModels_copied_verbatim": True,
        "inherited_fvModels_sha256": digest(original_models),
        "inherited_VoFTurbulenceDamping_preserved": True,
        "native_fvModels_entries": [
            "turbulenceDamping", "FS_C06_vof_phase_change"
        ],
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
        result["native_cfd_executed"] = True
        p = subprocess.run(cmd, capture_output=True, text=True,
                           errors="replace", check=False,
                           timeout=MAX_NATIVE_SECONDS)
        log.write_text("COMMAND: " + " ".join(cmd) + "\nEXIT: " +
                       str(p.returncode) + "\n" + p.stdout + "\n" + p.stderr)
        require(p.returncode == 0, "native foamMultiRun failed")
        result["native_solver_log"] = validate_run_log(p.stdout + "\n" + p.stderr)
        fraction = read_native_fraction(dest, reference["values"]["Tliq"])
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
    except (OSError, ValueError, KeyError, TypeError,
            subprocess.TimeoutExpired) as exc:
        print("FS-C06 BLOCKED:", exc, file=sys.stderr)
        print("ISOLATED EVIDENCE:", out, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
