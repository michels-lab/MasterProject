#!/usr/bin/env python3
"""Isolated MPI pilot/full adaptive run; OpenFOAM Foundation 14, no serial overwrite."""
from __future__ import annotations
import argparse
import csv
import fcntl
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time

import run_adaptive_campaign_200s as adaptive
import transfer_campaign_200s as transfer

ROOT = adaptive.HOME / "CAMPAIGN_200S_ADAPTIVE_MPI_01"
CASES = ("C14-3DB-200s", "C14-3DA-200s", "B14-2D-200s")
need = adaptive.need
read = adaptive.read
dump = adaptive.dump

def execute(case, filename, args, on_line=None):
    print("START", filename, " ".join(args), flush=True)
    started = time.monotonic()
    with (case / filename).open("x", buffering=1) as log:
        p = subprocess.Popen(args, cwd=case, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True,
                             errors="replace", start_new_session=True)
        try:
            for line in p.stdout:
                log.write(line)
                if on_line:
                    on_line(line)
                elif line.strip():
                    print(line.rstrip(), flush=True)
            need(p.wait() == 0, "native command failed: " + filename)
        except BaseException:
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                    p.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()
                except ProcessLookupError:
                    p.wait()
            raise
    return time.monotonic() - started

def prepare(case, url, ranks, end, no_max_co=False):
    # Fetch original verified inputs, never copy a live or previously run case.
    with tempfile.TemporaryDirectory(prefix="mpi-input-", dir=case.parent) as tmp:
        p = Path(tmp)
        archive = p / "input.tar.gz"
        m = transfer.download(url, transfer.INPUT_BRANCH, p / "git", archive)
        need(m["kind"] == "inputs" and m["solver_commit"] == transfer.PIN
             and case.name in m["cases"], "wrong input archive")
        stage = p / "unpacked"
        stage.mkdir()
        transfer.extract(archive, stage)
        src = stage / transfer.COMPACT.name / case.name
        r = transfer.untouched(src)
        for name in ("0", "constant", "system"):
            shutil.copytree(src / name, case / name)
        need(transfer.input_hashes(case) == r["input_sha256"], "copy drift")
        changed = adaptive.adapt_dicts(case)
        if no_max_co:
            p = case / "system/controlDict"
            content, count = re.subn(r"(?m)^[ \t]*maxCo[ \t]+0\.25[ \t]*;[ \t]*(?:\n|$)", "", p.read_text())
            need(count == 1 and not re.search(r"(?m)^[ \t]*maxCo\b", content), "unexpected maxCo entry")
            p.write_text(content)
            changed["system/controlDict"] = transfer.sha(p)
        if end != 200:
            p = case / "system/controlDict"
            p.write_text(adaptive.edit_key(p.read_text(), "endTime", "200", str(end)))
            changed["system/controlDict"] = transfer.sha(p)
        if ranks > 1:
            p = case / "system/decomposeParDict"
            need(not p.exists(), "unexpected existing decomposeParDict")
            p.write_text("FoamFile\n{\n    version 2.0;\n    format ascii;\n"
                         "    class dictionary;\n    object decomposeParDict;\n}\n"
                         f"numberOfSubdomains {ranks};\nmethod scotch;\n")
            changed["system/decomposeParDict"] = transfer.sha(p)
        after = transfer.input_hashes(case)
        need({k for k in set(after) | set(r["input_sha256"])
              if after.get(k) != r["input_sha256"].get(k)} == set(changed),
             "unexpected input changes")
        r.update(status="MPI_PREPARED", solver_completed=False, physical_validation=False,
                 execution_mode="serial_reference" if ranks == 1 else "mpi",
                 mpi_ranks=ranks, target_time_s=end, time_mode="adaptive_uncapped",
                 initial_dt_s=.001, max_co=None if no_max_co else .25, max_dt_s=None,
                 max_co_policy="omit explicit maxCo; native remaining limits" if no_max_co else "explicit 0.25",
                 fixed_input_sha256=r["input_sha256"], input_sha256=after,
                 changed_time_control_files=changed, source_transfer_sha256=m["archive_sha256"],
                 profile_target_interval_s=.1, volume_target_interval_s=1.0,
                 probe_cadence="every actual solver step", solver_steps_target=None,
                 probe_samples_target=None)
        dump(case / adaptive.REPORT, r)
        (case / (case.name + ".foam")).touch()
        return r

def run(case, r, ranks, end):
    steps, dts, cos = [], [], []
    last = 0.
    dt_log = co_log = None
    ended = fatal = False
    last_progress = 0.
    previous_wall = None
    phase = "decomposition"
    try:
        need(transfer.input_hashes(case) == r["input_sha256"], "input hash drift")
        projected = r["disk_projection"]["projected_bytes_with_50pct_margin"]
        reserve = adaptive.RESERVE
        # Keep original processor data and reconstructed data.
        need(shutil.disk_usage(case).free >= reserve + 2 * projected * end / 200,
             "insufficient disk reserve for distributed and reconstructed fields")
        if ranks > 1:
            r["decomposition_seconds"] = execute(case, "log.decomposePar",
                ["decomposePar", "-allRegions", "-case", str(case)])
        phase = "solver"
        r["status"] = "MPI_RUNNING"
        dump(case / adaptive.REPORT, r)
        with (case / adaptive.TIMELINE).open("x", buffering=1) as timeline:
            w = csv.writer(timeline)
            w.writerow(("step", "time_s", "deltaT_from_time_s", "solver_deltaT_reported_s",
                        "maxCourant_reported", "wall_since_launch_s"))
            started = time.monotonic()
            def parse(line):
                nonlocal last, dt_log, co_log, ended, fatal, last_progress, previous_wall
                ended |= line.strip() == "End"
                fatal |= "FOAM FATAL" in line
                m = re.search(r"deltaT\s*=\s*(" + adaptive.NUM + ")", line)
                if m:
                    dt_log = float(m[1])
                m = re.search(r"Courant Number.*?max:\s*(" + adaptive.NUM + ")", line)
                if m:
                    co_log = float(m[1])
                    cos.append(co_log)
                m = re.match(r"^\s*Time\s*=\s*(" + adaptive.NUM + r")\s*s?\s*$", line)
                if not m:
                    if not steps and any(x in line for x in ("dynamicCode", "wmake", "Ctoo:", "Selecting", "Creating", "nProcs")):
                        print(line.rstrip(), flush=True)
                    return
                t = float(m[1])
                dt = t - last
                need(math.isfinite(dt) and dt > 0 and t <= end + 1e-7, "invalid time step")
                steps.append(t)
                dts.append(dt)
                elapsed = time.monotonic() - started
                w.writerow((len(steps), t, dt, dt_log, co_log, elapsed))
                if len(steps) == 1 or t - last_progress >= .099999 or t >= end - 1e-7:
                    print(f"{case.name}: {t:.9g}/{end}s steps={len(steps)} dt={dt:.6g} Co={co_log} wall={elapsed:.1f}s",
                          flush=True)
                    last_progress = t
                    need(shutil.disk_usage(case).free > reserve, "disk reserve reached")
                last = t
                dt_log = co_log = None
            args = ["foamMultiRun", "-case", str(case)]
            if ranks > 1:
                args = ["mpirun", "-np", str(ranks)] + args + ["-parallel"]
            r["solver_wall_seconds"] = execute(case, "log.foamMultiRun", args, parse)
        need(ended and not fatal and steps and abs(last - end) < 1e-7, "incomplete solver")
        r.update(solver_completed=True, final_time_s=last, solver_steps=len(steps),
                 status="MPI_SOLVER_COMPLETE_AUDIT_PENDING",
                 adaptive_statistics={"min_dt_s":min(dts), "max_dt_s":max(dts),
                    "mean_dt_s":sum(dts)/len(dts), "max_logged_Courant":max(cos) if cos else None,
                    "wall_seconds":r["solver_wall_seconds"]})
        dump(case / adaptive.REPORT, r)
        phase = "reconstruction"
        if ranks > 1:
            r["reconstruction_seconds"] = execute(case, "log.reconstructPar",
                ["reconstructPar", "-allRegions", "-case", str(case)])
        phase = "audit"
        adaptive.early_gate(case, r)
        execute(case, "log.foamLog", ["foamLog", "log.foamMultiRun"])
        if end == 200:
            r["runtime_audit"] = adaptive.audit(case, r, steps)
            need(r["runtime_audit"]["native_runtime_coverage_complete"], "full output audit failed")
            r["status"] = "SOLVER_COMPLETE_ADAPTIVE_AUDITED"
        else:
            pp = case / "postProcessing/metal"
            for name in ("T", "U", "p_rgh", "rho", "phaseChangeSource:alpha1"):
                adaptive.times_table(pp / "temperatureProbe/0" / name, [0.] + steps, 5.1e-4)
            for t in range(1, end + 1):
                for region, fields in (("metal", ("T", "U", "p_rgh", "phaseChangeSource:alpha1") + adaptive.DERIVED),
                                       ("mold", ("T",))):
                    for field in fields:
                        need((case / str(t) / region / field).is_file(), f"missing {t}/{region}/{field}")
            target = [i / 10 for i in range(end * 10 + 1)]
            for group, names in adaptive.profile_groups(r).items():
                dirs = adaptive.directories(pp / group)
                need(len(dirs) == len(target), "pilot profile count " + group)
                for (t, folder), expected in zip(dirs, target):
                    need(abs(t-expected) < 5e-7, "pilot profile cadence " + group)
                    for name in names:
                        adaptive.profile(folder / (name + ".xy"),
                            adaptive.NEAR if group == "nearTopInternalLine" else adaptive.CANON)
            r["status"] = "MPI_PILOT_PASS"
            r["pilot_audit"] = "probes, profiles, early topFlow and reconstructed fields"
        print(r["status"], case, "solver wall seconds:", r["solver_wall_seconds"], flush=True)
    except BaseException as e:
        r["status"] = "MPI_ATTEMPT_PRESERVED"
        r["failed_phase"] = phase
        r["error"] = str(e) or type(e).__name__
        r["last_reported_time_s"] = last
        raise
    finally:
        dump(case / adaptive.REPORT, r)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", choices=CASES, default=CASES[0])
    ap.add_argument("--ranks", type=int, choices=(1, 8, 10), default=8)
    ap.add_argument("--no-max-co", action="store_true", help="experimental: omit explicit maxCo from new attempts")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--repo", type=Path, default=adaptive.HOME / "MasterProject")
    a = ap.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION") == "14", "load Foundation14")
    need(a.ranks <= len(os.sched_getaffinity(0)), "not enough available logical CPUs")
    need(not a.publish or a.full, "pilots cannot be published as 200s results")
    need(not ROOT.is_symlink() and not adaptive.ROOT.is_symlink(), "unsafe root")
    ROOT.mkdir(exist_ok=True)
    adaptive.ROOT.mkdir(exist_ok=True)
    url = transfer.root_url(a.repo)
    with (adaptive.ROOT / ".execution.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Serial campaign still active. Stop it in its own terminal before benchmarking.")
        end = 200 if a.full else 3
        if a.full:
            reports = ROOT.glob("*/" + a.case + "/" + adaptive.REPORT)
            need(any((r := read(p)).get("status") == "MPI_PILOT_PASS" and
                     r.get("mpi_ranks") == a.ranks and
                     r.get("max_co") == (None if a.no_max_co else .25) for p in reports), "pass same-case/ranks pilot first")
        parent = Path(tempfile.mkdtemp(prefix=f"r{a.ranks}-{end}s-{'noCo' if a.no_max_co else 'Co025'}-", dir=ROOT))
        case = parent / a.case
        case.mkdir()
        print("NEW_ATTEMPT", case, flush=True)
        r = prepare(case, url, a.ranks, end, a.no_max_co)
        run(case, r, a.ranks, end)
        if a.publish:
            adaptive.ROOT = parent
            adaptive.RESULT_PREFIX = (f"results/campaign-200s-adaptive-mpi-r{a.ranks}-"
                                      + ("noCo-v1/" if a.no_max_co else "v1/"))
            adaptive.publish(case, url)

if __name__ == "__main__":
    main()
