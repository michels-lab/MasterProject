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
from contextlib import contextmanager
import fcntl
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
from fs_c08_transient_ledger import write_transient_ledger

REQUIRED_FINAL_FIELDS = (
    "rhoAlpha.liquid", "rhoAlpha.solid", "alpha.metal",
    "alpha.metal.solid", "internalEnergy.fsC08",
    "Gamma.fsC08", "SvolMaterial.fsC08",
    "rhoAlpha.airTrial.fsC08", "alpha.air", "rhoLiquid.fsC08", "rhoSolid.fsC08",
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


@contextmanager
def native_library_lock():
    """Serialize builds and executions using the shared user library.
    The batch holds this lock until its worker cases have all stopped.
    External manual wmake commands are outside this lock's protection.
    """
    libbin = os.environ.get("FOAM_USER_LIBBIN")
    require(bool(libbin), "FOAM_USER_LIBBIN missing")
    directory = Path(libbin).expanduser()
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".fsC08-native-run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def build_native_library(logfile: Path) -> dict:
    require(os.environ.get("WM_PROJECT_VERSION") == "14",
            "load OpenFOAM Foundation14")
    require(shutil.which("wmake") is not None, "wmake unavailable")
    libbin = os.environ.get("FOAM_USER_LIBBIN")
    require(bool(libbin), "FOAM_USER_LIBBIN missing")
    libfile = Path(libbin).expanduser() / "libfsC08ConservativeVoF.so"
    print("FS-C08 native build log:", logfile, flush=True)
    build = run_logged(["wmake", "libso"], BASE_MODULE, logfile, 30)
    ok = build["exit_code"] == 0 and libfile.is_file()
    return {"wmake": build, "native_library": str(libfile),
            "native_library_sha256": digest(libfile) if ok else None,
            "build_log": str(logfile),
            "verified": ok,
            "first_compiler_error": None if ok else first_compiler_error(logfile),
            "compiler_error_context": [] if ok else compiler_error_context(logfile)}


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


def compiler_error_context(logfile: Path) -> list[str]:
    """Preserve template instantiation context and trailing build failure."""
    lines = logfile.read_text(encoding="utf-8", errors="replace").splitlines()
    first = next((i for i, line in enumerate(lines)
                  if re.search(r"fatal error:|(?<![a-z])error:|undefined reference",
                               line, re.IGNORECASE)), None)
    if first is None:
        return lines[-40:]
    indices = sorted(set(range(max(0, first-25), min(len(lines), first+35)))
                     | set(range(max(0, len(lines)-12), len(lines))))
    return [lines[i][:2000] for i in indices]


def first_native_error(logfile: Path) -> str | None:
    """Prefer actual fatal details to startup diagnostics and warning banners."""
    lines = logfile.read_text(encoding="utf-8", errors="replace").splitlines()
    fatal = re.compile(r"FOAM FATAL(?: IO)? ERROR", re.IGNORECASE)
    for i, line in enumerate(lines):
        if fatal.search(line):
            detail = next((x.strip() for x in lines[i+1:]
                           if x.strip()), "")
            return (line.strip() + (" | " + detail if detail else ""))[:1000]
    pattern = re.compile(
        r"floating point exception|segmentation fault|error:|"
        r"cannot open shared object|unknown solver|uncaught exception|"
        r"FS_C08_RUNTIME_TIMEOUT",
        flags=re.IGNORECASE,
    )
    for line in lines:
        if re.search(r"Enabling floating point exception trapping", line,
                     re.IGNORECASE):
            continue
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


def inspect_coupled_volume_closure(log: str, final_saved_time_s: float) -> dict:
    """Require real three-phase local closure for every accepted pressure step."""
    last_iter = {}
    accepted = []
    fields = {"maxVolumeResidual": 1e-12, "maxDeltaT_K": 1e-6,
              "maxPhaseReplayRelative": 1e-10, "maxMetalOverfill": 1e-12,
              "maxLocalMetalContinuity": 1e-10, "maxLocalGasContinuity": 1e-10}
    for line in log.splitlines():
        iteration = "FS_C08_COUPLED_VOLUME_ENERGY_ITER" in line
        pressure = "FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY" in line
        if not iteration and not pressure:
            continue
        entries = dict(re.findall(r"([A-Za-z][A-Za-z0-9_]*)=([^\s]+)", line))
        try:
            t = float(entries["time_s"])
            if not math.isfinite(t) or t <= 0:
                raise ValueError("invalid coupled time")
            if iteration:
                values = {key: float(entries[key]) for key in fields}
                if not all(math.isfinite(v) and v >= 0 for v in values.values()):
                    raise ValueError("nonfinite or negative coupled residual")
                last_iter[t] = values
            else:
                if entries.get("pressureVolumeEnergyIterationConverged") != "1":
                    raise ValueError("old or unconverged pressure path")
                mismatch = float(entries["gasEOSMismatch"])
                if not math.isfinite(mismatch) or not 0 <= mismatch <= 2e-12:
                    raise ValueError("independent gas EOS mismatch")
                if t not in last_iter or any(last_iter[t][k] > v for k,v in fields.items()):
                    raise ValueError("accepted pressure step without converged local closure")
                accepted.append((t, last_iter[t], mismatch))
        except (KeyError, ValueError) as exc:
            raise ValueError("invalid coupled volume evidence: " + str(exc)) from exc
    if not accepted or abs(accepted[-1][0]-final_saved_time_s) > max(1e-9,1e-6*abs(final_saved_time_s)):
        raise ValueError("no final accepted three-phase pressure-volume closure")
    return {
        "accepted_pressure_closure_records": len(accepted),
        "final_time_s": accepted[-1][0],
        "final_local_closure": accepted[-1][1],
        "max_accepted_volume_residual": max(v["maxVolumeResidual"] for _,v,_ in accepted),
        "max_accepted_gas_eos_mismatch": max(x[2] for x in accepted),
        "global_energy_verified": False,
        "physical_shrinkage_validated": False,
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


def inspect_fixed_probe_schedule(log: str, snapshots: list[tuple[float, Path]],
                                 dt: float, steps: int) -> dict:
    """Require every requested positive step, not merely the final marker."""
    expected = [dt*i for i in range(1, steps+1)]
    tol = max(1e-14, dt*1e-6)
    def matches(times, name, unique=True):
        values = sorted(times)
        if unique:
            if len(values)!=steps or any(abs(a-b)>tol for a,b in zip(values, expected)):
                raise ValueError("probe schedule mismatch: "+name)
        elif any(not any(abs(t-e)<=tol for t in values) for e in expected):
            raise ValueError("probe schedule missing timestep: "+name)
    matches([t for t,_ in snapshots], "saved fields")
    marker_names = {
        "pressure": "FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY",
        "mass_budget": "FS_C08_REAL_CFD_MASS_BUDGET",
        "mass_pass": "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED",
        "thermal": "FS_C08_NATIVE_PHASE_RESOLVED_INTERNAL_ENERGY",
    }
    marker_times = {key: [] for key in marker_names}
    for line in log.splitlines():
        for key, marker in marker_names.items():
            if marker in line:
                m = re.search(r"\btime_s=([^\s]+)", line)
                if not m:
                    raise ValueError("missing probe timestamp: "+key)
                t = float(m.group(1))
                if not math.isfinite(t):
                    raise ValueError("nonfinite probe timestamp: "+key)
                marker_times[key].append(t)
    for key, times in marker_times.items():
        matches(times, key, unique=key!="thermal")
    for time, directory in snapshots:
        missing = [field for field in REQUIRED_FINAL_FIELDS
                   if not ((directory/"fluid"/field).is_file()
                           or (directory/"fluid"/(field+".gz")).is_file())]
        if missing:
            raise ValueError(f"probe time {time:g} missing fields: {missing}")
    return {"expected_steps": steps, "verified_steps": steps,
            "dt_s": dt, "endTime_s": expected[-1],
            "all_step_mass_pressure_and_thermal_records_present": True,
            "all_step_physical_fields_present": True}


def execute(source: Path, material: Path, output: Path,
            diagnostics: Path, timeout_minutes: int,
            laminar_reference: bool = False,
            startup_probe_dt: float | None = None,
            startup_probe_steps: int = 1,
            momentum_face_mobility: str = "linear",
            momentum_matrix_coupling: str = "legacy",
            phase_pressure_mobility: str = "separate",
            momentum_flux_mode: str = "incremental",
            energy_donor_mode: str = "legacy",
            pressure_transport_support: str = "trial",
            *, verified_batch_build: dict | None = None) -> dict:
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
    if laminar_reference:
        tracked += ("constant/fluid/momentumTransport",)
    source_before = {part: digest(source/part) for part in tracked}
    diagnostics.mkdir(parents=True)
    report = {
        "schema": "fs-c08-real-native-cfd-v1",
        "status": "FS_C08_REAL_CFD_NOT_STARTED",
        "source": str(source),
        "material_sha256": digest(material),
        "transport_reference": "laminar_molecular" if laminar_reference else "inherited_RAS",
        "output_case": str(output),
        "momentum_face_mobility": momentum_face_mobility,
        "momentum_matrix_coupling": momentum_matrix_coupling,
        "phase_pressure_mobility": phase_pressure_mobility,
        "momentum_flux_mode": momentum_flux_mode,
        "energy_donor_mode": energy_donor_mode,
        "pressure_transport_support": pressure_transport_support,
        "startup_probe_dt_s": startup_probe_dt,
        "startup_probe_steps": startup_probe_steps if startup_probe_dt is not None else None,
        "startup_probe_only": startup_probe_dt is not None,
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
        receipt = (build_native_library(compile_log) if verified_batch_build is None
                   else verified_batch_build)
        report["wmake"] = receipt["wmake"]
        report["native_library"] = receipt["native_library"]
        report["native_library_sha256"] = receipt["native_library_sha256"]
        report["native_build_log"] = receipt["build_log"]
        report["shared_batch_build"] = verified_batch_build is not None
        libfile = Path(libbin).expanduser() / "libfsC08ConservativeVoF.so"
        if not receipt["verified"]:
            report["status"] = "FS_C08_ACTUAL_NATIVE_CFD_LIBRARY_COMPILE_FAIL"
            report["first_compiler_error"] = receipt["first_compiler_error"]
            return report
        require(libfile.is_file() and digest(libfile) == receipt["native_library_sha256"],
                "native library differs from verified build")
        report["native_OpenFOAM14_wmake_verified"] = True
        staged = stage(source, material, output, laminar_reference, startup_probe_dt, startup_probe_steps, momentum_face_mobility, momentum_matrix_coupling, phase_pressure_mobility, momentum_flux_mode, energy_donor_mode, pressure_transport_support)
        report["isolated_case_stage_status"] = staged["status"]
        report["source_sha256_before"] = source_before
        report["source_sha256_after_stage"] = {
            part: digest(source/part) for part in tracked
        }
        require(report["source_sha256_after_stage"] == source_before,
                "FS-C07 source mutated unexpectedly")

        native_log = diagnostics / "foamMultiRun.log"
        report["real_foamMultiRun_started"] = True
        write_report(reportfile, report)
        print("FS-C08 native CFD log:", native_log, flush=True)
        run = run_logged(["foamMultiRun", "-case", str(output)], output,
                         native_log, timeout_minutes)
        report["foamMultiRun"] = run
        # Always include actionable evidence for a failed native attempt.
        log = native_log.read_text(encoding="utf-8", errors="replace")
        report["transient_ledger"] = write_transient_ledger(log, diagnostics)
        markers = ("FS_C08_INITIAL_GAS_INVENTORY", "FS_C08_PRE_ENERGY_VOLUME",
                   "FS_C08_ACCEPTED_STATE_LEDGER", "FS_C08_LOCAL_ENERGY_LEDGER",
                   "FS_C08_THERMAL_TRANSPORT_SPLIT", "FS_C08_THREE_PHASE_TRIAL_VOLUME",
                   "FS_C08_TRIAL_VOLUME_COMPONENTS", "FS_C08_VOLUME_STEP_BOUND",
                   "FS_C08_VOLUME_JACOBIAN_AUDIT",
                   "FS_C08_VOLUME_DONOR_CAPACITY",
                   "FS_C08_PREDICTOR_DONOR_CAPACITY",
                   "FS_C08_MOMENTUM_REFRESH_BEGIN",
                   "FS_C08_MOMENTUM_REFRESH_ASSEMBLED",
                   "FS_C08_MOMENTUM_REFRESH_PRESSURE_BC_READY",
                   "FS_C08_IN_SOLVER_PHASE_MASS_EQUATIONS",
                   "FS_C08_EQUILIBRIUM_PRESSURE_INVENTORY",
                   "FS_C08_FIXED_T_EQUILIBRIUM_REPLAY",
                   "FS_C08_VOLUME_PROJECTION_REJECTED",
                   "FS_C08_FIXED_T_VOLUME_PROJECTION_CONVERGED",
                   "FS_C08_COUPLED_VOLUME_ENERGY_ITER",
                   "FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY")
        report["native_diagnostic_tail"] = [
            line.strip() for line in log.splitlines()
            if any(marker in line for marker in markers)
        ][-30:]
        report["phase_energy_split_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_PHASE_ENERGY_SPLIT" in line
        ]
        report["pressure_transport_support_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_PRESSURE_TRANSPORT_SUPPORT" in line
        ]
        report["interface_transport_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_INTERFACE_TRANSPORT_AUDIT" in line
        ]
        report["phase_pressure_mobility_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_PHASE_PRESSURE_MOBILITY" in line
        ]
        report["startup_pressure_attribution_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_STARTUP_PRESSURE_COMPONENT" in line
            or "FS_C08_STARTUP_PRESSURE_ATTRIBUTION" in line
        ]
        report["initial_projection_jacobian_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_VOLUME_JACOBIAN_AUDIT" in line
        ][:5]
        report["momentum_force_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_MOMENTUM_FORCE_SPLIT" in line
            or "FS_C08_FRESH_MOMENTUM_DEFECT" in line
        ]
        report["momentum_consistency_records"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_MOMENTUM_CONSISTENCY" in line
        ]
        report["accepted_extreme_cells"] = [
            line.strip() for line in log.splitlines()
            if "FS_C08_ACCEPTED_EXTREME_CELL" in line
        ][-6:]
        report["accepted_pressure_records"] = log.count(
            "pressureVolumeEnergyIterationConverged=1")
        snapshots = numeric_time_dirs(output)
        report["saved_positive_times_s"] = [t for t,_ in snapshots]
        if snapshots:
            report["latest_saved_time_s"] = snapshots[-1][0]
        if run["exit_code"] != 0:
            report["status"] = "FS_C08_REAL_CFD_NATIVE_RUN_FAILED_OR_INCOMPLETE"
            report["first_run_error"] = first_native_error(native_log)
            return report

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
            report["native_coupled_volume_gate"] = inspect_coupled_volume_closure(
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
        # Native OpenFOAM can write either uncompressed or gzip fields.
        # Do not confuse an on-disk compression option with missing physics.
        missing = [name for name in REQUIRED_FINAL_FIELDS
                   if not ((fluid / name).is_file()
                           or (fluid / (name + ".gz")).is_file())]
        report["latest_saved_time_s"] = finaltime
        report["missing_final_physical_fields"] = missing
        if (missing or not report["metal_gas_conservation_gate_records"]
                or not report["native_thermal_solve_records"]):
            report["status"] = "FS_C08_REAL_CFD_OUTPUTS_OR_BUDGET_GATES_MISSING"
            return report

        if startup_probe_dt is not None:
            try:
                report["fixed_probe_schedule_gate"] = inspect_fixed_probe_schedule(
                    log, snapshots, startup_probe_dt, startup_probe_steps)
            except ValueError as exc:
                report["status"] = "FS_C08_FIXED_PROBE_SCHEDULE_GATE_FAILED"
                report["budget_gate_error"] = str(exc)
                return report
        report["real_CFD_completed"] = True
        # The presence of written fields is not proof that any quantity
        # changed or that the casting shrank physically.
        report["required_physical_fields_written"] = True
        report["field_evolution_verified"] = False
        report["global_metal_and_gas_mass_verified"] = True
        report["status"] = (
            "FS_C08_STARTUP_PROBE_CONSERVATION_GATES_PASS__NOT_FULL_TRANSIENT"
            if startup_probe_dt is not None else
            "FS_C08_REAL_CFD_NATIVE_EXECUTION_WITH_CONSERVATION_GATES_PASS"
            "__NOT_PHYSICAL_SHRINKAGE_VALIDATION"
        )
        return report
    finally:
        report["source_sha256_after"] = {
            part: digest(source / part) for part in tracked
        }
        if report.get("native_OpenFOAM14_wmake_verified"):
            library = Path(report["native_library"])
            if not library.is_file() or digest(library) != report["native_library_sha256"]:
                report["status"] = "FS_C08_NATIVE_LIBRARY_CHANGED__INVALID_RUN"
                report["real_CFD_completed"] = False
                report["global_metal_and_gas_mass_verified"] = False
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
    ap.add_argument("--laminar-reference", action="store_true",
                    help="Controlled molecular transport reference; preserves source RAS")
    ap.add_argument("--startup-probe-dt", type=float,
                    help="One fixed real CFD step; not a full casting transient")
    ap.add_argument("--startup-probe-steps", type=int, default=1,
                    help="Consecutive fixed-dt steps; every step must pass audits")
    ap.add_argument("--momentum-face-mobility", choices=("linear","harmonic"), default="linear")
    ap.add_argument("--momentum-matrix-coupling", choices=("legacy","refreshBeforePressure"), default="legacy")
    ap.add_argument("--phase-pressure-mobility", choices=("separate","phaseWeighted"), default="separate")
    ap.add_argument("--momentum-flux-mode",choices=("incremental","totalUpwind","incrementalNoDdtCorr","totalUpwindNoDdtCorr"),default="incremental")
    ap.add_argument("--energy-donor-mode",choices=("legacy","oldGas","currentLiquid","oldGasCurrentLiquid"),default="legacy")
    ap.add_argument("--pressure-transport-support",choices=("trial","oldLiquid","oldGas","oldBoth"),default="trial")
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
        with native_library_lock():
            report = execute(args.source, args.material, output,
                             diagnostics, args.timeout_minutes, args.laminar_reference,
                             args.startup_probe_dt, args.startup_probe_steps, args.momentum_face_mobility, args.momentum_matrix_coupling, args.phase_pressure_mobility, args.momentum_flux_mode, args.energy_donor_mode, args.pressure_transport_support)
    except (RuntimeError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("FS-C08 REAL NATIVE CFD REPORT:",
          diagnostics.expanduser().absolute() / "FS_C08_REAL_CFD_REPORT.json")
    print("FS-C08 STATUS:", report["status"])
    for key in ("first_compiler_error", "first_run_error", "budget_gate_error",
                "accepted_pressure_records", "latest_saved_time_s",
                "missing_final_physical_fields",
                "metal_gas_conservation_gate_records",
                "native_thermal_solve_records", "fixed_probe_schedule_gate"):
        if key in report:
            print(key + ":", report[key])
    for line in report.get("phase_energy_split_records", [])[-3:]:
        print(line)
    for line in report.get("interface_transport_records", [])[-3:]:
        print(line)
    for line in report.get("phase_pressure_mobility_records", [])[-6:]:
        print(line)
    for line in report.get("momentum_force_records", [])[-6:]:
        print(line)
    for line in report.get("momentum_consistency_records", [])[-3:]:
        print(line)
    for line in report.get("accepted_extreme_cells", []):
        print(line)
    for key in ("native_numeric_budget_gate", "native_coupled_volume_gate", "transient_ledger"):
        if key in report:
            print(key + ":", json.dumps(report[key], sort_keys=True))
    if not report["real_CFD_completed"] or report.get("startup_probe_only"):
        for line in report.get("native_diagnostic_tail", []):
            print(line)
    return 0 if report["real_CFD_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
