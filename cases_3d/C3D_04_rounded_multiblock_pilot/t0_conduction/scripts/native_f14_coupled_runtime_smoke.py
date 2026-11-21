#!/usr/bin/env python3
"""C3D-04 A: REAL Foundation14 coupled two-solid smoke on a SYNTHETIC mesh.

Use exactly the production Case A ten T0 dictionaries derived from C14.
Build two new 1-cell cubes with a single reciprocal mappedWall interface,
initialize F14 solid thermophysics and run only 2 time steps with foamMultiRun.

This CI gate tests runtime compatibility of native BC, solvers and coupling.
It DOES NOT use the accepted V4/T02 mesh, verify numerical convergence,
simulate cast-iron solidification or count as an executed case-A milestone.
Never run blockMesh or the solver against the researcher's reference mesh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prepare_case_a_t0 as engine

SCOPE = "C3D04_A_SYNTHETIC_TWO_CUBE_F14_RUNTIME_ONLY"
FLOAT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
FACES = {
    "west": "(0 4 7 3)",
    "east": "(1 2 6 5)",
    "south": "(0 1 5 4)",
    "north": "(3 7 6 2)",
    "floor": "(0 3 2 1)",
    "roof": "(4 5 6 7)",
}
PATCHES = {
    "metal": {
        "metalTop": ("wall", ("west", "south", "north", "floor", "roof"), None),
        "metal_to_mold": ("mappedWall", ("east",), "mold_to_metal"),
    },
    "mold": {
        "mold_to_metal": ("mappedWall", ("west",), "metal_to_mold"),
        "moldTop": ("wall", ("north",), None),
        "moldExterior": ("wall", ("east",), None),
        "moldBottom": ("wall", ("south",), None),
        "moldRecessWall": ("wall", ("floor",), None),
        "moldRecessRoof": ("wall", ("roof",), None),
    },
}


def block_mesh_dict(region: str) -> str:
    if region not in PATCHES:
        raise ValueError("Unrecognized Case A region")
    x = 0 if region == "metal" else 1
    vertices = "\n".join(
        f"    ({x+dx} {y} {z})"
        for dx, y, z in (
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
        )
    )
    entries = []
    for name, (kind, faces, neighbour) in PATCHES[region].items():
        mapping = (
            f"        sampleRegion {'mold' if region == 'metal' else 'metal'};\n"
            f"        samplePatch {neighbour};\n"
            "        sampleMode nearestPatchFace;\n"
            if neighbour else ""
        )
        entries.append(
            "    " + name + "\n    {\n"
            + f"        type {kind};\n"
            + mapping
            + "        faces\n        (\n"
            + "\n".join("            " + FACES[face] for face in faces)
            + "\n        );\n    }"
        )
    return (
        "FoamFile\n{\n    version 2.0;\n    format ascii;\n"
        f'    class dictionary;\n    location "system/{region}";\n'
        "    object blockMeshDict;\n}\n"
        "// TWO ONE-CELL SYNTHETIC CUBES; NOT C3D04 V4/T02.\n"
        "scale 0.01;\n"
        "vertices\n(\n" + vertices + "\n);\n"
        "blocks ( hex (0 1 2 3 4 5 6 7) (1 1 1) simpleGrading (1 1 1) );\n"
        "edges ();\n"
        "boundary\n(\n" + "\n".join(entries) + "\n);\n"
        "mergePatchPairs ();\n"
    )


def shorten_for_runtime(control: str) -> str:
    """Change ONLY the synthetic copies of timestep and output policies."""
    rules = [
        (r"(?m)^\s*endTime\s+10\s*;", "endTime 0.002;"),
        (r"(?m)^\s*deltaT\s+0\.001\s*;", "deltaT 0.001;"),
        (r"(?m)^\s*writeInterval\s+100\s*;", "writeInterval 1;"),
    ]
    for pattern, replacement in rules:
        control, count = re.subn(pattern, replacement, control)
        if count != 1:
            raise ValueError("Unexpected real C14-derived solver control: " + pattern)
    if "regionSolvers" not in control:
        raise ValueError("Missing native regionSolvers declaration")
    return control


def native_field_temperature(path: Path) -> float:
    text = path.read_text(encoding="utf-8")
    if not re.search(r"\bclass\s+volScalarField\s*;", text) or not re.search(
        r"\bobject\s+T\s*;", text
    ):
        raise ValueError("Native output is not a temperature volScalarField: " + str(path))
    match = re.search(r"\binternalField\s+uniform\s+(" + FLOAT + r")\s*;", text)
    if not match:
        match = re.search(
            r"\binternalField\s+nonuniform\s+List<scalar>\s+1\s*"
            r"\(\s*(" + FLOAT + r")\s*\)", text, re.S
        )
    if not match:
        raise ValueError("Native one-cell temperature data absent: " + str(path))
    value = float(match.group(1))
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Nonphysical/unreadable native T field: " + str(path))
    return value


def native_env() -> dict:
    version = os.environ.get("WM_PROJECT_VERSION", "")
    required = ("blockMesh", "foamDictionary", "foamMultiRun")
    missing = [name for name in required if shutil.which(name) is None]
    if version != "14" or missing:
        raise RuntimeError(
            f"Foundation14 only: WM_PROJECT_VERSION={version!r}; missing {missing}"
        )
    return {"WM_PROJECT_VERSION": version, "executables": list(required)}


def run_command(cmd: list[str], cwd: Path, log_name: str, seconds: int) -> dict:
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        errors="replace", timeout=seconds, check=False,
    )
    log = cwd/log_name
    log.write_text(
        "COMMAND: " + " ".join(cmd) + "\nEXIT: " + str(result.returncode)
        + "\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr,
        encoding="utf-8",
    )
    if result.returncode != 0 or "FOAM FATAL" in (result.stdout+result.stderr):
        raise RuntimeError(
            "Native Foundation14 command failed (" + log_name
            + "); preserved log at " + str(log) + "; tail: "
            + (result.stdout + result.stderr)[-2000:]
        )
    return {
        "log_file": log_name,
        "sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "returncode": result.returncode,
    }


def run(out: Path) -> dict:
    out = out.expanduser().resolve()
    if out.exists() or out.is_symlink():
        raise FileExistsError("Refusing to overwrite synthetic native run: " + str(out))
    env = native_env()
    cfg = json.loads(engine.INPUTS.read_text(encoding="utf-8"))
    errors = engine.validate(cfg)
    if errors:
        raise ValueError("Real C14-sourced T0 config invalid: " + "; ".join(errors))
    provenance = engine.c14_source_gate(cfg)
    files = engine.generate(cfg)
    if len(files) != 10:
        raise ValueError("Case A production generator must yield exactly ten files")
    files["system/controlDict"] = shorten_for_runtime(files["system/controlDict"])
    out.mkdir(parents=True, exist_ok=False)
    record = {
        "schema": "C3D04_A_F14_SYNTHETIC_COUPLED_RUNTIME_V1",
        "scope": SCOPE,
        "status": "SYNTHETIC_NATIVE_RUNTIME_IN_PROGRESS",
        "actual_V4_T02_present_or_modified": False,
        "research_case_CFD_executed": False,
        "case_A_stage06_WSL_verified": False,
        "phase_change_or_cast_iron_physics_validated": False,
        "mass_or_energy_balance_validated": False,
        "grid_independence_validated": False,
        "foundation14": env,
        "archived_C14_source_sha256": provenance["source_file_sha256"],
        "generated_file_count": 10,
        "native_logs": [],
        "native_temperature_snapshots": [],
    }
    report = out/"C3D04_A_SYNTHETIC_NATIVE_REPORT.json"
    try:
        for relative, content in files.items():
            path = out/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        for region in ("metal", "mold"):
            path = out/"system"/region/"blockMeshDict"
            path.write_text(block_mesh_dict(region), encoding="utf-8")
        for region in ("metal", "mold"):
            record["native_logs"].append(
                run_command(
                    ["blockMesh", "-case", str(out), "-region", region,
                     "-dict", str(out/"system"/region/"blockMeshDict")],
                    out, f"log.blockMesh.{region}", 120,
                )
            )
            for filename in ("points", "faces", "owner", "neighbour", "boundary"):
                if not (out/"constant"/region/"polyMesh"/filename).is_file():
                    raise RuntimeError(f"Region {region} missing native polyMesh/{filename}")
        for relative in sorted(files):
            record["native_logs"].append(
                run_command(
                    ["foamDictionary", str(out/relative)],
                    out, "log.dict." + relative.replace("/", "."), 30,
                )
            )
        record["native_logs"].append(
            run_command(["foamMultiRun", "-case", str(out)],
                        out, "log.foamMultiRun", 180)
        )
        full_log = (out/"log.foamMultiRun").read_text(encoding="utf-8")
        if not re.search(r"(?m)^\s*End\s*$", full_log):
            raise RuntimeError("Native solver log does not end with End")
        steps = re.findall(r"(?m)^\s*Time\s*=\s*(" + FLOAT + r")\s*s?\s*$", full_log)
        if len(steps) < 2 or not any(math.isclose(float(t), 0.002, abs_tol=1e-10)
                                      for t in steps):
            raise RuntimeError("Native two-step runtime did not reach 0.002 s")
        for time in ("0.001", "0.002"):
            item = {"time_s": float(time)}
            for region in ("metal", "mold"):
                path = out/time/region/"T"
                item[region+"_T_K"] = native_field_temperature(path)
                item[region+"_T_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            record["native_temperature_snapshots"].append(item)
        record["status"] = "NATIVE_F14_TWO_SOLID_SYNTHETIC_RUNTIME_PASS_NOT_V4_T02"
        return record
    except Exception as exc:
        record["status"] = "BLOCKED_SYNTHETIC_NATIVE_RUNTIME_PRESERVE_LOGS"
        record["failure"] = str(exc)
        raise
    finally:
        report.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print("Case A synthetic Foundation14 evidence:", report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True,
                        help="Brand-new disposable synthetic case directory")
    args = parser.parse_args()
    try:
        result = run(args.out)
        print(json.dumps({
            "status": result["status"],
            "snapshots": result["native_temperature_snapshots"],
            "research_case_CFD_executed": False,
        }, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("CASE_A_SYNTHETIC_RUNTIME_BLOCKED:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
