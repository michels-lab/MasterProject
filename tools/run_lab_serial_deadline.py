#!/usr/bin/env python3
"""Lab deadline queue: native serial CFD first, no network or MPI benchmarks.
Preserves distributed attempts and the completed C14-3DA. C14-2D is last.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

import compact_campaign_200s as compact
import transfer_campaign_200s as transfer

HOME=transfer.HOME
ROOT=transfer.COMPACT
MPI=HOME/"CAMPAIGN_200S_FIXED_MPI_08"
RESUME=HOME/"CAMPAIGN_200S_SERIAL_RESUME_01"
REPORT=transfer.REPORT
ORDER=("C14-3DB-200s","B14-2D-200s","C14-2D-200s")
TIME=re.compile(r"^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$")

def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def read(p): return json.loads(p.read_text())
def save(p,r):
    tmp=p.with_name("."+p.name+".tmp")
    tmp.write_text(json.dumps(r,indent=2)+"\n")
    tmp.replace(p)
def procs():
    for p in Path("/proc").iterdir():
        if not p.name.isdigit(): continue
        try:
            args=(p/"cmdline").read_bytes().decode(errors="replace").rstrip("\0").split("\0")
            if args and args[0]: yield int(p.name),args
        except OSError: pass
def is_manager(args,names):
    return Path(args[0]).name.startswith("python") and any(Path(a).name in names for a in args[1:])
def is_solver(args):
    return Path(args[0]).name in ("foamMultiRun","prterun","mpirun","orterun") and any(Path(a).name=="foamMultiRun" for a in args)
def mpi_case(args):
    return any(str(MPI/n) in args for n in ORDER)
def terminate(pid):
    try:
        os.kill(pid,signal.SIGTERM)
        os.kill(pid,signal.SIGCONT)
    except ProcessLookupError: pass
def stop_mpi():
    active=list(procs())
    # Do not interrupt unrelated CFD or a previously launched serial queue.
    others=[(pid,args) for pid,args in active if is_solver(args) and not mpi_case(args)]
    need(not others,"unrelated or serial CFD active; not stopping it: "+str(others))
    old=[(pid,args) for pid,args in active if is_manager(args,{"transfer_campaign_200s.py","compact_campaign_200s.py"}) and ("run-lab" in args or "--run" in args)]
    need(not old,"original serial manager still active; no duplicate queue")
    # Stop waiting recovery first, then the MPI manager, to prevent new cases.
    for name in ("recover_lab_mpi_reference.py","run_lab_fixed_mpi8.py"):
        for pid,args in procs():
            if is_manager(args,{name}):
                print("STOP_OLD_MANAGER",pid,name,flush=True)
                terminate(pid)
    for _ in range(20):
        if not any(is_manager(a,{"recover_lab_mpi_reference.py","run_lab_fixed_mpi8.py"}) for _,a in procs()): break
        time.sleep(.5)
    need(not any(is_manager(a,{"recover_lab_mpi_reference.py","run_lab_fixed_mpi8.py"}) for _,a in procs()),"MPI manager still active")
    # Stop only the known lab MPI cases; no file removal and no SIGKILL.
    for pid,args in procs():
        if is_solver(args) and mpi_case(args):
            print("STOP_OLD_MPI",pid,flush=True)
            terminate(pid)
    for _ in range(60):
        if not any(is_solver(a) for _,a in procs()): return
        time.sleep(.5)
    raise RuntimeError("CFD still active; no second solver started")

def check_fresh(name):
    case=ROOT/name
    r=read(case/REPORT)
    if r.get("solver_completed") and r.get("final_time_s")==200: return
    need(r["status"]=="PREPARED_COMPACT_NOT_RUN","original serial input not fresh: "+name)
    need(not (case/"log.foamMultiRun").exists() and not (case/"postProcessing").exists(),"serial output already exists: "+name)
    need(transfer.input_hashes(case)==r["input_sha256"],"serial input drift: "+name)

def fresh(name):
    case=ROOT/name
    r=read(case/REPORT)
    if r.get("solver_completed") and r.get("final_time_s")==200:
        return {"status":r["status"],"path":str(case)}
    check_fresh(name)
    rc=subprocess.run([sys.executable,"-u","-B",str(HOME/"compact_campaign_200s.py"),"--run",name]).returncode
    r=read(case/REPORT)
    need(rc==0 and r.get("solver_completed") and r.get("final_time_s")==200,
         "serial case incomplete; inspect "+str(case/"log.foamMultiRun"))
    return {"status":r["status"],"path":str(case)}

def checkpoint(case):
    last=0.
    with (case/"log.foamMultiRun").open(errors="replace") as f:
        for line in f:
            m=TIME.match(line)
            if m: last=float(m[1])
    required={"metal":("T","U","p","p_rgh","phaseChangeSource:alpha1")+compact.DERIVED,"mold":("T",)}
    good=[]
    for d in case.iterdir():
        if d.is_dir() and d.name.isdigit() and 0<int(d.name)<last:
            if all((d/r/f).is_file() and (d/r/f).stat().st_size>0 for r,fs in required.items() for f in fs):
                good.append(int(d.name))
    need(good,"no complete serial checkpoint")
    return max(good)

def resume():
    from finalize_lab_fixed_mpi8 import merge_diagnostics, native_log, complete_steps
    name=ORDER[-1]
    src=ROOT/name
    r=read(src/REPORT)
    if r.get("solver_completed") and r.get("final_time_s")==200:
        return {"status":r["status"],"path":str(src)}
    start=checkpoint(src)
    case=RESUME/name
    merged=RESUME/"AUDITED"/name
    need(not case.exists() and not merged.exists(),"prior serial continuation exists; no overwrite")
    need(shutil.disk_usage(HOME).free>transfer.RESERVE+2*r["disk_projection"]["projected_bytes_with_50pct_margin"],"insufficient disk budget")
    for rel,h in r["input_sha256"].items():
        if rel.startswith(("constant/","system/")):
            need(transfer.sha(src/rel)==h,"serial input drift "+rel)
    case.mkdir(parents=True)
    for d in ("0","constant","system",str(start)):
        shutil.copytree(src/d,case/d)
    p=case/"system/controlDict"
    s=p.read_text()
    for k,v in {"startFrom":"startTime","startTime":str(start)}.items():
        s,n=re.subn(r"(?m)^("+k+r"\s+)[^;]+;",lambda m:m[1]+v+";",s)
        need(n==1,"control key not unique "+k)
    p.write_text(s)
    (case/(name+".foam")).touch()
    meta={"status":"RUNNING_SERIAL_RESUME","restart_time_s":start,"mpi_ranks":1,
          "source":str(src),"deltaT":.001}
    save(case/"SERIAL_RESUME_METADATA.json",meta)
    print("SERIAL_RESTART",name,start,flush=True)
    with compact.lock(compact.SOURCE),compact.lock(compact.TARGET):
        count=0; end=fatal=False; wall=time.monotonic()
        with (case/"log.foamMultiRun").open("x",buffering=1) as f:
            p=subprocess.Popen(["foamMultiRun","-case",str(case)],cwd=case,stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,text=True,errors="replace")
            try:
                for line in p.stdout:
                    f.write(line)
                    end|=line.strip()=="End";fatal|="FOAM FATAL" in line
                    m=TIME.match(line)
                    if m:
                        count+=1; t=float(m[1])
                        need(abs(t-(start+count/1000))<1e-7,"serial resume time drift")
                        if count==1 or count%1000==0:
                            print(f"{name}: {t:g}/200 s | serial | wall {time.monotonic()-wall:.1f}s",flush=True)
                            need(shutil.disk_usage(HOME).free>transfer.RESERVE,"disk reserve reached")
                need(p.wait()==0 and end and not fatal and count==(200-start)*1000,"incomplete serial resume")
            except BaseException:
                if p.poll() is None: p.terminate();p.wait()
                raise
        meta["status"]="SOLVER_COMPLETE_AUDIT_PENDING"
        save(case/"SERIAL_RESUME_METADATA.json",meta)
        merged.mkdir(parents=True)
        for d in ("0","constant","system"):
            shutil.copytree(src/d,merged/d)
        for t in range(1,201):
            path=(src if t<=start else case)/str(t)
            need(path.is_dir(),"missing volume checkpoint "+str(path))
            (merged/str(t)).symlink_to(path,target_is_directory=True)
        (merged/(name+".foam")).touch()
        steps,_,_,_=native_log(src/"log.foamMultiRun")
        need(complete_steps([t for t in steps if t<=start+1e-7],0,start),"serial prefix time grid invalid")
        with (merged/"log.foamMultiRun").open("x") as f, (src/"log.foamMultiRun").open(errors="replace") as old:
            for line in old:
                m=TIME.match(line)
                if m and float(m[1])>start+1e-7: break
                f.write(line)
            f.write("\n# Serial restart at "+str(start)+" s\n")
            with (case/"log.foamMultiRun").open(errors="replace") as new: shutil.copyfileobj(new,f)
        need(complete_steps(native_log(merged/"log.foamMultiRun")[0],0,200),"merged time grid invalid")
        merge_diagnostics(merged,src,case,start,r)
        compact.check_native(merged,"log.foamLog",["foamLog","log.foamMultiRun"])
        r.update(status="SOLVER_COMPLETE_AUDIT_PENDING",solver_completed=True,solver_steps=200000,
                 final_time_s=200,physical_validation=False,execution_mode="serial_restart",
                 restart_time_s=start,mpi_ranks=1,diagnostic_merge_policy="original through checkpoint; resumed strictly after")
        r.pop("error",None)
        save(merged/REPORT,r)
        r["runtime_audit"]=compact.audit(merged,r)
        ok=r["runtime_audit"]["native_runtime_coverage_complete"]
        r["status"]="SOLVER_COMPLETE_COMPACT_AUDITED" if ok else "SOLVER_COMPLETE_PARTIAL_DIAGNOSTICS"
        save(merged/REPORT,r)
        meta["status"]=r["status"];save(case/"SERIAL_RESUME_METADATA.json",meta)
        return {"status":r["status"],"path":str(merged),"restart_time_s":start}

def main():
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(shutil.which("foamMultiRun") and shutil.which("foamLog"),"native tools missing")
    need((HOME/"finalize_lab_fixed_mpi8.py").is_file(),"resume audit helper missing")
    need(transfer.sha(HOME/"compact_campaign_200s.py")==read(ROOT/ORDER[0]/REPORT)["implementation_sha256"],"pinned compact script mismatch")
    with (HOME/".lab_serial_deadline.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        r=read(ROOT/"C14-3DA-200s"/REPORT)
        need(r["status"]=="SOLVER_COMPLETE_COMPACT_AUDITED" and r["final_time_s"]==200,"completed reference not confirmed")
        # Verify pristine serial alternatives BEFORE stopping the distributed run.
        for name in ORDER[:2]: check_fresh(name)
        stop_mpi()
        summary={"C14-3DA-200s":{"status":r["status"],"path":str(ROOT/"C14-3DA-200s")}}
        index=HOME/"LAB_SERIAL_DEADLINE_STATUS.json"
        save(index,summary)
        for name in ORDER:
            print("NEXT_SERIAL_CASE",name,flush=True)
            try:
                summary[name]=resume() if name==ORDER[-1] else fresh(name)
            except Exception as e:
                summary[name]={"status":"BLOCKED_PRESERVED","error":str(e)}
            save(index,summary)
            print("CASE_STATUS",name,summary[name],flush=True)
        print("SERIAL_QUEUE_FINISHED",summary,flush=True)
if __name__=="__main__": main()
