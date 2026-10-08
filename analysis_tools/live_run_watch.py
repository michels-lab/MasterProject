#!/usr/bin/env python3
"""Read-only OpenFOAM foamMultiRun log observer; requires local process to follow."""
import argparse
import re
import time
from pathlib import Path

def last(pattern, text):
    m = list(re.finditer(pattern,text,re.M|re.I))
    return m[-1] if m else None

def scan(text):
    tm = last(r"^Time =\s*([0-9.eE+-]+)",text)
    co = last(r"Courant Number mean:\s*([0-9.eE+-]+)\s+max:\s*([0-9.eE+-]+)",text)
    ct = last(r"time step continuity errors\s*:\s*sum local\s*=\s*([0-9.eE+-]+),\s*global\s*=\s*([0-9.eE+-]+),\s*cumulative\s*=\s*([0-9.eE+-]+)",text)
    pr = last(r"Solving for p_rgh,\s*Initial residual =\s*([0-9.eE+-]+),\s*Final residual =\s*([0-9.eE+-]+)",text)
    fatal = bool(re.search(r"FOAM FATAL|Segmentation fault|Floating point exception|Failed wmake|^Killed$",text,re.I|re.M))
    finished = bool(re.search(r"^End\s*$",text,re.M))
    return {"t":float(tm.group(1)) if tm else None,
        "Co":float(co.group(2)) if co else None,
        "continuity":float(ct.group(3)) if ct else None,
        "p_initial":float(pr.group(1)) if pr else None,
        "p_final":float(pr.group(2)) if pr else None,
        "fatal":fatal,"end":finished}

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--case",type=Path,required=True)
    mode = a.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once",action="store_true")
    mode.add_argument("--follow",action="store_true")
    a.add_argument("--interval",type=float,default=3.0)
    a.add_argument("--report-dt",type=float,default=0.25)
    x = a.parse_args()
    if x.interval <= 0 or x.report_dt <= 0: a.error("intervals must be positive")
    path = x.case / "log.foamMultiRun"
    print("READ-ONLY watcher:",path,flush=True)
    previous_size, last_time = -1, None
    notified = set()
    while True:
        if not path.is_file():
            if x.once:
                print("ERROR: no log; run not evidenced")
                return 2
            time.sleep(x.interval)
            continue
        try:
            src = path.read_text(errors="replace")
        except OSError as err:
            if x.once:
                print("ERROR:",err)
                return 2
            time.sleep(x.interval)
            continue
        if x.follow and previous_size == len(src):
            time.sleep(x.interval)
            continue
        previous_size = len(src)
        v = scan(src)
        now = v["t"]
        if x.once or v["fatal"] or v["end"] or (now is not None and
            (last_time is None or now < last_time or now-last_time >= x.report_dt)):
            print("t=",v["t"]," maxCo=",v["Co"]," continuity cumulative=",v["continuity"],
                " p initial/final=",v["p_initial"],v["p_final"],flush=True)
            last_time = now
        alarms = []
        if v["Co"] is not None and v["Co"] >= 1: alarms.append("maxCo >= 1; screen stability")
        if v["continuity"] is not None and abs(v["continuity"]) > 1e-3:
            alarms.append("large cumulative continuity; check mass and model physics")
        if v["fatal"]: alarms.append("fatal marker present in log")
        for msg in alarms:
            if msg not in notified:
                print("ALERT:",msg,flush=True)
                notified.add(msg)
        if v["end"]:
            print("End seen: still verify exit code, target time, postProcessing and physics.",flush=True)
            return int(v["fatal"])
        if x.once:
            print("No End marker (may be incomplete or log missing final section)",flush=True)
            return int(v["fatal"])
        time.sleep(x.interval)

if __name__ == "__main__":
    raise SystemExit(main())
