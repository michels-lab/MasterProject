#!/usr/bin/env python3
"""Lab fixed-step eight-rank queue. Preserve serial evidence; no rerun of completed CFD."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import compact_campaign_200s as compact
import transfer_campaign_200s as transfer

HOME=transfer.HOME
SRC=transfer.COMPACT
DST=HOME/"CAMPAIGN_200S_FIXED_MPI_08"
NAMES=("C14-2D-200s","B14-2D-200s","C14-3DB-200s")
REPORT=transfer.REPORT
MPI_CMD=None
MPI_CANDIDATES=(
    ["mpirun","--host","localhost:8","--map-by","slot","--bind-to","none","-np","8"],
    ["mpirun","--host","localhost:8","--map-by","slot:OVERSUBSCRIBE","--bind-to","none","-np","8"],
    ["mpirun","--map-by","hwthread:HWTCPUS","--bind-to","hwthread","-np","8"],
)
TIME=re.compile(r"^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$")
RANK=re.compile(r"^\s*nProcs\s*:\s*(\d+)")
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def read(p): return json.loads(p.read_text())
def save(p,v):
    compact.json_out(p,v)
def procs():
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            try:
                args=(p/"cmdline").read_bytes().decode(errors="replace").rstrip("\0").split("\0")
                if args and args[0]: yield int(p.name),args
            except OSError: pass
def old_processes():
    parents=[]; workers=[]; solvers=[]
    for pid,args in procs():
        if str(HOME/"transfer_campaign_200s.py") in args and "run-lab" in args:
            parents.append(pid)
        if str(HOME/"compact_campaign_200s.py") in args and "--run" in args:
            workers.append(pid)
        if Path(args[0]).name=="foamMultiRun" and any(str(SRC/n) in args for n in transfer.RUN_ORDER):
            solvers.append(pid)
    return parents,workers,solvers
def last_time(p):
    last=0.
    if p.is_file():
        with p.open(errors="replace") as f:
            for line in f:
                m=TIME.match(line)
                if m: last=float(m[1])
    return last
def checkpoint(src):
    last=last_time(src/"log.foamMultiRun")
    fields={"metal":("T","U","p","p_rgh","phaseChangeSource:alpha1")+compact.DERIVED,"mold":("T",)}
    good=[]
    for p in src.iterdir():
        if not p.is_dir() or not p.name.isdigit(): continue
        t=int(p.name)
        if t<=0 or t>=last: continue
        if all((p/r/f).is_file() and (p/r/f).stat().st_size>0 for r,fs in fields.items() for f in fs):
            good.append(t)
    return max(good,default=0)
def terminate_old(allow_takeover=False):
    # Parent first: prevents old serial manager launching a subsequent case.
    parents,workers,solvers=old_processes()
    need(allow_takeover or not (parents or workers or solvers),
         "active serial campaign; explicit --allow-takeover required")
    for pid in parents:
        try: os.kill(pid,signal.SIGTERM); os.kill(pid,signal.SIGCONT)
        except ProcessLookupError: pass
    for _ in range(20):
        if not old_processes()[0]: break
        time.sleep(.5)
    need(not old_processes()[0],"old serial queue still running; no MPI launch")
    for pid in old_processes()[2]:
        try: os.kill(pid,signal.SIGTERM); os.kill(pid,signal.SIGCONT)
        except ProcessLookupError: pass
    for _ in range(60):
        if not any(old_processes()): return
        time.sleep(.5)
    need(not any(old_processes()),"old serial solver/wrapper still active; preserve and inspect")
def native(case,name,args,progress=False,start=0):
    last=start; count=0; ranks=None; end=fatal=False
    start_wall=time.monotonic()
    print("START",case.name,name,flush=True)
    with transfer.checked_relative(case,name).open("x",buffering=1) as log:
        p=subprocess.Popen(args,cwd=case,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace",start_new_session=True)
        try:
            for line in p.stdout:
                log.write(line)
                end |= line.strip()=="End"
                fatal |= "FOAM FATAL" in line
                if not progress: continue
                m=RANK.match(line)
                if m:
                    ranks=int(m[1]); need(ranks==8,"native rank count differs")
                m=TIME.match(line)
                if m:
                    count+=1
                    t=float(m[1])
                    need(abs(t-(start+count/1000))<1e-7,"fixed step cadence drift")
                    if count==1 or int(t)>int(last):
                        print(f"{case.name}: {t:g}/200 s | MPI 8 | wall {time.monotonic()-start_wall:.1f}s",flush=True)
                        need(shutil.disk_usage(case).free>transfer.RESERVE,"disk reserve reached")
                    last=t
            rc=p.wait()
        except BaseException:
            if p.poll() is None:
                os.killpg(p.pid,signal.SIGTERM)
                try: p.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL);p.wait()
            raise
    if rc!=0 or fatal or not end:
        from collections import deque
        with (case/name).open(errors="replace") as f:
            tail="".join(deque(f,maxlen=35))
        print("NATIVE_FAILURE",case,name,"exit",rc,"\n"+tail,flush=True)
        raise RuntimeError("native command incomplete "+name+" exit="+str(rc))
    if progress:
        need(ranks==8 and count==(200-start)*1000 and abs(last-200)<1e-7,"MPI completion not proven")
    return time.monotonic()-start_wall
def prepare(name):
    need(name in NAMES,"case not authorized for MPI queue")
    src=transfer.checked_relative(SRC,name);case=transfer.checked_relative(DST,name)
    r=read(transfer.checked_relative(src,REPORT))
    if r.get("solver_completed") and r.get("final_time_s")==200:
        return None
    need(not case.exists(),"existing MPI attempt preserved: "+str(case))
    start=checkpoint(src)
    if name=="C14-2D-200s":
        need(start>=25,"no complete C14-2D checkpoint at or beyond 25s")
    elif start==0:
        need(r["status"]=="PREPARED_COMPACT_NOT_RUN","unrun input status not confirmed")
        need(transfer.input_hashes(src)==r["input_sha256"],"input hash drift")
    need(shutil.disk_usage(DST).free>transfer.RESERVE+2*r["disk_projection"]["projected_bytes_with_50pct_margin"],"insufficient disk budget")
    for rel,h in r["input_sha256"].items():
        if rel.startswith(("system/","constant/")):
            need((src/rel).is_file() and transfer.sha(src/rel)==h,"source input drift "+rel)
    case.mkdir()
    for d in ("0","constant","system"):
        shutil.copytree(src/d,case/d)
    if start: shutil.copytree(src/str(start),case/str(start))
    p=case/"system/controlDict"
    # Change only restart controls; preserve fixed dt, all diagnostics and tolerances.
    s=p.read_text()
    for key,value in {"startFrom":"startTime","startTime":str(start)}.items():
        s,n=re.subn(r"(?m)^("+key+r"\s+)[^;]+;",lambda m:m[1]+value+";",s)
        need(n==1,"missing/ambiguous "+key)
    for key,value in {"endTime":"200","deltaT":"0.001","adjustTimeStep":"no","writeInterval":"1000"}.items():
        need(re.search(r"(?m)^"+key+r"\s+"+re.escape(value)+r"\s*;",s),"control drift "+key)
    p.write_text(s)
    p=case/"system/decomposeParDict"
    need(not p.exists(),"unexpected decomposition dictionary")
    p.write_text("FoamFile\n{\n version 2.0;\n format ascii;\n class dictionary;\n object decomposeParDict;\n}\nnumberOfSubdomains 8;\nmethod scotch;\n")
    (case/(name+".foam")).touch()
    meta={"source":str(src),"restart_time_s":start,"end_time_s":200,"deltaT":.001,"mpi_ranks":8,"status":"PREPARED"}
    save(case/"MPI_RUN_METADATA.json",meta)
    args=["decomposePar","-allRegions","-case",str(case)]
    if start: args+=["-time",str(start)]
    native(case,"log.decomposePar",args)
    need(all((case/f"processor{i}"/str(start)).is_dir() for i in range(8)),"processor start states missing")
    return case,meta
def execute(prepared):
    case,meta=prepared
    path=case/"MPI_RUN_METADATA.json"
    start=meta["restart_time_s"]
    try:
        meta["status"]="RUNNING";save(path,meta)
        meta["solver_wall_seconds"]=native(case,"log.foamMultiRun",
            MPI_CMD+["foamMultiRun","-case",str(case),"-parallel"],True,start)
        meta["status"]="MPI_SOLVER_COMPLETE_RECONSTRUCT_PENDING";save(path,meta)
        meta["reconstruction_seconds"]=native(case,"log.reconstructPar",
            ["reconstructPar","-allRegions","-time",f"{start+1}:200","-case",str(case)])
        need(all((case/str(t)/r/"T").is_file() for t in range(start+1,201) for r in ("metal","mold")),"reconstructed volume time missing")
        # Earlier serial states remain in the original folder; finalizer reads them there.
        meta["status"]="MPI_COMPLETE_RECONSTRUCTED";save(path,meta)
        return meta
    except BaseException as exc:
        meta["error"]=str(exc) or type(exc).__name__
        save(path,meta)
        raise
def mpi_preflight():
    global MPI_CMD
    for cmd in MPI_CANDIDATES:
        print("MPI_PREFLIGHT",cmd,flush=True)
        try:
            p=subprocess.run(cmd+["sh","-c",'printf "%s\\n" "$OMPI_COMM_WORLD_RANK"'],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
        except subprocess.TimeoutExpired:
            print("MPI_PREFLIGHT_TIMEOUT",cmd,flush=True)
            continue
        print(p.stdout,p.stderr,flush=True)
        if p.returncode==0 and sorted(p.stdout.split())==list("01234567"):
            MPI_CMD=cmd
            print("MPI_PREFLIGHT_PASS",MPI_CMD,flush=True)
            return
    print("MPI_DIAGNOSTIC_SINGLE_RANK",flush=True)
    try:
        subprocess.run(["mpirun","--host","localhost:1","--bind-to","none","-np","1","hostname"],timeout=20)
    except subprocess.TimeoutExpired:
        print("MPI_SINGLE_RANK_TIMEOUT",flush=True)
    raise RuntimeError("eight distinct MPI ranks not proven by any mapping; no case mutation")


def archive_failed_starts():
    existing=[DST/n for n in NAMES if (DST/n).exists()]
    if not existing: return
    index=DST/"QUEUE_STATUS.json"
    need(index.is_file(),"prior MPI attempt exists without queue status; no overwrite")
    summary=read(index)
    for case in existing:
        need(summary.get(case.name,{}).get("status")=="FAILED_PRESERVED",
             "prior MPI case not a documented failure; no overwrite")
        log=case/"log.foamMultiRun"
        need(log.is_file(),"missing native log; no overwrite")
        with log.open(errors="replace") as f:
            need(not any(TIME.match(line) for line in f),"prior MPI CFD time exists; recovery required")
        meta=read(case/"MPI_RUN_METADATA.json")
        need(meta["status"]=="RUNNING","prior attempt may contain completed solver; no overwrite")
    backup=Path(tempfile.mkdtemp(prefix="CAMPAIGN_200S_FIXED_MPI_08_STARTUP_FAILURE_",dir=HOME))
    for case in existing: case.rename(backup/case.name)
    index.rename(backup/index.name)
    print("FAILED_STARTS_ARCHIVED",backup,flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--allow-takeover",action="store_true",help="explicitly authorize stopping the old serial campaign")
    a=ap.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(len(os.sched_getaffinity(0))>=8,"eight CPUs unavailable")
    for cmd in ("foamMultiRun","mpirun","decomposePar","reconstructPar","foamLog"):
        need(shutil.which(cmd),"missing "+cmd)
    need((HOME/"finalize_lab_fixed_mpi8.py").is_file(),"finalizer missing")
    mpi_preflight()
    need(not DST.is_symlink(),"unsafe MPI root")
    DST.mkdir(exist_ok=True)
    audit=HOME/"CAMPAIGN_200S_FIXED_MPI_08_AUDIT"
    need(not audit.is_symlink(),"unsafe audit root")
    audit.mkdir(exist_ok=True)
    print("WAITING_FOR_PREVIOUS_FINALIZER_IF_ANY",flush=True)
    with transfer.checked_relative(audit,".finalize.lock").open("a") as finalizer_lock, transfer.checked_relative(DST,".queue.lock").open("a") as lock:
        fcntl.flock(finalizer_lock,fcntl.LOCK_EX)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(a.allow_takeover or not any(old_processes()),"active serial campaign; no takeover authorized")
        archive_failed_starts()
        r=read(SRC/"C14-3DA-200s"/REPORT)
        need(r["status"]=="SOLVER_COMPLETE_COMPACT_AUDITED" and r["final_time_s"]==200 and r["solver_completed"],"C14-3DA audit not confirmed")
        # Verify MPI decomposition on a stable checkpoint before stopping serial.
        first=prepare(NAMES[0])
        terminate_old(a.allow_takeover)
        summary={"C14-3DA-200s":{"status":"SERIAL_COMPLETE_PRESERVED"}}
        for name in NAMES:
            try:
                print("NEXT_CASE",name,flush=True)
                p=first if name==NAMES[0] else prepare(name)
                summary[name]=execute(p) if p else {"status":"SERIAL_COMPLETE_PRESERVED"}
            except Exception as exc:
                summary[name]={"status":"FAILED_PRESERVED","error":str(exc)}
            save(DST/"QUEUE_STATUS.json",summary)
            print(name,summary[name],flush=True)
    print("QUEUE_FINISHED_STARTING_AUDIT_AND_PUBLICATION",flush=True)
    subprocess.run([sys.executable,"-u","-B",str(HOME/"finalize_lab_fixed_mpi8.py")],check=True)
if __name__=="__main__":
    main()
