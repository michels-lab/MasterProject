#!/usr/bin/env python3
"""Integrated Case A / C3D-04 T0 transient two-solid *numerical* preflight.

This module:
- validates real sourced material data, stage acknowledgement and BC hypothesis;
- reuses the previously accepted V4/T02 mesh, read-only;
- checks actual patch names/types, native checkMesh status/contact acceptance;
- builds nine Foundation14-oriented dictionaries IN MEMORY;
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

INPUTS = T0 / "T0_INPUTS.json"
SOURCE = Path.home() / "OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02"
OUTPUT = Path.home() / "OpenFOAM/C3D04_A_T0_CONDUCTION_01"
SCHEMA = "C3D04_A_T0_1"
PURPOSE = "TRANSIENT_TWO_SOLID_CONDUCTION_NUMERICAL_CHECK_ONLY_NOT_CAST_IRON_SOLIDIFICATION"
MODEL = "constIsoSolid_rhoConst_eConst_sensibleInternalEnergy"
BC = "ADIA_BC_EXTERNAL_PERFECT_THERMAL_CONTACT_UNVALIDATED_QUICKCUP"
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
        nonorth = simulation.get("nNonOrthogonalCorrectors")
        if type(nonorth) is not int or not 0 <= nonorth <= 20:
            errors.append("simulation.nNonOrthogonalCorrectors: explicit integer 0..20 required")
        for key in ("source_time_choices", "source_nonorth_choice", "source_energy_coupling_choice"):
            evidence = simulation.get(key)
            if not isinstance(evidence, str) or len(evidence.strip()) < 10:
                errors.append(f"simulation.{key}: documented numerical rationale required")
    metal = config.get("metal")
    mold = config.get("mold")
    if isinstance(metal, dict) and isinstance(mold, dict):
        a, b = metal.get("T_initial_K"), mold.get("T_initial_K")
        if positive(a) and positive(b) and a == b:
            errors.append("metal and mold T_initial_K must differ for the T0 transfer test")
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


def temperature(region: str, initial_K) -> str:
    lines = [
        header(f"0/{region}", "T", "volScalarField"),
        "dimensions [0 0 0 1 0 0 0];",
        f"internalField uniform {fmt(initial_K)};",
        "boundaryField", "{",
        '    #includeEtc "caseDicts/setConstraintTypes"',
    ]
    for patch in EXTERIOR[region]:
        lines += [
            f"    {patch}", "    {",
            "        type zeroGradient; // T0 insulated TEST, not measured air cooling",
            "    }",
        ]
    lines += [
        f"    {COUPLED[region]}", "    {",
        "        type coupledTemperature;",
        "        value $internalField;",
        "    }", "}",
    ]
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


def global_solution(energy_correctors: int) -> str:
    """Foundation14 foamMultiRun multi-region PIMPLE control (top-level)."""
    return header("system", "fvSolution") + (
        "PIMPLE\n{\n"
        "    nOuterCorrectors 1; // T0 numerical hypothesis, no flow\n"
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
            cfg["simulation"]["nEnergyCorrectors"]
        ),
    }
    for region in ("metal", "mold"):
        items[f"0/{region}/T"] = temperature(region, cfg[region]["T_initial_K"])
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
        "model": "THEORETICAL_ADIABATIC_TWO_CONSTANT_CV_SOLIDS_ONLY",
        "regional_heat_capacity_J_per_K": capacity,
        "total_heat_capacity_J_per_K": total,
        "ideal_equilibrium_K_no_heat_loss": eq,
        "energy_residual_equation": (
            "Cmetal*(Tmetal-Tmetal0)+Cmold*(Tmold-Tmold0)=0"
        ),
        "validation_status": "ANALYTICAL_TARGET_ONLY_NOT_CFD_OUTPUT",
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
            "source_rho": "SYNTHETIC_UNIT_TEST",
            "source_Cv": "SYNTHETIC_UNIT_TEST",
            "source_kappa": "SYNTHETIC_UNIT_TEST",
            "source_molWeight": "SYNTHETIC_UNIT_TEST",
            "source_T_initial": "SYNTHETIC_UNIT_TEST",
        })
    cfg["simulation"].update({
        "deltaT_s": 0.01, "endTime_s": 0.10,
        "writeEverySteps": 2, "nNonOrthogonalCorrectors": 2,
        "nEnergyCorrectors": 2,
        "source_time_choices": "SYNTHETIC_UNIT_TEST",
        "source_nonorth_choice": "SYNTHETIC_UNIT_TEST",
        "source_energy_coupling_choice": "SYNTHETIC_UNIT_TEST",
    })
    return cfg


def self_test():
    base = json.loads(INPUTS.read_text(encoding="utf-8"))
    errors = validate(base)
    assert len(errors) >= 15, "Null physical inputs must remain blocked"
    cfg = synthetic_fixture()
    assert validate(cfg, allow_synthetic_test=True) == []
    assert validate(cfg, allow_synthetic_test=False) != []
    files = generate(cfg)
    assert len(files) == 10
    assert "nEnergyCorrectors 2;" in files["system/fvSolution"]
    assert "application foamMultiRun;" in files["system/controlDict"]
    for region in ("metal", "mold"):
        field = files[f"0/{region}/T"]
        for patch in EXTERIOR[region] + (COUPLED[region],):
            assert patch in field
        assert "type coupledTemperature;" in field
        assert "type zeroGradient;" in field
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
    print("STATIC_INTEGRATED_T0_PASS: null data blocked; 10 files incl global PIMPLE; all native patch names; energy target; provenance; rejection regressions")
    print("STATIC_ONLY: no OpenFOAM, CFD or thermal case creation.")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, default=INPUTS)
    p.add_argument("--source", type=Path, default=SOURCE)
    p.add_argument("--out", type=Path, default=OUTPUT)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--materialize", action="store_true",
                   help="Explicitly copy native mesh and nine dictionaries to a brand-new isolated directory, NEVER run solver")
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
    evidence = native_case_gate(source)
    errors = validate(cfg)
    if errors:
        print("CASE_A_T0_BLOCKED_PENDING_REAL_INPUTS | native mesh/contact and real patch names verified:")
        for e in errors:
            print(" - " + e)
        print("No physical parameters invented. No materialization. No CFD.")
        return 3 if args.materialize else 0
    files = generate(cfg)
    energy = closed_t0_energy_target(
        cfg, evidence["native_volumes_m3_from_preserved_tsv"]
    )
    if not args.materialize:
        print(f"CASE_A_T0_CONFIG_AND_SOURCE_PRECHECK_OK: {len(files)} files renderable")
        print("IDEALIZED_T0_CLOSED_EQUILIBRIUM_K:",
              energy["ideal_equilibrium_K_no_heat_loss"],
              "| theoretical constant-Cv and adiabatic only, NOT CFD")
        print("No files written. No CFD. Native Foundation14 dictionary parse remains pending.")
        return 0
    materialize(source, dest, cfg, input_file, files, evidence)
    print(f"CASE_A_T0_MATERIALIZED_NOT_SOLVED: {dest}")
    print("Native Foundation14 dictionary syntax and coupled thermophysics must still be verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
