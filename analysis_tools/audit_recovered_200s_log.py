#!/usr/bin/env python3
"""Stream verified 200 s native logs without running OpenFOAM.

Continuity and linear solver residuals are diagnostics, not conservation
certificates. Record every occurrence, without assuming a fixed PIMPLE count.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
TIME = re.compile(r"^\s*Time\s*=\s*("+NUM+r")\s*s?\s*$")
CONT = re.compile(r"time step continuity errors\s*:\s*sum local\s*=\s*("+NUM+r"),\s*global\s*=\s*("+NUM+r"),\s*cumulative\s*=\s*("+NUM+r")",re.I)
SOLVE = re.compile(r"Solving for\s+([^,]+),\s*Initial residual\s*=\s*("+NUM+r"),\s*Final residual\s*=\s*("+NUM+r"),\s*No Iterations\s+(\d+)",re.I)
CO = re.compile(r"Courant Number\s+mean\s*:\s*("+NUM+r")\s+max\s*:\s*("+NUM+r")",re.I)
REGION = re.compile(r"^\s*Solving for\s+(?:fluid|solid)\s+region\s+(\S+)\s*$",re.I)
REGION_OTHER = re.compile(r"^\s*Solving for\s+region\s+(\S+)\s*$",re.I)
END = re.compile(r"^\s*End\s*$")
FATAL = re.compile(r"FOAM FATAL|Floating point exception|MPI_ABORT|Segmentation fault",re.I)
EXEC = re.compile(r"^\s*ExecutionTime\s*=")
EXEC_VALUES = re.compile(r"^\s*ExecutionTime\s*=\s*("+NUM+r")\s*s\s+ClockTime\s*=\s*("+NUM+r")\s*s\s*$")
RANK = re.compile(r"^\s*nProcs\s*:\s*(\d+)\s*$")

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def finite(*values):
    return all(math.isfinite(x) for x in values)

def parse_log(stream, writers, *, fixed_dt=None, max_dt=None):
    """Retain native line ordering, including multiple events per physical step."""
    time=None
    step=0
    region=""
    end_count=0
    last_end_line=0
    last_time_line=0
    last_execution_line=0
    completed=0
    current_exec=0
    malformed=0
    fatal_count=0
    unassigned=0
    pre_time_co=0
    cont_count=0
    pressure_count=0
    co_count=0
    cont_steps=0
    pressure_steps=0
    has_cont=False
    has_pressure=False
    max_local=None
    max_global_abs=None
    last_cumulative=None
    max_pressure_final=None
    max_co=None
    previous=0.
    dt=None
    min_dt=max_step_dt=None
    cadence_errors=0
    timing_errors=0
    after_end_events=0
    after_execution_events=0
    observed_ranks=set()
    execution=clock=None
    last_execution=last_clock=None
    step_line=0
    def finish_step():
        if "steps" in writers:
            writers["steps"].writerow([step,step_line,time,dt,execution,clock,
                                      current_exec,int(has_cont),int(has_pressure)])
    for line_no,line in enumerate(stream,1):
        rank=RANK.match(line)
        if rank:observed_ranks.add(int(rank[1]))
        diagnostic=bool(TIME.match(line) or EXEC.match(line) or
                        "time step continuity errors" in line.lower() or
                        ("Solving for" in line and "residual" in line) or
                        "Courant Number" in line)
        if end_count and diagnostic:after_end_events+=1
        if current_exec and not TIME.match(line) and (
                "time step continuity errors" in line.lower() or
                ("Solving for" in line and "residual" in line)):
            after_execution_events+=1
        if FATAL.search(line):
            fatal_count+=1
        match=TIME.match(line)
        if match:
            new=float(match[1])
            need(math.isfinite(new) and new>=0 and (time is None or new>time),
                 "non-increasing or invalid native Time at line "+str(line_no))
            if time is not None:
                finish_step()
                completed+=int(current_exec==1)
                cont_steps+=int(has_cont)
                pressure_steps+=int(has_pressure)
            previous=time if time is not None else 0.
            time=new
            dt=time-previous
            min_dt=dt if min_dt is None else min(min_dt,dt)
            max_step_dt=dt if max_step_dt is None else max(max_step_dt,dt)
            last_time_line=line_no
            step_line=line_no
            step+=1
            if dt<=0 or (fixed_dt is not None and abs(time-step*fixed_dt)>1e-7) or (
                    max_dt is not None and dt>max_dt+1e-7):
                cadence_errors+=1
            execution=clock=None
            region=""
            current_exec=0
            has_cont=False
            has_pressure=False
            continue
        marker=REGION.match(line) or REGION_OTHER.match(line)
        if marker:
            region=marker[1]
            continue
        if END.match(line):
            end_count+=1
            last_end_line=line_no
        if EXEC.match(line):
            match=EXEC_VALUES.match(line)
            if time is None or not match:
                timing_errors+=1
            else:
                current_exec+=1
                last_execution_line=line_no
                execution,clock=map(float,match.groups())
                if not finite(execution,clock) or min(execution,clock)<0 or (
                        last_execution is not None and execution<last_execution) or (
                        last_clock is not None and clock<last_clock):
                    timing_errors+=1
                else:
                    last_execution,last_clock=execution,clock
        if "time step continuity errors" in line.lower():
            match=CONT.search(line)
            if not match:
                malformed+=1
                continue
            local,global_,cumulative=map(float,match.groups())
            if not finite(local,global_,cumulative) or local<0:
                malformed+=1
                continue
            if time is None:
                unassigned+=1
                continue
            cont_count+=1
            has_cont=True
            max_local=local if max_local is None else max(max_local,local)
            max_global_abs=abs(global_) if max_global_abs is None else max(max_global_abs,abs(global_))
            last_cumulative=cumulative
            writers["continuity"].writerow([line_no,step,time,region,local,global_,cumulative])
        elif "Solving for" in line and "residual" in line:
            match=SOLVE.search(line)
            if not match:
                malformed+=1
                continue
            field=match[1].strip()
            initial,final=float(match[2]),float(match[3])
            if not finite(initial,final) or min(initial,final)<0:
                malformed+=1
                continue
            if time is None:
                unassigned+=1
                continue
            writers["linear_solves"].writerow([line_no,step,time,region,field,initial,final,int(match[4])])
            if field=="p_rgh":
                pressure_count+=1
                has_pressure=True
                max_pressure_final=final if max_pressure_final is None else max(max_pressure_final,final)
        elif "Courant Number" in line:
            match=CO.search(line)
            if not match:
                malformed+=1
                continue
            mean,maximum=map(float,match.groups())
            if not finite(mean,maximum) or min(mean,maximum)<0:
                malformed+=1
                continue
            co_count+=1
            max_co=maximum if max_co is None else max(max_co,maximum)
            pre_time_co+=int(time is None)
            # Co can be printed BEFORE the next Time marker; do not claim
            # the previous marker is the physical time of the Co calculation.
            writers["courant"].writerow([line_no,step if time is not None else "",time if time is not None else "",region,mean,maximum])
    if time is not None:
        finish_step()
        completed+=int(current_exec==1)
        cont_steps+=int(has_cont)
        pressure_steps+=int(has_pressure)
    return {"time_markers":step,"last_time_s":time,"steps_with_exactly_one_execution_time":completed,
            "end_markers":end_count,"last_end_line":last_end_line,"fatal_markers":fatal_count,
            "last_time_line":last_time_line,"last_execution_line":last_execution_line,
            "malformed_diagnostic_lines":malformed,"unassigned_continuity_or_solve_lines":unassigned,
            "continuity_events":cont_count,"steps_with_continuity":cont_steps,
            "pressure_events":pressure_count,"steps_with_p_rgh_solve":pressure_steps,
            "max_continuity_sum_local":max_local,"max_abs_continuity_global":max_global_abs,
            "last_cumulative_continuity_as_printed":last_cumulative,
            "max_p_rgh_final_residual":max_pressure_final,"courant_events":co_count,
            "courant_before_first_time":pre_time_co,"max_logged_courant":max_co,
            "min_dt_s_from_markers":min_dt,"max_dt_s_from_markers":max_step_dt,
            "cadence_errors":cadence_errors,"timing_errors":timing_errors,
            "diagnostics_after_end":after_end_events,"solves_or_continuity_after_execution":after_execution_events,
            "observed_native_ranks":sorted(observed_ranks),
            "last_execution_time_s":last_execution,"last_clock_time_s":last_clock}

def no_links(path):
    need(not any(p.is_symlink() for p in (path,*path.parents)),"linked audit path")
    return path

def audit(root,out,index):
    root=no_links(root.expanduser().absolute()).resolve(strict=True)
    raw=no_links(out.expanduser().absolute())
    out=raw.resolve()
    need(not out.exists() and out!=root and
         root not in out.parents and out not in root.parents,
         "choose a new output outside the recovered archive")
    receipt_path=no_links(root/"VERIFIED_RECOVERY.json")
    receipt_hash=sha(receipt_path)
    receipt=json.loads(receipt_path.read_text())
    need(receipt.get("archive_parts_sha256_verified") is True and
         receipt.get("report_and_log_sha256_verified") is True,
         "missing successful recovery receipt")
    m=receipt["manifest"]
    match=[e for e in index["branches"] if e.get("sha")==receipt["source_commit"]
           and e.get("complete") is True and e.get("manifest_blob_sha")==receipt["manifest_blob"]]
    need(len(match)==1,"recovery not pinned in current index")
    e=match[0]
    need(all(m.get(k)==e.get(k) for k in
             ("case","kind","solver_steps","final_time_s","archive_sha256","report_sha256","time_mode")),
         "recovery manifest metadata mismatch")
    need(all(m.get(k)==e[k] for k in ("mpi_ranks","max_dt_s","deltaT_s","solver_log_sha256",
                                    "execution_mode","physical_validation","archive_bytes") if k in e),
         "recovery execution metadata mismatch")
    need(m.get("complete") is True and m.get("native_runtime_coverage_complete") is True
         and m.get("volume_fields_included") is False and m.get("physical_validation",False) is False
         and type(m.get("solver_steps")) is int and m["solver_steps"]>0 and m.get("final_time_s")==200,
         "unexpected recovery manifest scope")
    need(m["time_mode"] in ("fixed","adaptive_capped","adaptive_uncapped"),"unknown time mode")
    fixed_dt=m.get("deltaT_s") if m["time_mode"]=="fixed" else None
    max_dt=m.get("max_dt_s") if m["time_mode"]=="adaptive_capped" else None
    if m["time_mode"]=="fixed":need(isinstance(fixed_dt,(int,float)) and finite(fixed_dt) and fixed_dt>0,"invalid fixed dt")
    if m["time_mode"]=="adaptive_capped":need(isinstance(max_dt,(int,float)) and finite(max_dt) and max_dt>0,"invalid cap")
    need(m["case"] in {"B14-2D-200s","C14-2D-200s","C14-3DA-200s","C14-3DB-200s"},
         "unexpected case")
    case=root/m["case"]
    log=no_links(case/"log.foamMultiRun")
    report=no_links(case/"CAMPAIGN_200S_REPORT.json")
    need(log.resolve().is_relative_to(root) and report.resolve().is_relative_to(root)
         and sha(log)==m["solver_log_sha256"] and sha(report)==m["report_sha256"],
         "native log or report provenance mismatch")
    r=json.loads(report.read_text())
    need(r.get("case")==m["case"] and r.get("solver_completed") is True and
         r.get("solver_steps")==m["solver_steps"] and r.get("final_time_s")==200 and
         r.get("physical_validation",False) is False and
         r["runtime_audit"]["native_runtime_coverage_complete"] is True and not r["runtime_audit"]["errors"],
         "recovered report identity or coverage mismatch")
    need(out.parent.is_dir(),"output parent must exist")
    with tempfile.TemporaryDirectory(prefix=".native_log_audit_",dir=out.parent) as tmp:
        staged=Path(tmp)/"report"
        staged.mkdir()
        headers={
            "steps":["step","time_marker_line","time_s","delta_t_from_markers_s","execution_time_s","clock_time_s","execution_marker_count","has_continuity","has_p_rgh_solve"],
            "continuity":["line","step","time_s","last_explicit_region_marker","sum_local","global","cumulative"],
            "linear_solves":["line","step","time_s","last_explicit_region_marker","field","initial_residual","final_residual","iterations"],
            "courant":["line","previous_time_marker_step","previous_time_marker_s","last_explicit_region_marker","mean","max"]}
        from contextlib import ExitStack
        with ExitStack() as stack:
            writers={}
            for name,header in headers.items():
                f=stack.enter_context((staged/(name+".csv")).open("x",newline=""))
                writers[name]=csv.writer(f)
                writers[name].writerow(header)
            with log.open(encoding="utf-8",errors="strict") as stream:
                summary=parse_log(stream,writers,fixed_dt=fixed_dt,max_dt=max_dt)
        expected=m["solver_steps"]
        gates={"step_count_matches":summary["time_markers"]==expected,
               "execution_markers_match":summary["steps_with_exactly_one_execution_time"]==expected,
               "final_time_matches":summary["last_time_s"]==m["final_time_s"],
               "one_end_no_fatal":summary["end_markers"]==1 and summary["fatal_markers"]==0 and
                   summary["last_end_line"]>summary["last_execution_line"]>summary["last_time_line"],
               "no_malformed_diagnostics":summary["malformed_diagnostic_lines"]==0 and
                   summary["unassigned_continuity_or_solve_lines"]==0,
               "native_time_cadence":summary["cadence_errors"]==0,
               "native_timing_values":summary["timing_errors"]==0,
               "no_diagnostics_after_end":summary["diagnostics_after_end"]==0,
               "no_solves_after_execution":summary["solves_or_continuity_after_execution"]==0,
               "native_rank_matches_if_declared":m.get("mpi_ranks") is None or summary["observed_native_ranks"]==[m["mpi_ranks"]],
               "courant_observed":summary["courant_events"]>0,
               "continuity_each_step":summary["steps_with_continuity"]==expected,
               "pressure_each_step":summary["steps_with_p_rgh_solve"]==expected}
        need(sha(log)==m["solver_log_sha256"] and sha(report)==m["report_sha256"] and
             sha(receipt_path)==receipt_hash,"source changed during audit")
        result={"source_commit":e["sha"],"case":m["case"],"source_log_sha256":m["solver_log_sha256"],
                "source_report_sha256":m["report_sha256"],"source_receipt_sha256":receipt_hash,
                "time_mode":m["time_mode"],"declared_mpi_ranks":m.get("mpi_ranks"),
                "expected_steps":expected,"diagnostics":summary,"gates":gates,
                "status":"LOG_DIAGNOSTICS_COVERAGE_OK" if all(gates.values()) else "LOG_DIAGNOSTICS_REVIEW_REQUIRED",
                "mass_conservation_verified":False,"energy_conservation_verified":False,
                "physical_validation":False,"solver_rerun":False,
                "notes":"Native cumulative continuity as printed, not integrated mass. Region label is last explicit marker only. Co rows use previous Time marker, not necessarily physical time. No fixed iteration count assumed.",
                "output_sha256":{p.name:sha(p) for p in staged.iterdir()}}
        (staged/"REPORT.json").write_text(json.dumps(result,indent=2)+"\n")
        no_links(out)
        need(not out.exists(),"destination appeared during audit")
        staged.rename(out)
    print(result["status"],out)
    return all(gates.values())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--recovered",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--index",type=Path,default=Path(__file__).resolve().parents[1]/"docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json")
    a=p.parse_args()
    if not audit(a.recovered,a.out,json.loads(a.index.read_text())):
        raise SystemExit(2)

if __name__=="__main__":
    main()
