#!/usr/bin/env python3
"""Safe materializer for T0 coupled two-solid transient conduction, OF Foundation 14.

No execution of foamMultiRun; source CAD HEX8 reference is NEVER modified.
Refuses placeholder/null material inputs, absent citations and prior destination.
Independent native geometry/patch acceptance is performed by shell runner.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import re
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = HERE / "T0_INPUTS.json"
SOURCE = Path.home() / "OpenFOAM" / "C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
OUTPUT = Path.home() / "OpenFOAM" / "C3D05_T0_CONDUCTION_01"
FIELDS = ("rho_kg_m3", "Cv_J_kg_K", "kappa_W_m_K", "molWeight_g_mol", "T_initial_K")
ACK = "T0_IS_NOT_CAST_IRON_PHYSICAL_VALIDATION"
SCHEMA = "C3D05_T0_1"
BC = "ALL_EXTERNAL_ADIABATIC_IDEAL_METAL_MOLD_CONTACT"


def validate(config: dict) -> list[str]:
    """Return each missing or invalid value; strict gating, no defaults."""
    errors = []
    if not isinstance(config, dict):
        return ["root: must be JSON object"]
    if config.get("schema") != SCHEMA:
        errors.append("schema: expected " + SCHEMA)
    if config.get("acknowledgement") != ACK:
        errors.append("acknowledgement: explicit T0_NOT_PHYSICALLY_VALIDATED required")
    if config.get("thermal_BC_hypothesis") != BC:
        errors.append("thermal_BC_hypothesis: unexpected boundary model")
    if config.get("material_model") != "constIsoSolid_rhoConst_eConst_sensibleInternalEnergy":
        errors.append("material_model: unexpected Foundation14 model")
    if config.get("purpose") != "T0_TRANSIENT_TWO_SOLID_NUMERICAL_VERIFICATION_NOT_CAST_IRON_SOLIDIFICATION":
        errors.append("purpose: cannot treat numerical T0 as a casting result")
    for region in ("metal", "mold"):
        group = config.get(region)
        if not isinstance(group, dict):
            errors.append(f"{region}: expected object")
            continue
        for field in FIELDS:
            value = group.get(field)
            if (type(value) not in (float, int) or not math.isfinite(value)
                    or value <= 0):
                errors.append(f"{region}.{field}: positive SI number required, got {value!r}")
            evidence = group.get("source_" + field.split("_")[0])
            if not isinstance(evidence, str) or len(evidence.strip()) < 8:
                errors.append(f"{region}.source_{field.split('_')[0]}: cite provenance and model assumption")
    sim = config.get("simulation")
    if not isinstance(sim, dict):
        errors.append("simulation: expected object")
    else:
        for key in ("deltaT_s", "endTime_s"):
            val = sim.get(key)
            if type(val) not in (float, int) or not math.isfinite(val) or val <= 0:
                errors.append(f"simulation.{key}: positive numeric seconds required")
        dt, end = sim.get("deltaT_s"), sim.get("endTime_s")
        if (type(dt) in (int, float) and type(end) in (int, float)
                and math.isfinite(dt) and math.isfinite(end) and end <= dt):
            errors.append("simulation.endTime_s must be > deltaT_s")
        steps = sim.get("writeEverySteps")
        if type(steps) is not int or steps <= 0:
            errors.append("simulation.writeEverySteps: positive integer required")
        if not isinstance(sim.get("source_time_choices"), str) or len(sim["source_time_choices"].strip()) < 8:
            errors.append("simulation.source_time_choices: document proposed numerical steps")
    for region in ("metal", "mold"):
        if isinstance(config.get(region), dict):
            group = config[region]
            # No two-solid energy exchange without a temperature difference.
            if region == "mold" and isinstance(config.get("metal"), dict):
                t1, t2 = config["metal"].get("T_initial_K"), group.get("T_initial_K")
                if (type(t1) in (int, float) and type(t2) in (int, float)
                        and t1 == t2):
                    errors.append("metal and mold T_initial_K must differ for T0 coupling test")
    return errors


def render(template: str, values: dict[str, str]) -> str:
    names = set(re.findall(r"\{\{([A-Z_]+)\}\}", template))
    if names != set(values):
        raise ValueError(f"Template placeholders {sorted(names)} differ from values {sorted(values)}")
    output = template
    for key, value in values.items():
        output = output.replace("{{" + key + "}}", value)
    if "{{" in output or "}}" in output:
        raise ValueError("Unresolved placeholder, no invalid OpenFOAM case written")
    return output


def fmt(value: int | float) -> str:
    if type(value) is int:
        return str(value)
    return format(value, ".12g")


def file_map(cfg: dict) -> dict[str, str]:
    files = {}
    for region in ("metal", "mold"):
        mat = cfg[region]
        material = {
            "MOL_WEIGHT": fmt(mat["molWeight_g_mol"]),
            "RHO": fmt(mat["rho_kg_m3"]),
            "KAPPA": fmt(mat["kappa_W_m_K"]),
            "CV": fmt(mat["Cv_J_kg_K"]),
        }
        files[f"constant/{region}/physicalProperties"] = render(
            (HERE / f"templates/constant/{region}/physicalProperties.tpl").read_text(),
            material
        )
        files[f"0/{region}/T"] = render(
            (HERE / f"templates/0/{region}/T.tpl").read_text(),
            {"T_INITIAL": fmt(mat["T_initial_K"])}
        )
        for name in ("fvSchemes", "fvSolution"):
            files[f"system/{region}/{name}"] = render(
                (HERE / f"templates/system/{region}/{name}.tpl").read_text(), {}
            )
    t = cfg["simulation"]
    files["system/controlDict"] = render(
        (HERE / "templates/system/controlDict.tpl").read_text(),
        {
            "END_TIME": fmt(t["endTime_s"]),
            "DELTA_T": fmt(t["deltaT_s"]),
            "WRITE_STEPS": fmt(t["writeEverySteps"]),
        }
    )
    return files


def check_source(source: Path) -> None:
    for region in ("metal", "mold"):
        poly = source / "constant" / region / "polyMesh"
        for file in ("points", "faces", "owner", "neighbour", "boundary"):
            if not (poly / file).is_file():
                raise FileNotFoundError(f"Missing accepted native source mesh {poly / file}")
    for f in ("STEP_CAD_AUDIT.json", "CONTACT_AREA_REPORT.json", "NATIVE_BUILD_STATUS.txt"):
        if not (source / f).is_file():
            raise FileNotFoundError(f"Missing primary source evidence {source / f}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--out", type=Path, default=OUTPUT)
    p.add_argument("--check-only", action="store_true",
                   help="Validate templates and parameter evidence; write NOTHING")
    args = p.parse_args()
    if not args.inputs.is_file():
        p.error(f"No input parameter JSON: {args.inputs}")
    cfg = json.loads(args.inputs.read_text(encoding="utf-8"))
    missing = validate(cfg)
    if missing:
        print("T0_BLOCKED_MISSING_PHYSICAL_INPUTS_OR_EVIDENCE — NO CFD; NO NEW CASE:")
        for value in missing:
            print("  - " + value)
        return 3
    source = args.source.expanduser().resolve()
    output = args.out.expanduser().resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("T0 output must be independent of accepted source geometry")
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Never overwrite an existing T0 case: {output}")
    check_source(source)
    files = file_map(cfg)
    if args.check_only:
        print("T0_INPUTS_AND_TEMPLATE_VALIDATED | source meshes exist | NO FILES WRITTEN | NO CFD")
        return 0
    # All logical/material/template checks above completed before creating output.
    output.mkdir(parents=True, exist_ok=False)
    for region in ("metal", "mold"):
        shutil.copytree(source / "constant" / region / "polyMesh",
                        output / "constant" / region / "polyMesh")
    for relative_path, value in files.items():
        destination = output / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            stream.write(value)
    proof = {
        "T0_status": "PREPARED_NOT_EXECUTED_NEEDS_NATIVE_FOAM_VALIDATION",
        "original_native_mesh": str(source),
        "output": str(output),
        "mesh_independence": False,
        "physics_validated": False,
        "no_solver_executed": True,
        "boundary_hypothesis": BC,
        "temperature_and_material_sources": cfg,
        "input_sha256": sha256(args.inputs.read_bytes()).hexdigest(),
        "mesh_components": ["metal", "mold"],
        "mesh_is_copied_not_symlinked": True,
        "expected_solver": "foamMultiRun",
        "expected_regionSolvers": {"metal": "solid", "mold": "solid"},
    }
    with (output / "T0_PREPARATION_REPORT.json").open("x", encoding="utf-8") as s:
        json.dump(proof, s, indent=2, ensure_ascii=False)
        s.write("\n")
    print(f"T0_PREPARED_NO_SOLVER: {output}")
    print("BLOCKED_FOR_CFD pending native dictionary / boundary / thermophysics checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
