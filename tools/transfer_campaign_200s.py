#!/usr/bin/env python3
"""Portable 200s campaign via private Git branches; no calculated volume uploads.
Run from a standalone downloaded script. Requires Python3, git; CFD needs OF14.
Input branch contains dense+compact initial case inputs and pinned solver script.
Result branches carry per-case compressed, SHA256-verified scientific archives.
"""
from __future__ import annotations
import argparse
import hashlib
import gzip
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import sys

HOME=Path.home()/"OpenFOAM"
DENSE=HOME/"CAMPAIGN_200S_01"
COMPACT=HOME/"CAMPAIGN_200S_COMPACT_01"
REPORT="CAMPAIGN_200S_REPORT.json"
ORDER=("C14-3DA-200s","C14-2D-200s","B14-2D-200s","B14-3DA-200s","C14-3DB-200s","B14-3DB-200s")
PIN="50d3bbd7750756d7d854eaa2a6f8d69157a3341f"
INPUT_BRANCH="transfer/campaign-200s-compact-inputs-v1"
RESULT_PREFIX="results/campaign-200s-compact-v1/"
CHUNK=32*1024*1024
BATCH=10
RESERVE=10*1024**3

def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def git(*args,cwd=None,capture=False):
    p=subprocess.run(["git",*map(str,args)],cwd=cwd,check=True,text=True,stdout=subprocess.PIPE if capture else None)
    return p.stdout.strip() if capture else None
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2)+"\n")
def input_hashes(p):
    h={}
    for d in ("0","constant","system"):
        for q in (p/d).rglob("*"):
            need(not q.is_symlink(),"symlink input: "+str(q))
            if q.is_file():h[str(q.relative_to(p))]=sha(q)
    return h
def root_url(repo):
    url=git("remote","get-url","origin",cwd=repo,capture=True)
    need("michels-lab/MasterProject" in url,"origin must be MasterProject")
    return url
def remote_head(url,branch):
    return git("ls-remote","--heads",url,"refs/heads/"+branch,capture=True)
def numeric_time(p):
    try:return float(p.name)
    except ValueError:return None
def untouched(p):
    r=read(p/REPORT)
    need(r["status"] in ("PREPARED_NOT_RUN","PREPARED_COMPACT_NOT_RUN") and not r.get("solver_completed"),"case not unrun "+str(p))
    need(not (p/"log.foamMultiRun").exists() and not (p/"postProcessing").exists(),"solver evidence exists "+str(p))
    need(not any(q.is_dir() and (v:=numeric_time(q)) is not None and v>0 for q in p.iterdir()),"positive time exists "+str(p))
    need(input_hashes(p)==r["input_sha256"],"input SHA mismatch "+str(p))
    return r
def add(t,p,arc):
    need(p.exists() and not p.is_symlink(),"missing/linked "+str(p))
    def filt(info):
        need(info.isfile() or info.isdir(),"nonregular archive entry "+info.name)
        info.uid=info.gid=0;info.uname=info.gname="";info.mtime=0
        return info
    t.add(p,arcname=arc,recursive=True,filter=filt)
@contextmanager
def deterministic_tar(path):
    with path.open("xb") as raw:
        with gzip.GzipFile(filename="",fileobj=raw,mode="wb",compresslevel=3,mtime=0) as zipped:
            with tarfile.open(fileobj=zipped,mode="w") as t:
                yield t
def archive_inputs(path,repo):
    solver=subprocess.check_output(["git","-C",str(repo),"show",PIN+":tools/compact_campaign_200s.py"])
    with deterministic_tar(path) as t:
        for root in (DENSE,COMPACT):
            for name in ORDER:
                p=root/name;r=untouched(p)
                need(r["case"]==name,"wrong identity")
                if root==COMPACT:
                    need(r["source_input_sha256"]==read(DENSE/name/REPORT)["input_sha256"],"dense provenance mismatch")
                    need(r["implementation_sha256"]==hashlib.sha256(solver).hexdigest(),"prepared solver differs from pinned script")
                for d in ("0","constant","system",REPORT):add(t,p/d,root.name+"/"+name+"/"+d)
                marker=p/(name+".foam")
                if marker.exists():add(t,marker,root.name+"/"+name+"/"+marker.name)
            for f in ("CAMPAIGN_INDEX.json","CAMPAIGN_RESOURCES.json"):add(t,root/f,root.name+"/"+f)
        with tempfile.TemporaryDirectory() as tmp:
            script=Path(tmp)/"compact_campaign_200s.py";script.write_bytes(solver)
            add(t,script,script.name)
def archive_results(path,case):
    r=read(case/REPORT)
    need(r.get("solver_completed") is True and r.get("solver_steps")==200000 and r.get("final_time_s")==200,
         "case did not finish 200s: "+case.name)
    need((case/"postProcessing").is_dir() and (case/"log.foamMultiRun").is_file(),"missing analysis evidence")
    # Preserve original folder structure for FoamLens. Mesh and initial inputs
    # are in the transfer branch, NOT duplicated here. No 1..200 field dirs.
    with deterministic_tar(path) as t:
        for d in ("postProcessing","logs",REPORT,"log.foamMultiRun","log.foamLog"):
            p=case/d
            if p.exists():add(t,p,case.name+"/"+d)
        for p in sorted(case.glob("log.campaign.*")):add(t,p,case.name+"/"+p.name)
    return r
def init_repo(p,url):
    git("init","-q",cwd=p)
    git("remote","add","origin",url,cwd=p)
    # Respect global identity; local fallback is the explicit campaign bot.
    if not subprocess.run(["git","var","GIT_AUTHOR_IDENT"],cwd=p,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
        git("config","user.name","MasterProject campaign",cwd=p)
        git("config","user.email","campaign@users.noreply.github.com",cwd=p)
def preview(case,work):
    """Small native-data view for direct GitHub analysis, not full archive."""
    dst=work/"analysis_preview";dst.mkdir(exist_ok=True)
    shutil.copy2(case/REPORT,dst/REPORT)
    pp=case/"postProcessing/metal"
    probe=pp/"temperatureProbe/0"
    for field in ("T","U","p_rgh","rho","phaseChangeSource:alpha1"):
        p=probe/field
        if not p.is_file():continue
        target=dst/"postProcessing/metal/temperatureProbe/0"/field
        target.parent.mkdir(parents=True,exist_ok=True)
        with p.open() as f,target.open("w") as out:
            for line in f:
                if line.lstrip().startswith("#"):out.write(line);continue
                if not line.strip():continue
                try:t=float(line.split()[0])
                except ValueError:continue
                if abs(t*10-round(t*10))<1e-7:out.write(line)
    for group in ("metalTopPhiSum","metalTopEnergyPower","metalMoldEnergyPower","metalBoundaryEnergyPower",
                  "metalSensibleEnthalpy","metalMeanLiquidFraction","metalLatentHeatPower","metalMeanCoolingRate",
                  "metalMeanSolidificationRate","metalMaxCourant","metalMaxThermalGradient","metalMaxDensityGradient"):
        for p in (pp/group).glob("*/*.dat"):
            if p.stat().st_size>10*1024**2:continue
            target=dst/"postProcessing/metal"/group/p.parent.name/p.name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    (dst/"README.md").write_text("Native exact-time subset of central probes at 0.1 s; reductions as saved. No interpolation. Full probes, profiles and logs are in the verified archive. Not an independent physical validation.\n")
def publish(url,branch,archive,metadata,work,case=None):
    # New independent result branch: no checkout or mutations of MasterProject.
    # Small pushes, even when the final archive is several GB.
    exists=bool(remote_head(url,branch))
    work.mkdir()
    init_repo(work,url)
    if exists:
        git("fetch","--depth=1","origin","refs/heads/"+branch,cwd=work)
        git("checkout","--detach","FETCH_HEAD",cwd=work)
        need(not (work/"MANIFEST.json").exists(),"complete branch already exists; no overwrite")
    parts=[];pending=[]
    with archive.open("rb") as f:
        i=0
        while data:=f.read(CHUNK):
            name=f"archive.tar.gz.part{i:06d}"
            chunk=work/name
            if chunk.exists():need(sha(chunk)==hashlib.sha256(data).hexdigest(),"existing partial chunk differs: "+name)
            else:chunk.write_bytes(data);pending.append(name)
            parts.append({"name":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
            i+=1
    need(parts,"empty archive")
    manifest={**metadata,"archive_bytes":archive.stat().st_size,"archive_sha256":sha(archive),"parts":parts,
              "archive_format":"tar.gz split into ordered binary chunks","complete":True}
    # Manifest is committed LAST; readers never accept an incomplete upload.
    need(set(q.name for q in work.glob("archive.tar.gz.part*"))==set(p["name"] for p in parts),"unexpected old partial chunks")
    for i in range(0,len(pending),BATCH):
        group=pending[i:i+BATCH]
        git("add","--",*group,cwd=work)
        git("commit","-qm",f"Archive chunks {i+1}-{i+len(group)} / {len(parts)}",cwd=work)
        git("push","origin","HEAD:refs/heads/"+branch,cwd=work)
    dump(work/"MANIFEST.json",manifest)
    if case is not None:
        preview(case,work)
        git("add","analysis_preview",cwd=work)
    git("add","MANIFEST.json",cwd=work)
    git("commit","-qm","Complete archive SHA256 manifest",cwd=work)
    git("push","origin","HEAD:refs/heads/"+branch,cwd=work)
    print("PUBLICADO",branch,flush=True)
def download(url,branch,work,archive):
    work.mkdir()
    init_repo(work,url)
    git("fetch","--depth=1","origin","refs/heads/"+branch,cwd=work)
    git("checkout","--detach","FETCH_HEAD",cwd=work)
    m=read(work/"MANIFEST.json")
    need(m.get("complete") is True,"incomplete publication "+branch)
    with archive.open("xb") as out:
        for i,p in enumerate(m["parts"]):
            need(p["name"]==f"archive.tar.gz.part{i:06d}","invalid part name/order")
            q=work/p["name"]
            need(q.stat().st_size==p["bytes"] and sha(q)==p["sha256"],"chunk SHA mismatch")
            with q.open("rb") as f:shutil.copyfileobj(f,out)
    need(archive.stat().st_size==m["archive_bytes"] and sha(archive)==m["archive_sha256"],"archive SHA mismatch")
    return m
def extract(archive,dst):
    # No symlinks, absolute paths, traversal, or pre-existing files.
    with tarfile.open(archive,"r:gz") as t:
        for member in t:
            p=Path(member.name)
            need(not p.is_absolute() and ".." not in p.parts and (member.isdir() or member.isfile()),"unsafe archive path")
            target=dst/p
            need(not target.is_symlink(),"symlink destination")
            need(target.resolve().is_relative_to(dst.resolve()),"outside extraction")
            if member.isdir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with t.extractfile(member) as f,target.open("xb") as out:shutil.copyfileobj(f,out)
def complete_manifest(url,branch):
    if not remote_head(url,branch):return None
    with tempfile.TemporaryDirectory(prefix="manifest-",dir=HOME) as d:
        p=Path(d);init_repo(p,url)
        git("fetch","--depth=1","--filter=blob:none","origin","refs/heads/"+branch,cwd=p)
        proc=subprocess.run(["git","show","FETCH_HEAD:MANIFEST.json"],cwd=p,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        if proc.returncode:return None
        m=json.loads(proc.stdout);need(m.get("complete") is True,"invalid published manifest")
        return m
def push_inputs(repo,url):
    HOME.mkdir(exist_ok=True)
    if complete_manifest(url,INPUT_BRANCH) is not None:
        print("INPUTS ALREADY PUBLISHED",INPUT_BRANCH);return
    with tempfile.TemporaryDirectory(prefix="campaign-input-",dir=HOME) as d:
        p=Path(d);archive=p/"input.tar.gz"
        archive_inputs(archive,repo)
        publish(url,INPUT_BRANCH,archive,{"kind":"inputs","solver_commit":PIN,"cases":ORDER},p/"git")
def install_inputs(url):
    HOME.mkdir(exist_ok=True)
    # Existing copies must match the pinned input archive; never overwrite.
    if DENSE.exists() or COMPACT.exists():
        need(DENSE.is_dir() and COMPACT.is_dir(),"only one campaign root exists; preserve")
        for name in ORDER:
            a=untouched(DENSE/name);b=read(COMPACT/name/REPORT)
            need(b["source_input_sha256"]==a["input_sha256"] and input_hashes(COMPACT/name)==b["input_sha256"],"existing compact inputs differ")
        need((HOME/"compact_campaign_200s.py").is_file(),"solver script missing")
        need(all(sha(HOME/"compact_campaign_200s.py")==read(COMPACT/n/REPORT)["implementation_sha256"] for n in ORDER),"existing solver differs from prepared inputs")
        return
    with tempfile.TemporaryDirectory(prefix="campaign-receive-",dir=HOME) as d:
        p=Path(d);archive=p/"input.tar.gz"
        m=download(url,INPUT_BRANCH,p/"git",archive)
        need(m["kind"]=="inputs" and m["solver_commit"]==PIN and tuple(m["cases"])==ORDER,"wrong input manifest")
        stage=p/"unpacked";stage.mkdir();extract(archive,stage)
        for name in ORDER:
            a=untouched(stage/DENSE.name/name);b=untouched(stage/COMPACT.name/name)
            need(b["source_input_sha256"]==a["input_sha256"],"input provenance mismatch")
            need(sha(stage/"compact_campaign_200s.py")==b["implementation_sha256"],"solver mismatch")
        script=HOME/"compact_campaign_200s.py"
        if script.exists():need(sha(script)==sha(stage/script.name),"existing script differs")
        else:shutil.copy2(stage/script.name,script)
        (stage/DENSE.name).rename(DENSE);(stage/COMPACT.name).rename(COMPACT)
def run_all(url):
    need(os.environ.get("WM_PROJECT_VERSION")=="14","load Foundation14 first")
    install_inputs(url)
    summary={}
    for name in ORDER:
        case=COMPACT/name;branch=RESULT_PREFIX+name
        try:
            r=read(case/REPORT)
            if not r.get("solver_completed"):
                need(r["status"]=="PREPARED_COMPACT_NOT_RUN","attempted case preserved; not restarted")
                rc=subprocess.run([sys.executable,"-B",str(HOME/"compact_campaign_200s.py"),"--run",name]).returncode
                r=read(case/REPORT)
                need(r.get("solver_completed"),f"CFD not completed (exit {rc}); preserve logs")
            manifest=complete_manifest(url,branch)
            if manifest is not None:
                need(manifest["solver_log_sha256"]==sha(case/"log.foamMultiRun"),"existing publication differs")
                summary[name]={"status":r["status"],"publication":branch,"already_published":True}
            else:
                with tempfile.TemporaryDirectory(prefix="campaign-result-",dir=HOME) as d:
                    p=Path(d);archive=p/"result.tar.gz"
                    r=archive_results(archive,case)
                    publish(url,branch,archive,{"kind":"scientific_results","case":name,"solver_steps":200000,
                        "final_time_s":200,"solver_log_sha256":sha(case/"log.foamMultiRun"),
                        "report_sha256":sha(case/REPORT),"native_runtime_coverage_complete":r.get("runtime_audit",{}).get("native_runtime_coverage_complete",False),
                        "status":r["status"],"volume_fields_included":False},p/"git",case=case)
                summary[name]={"status":r["status"],"publication":branch}
        except (RuntimeError,OSError,KeyError,ValueError,subprocess.SubprocessError) as e:
            summary[name]={"status":"BLOCKED_OR_FAILED_PRESERVED","error":str(e)}
            print(name,summary[name],flush=True)
        dump(COMPACT/"LAB_CAMPAIGN_PUBLICATION.json",summary)
    print(json.dumps(summary,indent=2),flush=True)
    need(all("publication" in x for x in summary.values()),"some cases incomplete or not uploaded; inspect summary")
def get_results(url):
    dest=HOME/"CAMPAIGN_200S_HOME_RESULTS_01"
    need(COMPACT.is_dir(),"prepared laptop compact inputs required")
    dest.mkdir(exist_ok=True)
    for name in ORDER:
        branch=RESULT_PREFIX+name
        if complete_manifest(url,branch) is None:
            print("NOT PUBLISHED OR INCOMPLETE",name,flush=True);continue
        target=dest/name
        if target.exists():
            print("EXISTING PRESERVED",target,flush=True);continue
        with tempfile.TemporaryDirectory(prefix="home-results-",dir=HOME) as d:
            p=Path(d);archive=p/"results.tar.gz";m=download(url,branch,p/"git",archive)
            need(m["kind"]=="scientific_results" and m["case"]==name,"wrong results")
            stage=p/"unpacked";stage.mkdir();extract(archive,stage)
            case=stage/name
            need(sha(case/REPORT)==m["report_sha256"] and sha(case/"log.foamMultiRun")==m["solver_log_sha256"],"result provenance mismatch")
            r=read(case/REPORT)
            need(r["solver_completed"] and r["final_time_s"]==200,"incomplete result")
            for folder in ("0","constant","system"):shutil.copytree(COMPACT/name/folder,case/folder)
            need(input_hashes(case)==r["input_sha256"],"home mesh/input differs from laboratory result")
            (case/(name+".foam")).touch()
            case.rename(target)
            print("READY FOR ANALYSIS",target,flush=True)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",choices=("push-inputs","run-lab","get-results"))
    ap.add_argument("--repo",type=Path,default=HOME/"MasterProject")
    a=ap.parse_args();url=root_url(a.repo)
    if a.mode=="push-inputs":push_inputs(a.repo,url)
    elif a.mode=="run-lab":run_all(url)
    else:get_results(url)
if __name__=="__main__":main()
