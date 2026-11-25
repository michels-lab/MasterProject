#!/usr/bin/env python3
"""Independent zero-time, fixed-step, eight-rank lab timing campaign.
Preserve old attempts. All fresh inputs are verified against original manifests.
No network publication blocks the CFD queue.
"""
import csv
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
from collections import deque

import run_lab_fixed_mpi8 as q
import finalize_lab_fixed_mpi8 as final
import recover_lab_mpi_reference as ref

HOME=q.HOME
ORDER=("C14-3DB-200s","B14-2D-200s","C14-2D-200s")
REPORT=q.transfer.REPORT
ROOT=HOME/"CAMPAIGN_200S_FIXED_MPI8_FRESH"
MANAGERS={"run_lab_fixed_mpi8.py","run_lab_serial_deadline.py","resume_lab_mpi8_deadline.py",
          "recover_lab_mpi_reference.py","transfer_campaign_200s.py","compact_campaign_200s.py"}
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def save(p,x):q.save(p,x)
def manager(a):
    return Path(a[0]).name.startswith("python") and any(Path(x).name in MANAGERS for x in a[1:])
def solver(a):
    return Path(a[0]).name in ("foamMultiRun","mpirun","prterun","orterun") and any(Path(x).name=="foamMultiRun" for x in a)
def ours(a):
    paths=[q.SRC/n for n in ORDER]+[q.DST/n for n in ORDER]+[HOME/"CAMPAIGN_200S_SERIAL_RESUME_01"/n for n in ORDER]
    return any(str(p) in a for p in paths)
def signal_stop(pid):
    try:os.kill(pid,signal.SIGTERM);os.kill(pid,signal.SIGCONT)
    except ProcessLookupError:pass
def stop_previous():
    active=list(q.procs())
    need(not any(solver(a) and not ours(a) for _,a in active),"unrelated CFD active; refusing takeover")
    # Stop queue controllers before solver so they cannot start another case.
    for name in ("recover_lab_mpi_reference.py","resume_lab_mpi8_deadline.py","run_lab_fixed_mpi8.py",
                 "run_lab_serial_deadline.py","transfer_campaign_200s.py","compact_campaign_200s.py"):
        def matches(a):
            return manager(a) and any(Path(x).name==name for x in a[1:]) and (
                name!="transfer_campaign_200s.py" or "run-lab" in a) and (
                name!="compact_campaign_200s.py" or "--run" in a)
        for pid,a in q.procs():
            if matches(a):
                print("STOP_PREVIOUS_MANAGER",pid,name,flush=True);signal_stop(pid)
        for _ in range(40):
            if not any(matches(a) for _,a in q.procs()):break
            time.sleep(.25)
        need(not any(matches(a) for _,a in q.procs()),"previous manager did not stop")
    for pid,a in q.procs():
        if solver(a) and ours(a):
            print("STOP_PREVIOUS_SOLVER",pid,flush=True);signal_stop(pid)
    for _ in range(120):
        if not any(solver(a) for _,a in q.procs()):return
        time.sleep(.25)
    raise RuntimeError("previous CFD remains active; no duplicate launch")

def fresh_inputs(name,case):
    original=q.SRC/name
    dense=q.transfer.DENSE/name
    r=q.read(original/REPORT)
    manifest=r["input_sha256"]
    need(r["case"]==name and manifest and
         r["implementation_sha256"]==q.transfer.sha(HOME/"compact_campaign_200s.py"),"original input provenance invalid")
    case.mkdir()
    for rel,h in sorted(manifest.items()):
        rp=Path(rel)
        need(not rp.is_absolute() and ".." not in rp.parts and rp.parts[0] in ("0","constant","system"),"unsafe input path")
        p=next((root/rp for root in (original,dense) if (root/rp).is_file() and not (root/rp).is_symlink() and q.transfer.sha(root/rp)==h),None)
        need(p is not None,"original exact input unavailable: "+name+"/"+rel)
        dest=case/rp;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    need(q.transfer.input_hashes(case)==manifest,"fresh input hash mismatch")
    control=(case/"system/controlDict").read_text()
    for key,value in {"startFrom":"startTime","startTime":"0","endTime":"200","deltaT":"0.001","adjustTimeStep":"no","writeInterval":"1000"}.items():
        need(re.search(r"(?m)^"+key+r"\s+"+re.escape(value)+r"\s*;",control),"control drift "+key)
    (case/"system/decomposeParDict").write_text("FoamFile\n{\n version 2.0;\n format ascii;\n class dictionary;\n object decomposeParDict;\n}\nnumberOfSubdomains 8;\nmethod scotch;\n")
    (case/(name+".foam")).touch()
    r.update(status="FRESH_MPI_PREPARED",solver_completed=False,physical_validation=False,
             source_original_input_sha256=manifest,mpi_ranks=8,restart_time_s=0,execution_mode="mpi",
             time_mode="fixed",deltaT_s=.001,experiment="fresh_from_zero_timing",
             input_sha256=q.transfer.input_hashes(case))
    for key in ("runtime_audit","solver_steps","final_time_s","error","early_split_cadence_gate"):
        r.pop(key,None)
    save(case/REPORT,r)
    return r
def pressure_fix(case,r):
    fv=case/"system/metal/fvSolution";before=fv.read_text()
    points=list(ref.POINT.finditer(before));need(len(points)==1,"reference point not unique")
    original=tuple(map(float,points[0][1].split()))
    i,centre,distance=ref.nearest_cell(case,original,case/"log.referenceCellCentres")
    after,n=ref.POINT.subn("    pRefPoint ("+" ".join(format(x,".15g") for x in centre)+");",before)
    need(n==1,"reference change failed")
    fv.write_text(after)
    r["reference_point_recovery"]={"original_m":original,"new_m":centre,"cell_index":i,
                                   "displacement_m":distance,"physical_validation":False}
    r["input_sha256"]=q.transfer.input_hashes(case);save(case/REPORT,r)
    print("REFERENCE_POINT_CHANGE",case.name,r["reference_point_recovery"],flush=True)

def rank_samples(case,writer,t,wall):
    hz=os.sysconf("SC_CLK_TCK")
    for pid,a in q.procs():
        if Path(a[0]).name!="foamMultiRun" or str(case) not in a:continue
        try:
            env=(Path("/proc")/str(pid)/"environ").read_bytes().split(b"\0")
            rank=next(int(x.split(b"=",1)[1]) for x in env if x.startswith(b"OMPI_COMM_WORLD_RANK="))
            fields=(Path("/proc")/str(pid)/"stat").read_text().rsplit(")",1)[1].split()
            writer.writerow((t,wall,rank,pid,(int(fields[11])+int(fields[12]))/hz))
        except (OSError,ValueError,StopIteration,IndexError):pass

def solve(case):
    started=time.monotonic();count=0;ranks=None;end=fatal=False;tail=deque(maxlen=35)
    with (case/"log.foamMultiRun").open("x",buffering=1) as log, \
         (case/"TIMING_STEPS.csv").open("x",buffering=1) as tf, \
         (case/"TIMING_MPI_RANKS.csv").open("x",buffering=1) as rf:
        w=csv.writer(tf);w.writerow(("step","physical_time_s","wall_since_solver_launch_s","openfoam_execution_time_s","openfoam_clock_time_s"))
        rw=csv.writer(rf);rw.writerow(("physical_time_s","wall_since_solver_launch_s","mpi_rank","pid","sampled_rank_cpu_seconds"))
        p=subprocess.Popen(q.MPI_CMD+["foamMultiRun","-case",str(case),"-parallel"],
                           cwd=case,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace",start_new_session=True)
        current=None;last_cpu_sample=0.
        try:
            for line in p.stdout:
                log.write(line);tail.append(line)
                end|=line.strip()=="End";fatal|="FOAM FATAL" in line
                m=q.RANK.match(line)
                if m:ranks=int(m[1]);need(ranks==8,"unexpected MPI ranks")
                m=q.TIME.match(line)
                if m:
                    count+=1;t=float(m[1]);need(abs(t-count/1000)<1e-7,"time grid drift")
                    current=t
                m=re.search(r"ExecutionTime\s*=\s*([0-9.eE+-]+)\s*s\s+ClockTime\s*=\s*([0-9.eE+-]+)\s*s",line)
                if m and current is not None:
                    wall=time.monotonic()-started
                    w.writerow((count,current,wall,m[1],m[2]))
                    if count==1 or count%1000==0:
                        print(f"{case.name}: {current:g}/200 s | MPI 8 | wall {wall:.1f}s",flush=True)
                        need(shutil.disk_usage(case).free>q.transfer.RESERVE,"disk reserve reached")
                    if wall-last_cpu_sample>=10 or count==1:
                        rank_samples(case,rw,current,wall);last_cpu_sample=wall
                    current=None
            rc=p.wait()
        except BaseException:
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=15)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            raise
    if rc or fatal or not end:
        print("NATIVE_FAILURE",case,"".join(tail),flush=True)
        raise RuntimeError("native solver failed: "+str(rc))
    need(ranks==8 and count==200000,"incomplete native fixed-step run")
    return time.monotonic()-started

def execute(case,r):
    r["status"]="RUNNING_MPI";save(case/REPORT,r)
    r["decomposition_wall_s"]=q.native(case,"log.decomposePar",
        ["decomposePar","-allRegions","-case",str(case)])
    need(all((case/f"processor{i}"/"0").is_dir() for i in range(8)),"decomposition incomplete")
    r["solver_wall_s"]=solve(case)
    r.update(solver_completed=True,solver_steps=200000,final_time_s=200,
             status="MPI_SOLVER_COMPLETE_RECONSTRUCT_PENDING")
    save(case/REPORT,r)
    return r

def audit(case,r):
    started=time.monotonic()
    r["reconstruction_wall_s"]=q.native(case,"log.reconstructPar",
        ["reconstructPar","-allRegions","-time","1:200","-case",str(case)])
    needed=q.compact.DERIVED
    if not all((case/"0/metal"/f).is_file() for f in needed):
        q.native(case,"log.reconstructZero",["reconstructPar","-allRegions","-withZero","-time","0","-case",str(case)])
    audit_start=time.monotonic()
    q.compact.check_native(case,"log.foamLog",["foamLog","log.foamMultiRun"])
    r["runtime_audit"]=q.compact.audit(case,r)
    r["audit_wall_s"]=time.monotonic()-audit_start
    r["postsolver_wall_s"]=time.monotonic()-started
    r["status"]="SOLVER_COMPLETE_FIXED_MPI_AUDITED" if r["runtime_audit"]["native_runtime_coverage_complete"] else "FIXED_MPI_DIAGNOSTICS_INCOMPLETE"
    save(case/REPORT,r)
    return r

def main():
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(len(os.sched_getaffinity(0))>=8,"eight CPUs unavailable")
    for cmd in ("foamMultiRun","decomposePar","reconstructPar","foamLog","mpirun"):
        need(shutil.which(cmd),"missing "+cmd)
    ROOT.mkdir(exist_ok=True)
    with (ROOT/".queue.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(q.read(q.SRC/"C14-3DA-200s"/REPORT)["status"]=="SOLVER_COMPLETE_COMPACT_AUDITED","completed reference not confirmed")
        q.mpi_preflight()
        run=Path(tempfile.mkdtemp(prefix="run-",dir=ROOT))
        print("FRESH_CAMPAIGN",run,flush=True)
        # Copy exact original inputs for all cases before interrupting active CFD.
        prepared={}
        for name in ORDER:
            prepared[name]=fresh_inputs(name,run/name)
        stop_previous()
        summary={"C14-3DA-200s":{"status":"SERIAL_COMPLETE_PRESERVED","path":str(q.SRC/"C14-3DA-200s")}}
        index=run/"QUEUE_STATUS.json";save(index,summary)
        completed=[]
        for name in ORDER:
            case=run/name;r=prepared[name]
            try:
                print("NEXT_FRESH_CASE",name,flush=True)
                # Apply a pressure-reference correction only after a demonstrated
                # zero-step reference failure, preserving the first fresh attempt.
                old=q.DST/name
                if ref.ref_failure(old):pressure_fix(case,r)
                try:r=execute(case,r)
                except Exception:
                    if not ref.ref_failure(case) or r.get("reference_point_recovery"):raise
                    backup=run/(name+".reference-failed");case.rename(backup)
                    r=fresh_inputs(name,case);pressure_fix(case,r);r=execute(case,r)
                completed.append((case,r))
                summary[name]={"status":r["status"],"path":str(case),"solver_wall_s":r["solver_wall_s"]}
            except Exception as exc:
                r["error"]=str(exc);save(case/REPORT,r)
                summary[name]={"status":"FAILED_PRESERVED","path":str(case),"error":str(exc)}
            save(index,summary);print("CASE_STATUS",name,summary[name],flush=True)
        print("CFD_QUEUE_FINISHED_STARTING_POSTPROCESSING",flush=True)
        for case,r in completed:
            try:
                r=audit(case,r)
                summary[case.name].update(status=r["status"],reconstruction_wall_s=r["reconstruction_wall_s"],audit_wall_s=r["audit_wall_s"])
            except Exception as exc:
                r["error"]=str(exc);save(case/REPORT,r)
                summary[case.name].update(status="POSTSOLVER_BLOCKED_PRESERVED",error=str(exc))
            save(index,summary);print("AUDIT_STATUS",case.name,summary[case.name],flush=True)
        print("FRESH_QUEUE_FINISHED",index,flush=True)
if __name__=="__main__":main()
