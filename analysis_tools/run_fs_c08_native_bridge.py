#!/usr/bin/env python3
"""Compile Foundation14 field inventory and audit preserved FS-C07 without CFD.

One command for the researcher's existing FS_C08_WORKTREE / WSL. This creates
build products only in FS-C08 and evidence only outside FS-C07, NEVER runs
foamMultiRun, writes native alpha fields, adjusts physical inputs or claims
conservative shrinkage 3D.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from verify_fs_c08_openfoam_inventory import verify_native_log

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "freesurface/FS-C08_conservative_phase_mass/native_openfoam"
SNAPSHOTS = ("0.2", "0.4", "1")
FIELDS = ("alpha.metal", "alpha.metal.solid")
SCIENTIFIC_TIMES = (0.2, 0.4, 1.0)


def require(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError("FS-C08 NATIVE BRIDGE BLOCKED: " + why)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for buf in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def case_inputs(case: Path) -> dict[str, str]:
    require(case.is_absolute() and case.is_dir()
            and case.name.startswith("FS_C07_THERMAL_"),
            "requires exact external existing FS_C07_THERMAL_* case")
    require(ROOT != case and ROOT not in case.parents,
            "research source and Git worktree must be separate")
    require((case / "constant/fluid/polyMesh/points").is_file(),
            "native fluid polyMesh points missing")
    checksums = {}
    for t in SNAPSHOTS:
        for field in FIELDS:
            f = case / t / "fluid" / field
            require(f.is_file() and not f.is_symlink(),
                    "missing or linked original field: " + str(f))
            checksums[f"{t}/fluid/{field}"] = digest(f)
    return checksums


def compiler_error_excerpt(log: Path, *, limit: int = 8) -> str:
    """Extract real compiler diagnostics instead of guessing from exit code."""
    if not log.is_file():
        return "(compiler log unavailable)"
    text = log.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return "(compiler log empty)"
    lines = text.splitlines()
    errors = [
        line.strip() for line in lines
        if re.search(
            r"fatal error:|(?<!\w)error:|undefined reference"
            r"|No rule to make target|\*\*\*.*Error [0-9]+",
            line, re.IGNORECASE,
        )
    ]
    chosen = errors[:limit] if errors else lines[-limit:]
    return "\n".join(chosen)


def execute_checked(
    argv: list[str], cwd: Path, timeout_seconds: int, log: Path,
) -> subprocess.CompletedProcess:
    with log.open("w", encoding="utf-8") as sink:
        try:
            run = subprocess.run(
                argv, cwd=str(cwd), stdout=sink, stderr=subprocess.STDOUT,
                text=True, timeout=timeout_seconds, check=False,
            )
        except subprocess.TimeoutExpired:
            raise ValueError(
                "Command timeout; see preserved log " + str(log)
            )
    if run.returncode != 0:
        excerpt = compiler_error_excerpt(log)
        raise ValueError(
            f"External command returned {run.returncode}; preserved log: {log}"
            f"\nFirst compiler/error diagnostics (or last log lines):\n{excerpt}"
        )
    return run


def run(case: Path, output_root: Path | None = None) -> dict:
    case = case.expanduser().resolve()
    hashes_before = case_inputs(case)
    require(NATIVE.is_dir()
            and (NATIVE / "Make/files").is_file()
            and (NATIVE / "Make/options").is_file(),
            "missing versioned Foundation14 wmake sources")
    require(os.environ.get("WM_PROJECT_VERSION") == "14",
            "source OpenFOAM Foundation14 first; WM_PROJECT_VERSION must equal 14")
    require(shutil.which("wmake") is not None,
            "wmake is not in PATH (Foundation14 environment not loaded)")
    bin_dir = os.environ.get("FOAM_USER_APPBIN")
    require(bool(bin_dir), "FOAM_USER_APPBIN environment variable missing")
    binary = Path(bin_dir).expanduser().resolve() / "fsC08NativeInventory"
    if output_root is None:
        output_root = Path.home() / "OpenFOAM" / "FS_C08_DIAGNOSTICS"
    output_root = output_root.expanduser().resolve()
    require(case != output_root and case not in output_root.parents
            and output_root not in case.parents,
            "diagnostic folder must be outside preserved FS-C07 case")
    run_dir = output_root / (
        "FS_C08_NATIVE_FIELD_BRIDGE_"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_" + uuid.uuid4().hex[:8]
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    build_log = run_dir / "wmake.log"
    native_log = run_dir / "fsC08NativeInventory.log"
    report_file = run_dir / "FS_C08_NATIVE_BRIDGE_REPORT.json"
    report = {
        "schema": "masterproject-fs-c08-native-bridge-evidence-v1",
        "source_FS_C07_case": str(case),
        "source_Git_worktree": str(ROOT),
        "native_utility": str(binary),
        "source_input_SHA256_before": hashes_before,
        "source_input_SHA256_after": None,
        "source_changed": None,
        "wmake_compiled": False,
        "native_field_bridge_executed": False,
        "independent_parity_gate_pass": False,
        "OpenFOAM_CFD_solver_executed": False,
        "OpenFOAM_CFD_pressure_solved": False,
        "physical_shrinkage_implemented": False,
        "physical_shrinkage_validated": False,
        "status": "FS_C08_BRIDGE_STAGED",
        "last_error": None,
        "diagnostic_folder": str(run_dir),
        "wmake_log_path": str(build_log),
        "native_stdout_path": str(native_log),
    }
    try:
        report_file.write_text(json.dumps(report, indent=2) + "\n")
        execute_checked(["wmake"], NATIVE, 240, build_log)
        report["wmake_compiled"] = True
        require(binary.is_file(),
                "wmake reported success but native inventory binary not found")
        execute_checked(
            [
                str(binary), "-case", str(case), "-region", "fluid",
                "-time", "0.2,0.4,1",
            ],
            ROOT, 180, native_log,
        )
        report["native_field_bridge_executed"] = True
        evidence = verify_native_log(
            native_log.read_text(encoding="utf-8"), SCIENTIFIC_TIMES
        )
        report["native_result"] = evidence
        report["independent_parity_gate_pass"] = True
        report["status"] = "FS_C08_NATIVE_FVMESH_READ_ONLY_BRIDGE_PASS__NO_CFD"
    except (ValueError, OSError) as err:
        report["status"] = "FS_C08_NATIVE_BRIDGE_INCOMPLETE_EVIDENCE_PRESERVED"
        report["last_error"] = str(err)
    finally:
        try:
            hashes_after = case_inputs(case)
            report["source_input_SHA256_after"] = hashes_after
            report["source_changed"] = hashes_before != hashes_after
            if report["source_changed"]:
                report["status"] = "FS_C08_SOURCE_HASH_CHANGED_CRITICAL_BLOCK"
                report["last_error"] = (
                    "Saved FS-C07 native field hashes differ; preservation gate failed"
                )
        except (ValueError, OSError) as err:
            report["status"] = "FS_C08_SOURCE_INTEGRITY_RECHECK_BLOCK"
            report["last_error"] = str(err)
        report_file.write_text(json.dumps(report, indent=2) + "\n")
        print("FS-C08 NATIVE BRIDGE REPORT:", report_file)
        print("FS-C08 STATUS:", report["status"])
        if report["last_error"]:
            print("FS-C08 DIAGNOSTIC:", report["last_error"], file=sys.stderr)
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", type=Path, required=True,
                    help="EXISTING preserved FS-C07 run, not the Git source")
    ap.add_argument("--output-root", type=Path, default=None)
    args = ap.parse_args(argv)
    try:
        r = run(args.case, args.output_root)
    except (ValueError, OSError) as err:
        print("FS-C08 BRIDGE PREFLIGHT BLOCKED:", err, file=sys.stderr)
        return 2
    return 0 if r["status"] == "FS_C08_NATIVE_FVMESH_READ_ONLY_BRIDGE_PASS__NO_CFD" else 2


if __name__ == "__main__":
    raise SystemExit(main())
