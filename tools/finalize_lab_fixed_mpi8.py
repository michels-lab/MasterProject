#!/usr/bin/env python3
"""Postsolver-only lab fixed-step MPI campaign recovery and publication.
Never starts/stops CFD or modifies the original serial/MPI case directories.
A merged scientific archive is published only after the pinned compact audit.
"""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

import compact_campaign_200s as compact
import transfer_campaign_200s as transfer

HOME = transfer.HOME
SERIAL = transfer.COMPACT
MPI = HOME / "CAMPAIGN_200S_FIXED_MPI_08"
OUT = HOME / "CAMPAIGN_200S_FIXED_MPI_08_AUDIT"
REPORT = transfer.REPORT
TIME = re.compile(r"^\s*Time\s*=\s*([0-9.eE+-]+)s?\s*$")
NAMES = ("C14-3DA-200s", "C14-2D-200s", "B14-2D-200s", "C14-3DB-200s")
MPI_PREFIX = "results/campaign-200s-fixed-mpi-r8-v1/"
EPS = 1e-7

def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def save(path, value):
    compact.json_out(path,value)

def number(name):
    try:
        v = float(name)
        return v if math.isfinite(v) else None
    except ValueError:
        return None

def read(path):
    return json.loads(path.read_text())

def native_log(path):
    steps = []
    ranks = None
    end = fatal = False
    with path.open(errors="replace") as f:
        for line in f:
            m = TIME.match(line)
            if m:
                steps.append(float(m[1]))
            m = re.match(r"^\s*nProcs\s*:\s*(\d+)", line)
            if m:
                ranks = int(m[1])
            end |= line.strip() == "End"
            fatal |= "FOAM FATAL" in line
    return steps, ranks, end, fatal

def complete_steps(steps, start, end):
    return (len(steps) == round((end-start)*1000)
            and all(abs(t-(start+i/1000)) < EPS
                    for i,t in enumerate(steps,1)))

def native_command(case, log, args):
    with (case / log).open("x") as f:
        subprocess.run(args, cwd=case, stdout=f, stderr=subprocess.STDOUT, check=True)
    need("FOAM FATAL" not in (case/log).read_text(errors="replace"),
         "native fatal: " + log)

def table_merge(paths, target, start):
    """paths: list of (file, phase). Keep serial <= restart, MPI > restart."""
    header = None
    data = {}
    for path, phase in paths:
        comments = []
        with path.open() as f:
            for line in f:
                if line.lstrip().startswith("#"):
                    comments.append(line)
                    continue
                if not line.strip():
                    continue
                t = float(line.split()[0])
                need(math.isfinite(t), "invalid native table time " + str(path))
                if phase == "serial" and t > start+EPS:
                    continue
                if phase == "mpi" and start and t <= start+EPS:
                    continue
                key = round(t*1000)
                need(abs(t-key/1000)<EPS, "off-grid table time " + str(path))
                row = line.strip().split()
                if key in data:
                    need(data[key].strip().split() == row, "conflicting duplicate sample " + str(path))
                else:
                    data[key] = line if line.endswith("\n") else line+"\n"
        if header is None:
            header = comments
    need(data, "empty merged table " + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as f:
        f.writelines(header or [])
        for key in sorted(data):
            f.write(data[key])

def merge_diagnostics(case, src, mpi, start, report):
    pp = case/"postProcessing/metal"
    sources = [(src/"postProcessing/metal","serial")] if start else []
    sources.append((mpi/"postProcessing/metal","mpi"))
    for group in ("temperatureProbe", *compact.REDUCTIONS):
        if group == "temperatureProbe":
            names = compact.PROBES
        else:
            names = sorted({p.name for root,_ in sources
                            for p in (root/group).glob("*/*.dat")})
            need(len(names)==1, "missing/ambiguous reduction " + group)
        for name in names:
            inputs = []
            for root,phase in sources:
                files = sorted((root/group).glob("*/"+name))
                need(files, "missing segment " + phase + " " + group + "/" + name)
                inputs.extend((p,phase) for p in files)
            table_merge(inputs, pp/group/"0"/name, start)
    groups = (*compact.profile_groups(report), "nearTopInternalLine", "topFlow")
    for group in groups:
        for root, phase in sources:
            folder = root/group
            need(folder.is_dir(), "missing profile group " + str(folder))
            for path in sorted(folder.iterdir()):
                t = number(path.name)
                if not path.is_dir() or t is None:
                    continue
                if phase=="serial" and t>start+EPS:
                    continue
                if phase=="mpi" and start and t<=start+EPS:
                    continue
                dest = pp/group/format(t,"g")
                need(not dest.exists(), "duplicate native profile directory "+str(dest))
                shutil.copytree(path,dest)

def combine_log(case, src, mpi, start):
    out = case/"log.foamMultiRun"
    mpi_log = mpi/"log.foamMultiRun"
    steps,ranks,end,fatal = native_log(mpi_log)
    need(ranks==8 and end and not fatal and complete_steps(steps,start,200),
         "MPI native log does not prove exact 8-rank fixed-step completion")
    if not start:
        shutil.copy2(mpi_log,out)
        return
    serial_log = src/"log.foamMultiRun"
    steps0,serial_ranks,_,fatal0 = native_log(serial_log)
    need(serial_ranks==1,"serial prefix rank identity not confirmed")
    need(complete_steps([t for t in steps0 if t<=start+EPS],0,start),
         "serial prefix has missing/duplicate steps")
    with out.open("x") as f, serial_log.open(errors="replace") as s:
        for line in s:
            m=TIME.match(line)
            if m and float(m[1])>start+EPS:
                break
            f.write(line)
        f.write("\n# Restart boundary: serial to eight MPI ranks at "+str(start)+" s\n")
        with mpi_log.open(errors="replace") as m:
            shutil.copyfileobj(m,f)
    merged,rank,ended,fatal=native_log(out)
    need(rank==8 and ended and not fatal and complete_steps(merged,0,200), "merged native log time grid invalid or fatal")

def stage_mpi(name):
    need(name in NAMES,"unknown lab case")
    src,mpi = transfer.checked_relative(SERIAL,name),transfer.checked_relative(MPI,name)
    report = read(transfer.checked_relative(src,REPORT))
    metadata = read(transfer.checked_relative(mpi,"MPI_RUN_METADATA.json"))
    start = metadata["restart_time_s"]
    need(type(start) is int and 0<=start<200 and
         metadata["mpi_ranks"]==8 and metadata["deltaT"]==.001 and
         metadata["end_time_s"]==200, "unexpected MPI metadata")
    need(metadata["status"]=="MPI_COMPLETE_RECONSTRUCTED",
         "MPI run/reconstruction not confirmed by queue")
    need((mpi/"log.reconstructPar").is_file() and
         "End" in (mpi/"log.reconstructPar").read_text(errors="replace").splitlines(),
         "reconstruction did not finish")
    parent = Path(tempfile.mkdtemp(prefix=name+"-",dir=OUT))
    case = parent/name
    case.mkdir()
    print("AUDIT_STAGE",case,flush=True)
    shutil.copytree(mpi/"system",case/"system")
    shutil.copytree(mpi/"constant",case/"constant")
    required = {"metal":("T","U","p","p_rgh","phaseChangeSource:alpha1")+compact.DERIVED,
                "mold":("T",)}
    def fields_ok(p):
        return all((p/reg/f).is_file() and (p/reg/f).stat().st_size>0
                   for reg,fields in required.items() for f in fields)
    # Audit positive times in place via read-only-by-convention symlinks;
    # no native command will write to these directories.
    for t in range(1,201):
        path = (src if t<=start else mpi)/str(t)
        need(fields_ok(path),"missing volumetric fields "+str(path))
        (case/str(t)).symlink_to(path,target_is_directory=True)
    initial = (src if start else mpi)/"0"
    shutil.copytree(initial,case/"0")
    if not fields_ok(case/"0") and not start:
        need(all(fields_ok(mpi/f"processor{i}"/"0") for i in range(8)),
             "zero-time native fields unavailable; no fabrication")
        for i in range(8):
            (case/f"processor{i}").symlink_to(mpi/f"processor{i}",target_is_directory=True)
        native_command(case,"log.reconstructZero",
            ["reconstructPar","-allRegions","-withZero","-time","0","-case",str(case)])
    need(fields_ok(case/"0"),"zero-time field coverage incomplete")
    combine_log(case,src,mpi,start)
    merge_diagnostics(case,src,mpi,start,report)
    native_command(case,"log.foamLog",["foamLog","log.foamMultiRun"])
    for filename in ("log.decomposePar","log.reconstructPar","MPI_RUN_METADATA.json"):
        shutil.copy2(mpi/filename,case/filename)
    report.update(status="MPI_SOLVER_COMPLETE_AUDIT_PENDING",
        solver_completed=True, solver_steps=200000, final_time_s=200,
        physical_validation=False, mpi_ranks=8, restart_time_s=start,
        execution_mode="serial_then_mpi" if start else "mpi",
        time_mode="fixed", deltaT_s=.001,
        diagnostic_merge_policy="serial through checkpoint inclusive; MPI strictly after; no interpolation",
        original_serial_report_sha256=transfer.sha(src/REPORT),
        original_mpi_log_sha256=transfer.sha(mpi/"log.foamMultiRun"),
        original_serial_log_sha256=transfer.sha(src/"log.foamMultiRun") if start else None,
        diagnostic_scope="pinned compact audit groups; raw segments remain local",
        source_paths={"serial":str(src),"mpi":str(mpi)},
        input_sha256=transfer.input_hashes(case))
    report.pop("error",None)
    save(case/REPORT,report)
    report["runtime_audit"]=compact.audit(case,report)
    ok=report["runtime_audit"]["native_runtime_coverage_complete"]
    report["status"]="SOLVER_COMPLETE_FIXED_MPI_AUDITED" if ok else "FIXED_MPI_DIAGNOSTICS_INCOMPLETE"
    save(case/REPORT,report)
    need(ok,"coverage audit failed: "+str(report["runtime_audit"]["errors"]))
    return case

def publish(case,url,branch,mode):
    r=read(case/REPORT)
    need(r["runtime_audit"]["native_runtime_coverage_complete"] is True,
         "publication blocked without complete coverage")
    transfer.BATCH=1  # Keep 32 MiB chunk boundaries compatible with earlier attempt.
    metadata={"kind":"scientific_results" if mode=="serial" else "fixed_mpi_scientific_results",
        "case":case.name,"solver_steps":200000,"final_time_s":200,
        "solver_log_sha256":transfer.sha(case/"log.foamMultiRun"),
        "report_sha256":transfer.sha(case/REPORT),
        "native_runtime_coverage_complete":True,
        "status":r["status"],"volume_fields_included":False}
    if mode!="serial":
        metadata.update(mpi_ranks=8,time_mode="fixed",deltaT_s=.001,
                        restart_time_s=r["restart_time_s"],
                        execution_mode=r["execution_mode"])
    with tempfile.TemporaryDirectory(prefix="archive-",dir=OUT) as tmp:
        root=Path(tmp)
        archive=root/"result.tar.gz"
        if mode=="serial":
            transfer.archive_results(archive,case)
        else:
            with transfer.deterministic_tar(archive) as t:
                for filename in ("postProcessing","logs",REPORT,"log.foamMultiRun",
                                 "log.foamLog","log.decomposePar","log.reconstructPar",
                                 "log.reconstructZero","MPI_RUN_METADATA.json"):
                    p=case/filename
                    if p.exists():
                        transfer.add(t,p,case.name+"/"+filename)
        for attempt in range(1,4):
            try:
                m=transfer.complete_manifest(url,branch)
                if m is not None:
                    need(m["solver_log_sha256"]==metadata["solver_log_sha256"] and
                         m["report_sha256"]==metadata["report_sha256"],
                         "remote complete result differs; refusing overwrite")
                    return branch
                transfer.publish(url,branch,archive,metadata,
                                 root/f"git-{attempt}",case=case)
                return branch
            except subprocess.SubprocessError as exc:
                print("PUBLICATION_RETRY",attempt,branch,str(exc),flush=True)
                if attempt==3:
                    raise
                time.sleep(15*attempt)
    raise RuntimeError("publication failed")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo",type=Path,default=HOME/"MasterProject")
    ap.add_argument("--serial-only",action="store_true",
                    help="retry C14-3DA publication without waiting for MPI")
    ap.add_argument("--audit-only",action="store_true")
    a=ap.parse_args()
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14")
    need(not OUT.is_symlink(),"unsafe finalization root")
    OUT.mkdir(exist_ok=True)
    url=transfer.root_url(a.repo)
    with transfer.checked_relative(OUT,".finalize.lock").open("a") as own:
        fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not a.serial_only:
            need((MPI/".queue.lock").is_file(),"MPI queue has not been launched")
            print("WAITING_FOR_MPI_QUEUE_TO_RELEASE_LOCK",flush=True)
            with transfer.checked_relative(MPI,".queue.lock").open("a") as queue:
                fcntl.flock(queue,fcntl.LOCK_EX)
                need((MPI/"QUEUE_STATUS.json").is_file(),"queue status unavailable")
                finish(url,NAMES,a.audit_only)
        else:
            finish(url,NAMES[:1],a.audit_only)

def finish(url,names,audit_only):
    index=transfer.checked_relative(OUT,"FINALIZATION_STATUS.json")
    summary=read(index) if index.is_file() else {}
    for name in names:
        case=None
        try:
            src=transfer.checked_relative(SERIAL,name)
            r=read(transfer.checked_relative(src,REPORT))
            if r.get("solver_completed") and r.get("final_time_s")==200:
                need(r["status"]=="SOLVER_COMPLETE_COMPACT_AUDITED",
                     "serial solver is not fully audited")
                case=src
                mode="serial"
                branch=transfer.RESULT_PREFIX+name
            else:
                mode="mpi"
                branch=MPI_PREFIX+name
                previous=summary.get(name,{})
                old=Path(previous["audit_path"]) if previous.get("audit_path") else None
                if old is not None:
                    need(old.is_absolute() and old.is_relative_to(OUT) and old.name==name,"invalid prior audit path")
                    transfer.checked_relative(OUT,old.relative_to(OUT))
                if old and old.is_dir() and transfer.checked_relative(old,REPORT).is_file() and read(old/REPORT).get("status")=="SOLVER_COMPLETE_FIXED_MPI_AUDITED":
                    case=old
                else:
                    case=stage_mpi(name)
            summary[name]={"status":"AUDITED","audit_path":str(case),"mode":mode}
            save(index,summary)
            if not audit_only:
                summary[name]["branch"]=publish(case,url,branch,mode)
                summary[name]["status"]="PUBLISHED"
        except Exception as exc:
            summary[name]={"status":"BLOCKED_PRESERVED","error":str(exc),
                           "audit_path":str(case) if case else None}
        save(index,summary)
        print(name,summary[name],flush=True)
    expected="AUDITED" if audit_only else "PUBLISHED"
    need(all(summary.get(n,{}).get("status")==expected for n in names),
         "finalization incomplete; consult "+str(index))

if __name__=="__main__":
    main()
