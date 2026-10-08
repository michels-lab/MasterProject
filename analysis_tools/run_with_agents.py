#!/usr/bin/env python3
"""Guarded local runner: launches an existing case with read-only run supervision.

Won't run on a case with historical outputs unless explicitly overridden.
Does NOT patch configuration, clean existing results, or synchronize Git.
WARNING: the case's pre-existing ./Allrun may itself regenerate mesh/log outputs;
run only a deliberately prepared case or an authorized copy.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from live_run_watch import scan

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "cases_controlled_buoyancy"

def inspect(path: Path):
    issues=[]
    if not path.is_dir(): issues.append("case directory not found")
    elif not (path/"Allrun").is_file(): issues.append("Allrun missing")
    if path.is_dir():
        for p in path.iterdir():
            if p.is_dir() and p.name not in ("0","constant","system"):
                try:
                    float(p.name)
                    if float(p.name) > 0: issues.append("solved time directory already exists")
                except ValueError:
                    pass
        if (path/"postProcessing").exists(): issues.append("postProcessing already exists")
        if (path/"log.foamMultiRun").exists(): issues.append("solver log already exists")
    return sorted(set(issues))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",required=True,help="Existing case name under cases_controlled_buoyancy")
    ap.add_argument("--dry-run",action="store_true",help="Safety check only; no solver launch")
    ap.add_argument("--allow-existing-output",action="store_true",
                    help="Explicitly authorize invoking existing Allrun despite existing results")
    ap.add_argument("--interval",type=float,default=3.0)
    args=ap.parse_args()
    if args.interval <= 0: ap.error("interval must be positive")
    if args.case in (".","..") or "/" in args.case or "\\" in args.case:
        ap.error("case must be a single known directory name, not a path")
    path=CASE_DIR/args.case
    issues=inspect(path)
    hard=[x for x in issues if x in ("case directory not found","Allrun missing")]
    print("Case:",path,flush=True)
    print("Preflight:", " | ".join(issues) if issues else "CLEAN",flush=True)
    if hard: return 2
    if issues and not args.allow_existing_output:
        print("REFUSED: preserve original results. Use a fresh test case.",flush=True)
        return 3
    if args.dry_run:
        print("DRY RUN: will execute ./Allrun and concurrently inspect log.foamMultiRun.",flush=True)
        return 0
    if not (ROOT/"analysis_tools/live_run_watch.py").is_file():
        print("ERROR: live watcher missing")
        return 2
    print("Starting case's EXISTING Allrun. Does not modify its code.",flush=True)
    started=datetime.now(timezone.utc)
    log=path/"log.foamMultiRun"
    stop=threading.Event()
    samples=[]
    def watch():
        prev=-1
        last_t=None
        notified=set()
        while not stop.wait(args.interval):
            if not log.is_file(): continue
            try: source=log.read_text(errors="replace")
            except OSError: continue
            if len(source)==prev: continue
            prev=len(source)
            state=scan(source)
            if state["t"] is not None and (last_t is None or state["t"]<last_t or state["t"]-last_t>=0.25):
                print("[RUN OBSERVER] t=",state["t"],"maxCo=",state["Co"],
                      "continuity=",state["continuity"],"p_rgh residual=",state["p_initial"],state["p_final"],flush=True)
                last_t=state["t"]
                samples.append(state)
            for key, alarm in (
                ("courant","High maxCo requires stability audit" if state["Co"] is not None and state["Co"] >= 1 else None),
                ("continuity","High cumulative continuity: check mass/physics" if state["continuity"] is not None and abs(state["continuity"])>1e-3 else None),
                ("fatal","Fatal marker in log" if state["fatal"] else None),
            ):
                if alarm and key not in notified:
                    notified.add(key)
                    print("[RUN OBSERVER ALERT]",alarm,flush=True)
    thread=threading.Thread(target=watch,daemon=True)
    thread.start()
    try:
        proc=subprocess.run(["/bin/sh","./Allrun"],cwd=path,check=False)
        code=proc.returncode
    except KeyboardInterrupt:
        print("INTERRUPTED: stopping watcher; check solver process manually.",flush=True)
        return 130
    finally:
        stop.set()
        thread.join(timeout=max(1.0,args.interval+1))
    state=scan(log.read_text(errors="replace")) if log.is_file() else {}
    ended=state.get("end",False)
    fatal=state.get("fatal",False)
    control=(path/"system/controlDict").read_text(errors="replace")
    target=re.search(r"(?m)^\s*endTime\s+([0-9.eE+-]+)\s*;",control)
    objective=float(target.group(1)) if target else None
    last=state.get("t")
    reached=last is not None and objective is not None and last >= objective-1e-7
    status="RUN-SCREEN-PASS" if code==0 and ended and reached and not fatal else "REVIEW-REQUIRED"
    print("RUN OBSERVER",status,"Allrun exit=",code,"End=",ended,
          "last time=",last,"requested=",objective,"fatal=",fatal,flush=True)
    print("Still required: inspect full pressure solves, flux per face, alphaL, energy and postProcessing completeness.",flush=True)
    out=ROOT/"analysis_results/agent_checks"/(args.case+"_runtime_observer.md")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(
        "# Local runtime observer (screening only)\n\n"+
        "- Case: "+args.case+"\n"+
        "- Started UTC: "+started.isoformat()+"\n"+
        "- Status: "+status+"\n"+
        "- Allrun exit code: "+str(code)+"\n"+
        "- End marker: "+str(ended)+"\n"+
        "- Fatal marker: "+str(fatal)+"\n"+
        "- Last logged Time: "+str(last)+" s\n"+
        "- Requested endTime: "+str(objective)+" s\n"+
        "- Observer samples: "+str(len(samples))+"\n"+
        "- Evidence: "+str(log)+"\n"+
        "\nThis is a read-only log screening report, NOT a physics or experimental validation.\n",
        encoding="utf-8")
    print("Run report:",out,flush=True)
    return 0 if status=="RUN-SCREEN-PASS" else 4

if __name__ == "__main__":
    raise SystemExit(main())
