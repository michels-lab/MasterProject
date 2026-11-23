#!/usr/bin/env python3
"""Integrated read-only native Stage07 C14-A failure forensics (no CFD).

Reads the 10s authentic source, existing C14 native offline workcopy, the
101-state WSL recovery report and original C14 diagnostic definitions.
Publishes a fresh, immutable independent forensic report. Classifies observed
native exit codes, missing original function-object outputs/derived fields,
missing/nonfinite profiles, energy-table audit and real log error signatures.

Does NOT run foamPostProcess/foamMultiRun, modify the existing workcopy,
repair source physics, fabricate 0.001s probe history, or claim conservation.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import c14_3d_native_energy_closure as energy
import run_c14_3d_complete_postprocess as native_runner

C14 = native_runner.C14
RECOVERY_NAME = "C3D04_A_STAGE07_RECOVERY_REPORT.json"
NATIVE_NAME = "C3D04_A_C14_NATIVE_POSTPROCESS_REPORT.json"
FORENSIC_NAME = "C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json"
TASK_NAMES = {"c14_functions", "momentum", "top_surface", "foamLog"}
ERROR_SIGNS = (
    ("FATAL_IO", re.compile(r"FOAM FATAL IO ERROR", re.I)),
    ("FATAL_OPENFOAM", re.compile(r"FOAM FATAL ERROR", re.I)),
    ("FATAL_CPP", re.compile(r"(Segmentation fault|Floating point exception|"
                             r"terminate called after throwing)", re.I)),
    ("FAILED_TO_READ", re.compile(r"(cannot find file|cannot read|could not find|"
                                  r"no such file or directory|cannot open)", re.I)),
    ("MISSING_FIELD", re.compile(r"(field [^\n]{0,130} (not found|not available)|"
                                 r"cannot find field|Unknown field|"
                                 r"objectRegistry [^\n]* not found)", re.I)),
    ("DYNAMIC_CODE", re.compile(r"(dynamicCode|wmake|compile error|fatal error: "
                                 r"[^\n]{0,150} file)", re.I)),
    ("FUNCTION_OBJECT_UNSUPPORTED", re.compile(
        r"(functionObject [^\n]* (not supported|not found)|"
        r"Unknown function type|ddt.*(not supported|cannot))", re.I)),
)


class NativeEvidenceBlocked(ValueError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise NativeEvidenceBlocked("C14_STAGE07_NATIVE_FORENSICS_BLOCKED: " + msg)


def regular(p: Path) -> bool:
    return p.is_file() and not p.is_symlink()


def sha(p: Path) -> str:
    need(regular(p), "missing or symlinked file " + str(p))
    dig = hashlib.sha256()
    with p.open("rb") as f:
        for buf in iter(lambda: f.read(1 << 20), b""):
            dig.update(buf)
    return dig.hexdigest()


def read_obj(p: Path) -> dict:
    need(regular(p), "missing or symlinked evidence JSON " + str(p))
    obj = json.loads(p.read_text(encoding="utf-8"))
    need(isinstance(obj, dict), "JSON is not an object: " + str(p))
    return obj


def error_excerpt(p: Path, limit: int = 6) -> dict:
    """Inspect actual log error evidence, without mistaking FPE banner for crash."""
    if not regular(p):
        return {"exists": False, "sha256": None, "error_signatures": [],
                "tail_last_24_lines": []}
    results: list[dict[str, object]] = []
    tail = deque(maxlen=24)
    with p.open(encoding="utf-8", errors="replace") as f:
        for line_number, line in enumerate(f, 1):
            clean = line.strip()[:300]
            if clean:
                tail.append(clean)
            if "Enabling floating point exception trapping" in line:
                continue  # normal native OpenFOAM configuration banner
            for key, pattern in ERROR_SIGNS:
                if pattern.search(line):
                    if len(results) < limit:
                        results.append({
                            "kind": key, "line_number": line_number,
                            "excerpt": line.strip()[:260],
                        })
                    break
    return {"exists": True, "sha256": sha(p),
            "error_signatures": results, "tail_last_24_lines": list(tail)}


def source_offline_incompatibilities() -> list[dict]:
    """C14's original ddt functionObjects explicitly require solver runtime."""
    src = C14 / "system/researchDiagnostics"
    need(regular(src), "missing original researchDiagnostics")
    text = src.read_text(encoding="utf-8")
    answer = []
    for name in ("temperatureTimeDerivative", "liquidFractionTimeDerivative"):
        m = re.search(r"(?m)^" + re.escape(name) + r"\s*\{", text)
        need(m is not None, "C14 expected function object missing: " + name)
        body_start = m.end()
        # These block bodies have simple dictionary entries, no nested braces.
        end = text.find("}", body_start)
        need(end > body_start, "unclosed C14 function block: " + name)
        block = text[body_start:end]
        need(re.search(r"\btype\s+ddt\s*;", block) is not None,
             "native C14 ddt definition changed unexpectedly: " + name)
        answer.append({
            "object": name,
            "source": "C14 original system/researchDiagnostics",
            "offline_foamPostProcess_0p1s_parity_possible": False,
            "reason": "C14 source explicitly documents Foundation14 ddt as "
                      "in-run-only; 0.1s snapshot finite differences are "
                      "distinct from the native 0.001s ddt field.",
            "observed_native_failure_cause": False,
        })
    return answer


def copy_safe(case: Path, copy: Path) -> dict:
    need(copy.is_dir() and not copy.is_symlink(),
         "native workcopy missing or symlinked; no automatic recreation")
    original = C14 / "system/controlDict"
    control = case / "system/controlDict"
    copy_control = copy / "system/controlDict"
    need(sha(original) == sha(control) == sha(copy_control),
         "C14 controlDict is not identical between original, case and native copy")
    original_log = case / "log.foamMultiRun"
    copy_log = copy / "log.foamMultiRun"
    need(sha(original_log) == sha(copy_log),
         "authentic 10s CFD solver log SHA differs from native copy")
    return {
        "original_source_controlDict_SHA256": sha(original),
        "actual_10s_CFD_controlDict_SHA256": sha(control),
        "native_copy_controlDict_SHA256": sha(copy_control),
        "authentic_10s_solver_log_sha256": sha(original_log),
        "native_copy_solver_log_sha256": sha(copy_log),
    }


def resolve_steps(native: dict, copy: Path) -> dict:
    raw = native.get("steps")
    need(isinstance(raw, list), "original native audit has no steps list")
    steps = {}
    for item in raw:
        need(isinstance(item, dict), "invalid native subprocess record")
        name = item.get("name")
        need(name in TASK_NAMES and name not in steps,
             "unexpected/duplicated native subprocess name: " + str(name))
        path = copy / ("log.C14_3D_postprocess_" + name)
        logged = error_excerpt(path)
        exit_code = item.get("exit_code")
        need(isinstance(exit_code, int) and not isinstance(exit_code, bool),
             "native subprocess exit code missing; cannot attest completion")
        passed = item.get("passed")
        need(isinstance(passed, bool) and passed == (exit_code == 0),
             "native exit code/passed contradiction: " + name)
        steps[name] = {
            "exit_code": exit_code, "exit_zero": exit_code == 0,
            "log": str(path), **logged,
            "output_checked_not_just_log": False,
        }
    need(set(steps) == TASK_NAMES, "original native audit did not record 4 subprocesses")
    return steps


def energy_status(copy: Path, native: dict) -> dict:
    original = native.get("native_energy_closure_audit", {})
    need(isinstance(original, dict), "energy audit must be an object")
    result = {"prior_native_energy_audit": original,
              "energy_balance_verified": False,
              "physically_validated": False,
              "read_only_101_native_energy_tables_reconciled": False}
    try:
        analysis = energy.calculate(copy)
        result.update({
            "read_only_101_native_energy_tables_reconciled": True,
            "status": "NATIVE_METAL_ONLY_NOMINAL_ENERGY_DIAGNOSTIC_NOT_CLOSURE_PROOF",
            "final_relative_nominal_residual":
                analysis["final_relative_nominal_closure_residual"],
            "final_0p1s_integrated_terms":
                analysis["final_integrated_terms"],
        })
    except (OSError, ValueError, KeyError) as exc:
        result.update({
            "status": "MISSING_OR_INCOMPATIBLE_NATIVE_ENERGY_TABLES",
            "error": str(exc)[:900],
        })
    return result


def analyze(case: Path, copy: Path, recovery: Path) -> dict:
    case, copy, recovery = (
        case.expanduser().resolve(), copy.expanduser().absolute(),
        recovery.expanduser().resolve()
    )
    need(case.is_dir() and not case.is_symlink(), "authentic saved 10s CFD is absent")
    identities = copy_safe(case, copy)
    previous = read_obj(recovery / RECOVERY_NAME)
    need(previous.get("schema") == "C3D04_A_C14_3D_STAGE07_EXISTING_EVIDENCE_V1",
         "existing stage07 recovery does not match original C14 model")
    need(previous.get("case_A_source_run_read_only") == str(case),
         "original recovery evidence references another CFD source")
    recovered_hashes = previous.get("source_sha256", {})
    need(isinstance(recovered_hashes, dict)
         and recovered_hashes.get("source_CFD_log_sha256") ==
         identities["authentic_10s_solver_log_sha256"],
         "original recovery log hash is not identical to native copied source")
    path = copy / NATIVE_NAME
    native = read_obj(path)
    need(native.get("schema") ==
         "C3D04_A_C14_3D_NATIVE_FUNCTION_OBJECT_PARITY_V1",
         "unexpected original native postprocessing report")
    need(native.get("original_CFD_read_only") == str(case)
         and native.get("source_log_sha256") ==
         identities["authentic_10s_solver_log_sha256"]
         and native.get("isolated_copy") == str(copy),
         "native audit belongs to a different source/workcopy")
    steps = resolve_steps(native, copy)
    missing = native.get("missing_expected_C14_object_dirs")
    missing_fields = native.get("missing_derived_C14_fields_at_final_time")
    bad_profiles = native.get("incomplete_profiles_at_t10")
    need(all(isinstance(x, list) for x in (missing, missing_fields, bad_profiles)),
         "native audit has no explicit missing family, field, profile lists")
    native_claim = native.get("all_native_processing_commands_passed")
    need(isinstance(native_claim, bool)
         and native_claim == all(v["exit_zero"] for v in steps.values()),
         "native report aggregate success contradicts individual exit codes")
    profiles = native.get("full_80_point_profiles_at_t10")
    need(isinstance(profiles, dict), "native profile coverage inventory missing")
    failed_profiles = {key: val for key, val in profiles.items()
                       if not isinstance(val, dict) or val.get("status") != "PASS"}
    failed_steps = [key for key, val in steps.items() if not val["exit_zero"]]
    native_energy = energy_status(copy, native)
    evidence = {
        "native_report_sha256": sha(path),
        "stage07_recovery_report_sha256": sha(recovery / RECOVERY_NAME),
        "native_step_logs": {k: v["sha256"] for k, v in steps.items()},
        "source_model_sha": identities,
    }
    previous_energy = native.get("native_energy_closure_audit", {})
    report = {
        "schema": "C3D04_A_STAGE07_NATIVE_FAILURE_FORENSICS_V1",
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "7/10", "milestones_done": "6/10",
        "operational_hitos_percent_not_physical_validation": 60,
        "status": (
            "NATIVE_OFFLINE_INCOMPLETE_SOURCE_IDENTITIES_VERIFIED"
            if failed_steps or missing or missing_fields or bad_profiles
            else "NATIVE_OFFLINE_RECOVERED_ONLY_NO_PHYSICAL_VALIDATION"
        ),
        "original_10s_case_read_only": str(case),
        "existing_native_workcopy_read_only": str(copy),
        "existing_101_snapshot_recovery_read_only": str(recovery),
        "evidence_sha256": evidence,
        "native_commands_verified": native_claim,
        "native_failed_commands": failed_steps,
        "native_command_runs": steps,
        "missing_C14_postProcessing_object_families": missing,
        "missing_derived_C14_fields_at_10s": missing_fields,
        "missing_or_partial_80_point_profiles": bad_profiles,
        "profile_coverage_values": failed_profiles,
        "native_report_energy_audit_passed": previous_energy.get("passed"),
        "energy_table_read_only_audit": native_energy,
        "known_original_C14_functionObjects_unavailable_in_offline_replay":
            source_offline_incompatibilities(),
        "candidate_root_cause_guidance": [
            "Prioritize nonzero native subprocess exit and matching OpenFOAM FATAL/IO/"
            "missing-field/dynamic-code signatures; do not infer root cause from "
            "this classifier alone.",
            "Original C14 ddt(T) and ddt(alpha1) require in-run solver histories "
            "that the 101 saved states cannot recreate; do NOT spoof those outputs.",
            "Do not modify C14 physics, reconstruct 0.001s probes, or reset/bulk "
            "rerun the original 10-second CFD. If native retry is justified, "
            "create another isolated copy and preserve the existing failed one.",
        ],
        "other_case_worktrees_untouched": ["C3D05_B_WORKTREE", "FS_C02_WORKTREE"],
        "new_CFD_run": False,
        "native_commands_executed_by_this_audit": False,
        "energy_conservation_verified": False,
        "grid_or_time_step_independence_verified": False,
        "quickcup_validation": False,
    }
    return report


def publish(report: dict, out: Path) -> str:
    out = out.expanduser().absolute()
    preserve = [Path(report[key]).resolve() for key in
                ("original_10s_case_read_only",
                 "existing_native_workcopy_read_only",
                 "existing_101_snapshot_recovery_read_only")] + [
                     C14.resolve(), native_runner.BASE.parents[2].resolve()
                 ]
    need(all(out != p and p not in out.parents and out not in p.parents
             for p in preserve), "forensic output overlaps protected input/source")
    path = out / FORENSIC_NAME
    if out.exists() or out.is_symlink():
        prev = read_obj(path)
        need(prev.get("schema") == report["schema"]
             and prev.get("evidence_sha256") == report["evidence_sha256"],
             "prior forensic output exists with different input evidence; "
             "choose a new --out path, NEVER overwrite")
        return "PREVIOUS_EVIDENCE_MATCHED_REPORT_PRESERVED"
    need(out.parent.is_dir(), "forensic output parent directory absent")
    out.mkdir(exist_ok=False)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n",
                    encoding="utf-8")
    return "FORENSIC_NATIVE_EVIDENCE_PUBLISHED_READONLY_INPUTS"


def brief(report: dict) -> dict:
    return {
        "case": "C3D04-A", "stage": report["stage"],
        "milestones_done": report["milestones_done"],
        "native_commands_verified": report["native_commands_verified"],
        "failed_native_commands": report["native_failed_commands"],
        "failed_log_signatures": {
            k: v["error_signatures"] for k,v in
            report["native_command_runs"].items()
            if v["error_signatures"]
        },
        "failed_command_last_24_log_lines": {
            k: v["tail_last_24_lines"] for k,v in
            report["native_command_runs"].items()
            if not v["exit_zero"]
        },
        "missing_C14_object_families_count":
            len(report["missing_C14_postProcessing_object_families"]),
        "missing_C14_object_families":
            report["missing_C14_postProcessing_object_families"][:45],
        "missing_derived_fields":
            report["missing_derived_C14_fields_at_10s"][:35],
        "partial_or_missing_80_point_profiles":
            report["missing_or_partial_80_point_profiles"],
        "native_metal_energy_status":
            report["energy_table_read_only_audit"]["status"],
        "native_metal_energy_error":
            report["energy_table_read_only_audit"].get("error"),
        "offline_only_unsupported_ddt":
            [x["object"] for x in
             report["known_original_C14_functionObjects_unavailable_in_offline_replay"]],
        "energy_conservation_verified": False,
        "new_CFD_run": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", type=Path, default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    ap.add_argument("--copy", type=Path, default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01")
    ap.add_argument("--recovery", type=Path, default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01")
    ap.add_argument("--out", type=Path, default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_NATIVE_STAGE07_FORENSICS_01")
    args = ap.parse_args()
    try:
        report = analyze(args.case, args.copy, args.recovery)
        status = publish(report, args.out)
        message = brief(report)
        message["status"] = status
        message["report"] = str(args.out/FORENSIC_NAME)
        print(json.dumps(message, indent=2, ensure_ascii=False))
        return 0  # Audit completed, even if native postProcessing has failures.
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("C3D04_A_NATIVE_POSTPROCESS_FORENSICS_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
