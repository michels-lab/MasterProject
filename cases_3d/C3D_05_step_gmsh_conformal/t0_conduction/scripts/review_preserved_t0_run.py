#!/usr/bin/env python3
"""Re-audit ONE preserved C3D-05 numerical WSL run; never rerun OpenFOAM.

The first real Foundation14 270788-cell attempt may have been misclassified
because the original log auditor rejected 'Time = 0.1s' and interpreted the
FOAM_SIGFPE *enablement banner* as a fatal exception. The old JSON/log remain
immutable; a separately named SHA-bound reviewed report records the correction.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def recover(legacy_bytes: bytes, log_bytes: bytes, input_bytes: bytes) -> dict:
    previous = json.loads(legacy_bytes)
    if not isinstance(previous, dict):
        raise ValueError("legacy run report must be a JSON object")
    if (previous.get("status") != "NUMERICAL_ONLY_SOLVER_NOT_VERIFIED_COMPLETE"
            or previous.get("numerical_run_completed") is not False
            or type(previous.get("exit_code")) is not int
            or previous["exit_code"] != 0):
        raise ValueError("legacy result is not an eligible zero-exit false negative")
    if (previous.get("input_sha256") != sha(input_bytes)
            or previous.get("log_sha256") != sha(log_bytes)
            or previous.get("scope") != "C14_ARCHIVED_NUMERICAL_TWO_SOLID_T0_ONLY"):
        raise ValueError("legacy report and original input/log SHA-256 differ")
    text = log_bytes.decode("utf-8", errors="replace")
    banner = bool(re.search(
        r"(?im)^\s*Enabling floating point exception trapping \(FOAM_SIGFPE\)\s*$",
        text
    ))
    unit_time = bool(re.search(r"(?m)^\s*Time\s*=\s*[0-9.]+\s*s\s*$", text))
    if not (banner or unit_time):
        raise ValueError("no documented Foundation14 false-negative signature found")
    source = Path(__file__).with_name("audit_t0_numerical_run.py")
    spec = importlib.util.spec_from_file_location("case_b_reauditor", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("canonical auditor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    current = module.audit(text, previous["exit_code"], json.loads(input_bytes))
    if current["numerical_run_completed"] is not True:
        raise ValueError("original native run STILL fails corrected auditor; no recovery permitted")
    current["input_sha256"] = sha(input_bytes)
    current["log_sha256"] = sha(log_bytes)
    current["original_legacy_status_sha256"] = sha(legacy_bytes)
    current["recovered_without_solver_rerun"] = True
    current["documented_prior_false_negative"] = {
        "informational_sigfpe_banner": banner,
        "time_lines_with_seconds_suffix": unit_time,
    }
    current["energy_conservation_verified"] = False
    current["interface_flux_verified"] = False
    current["experimental_validation"] = False
    return current


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--legacy", type=Path, required=True)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--inputs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    for item in (args.legacy, args.log, args.inputs, args.out):
        if item.is_symlink():
            raise ValueError("symlink is not trusted: " + str(item))
    source = recover(args.legacy.read_bytes(), args.log.read_bytes(), args.inputs.read_bytes())
    auditor = Path(__file__).with_name("audit_t0_numerical_run.py")
    spec = importlib.util.spec_from_file_location("case_b_status_writer", auditor)
    if spec is None or spec.loader is None:
        raise RuntimeError("auditor unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print(module.save(args.out, source), "REVIEWED_PRESERVED_SOLVER_RUN_COMPLETE_NO_RERUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
