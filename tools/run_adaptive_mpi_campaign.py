#!/usr/bin/env python3
"""Isolated MPI pilot/full adaptive run; OpenFOAM Foundation 14, no serial overwrite."""
from __future__ import annotations
import argparse
import csv
import errno
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
CASES = ("C14-3DB-200s", "C14-2D-200s", "B14-2D-200s", "C14-3DA-200s")
need = adaptive.need
read = adaptive.read
dump = adaptive.dump
EXPERIMENT = "experimental_adaptive_capped_mpi"

def experiment(max_dt):
    return EXPERIMENT if max_dt is not None else "experimental_adaptive_uncapped_mpi"

def time_mode(max_dt):
    return "adaptive_capped" if max_dt is not None else "adaptive_uncapped"

def cap_tag(max_dt):
    return "uncapped" if max_dt is None else format(max_dt, ".15g").replace(".", "p")

def result_branch(name, ranks, max_dt):
    return f"results/campaign-200s-adaptive-mpi-r{ranks}-Co025-dt{cap_tag(max_dt)}-v1/{name}"


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

def prepare(case, url, ranks, end, max_dt=.025):
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
        p = case / "system/controlDict"
        content = p.read_text()
        need(not re.search(r"(?m)^[ \t]*maxDeltaT\b", content), "unexpected maxDeltaT entry")
        content, count = re.subn(r"(?m)^([ \t]*maxCo[ \t]+0\.25[ \t]*;)[ \t]*$", lambda m: m[1] if max_dt is None else m[1] + f"\nmaxDeltaT       {max_dt:.15g};", content)
        need(count == 1, "missing explicit maxCo 0.25")
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
                 mpi_ranks=ranks, target_time_s=end, time_mode=time_mode(max_dt),
                 validation_class=experiment(max_dt), production_approved=False,
                 initial_dt_s=.001, max_co=.25, max_dt_s=max_dt,
                 max_co_policy="explicit 0.25", max_deltaT_policy=("no explicit maxDeltaT; native solver and output restrictions retained"
                    if max_dt is None else "explicit configurable cap"),
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
    first_step_wall = None
    observed_ranks = None
    benchmark = {}
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
                nonlocal last, dt_log, co_log, ended, fatal, last_progress, first_step_wall, observed_ranks
                m = re.match(r"^\s*nProcs\s*:\s*(\d+)", line)
                if m:
                    observed_ranks = int(m[1])
                    need(observed_ranks == ranks, "actual MPI process count mismatch")
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
                if r["max_dt_s"] is not None:
                    need(dt <= r["max_dt_s"] + 1e-9, "actual time step exceeds configured maxDeltaT")
                steps.append(t)
                dts.append(dt)
                elapsed = time.monotonic() - started
                w.writerow((len(steps), t, dt, dt_log, co_log, elapsed))
                if first_step_wall is None:
                    first_step_wall = elapsed
                for station in (1., 2., 2.4, 3.):
                    if last < station <= t and str(station) not in benchmark:
                        benchmark[str(station)] = {"actual_time_s":t, "steps":len(steps),
                            "wall_from_launch_s":elapsed, "wall_since_first_step_s":elapsed-first_step_wall}
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
        need(observed_ranks == ranks, "native nProcs not confirmed")
        r.update(solver_completed=True, final_time_s=last, solver_steps=len(steps),
                 status="MPI_SOLVER_COMPLETE_AUDIT_PENDING", observed_mpi_ranks=observed_ranks,
                 benchmark_stations=benchmark, first_step_wall_seconds=first_step_wall,
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
            reductions = ("metalTopPhiSum", "metalTopEnergyPower", "metalMoldEnergyPower",
                          "metalBoundaryEnergyPower", "metalSensibleEnthalpy", "metalMeanLiquidFraction",
                          "metalLatentHeatPower", "metalMeanCoolingRate", "metalMeanSolidificationRate",
                          "metalMaxCourant", "metalMaxThermalGradient", "metalMaxDensityGradient")
            for group in reductions:
                files = list((pp / group / "0").glob("*.dat"))
                need(len(files) == 1, "missing/ambiguous pilot reduction " + group)
                adaptive.times_table(files[0], target, 5e-5)
                if group == "metalMeanLiquidFraction":
                    need(all(len(row) == 2 and -1e-6 <= row[1] <= 1 + 1e-6
                             for row in adaptive.rows(files[0])), "mean liquid fraction outside bounds")
            top = [(t, p) for t, p in adaptive.directories(pp / "topFlow") if t > 0]
            need(len(top) == len(target)-1 and all(abs(t-e)<5e-7 and
                 (p / "patch(metalTop).xy").is_file() for (t,p),e in zip(top,target[1:])),
                 "pilot topFlow cadence")
            temperatures = [v for row in adaptive.rows(pp / "temperatureProbe/0/T") for v in row[1:]]
            need(temperatures and all(0 < v < 1e6 for v in temperatures),
                 "nonpositive or invalid sampled temperature")
            r["pilot_temperature_probe_range_K"] = [min(temperatures), max(temperatures)]
            r["status"] = "MPI_PILOT_PASS"
            r["pilot_audit"] = {"probes":len(steps)+1, "profile_stations":len(target),
                "volume_stations":end+1, "reduction_stations":len(target),
                "topFlow_stations":len(top), "scope":"sampled diagnostics; no physical validation"}
        print(r["status"], case, "solver wall seconds:", r["solver_wall_seconds"], flush=True)
    except BaseException as e:
        r["status"] = "MPI_ATTEMPT_PRESERVED"
        r["failed_phase"] = phase
        r["error"] = str(e) or type(e).__name__
        r["last_reported_time_s"] = last
        raise
    finally:
        dump(case / adaptive.REPORT, r)

def reports_for(name, ranks, max_dt, end):
    prefix = f"r{ranks}-{end}s-Co025-dt{cap_tag(max_dt)}-"
    for parent in sorted(ROOT.glob(prefix + "*")):
        case = parent / name
        if not case.is_dir():
            continue
        p = case / adaptive.REPORT
        if not p.exists():
            yield case, None
            continue
        r = read(p)
        need(r.get("mpi_ranks") == ranks and r.get("max_co") == .25
             and r.get("max_dt_s") == max_dt and r.get("target_time_s") == end,
             "attempt metadata mismatch: " + str(case))
        yield case, r

def pilot_pass(r, ranks, max_dt):
    return (r is not None and r.get("status") == "MPI_PILOT_PASS"
            and r.get("mpi_ranks") == ranks and r.get("max_co") == .25
            and r.get("max_dt_s") == max_dt
            and r.get("validation_class") == experiment(max_dt)
            and r.get("observed_mpi_ranks") == ranks
            and isinstance(r.get("pilot_audit"), dict))

def new_attempt(name, url, ranks, max_dt, end):
    parent = Path(tempfile.mkdtemp(prefix=f"r{ranks}-{end}s-Co025-dt{cap_tag(max_dt)}-", dir=ROOT))
    case = parent / name
    case.mkdir()
    print("NEW_ATTEMPT", case, flush=True)
    r = prepare(case, url, ranks, end, max_dt)
    run(case, r, ranks, end)
    return case

def publish_result(case, url, ranks, max_dt):
    branch = result_branch(case.name, ranks, max_dt)
    report = read(case / adaptive.REPORT)
    need(report["status"] == "SOLVER_COMPLETE_ADAPTIVE_AUDITED", "publication requires full audit")
    manifest = transfer.complete_manifest(url, branch)
    if manifest is not None:
        need(manifest["solver_log_sha256"] == transfer.sha(case / "log.foamMultiRun")
             and manifest["report_sha256"] == transfer.sha(case / adaptive.REPORT),
             "published result differs from local result")
        return branch
    with tempfile.TemporaryDirectory(prefix="mpi-publish-", dir=case.parent) as tmp:
        p = Path(tmp)
        archive = p / "result.tar.gz"
        with transfer.deterministic_tar(archive) as tar:
            for name in ("postProcessing", "logs", adaptive.REPORT, adaptive.TIMELINE,
                         "log.foamMultiRun", "log.foamLog", "log.decomposePar", "log.reconstructPar"):
                q = case / name
                if q.exists():
                    transfer.add(tar, q, case.name + "/" + name)
            for q in sorted(case.glob("log.*.recovery-*")):
                transfer.add(tar,q,case.name+"/"+q.name)
        transfer.publish(url, branch, archive, {"kind":"adaptive_scientific_results",
            "case":case.name, "time_mode":time_mode(max_dt), "mpi_ranks":ranks,
            "validation_class":experiment(max_dt), "physical_validation":False,
            "max_co":.25, "max_dt_s":max_dt, "solver_steps":report["solver_steps"],
            "final_time_s":200, "solver_log_sha256":transfer.sha(case / "log.foamMultiRun"),
            "report_sha256":transfer.sha(case / adaptive.REPORT),
            "native_runtime_coverage_complete":True, "volume_fields_included":False},
            p / "git", case=case)
    return branch

def recover_completed(case, r, ranks, max_dt):
    """Recover post-solver stages only; never launch foamMultiRun."""
    need(r.get("solver_completed") is True and r.get("final_time_s") == 200
         and r.get("observed_mpi_ranks") == ranks and r.get("max_dt_s") == max_dt,
         "no proven completed solver to recover")
    steps = []
    with (case / adaptive.TIMELINE).open() as f:
        for row in csv.DictReader(f):
            t = float(row["time_s"])
            need(int(row["step"]) == len(steps)+1 and math.isfinite(t)
                 and t > (steps[-1] if steps else 0.) and t <= 200+1e-7,
                 "invalid recovered timeline")
            if max_dt is not None:
                need(t-(steps[-1] if steps else 0.) <= max_dt+1e-9,
                     "recovered timeline exceeds cap")
            steps.append(t)
    need(len(steps) == r["solver_steps"] and steps and abs(steps[-1]-200)<1e-7,
         "incomplete recovered timeline")
    ended = fatal = False
    native_ranks = None
    last = None
    with (case / "log.foamMultiRun").open(errors="replace") as f:
        for line in f:
            ended |= line.strip() == "End"
            fatal |= "FOAM FATAL" in line
            m = re.match(r"^\s*nProcs\s*:\s*(\d+)", line)
            if m: native_ranks = int(m[1])
            m = re.match(r"^\s*Time\s*=\s*(" + adaptive.NUM + r")\s*s?\s*$", line)
            if m: last = float(m[1])
    need(ended and not fatal and native_ranks == ranks and last is not None
         and abs(last-200)<1e-7, "native log does not prove completion")
    backup = Path(tempfile.mkdtemp(prefix="postsolver-recovery-", dir=case.parent))
    print("RECOVER_POSTSOLVER", case, "evidence backup", backup, flush=True)
    required = {"metal":("T","U","p","p_rgh","phaseChangeSource:alpha1")+adaptive.DERIVED,
                "mold":("T",)}
    def has_fields(folder):
        return all((folder/reg/field).is_file() and (folder/reg/field).stat().st_size>0
                   for reg, fields in required.items() for field in fields)
    if ranks > 1:
        # Reconstruct from the last time in the interrupted native log
        # (even if some files exist), and all missing positive stations.
        # Never overwrite an existing output: move suspect folders aside.
        attempted = []
        for p in [case/"log.reconstructPar", *sorted(case.glob("log.reconstructPar.recovery-*"))]:
            if p.is_file():
                times = []
                with p.open(errors="replace") as f:
                    for line in f:
                        m = re.match(r"^\s*Time\s*=\s*(" + adaptive.NUM + r")\s*s?\s*$", line)
                        if m: times.append(float(m[1]))
                if times: attempted.append(times[-1])
        missing = [t for t in range(1,201) if not has_fields(case/str(t))]
        if missing:
            start = max(1, min([min(missing)] + [int(t) for t in attempted if 1<=t<=200]))
        else:
            start = max(1,min([200]+[int(t) for t in attempted if 1<=t<=200]))
        # Check all processor sources before moving any reconstructed output.
        for n in range(ranks):
            proc = case/f"processor{n}"
            need(proc.is_dir(), "missing processor directory "+str(proc))
            for t in range(start,201):
                need(has_fields(proc/str(t)), "missing distributed fields "+str(proc/str(t)))
        for t in range(start,201):
            folder = case/str(t)
            if folder.exists(): folder.rename(backup/str(t))
        need(shutil.disk_usage(case).free > adaptive.RESERVE,
             "insufficient free space for recovery")
        r["recovery_reconstruct_from_s"] = start
        name = "log.reconstructPar.recovery-" + backup.name
        execute(case,name,["reconstructPar","-allRegions","-time",f"{start}:200","-case",str(case)])
        # Native reconstruction normally excludes zero. If necessary, recover
        # actual zero-time outputs only when every processor retained them.
        if not has_fields(case/"0"):
            need(all(has_fields(case/f"processor{n}"/"0") for n in range(ranks)),
                 "native zero-time fields unavailable; do not fabricate them")
            shutil.copytree(case/"0",backup/"original-zero")
            execute(case,"log.reconstructZero.recovery-"+backup.name,
                    ["reconstructPar","-allRegions","-withZero","-time","0","-case",str(case)])
    # Preserve partial previous audit products; audit uses exclusive creation.
    pp = case/"postProcessing/metal"
    for p in pp.glob("CompactCanonical*"):
        if p.is_dir(): p.rename(backup/p.name)
    if (case/"logs").exists(): (case/"logs").rename(backup/"logs")
    adaptive.early_gate(case,r)
    execute(case,"log.foamLog.recovery-"+backup.name,["foamLog","log.foamMultiRun"])
    r["runtime_audit"] = adaptive.audit(case,r,steps)
    r["recovery_backup_path"] = str(backup)
    if not r["runtime_audit"]["native_runtime_coverage_complete"]:
        r["status"]="MPI_SOLVER_COMPLETE_AUDIT_PENDING"
        dump(case/adaptive.REPORT,r)
        raise RuntimeError("recovered output audit failed: "+str(r["runtime_audit"]["errors"]))
    r["status"]="SOLVER_COMPLETE_ADAPTIVE_AUDITED"
    r["recovered_postsolver"]=True
    r["physical_validation"]=False
    dump(case/adaptive.REPORT,r)
    print("RECOVERY_AUDITED",case,flush=True)

def run_queued_case(name, url, ranks, max_dt):
    branch = result_branch(name, ranks, max_dt)
    full = list(reports_for(name, ranks, max_dt, 200))
    manifest = transfer.complete_manifest(url, branch)
    if manifest is not None:
        need(manifest.get("case") == name and manifest.get("mpi_ranks") == ranks
             and manifest.get("max_co") == .25 and manifest.get("max_dt_s") == max_dt
             and manifest.get("time_mode") == time_mode(max_dt)
             and manifest.get("final_time_s") == 200
             and manifest.get("native_runtime_coverage_complete") is True,
             "published manifest does not match requested experiment")
        if full:
            need(any(r is not None and (c / "log.foamMultiRun").is_file()
                     and transfer.sha(c / "log.foamMultiRun") == manifest["solver_log_sha256"]
                     and transfer.sha(c / adaptive.REPORT) == manifest["report_sha256"]
                     for c, r in full), "published manifest differs from local attempts")
        return {"status":"PUBLISHED", "branch":branch, "reused":True}
    for case, r in full:
        if r and r.get("status") == "SOLVER_COMPLETE_ADAPTIVE_AUDITED":
            return {"status":"PUBLISHED", "branch":publish_result(case,url,ranks,max_dt),
                    "case_path":str(case), "reused":True}
    for case, r in full:
        if r and r.get("solver_completed") is True and r.get("final_time_s") == 200:
            return {"status":"POSTSOLVER_RECOVERY_DEFERRED","case_path":str(case),
                    "note":"continue other cases now; recover separately with --recover-only"}
    if full:
        return {"status":"FULL_ATTEMPT_PRESERVED", "paths":[str(c) for c,_ in full],
                "note":"incomplete or unaudited; no automatic rerun"}
    pilots = list(reports_for(name, ranks, max_dt, 3))
    if not any(pilot_pass(r,ranks,max_dt) for _,r in pilots):
        if pilots:
            return {"status":"PILOT_ATTEMPT_PRESERVED", "paths":[str(c) for c,_ in pilots],
                    "note":"pilot not approved; full run not launched"}
        new_attempt(name,url,ranks,max_dt,3)
    case = new_attempt(name,url,ranks,max_dt,200)
    return {"status":"PUBLISHED", "branch":publish_result(case,url,ranks,max_dt),
            "case_path":str(case)}

def check_queue_storage():
    # A failed case is not a reason to stop. A non-writable shared
    # workspace is: every remaining solver and the queue need it.
    with tempfile.NamedTemporaryFile(prefix=".queue-write-", dir=ROOT) as f:
        f.write(b"ok")
        f.flush()
        os.fsync(f.fileno())

def sequence(url, ranks):
    # Two waves, four cases each, no overlap. A failed pilot/full attempt
    # is recorded and preserved; other cases continue.
    index = ROOT / f"MPI_SEQUENCE_R{ranks}.json"
    summary = read(index) if index.is_file() else {}
    for max_dt in (.025, None):
        tag = cap_tag(max_dt)
        wave = summary.setdefault(tag, {})
        for name in CASES:
            print("SEQUENCE", tag, name, flush=True)
            try:
                check_queue_storage()
            except OSError as exc:
                raise RuntimeError("Shared campaign storage is not writable; repair WSL before continuing") from exc
            try:
                wave[name] = run_queued_case(name,url,ranks,max_dt)
            except (RuntimeError, ValueError, OSError, KeyError, subprocess.SubprocessError) as exc:
                wave[name] = {"status":"BLOCKED_OR_FAILED_PRESERVED", "error":str(exc)}
                print("CASE_FAILED_CONTINUE_IF_STORAGE_WRITABLE", wave[name], flush=True)
                if isinstance(exc,OSError) and exc.errno in (errno.EROFS,errno.EIO,errno.ENOSPC):
                    try:
                        check_queue_storage()
                    except OSError:
                        print("SHARED_STORAGE_UNAVAILABLE: cannot run remaining cases",flush=True)
                        raise
            # Atomic replacement only after successful handling; storage failures
            # must stop the queue instead of masking the original exception.
            dump(index, summary)
            print("CASE_STATUS", tag, name, wave[name]["status"], flush=True)
        print("WAVE_ATTEMPTS_FINISHED", tag, flush=True)
    print(summary, flush=True)
    need(all(summary[cap_tag(dt)][name]["status"] == "PUBLISHED"
             for dt in (.025,None) for name in CASES),
         "some cases did not complete or publish; inspect " + str(index))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", choices=CASES, default=CASES[0])
    ap.add_argument("--ranks", type=int, choices=(1, 8, 10), default=8)
    caps = ap.add_mutually_exclusive_group()
    caps.add_argument("--max-dt", type=float, default=.025, help="maximum time step in seconds, default 0.025")
    caps.add_argument("--no-max-dt", action="store_true", help="omit explicit maxDeltaT; retain maxCo 0.25")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--recover-only", action="store_true", help="recover and publish the named completed solver; never launch CFD")
    ap.add_argument("--sequence", action="store_true", help="wait for active campaign; run capped then uncapped four-case waves; publish automatically")
    ap.add_argument("--repo", type=Path, default=adaptive.HOME / "MasterProject")
    a = ap.parse_args()
    max_dt = None if a.no_max_dt else a.max_dt
    need(os.environ.get("WM_PROJECT_VERSION") == "14", "load Foundation14")
    need(max_dt is None or (math.isfinite(max_dt) and .001 <= max_dt <= 1.),
         "max-dt must be finite and between 0.001 and 1 s")
    need(a.ranks <= len(os.sched_getaffinity(0)), "not enough available logical CPUs")
    need(not a.publish or a.full or a.sequence, "pilots cannot be published as 200s results")
    need(not a.recover_only or (not a.sequence and not a.full), "recover-only is separate from new runs")
    need(not a.sequence or (not a.full and not a.no_max_dt and a.max_dt == .025),
         "sequence has fixed capped/uncapped waves")
    need(not ROOT.is_symlink() and not adaptive.ROOT.is_symlink(), "unsafe root")
    ROOT.mkdir(exist_ok=True)
    adaptive.ROOT.mkdir(exist_ok=True)
    url = transfer.root_url(a.repo)
    with (adaptive.ROOT / ".execution.lock").open("a") as lock:
        try:
            if a.sequence:
                print("WAITING_FOR_ACTIVE_CAMPAIGN_IF_ANY", flush=True)
                fcntl.flock(lock, fcntl.LOCK_EX)
            else:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Campaign still active. Use --sequence to wait without interrupting.")
        if a.sequence:
            sequence(url,a.ranks)
            return
        if a.recover_only:
            full = list(reports_for(a.case,a.ranks,max_dt,200))
            for case,r in full:
                if r and r.get("status") == "SOLVER_COMPLETE_ADAPTIVE_AUDITED":
                    print("PUBLISHED",publish_result(case,url,a.ranks,max_dt),flush=True)
                    return
            for case,r in full:
                if r and r.get("solver_completed") is True and r.get("final_time_s")==200:
                    recover_completed(case,r,a.ranks,max_dt)
                    print("PUBLISHED",publish_result(case,url,a.ranks,max_dt),flush=True)
                    return
            raise RuntimeError("no completed solver report found; preserve all attempts")
        end = 200 if a.full else 3
        if a.full:
            need(any(pilot_pass(r,a.ranks,max_dt)
                     for _,r in reports_for(a.case,a.ranks,max_dt,3)),
                 "pass same-case/ranks/maxDeltaT pilot first")
        case = new_attempt(a.case,url,a.ranks,max_dt,end)
        if a.publish:
            publish_result(case,url,a.ranks,max_dt)

if __name__ == "__main__":
    main()
