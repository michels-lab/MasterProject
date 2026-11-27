#!/usr/bin/env python3
"""Retry ONLY zero-step pRefPoint failures after the active fixed MPI queue.
Original serial files and failed attempts are preserved. No active CFD is stopped.
"""
import fcntl
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import run_lab_fixed_mpi8 as q

AUDIT=q.HOME/"CAMPAIGN_200S_FIXED_MPI_08_AUDIT"
NUM=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
POINT=re.compile(r"(?m)^[ \t]*pRefPoint[ \t]+\(([^)]+)\)[ \t]*;")

def ref_failure(case):
    if not case.exists() and not case.is_symlink():return False
    log=q.transfer.checked_relative(case,"log.foamMultiRun")
    if not log.is_file(): return False
    fatal=False
    with log.open(errors="replace") as f:
        for line in f:
            if q.TIME.match(line): return False
            fatal |= "Unable to set reference cell for field p" in line
    return fatal

def nearest_cell(case, original, evidence):
    q.need(len(original)==3 and all(math.isfinite(x) for x in original),"invalid reference coordinate")
    # Use the native serial mesh on a private copy; no change to initial fields.
    with tempfile.TemporaryDirectory(prefix="reference-mesh-",dir=q.HOME) as d:
        tmp=Path(d)
        for folder in ("0","constant","system"):
            shutil.copytree(case/folder,tmp/folder)
        control=tmp/"system/controlDict"
        s=control.read_text()
        s,n=re.subn(r"(?m)^writePrecision\s+[^;]+;","writePrecision 15;",s)
        q.need(n==1,"writePrecision not unique")
        control.write_text(s)
        p=subprocess.run(["foamPostProcess","-case",str(tmp),"-region","metal",
                          "-time","0","-func","writeCellCentres"],
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        evidence.write_text(p.stdout)
        q.need(p.returncode==0 and "FOAM FATAL" not in p.stdout,
               "native cell-centre calculation failed: "+str(evidence))
        field=tmp/"0/metal/C"
        q.need(field.is_file(),"missing native centre field")
        text=field.read_text()
        m=re.search(r"\binternalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\((.*?)\)\s*;",text,re.S)
        q.need(m is not None,"cannot parse native cell centres")
        points=[tuple(map(float,t)) for t in re.findall(r"\(\s*("+NUM+r")\s+("+NUM+r")\s+("+NUM+r")\s*\)",m[2])]
        q.need(len(points)==int(m[1]) and points and all(math.isfinite(v) for p in points for v in p),"invalid centre field")
        i=min(range(len(points)),key=lambda i: math.dist(points[i],original))
        return i,points[i],math.dist(points[i],original)

def retry(name,case,summary):
    q.need(name in q.NAMES and case==q.DST/name,"invalid reference recovery case")
    q.transfer.checked_relative(q.DST,name)
    q.need(ref_failure(case),"not a zero-step reference failure")
    backup=Path(tempfile.mkdtemp(prefix=name+"-reference-failure-",dir=q.HOME))
    case.rename(backup/name)
    print("PRESERVED",backup/name,flush=True)
    prepared=q.prepare(name)
    q.need(prepared is not None,"source solver already complete")
    case,meta=prepared
    fv=case/"system/metal/fvSolution"
    before=fv.read_text()
    matches=list(POINT.finditer(before))
    q.need(len(matches)==1,"pRefPoint not unique")
    original=tuple(map(float,matches[0][1].split()))
    q.need(len(original)==3,"invalid original reference point")
    index,centre,distance=nearest_cell(case,original,case/"log.referenceCellCentres")
    # Original coordinate is preserved in the serial case and this metadata.
    # pRefValue, tolerances, dt, mesh and boundary conditions remain unchanged.
    after,n=POINT.subn("    pRefPoint ("+" ".join(format(x,".15g") for x in centre)+");",before)
    q.need(n==1,"reference replacement failed")
    q.need(re.findall(r"(?m)^\s*pRefValue\s+[^;]+;",before)==re.findall(r"(?m)^\s*pRefValue\s+[^;]+;",after),"pRefValue drift")
    fv.write_text(after)
    meta["reference_point_recovery"]={"original_m":original,"new_m":centre,
        "nearest_serial_cell_index":index,"displacement_m":distance,
        "method":"native serial cell centres; nearest Euclidean centre",
        "physical_validation":False,"before_sha256":q.transfer.sha(backup/name/"system/metal/fvSolution"),
        "after_sha256":q.transfer.sha(fv),"failed_attempt_path":str(backup/name)}
    q.save(case/"MPI_RUN_METADATA.json",meta)
    print("REFERENCE_POINT_RECOVERY",name,meta["reference_point_recovery"],flush=True)
    return q.execute((case,meta))

def main():
    q.need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    q.need((q.DST/".queue.lock").is_file(),"original queue missing")
    q.need(not AUDIT.is_symlink() and not q.DST.is_symlink(),"unsafe recovery root")
    AUDIT.mkdir(exist_ok=True)
    with q.transfer.checked_relative(AUDIT,".finalize.lock").open("a") as audit, q.transfer.checked_relative(q.DST,".queue.lock").open("a") as lock:
        print("WAITING_FOR_ACTIVE_CFD_QUEUE_WITHOUT_INTERRUPTING",flush=True)
        fcntl.flock(audit,fcntl.LOCK_EX)
        fcntl.flock(lock,fcntl.LOCK_EX)
        index=q.DST/"QUEUE_STATUS.json"
        summary=q.read(index)
        q.mpi_preflight()
        for name in q.NAMES:
            case=q.DST/name
            status=summary.get(name,{}).get("status")
            if status!="FAILED_PRESERVED" or not ref_failure(case):
                print("UNCHANGED",name,status,flush=True)
                continue
            try:
                summary[name]=retry(name,case,summary)
            except Exception as exc:
                summary[name]={"status":"FAILED_PRESERVED","error":str(exc)}
            q.save(index,summary)
            print("RECOVERY_STATUS",name,summary[name],flush=True)
    print("RECOVERY_QUEUE_FINISHED_STARTING_FINALIZATION",flush=True)
    subprocess.run([sys.executable,"-u","-B",str(q.HOME/"finalize_lab_fixed_mpi8.py")],check=True)
if __name__=="__main__":
    main()
