#!/usr/bin/env python3
"""Resume the interrupted eight-rank C14-3DB from a shared native checkpoint.
Preserve serial and MPI attempts, then retry only zero-step pressure-reference
failures. Never run a benchmark or wait for GitHub before CFD.
"""
import argparse
import fcntl
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import run_lab_fixed_mpi8 as q
import finalize_lab_fixed_mpi8 as f
import recover_lab_mpi_reference as recovery

NAME="C14-3DB-200s"
SERIAL=q.SRC/NAME
CASE=q.DST/NAME
REPORT=q.transfer.REPORT
RANKS=8

def need(ok,msg):
    if not ok: raise RuntimeError(msg)

def processes():
    return list(q.procs())

def manager(args,names):
    return Path(args[0]).name.startswith("python") and any(Path(a).name in names for a in args[1:])

def solver(args):
    return Path(args[0]).name in ("foamMultiRun","prterun","mpirun","orterun") and any(Path(a).name=="foamMultiRun" for a in args)

def terminate(pid):
    try: os.kill(pid,signal.SIGTERM); os.kill(pid,signal.SIGCONT)
    except ProcessLookupError: pass

def stop_serial(allow_takeover=False):
    names={"run_lab_serial_deadline.py","compact_campaign_200s.py"}
    active=processes()
    need(allow_takeover or not any(solver(a) or manager(a,names) for _,a in active),
         "active campaign; explicit --allow-takeover required")
    allowed=[str(q.SRC/n) for n in q.NAMES]
    need(not any(solver(a) and not any(p in a for p in allowed) for _,a in active),
         "unrelated solver active; no interruption")
    need(not any(manager(a,{"run_lab_fixed_mpi8.py","recover_lab_mpi_reference.py"}) for _,a in active),
         "old MPI/recovery manager active; refusing concurrent queue")
    for name in ("run_lab_serial_deadline.py","compact_campaign_200s.py"):
        for pid,a in processes():
            if manager(a,{name}) and (name!="compact_campaign_200s.py" or "--run" in a):
                print("STOP_SERIAL_MANAGER",pid,flush=True);terminate(pid)
        for _ in range(30):
            if not any(manager(a,{name}) and (name!="compact_campaign_200s.py" or "--run" in a) for _,a in processes()): break
            time.sleep(.2)
        need(not any(manager(a,{name}) and (name!="compact_campaign_200s.py" or "--run" in a) for _,a in processes()),"serial manager did not stop")
    for pid,a in processes():
        if solver(a) and any(p in a for p in allowed):
            print("STOP_SERIAL_SOLVER",pid,flush=True);terminate(pid)
    for _ in range(60):
        if not any(solver(a) for _,a in processes()):return
        time.sleep(.5)
    raise RuntimeError("solver still active; no duplicate CFD launched")

def checkpoint():
    meta=q.read(CASE/"MPI_RUN_METADATA.json")
    need(meta["mpi_ranks"]==8 and meta["restart_time_s"]==0 and meta["deltaT"]==.001,
         "unexpected original MPI attempt")
    steps,ranks,end,fatal=f.native_log(CASE/"log.foamMultiRun")
    need(ranks==8 and steps and not fatal and not end,"expected interrupted eight-rank run")
    fields={"metal":("T","U","p","p_rgh","phaseChangeSource:alpha1","latentHeat","phaseChangeSolidFraction"),
            "mold":("T",)}
    def valid(t):
        return all((CASE/f"processor{i}"/str(t)/reg/field).is_file() and
                   (CASE/f"processor{i}"/str(t)/reg/field).stat().st_size>0
                   for i in range(8) for reg,fs in fields.items() for field in fs)
    times=[t for t in range(1,min(199,int(steps[-1]))+1)
           if t<steps[-1]-1e-7 and valid(t)]
    need(times,"no shared completed checkpoint; serial remains running")
    t=max(times)
    need(f.complete_steps([x for x in steps if x<=t+1e-7],0,t),"original MPI prefix time grid invalid")
    # Require all earlier distributed states and native diagnostic roots before takeover.
    need(all(valid(i) for i in range(1,t+1)),"earlier distributed volumes missing")
    pp=CASE/"postProcessing/metal"
    need(all((pp/g).is_dir() for g in ("temperatureProbe",*q.compact.REDUCTIONS,*q.compact.profile_groups(q.read(SERIAL/REPORT)),"nearTopInternalLine","topFlow")),
         "original diagnostic groups missing")
    return t

def prepare(start):
    parent=Path(tempfile.mkdtemp(prefix="C14-3DB-MPI8-resume-stage-",dir=q.HOME))
    stage=parent/NAME
    stage.mkdir()
    for folder in ("0","constant","system"):
        shutil.copytree(CASE/folder,stage/folder)
    for i in range(8):
        old=CASE/f"processor{i}"
        new=stage/old.name;new.mkdir()
        for d in ("constant","0",*(str(t) for t in range(1,start+1))):
            need((old/d).is_dir(),"missing distributed input "+str(old/d))
            shutil.copytree(old/d,new/d)
    control=stage/"system/controlDict"
    s=control.read_text()
    for key,value in {"startFrom":"startTime","startTime":str(start)}.items():
        s,n=re.subn(r"(?m)^("+key+r"\s+)[^;]+;",lambda m:m[1]+value+";",s)
        need(n==1,"restart key not unique "+key)
    for key,value in {"endTime":"200","deltaT":"0.001","adjustTimeStep":"no","writeInterval":"1000"}.items():
        need(re.search(r"(?m)^"+key+r"\s+"+re.escape(value)+r"\s*;",s),"control drift "+key)
    control.write_text(s)
    (stage/(NAME+".foam")).touch()
    return stage

def combine(old,start):
    report=q.read(SERIAL/REPORT)
    # Build the merged native diagnostics independently; preserve both raw segments.
    with tempfile.TemporaryDirectory(prefix="merge-diagnostics-",dir=q.DST) as d:
        merged=Path(d)
        f.merge_diagnostics(merged,old,CASE,start,report)
        raw=CASE/"postProcessing.mpi-resume-raw"
        (CASE/"postProcessing").rename(raw)
        (merged/"postProcessing").rename(CASE/"postProcessing")
    oldlog=old/"log.foamMultiRun"
    newlog=CASE/"log.foamMultiRun"
    with (CASE/"log.foamMultiRun.merged").open("x") as out,oldlog.open(errors="replace") as inp:
        for line in inp:
            m=q.TIME.match(line)
            if m and float(m[1])>start+1e-7:break
            out.write(line)
        out.write("\n# Native 8-rank restart from "+str(start)+" s\n")
        with newlog.open(errors="replace") as inp:shutil.copyfileobj(inp,out)
    steps,ranks,end,fatal=f.native_log(CASE/"log.foamMultiRun.merged")
    need(ranks==8 and end and not fatal and f.complete_steps(steps,0,200),"merged log not complete")
    newlog.rename(CASE/"log.foamMultiRun.resume-raw")
    (CASE/"log.foamMultiRun.merged").rename(newlog)

def run(start,stage):
    backup=Path(tempfile.mkdtemp(prefix="C14-3DB-MPI8-original-",dir=q.HOME))/NAME
    CASE.rename(backup)
    stage.rename(CASE)
    if (backup/"log.decomposePar").is_file():
        shutil.copy2(backup/"log.decomposePar",CASE/"log.decomposePar")
    meta={"source":str(SERIAL),"restart_time_s":0,"mpi_resume_time_s":start,
          "original_mpi_attempt":str(backup),"end_time_s":200,"deltaT":.001,"mpi_ranks":8,"status":"RUNNING"}
    p=CASE/"MPI_RUN_METADATA.json"
    q.save(p,meta)
    print("MPI_RESUME",NAME,"checkpoint",start,"original preserved",backup,flush=True)
    try:
        meta["solver_wall_seconds_resume"]=q.native(CASE,"log.foamMultiRun",
             q.MPI_CMD+["foamMultiRun","-case",str(CASE),"-parallel"],True,start)
        meta["status"]="MPI_SOLVER_COMPLETE_RECONSTRUCT_PENDING";q.save(p,meta)
        meta["reconstruction_seconds"]=q.native(CASE,"log.reconstructPar",
            ["reconstructPar","-allRegions","-time","1:200","-case",str(CASE)])
        need(all((CASE/str(t)/r/"T").is_file() for t in range(1,201) for r in ("metal","mold")),"missing reconstructed volume")
        combine(backup,start)
        meta["status"]="MPI_COMPLETE_RECONSTRUCTED";q.save(p,meta)
        return meta
    except BaseException as exc:
        meta["error"]=str(exc) or type(exc).__name__;q.save(p,meta);raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--allow-takeover",action="store_true",help="explicitly authorize stopping the serial queue")
    a=ap.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(len(os.sched_getaffinity(0))>=8,"eight CPUs unavailable")
    need((q.DST/".queue.lock").is_file(),"previous MPI queue missing")
    need(q.read(q.SRC/"C14-3DA-200s"/REPORT)["status"]=="SOLVER_COMPLETE_COMPACT_AUDITED","C14-3DA audit missing")
    audit=q.HOME/"CAMPAIGN_200S_FIXED_MPI_08_AUDIT"
    need(not audit.is_symlink() and not q.DST.is_symlink(),"unsafe recovery root")
    audit.mkdir(exist_ok=True)
    with q.transfer.checked_relative(audit,".finalize.lock").open("a") as al,q.transfer.checked_relative(q.DST,".queue.lock").open("a") as lk:
        fcntl.flock(al,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(lk,fcntl.LOCK_EX|fcntl.LOCK_NB)
        q.mpi_preflight()
        start=checkpoint()
        print("VERIFIED_SHARED_MPI_CHECKPOINT",start,flush=True)
        need(shutil.disk_usage(q.HOME).free>q.transfer.RESERVE+2*q.read(SERIAL/REPORT)["disk_projection"]["projected_bytes_with_50pct_margin"],"insufficient disk budget")
        stage=prepare(start)
        # Only stop the serial queue after the MPI preflight and copied checkpoint pass.
        stop_serial(a.allow_takeover)
        index=q.DST/"QUEUE_STATUS.json"
        summary=q.read(index) if index.is_file() else {}
        try:summary[NAME]=run(start,stage)
        except Exception as exc:summary[NAME]={"status":"FAILED_PRESERVED","error":str(exc)}
        q.save(index,summary)
        print("CASE_STATUS",NAME,summary[NAME],flush=True)
        for name in ("B14-2D-200s","C14-2D-200s"):
            case=q.DST/name
            if summary.get(name,{}).get("status")!="FAILED_PRESERVED" or not recovery.ref_failure(case):
                print("UNCHANGED_NOT_ZERO_STEP_REFERENCE_FAILURE",name,flush=True);continue
            try:summary[name]=recovery.retry(name,case,summary)
            except Exception as exc:summary[name]={"status":"FAILED_PRESERVED","error":str(exc)}
            q.save(index,summary)
            print("CASE_STATUS",name,summary[name],flush=True)
    print("CFD_QUEUE_FINISHED_STARTING_FINALIZATION",flush=True)
    subprocess.run([sys.executable,"-u","-B",str(q.HOME/"finalize_lab_fixed_mpi8.py")],check=True)
if __name__=="__main__":main()
