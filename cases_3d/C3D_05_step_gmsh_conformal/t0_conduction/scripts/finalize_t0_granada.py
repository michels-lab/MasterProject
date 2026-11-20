#!/usr/bin/env python3
"""One auditable C3D-05/B numerical-only evidence summary (never CFD validation).

Called by the existing single-command Granada after BOTH native regional energy
history and bilateral 12636-face q diagnostics have been produced. Rechecks
input/log/report/checksums and mesh-count evidence, then publishes a read-only,
idempotent JSON synopsis. Never launches OpenFOAM, edits case/mesh or upgrades
the 2/7 technical milestones or experimental validation state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


NAME = "C3D_05_step_gmsh_conformal"
FACES = 12636
EXPECTED_FILES = ("metal.csv", "mold.csv", "bilateral_diagnostics.json",
                  "log.c3d05PatchFlux")
REQUIRED_STAGE = "T0_PREPARED_DICTIONARIES_PARSED_NO_CFD"
REQUIRED_ENERGY = "OBSERVED_NATIVE_VOLUMETRIC_ENERGY_METRICS_NOT_PHYSICAL_VALIDATION"
REQUIRED_FLUX = "NATIVE_PATCH_Q_FACE_PAIR_DIAGNOSTICS_NO_ACCEPTANCE_THRESHOLD"


def sha(path: Path):
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or unsafe evidence: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    # JSON objects are not accepted if backed by symlinks or malformed bytes.
    sha(path)
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Evidence must be a JSON object: {path}")
    return obj


def manifest_verify(directory: Path) -> dict[str, str]:
    manifest = directory / "manifest.sha256"
    sha(manifest)
    found = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise ValueError("Invalid two-column native SHA-256 manifest")
        digest, name = parts
        if (len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
                or name not in EXPECTED_FILES or name in found):
            raise ValueError("Invalid, duplicate or unexpected native evidence digest/name")
        if sha(directory / name) != digest:
            raise ValueError(f"Native evidence modified after publication: {name}")
        found[name] = digest
    if set(found) != set(EXPECTED_FILES):
        raise ValueError("Incomplete manifest: expected exactly four primary native artifacts")
    return found


def require_finite_metric(value, label):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{label}: requires nonnegative finite numerical metric")
    return float(value)


def summarize(case: Path, inputs: Path) -> dict:
    data = inputs.read_bytes()
    config = json.loads(data)
    identity = hashlib.sha256(data).hexdigest()
    if not config.get("reference_profile", "").startswith("C14_ARCHIVED_NUMERICAL_REFERENCE"):
        raise ValueError("This summary is restricted to archived numerical C14 T0")
    prep = load(case / "T0_GRANADA_REPORT.json")
    if prep.get("case") != NAME or prep.get("status") != REQUIRED_STAGE or prep.get("input_sha256") != identity:
        raise ValueError("Preparation metadata inconsistent with present numerical candidate")
    reference_path = case / "T0_CLOSED_ENERGY_REFERENCE.json"
    ref = load(reference_path)
    if ref.get("input_file_sha256") != identity:
        raise ValueError("Closed-system theoretical energy uses different inputs")
    runlog = case / "log.foamMultiRun.C14_NUMERICAL_T0"
    status = load(case / "T0_NUMERICAL_RUN_STATUS.json")
    if (status.get("numerical_run_completed") is not True
            or status.get("input_sha256") != identity
            or status.get("log_sha256") != sha(runlog)
            or status.get("scope") != "C14_ARCHIVED_NUMERICAL_TWO_SOLID_T0_ONLY"):
        raise ValueError("Native solver report does not verify this log/input pair")
    energy_file = case / "T0_NATIVE_ENERGY_HISTORY.json"
    energy = load(energy_file)
    if energy.get("status") != REQUIRED_ENERGY or energy.get("input_sha256") != identity:
        raise ValueError("Native volumetric energy report missing or mismatched")
    fluxdir = case / "T0_NATIVE_FACE_FLUX"
    if fluxdir.is_symlink() or not fluxdir.is_dir():
        raise ValueError("No safely published native bilateral face directory")
    digest = manifest_verify(fluxdir)
    face = load(fluxdir / "bilateral_diagnostics.json")
    if face.get("status") != REQUIRED_FLUX or face.get("faces_paired_per_side") != FACES:
        raise ValueError("No accepted C3D05 native 12636-pair diagnostics")
    source = face.get("source_sha256", {})
    if (source.get("metal_face_csv") != digest["metal.csv"]
            or source.get("mold_face_csv") != digest["mold.csv"]
            or source.get("regional_energy_json") != sha(energy_file)
            or source.get("inputs_json") != identity
            or source.get("solver_log") != sha(runlog)):
        raise ValueError("Facewise diagnostics were derived from different native data")
    # Validate the same time endpoints without requiring arbitrary physical
    # energy/flux tolerances. They must describe EXACTLY one numerical run.
    expected_end = float(config["simulation"]["endTime_s"])
    e_series, q_series = energy.get("history", []), face.get("history", [])
    if len(e_series) < 2 or len(q_series) < 2 or len(e_series) != len(q_series):
        raise ValueError("Incomplete energy/flux history")
    for e, q in zip(e_series, q_series):
        if abs(float(e["time_s"]) - float(q["time_s"])) > 1e-12:
            raise ValueError("Energy and flux histories do not share time samples")
    if (abs(float(e_series[0]["time_s"])) > 1e-12
            or abs(float(q_series[-1]["time_s"]) - expected_end) > max(1e-10, expected_end*1e-7)):
        raise ValueError("Incomplete native run time window")

    errors = [
        require_finite_metric(row["relative_pairwise_mismatch_over_gross_flux"],
                              "local q mismatch fraction")
        for row in q_series
        if row.get("relative_pairwise_mismatch_over_gross_flux") is not None
    ]
    if not errors:
        raise ValueError("All patch flux denominators are zero; continuity cannot be interpreted")
    return {
        "schema": "C3D05_T0_EVIDENCE_SUMMARY_V1",
        "case": NAME,
        "case_stage": "3/7",
        "technical_milestones_closed": 2,
        "technical_milestones_total": 7,
        "percent_technical_milestones": 29,
        "scientific_state": "NUMERICAL_EVIDENCE_PRESENT_NOT_EXPERIMENTALLY_VALIDATED",
        "scope": "C14_ARCHIVED_NUMERICAL_ONLY_NOT_JMATPRO_OR_CASTING",
        "native_solver_report_indicates_complete": True,
        "native_two_region_thermal_metrics_observed_in_supplied_artifacts": True,
        "direct_bilateral_native_face_data_present_in_supplied_artifacts": True,
        "total_flux_pairs_per_time": FACES,
        "temporal_samples": len(e_series),
        "configured_end_s": expected_end,
        "max_relative_energy_discrepancy_over_initial_exchange":
            require_finite_metric(energy["max_abs_energy_closure_relative_to_initial_exchange"],
                                  "energy exchange discrepancy"),
        "max_relative_pairwise_flux_mismatch_over_gross": max(errors),
        "numerical_energy_accepted": False,
        "numerical_flux_continuity_accepted": False,
        "grid_and_time_convergence_accepted": False,
        "experimental_JMatPro_or_QuickCup_validation": False,
        "user_WSL_host_origin_independently_attested": False,
        "evidence_sha256": {
            "C14_reference_inputs": identity,
            "original_solver_log": sha(runlog),
            "native_energy": sha(energy_file),
            "closed_energy_target": sha(reference_path),
            "face_diagnostics": digest["bilateral_diagnostics.json"],
            "native_face_manifest": sha(fluxdir / "manifest.sha256")
        },
        "warnings": [
            "Supplied native logs/data cannot independently attest host machine provenance",
            "Model is archived C14 two solids with Cp≈Cv and derived k; not JMatPro",
            "No acceptance threshold claimed without dt/mesh/nonorth sensitivity",
            "CFD evidence presence is separate from experimental physical validation",
        ]
    }


def exclusive(path: Path, payload: dict) -> str:
    target = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)+"\n"
    if path.exists() or path.is_symlink():
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8") == target:
            return "CASE_B_NUMERICAL_EVIDENCE_SUMMARY_IDENTICAL"
        raise FileExistsError("Preserving pre-existing incompatible T0 summary: " + str(path))
    with path.open("x", encoding="utf-8") as f:
        f.write(target)
    return "CASE_B_NUMERICAL_EVIDENCE_SUMMARY_GENERATED_NO_SCIENTIFIC_ACCEPTANCE"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    args = p.parse_args()
    case = args.case.expanduser().resolve()
    summary = summarize(case, args.inputs.expanduser().resolve())
    status = exclusive(case / "T0_GRANADA_EVIDENCE_SUMMARY.json", summary)
    print(status)
    print("Native numerical metrics: peak energy discrepancy / Qref =",
          summary["max_relative_energy_discrepancy_over_initial_exchange"])
    print("Native numerical metrics: peak local relative face-q discrepancy =",
          summary["max_relative_pairwise_flux_mismatch_over_gross"])
    print("CASO B ETAPA 3/7; 2/7 HITOS=29% TECNICO; NO VALIDACION EXPERIMENTAL/CFD ACEPTADA")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
