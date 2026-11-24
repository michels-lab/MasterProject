#!/usr/bin/env python3
"""FS-C07 native Foundation14 CHT/VOF cooling transient, NOT a shrinkage solver.

Stages an isolated accepted FS-C06 clone. --native executes actual foamMultiRun
for up to 1 s simulated time with Courant-controlled dt. Numeric reports are
derived only from saved OpenFOAM fields, not predicted or fabricated data.
Source and tracked branch are not modified; no phase density source is added.
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
import time

from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import read_mesh, cell_volume_m3
from stage_fs_c06_vof_solidification import (
    FLUID_CELLS, MODEL_FIELD, phase_volume_metrics,
    read_native_metal_temperature, read_native_solid_fraction,
)

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "freesurface/FS-C07_thermal_transition/native/system/controlDict"
FS_C06_FUNCTIONS = ROOT / "freesurface/FS-C06_vof_solidification/native/system/functions"
FUNCTIONS = ROOT / "freesurface/FS-C07_thermal_transition/native/system/functions"
FVMODELS = ROOT / "freesurface/FS-C06_vof_solidification/native/constant/fluid/fvModels"
MONITORS = (
    "FS_C06_metalVoFVolume", "FS_C06_solidMetalVolume",
    "FS_C06_mixtureMass", "FS_C06_atmosphereMassFlux",
    "FS_C06_atmosphereTopMassFlux", "FS_C06_atmosphereSidesMassFlux",
    "FS_C06_atmosphereLowerSidesMassFlux", "FS_C06_fluidToMoldMassFlux",
    "FS_C06_wallHeatFluxFluid", "FS_C06_wallHeatFluxMold",
)


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("FS-C07 BLOCKED: " + why)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def time_dir(name: str) -> float | None:
    try:
        value = float(name)
    except ValueError:
        return None
    return value if math.isfinite(value) and value >= 0 else None


def source_preflight(src: Path) -> dict:
    require(src.is_dir() and src.name.startswith("FS_C06_VOF_SOLID_SMOKE_"),
            "need native accepted FS-C06 isolated source")
    require(src.is_absolute() and ROOT not in src.parents and src != ROOT,
            "source must be external to Git worktree")
    require(not any(p.is_symlink() for p in src.rglob("*")),
            "source has symlinks; unsafe clone")
    report_file = src / "FS_C06_REPORT.json"
    require(report_file.is_file(), "original native report missing")
    previous = json.loads(report_file.read_text())
    require(previous.get("status") ==
            "FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE"
            and previous.get("native_cfd_executed") is True
            and previous.get("solid_fraction_fields_measured") is True,
            "FS-C06 CFD provenance not accepted")
    for relative in ("0/fluid/alpha.metal",
                     "0/mold/T", "constant/fluid/polyMesh/points",
                     "constant/mold/polyMesh/points"):
        require((src / relative).is_file(), "missing initial file " + relative)
    initial_metal_T = src / "0/fluid/T.metal"
    if not initial_metal_T.is_file():
        initial_metal_T = src / "0/fluid/T"
    require(initial_metal_T.is_file(), "no initial thermal field in accepted fluid case")
    for name in ("1e-07", "2e-07"):
        # Source may use different numeric representations.
        require(any(time_dir(p.name) == float(name)
                    for p in src.iterdir() if p.is_dir()),
                "source missing accepted native time " + name)
    for p in src.iterdir():
        if p.is_dir():
            t = time_dir(p.name)
            require(t is None or t in (0.0, 1e-7, 2e-7),
                    "unexpected or unreviewed source time " + p.name)
    require((src / "constant/fluid/fvModels").read_bytes() == FVMODELS.read_bytes(),
            "native FS-C06 fvModels differs from proven physics")
    require((src / "system/functions").read_bytes() == FS_C06_FUNCTIONS.read_bytes(),
            "native FS-C06 function object definitions changed")
    post = src / "postProcessing"
    require(post.is_dir(), "accepted second run monitors absent")
    available = {}
    for name in MONITORS:
        files = sorted(p for p in post.rglob("*.dat")
                       if name in p.parts and p.stat().st_size > 0)
        require(files, "accepted FS-C06 monitor absent: " + name)
        available[name] = [{"path": str(p.relative_to(src)),
                            "sha256": digest(p)} for p in files]
    return {"native_FS_C06_report_sha256": digest(report_file),
            "source_monitor_sha256": available,
            "initial_temperature_source": str(initial_metal_T.relative_to(src)),
            "initial_temperature_sha256": digest(initial_metal_T),
            "initial_alpha_metal_sha256": digest(src / "0/fluid/alpha.metal")}


def stage(src: Path, dest: Path) -> dict:
    src = src.expanduser().resolve()
    dest = dest.expanduser().absolute()
    require(not dest.exists() and not dest.is_symlink(),
            "isolated FS-C07 destination already exists")
    require(src != dest and src not in dest.parents and dest not in src.parents,
            "source/output overlap")
    require(dest != ROOT and ROOT not in dest.parents,
            "new FS-C07 cases must be external to Git worktree")
    require(dest.name.startswith("FS_C07_THERMAL_"),
            "destination must use FS_C07_THERMAL_ prefix")
    evidence = source_preflight(src)
    control = CONTROL.read_text()
    # Fail closed against accidental smoke reruns, source terms, or unbounded dt.
    for marker in ("endTime         1;", "deltaT          1e-07;",
                   "maxDeltaT       1e-04;", "maxCo           0.1;",
                   "maxAlphaCo      0.1;", "writeControl    adjustableRunTime;",
                   "writeInterval   0.05;"):
        require(marker in control, "native FS-C07 runtime gate drift: " + marker)
    require(re.search(r"(?m)^\s*functions\s*\{", control) is None,
            "function objects must be separate system/functions")
    require(FUNCTIONS.is_file() and FS_C06_FUNCTIONS.is_file(),
            "native FS-C07 or accepted FS-C06 monitoring dictionary missing")
    ftext = FUNCTIONS.read_text()
    require(ftext.count("writeControl  writeTime;") == len(MONITORS),
            "FS-C07 must write each native monitor on main writeTime")
    require("writeControl  timeStep;" not in ftext,
            "FS-C07 monitor writes every CFD timestep; storage explosion risk")
    require(ftext.count("writeInterval 1;") == len(MONITORS),
            "FS-C07 monitor write interval drift")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, symlinks=False)
    (dest / "FS_C06_REPORT.json").rename(dest / "FS_C06_PARENT_REPORT.json")
    # Remove only past outputs from the NEW clone; original WSL source is intact.
    shutil.rmtree(dest / "postProcessing")
    for p in list(dest.iterdir()):
        t = time_dir(p.name) if p.is_dir() else None
        if t is not None and t > 0:
            shutil.rmtree(p)
    shutil.copyfile(CONTROL, dest / "system/controlDict")
    shutil.copyfile(FUNCTIONS, dest / "system/functions")
    require((dest / "system/controlDict").read_bytes() == CONTROL.read_bytes(),
            "native controlDict installation drift")
    require((dest / "system/functions").read_bytes() == FUNCTIONS.read_bytes(),
            "native functions installation drift")
    record = {
        "schema": "masterproject-fs-c07-native-thermal-transition-v1",
        "status": "FS_C07_STAGED_NO_CFD",
        "source_accepted_FS_C06": str(src),
        "isolated_case": str(dest),
        "source_evidence": evidence,
        "native_controlDict_sha256": digest(dest / "system/controlDict"),
        "native_functions_sha256": digest(dest / "system/functions"),
        "native_fvModels_sha256": digest(dest / "constant/fluid/fvModels"),
        "native_cfd_executed": False,
        "liquidus_crossing_observed": False,
        "positive_solid_fraction_observed": False,
        "volumetric_shrinkage_implemented": False,
        "feeding_implemented": False,
        "phase_density_coupling_implemented": False,
        "global_mass_energy_validated": False,
        "C14_reference_not_calibrated_JMatPro": True,
        "thermal_screen_endTime_s": 1.0,
        "maxDeltaT_s": 1e-4,
        "write_interval_s": 0.05,
    }
    (dest / "FS_C07_REPORT.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def audit_native_monitor_files(dest: Path, final_time: float) -> dict:
    """Read native Foundation14 .dat records; not a global balance claim."""
    post = dest / "postProcessing"
    require(post.is_dir(), "FS-C07 native postProcessing missing")
    result = {}
    for name in MONITORS:
        files = sorted(p for p in post.rglob("*.dat")
                       if name in p.parts and p.stat().st_size > 0)
        require(files, "native monitor did not write data: " + name)
        for p in files:
            lines = p.read_text(errors="strict").splitlines()
            require(any(line.lstrip().startswith("# Time") for line in lines),
                    "native monitor .dat header missing: " + str(p))
            rows = [line.split() for line in lines
                    if line.strip() and not line.lstrip().startswith("#")]
            require(rows, "native monitor has no numerical rows: " + str(p))
            records = []
            for row in rows:
                try:
                    t = float(row[0])
                except (ValueError, IndexError) as exc:
                    raise ValueError("invalid native monitor time: " + str(p)) from exc
                values = []
                for token in row[1:]:
                    try:
                        val = float(token)
                    except ValueError:
                        # wallHeatFlux.dat has a patch-name string after time.
                        continue
                    require(math.isfinite(val), "nonfinite monitor value: " + str(p))
                    values.append(val)
                require(math.isfinite(t) and t >= 0 and values,
                        "empty/nonfinite numerical monitor record: " + str(p))
                records.append((t, row))
            require(abs(records[-1][0] - final_time) < 5e-4,
                    "native monitor did not reach last saved solver time: " + str(p))
            result[name] = {
                "path": str(p.relative_to(dest)),
                "sha256": digest(p),
                "rows": len(records),
                "time_last_s": records[-1][0],
                "last_native_raw_columns": records[-1][1],
            }
    return result


def audit_saved_fields(dest: Path, report: dict) -> dict:
    from stage_fs_c06_vof_solidification import check_solid_fraction
    mesh = read_mesh(dest / "constant/fluid/polyMesh", FLUID_CELLS)
    volumes = [cell_volume_m3(mesh, i) for i in range(FLUID_CELLS)]
    initial = read_alpha(dest / "0/fluid/alpha.metal", expected_cells=FLUID_CELLS)
    initial_volume = math.fsum(v * a for v, a in zip(volumes, initial))
    require(initial_volume > 0, "source metal volume must be positive")
    liquidus = 1473.0  # Actual C14 model table; numerical reference, not JMatPro
    times = sorted((t, p) for p in dest.iterdir() if p.is_dir()
                   if (t := time_dir(p.name)) is not None and t > 0)
    require(times, "native solver wrote no time steps")
    snapshots = []
    for t, time_path in times:
        fluid = time_path / "fluid"
        if not (fluid / MODEL_FIELD).is_file():
            continue  # A solver write may be partial; report exactly what exists.
        alpha = read_alpha(fluid / "alpha.metal", expected_cells=FLUID_CELLS)
        solid = read_native_solid_fraction(fluid / MODEL_FIELD, expected_cells=FLUID_CELLS)
        T = read_native_metal_temperature(fluid / "T.metal",
                                          expected_cells=FLUID_CELLS)
        phase = phase_volume_metrics(volumes, alpha, solid, T, liquidus)
        core_T = [temp for a, temp in zip(alpha, T) if a >= 0.5]
        snapshots.append({
            "time_s": t,
            **phase,
            **check_solid_fraction(alpha, solid),
            "metal_T_min_K_where_alpha_ge_0p5": min(core_T) if core_T else None,
            "metal_T_max_K_where_alpha_ge_0p5": max(core_T) if core_T else None,
            "metal_vof_relative_volume_change_from_t0":
                (phase["metal_vof_volume_m3"] - initial_volume) / initial_volume,
            "native_fields_sha256": {name: digest(fluid / name)
                for name in ("alpha.metal", MODEL_FIELD, "T.metal")},
        })
    require(snapshots, "no complete native phase field snapshots")
    require(snapshots[-1]["time_s"] >= 0.999,
            "1 s native thermal horizon not reached; preserve files, no completed claim")
    monitor_records = audit_native_monitor_files(dest, snapshots[-1]["time_s"])
    report.update({
        "status": "FS_C07_NATIVE_THERMAL_SCREEN_COMPLETED_NO_SHRINKAGE_MODEL",
        "native_10_monitors_values_reviewed": True,
        "native_monitor_records": monitor_records,
        "native_cfd_executed": True,
        "native_saved_phase_snapshots": snapshots,
        "initial_metal_vof_volume_m3": initial_volume,
        "liquidus_crossing_observed": any(
            s["metal_vof_fraction_below_C14_liquidus"] > 0 for s in snapshots),
        "positive_solid_fraction_observed": any(
            s["metal_solid_volume_m3"] > 0 for s in snapshots),
        "global_mass_energy_validated": False,
        "volumetric_shrinkage_implemented": False,
        "feeding_implemented": False,
        "phase_density_coupling_implemented": False,
    })
    return report


def read_cfd_time_from_log(log: Path) -> tuple[float | None, int]:
    """Read only the tail of a growing native solver log (no CFD work)."""
    try:
        with log.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 65536), os.SEEK_SET)
            tail = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None, 0
    matches = re.findall(
        r"(?m)^\s*Time\s*=\s*([0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?)",
        tail,
    )
    return (float(matches[-1]) if matches else None), size


def _stop_native_child(proc: subprocess.Popen, log: Path, why: str) -> None:
    """Leave a stopped child and preserve every saved OpenFOAM file."""
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=15)
    raise ValueError(f"{why}; native logs/fields preserved: {log}")


def run_native(dest: Path, report: dict, timeout_minutes: int) -> dict:
    require(os.getenv("WM_PROJECT_VERSION") == "14",
            "native run needs sourced OpenFOAM Foundation 14")
    require(shutil.which("foamMultiRun") is not None,
            "native foamMultiRun not found")
    require(1 <= timeout_minutes <= 240, "timeout must be 1..240 minutes")
    log = dest / "log.FS_C07_foamMultiRun"
    started = time.monotonic()
    print("FS-C07 LIVE LOG:", log, flush=True)
    print("FS-C07 RUN: each 15s prints elapsed wall time and latest native Time; "
          "no fields are inferred from missing log data.", flush=True)
    with log.open("w") as fh:
        proc = subprocess.Popen(["foamMultiRun", "-case", str(dest)],
                                stdout=fh, stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                remaining = timeout_minutes*60 - (time.monotonic() - started)
                if remaining <= 0:
                    _stop_native_child(proc, log, f"FS-C07 watchdog timeout at {timeout_minutes} minutes")
                try:
                    proc.wait(timeout=min(15.0, remaining))
                except subprocess.TimeoutExpired:
                    simtime, logsize = read_cfd_time_from_log(log)
                    elapsed = time.monotonic() - started
                    print(f"FS-C07 LIVE: wall={elapsed:.0f}s, "
                          f"CFD_Time={simtime if simtime is not None else 'not-yet-found'}, "
                          f"log={logsize} bytes", flush=True)
            require(proc.returncode == 0,
                    f"foamMultiRun returned {proc.returncode}; inspect {log}")
        except KeyboardInterrupt:
            _stop_native_child(proc, log, "FS-C07 user interrupted")
    report["native_log_sha256"] = digest(log)
    # A solver that returned 0 is *executed and completed* even if the
    # subsequent phase-allocation audit blocks physical acceptance. Save this
    # fact BEFORE the scientific audit so the failure handler does not
    # rewrite a real 1 s run as "native_cfd_executed=false".
    report["native_cfd_executed"] = True
    report["native_solver_completed"] = True
    report["status"] = "FS_C07_NATIVE_SOLVER_COMPLETED_PHASE_AUDIT_PENDING"
    report["last_native_log_time_s"], report["native_log_size_bytes"] = (
        read_cfd_time_from_log(log)
    )
    (dest / "FS_C07_REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    return audit_saved_fields(dest, report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--native", action="store_true",
                        help="Run real foamMultiRun on isolated NEW case")
    parser.add_argument("--timeout-minutes", type=int, default=120)
    a = parser.parse_args()
    target = a.out or (Path.home() / "OpenFOAM/FS_C07_RUNS" /
                       ("FS_C07_THERMAL_" +
                        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                        + "_" + secrets.token_hex(4)))
    target = target.expanduser().absolute()
    try:
        report = stage(a.source, target)
        print("FS-C07 ISOLATED CASE:", target, flush=True)
        print("FS-C07 CASE PREPARED, NO PHYSICAL SHRINKAGE/FEEDING", flush=True)
        if a.native:
            print("FS-C07 starting native 1s thermal screening (not shrinkage)...",
                  flush=True)
            report = run_native(target, report, a.timeout_minutes)
            (target / "FS_C07_REPORT.json").write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n")
            print("FS-C07 NATIVE SCREEN:", report["status"])
            print("FS-C07 LIQUIDUS CROSSED:",
                  report["liquidus_crossing_observed"])
            print("FS-C07 POSITIVE SOLID:",
                  report["positive_solid_fraction_observed"])
            print("FS-C07 PHYSICAL SHRINKAGE: NOT IMPLEMENTED")
        else:
            print("FS-C07 STAGED ONLY: --native executes actual Foundation14 CFD")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("FS-C07 ROOT CAUSE:", str(exc), file=sys.stderr)
        if target.exists() and (target / "FS_C07_REPORT.json").exists():
            old = json.loads((target / "FS_C07_REPORT.json").read_text())
            old["status"] = "FS_C07_INCOMPLETE_PRESERVE_EVIDENCE"
            old["last_error"] = str(exc)
            log = target / "log.FS_C07_foamMultiRun"
            if log.is_file():
                last_time, log_bytes = read_cfd_time_from_log(log)
                old["last_native_log_time_s"] = last_time
                old["last_native_log_size_bytes"] = log_bytes
                old["solver_log_path"] = str(log)
            (target / "FS_C07_REPORT.json").write_text(
                json.dumps(old, indent=2) + "\n")
            print("FS-C07 LAST NATIVE CFD TIME:",
                  old.get("last_native_log_time_s", "not available"),
                  file=sys.stderr)
            print("FS-C07 EVIDENCE PRESERVED:", target, file=sys.stderr)
            print("FS-C07 SEE FS_C07_REPORT.json:last_error "
                  "AND log.FS_C07_foamMultiRun", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
