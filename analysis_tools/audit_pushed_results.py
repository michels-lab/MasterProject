#!/usr/bin/env python3
"""Read-only audit of evidence committed AFTER local OpenFOAM simulation.

No solver calls, reruns, cleanup or changes to scientific case directories.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases_controlled_buoyancy"

def tail(path: Path, limit=131072):
    if not path.is_file():
        return ""
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell()-limit))
        return f.read().decode("utf-8", "replace")

def last_row(path: Path):
    for line in reversed(tail(path).splitlines()):
        if line.lstrip().startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                return [float(x) for x in parts]
            except ValueError:
                continue
    return None

def get_registry():
    path=ROOT/"RUN_CASE_REGISTRY.csv"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig",newline="") as f:
        return {r["case"]:r for r in csv.DictReader(f)}

def git_changed(base):
    if not re.fullmatch(r"[0-9a-f]{40}",base or "") or set(base)=={"0"}:
        return None
    proc=subprocess.run(["git","diff","--name-only",base,"HEAD"], cwd=ROOT,
        text=True,capture_output=True,check=False)
    if proc.returncode:
        return None
    selected=set()
    for path in proc.stdout.splitlines():
        bits=Path(path).parts
        if len(bits)>2 and bits[0]=="cases_controlled_buoyancy":
            selected.add(bits[1])
    return selected

def audit_case(case,reg):
    check, notes=[],[]
    status=reg.get("run_status","UNREGISTERED")
    analysis=reg.get("analysis_status","UNKNOWN")
    control=case/"system/controlDict"
    target=None
    if control.is_file():
        match=re.search(r"(?m)^\s*endTime\s+([0-9.eE+-]+)\s*;",control.read_text(errors="replace"))
        if match:
            target=float(match.group(1))
    probe=case/"postProcessing/metal/temperatureProbe/0/T"
    values=last_row(probe)
    probe_time=values[0] if values else None
    if not values:
        check.append("Temperature probe unavailable in committed files")
    elif target is not None and probe_time < target-1e-5:
        check.append("Temperature probe not at requested endTime")
    log=case/"log.foamMultiRun"
    log_size=log.stat().st_size if log.is_file() else 0
    data=tail(log)
    if log_size==0:
        notes.append("Full foamMultiRun log missing or empty in checkout")
    else:
        if not re.search(r"(?m)^\s*End\s*$",data):
            notes.append("End marker not found near saved log tail")
        if re.search(r"FOAM FATAL|segmentation fault|floating point exception|failed wmake",data,re.I):
            check.append("Fatal/error marker in saved log tail")
    logs=case/"logs"
    expected={
        "Courant": "CourantMax_*",
        "pressure initial": "p_rgh_[0-9]*",
        "pressure final": "p_rghFinalRes_*",
        "continuity": "contCumulative_*",
        "enthalpy": "h_[0-9]*",
        "internal energy": "e_[0-9]*",
    }
    series={}
    for key,glob in expected.items():
        n=len(list(logs.glob(glob))) if logs.is_dir() else 0
        series[key]=n
        if n==0:
            check.append("Missing foamLog "+key+" series")
    post=case/"postProcessing/metal"
    required=("metalTopPhiSum","metalTopEnergyPower","metalMoldEnergyPower",
              "metalMeanLiquidFraction","horizontalProfiles","verticalProfiles")
    present=sorted(d.name for d in post.iterdir() if d.is_dir()) if post.is_dir() else []
    for key in required:
        if key not in present:
            check.append("Missing postProcessing/"+key)
    functions=case/"system/functions"
    has_top_flow=functions.is_file() and bool(re.search(r"(?m)^topFlow\s*$",functions.read_text(errors="replace")))
    if has_top_flow and "topFlow" not in present:
        check.append("topFlow configured but face-wise output not present in Git checkout")
    if "topFlow" in present:
        notes.append("topFlow folder available; face-by-face phi values still need interpretation")
    if status=="PREPARED_NOT_RUN" and (values or log_size):
        check.append("Registry says prepared/not run, but committed output exists: verify provenance")
    if status=="PREPARED_NOT_RUN":
        notes.append("Prepared case: do not invent a run or classify as verified")
    notes.append("Missing Git evidence does not imply the user failed to run locally")
    notes.append("Numerical completion does not establish physical/experimental validity")
    notes.append("energyFlux includes heatFlux and energyAdvectiveFlux, do not add all three")
    notes.append("Net phi can conceal opposite local face fluxes")
    return {"case":case.name,"registry_run_status":status,
            "registry_analysis_status":analysis,
            "evidence_status":"REVIEW" if check else "TRACKED_EVIDENCE_PRESENT",
            "requested_end_s":target,"probe_last_s":probe_time,
            "log_bytes":log_size,"foamLog_series_count":series,
            "postProcessing_groups":present,"alerts":check,"notes":notes}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all",action="store_true")
    ap.add_argument("--changed-base",default="")
    ap.add_argument("--out",type=Path,default=ROOT/"analysis_results/agent_checks/post_push")
    args=ap.parse_args()
    if not CASES.is_dir():
        ap.error("Controlled case directory missing")
    diff=None if args.all else git_changed(args.changed_base)
    reg=get_registry()
    folders=sorted((p for p in CASES.iterdir() if p.is_dir() and
                    re.match(r"^[BC]\d",p.name)),key=lambda p:p.name)
    chosen=[p for p in folders if diff is None or p.name in diff]
    results=[audit_case(p,reg.get(p.name,{})) for p in chosen]
    payload={"generated_utc":datetime.now(timezone.utc).isoformat(),
             "selection":"ALL" if diff is None else "CHANGED_CASES",
             "case_count":len(results),"no_simulation_executed":True,
             "results":results}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"report.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
    lines=["# QuickCup post-push evidence audit","",
           "Scientific data from user-executed laptop runs only. No OpenFOAM simulation launched.","",
           "| Case | Registry status | Tracked evidence | Last probe s | Alerts |",
           "|---|---|---|---:|---:|"]
    for item in results:
        ts=item["probe_last_s"]
        lines.append(f"| {item['case']} | {item['registry_run_status']} | {item['evidence_status']} | {ts if ts is not None else '-'} | {len(item['alerts'])} |")
    if not results:
        lines.append("| No controlled case files changed | - | - | - | - |")
    for item in results:
        lines.extend(["",f"## {item['case']}"])
        lines.extend("- ALERT: "+msg for msg in item["alerts"])
        lines.extend("- NOTE: "+msg for msg in item["notes"])
    lines.extend(["","## Human scientific/documentation follow-up","",
                  "Review CASE_NOTES, CASE_VARIANT, RUN_CASE_REGISTRY, both PROJECT_AUDIT_LOG languages,",
                  "both validation matrices, postprocessing guide and command manuals after new results.",
                  "GitHub Actions does not edit these scientific conclusions automatically.",""])
    (args.out/"report.md").write_text("\n".join(lines),encoding="utf-8")
    print("Post-push review:",len(results),"case(s)")
    for item in results:
        print(item["case"],item["evidence_status"],"alerts=",len(item["alerts"]))
    print("Report:",args.out/"report.md")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
