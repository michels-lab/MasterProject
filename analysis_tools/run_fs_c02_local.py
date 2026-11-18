#!/usr/bin/env python3
"""FS-C02: isolated provisional cast-iron/air VOF smoke case for Foundation 14.

Scientific status: no solidification, shrinkage, feeding, mold, or material
validation. Never edits B14, FS-C01, C3D-02, or any pre-existing run folder.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from run_fs_c01_local import validate_source, mesh_success, solver_success

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "freesurface" / "FS-C01"
B14_MATERIAL = (REPO / "cases_controlled_buoyancy" /
                "B14_topFixedFlux_explicitRef" / "constant" /
                "metal" / "materials" / "castIron")
CASE_ID = "FS-C02"
WIDTH, HEIGHT, DEPTH, METAL_HEIGHT = .04, .06, .01, .04
INITIAL_VOLUME = WIDTH * DEPTH * METAL_HEIGHT
DENSITY = 6820.0        # B14 rho0, NOT rho_s/rho_l or JMatPro
CV = 827.0              # B14 Cp used as constant-Cv smoke approximation
MU = .0055              # B14 mu, Pa s
PR = .14                # B14 Pr
SIGMA = 1.0             # PROVISIONAL N/m; NOT a validated Fe-air measurement

THERMO_METAL = """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    location "constant";
    object physicalProperties.metal;
}
thermoType
{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          eConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleInternalEnergy;
}
mixture
{
    specie
    {
        molWeight 55.845;
    }
    equationOfState
    {
        rho 6820;
    }
    thermodynamics
    {
        Cv 827;
        hf 0;
    }
    transport
    {
        mu 0.0055;
        Pr 0.14;
    }
}
"""

def check(condition: bool, explanation: str) -> None:
    if not condition:
        raise ValueError("FS-C02: " + explanation)

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace_once(content: str, original: str, replacement: str, label: str) -> str:
    check(content.count(original) == 1, f"unexpected {label} in FS-C01 baseline")
    return content.replace(original, replacement, 1)

def outside_repo(path: Path) -> None:
    # Output must be separate from the checkout (and therefore from all original cases).
    resolved = path.expanduser().resolve()
    base = REPO.resolve()
    check(resolved != base and base not in resolved.parents
          and resolved != Path.home().resolve(),
          "output must be outside the repository and not equal home")
    check("MasterProject" not in resolved.parts
          and "cases_3d" not in resolved.parts and "cases_controlled_buoyancy" not in resolved.parts
          and "FS_C01_RUNS" not in resolved.parts
          and "FS_C01_WORKTREE" not in resolved.parts,
          "refusing FS-C01/B14/C3D output namespace")

def validate_b14_reference() -> str:
    check(B14_MATERIAL.is_file() and not B14_MATERIAL.is_symlink(),
          "B14 material reference missing or symlinked")
    text = B14_MATERIAL.read_text(encoding="utf-8")
    for key, value in (("rho0", "6820"), ("Cp", "827"),
                       ("mu", "5.5e-03"), ("Pr", "0.14")):
        check(bool(re.search(r"\b"+key+r"\s+"+re.escape(value)+r"\s*;", text)),
              f"B14 source value {key} differs; do not silently guess")
    return digest(B14_MATERIAL)

def write_record(path: Path, record: dict) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(record, indent=2, ensure_ascii=False)+"\n")
    temp.replace(path)

def stage(out: Path) -> tuple[Path, dict]:
    validate_source(SOURCE)
    b14_sha = validate_b14_reference()
    out = out.expanduser().resolve()
    outside_repo(out)
    check(not out.exists(), "refusing to overwrite pre-existing run directory")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()  # never overwrite any existing case or result
    case = out / CASE_ID
    case.mkdir()
    for directory in ("0", "constant", "system"):
        shutil.copytree(SOURCE / directory, case / directory)

    alpha = case / "0" / "alpha.water"
    new_alpha = replace_once(alpha.read_text(), "object alpha.water;",
                             "object alpha.metal;", "alpha identifier")
    new_alpha = replace_once(new_alpha, "waterColumn", "metalColumn", "VOF metal zone")
    alpha.unlink()
    (case / "0" / "alpha.metal").write_text(new_alpha)

    solution = case / "system" / "fvSolution"
    solution.write_text(replace_once(solution.read_text(), '"alpha.water.*"',
                                     '"alpha.metal.*"', "fvSolution alpha"))

    phases = case / "constant" / "phaseProperties"
    data = replace_once(phases.read_text(), "phases (water air);",
                        "phases (metal air);", "phase list")
    data, count = re.subn(
        r"sigma\s*\{\s*type\s+liquidProperties;\s*phase\s+water;\s*\}",
        "sigma\n{\n    type constant;\n    sigma 1.0;\n}", data,
    )
    check(count == 1, "unknown phaseProperties sigma model")
    phases.write_text(data)

    old_thermo = case / "constant" / "physicalProperties.water"
    check(old_thermo.is_file(), "missing water thermophysics to replace")
    old_thermo.unlink()
    (case / "constant" / "physicalProperties.metal").write_text(THERMO_METAL)

    temp = case / "0" / "T"
    t_content = replace_once(temp.read_text(), "internalField   uniform 300;",
                             """internalField
{
    type zonal;
    defaultValue 300;
    zones
    {
        metalColumn
        {
            type box;
            box (0 0 -1) (0.04 0.04 1);
            value 1500;
        }
    }
}""", "initial hot metal T")
    t_content = replace_once(t_content, "inletValue      $internalField;",
                             "inletValue      uniform 300;", "atmospheric T inlet")
    temp.write_text(t_content)

    control = case / "system" / "controlDict"
    data = replace_once(control.read_text(), "waterVolume", "metalVolume", "volume function")
    data = replace_once(data, "fields (alpha.water);",
                        "fields (alpha.metal);", "volume field")
    check("writeFields false;" in data, "Foundation 14 writeFields keyword absent")
    control.write_text(data)

    input_paths = sorted(p for directory in ("0", "constant", "system")
                         for p in (case / directory).rglob("*") if p.is_file())
    expected = {p.relative_to(case).as_posix(): digest(p) for p in input_paths}
    check(len(expected) == 20, "expected 20 solver inputs in provisional FS-C02")
    check(not any("water" in key for key in expected), "water file remains in FS-C02")
    check("phases (metal air)" in phases.read_text(), "missing metal/air phase identity")

    manifest = {
        "schema": "masterproject-fs-c02-metal-air-smoke-v1",
        "case_id": CASE_ID,
        "status": "PREPARED_NOT_MESHED_OR_RUN",
        "source_fs_c01_manifest_sha256": digest(SOURCE / "BFS01_MANIFEST.json"),
        "b14_material_source": B14_MATERIAL.relative_to(REPO).as_posix(),
        "b14_material_sha256": b14_sha,
        "generated_input_sha256": expected,
        "initial_metal_volume_m3": INITIAL_VOLUME,
        "reference_metal_density_kg_m3": DENSITY,
        "reference_metal_mass_kg": INITIAL_VOLUME * DENSITY,
        "physical_assumptions": {
            "metal_air_vof": True,
            "metal_density": "rhoConst 6820 kg/m3, B14 reference, NO shrinkage",
            "energy": "nonisothermal smoke; Cv=827 J/(kg K) approximates B14 Cp",
            "surface_tension": "1.0 N/m PROVISIONAL UNSOURCED",
            "initial_temperature": "metal 1500 K, air 300 K (zonal)",
            "turbulence": "unmodified FS-C01 RAS and VoFTurbulenceDamping, not calibrated for iron",
            "solidification": False,
            "latent_heat": False,
            "mold": False,
            "contraction": False,
            "porosity": False,
        },
    }
    write_record(case / "FS-C02_MANIFEST.json", manifest)
    record = {
        "case_id": CASE_ID,
        "run_directory": str(out),
        "source_case": "FS-C01 frozen inputs + B14 property reference ONLY",
        "status": "STAGED_NO_CFD_YET",
        "solver_tested_on_real_openfoam": False,
        "mass_verified": False,
        "contraction_modelled": False,
        "stages": [],
    }
    write_record(out / "FS-C02_RUN_STATUS.json", record)
    (out / "logs").mkdir()
    return case, record

def check_runtime() -> None:
    check(os.environ.get("WM_PROJECT_VERSION") == "14",
          "OpenFOAM Foundation 14 environment must be activated")
    for command in ("blockMesh", "checkMesh", "foamRun"):
        check(shutil.which(command) is not None, command + " not in PATH")

def execute(out: Path, case: Path, record: dict) -> None:
    for label, args, validator in (
        ("blockMesh", ["blockMesh"], lambda text: "FOAM FATAL" not in text),
        ("checkMesh", ["checkMesh", "-allGeometry", "-allTopology"], mesh_success),
        ("foamRun", ["foamRun"], solver_success),
    ):
        logfile = out / "logs" / ("FS-C02_" + label + ".log")
        print("FS-C02 [" + label + "] " + str(logfile), flush=True)
        with logfile.open("w", encoding="utf-8") as f:
            completed = subprocess.run(args, cwd=case, stdout=f,
                                       stderr=subprocess.STDOUT, check=False)
        log = logfile.read_text(encoding="utf-8", errors="replace")
        passed = completed.returncode == 0 and bool(validator(log))
        record["stages"].append({"stage": label, "returncode": completed.returncode,
                                 "gate_passed": passed, "log": str(logfile)})
        record["status"] = ("PASSED_" if passed else "BLOCKED_") + label.upper()
        write_record(out / "FS-C02_RUN_STATUS.json", record)
        check(passed, label + " gate failed; inspect " + str(logfile))
    record["solver_tested_on_real_openfoam"] = True
    record["status"] = "SOLVER_FINISHED_PHYSICS_NOT_VALIDATED"
    write_record(out / "FS-C02_RUN_STATUS.json", record)
    print("FS-C02 foamRun completed. MASS, INTERFACE, THERMAL PHYSICS, SHRINKAGE UNVERIFIED.")

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--stage-only", action="store_true",
                        help="create a provisional FS-C02 case without running OpenFOAM")
    args = parser.parse_args(argv)
    name = "FS-C02_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    out = args.out or Path.home() / "OpenFOAM" / "FS_C02_RUNS" / name
    try:
        validate_source(SOURCE)
        validate_b14_reference()
        if not args.stage_only:
            check_runtime()
        case, record = stage(out)
        print("FS-C02 isolated new case staged: " + str(case))
        if args.stage_only:
            print("FS-C02 STAGED ONLY; no metal-air CFD executed.")
        else:
            execute(out, case, record)
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("FS-C02 BLOCKED: " + str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
