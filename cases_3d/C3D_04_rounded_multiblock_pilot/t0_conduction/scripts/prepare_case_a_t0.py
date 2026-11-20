#!/usr/bin/env python3
"""Integrated Case A / C3D-04 T0 transient two-solid *numerical* preflight.

This module:
- validates real sourced material data, stage acknowledgement and BC hypothesis;
- reuses the previously accepted V4/T02 mesh, read-only;
- checks actual patch names/types, native checkMesh status/contact acceptance;
- builds ten Foundation14-oriented dictionaries IN MEMORY;
- materializes a new isolated directory ONLY if explicitly requested and
  every documented guard is satisfied.
It NEVER runs CFD, checkMesh or blockMesh. T0 is not solidification physics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

T0 = Path(__file__).resolve().parents[1]
CASE_A = T0.parent
sys.path.insert(0, str(CASE_A / "scripts"))
from audit_v4_t02_nonorth import audit as audit_saved_native, patch_metadata
from measure_interface_area import patch_area

INPUTS = T0 / "T0_INPUTS.json"
SOURCE = Path.home() / "OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02"
OUTPUT = Path.home() / "OpenFOAM/C3D04_A_T0_CONDUCTION_01"
SCHEMA = "C3D04_A_T0_1"
PURPOSE = "TRANSIENT_TWO_SOLID_CONDUCTION_NUMERICAL_CHECK_ONLY_NOT_CAST_IRON_SOLIDIFICATION"
MODEL = "constIsoSolid_rhoConst_eConst_sensibleInternalEnergy"
BC = "C14_THERMAL_EXTERIOR_H10_FINITE_CONTACT_TWO_SOLID_SURROGATE"
C14_ROOT = CASE_A.parents[1]/"cases_controlled_buoyancy"/"C14_topFixedFlux_explicitRef"
ACK = "T0_NUMERICAL_CHECK_ONLY_NOT_EXPERIMENTAL_VALIDATION"
FIELDS = {
    "rho_kg_m3": "source_rho",
    "Cv_J_kg_K": "source_Cv",
    "kappa_W_m_K": "source_kappa",
    "molWeight_g_mol": "source_molWeight",
    "T_initial_K": "source_T_initial",
}
EXTERIOR = {
    "metal": ("metalTop",),
    "mold": (
        "moldTop", "moldExterior", "moldBottom",
        "moldRecessWall", "moldRecessRoof"
    ),
}
COUPLED = {"metal": "metal_to_mold", "mold": "mold_to_metal"}


def positive(value) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def validate(config: object, allow_synthetic_test: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["root: must be a JSON object"]
    for key, expected in (
        ("schema", SCHEMA), ("purpose", PURPOSE),
        ("material_model", MODEL), ("thermal_BC_hypothesis", BC),
        ("acknowledgement", ACK),
    ):
        if config.get(key) != expected:
            errors.append(f"{key}: expected exact {expected}")
    for region in ("metal", "mold"):
        values = config.get(region)
        if not isinstance(values, dict):
            errors.append(f"{region}: missing object")
            continue
        for name, citation_key in FIELDS.items():
            if not positive(values.get(name)):
                errors.append(f"{region}.{name}: missing positive finite SI input")
            source = values.get(citation_key)
            if not isinstance(source, str) or len(source.strip()) < 10:
                errors.append(f"{region}.{citation_key}: missing meaningful provenance")
            elif not allow_synthetic_test and any(
                word in source.lower()
                for word in ("synthetic", "todo", "placeholder", "example", "dummy")
            ):
                errors.append(f"{region}.{citation_key}: synthetic/placeholder evidence is forbidden")
    simulation = config.get("simulation")
    if not isinstance(simulation, dict):
        errors.append("simulation: missing object")
    else:
        for key in ("deltaT_s", "endTime_s"):
            if not positive(simulation.get(key)):
                errors.append(f"simulation.{key}: positive finite seconds required")
        dt = simulation.get("deltaT_s")
        end = simulation.get("endTime_s")
        if positive(dt) and positive(end) and end <= dt:
            errors.append("simulation.endTime_s: must exceed deltaT_s")
        interval = simulation.get("writeEverySteps")
        if type(interval) is not int or interval <= 0:
            errors.append("simulation.writeEverySteps: positive integer required")
        energy = simulation.get("nEnergyCorrectors")
        if type(energy) is not int or not 1 <= energy <= 20:
            errors.append("simulation.nEnergyCorrectors: sourced integer 1..20 required")
        outer = simulation.get("nOuterCorrectors")
        if type(outer) is not int or not 1 <= outer <= 20:
            errors.append("simulation.nOuterCorrectors: sourced integer 1..20 required")
        nonorth = simulation.get("nNonOrthogonalCorrectors")
        if type(nonorth) is not int or not 0 <= nonorth <= 20:
            errors.append("simulation.nNonOrthogonalCorrectors: explicit integer 0..20 required")
        for key in ("source_time_choices", "source_nonorth_choice", "source_outer_correctors", "source_energy_coupling_choice"):
            evidence = simulation.get(key)
            if not isinstance(evidence, str) or len(evidence.strip()) < 10:
                errors.append(f"simulation.{key}: documented numerical rationale required")
    metal = config.get("metal")
    mold = config.get("mold")
    if isinstance(metal, dict) and isinstance(mold, dict):
        a, b = metal.get("T_initial_K"), mold.get("T_initial_K")
        if positive(a) and positive(b) and a == b:
            errors.append("metal and mold T_initial_K must differ for the T0 transfer test")
    # A C14 numerical solid-solid surrogate is NOT the original C14 metal-fluid
    # enthalpy formulation; the Cp→Cv approximation must be explicit and checked.
    metal = config.get("metal")
    if isinstance(metal, dict):
        if metal.get("Cp_to_Cv_surrogate_assumption") != (
            "CP_AS_EFFECTIVE_CV_ONLY_FOR_TWO_SOLID_T0_NOT_C14_FLUID_ENTHALPY"
        ):
            errors.append("metal.Cp_to_Cv_surrogate_assumption: must explicitly acknowledge Cp!=Cv")
        for key in ("Cp_C14_J_kg_K", "mu_C14_Pa_s", "Pr_C14"):
            if not positive(metal.get(key)):
                errors.append(f"metal.{key}: C14 source value missing")
        if positive(metal.get("Cv_J_kg_K")) and positive(metal.get("Cp_C14_J_kg_K")):
            if not math.isclose(metal["Cv_J_kg_K"], metal["Cp_C14_J_kg_K"], rel_tol=1e-10):
                errors.append("metal.Cv_J_kg_K: T0 surrogate must exactly trace to C14 Cp")
        if all(positive(metal.get(k)) for k in ("kappa_W_m_K","Cp_C14_J_kg_K","mu_C14_Pa_s","Pr_C14")):
            derived = metal["mu_C14_Pa_s"] * metal["Cp_C14_J_kg_K"] / metal["Pr_C14"]
            if not math.isclose(metal["kappa_W_m_K"], derived, rel_tol=1e-10):
                errors.append("metal.kappa_W_m_K: differs from C14 constTransport derived mu*Cp/Pr")
    bc = config.get("c14_boundary_reference")
    if not isinstance(bc, dict):
        errors.append("c14_boundary_reference: missing original C14 exterior/contact values")
    else:
        for side, names in {
            "metalTop": ("h_W_m2_K","Ta_K","emissivity"),
            "moldExterior": ("h_W_m2_K","Ta_K","emissivity"),
            "metal_to_mold": ("layer_thickness_m","layer_kappa_W_m_K","conductance_W_m2_K")
        }.items():
            item = bc.get(side)
            if not isinstance(item, dict) or any(not positive(item.get(k)) for k in names):
                errors.append(f"c14_boundary_reference.{side}: missing C14 values")
        interface = bc.get("metal_to_mold", {})
        if (isinstance(interface, dict) and
            all(positive(interface.get(k)) for k in ("layer_thickness_m","layer_kappa_W_m_K","conductance_W_m2_K"))):
            if not math.isclose(
                interface["layer_kappa_W_m_K"]/interface["layer_thickness_m"],
                interface["conductance_W_m2_K"], rel_tol=1e-10
            ):
                errors.append("C14 contact layer conductance must equal k/thickness")
    return errors


def fmt(n) -> str:
    if type(n) is int:
        return str(n)
    return format(n, ".12g")


def header(location: str, obj: str, cls: str = "dictionary") -> str:
    return (
        "/* C3D-04 Caso A. T0 only: isolated two-solid numerical conduction.\n"
        " * NOT cast iron solidification; NOT a validated casting BC.\n"
        " * OpenFOAM Foundation 14-oriented, native dictionary parse pending.\n"
        " */\n"
        "FoamFile\n{\n"
        "    version 2.0;\n    format ascii;\n"
        f"    class {cls};\n    location \"{location}\";\n    object {obj};\n"
        "}\n"
    )


def temperature(region: str, initial_K, bc: dict) -> str:
    lines = [
        header(f"0/{region}", "T", "volScalarField"),
        "dimensions [0 0 0 1 0 0 0];",
        f"internalField uniform {fmt(initial_K)};",
        "boundaryField", "{",
        '    #includeEtc "caseDicts/setConstraintTypes"',
    ]
    exterior = bc["metalTop"] if region == "metal" else bc["moldExterior"]
    for patch in EXTERIOR[region]:
        lines += [
            f"    {patch}", "    {",
            "        type externalTemperature;",
            f"        Ta constant {fmt(exterior['Ta_K'])};",
            f"        h constant {fmt(exterior['h_W_m2_K'])};",
            f"        emissivity {fmt(exterior['emissivity'])};",
            "        value $internalField;",
            "    }",
        ]
    lines += [
        f"    {COUPLED[region]}", "    {",
        "        type coupledTemperature;",
    ]
    if region == "metal":
        contact = bc["metal_to_mold"]
        lines += [
            "        h",
            "        {",
            "            type wallLayersHeatTransferCoefficient;",
            f"            thicknessLayers ({fmt(contact['layer_thickness_m'])});",
            f"            kappaLayers ({fmt(contact['layer_kappa_W_m_K'])});",
            "        }",
        ]
    lines += ["        value $internalField;", "    }", "}"]
    return "\n".join(lines) + "\n"


def thermophysical(region: str, data: dict) -> str:
    return header(f"constant/{region}", "physicalProperties") + (
        "thermoType\n{\n"
        "    type heSolidThermo;\n"
        "    mixture pureMixture;\n"
        "    transport constIsoSolid;\n"
        "    thermo eConst;\n"
        "    equationOfState rhoConst;\n"
        "    specie specie;\n"
        "    energy sensibleInternalEnergy;\n}\n"
        "mixture\n{\n"
        f"    specie {{ molWeight {fmt(data['molWeight_g_mol'])}; }}\n"
        f"    equationOfState {{ rho {fmt(data['rho_kg_m3'])}; }}\n"
        f"    transport {{ kappa {fmt(data['kappa_W_m_K'])}; }}\n"
        f"    thermodynamics {{ hf 0; Cv {fmt(data['Cv_J_kg_K'])}; }}\n"
        "}\n"
    )


def schemes(region: str) -> str:
    return header(f"system/{region}", "fvSchemes") + (
        "ddtSchemes { default Euler; }\n"
        "gradSchemes { default Gauss linear; }\n"
        "divSchemes { default none; }\n"
        "// Preliminary corrected diffusion: requires numerical sensitivity study.\n"
        "laplacianSchemes { default Gauss linear corrected; }\n"
        "interpolationSchemes { default linear; }\n"
        "snGradSchemes { default corrected; }\n"
    )


def solution(region: str, nonorth: int) -> str:
    return header(f"system/{region}", "fvSolution") + (
        "solvers\n{\n"
        "    e\n    {\n"
        "        solver GAMG;\n"
        "        smoother symGaussSeidel;\n"
        "        tolerance 1e-8;\n"
        "        relTol 0.05;\n"
        "        maxIter 200;\n"
        "    }\n"
        "    eFinal { $e; relTol 0; }\n"
        "}\n"
        f"PIMPLE {{ nNonOrthogonalCorrectors {nonorth}; }}\n"
    )


def global_solution(energy_correctors: int, outer_correctors: int) -> str:
    """Foundation14 foamMultiRun multi-region PIMPLE control (top-level)."""
    return header("system", "fvSolution") + (
        "PIMPLE\n{\n"
        f"    nOuterCorrectors {outer_correctors}; // traced from C14 root PIMPLE\n"
        f"    nEnergyCorrectors {energy_correctors};\n"
        "}\n"
    )


def control(cfg: dict) -> str:
    return header("system", "controlDict") + (
        "application foamMultiRun;\n"
        "regionSolvers\n{\n    metal solid;\n    mold solid;\n}\n"
        "startFrom startTime;\nstartTime 0;\nstopAt endTime;\n"
        f"endTime {fmt(cfg['endTime_s'])};\n"
        f"deltaT {fmt(cfg['deltaT_s'])};\n"
        "writeControl timeStep;\n"
        f"writeInterval {fmt(cfg['writeEverySteps'])};\n"
        "purgeWrite 0;\nwriteFormat ascii;\nwritePrecision 10;\n"
        "runTimeModifiable no;\n"
    )


def generate(cfg: dict) -> dict[str, str]:
    errors = validate(cfg, allow_synthetic_test=True)
    if errors:
        raise ValueError("Config validation failed: " + "; ".join(errors))
    items = {
        "system/controlDict": control(cfg["simulation"]),
        "system/fvSolution": global_solution(
            cfg["simulation"]["nEnergyCorrectors"],
            cfg["simulation"]["nOuterCorrectors"]
        ),
    }
    for region in ("metal", "mold"):
        items[f"0/{region}/T"] = temperature(region, cfg[region]["T_initial_K"], cfg["c14_boundary_reference"])
        items[f"constant/{region}/physicalProperties"] = thermophysical(region, cfg[region])
        items[f"system/{region}/fvSchemes"] = schemes(region)
        items[f"system/{region}/fvSolution"] = solution(
            region, cfg["simulation"]["nNonOrthogonalCorrectors"]
        )
    if len(items) != 10:
        raise AssertionError("Expected 10 independently rendered OpenFOAM files")
    for name, text in items.items():
        if "{{" in text or "}}" in text:
            raise AssertionError(f"Unresolved placeholder {name}")
        if text.count("{") != text.count("}"):
            raise AssertionError(f"Unbalanced dictionary braces {name}")
        if "C3D-05" in text:
            raise AssertionError(f"Case B tag contaminated Case A file: {name}")
    return items


def physical_patch_names(boundary_path: Path) -> set[str]:
    """Count active patches, rejecting unmodelled nonempty thermal boundaries.

    The regex must have ONE backslash per raw-string escape. The associated
    integrated static test checks actual mixed named/zero-face patch parsing.
    """
    body = boundary_path.read_text(encoding="utf-8")
    blocks = re.finditer(
        r"(?m)^\s*([A-Za-z_][A-Za-z_0-9]*)\s*\{([^{}]*)\}",
        body, re.S
    )
    found: set[str] = set()
    for match in blocks:
        inner = match.group(2)
        number = re.search(r"\bnFaces\s+(\d+)\s*;", inner)
        if number and int(number.group(1)) > 0:
            found.add(match.group(1))
    return found


def read_preserved_mesh_volumes(source: Path) -> dict[str, float]:
    """Read native V4/T02 reported volumes (NOT CAD volumes), never invent."""
    tsv = source/"PILOT_MESH_REPORT.tsv"
    if not tsv.is_file():
        raise FileNotFoundError(f"V4/T02 saved native volume table missing: {tsv}")
    with tsv.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if len(rows) != 2:
        raise ValueError("Expected exactly two native material volume rows")
    answer = {}
    expected_cells = {"metal": 8960, "mold": 12352}
    for row in rows:
        region = row.get("region")
        if region not in expected_cells or region in answer:
            raise ValueError(f"Unexpected or repeated volume region: {region}")
        volume = float(row.get("volume_m3", "nan"))
        if (not math.isfinite(volume) or volume <= 0
            or int(row.get("cells", -1)) != expected_cells[region]
            or row.get("mesh_ok") != "YES"):
            raise ValueError(f"{region}: native cell count/volume/acceptance changed")
        answer[region] = volume
    if set(answer) != set(expected_cells):
        raise ValueError("Saved native volume regions incomplete")
    return answer


def closed_t0_energy_target(cfg: dict, volumes: dict[str, float]) -> dict:
    """Ideal insulated two-solid T0 equilibrium, NEVER a CFD result."""
    capacity = {
        reg: cfg[reg]["rho_kg_m3"] * cfg[reg]["Cv_J_kg_K"] * volumes[reg]
        for reg in ("metal", "mold")
    }
    if not all(math.isfinite(v) and v > 0 for v in capacity.values()):
        raise ValueError("T0 lumped heat capacity must be positive and finite")
    total = sum(capacity.values())
    eq = sum(
        capacity[region] * cfg[region]["T_initial_K"]
        for region in ("metal", "mold")
    ) / total
    if not math.isfinite(eq):
        raise ValueError("T0 equilibrium-temperature calculation overflow")
    return {
        "model": "COUNTERFACTUAL_NO_EXTERNAL_HEAT_LOSS_TWO_SOLIDS_NOT_C14_BC",
        "regional_heat_capacity_J_per_K": capacity,
        "total_heat_capacity_J_per_K": total,
        "ideal_equilibrium_K_no_heat_loss": eq,
        "energy_residual_equation": (
            "Cmetal*(Tmetal-Tmetal0)+Cmold*(Tmold-Tmold0)=0"
        ),
        "validation_status": "COUNTERFACTUAL_INSULATED_LIMIT_NOT_T0_WITH_C14_CONVECTIVE_BOUNDARIES",
    }


def c14_source_gate(cfg: dict) -> dict:
    """Read the ORIGINAL tracked C14 files and refuse altered values.

    This checks physical input parity with the historical C14 dictionary.
    It does NOT imply the two-solid T0 reproduces fluid-solid C14 physics.
    """
    reference = json.loads(
        (T0/"C14_PARAMETER_BASELINE.json").read_text(encoding="utf-8")
    )
    if cfg.get("c14_reference_path") != (
        "cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
    ):
        raise ValueError("T0 inputs must identify the exact original C14 case")
    source_hashes = {}
    contents = {}
    for row in reference["source_details"]:
        path = C14_ROOT/row["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Original C14 file missing: {path}")
        data = path.read_bytes()
        git_blob = hashlib.sha1(
            ("blob " + str(len(data))).encode("ascii") + bytes([0]) + data
        ).hexdigest()
        if git_blob != row["blob_sha"]:
            raise ValueError(
                "Original C14 source changed since baseline; "
                f"{row['path']} expected git blob {row['blob_sha']}, got {git_blob}. "
                "Review and update provenance BEFORE reusing parameters."
            )
        source_hashes[row["path"]] = hashlib.sha256(data).hexdigest()
        # The original executable dictionary is before the appended
        # QUICKCUP DOCUMENTATION APPENDIX; never parse comment-only numbers.
        contents[row["path"]] = data.decode("utf-8").split(
            "// QUICKCUP DOCUMENTATION APPENDIX"
        )[0]
    def scalar(relative: str, key: str) -> float:
        body = contents[relative]
        match = re.search(
            rf"(?m)^\s*{re.escape(key)}\s+"
            rf"(?:uniform\s+|constant\s+)?"
            rf"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*;",
            body
        )
        if match is None:
            raise ValueError(f"C14 executable parameter not found: {relative}/{key}")
        return float(match.group(1))
    metal_source = "constant/metal/materials/castIron"
    mold_source = "constant/mold/materials/silica"
    initial_m = "0/metal/T"
    initial_s = "0/mold/T"
    control = "system/controlDict"
    root_sol = "system/fvSolution"
    metal_sol = "system/metal/fvSolution"
    derived = (
        scalar(metal_source, "mu") * scalar(metal_source, "Cp")
        / scalar(metal_source, "Pr")
    )
    expects = [
        ("metal.rho", cfg["metal"]["rho_kg_m3"], scalar(metal_source, "rho")),
        ("metal.Cp", cfg["metal"]["Cp_C14_J_kg_K"], scalar(metal_source, "Cp")),
        ("metal.T0_Cv_surrogate", cfg["metal"]["Cv_J_kg_K"], scalar(metal_source, "Cp")),
        ("metal.kappa_derived", cfg["metal"]["kappa_W_m_K"], derived),
        ("metal.mu", cfg["metal"]["mu_C14_Pa_s"], scalar(metal_source, "mu")),
        ("metal.Pr", cfg["metal"]["Pr_C14"], scalar(metal_source, "Pr")),
        ("metal.molWeight", cfg["metal"]["molWeight_g_mol"], scalar(metal_source, "molWeight")),
        ("metal.T_initial", cfg["metal"]["T_initial_K"], scalar(initial_m, "internalField")),
        ("mold.rho", cfg["mold"]["rho_kg_m3"], scalar(mold_source, "rho")),
        ("mold.Cv", cfg["mold"]["Cv_J_kg_K"], scalar(mold_source, "Cv")),
        ("mold.kappa", cfg["mold"]["kappa_W_m_K"], scalar(mold_source, "kappa")),
        ("mold.molWeight", cfg["mold"]["molWeight_g_mol"], scalar(mold_source, "molWeight")),
        ("mold.T_initial", cfg["mold"]["T_initial_K"], scalar(initial_s, "internalField")),
        ("sim.deltaT", cfg["simulation"]["deltaT_s"], scalar(control, "deltaT")),
        ("sim.endTime", cfg["simulation"]["endTime_s"], scalar(control, "endTime")),
        ("sim.writeEverySteps", cfg["simulation"]["writeEverySteps"], scalar(control, "writeInterval")),
        ("sim.nNonOrthogonalCorrectors",cfg["simulation"]["nNonOrthogonalCorrectors"],scalar(root_sol,"nNonOrthogonalCorrectors")),
        ("sim.nOuterCorrectors",cfg["simulation"]["nOuterCorrectors"],scalar(root_sol,"nOuterCorrectors")),
        # This was written in *regional* C14. Its EFFECT in C14 fluid was
        # not demonstrated. T0 global use is a separate documented hypothesis.
        ("sim.nEnergyCorrectors",cfg["simulation"]["nEnergyCorrectors"],scalar(metal_sol,"nEnergyCorrectors")),
        ("BC.metalTop.h",cfg["c14_boundary_reference"]["metalTop"]["h_W_m2_K"],scalar(initial_m,"h")),
        ("BC.metalTop.Ta",cfg["c14_boundary_reference"]["metalTop"]["Ta_K"],scalar(initial_m,"Ta")),
        ("BC.metalTop.emissivity",cfg["c14_boundary_reference"]["metalTop"]["emissivity"],scalar(initial_m,"emissivity")),
        ("BC.mold.h",cfg["c14_boundary_reference"]["moldExterior"]["h_W_m2_K"],scalar(initial_s,"h")),
        ("BC.mold.Ta",cfg["c14_boundary_reference"]["moldExterior"]["Ta_K"],scalar(initial_s,"Ta")),
        ("BC.mold.emissivity",cfg["c14_boundary_reference"]["moldExterior"]["emissivity"],scalar(initial_s,"emissivity")),
    ]
    for key, actual, original in expects:
        if type(actual) not in (int,float) or not math.isclose(
            actual, original, rel_tol=1e-10, abs_tol=1e-12
        ):
            raise ValueError(
                f"C14 SOURCE DRIFT / {key}: T0={actual!r}, C14 original={original}"
            )
    def layer(name: str) -> float:
        pattern=rf"\b{name}\s*\(\s*([0-9.eE+-]+)\s*\)\s*;"
        match=re.search(pattern, contents[initial_m])
        if match is None:
            raise ValueError(f"C14 metal interface missing {name}")
        return float(match.group(1))
    a=cfg["c14_boundary_reference"]["metal_to_mold"]
    for key, original in (
        ("layer_thickness_m", layer("thicknessLayers")),
        ("layer_kappa_W_m_K",layer("kappaLayers")),
    ):
        if not math.isclose(a[key], original, rel_tol=1e-10):
            raise ValueError(f"C14 source interface drift {key}")
    if not re.search(r"(?m)^\s*adjustTimeStep\s+no\s*;", contents[control]):
        raise ValueError("Original C14 time step no longer fixed")
    return {
        "original_case": str(C14_ROOT),
        "source_file_sha256": source_hashes,
        "verified_scalar_comparisons": len(expects)+2,
        "Cp_as_Cv_surrogate_explicit_not_original_C14_thermo": True,
        "model_3d_T0_is_not_original_C14_fluid_solidification": True,
    }


def thermal_network_budget(source: Path, cfg: dict,
                           volumes: dict[str, float]) -> dict:
    """Initial thermal power scales from original C14 BCs and native 3D areas.

    This is an initial-surface-temperature *estimate*. It is NOT a
    temperature time history, not an OpenFOAM heat-flux measurement,
    and not a substitute for 3D solver energy conservation.
    """
    if set(volumes) != {"metal", "mold"}:
        raise ValueError("Missing native metal/mold volumes")
    bc = cfg["c14_boundary_reference"]
    wall_area = {}
    for region in ("metal", "mold"):
        wall_area[region] = {}
        for patch in EXTERIOR[region]:
            area, count = patch_area(source, region, patch)
            if not positive(area) or count < 1:
                raise ValueError(f"Native exterior patch invalid: {region}/{patch}")
            wall_area[region][patch] = area
    contact_m, faces_m = patch_area(source, "metal", COUPLED["metal"])
    contact_s, faces_s = patch_area(source, "mold", COUPLED["mold"])
    if faces_m != faces_s or faces_m != 2496:
        raise ValueError("Native interface patch faces must remain reciprocal 2496")
    if (not positive(contact_m) or not positive(contact_s)
        or abs(contact_m-contact_s)/max(contact_m, contact_s) > 1e-6):
        raise ValueError("Native interface areas are not reciprocal within 1e-6")
    contact = bc["metal_to_mold"]
    g_contact = contact_m * contact["conductance_W_m2_K"]
    top_metal_area = sum(wall_area["metal"].values())
    outside_mold_area = sum(wall_area["mold"].values())
    g_out_metal = top_metal_area * bc["metalTop"]["h_W_m2_K"]
    g_out_mold = outside_mold_area * bc["moldExterior"]["h_W_m2_K"]
    t_m = cfg["metal"]["T_initial_K"]
    t_s = cfg["mold"]["T_initial_K"]
    amb_m = bc["metalTop"]["Ta_K"]
    amb_s = bc["moldExterior"]["Ta_K"]
    c_m = cfg["metal"]["rho_kg_m3"] * cfg["metal"]["Cv_J_kg_K"] * volumes["metal"]
    c_s = cfg["mold"]["rho_kg_m3"] * cfg["mold"]["Cv_J_kg_K"] * volumes["mold"]
    if not all(positive(x) for x in (g_contact, c_m, c_s, g_out_metal, g_out_mold)):
        raise ValueError("Thermal budget: nonpositive conductance or heat capacity")
    p_contact = g_contact * (t_m-t_s)
    p_ext_metal = g_out_metal * (t_m-amb_m)
    p_ext_mold = g_out_mold * (t_s-amb_s)
    # Optional Stefan-Boltzmann reference. emissivity on externalTemperature
    # also radiates; this is an INITIAL UNIFORM-T bounding proxy only.
    sigma = 5.670374419e-8
    p_rad_metal = (
        bc["metalTop"]["emissivity"] * sigma * top_metal_area
        * (t_m**4-amb_m**4)
    )
    p_rad_mold = (
        bc["moldExterior"]["emissivity"] * sigma * outside_mold_area
        * (t_s**4-amb_s**4)
    )
    return {
        "status": "INITIAL_C14_BC_GEOMETRIC_POWER_SCALE_NOT_CFD",
        "native_external_patch_areas_m2": wall_area,
        "native_contact_area_m2": contact_m,
        "native_contact_faces_each_side": faces_m,
        "heat_capacities_J_per_K": {"metal": c_m, "mold": c_s},
        "conductance_W_per_K": {
            "contact": g_contact,
            "metal_outer": g_out_metal,
            "mold_outer": g_out_mold,
        },
        "initial_uniform_temperature_power_W_positive_outward": {
            "metal_to_mold_contact": p_contact,
            "metal_to_ambient_convection": p_ext_metal,
            "mold_to_ambient_convection": p_ext_mold,
            "metal_to_ambient_radiation_estimate": p_rad_metal,
            "mold_to_ambient_radiation_estimate": p_rad_mold,
        },
        "contact_only_lumped_time_scale_s": {
            "metal": c_m/g_contact,
            "mold": c_s/g_contact,
        },
        "limits": [
            "All exterior/contact areas are real saved native polyMesh areas; thermal powers use C14 constants",
            "Uniform initial wall temperatures assumed equal to the region initial fields; real near-wall gradients unknown",
            "Contact series resistance also includes cell conduction; h_contact*A is NOT full interface effective conductance",
            "Stefan-Boltzmann term is an indicative estimate, not native OpenFOAM radiative flux",
            "Initial 1500K exceeds C14 liquidus 1473K, yet T0 intentionally neglects phase change and flow",
            "This is not a temporal solution nor evidence of numerical stability, energy conservation or physical validation",
        ],
    }


def native_case_gate(source: Path) -> dict:
    if not source.is_dir():
        raise FileNotFoundError(f"Preserved Case A V4/T02 missing: {source}")
    evidence = audit_saved_native(source)
    # Source inspector also directly checks saved logs, three regions,
    # mappedWall reciprocal metadata, top wall and original contact-area gate.
    for region in ("metal", "mold"):
        root = source/"constant"/region/"polyMesh"
        for key in ("points", "faces", "owner", "neighbour", "boundary"):
            if not (root/key).is_file():
                raise FileNotFoundError(f"Missing native source {root/key}")
        for patch in EXTERIOR[region]:
            actual = patch_metadata(root/"boundary", patch)
            if actual["type"] != "wall" or actual["nFaces"] <= 0:
                raise ValueError(
                    f"C3D04 T0 exterior patch {region}/{patch}: "
                    f"expected nonempty native wall, observed={actual}"
                )
        coupled = patch_metadata(root/"boundary", COUPLED[region])
        if coupled["type"] != "mappedWall" or coupled["nFaces"] != 2496:
            raise ValueError(f"Invalid native coupled patch {region}/{COUPLED[region]}")
        actual_nonempty = physical_patch_names(root/"boundary")
        expected_nonempty = set(EXTERIOR[region]) | {COUPLED[region]}
        if actual_nonempty != expected_nonempty:
            raise ValueError(
                f"Case A {region}: T0 does not cover all active polyMesh patches; "
                f"missing field BC={sorted(actual_nonempty - expected_nonempty)}, "
                f"incorrectly assumed BC={sorted(expected_nonempty - actual_nonempty)}"
            )
    saved_volumes = read_preserved_mesh_volumes(source)
    return {
        "source": str(source),
        "native_volumes_m3_from_preserved_tsv": saved_volumes,
        "native_mesh_quality_and_contact_from_saved_evidence": True,
        "expected_regions": ["metal", "mold"],
        "expected_external_patch_names": EXTERIOR,
        "severe_face_counts_from_logs": {
            name: v["severely_nonorthogonal_faces_above_70deg"]
            for name, v in evidence["regions"].items()
        },
        "no_new_checkMesh_or_CFD": True,
    }


def isolated_output(source: Path, dest: Path):
    if source == dest or source in dest.parents or dest in source.parents:
        raise ValueError("Output must be separate from the accepted source mesh")
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f"Preserving pre-existing case output: {dest}")


def materialize(source: Path, dest: Path, cfg: dict, input_file: Path,
                items: dict[str, str], evidence: dict):
    """Build, parse and verify in staging; publish only a complete isolated T0.

    A failed native foamDictionary parse or copy leaves NO final directory.
    Native geometry is copied verbatim, never moved from the accepted T02.
    """
    isolated_output(source, dest)
    if os.environ.get("WM_PROJECT_VERSION") != "14":
        raise RuntimeError("Foundation 14 environment required BEFORE materialization")
    foam_dictionary = shutil.which("foamDictionary")
    if foam_dictionary is None:
        raise RuntimeError("foamDictionary unavailable; refusing incomplete output")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{dest.name}.staging.", dir=dest.parent
    ) as temp:
        stage = Path(temp)/"candidate"
        stage.mkdir()
        hashes = {}
        for region in ("metal", "mold"):
            base = Path("constant")/region/"polyMesh"
            for name in ("points", "faces", "owner", "neighbour", "boundary"):
                relative = base/name
                source_hash = hashlib.sha256((source/relative).read_bytes()).hexdigest()
                hashes[str(relative)] = source_hash
            shutil.copytree(
                source/base, stage/base, symlinks=False
            )
            for name in ("points", "faces", "owner", "neighbour", "boundary"):
                relative = base/name
                copy_hash = hashlib.sha256((stage/relative).read_bytes()).hexdigest()
                if copy_hash != hashes[str(relative)]:
                    raise ValueError(
                        f"Copy mismatch on preserved native mesh: {relative}"
                    )
        for name, content in items.items():
            target = stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as stream:
                stream.write(content)
        parsed = []
        for relative in sorted(items):
            command = subprocess.run(
                [foam_dictionary, str(stage/relative)],
                cwd=stage, capture_output=True, text=True,
                timeout=30, check=False
            )
            if command.returncode != 0:
                detail = (command.stdout + "\n" + command.stderr).strip()
                raise RuntimeError(
                    f"Foundation14 foamDictionary rejected {relative}; "
                    f"no final T0 case created. Output: {detail[-3000:]}"
                )
            parsed.append(relative)
        record = {
            "status": "T0_FILESET_MATERIALIZED_NATIVE_DICTIONARIES_PARSED_NOT_SOLVED",
            "initial_C14_BC_thermal_budget": thermal_network_budget(
                source, cfg, evidence["native_volumes_m3_from_preserved_tsv"]
            ),
            "idealized_closed_energy_preflight": closed_t0_energy_target(
                cfg, evidence["native_volumes_m3_from_preserved_tsv"]
            ),
            "not_validated_physics": True,
            "not_CFD_executed": True,
            "source_case_preserved": str(source),
            "new_case": str(dest),
            "input_sha256": hashlib.sha256(input_file.read_bytes()).hexdigest(),
            "source_native_gates": evidence,
            "source_and_copy_mesh_sha256": hashes,
            "native_foundation14_parsed_files": parsed,
            "thermophysical_parameters_and_sources": cfg,
            "expected_solver": "foamMultiRun",
            "next_gate": "EXPLICIT_PERMISSION_AND_THERMAL_COUPLING_ENERGY_CONSERVATION",
            "no_solver_executed": True,
        }
        with (stage/"T0_PREPARATION_REPORT.json").open(
            "x", encoding="utf-8"
        ) as stream:
            json.dump(record, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
        # Final stage last, without overwriting any prior evidence.
        isolated_output(source, dest)
        os.rename(stage, dest)


def synthetic_fixture():
    # Used only in internal unit tests; NEVER physical QuickCup parameters.
    cfg = json.loads(INPUTS.read_text(encoding="utf-8"))
    for region in ("metal", "mold"):
        cfg[region].update({
            "rho_kg_m3": 2., "Cv_J_kg_K": 3.,
            "kappa_W_m_K": 4., "molWeight_g_mol": 5.,
            "T_initial_K": 6. if region == "metal" else 7.,
            **({
                "Cp_C14_J_kg_K": 3., "mu_C14_Pa_s": 4*0.14/3,
                "Pr_C14": 0.14,
            } if region == "metal" else {}),
            "source_rho": "SYNTHETIC_UNIT_TEST",
            "source_Cv": "SYNTHETIC_UNIT_TEST",
            "source_kappa": "SYNTHETIC_UNIT_TEST",
            "source_molWeight": "SYNTHETIC_UNIT_TEST",
            "source_T_initial": "SYNTHETIC_UNIT_TEST",
        })
    cfg["simulation"].update({
        "deltaT_s": 0.01, "endTime_s": 0.10,
        "writeEverySteps": 2, "nNonOrthogonalCorrectors": 2,
        "nOuterCorrectors": 3, "nEnergyCorrectors": 2,
        "source_time_choices": "SYNTHETIC_UNIT_TEST",
        "source_nonorth_choice": "SYNTHETIC_UNIT_TEST",
        "source_outer_correctors": "SYNTHETIC_UNIT_TEST",
        "source_energy_coupling_choice": "SYNTHETIC_UNIT_TEST",
    })
    # The local test is synthetic-only: the C14 source contract is separately
    # validated against the actual tracked source files in production.
    return cfg


def self_test():
    base = json.loads(INPUTS.read_text(encoding="utf-8"))
    errors = validate(base)
    assert errors == [], "Original C14 source inputs must pass static schema: " + str(errors)
    cfg = synthetic_fixture()
    assert validate(cfg, allow_synthetic_test=True) == []
    assert validate(cfg, allow_synthetic_test=False) != []
    files = generate(cfg)
    assert len(files) == 10
    assert "nEnergyCorrectors 2;" in files["system/fvSolution"]
    assert "nOuterCorrectors 3;" in files["system/fvSolution"]
    assert "application foamMultiRun;" in files["system/controlDict"]
    for region in ("metal", "mold"):
        field = files[f"0/{region}/T"]
        for patch in EXTERIOR[region] + (COUPLED[region],):
            assert patch in field
        assert "type coupledTemperature;" in field
        assert "type externalWallHeatFluxTemperature;" in field
        assert "constIsoSolid" in files[f"constant/{region}/physicalProperties"]
        assert "nNonOrthogonalCorrectors 2;" in files[f"system/{region}/fvSolution"]
    cfg["mold"]["kappa_W_m_K"] = None
    assert any("mold.kappa_W_m_K" in e for e in validate(cfg))
    cfg["mold"]["kappa_W_m_K"] = 4.
    cfg["simulation"]["nNonOrthogonalCorrectors"] = -1
    assert any("nNonOrthogonalCorrectors" in e for e in validate(cfg))
    target = closed_t0_energy_target(
        synthetic_fixture(), {"metal": 1.0, "mold": 1.0}
    )
    assert abs(target["ideal_equilibrium_K_no_heat_loss"] - 6.5) < 1e-12
    print("STATIC_INTEGRATED_T0_PASS: archived C14 input schema; synthetic counterexamples; 10 files incl global PIMPLE; native patch contracts; source parity suite; zero solver runs")
    print("STATIC_ONLY: no OpenFOAM, CFD or thermal case creation.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, default=INPUTS)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--out", type=Path, default=OUTPUT)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--materialize", action="store_true",
                   help="Atomically copy native meshes and ten parsed dictionaries to a new directory, NEVER run CFD")
    args = p.parse_args()
    if args.self_test:
        self_test()
        return 0
    input_file = args.inputs.expanduser().resolve(strict=True)
    cfg = json.loads(input_file.read_text(encoding="utf-8"))
    source = args.source.expanduser().resolve(strict=True)
    dest = args.out.expanduser().resolve()
    if args.materialize:
        isolated_output(source, dest)
    # Fail-fast before expensive native mesh reading; this still checks all
    # original native gates on any valid candidate.
    errors = validate(cfg)
    if errors:
        print("CASE_A_T0_CONFIG_INVALID_OR_UNSUPPORTED:")
        for e in errors:
            print(" - " + e)
        print("No source mesh read, no output materialization, no CFD.")
        return 3
    evidence = native_case_gate(source)
    # Source parity only after full schema validation. Never treat
    # a C14-named citation string as proof of the actual archived values.
    evidence["c14_source_parity"] = c14_source_gate(cfg)
    files = generate(cfg)
    energy = closed_t0_energy_target(
        cfg, evidence["native_volumes_m3_from_preserved_tsv"]
    )
    initial_budget = thermal_network_budget(
        source, cfg, evidence["native_volumes_m3_from_preserved_tsv"]
    )
    if not args.materialize:
        print("C14_ARCHIVED_SOURCE_PARITY_OK: all source blob SHA-1 and scalar parameters verified")
        print(f"CASE_A_T0_CONFIG_AND_SOURCE_PRECHECK_OK: {len(files)} files renderable")
        print("COUNTERFACTUAL_INSULATED_EQUILIBRIUM_K_NOT_C14_BC:",
              energy["ideal_equilibrium_K_no_heat_loss"],
              "| theoretical constant-Cv and adiabatic only, NOT CFD")
        print("C14_3D_MESH_INITIAL_CONTACT_POWER_W_ESTIMATE:",
              initial_budget["initial_uniform_temperature_power_W_positive_outward"]
              ["metal_to_mold_contact"])
        print("C14_3D_MESH_INITIAL_METAL_OUTSIDE_CONVECTION_W_ESTIMATE:",
              initial_budget["initial_uniform_temperature_power_W_positive_outward"]
              ["metal_to_ambient_convection"])
        print("C14_INITIAL_BUDGET_IS_NOT_CFD_OR_ENERGY_CONSERVATION.")
        print("No files written. No CFD. Native Foundation14 dictionary parse remains pending.")
        return 0
    materialize(source, dest, cfg, input_file, files, evidence)
    print(f"CASE_A_T0_MATERIALIZED_NOT_SOLVED: {dest}")
    print("All 10 dictionaries parsed with native Foundation14 foamDictionary; actual coupled thermophysics/CFD still UNVERIFIED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
