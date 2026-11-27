#!/usr/bin/env python3
"""Read existing FS-C08 batch logs and saved field inventories; never run CFD."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from fs_c08_momentum_diagnostics import parse
from fs_c08_transient_ledger import extract
from run_fs_c08_real_cfd import comparison_ready_times, numeric_time_dirs

SPLIT="FS_C08_MOMENTUM_FORCE_SPLIT"
CONSISTENCY="FS_C08_MOMENTUM_CONSISTENCY"
FRESH="FS_C08_FRESH_MOMENTUM_DEFECT"
EXTREME="FS_C08_ACCEPTED_EXTREME_CELL"

def require(ok,message):
    if not ok:
        raise ValueError(message)

def tick(t,dt):
    if not math.isfinite(t) or t<=0:
        return None
    k=round(t/dt)
    return k if k>0 and abs(t-k*dt)<=max(1e-14,dt*1e-6) else None

def unique_ticks(records,dt):
    result={}
    duplicates=set()
    for row in records:
        k=tick(row["time_s"],dt)
        if k is None:
            continue
        if k in result or k in duplicates:
            result.pop(k,None)
            duplicates.add(k)
        else:
            result[k]=row
    return result

def compare_variant(log,snapshots,dt,steps,common_dt,strict):
    """Keep only native accepted, complete, saved states with consistent diagnostics."""
    require(math.isfinite(dt) and dt>0 and math.isfinite(common_dt) and common_dt>0
            and type(steps) is int and steps>0,"invalid fixed-step controls")
    ready=set(comparison_ready_times(log,snapshots,dt,strict))
    eligible=unique_ticks([{"time_s":t} for t in ready],dt)
    ledger,ledger_issues=extract(log)
    states=unique_ticks(ledger,dt)
    parsed=parse(log)
    records=parsed["diagnostic_records"]
    diagnostics={}
    for marker,reason in ((SPLIT,""),(CONSISTENCY,""),(FRESH,""),
                          (EXTREME,"maximumSpeed"),(EXTREME,"maximumGasDominatedHeating")):
        diagnostics[(marker,reason)]=unique_ticks(
            [r for r in records if r["marker"]==marker and r["reason"]==reason],dt)
    results={}
    excluded={}
    for k in sorted(eligible):
        if k>steps:
            continue
        t=eligible[k]["time_s"]
        common=tick(t,common_dt)
        if common is None:
            continue
        state=states.get(k)
        split=diagnostics[(SPLIT,"")].get(k)
        consistency=diagnostics[(CONSISTENCY,"")].get(k)
        extreme=diagnostics[(EXTREME,"maximumSpeed")].get(k)
        if not state or not state["all_native_ledgers_present"]:
            excluded[str(k)]="missing complete native ledger"
            continue
        if parsed["issues"] or not split or not consistency or not extreme:
            excluded[str(k)]="ambiguous parser output or missing mandatory momentum record"
            continue
        if split["cell"] is None or split["cell"]!=extreme["cell"]:
            excluded[str(k)]="maximum-speed cell identity differs within variant"
            continue
        speeds=[state["maxU_m_s"],split["speed_m_s"],extreme["speed_m_s"]]
        if min(speeds)<0 or max(speeds)-min(speeds)>max(1e-10,1e-6*max(speeds)):
            excluded[str(k)]="maximum-speed diagnostics disagree"
            continue
        results[common]={"native_step":k,"native_time_s":t,
            "state":state,"maximum_speed_split":split,"maximum_speed_cell":extreme,
            "consistency_domain_maxima":consistency,
            "fresh_matrix_defect_domain_maxima":diagnostics[(FRESH,"")].get(k),
            "maximum_gas_heating_cell":diagnostics[(EXTREME,"maximumGasDominatedHeating")].get(k)}
    return results,{"eligible_saved_steps":len(eligible),"joined_steps":len(results),
                    "excluded":excluded,"ledger_issues":ledger_issues,
                    "momentum_parser_issues":parsed["issues"],
                    "startup_records_without_physical_time":parsed["startup_records"]}

def compare_batch(batch):
    rows=batch["variants"]
    require(bool(rows) and len({r["variant"] for r in rows})==len(rows),"invalid variant inventory")
    dt=batch["comparison_tick_s"]
    require(math.isfinite(dt) and dt>0,"invalid comparison tick")
    histories={}
    provenance={}
    for row in rows:
        name=row["variant"]
        try:
            log_path=Path(row["diagnostics"])/"foamMultiRun.log"
            case=Path(row["case"])
            raw=log_path.read_bytes()
            strict=row.get("energy_linear_tolerance")
            require(isinstance(strict,(int,float)) and math.isfinite(strict) and strict>=0,
                    "missing strict energy contract")
            hist,meta=compare_variant(raw.decode("utf-8"),numeric_time_dirs(case),
                row["fixed_dt_s"],row["scheduled_steps"],dt,strict>0)
            histories[name]=hist
            provenance[name]={"log":str(log_path.resolve()),"log_sha256":hashlib.sha256(raw).hexdigest(),
                "case":str(case.resolve()),"strict_energy":strict>0,**meta}
        except (OSError,ValueError,TypeError,KeyError) as exc:
            histories[name]={}
            provenance[name]={"error":str(exc),"joined_steps":0}
    shared=set.intersection(*(set(x) for x in histories.values()))
    common=[]
    for k in sorted(shared):
        variants={n:h[k] for n,h in histories.items()}
        centers=[r["maximum_speed_cell"]["center_m"] for r in variants.values()]
        coincident=all(math.dist(centers[0],v)<=1e-9 for v in centers[1:])
        common.append({"time_s":k*dt,"comparison_tick":k,
            "maximum_speed_centers_coincident_within_1nm":coincident,"variants":variants})
    return {"status":"COMMON_DIAGNOSTICS_AVAILABLE" if common else "NO_COMMON_ELIGIBLE_DIAGNOSTICS",
        "comparison_tick_s":dt,"variant_provenance":provenance,"common_times":common,
        "physical_shrinkage_validated":False,"global_energy_verified":False,
        "temporal_independence_demonstrated":False,
        "scope":"All variants, no interpolation; same cell check within variant. Coincident centers do not prove identical mesh topology. Domain maxima may occur at different locations. No force or acceleration validation; field presence is not field-content verification."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--batch",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    source=a.batch.resolve(strict=True)
    raw=source.read_bytes()
    batch=json.loads(raw)
    out=a.out.expanduser().absolute()
    resolved=out.resolve()
    protected=[source.parent]
    for row in batch["variants"]:
        for key in ("case","diagnostics"):
            if row.get(key):
                protected.append(Path(row[key]).resolve())
    require(not out.is_symlink() and not resolved.exists() and all(
        resolved!=x and x not in resolved.parents and resolved not in x.parents for x in protected),
        "output must be new and independent of all source directories")
    result=compare_batch(batch)
    result["batch_summary_sha256"]=hashlib.sha256(raw).hexdigest()
    resolved.mkdir(parents=True,exist_ok=False)
    (resolved/"FS_C08_COMMON_MOMENTUM.json").write_text(
        json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print(result["status"],len(result["common_times"]),resolved)
    return 0 if result["common_times"] else 2

if __name__=="__main__":
    raise SystemExit(main())
