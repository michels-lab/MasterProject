#!/usr/bin/env python3
"""C3D-04 Caso A: source-faithful C14 fluid + solid physics, no T0 surrogate.

This validates the ACTUAL historical C14 files, not a copied numerical guess.
It renders the 3D initial scalar/vector fields and 3D patch BC using only
measured/declared source C14 values; does not execute CFD, copy the user's
V4/T02 meshes, or resolve geometry-only pRefPoint and cellZone mapping.
Those two gates MUST be resolved from actual native metal polyMesh before
any C14 3D solver materialization. It may NOT silently select a new model.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
C14 = ROOT / "cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
BASELINE = ROOT / "cases_3d/C3D_04_rounded_multiblock_pilot/t0_conduction/C14_PARAMETER_BASELINE.json"
CONTRACT = HERE / "C14_3D_PHYSICS_CONTRACT.json"

EXTERIOR = {
    "metal": ("metalTop",),
    "mold": ("moldTop", "moldExterior", "moldBottom",
             "moldRecessWall", "moldRecessRoof"),
}
CONTACT = {"metal": "metal_to_mold", "mold": "mold_to_metal"}
FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("C14_SOURCE_FIDELITY_BLOCKED: " + message)


def read_original(relative: str) -> str:
    require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
            "unsafe original C14 path")
    path = C14 / relative
    require(path.is_file() and not path.is_symlink(), "missing original " + relative)
    return path.read_text(encoding="utf-8")


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


def strip_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.S)


def number(body: str, key: str) -> float:
    matches = re.findall(r"\b" + re.escape(key) + r"\s+(" + FLOAT + r")\s*;",
                         strip_comments(body))
    require(len(matches) == 1, "expected exactly one original scalar " + key)
    v = float(matches[0])
    require(math.isfinite(v), "nonfinite C14 " + key)
    return v


def assert_eq(observed, expected, description: str) -> None:
    if isinstance(expected, bool):
        require(observed is expected, description + " drifted")
    elif type(expected) in (float, int):
        require(type(observed) in (float, int)
                and math.isclose(float(observed), float(expected),
                                 rel_tol=1e-10, abs_tol=1e-13),
                description + f" original={observed!r} contract={expected!r}")
    else:
        require(observed == expected, description + " differs from C14 contract")


def verify() -> dict:
    cfg = json.loads(CONTRACT.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    require(cfg["canonical_C14"] == baseline["source_case"], "wrong source case")
    require(cfg["scope"] == "CASE_A_C3D_04_V4_T02_METAL_FLUID_MOLD_SOLID_ONLY",
            "Case A/B or contraction confusion")
    c = cfg["C14_exact_values"]
    hard = cfg["non_negotiable"]
    require(hard["metal_solver"] == "fluid" and hard["mold_solver"] == "solid",
            "C14 is fluid-solid, NOT two solids")

    hashes = {}
    for item in baseline["source_details"]:
        rel = item["path"]
        path = C14 / rel
        require(path.is_file() and not path.is_symlink(), "missing pinned C14 " + rel)
        actual = git_blob_sha1(path.read_bytes())
        require(actual == item["blob_sha"], "original C14 blob changed " + rel)
        hashes[rel] = actual

    cast = read_original("constant/metal/materials/castIron")
    silica = read_original("constant/mold/materials/silica")
    phase = read_original("constant/metal/fvModels")
    control = read_original("system/controlDict")
    root_pimple = read_original("system/fvSolution")
    regional = read_original("system/metal/fvSolution")
    transport = read_original("constant/metal/momentumTransport")
    metalT = read_original("0/metal/T")
    moldT = read_original("0/mold/T")
    metalU = read_original("0/metal/U")
    metalP = read_original("0/metal/p")
    metalPRgh = read_original("0/metal/p_rgh")
    gravity = read_original("constant/metal/g")
    pressure_reference = read_original("constant/metal/pRef")

    for name, file, options in (
        ("castIron", cast, ("heRhoThermo", "hConst", "sensibleEnthalpy", "rhoConst", "const")),
        ("silica", silica, ("heSolidThermo", "eConst", "sensibleInternalEnergy", "rhoConst", "constIsoSolid")),
    ):
        for entry in options:
            require(re.search(r"\b" + entry + r"\s*;", strip_comments(file)) is not None,
                    f"C14 {name} missing thermo type {entry}")

    for key, source_key in (("rho_kg_m3", "rho"), ("Cp_J_kgK", "Cp"),
                            ("mu_Pas", "mu"), ("Pr", "Pr"),
                            ("molWeight_kg_kmol", "molWeight")):
        assert_eq(number(cast, source_key), c["metal"][key], "C14 castIron." + source_key)
    for key, source_key in (("rho_kg_m3", "rho"), ("Cv_J_kgK", "Cv"),
                            ("kappa_W_mK", "kappa"),
                            ("molWeight_kg_kmol", "molWeight")):
        assert_eq(number(silica, source_key), c["mold"][key], "C14 silica." + source_key)
    for key, original in (("Tsol_K", "Tsol"), ("Tliq_K", "Tliq"),
                          ("L_J_kg", "L"), ("alpha1e", "alpha1e"),
                          ("beta_1_K", "beta"), ("rhoRef_kg_m3", "rhoRef"),
                          ("relax", "relax"), ("Cu", "Cu"), ("q", "q")):
        assert_eq(number(phase, original), c["solidification"][key],
                  "C14 solidification." + original)
    for item in ("solidificationMeltingSource", "energy          h", "cellZone        metal",
                 "thermoMode      thermo"):
        require(item in phase, "C14 phase-change structure missing " + item)
    require("simulationType laminar;" in transport, "C14 laminar physics changed")
    require("metal       fluid;" in control and "mold        solid;" in control,
            "C14 solver assignment is not fluid+solid")
    for original, key in (("deltaT", "deltaT_s"), ("endTime", "endTime_s"),
                          ("writeInterval", "writeInterval_steps"),
                          ("maxCo", "maxCo_configured")):
        assert_eq(number(control, original), c["numerics"][key], "C14 control." + original)
    require(re.search(r"\badjustTimeStep\s+no\s*;", control) is not None,
            "C14 adjustTimeStep must stay no")
    for original, key in (("nOuterCorrectors", "PIMPLE_root_nOuterCorrectors"),
                          ("nCorrectors", "PIMPLE_root_nCorrectors"),
                          ("nNonOrthogonalCorrectors", "PIMPLE_root_nNonOrthogonalCorrectors")):
        assert_eq(number(root_pimple, original), c["numerics"][key], "C14 root." + original)
    assert_eq(number(regional, "nEnergyCorrectors"),
              c["numerics"]["metal_region_nEnergyCorrectors_written"],
              "C14 regional nEnergyCorrectors")
    require("nEnergyCorrectors" not in strip_comments(root_pimple),
            "C14 did not have root nEnergyCorrectors=2")
    require("slip;" in metalU and "noSlip;" in metalU, "C14 U patch types differ")
    require(re.search(r"\\binternalField\\s+uniform\\s*\\(\\s*0\\s+0\\s+0\\s*\\)\\s*;", metalU) is not None,
            "C14 U initial velocity must be the original zero vector")
    require(metalPRgh.count("fixedFluxPressure;") == 2,
            "C14 pressure BC differs")
    g_match = re.search(r"\bvalue\s*\(\s*("+FLOAT+r")\s+("+FLOAT+r")\s+("+FLOAT+r")\s*\)\s*;", gravity)
    require(g_match is not None, "C14 actual gravity vector missing")
    for coordinate, expected in zip(map(float, g_match.groups()), c["metal"]["gravity_m_s2"]):
        assert_eq(coordinate, expected, "C14 gravity vector component")
    assert_eq(number(pressure_reference, "value"), c["metal"]["pRefValue_Pa"],
              "C14 pRefValue")
    for text, expected in ((metalT,c["metal"]["T_initial_K"]),
                           (moldT,c["mold"]["T_initial_K"]),
                           (metalP,c["metal"]["p_initial_Pa"]),
                           (metalPRgh,c["metal"]["p_rgh_initial_Pa"])):
        match = re.search(r"\binternalField\s+uniform\s+("+FLOAT+r")\s*;", text)
        require(match is not None, "C14 initial field missing")
        assert_eq(float(match.group(1)), expected, "C14 original field initial")
    original_model_top = strip_comments(metalT)
    original_model_mold = strip_comments(moldT)
    require("h               uniform 10;" in original_model_top
            and "Ta              constant 300;" in original_model_top,
            "C14 metalTop convection original changed")
    require(re.search(r"\bh\s+uniform\s+10\s*;", original_model_mold)
            and re.search(r"\bTa\s+constant\s+300\s*;", original_model_mold),
            "C14 mold exterior original changed")
    assert_eq(number(metalT, "emissivity"), c["metal"]["top_emissivity"],
              "C14 metal emissivity")
    assert_eq(number(moldT, "emissivity"), c["mold"]["exterior_emissivity"],
              "C14 mold emissivity")
    for source_name, contract_name in (("thicknessLayers", "contact_thickness_m"),
                                      ("kappaLayers", "contact_kappa_W_mK")):
        match = re.search(r"\b"+source_name+r"\s*\(\s*("+FLOAT+r")\s*\)\s*;", metalT)
        require(match is not None, "C14 contact model missing "+source_name)
        assert_eq(float(match.group(1)), c["metal"][contract_name],
                  "C14 contact "+source_name)
    assert_eq(number(regional, "pRefValue"), c["metal"]["pRefValue_Pa"],
              "C14 point pressure reference value")
    require(re.search(r"\bpRefPoint\s+\(\s*0\.02\s+0\.04\s+0\.005\s*\)\s*;",regional),
            "original C14 pRefPoint changed; geometry mapping required")

    # No inferred thermo or ad-hoc missing data.
    require(hard["forbid_metal_Cp_as_Cv"] and hard["forbid_two_solid_solver_for_C14_3D"],
            "C14 3D must never use the former two-solid Cp->Cv surrogate")
    return {
        "schema": cfg["schema"],
        "status": "C14_EXECUTABLE_SOURCE_FIDELITY_PASS_NOT_3D_CFD",
        "original_C14_git_blob_sha1_verified": hashes,
        "regionSolvers": {"metal": "fluid", "mold": "solid"},
        "C14_phase_change_parameters": c["solidification"],
        "C14_momentum_and_energy_retained": True,
        "3D_native_reference_point_verified": False,
        "3D_metal_cell_zone_verified": False,
        "3D_solver_executed": False,
    }


def field(obj: str, region: str, value: str, dimensions: str,
          boundaries: dict[str,str], cls: str) -> str:
    patches = set(EXTERIOR[region]) | {CONTACT[region]}
    require(set(boundaries) == patches, "missing 3D thermal/physical patch coverage " + obj)
    return (
        "FoamFile\n{\n    version 2.0;\n    format ascii;\n"
        f"    class {cls};\n    location \"0/{region}\";\n    object {obj};\n}}\n"
        f"dimensions {dimensions};\ninternalField uniform {value};\n"
        "boundaryField\n{\n"
        + "".join(f"    {patch}\n    {{\n        {bc}\n    }}\n"
                  for patch,bc in boundaries.items())
        + "}\n"
    )


def generate_3d_initial_fields() -> dict[str,str]:
    # Source must be checked BEFORE any candidate field is rendered.
    verify()
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))["C14_exact_values"]
    m, s, pc = c["metal"], c["mold"], c["solidification"]
    def ext(material: str) -> str:
        data = m if material == "metal" else s
        h = data["top_h_W_m2K"] if material == "metal" else data["exterior_h_W_m2K"]
        Ta = data["top_Ta_K"] if material == "metal" else data["exterior_Ta_K"]
        epsilon = data["top_emissivity"] if material == "metal" else data["exterior_emissivity"]
        return ("type externalTemperature;\n"
                f"        h uniform {h:g};\n"
                f"        Ta constant {Ta:g};\n"
                f"        emissivity {epsilon:g};\n"
                "        value $internalField;")
    tmetal = {p:ext("metal") for p in EXTERIOR["metal"]}
    tmetal[CONTACT["metal"]] = (
        "type coupledTemperature;\n        h\n        {\n"
        "            type wallLayersHeatTransferCoefficient;\n"
        f"            thicknessLayers ({m['contact_thickness_m']:g});\n"
        f"            kappaLayers ({m['contact_kappa_W_mK']:g});\n"
        "        }\n        value $internalField;"
    )
    tmold = {p:ext("mold") for p in EXTERIOR["mold"]}
    tmold[CONTACT["mold"]] = "type coupledTemperature;\n        value $internalField;"
    def mbc(outer: str, contact: str):
        return {"metalTop":outer, CONTACT["metal"]:contact}
    pbc = mbc("type calculated;\n        value $internalField;",
              "type calculated;\n        value $internalField;")
    p_rgh_bc = mbc("type fixedFluxPressure;\n        value $internalField;",
                   "type fixedFluxPressure;\n        value $internalField;")
    u_bc = mbc("type slip;", "type noSlip;")
    fluid = {
        "0/metal/T":field("T","metal",f"{m['T_initial_K']:g}",
                          "[0 0 0 1 0 0 0]",tmetal,"volScalarField"),
        "0/metal/U":field("U","metal","(0 0 0)",
                          "[0 1 -1 0 0 0 0]",u_bc,"volVectorField"),
        "0/metal/p":field("p","metal",f"{m['p_initial_Pa']:g}",
                          "[1 -1 -2 0 0 0 0]",pbc,"volScalarField"),
        "0/metal/p_rgh":field("p_rgh","metal",f"{m['p_rgh_initial_Pa']:g}",
                          "[1 -1 -2 0 0 0 0]",p_rgh_bc,"volScalarField"),
        "0/mold/T":field("T","mold",f"{s['T_initial_K']:g}",
                         "[0 0 0 1 0 0 0]",tmold,"volScalarField"),
        "0/metal/phaseChangeSource:alpha1":field(
            "phaseChangeSource:alpha1","metal","1",
            "[0 0 0 0 0 0 0]",
            mbc("type zeroGradient;", "type zeroGradient;"),"volScalarField"
        ),
        "0/metal/phaseChangeSolidFraction":field(
            "phaseChangeSolidFraction","metal","0",
            "[0 0 0 0 0 0 0]",
            mbc("type calculated;\n        value uniform 0;",
                "type calculated;\n        value uniform 0;"),"volScalarField"
        ),
        "0/metal/latentHeat":field(
            "latentHeat","metal",f"{pc['L_J_kg']:g}",
            "[0 2 -2 0 0 0 0]",
            mbc("type calculated;\n        value $internalField;",
                "type calculated;\n        value $internalField;"),"volScalarField"
        ),
    }
    require(all("frontAndBack" not in v for v in fluid.values()),
            "2D empty must never be copied into the 3D domain")
    require("sensibleInternalEnergy" not in fluid["0/metal/T"],
            "must keep metal enthalpy, not T0 solid surrogate")
    return fluid



def assemble_unmaterialized_source_exact_fileset() -> dict[str, str]:
    """Assemble original C14 solver/model dictionaries plus 3D-ready fields.

    This is not a runnable case until BOTH region mesh-derived mappings for
    pRefPoint and cellZone are validated on actual V4/T02 polyMesh in WSL.
    Importing the old C14 2D point unmodified would be physically incorrect.
    """
    files = generate_3d_initial_fields()
    original = (
        "system/controlDict",
        "system/fvSolution",
        "system/metal/fvSchemes",
        "system/metal/fvSolution",
        "system/mold/fvSchemes",
        "system/mold/fvSolution",
        "constant/metal/physicalProperties",
        "constant/metal/materials/castIron",
        "constant/metal/fvModels",
        "constant/metal/momentumTransport",
        "constant/metal/g",
        "constant/metal/pRef",
        "constant/mold/physicalProperties",
        "constant/mold/materials/silica",
    )
    for relative in original:
        require(relative not in files, "duplicate C14 source path")
        files[relative] = read_original(relative)
    require("metal       fluid;" in files["system/controlDict"],
            "fluid phase omitted from native setup")
    require("mold        solid;" in files["system/controlDict"],
            "solid mold omitted from native setup")
    require("solidificationMeltingSource;" in files["constant/metal/fvModels"],
            "C14 latent heat source replaced")
    require("alpha1e         0.8;" in files["constant/metal/fvModels"],
            "C14 eutectic fraction omitted")
    require("type            heRhoThermo;" in files["constant/metal/materials/castIron"],
            "C14 fluid enthalpy material replaced")
    require("type            heSolidThermo;" in files["constant/mold/materials/silica"],
            "C14 mold material replaced")
    require("pRefPoint" in files["system/metal/fvSolution"],
            "3D reference point needs documented mesh-only adaptation")
    require(len(files) == 22, "C14 3D source-complete candidate expected 22 files")
    return files


def sources_manifest() -> dict:
    files = assemble_unmaterialized_source_exact_fileset()
    originals = set([
        "system/controlDict", "system/fvSolution",
        "system/metal/fvSchemes", "system/metal/fvSolution",
        "system/mold/fvSchemes", "system/mold/fvSolution",
        "constant/metal/physicalProperties",
        "constant/metal/materials/castIron",
        "constant/metal/fvModels", "constant/metal/momentumTransport",
        "constant/metal/g", "constant/metal/pRef",
        "constant/mold/physicalProperties",
        "constant/mold/materials/silica",
    ])
    return {
        "status": "C14_3D_FLUID_SOLID_NATIVE_FILESET_RENDERED_IN_MEMORY_ONLY",
        "files": [{
            "path": key,
            "source": "C14_ORIGINAL_BYTE_FOR_BYTE" if key in originals
                      else "C14_VALUES_3D_PATCH_ADAPTATION",
            "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        } for key, payload in sorted(files.items())],
        "files_total": len(files),
        "C14_metal_fluid": True,
        "C14_mold_solid": True,
        "C14_latentHeat_alpha1e_Cu_beta_kept": True,
        "Cp_to_Cv_substitution": False,
        "native_mesh_V4_T02_present": False,
        "native_pressure_reference_point_mapped": False,
        "native_phaseChange_metal_cellZone_mapped": False,
        "native_solver_run": False,
    }


def main() -> int:
    report = verify()
    fileset = sources_manifest()
    print(json.dumps({
        **report,
        **fileset,
        "3D_C14_fluid_model_materialized": False,
        "case_A_stage_completion_unchanged": True,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
