#!/usr/bin/env python3
"""C3D-05 / B — ONE integrated T0 preparation, evidence check and native parsing.
Never runs CFD, changes accepted STEP/polyMesh or overwrites existing thermal cases.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

T0 = Path(__file__).resolve().parents[1]
CASE_B = T0.parent
SRC_DEFAULT = Path.home() / "OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
OUT_DEFAULT = Path.home() / "OpenFOAM/C3D05_T0_CONDUCTION_01"
FILES = (
    "system/controlDict", "system/fvSolution", "system/metal/fvSchemes", "system/metal/fvSolution",
    "system/mold/fvSchemes", "system/mold/fvSolution",
    "constant/metal/physicalProperties", "constant/mold/physicalProperties",
    "0/metal/T", "0/mold/T",
)
STAGE = "T0_PREPARED_DICTIONARIES_PARSED_NO_CFD"
BAD_SOURCES = re.compile(r"(?i)\b(?:SYNTHETIC_UNIT_TEST|TODO|PLACEHOLDER|DUMMY_VALUE|UNVERIFIED_EXAMPLE)\b")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Module cannot be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_inputs(path: Path):
    if not path.is_file():
        return None, [f"Missing input JSON: {path}"]
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return None, [f"Invalid input JSON: {exc}"]
    prepare = load_module("case_b_t0_prepare", T0 / "scripts/prepare_t0.py")
    problems = prepare.validate(obj)
    if isinstance(obj, dict):
        for region in ("metal", "mold"):
            props = obj.get(region, {})
            if isinstance(props, dict):
                for key, value in props.items():
                    if key.startswith("source_") and isinstance(value, str) and BAD_SOURCES.search(value):
                        problems.append(f"{region}.{key}: synthetic/placeholder provenance prohibited")
        sim = obj.get("simulation", {})
        if isinstance(sim, dict) and isinstance(sim.get("source_time_choices"), str):
            if BAD_SOURCES.search(sim["source_time_choices"]):
                problems.append("simulation.source_time_choices: placeholder provenance prohibited")
    return obj, problems


def source_review(source: Path):
    prepare = load_module("case_b_t0_prepare", T0 / "scripts/prepare_t0.py")
    prepare.check_source(source)
    reviewer = load_module("case_b_saved_mesh_evidence", CASE_B / "scripts/review_accepted_hex_mesh.py")
    result = reviewer.assess(source)  # SAVED evidence only; no checkMesh or remeshing
    if result.get("geometry_topology_gate_passed") is not True:
        raise RuntimeError("Previously accepted native CAD/HEX8/contact evidence has changed or failed")
    return result


def check_environment():
    if os.environ.get("WM_PROJECT_VERSION") != "14":
        raise RuntimeError("OpenFOAM Foundation 14 not sourced in current WSL shell")
    if shutil.which("foamDictionary") is None:
        raise RuntimeError("foamDictionary (Foundation14) not on PATH")
    # The solver is NOT launched; confirm availability for future, separate CFD milestone.
    if shutil.which("foamMultiRun") is None:
        raise RuntimeError("foamMultiRun (Foundation14) not on PATH")


def source_fingerprint(source: Path) -> str:
    """Fingerprint actual accepted polyMesh and native source reports (no checkMesh)."""
    parts = [
        "STEP_CAD_AUDIT.json", "CONTACT_AREA_REPORT.json",
        "NATIVE_BUILD_STATUS.txt",
        "log.checkMesh.parent", "log.checkMesh.metal", "log.checkMesh.mold",
    ]
    for region in ("metal", "mold"):
        for name in ("points", "faces", "owner", "neighbour", "boundary"):
            parts.append(f"constant/{region}/polyMesh/{name}")
    digest = hashlib.sha256()
    for rel in parts:
        file = source / rel
        digest.update(rel.encode("utf-8") + b"\0")
        with file.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest()


def existing_output(out: Path, inp_hash: str, source: Path):
    """Idempotent success only for the *same* completed and documented preparation."""
    if not (out.exists() or out.is_symlink()):
        return None
    report_file = out / "T0_GRANADA_REPORT.json"
    prep_file = out / "T0_PREPARATION_REPORT.json"
    try:
        report = json.loads(report_file.read_text(encoding="utf-8"))
        prep = json.loads(prep_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, NotADirectoryError):
        raise FileExistsError(f"Existing output preserved; not recognized as completed GRANADA case: {out}")
    if (report.get("status") != STAGE
            or report.get("input_sha256") != inp_hash
            or report.get("source") != str(source)
            or prep.get("input_sha256") != inp_hash
            or sorted(report.get("parsed_dictionaries", [])) != sorted(FILES)
            or not all((out / rel).is_file() for rel in FILES)
            or any((out / "constant" / r / "polyMesh").is_symlink() for r in ("metal", "mold"))):
        raise FileExistsError(f"Existing output protected: different inputs/source or incomplete evidence: {out}")
    return report


def atomic_report(path: Path, data: dict):
    # This report is created only in the NEW private staging directory.
    with path.open("x", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
        fp.write("\n")


def pipeline(inputs: Path, source: Path, out: Path) -> int:
    inputs = inputs.expanduser().resolve()
    source = source.expanduser().resolve()
    out = out.expanduser().resolve()
    config, errors = read_inputs(inputs)
    if errors:
        print(f"BLOCKED_MISSING_OR_INVALID_INPUTS ({len(errors)} fields): NO CASE, NO CFD")
        for reason in errors:
            print("  - " + reason)
        return 3
    # Do not allow a destination nested inside the reference geometry or vice versa.
    if source == out or source in out.parents or out in source.parents:
        print("BLOCKED_UNSAFE_PATHS: output must be independent of accepted source")
        return 2
    if source.name != SRC_DEFAULT.name:
        print("BLOCKED_SOURCE_IDENTITY: expected accepted C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02")
        return 2
    inp_hash = hashlib.sha256(inputs.read_bytes()).hexdigest()
    try:
        prior = existing_output(out, inp_hash, source)
    except FileExistsError as exc:
        print("PRESERVED:", exc)
        return 2
    if prior:
        try:
            fingerprint = source_fingerprint(source)
        except (OSError, ValueError) as exc:
            print(f"BLOCKED_CHANGED_SOURCE: accepted mesh/evidence missing: {exc}")
            return 4
        if fingerprint != prior.get("source_fingerprint_sha256"):
            print("BLOCKED_CHANGED_SOURCE: accepted polyMesh/native evidence SHA differs from completed case")
            return 2
        try:
            # No re-running native checks: compare installed dictionaries against
            # the CURRENT C14-derived, SHA-verified templates and model.
            prepare = load_module("case_b_t0_prepare", T0 / "scripts/prepare_t0.py")
            current_files = prepare.file_map(config)
            drift = [rel for rel, body in current_files.items()
                     if not (out / rel).is_file()
                     or (out / rel).read_text(encoding="utf-8") != body]
        except (OSError, ValueError, KeyError) as exc:
            print(f"BLOCKED_CHANGED_T0_MODEL: {exc}")
            return 2
        if drift:
            print("BLOCKED_CHANGED_T0_MODEL: installed dictionaries differ from current templates: "
                  + ", ".join(drift))
            return 2
        print(f"ALREADY_PREPARED | {STAGE} | {out}")
        print("No repeat of checkMesh, materialization or foamDictionary; no CFD.")
        return 0
    try:
        check_environment()
        evidence = source_review(source)
        fingerprint = source_fingerprint(source)
    except (RuntimeError, ValueError, OSError, KeyError, TypeError) as exc:
        print(f"BLOCKED_NATIVE_OR_SAVED_EVIDENCE: {exc}")
        return 4
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = out.with_name(out.name + ".granada.lock")
    staging = out.with_name(out.name + ".granada-staging-" + uuid.uuid4().hex[:12])
    try:
        with lock.open("x", encoding="utf-8") as fp:
            fp.write(f"pid={os.getpid()}\n")
    except FileExistsError:
        print("BLOCKED_CONCURRENT_PREPARATION: destination lock exists, original case preserved")
        return 5
    try:
        if out.exists() or out.is_symlink():
            print("BLOCKED_CONCURRENT_OUTPUT: another thermal case appeared; preserved")
            return 2
        process = subprocess.run(
            [sys.executable, "-B", str(T0 / "scripts/prepare_t0.py"),
             "--inputs", str(inputs), "--source", str(source), "--out", str(staging)],
            cwd=str(T0), capture_output=True, text=True, check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(f"Materializer exit={process.returncode}: {process.stderr.strip()} {process.stdout.strip()}")
        for rel in FILES:
            path = staging / rel
            if not path.is_file():
                raise RuntimeError(f"Missing materialized Foundation14 dictionary: {rel}")
            parsed = subprocess.run(
                ["foamDictionary", str(path)], cwd=str(staging),
                capture_output=True, text=True, check=False,
            )
            if parsed.returncode != 0:
                raise RuntimeError(f"Native foamDictionary failed {rel}: {parsed.stderr.strip()} {parsed.stdout.strip()}")
        # The old materializer writes its temporary output path into its proof.
        # Normalize to the FINAL location before atomically publishing the case.
        prep_path = staging / "T0_PREPARATION_REPORT.json"
        preparation = json.loads(prep_path.read_text(encoding="utf-8"))
        preparation["output"] = str(out)
        preparation["staging_finalized_into_output"] = True
        prep_path.write_text(json.dumps(preparation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = {
            "status": STAGE,
            "case": "C3D_05_step_gmsh_conformal",
            "stage": "3/7 T0",
            "source": str(source),
            "output": str(out),
            "input_sha256": inp_hash,
            "source_fingerprint_sha256": fingerprint,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "parsed_dictionaries": list(FILES),
            "read_only_native_evidence_gate": evidence["geometry_topology_gate_passed"],
            "evidence_source": evidence.get("source"),
            "mesh_high_nonorth_warning": evidence.get("high_nonorthogonality_warning"),
            "cfd_executed": False,
            "energy_balance_verified": False,
            "physical_material_provenance_independently_verified": False,
            "grid_independence": False,
            "purpose": "conduction-only two-solid numerical setup, NOT cast-iron solidification",
        }
        atomic_report(staging / "T0_GRANADA_REPORT.json", report)
        if out.exists() or out.is_symlink():
            raise RuntimeError("Output path appeared during preparation; refuse overwrite")
        staging.rename(out)
        print(f"{STAGE}: {out}")
        print("10/10 native dictionaries parsed. Source mesh preserved; NO solver run or CFD validation.")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"T0_INTEGRATED_BUILD_FAILED: {exc}")
        print("Staging generated by this invocation will be discarded; original data untouched.")
        return 6
    finally:
        if staging.exists():
            shutil.rmtree(staging)  # only private stage, never accepted mesh or existing output
        lock.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, default=Path(os.environ.get("C3D05_T0_INPUTS", str(T0 / "T0_INPUTS.json"))))
    p.add_argument("--source", type=Path, default=SRC_DEFAULT)
    p.add_argument("--out", type=Path, default=OUT_DEFAULT)
    args = p.parse_args()
    return pipeline(args.inputs, args.source, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
