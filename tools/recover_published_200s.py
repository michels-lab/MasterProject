#!/usr/bin/env python3
"""Recover ONE published scientific archive at a pinned commit. Never runs CFD."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import tempfile

import transfer_campaign_200s as transfer

INDEX = "docs/MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json"
KINDS = {"adaptive_scientific_results", "fixed_lab_scientific_results"}
CASES = set(transfer.RUN_ORDER)
HEX64 = re.compile(r"[0-9a-f]{64}")
HEX40 = re.compile(r"[0-9a-f]{40}")

def need(ok, msg):
    if not ok:
        raise ValueError(msg)

def entries(index):
    return [x for x in index["branches"] if x.get("complete") is True
            and x.get("kind") in KINDS and x.get("case") in CASES
            and HEX40.fullmatch(x.get("sha") or "")]

def validate_manifest(m, e):
    for k in ("case", "kind", "solver_steps", "final_time_s",
              "archive_sha256", "report_sha256", "time_mode"):
        need(m.get(k) == e.get(k), "index mismatch: "+k)
    need(m.get("complete") is True and m.get("native_runtime_coverage_complete") is True
         and m.get("volume_fields_included") is False and m["final_time_s"] == 200,
         "unexpected coverage")
    for k in ("archive_sha256","report_sha256","solver_log_sha256"):
        need(HEX64.fullmatch(m.get(k) or ""), "invalid SHA256 "+k)
    parts=m["parts"]
    need(bool(parts), "empty archive")
    for i,p in enumerate(parts):
        need(p["name"] == f"archive.tar.gz.part{i:06d}" and
             type(p["bytes"]) is int and 0 < p["bytes"] <= transfer.CHUNK and
             HEX64.fullmatch(p["sha256"]), "invalid part metadata")
    need(sum(p["bytes"] for p in parts) == m["archive_bytes"], "archive size mismatch")

def safe_members(archive, case, limit):
    seen=set()
    total=0
    with tarfile.open(archive,"r:gz") as t:
        for member in t:
            p=PurePosixPath(member.name)
            need(not p.is_absolute() and ".." not in p.parts and
                 p.parts and p.parts[0]==case and
                 (member.isdir() or member.isfile()), "unsafe member "+member.name)
            need(p not in seen, "duplicate archive member "+member.name)
            seen.add(p)
            if member.isfile():
                total+=member.size
                need(total<=limit, "unpacked byte limit exceeded")
    return total

def recover(repo, e, out, limit):
    raw=out.expanduser().absolute()
    out=raw.resolve()
    repo=repo.resolve(strict=True)
    need(not raw.is_symlink() and not out.exists() and
         out!=repo and repo not in out.parents and out not in repo.parents,
         "choose a new destination outside the repository")
    need(out.parent.is_dir(), "destination parent must exist")
    url=transfer.root_url(repo)
    with tempfile.TemporaryDirectory(prefix=".campaign_recovery_",dir=out.parent) as tmp:
        work=Path(tmp)
        checkout=work/"git"
        checkout.mkdir()
        transfer.git("init","-q",cwd=checkout)
        transfer.git("remote","add","origin",url,cwd=checkout)
        transfer.git("fetch","--depth=1","--filter=blob:none","origin",e["sha"],cwd=checkout)
        need(transfer.git("rev-parse","FETCH_HEAD",cwd=checkout,capture=True)==e["sha"],
             "pinned revision mismatch")
        raw_manifest=subprocess.check_output(
            ["git","show","FETCH_HEAD:MANIFEST.json"],cwd=checkout)
        blob=hashlib.sha1(b"blob "+str(len(raw_manifest)).encode()+b"\0"+raw_manifest).hexdigest()
        need(blob==e["manifest_blob_sha"], "manifest blob differs")
        m=json.loads(raw_manifest)
        validate_manifest(m,e)
        need(shutil.disk_usage(out.parent).free > 3*m["archive_bytes"]+transfer.RESERVE,
             "insufficient initial disk reserve")
        archive=work/"result.tar.gz"
        with archive.open("xb") as target:
            for p in m["parts"]:
                chunk=work/"part"
                with chunk.open("xb") as stream:
                    subprocess.run(["git","show","FETCH_HEAD:"+p["name"]],
                                   cwd=checkout,stdout=stream,check=True)
                need(chunk.stat().st_size==p["bytes"] and transfer.sha(chunk)==p["sha256"],
                     "part SHA mismatch: "+p["name"])
                with chunk.open("rb") as f:
                    shutil.copyfileobj(f,target)
                chunk.unlink()
        need(archive.stat().st_size==m["archive_bytes"] and transfer.sha(archive)==m["archive_sha256"],
             "archive SHA mismatch")
        total=safe_members(archive,m["case"],limit)
        need(shutil.disk_usage(out.parent).free>total+transfer.RESERVE,
             "insufficient extraction reserve")
        stage=work/"extracted"
        stage.mkdir()
        transfer.extract(archive,stage)
        case=stage/m["case"]
        need(transfer.sha(case/transfer.REPORT)==m["report_sha256"] and
             transfer.sha(case/"log.foamMultiRun")==m["solver_log_sha256"], "report/log SHA mismatch")
        report=transfer.read(case/transfer.REPORT)
        need(report.get("solver_completed") is True and report.get("solver_steps")==m["solver_steps"]
             and report.get("final_time_s")==200 and
             report["runtime_audit"]["native_runtime_coverage_complete"] is True and
             not report["runtime_audit"]["errors"], "report coverage mismatch")
        (stage/"VERIFIED_RECOVERY.json").write_text(json.dumps({
            "source_commit":e["sha"],"manifest_blob":blob,"manifest":m,
            "unpacked_file_bytes":total,"archive_parts_sha256_verified":True,
            "report_and_log_sha256_verified":True,"physical_validation":False,
            "volume_fields_included":False,"solver_rerun":False},indent=2)+"\n")
        need(not out.exists(), "destination appeared during recovery")
        stage.rename(out)
    print("VERIFIED_ARCHIVE_RECOVERED",out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path,default=transfer.HOME/"MasterProject")
    p.add_argument("--commit")
    p.add_argument("--out",type=Path)
    p.add_argument("--max-unpacked-gib",type=int,default=20)
    args=p.parse_args()
    index=transfer.read(args.repo/INDEX)
    choices=entries(index)
    if args.commit is None:
        for e in choices:
            print(e["sha"],e["case"],e["time_mode"],e.get("mpi_ranks"),e["branch"])
        return
    match=[e for e in choices if e["sha"]==args.commit]
    need(len(match)==1 and args.out is not None and args.max_unpacked_gib>0,
         "select one listed commit and new --out")
    recover(args.repo,match[0],args.out,args.max_unpacked_gib*1024**3)

if __name__=="__main__":
    main()
