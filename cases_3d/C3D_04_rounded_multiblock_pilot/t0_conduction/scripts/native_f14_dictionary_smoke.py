#!/usr/bin/env python3
"""Native Foundation14 dictionary verification of C14-derived Case A T0.

Runs on GitHub Actions with actual Foundation14 installed. Checks all ten
generated files with foamDictionary. Does not read the laptop's native mesh.
No foamMultiRun execution, remeshing, CFD, or unsubstantiated physical result.
Uses temporary files only, never writes to original cases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

T0 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T0/"scripts"))
import prepare_case_a_t0 as engine

EXPECTED_FILES = {
    "0/metal/T", "0/mold/T",
    "constant/metal/physicalProperties",
    "constant/mold/physicalProperties",
    "system/controlDict", "system/fvSolution",
    "system/metal/fvSchemes", "system/metal/fvSolution",
    "system/mold/fvSchemes", "system/mold/fvSolution",
}


def inspect(environment_only: bool = False) -> dict:
    version = shutil.which("foamVersion")
    dictionary = shutil.which("foamDictionary")
    solver = shutil.which("foamMultiRun")
    if not (version and dictionary and solver):
        raise RuntimeError(
            "OpenFOAM Foundation14 executables missing: foamVersion, "
            "foamDictionary and foamMultiRun required."
        )
    v = subprocess.run(
        [version], capture_output=True, text=True, timeout=15, check=True
    )
    detected = (v.stdout + v.stderr).strip()
    if not detected.startswith("14") and "OpenFOAM-14" not in detected:
        raise RuntimeError("Wrong OpenFOAM version: " + repr(detected))
    if environment_only:
        return {"status": "FOUNDATION14_NATIVE_EXECUTABLES_PRESENT",
                "version": detected, "source_case_verified": False,
                "native_dictionary_parse": False, "CFD_executed": False}

    cfg_path = engine.INPUTS
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    problems = engine.validate(cfg)
    if problems:
        raise ValueError("C14 sourced T0 invalid: " + "; ".join(problems))
    source = engine.c14_source_gate(cfg)
    generated = engine.generate(cfg)
    if set(generated) != EXPECTED_FILES:
        raise ValueError(
            f"Expected exactly 10 known T0 files, got {sorted(generated)}"
        )

    result = {
        "schema": "C3D04_A_T0_F14_NATIVE_DICTIONARIES_V1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NATIVE_F14_DICTIONARY_SYNTAX_PASS_NOT_CFD",
        "foam_version": detected,
        "t0_sha256": hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
        "archived_C14_source_sha256": source["source_file_sha256"],
        "source_parity_comparisons": source["verified_scalar_comparisons"],
        "scope": "C3D04_A_T0_C14_TWO_SOLID_SURROGATE_ONLY",
        "native_C3D04_V4_T02_mesh_present_in_CI": False,
        "native_mesh_contact_verified_in_this_step": False,
        "actual_thermophysical_BC_runtime_initialized": False,
        "CFD_executed": False,
        "phase_change_verified": False,
        "grid_independence_verified": False,
        "dictionary_results": [],
    }

    with tempfile.TemporaryDirectory(prefix="C3D04_A_F14_DICT_SMOKE_") as tmp:
        root = Path(tmp)
        for relative, payload in generated.items():
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding="utf-8")
        for relative in sorted(generated):
            cmd = subprocess.run(
                [dictionary, str(root/relative)],
                cwd=root, capture_output=True, text=True,
                timeout=40, check=False,
            )
            result["dictionary_results"].append({
                "path": relative,
                "parsed_with_Foundation14_foamDictionary": cmd.returncode == 0
            })
            if cmd.returncode:
                detail = (cmd.stdout + "\n" + cmd.stderr).strip()[-2500:]
                raise RuntimeError(
                    f"Foundation14 rejected {relative}: {detail}. "
                    "No original native mesh or CFD was modified."
                )
    return result


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out", type=Path,
                     help="Optional brand-new JSON CI report path; never overwrite")
    cli.add_argument("--environment-only", action="store_true")
    args = cli.parse_args()
    result = inspect(environment_only=args.environment_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out = args.out.expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("x", encoding="utf-8") as f:
            json.dump(result, f, sort_keys=True, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
