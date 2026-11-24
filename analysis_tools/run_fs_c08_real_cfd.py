#!/usr/bin/env python3
"""Build and run ONE *real* Foundation14 FS-C08 CFD case; never a shadow run.

Requires scientifically sourced alloy tables and an accepted FS-C07 t=0 source.
- wmake libso compiles the actual coupled fluid solver.
- An isolated FS_C08_COUPLED_* case is staged; the FS-C07 source is untouched.
- foamMultiRun advances REAL liquid/solid/gas/energy/pressure fields.
- A nonzero return code or missing physical outputs fails closed.
- Success means "native CFD completed", NOT validated casting shrinkage.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys

from stage_fs_c08_coupled import BASE_MODULE, stage

REQUIRED_FINAL_FIELDS = (
    "rhoAlpha.liquid", "rhoAlpha.solid", "alpha.metal",
    "alpha.metal.solid", "internalEnergy.fsC08",
    "Gamma.fsC08", "SvolMaterial.fsC08",
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError("FS-C08 REAL CFD BLOCKED: " + reason)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run_logged(cmd: list[str], cwd: Path, logfile: Path,
               timeout_minutes: int) -> dict:
    logfile.parent.mkdir(parents=True, exist_ok=True)
    with logfile.open("w", encoding="utf-8") as fp:
        try:
            completed = subprocess.run(
                cmd, cwd=cwd, stdin=subprocess.DEVNULL,
                stdout=fp, stderr=subprocess.STDOUT, text=True,
                timeout=timeout_minutes * 60, check=False,
            )
            return {"exit_code": completed.returncode, "timeout": False}
        except subprocess.TimeoutExpired:
            fp.write("\nFS_C08_RUNTIME_TIMEOUT — native CFD incomplete\n")
            return {"exit_code": None, "timeout": True}


def first_compiler_error(logfile: Path) -> str | None:
    pattern = re.compile(
        r"fatal error:|(?<![a-z])error:|undefined reference|"
        r"make(?:\[\d+\])?: \*\*\*|wmake: \*\*\*",
        flags=re.IGNORECASE,
    )
    for line in logfile.read_text(encoding="utf-8", errors="replace").splitlines():
        if pattern.search(line):
            return line.strip()[:1000]
    return None


def first_native_error(logfile: Path) -> str | None:
    pattern = re.compile(
        r"FOAM FATAL ERROR|FOAM FATAL IO ERROR|floating point exception|"
        r"segmentation fault|error:|cannot open shared object|"
        r"unknown solver|uncaught exception",
        flags=re.IGNORECASE,
    )
    for line in logfile.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        if pattern.search(line):
            return line.strip()[:1000]
    return None



def inspect_real_cfd_budgets(log: str, final_saved_time_s: float) -> dict:
    """Require actual per-time OpenFOAM metal/gas gates, not log marker counts.

    Thermal energy remains diagnostic until the full multi-region first-law
    balance is independently accepted. No material or CFD values are invented.
    """
    required = (
        "time_s", "liquidSolidMetalMass_kg", "previousMetalMass_kg",
        "metalMassResidual_kg", "nativeGasInventory_kg",
        "previousGasInventory_kg", "gasContinuityDefect_kg",
        "gasMassBudgetTolerance_kg", "totalInternalEnergyEquationBalance_J",
        "pressureCorrectionEnergyGap_J",
        "phaseChangeVolumeSourceMean_s_1",
        "combinedMaterialVolumeSourceMean_s_1",
    )
    budgets: list[dict] = []
    pass_times: list[float] = []
    thermal_times: list[float] = []
    for line in log.splitlines():
        if not any(marker in line for marker in (
            "FS_C08_REAL_CFD_MASS_BUDGET",
            "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED",
            "FS_C08_NATIVE_PHASE_RESOLVED_INTERNAL_ENERGY",
        )):
            continue
        entries = dict(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=([^\s]+)", line))
        if "FS_C08_REAL_CFD_MASS_BUDGET" in line:
            missing = [field for field in required if field not in entries]
            if missing:
                raise ValueError("real mass/energy budget lacks " + ", ".join(missing))
            try:
                values = {field: float(entries[field]) for field in required}
            except ValueError as exc:
                raise ValueError("non-numeric native CFD mass budget") from exc
            if not all(math.isfinite(value) for value in values.values()):
                raise ValueError("nonfinite mass/energy/volume CFD budget")
            m = values["liquidSolidMetalMass_kg"]
            m0 = values["previousMetalMass_kg"]
            if m <= 0 or m0 <= 0:
                raise ValueError("no positive metal inventory in real CFD")
            if abs(values["metalMassResidual_kg"]) > 1e-7 * max(m, m0):
                raise ValueError("native metal mass balance exceeds 1e-7")
            if (values["gasMassBudgetTolerance_kg"] <= 0
                    or values["nativeGasInventory_kg"] < 0
                    or values["previousGasInventory_kg"] < 0
                    or abs(values["gasContinuityDefect_kg"])
                       > values["gasMassBudgetTolerance_kg"]):
                raise ValueError("native gas mass balance exceeds tolerance")
            budgets.append(values)
        else:
            if "time_s" not in entries:
                raise ValueError("native conservation/thermal PASS without time")
            try:
                t = float(entries["time_s"])
            except ValueError as exc:
                raise ValueError("non-numeric native gate time") from exc
            if not math.isfinite(t) or t <= 0:
                raise ValueError("invalid native gate timestamp")
            if "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED" in line:
                pass_times.append(t)
            if "FS_C08_NATIVE_PHASE_RESOLVED_INTERNAL_ENERGY" in line:
                thermal_times.append(t)

    if not budgets:
        raise ValueError("no actual FS-C08 numerical mass/energy budgets")
    tol = max(1e-9, 1e-6 * abs(final_saved_time_s))
    near_final = lambda t: abs(t - final_saved_time_s) <= tol
    if (not near_final(budgets[-1]["time_s"])
            or not any(near_final(t) for t in pass_times)
            or not any(near_final(t) for t in thermal_times)):
        raise ValueError("last saved CFD time lacks matched physical budget,"
                         " conservation gate, or thermal solve")
    return {
        "numeric_budget_records": len(budgets),
        "mass_conservation_pass_records": len(pass_times),
        "native_thermal_solve_records": len(thermal_times),
        "final_time_s": final_saved_time_s,
        "final_native_mass_energy_budget": budgets[-1],
        "maximum_absolute_metal_residual_kg":
            max(abs(b["metalMassResidual_kg"]) for b in budgets),
        "maximum_absolute_gas_residual_kg":
            max(abs(b["gasContinuityDefect_kg"]) for b in budgets),
        "all_native_mass_budget_records_checked": True,
        "global_energy_verified": False,
        "energy_residual_is_diagnostic_only": True,
        "physical_casting_shrinkage_validated": False,
    }


def require_native_end_time(control_dict: Path) -> float:
    """Read the staged OpenFOAM controlDict's finite requested endTime."""
    data = control_dict.read_text(encoding="utf-8")
    matches = re.findall(
        r"(?m)^\s*endTime\s+([0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)\s*;",
        data,
    )
    require(len(matches) == 1, "staged case requires exactly one numeric endTime")
    value = float(matches[0])
    require(math.isfinite(value) and value > 0, "invalid requested endTime")
    return value


def numeric_time_dirs(case: Path) -> list[tuple[float, Path]]:
    times: list[tuple[float, Path]] = []
    for path in case.iterdir():
        if not path.is_dir():
            continue
        try:
            time = float(path.name)
        except ValueError:
            continue
        if time > 0 and time != float("inf"):
            times.append((time, path))
    return sorted(times)


def execute(source: Path, material: Path, output: Path,
            diagnostics: Path, timeout_minutes: int) -> dict:
    require(os.environ.get("WM_PROJECT_VERSION") == "14",
            "load OpenFOAM Foundation14 before executing the actual solver")
    require(shutil.which("wmake") is not None, "wmake unavailable")
    require(shutil.which("foamMultiRun") is not None, "foamMultiRun unavailable")
    libbin = os.environ.get("FOAM_USER_LIBBIN")
    require(bool(libbin), "FOAM_USER_LIBBIN missing")
    require(timeout_minutes >= 1, "timeout-minutes must be >=1")
    source = source.expanduser().resolve()
    material = material.expanduser().resolve()
    output = output.expanduser().absolute()
    diagnostics = diagnostics.expanduser().absolute()
    require(source.is_dir() and source.name.startswith("FS_C07_THERMAL_"),
            "an untouched accepted FS_C07_THERMAL_* source is required")
    require(material.is_file(), "a sourced alloy fsC08Material dictionary is required")
    require(not output.exists() and not diagnostics.exists(),
            "new run and diagnostic directories must not exist already")

    tracked = ("0/fluid/alpha.metal", "constant/fluid/fvModels", "system/controlDict")
    source_before = {part: digest(source/part) for part in tracked}
    diagnostics.mkdir(parents=True)
    report = {
        "schema": "fs-c08-real-native-cfd-v1",
        "status": "FS_C08_REAL_CFD_NOT_STARTED",
        "source": str(source),
        "material_sha256": digest(material),
        "output_case": str(output),
        "diagnostics": str(diagnostics),
        "native_OpenFOAM14_wmake_verified": False,
        "real_foamMultiRun_started": False,
        "real_CFD_completed": False,
        "field_evolution_verified": False,
        "global_metal_and_gas_mass_verified": False,
        "global_energy_verified": False,
        "experimental_cast_iron_shrinkage_validated": False,
    }
    reportfile = diagnostics / "FS_C08_REAL_CFD_REPORT.json"
    write_report(reportfile, report)

    compile_log = diagnostics / "native_wmake.log"
    try:
        build = run_logged(["wmake", "libso"], BASE_MODULE, compile_log,
                           timeout_minutes=30)
        report["wmake"] = build
        libfile = Path(libbin).expanduser() / "libfsC08ConservativeVoF.so"
        report["native_library"] = str(libfile)
        if build["exit_code"] != 0 or not libfile.is_file():
            report["status"] = "FS_C08_ACTUAL_NATIVE_CFD_LIBRARY_COMPILE_FAIL"
            report["first_compiler_error"] = first_compiler_error(compile_log)
            return report

        report["native_OpenFOAM14_wmake_verified"] = True
        staged = stage(source, material, output)
        report["isolated_case_stage_status"] = staged["status"]
        report["source_sha256_before"] = source_before
        report["source_sha256_after_stage"] = {
            part: digest(source/part) for part in tracked
        }
        require(report["source_sha256_after_stage"] == source_before,
                "FS-C07 source mutated unexpectedly")

        native_log = diagnostics / "foamMultiRun.log"
        report["real_foamMultiRun_started"] = True
        run = run_logged(["foamMultiRun", "-case", str(output)], output,
                         native_log, timeout_minutes)
        report["foamMultiRun"] = run
        if run["exit_code"] != 0:
            report["status"] = "FS_C08_REAL_CFD_NATIVE_RUN_FAILED_OR_INCOMPLETE"
            report["first_run_error"] = first_native_error(native_log)
            return report

        log = native_log.read_text(encoding="utf-8", errors="replace")
        report["per_patch_budget_records"] = log.count(
            "FS_C08_REAL_CFD_PATCH_BUDGET"
        )
        snapshots = numeric_time_dirs(output)
        report["saved_positive_times_s"] = [t for t, _ in snapshots]
        if not snapshots:
            report["status"] = "FS_C08_REAL_CFD_NO_SAVED_POSITIVE_TIME"
            return report

        finaltime, finaldir = snapshots[-1]
        requested_endtime = require_native_end_time(output / "system/controlDict")
        report["requested_endTime_s"] = requested_endtime
        report["latest_saved_time_s"] = finaltime
        # A clean solver exit or a snapshot at t=0.05 is not completion
        # of the full endTime=1 s transient. Never accept partial cooling.
        horizon_tolerance = max(1e-8, 1e-6 * requested_endtime)
        if finaltime + horizon_tolerance < requested_endtime:
            report["status"] = "FS_C08_REAL_CFD_STOPPED_BEFORE_ENDTIME"
            return report
        try:
            report["native_numeric_budget_gate"] = inspect_real_cfd_budgets(
                log, finaltime
            )
        except ValueError as exc:
            report["status"] = "FS_C08_REAL_CFD_NUMERIC_BUDGET_GATE_FAILED"
            report["budget_gate_error"] = str(exc)
            return report
        report["metal_gas_conservation_gate_records"] = (
            report["native_numeric_budget_gate"]["mass_conservation_pass_records"]
        )
        report["native_thermal_solve_records"] = (
            report["native_numeric_budget_gate"]["native_thermal_solve_records"]
        )
        fluid = finaldir / "fluid"
        missing = [name for name in REQUIRED_FINAL_FIELDS
                   if not (fluid / name).is_file()]
        report["latest_saved_time_s"] = finaltime
        report["missing_final_physical_fields"] = missing
        if (missing or not report["metal_gas_conservation_gate_records"]
                or not report["native_thermal_solve_records"]):
            report["status"] = "FS_C08_REAL_CFD_OUTPUTS_OR_BUDGET_GATES_MISSING"
            return report

        report["real_CFD_completed"] = True
        # The presence of written fields is not proof that any quantity
        # changed or that the casting shrank physically.
        report["required_physical_fields_written"] = True
        report["field_evolution_verified"] = False
        report["global_metal_and_gas_mass_verified"] = True
        report["status"] = (
            "FS_C08_REAL_CFD_NATIVE_EXECUTION_WITH_CONSERVATION_GATES_PASS"
            "__NOT_PHYSICAL_SHRINKAGE_VALIDATION"
        )
        return report
    finally:
        report["source_sha256_after"] = {
            part: digest(source / part) for part in tracked
        }
        if report["source_sha256_after"] != source_before:
            report["status"] = "FS_C08_SOURCE_FS_C07_CHANGED__INVALID_RUN"
            report["real_CFD_completed"] = False
            report["global_metal_and_gas_mass_verified"] = False
        write_report(reportfile, report)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True,
                    help="Accepted external FS_C07_THERMAL_* case")
    ap.add_argument("--material", type=Path, required=True,
                    help="Actual sourced alloy fsC08Material dictionary")
    ap.add_argument("--output", type=Path,
                    help="New FS_C08_COUPLED_* path (must not exist)")
    ap.add_argument("--diagnostics", type=Path,
                    help="New FS_C08_REAL_CFD_DIAGNOSTICS_* path")
    ap.add_argument("--timeout-minutes", type=int, default=120)
    args = ap.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(4)
    output = args.output or (
        Path.home() / "OpenFOAM/FS_C08_COUPLED_RUNS"
        / f"FS_C08_COUPLED_{stamp}_{suffix}"
    )
    diagnostics = args.diagnostics or (
        Path.home() / "OpenFOAM/FS_C08_DIAGNOSTICS"
        / f"FS_C08_REAL_CFD_DIAGNOSTICS_{stamp}_{suffix}"
    )
    try:
        report = execute(args.source, args.material, output,
                         diagnostics, args.timeout_minutes)
    except (RuntimeError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("FS-C08 REAL NATIVE CFD REPORT:",
          diagnostics.expanduser().absolute() / "FS_C08_REAL_CFD_REPORT.json")
    print("FS-C08 STATUS:", report["status"])
    return 0 if report["real_CFD_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
