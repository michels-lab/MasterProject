#!/usr/bin/env python3
"""Read-only C14-3DA startup forensics. No CFD, no OpenFOAM writes."""
import argparse
import hashlib
import json
import math
import re
from collections import deque
from pathlib import Path

NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
TIME = re.compile(r"^\s*Time\s*=\s*("+NUM+r")\s*s?\s*$")
DT = re.compile(r"\bdeltaT\s*=\s*("+NUM+r")")
CO = re.compile(r"Courant Number.*?\bmax\s*[:=]\s*("+NUM+r")", re.I)
REGION = re.compile(r"^\s*(?:Solving for (?:fluid|solid) region|Region:)\s*(\w+)", re.I)
RES = re.compile(r"Solving for ([^,]+),\s*Initial residual\s*=\s*("+NUM+r"),\s*Final residual\s*=\s*("+NUM+r"),\s*No Iterations\s+(\d+)")
TEMP = re.compile(r"Negative initial temperature T0\s*[:=]?\s*("+NUM+r")",re.I)
FATAL = re.compile(r"FOAM FATAL(?: IO)? ERROR|Negative initial temperature T0|floating point exception|MPI_ABORT",re.I)
INPUTS = ("system/controlDict","system/fvSolution","system/metal/fvSolution",
          "system/mold/fvSolution","system/metal/fvSchemes","system/mold/fvSchemes",
          "constant/metal/fvModels","constant/metal/materials/castIron",
          "constant/mold/materials/silica","system/decomposeParDict")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def audit(path, horizon=0.8):
    before=path.stat()
    steps=[]
    events=[]
    context=deque(maxlen=16)
    current=None
    pending_dt=None
    pending_co=None
    region="unknown"
    end=False
    time_last=None
    with path.open(errors="replace") as f:
        for n,line in enumerate(f,1):
            line=line.rstrip()
            # Ignore sigFpe startup notice; preserve actual fatal lines.
            m=DT.search(line)
            if m: pending_dt=float(m.group(1))
            m=CO.search(line)
            if m: pending_co=float(m.group(1))
            m=TIME.match(line)
            if m:
                t=float(m.group(1))
                time_last=t
                current={"time_s":t,"line":n,"deltaT_s":pending_dt,
                         "maxCo_before_step":pending_co,"solves":{}}
                region="unknown"
                pending_dt=pending_co=None
                if t<=horizon: steps.append(current)
            m=REGION.search(line)
            if m: region=m.group(1)
            m=RES.search(line)
            if m and current is not None and current["time_s"]<=horizon:
                key=region+"/"+m.group(1).strip()
                i,v,it=float(m.group(2)),float(m.group(3)),int(m.group(4))
                x=current["solves"].setdefault(key,{"count":0,"max_initial":0.,
                  "max_final":0.,"max_iterations":0})
                x["count"]+=1
                x["max_initial"]=max(x["max_initial"],i)
                x["max_final"]=max(x["max_final"],v)
                x["max_iterations"]=max(x["max_iterations"],it)
            if line.strip()=="End": end=True
            if FATAL.search(line) and "Enabling floating point exception trapping" not in line:
                if len(events)<30:
                    mt=TEMP.search(line)
                    events.append({"line":n,"time_s":time_last,"message":line[:500],
                       "negative_T0_K":float(mt.group(1)) if mt else None,
                       "preceding_lines":list(context)})
            context.append(line[:500])
    digest=sha(path)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise RuntimeError("Log changed during audit; rerun only after solver stops: "+str(path))
    if not steps:
        raise ValueError("No native Time entries within startup window: "+str(path))
    hashes={p:sha(path.parent/p) for p in INPUTS if (path.parent/p).is_file()}
    monotonic=all(b["time_s"]>a["time_s"] for a,b in zip(steps,steps[1:]))
    return {"path":str(path),"log_sha256":digest,"input_sha256":hashes,
            "last_logged_time_s":time_last,"end_marker":end,"startup_monotonic":monotonic,
            "fatal_events":events,"startup_steps":steps}

def compare(a,b):
    shared=sorted(set(a["input_sha256"]) & set(b["input_sha256"]))
    return {"same_inputs":[p for p in shared if a["input_sha256"][p]==b["input_sha256"][p]],
            "different_inputs":[p for p in shared if a["input_sha256"][p]!=b["input_sha256"][p]],
            "missing_inputs":sorted(set(INPUTS)-set(shared)),
            "note":"Compare physical time, not step index; residuals do not prove conservation."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path.home()/"OpenFOAM")
    p.add_argument("--adaptive",type=Path,action="append",default=[])
    p.add_argument("--fixed",type=Path,action="append",default=[])
    p.add_argument("--horizon",type=float,default=0.8)
    args=p.parse_args()
    if not math.isfinite(args.horizon) or args.horizon<=0: p.error("positive finite horizon required")
    paths=args.adaptive or sorted((args.root/"CAMPAIGN_200S_ADAPTIVE_MPI_01").glob("*/C14-3DA-200s/log.foamMultiRun"))
    paths=sorted(set(q.resolve() for q in paths))
    if not paths: p.error("no adaptive logs found; supply --adaptive PATH")
    runs=[audit(q,args.horizon) for q in paths]
    fixed=[audit(q.resolve(),args.horizon) for q in args.fixed]
    result={"scope":"read-only log evidence; no field extrema, no causal or physical validation",
        "horizon_s":args.horizon,"adaptive":runs,"fixed":fixed,
        "comparisons":[{"adaptive":a["path"],"fixed":b["path"],**compare(a,b)}
                       for a in runs for b in fixed]}
    print(json.dumps(result,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
