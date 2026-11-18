#!/usr/bin/env python3
"""Isolated Ubuntu/OpenFOAM Foundation 14 runner for FS-C01 only.

This runs the WATER/AIR free-surface analogue B-FS-01, never C3D-02, B14,
C14, molten iron, CHT, shrinkage, feeding or porosity. No CFD runs in CI.
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

REPO = Path(__file__).resolve().parents[1]
SOURCE_CASE = REPO / "freesurface" / "FS-C01"
CASE_ID = "FS-C01"
EXPECTED_SCHEMA = "quickcup-bfs01-hydro-analogue-v1"
EXPECTED_FLUID = "WATER_AIR_ANALOGUE_NOT_MOLTEN_IRON"
INPUT_DIRS = ("0", "constant", "system")
VOLUME_AUDITOR = REPO / "analysis_tools" / "granada_bfs01_vof_benchmark.py"


class FSC01Error(ValueError):
    """Fail closed without altering original cases or claiming CFD success."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FSC01Error(message)


def within(path: Path, parent: Path) -> bool:
    path, parent = path.resolve(), parent.resolve()
    return path == parent or parent in path.parents


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_source(case: Path = SOURCE_CASE) -> dict:
    """Reject mismatched identity, modified inputs and CFD outputs in source."""
    require(case.is_dir() and not case.is_symlink(), "FS-C01 source directory missing or symlinked")
    manifest_file = case / "BFS01_MANIFEST.json"
    require(manifest_file.is_file() and not manifest_file.is_symlink(),
            "FS-C01 manifest missing or symlinked")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    require(manifest.get("schema") == EXPECTED_SCHEMA, "wrong FS-C01 schema")
    require(manifest.get("fluid_identity") == EXPECTED_FLUID, "not the FS-C01 water-air analogue")
    require(manifest.get("status") == "PREPARED_NOT_MESHED_OR_RUN",
            "source FS-C01 status changed; manual review required")
    physics = manifest.get("physics", {})
    require(physics.get("metal") is False and physics.get("shrinkage") is False
            and physics.get("solidification") is False,
            "source physics not permitted for FS-C01")
    expected = manifest.get("generated_sha256")
    require(isinstance(expected, dict) and len(expected) == 20,
            "expected exactly 20 frozen FS-C01 input hashes")
    actual = set()
    for folder in INPUT_DIRS:
        d = case / folder
        require(d.is_dir() and not d.is_symlink(), "missing/linked FS-C01 input directory: " + folder)
        for item in d.rglob("*"):
            require(not item.is_symlink(), "symlink in FS-C01 inputs: " + str(item))
            if item.is_file():
                actual.add(item.relative_to(case).as_posix())
    require(actual == set(expected), "frozen FS-C01 input inventory differs from manifest")
    for name, digest in expected.items():
        rel = Path(name)
        require(not rel.is_absolute() and ".." not in rel.parts
                and rel.parts[0] in INPUT_DIRS,
                "unsafe input path in FS-C01 manifest: " + name)
        require(sha256(case / rel) == digest, "FS-C01 input checksum mismatch: " + name)
    require(not (case / "postProcessing").exists()
            and not (case / "constant" / "polyMesh").exists()
            and not any(case.glob("processor[0-9]*")),
            "original FS-C01 source contains CFD outputs; abort to avoid contamination")
    return manifest


def verify_runtime() -> None:
    require(os.environ.get("WM_PROJECT_VERSION", "") == "14",
            "activate OpenFOAM Foundation 14 first (WM_PROJECT_VERSION must equal 14)")
    for executable in ("blockMesh", "checkMesh", "foamRun"):
        require(shutil.which(executable) is not None, "OpenFOAM14 command not found: " + executable)


def write_status(path: Path, record: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def prepare_run(output_root: Path, source: Path = SOURCE_CASE, run_id: str | None = None):
    """Create a new independent FS-C01 directory, never touch source or C3D."""
    manifest = validate_source(source)
    output_root = output_root.expanduser().resolve()
    require(not within(output_root, REPO) and not within(output_root, source),
            "output must be outside the entire MasterProject checkout")
    name = run_id or (
        "FS-C01_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "_" + uuid.uuid4().hex[:8]
    )
    require(bool(re.fullmatch(r"FS-C01_[A-Za-z0-9_-]+", name)),
            "run identifier must begin FS-C01_")
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = output_root / name
    run_dir.mkdir()  # fail if collision: never overwrite existing data
    case_dir = run_dir / CASE_ID
    case_dir.mkdir()
    for folder in INPUT_DIRS:
        shutil.copytree(source / folder, case_dir / folder)
    for filename in ("BFS01_MANIFEST.json", "CASE_NOTES.md", "HOW_TO_RUN.md"):
        if (source / filename).is_file():
            shutil.copy2(source / filename, case_dir / filename)
    validate_source(case_dir)
    (run_dir / "logs").mkdir()
    git_rev = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        text=True, capture_output=True, check=False,
    )
    record = {
        "case_id": CASE_ID,
        "scientific_stage": "B-FS-01",
        "fluid_identity": EXPECTED_FLUID,
        "source_repository": "michels-lab/MasterProject",
        "source_case": "freesurface/FS-C01",
        "source_git_sha": git_rev.stdout.strip() if git_rev.returncode == 0 else None,
        "source_manifest_sha256": sha256(source / "BFS01_MANIFEST.json"),
        "run_directory": str(run_dir),
        "case_directory": str(case_dir),
        "status": "STAGED_NO_CFD_YET",
        "cfd_verified": False,
        "mass_balance_verified": False,
        "shrinkage_modelled": False,
        "stages": [],
    }
    write_status(run_dir / "FS-C01_RUN_STATUS.json", record)
    return run_dir, case_dir, record


def mesh_success(log: str) -> bool:
    return (bool(re.search(r"\bMesh OK\.", log))
            and not re.search(r"Failed\s+[1-9][0-9]*\s+mesh checks?", log, re.I)
            and "FOAM FATAL" not in log)


def solver_success(log: str) -> bool:
    return bool(re.search(r"(?m)^End\s*$", log)) and "FOAM FATAL" not in log


def run_stage(run_dir: Path, case_dir: Path, status: dict, label: str,
              command: list[str], validator=None) -> None:
    logfile = run_dir / "logs" / ("FS-C01_" + label + ".log")
    print(f"FS-C01 [{label}] running; log: {logfile}", flush=True)
    with logfile.open("w", encoding="utf-8") as out:
        result = subprocess.run(command, cwd=case_dir, stdout=out,
                                stderr=subprocess.STDOUT, check=False, text=True)
    data = logfile.read_text(encoding="utf-8", errors="replace")
    valid = result.returncode == 0 and (validator(data) if validator else True)
    status["stages"].append({
        "name": label, "command": command, "returncode": result.returncode,
        "log": str(logfile), "gate_passed": bool(valid),
    })
    status["status"] = ("PASSED_" if valid else "BLOCKED_") + label.upper()
    write_status(run_dir / "FS-C01_RUN_STATUS.json", status)
    require(valid, "FS-C01 " + label + " failed its gate; inspect " + str(logfile))
    print(f"FS-C01 [{label}] gate passed", flush=True)


def execute_fs_c01(run_dir: Path, case_dir: Path, status: dict) -> None:
    run_stage(run_dir, case_dir, status, "blockMesh", ["blockMesh"])
    run_stage(run_dir, case_dir, status, "checkMesh",
              ["checkMesh", "-allGeometry", "-allTopology"], mesh_success)
    run_stage(run_dir, case_dir, status, "foamRun", ["foamRun"], solver_success)
    audit_dir = run_dir / "FS-C01_VOLUME_AUDIT"
    run_stage(
        run_dir, case_dir, status, "volumeAudit",
        [sys.executable, str(VOLUME_AUDITOR), "audit",
         "--case", str(case_dir), "--out", str(audit_dir)],
    )
    status["status"] = "FS_C01_VOLUME_SCREEN_PASSED_MASS_NOT_VERIFIED"
    write_status(run_dir / "FS-C01_RUN_STATUS.json", status)
    print("FS-C01 volume screening passed; mass, alpha bounds and physics remain UNVERIFIED.", flush=True)
    print("No iron/solidification/shrinkage simulation has been run.", flush=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path,
                        default=Path.home() / "OpenFOAM" / "FS_C01_RUNS")
    parser.add_argument("--preflight", action="store_true",
                        help="check frozen FS-C01 input only; create nothing")
    parser.add_argument("--stage-only", action="store_true",
                        help="create isolated FS-C01 input, but do not run OpenFOAM")
    args = parser.parse_args(argv)
    try:
        manifest = validate_source()
        if args.preflight:
            print("FS-C01 frozen-input preflight PASSED (20 SHA256); no OpenFOAM run.")
            return 0
        if not args.stage_only:
            verify_runtime()
        run_dir, case_dir, status = prepare_run(args.output_root)
        print(f"FS-C01 isolated directory: {run_dir}", flush=True)
        if args.stage_only:
            print("FS-C01 STAGED ONLY. C3D-02 remains untouched.", flush=True)
            return 0
        execute_fs_c01(run_dir, case_dir, status)
        return 0
    except (FSC01Error, OSError, json.JSONDecodeError) as exc:
        print("FS-C01 BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
