#!/usr/bin/env python3
"""Produce a bounded, source-SHA-specific *scan-completed* File Steward proof.

A generated proof is NOT a proof of successful GitHub Actions conclusion.
The central collector must verify the exact run via GitHub API.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = "michels-lab/MasterProject"
OUTPUT = "reports/file-governance/AUDIT_PROOF.json"
SUMMARY = "reports/file-governance/SUMMARY.json"

def head_sha(root):
    return subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],
                                   timeout=10,stderr=subprocess.DEVNULL).decode().strip()

def produce(root, env=None, now=None, require_actions=False):
    """Explicitly records what was scanned; prevents claimed run on other HEAD."""
    root=Path(root).resolve()
    env=os.environ if env is None else env
    head=head_sha(root)
    if not SHA.fullmatch(head):
        raise ValueError("Invalid local Git HEAD")
    summary=json.loads((root/SUMMARY).read_text(encoding="utf-8"))
    if summary.get("audit_kind") != "deterministic_full_tracked_tree":
        raise ValueError("Local File Steward summary missing or unsupported")
    fingerprint=summary.get("inventory_fingerprint")
    if not isinstance(fingerprint,str) or not re.fullmatch(r"[a-f0-9]{64}",fingerprint):
        raise ValueError("Source inventory fingerprint invalid")

    valid_actions = (env.get("GITHUB_REPOSITORY")==REPO
                     and env.get("GITHUB_SHA")==head
                     and env.get("GITHUB_REF")=="refs/heads/main"
                     and env.get("GITHUB_EVENT_NAME") in ("push","schedule","workflow_dispatch")
                     and str(env.get("GITHUB_RUN_ID","")).isdigit()
                     and str(env.get("GITHUB_RUN_ATTEMPT","")).isdigit()
                     and int(env.get("GITHUB_RUN_ID","0")) > 0
                     and int(env.get("GITHUB_RUN_ATTEMPT","0")) > 0)
    if require_actions and not valid_actions:
        raise ValueError("Refusing unverifiable Actions provenance; no forged run identifiers")

    utc=now or dt.datetime.now(dt.timezone.utc)
    if utc.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    proof={"schema_version":1,"repository":REPO,"audited_head_sha":head,
           "inventory_fingerprint":fingerprint,
           "scan_stage":"FILE_STEWARD_SCAN_COMPLETED",
           "evidence_state":"ACTIONS_CLAIM_PENDING_EXTERNAL_VERIFICATION" if valid_actions else "UNVERIFIED_LOCAL",
           "recorded_at_utc":utc.astimezone(dt.timezone.utc).isoformat(),
           "workflow_run_id":int(env["GITHUB_RUN_ID"]) if valid_actions else None,
           "workflow_run_attempt":int(env["GITHUB_RUN_ATTEMPT"]) if valid_actions else None}
    return proof

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--repo",default=".")
    cli.add_argument("--require-actions",action="store_true")
    a=cli.parse_args()
    base=Path(a.repo).resolve()
    proof=produce(base,require_actions=a.require_actions)
    dest=base/OUTPUT
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(proof,indent=2)+"\n",encoding="utf-8")
    print("File Steward SHA provenance:",proof["evidence_state"],proof["audited_head_sha"])

if __name__=="__main__": main()
