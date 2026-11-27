#!/usr/bin/env python3
"""Audit native FS-C08 fluid-side energy and patch budgets, not global CHT."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from fs_c08_transient_ledger import extract

PATCH="FS_C08_REAL_CFD_PATCH_BUDGET"
BUDGET="FS_C08_REAL_CFD_MASS_BUDGET"
PASS="FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED"
ENERGY="FS_C08_FINAL_COUPLED_ENERGY_AUDIT_PASS"
P_FIELDS=("liquidMetalIn_kg_s","liquidMetalOut_kg_s","signedGasOut_kg_s",
          "signedCHTHeatOut_W","energySolverAdvectedOut_W")
B_FIELDS=("deltaInternalEnergy_J","nativeEnergySolveAdvectionOut_W",
          "nativeEnergySolveConductionOut_W","nativeMechanicalWork_W",
          "mushyDarcyDissipation_W","totalInternalEnergyEquationBalance_J",
          "pressureCorrectionEnergyGap_J","boundaryMetalOut_kg_s","gasBoundaryOut_kg_s")

def number(s):
    x=float(s)
    if not math.isfinite(x):
        raise ValueError("nonfinite number")
    return x

def audit(log,expected_patches,strict=True):
    """Expected patches must come from the actual fluid mesh, not guessed roles."""
    if not expected_patches or len(set(expected_patches))!=len(expected_patches):
        raise ValueError("explicit unique fluid patch inventory required")
    rows,ledger_issues=extract(log)
    states={r["time_s"]:r for r in rows}
    records={}
    issues=[]
    ambiguous=False
    for line_no,line in enumerate(log.splitlines(),1):
        marker=next((m for m in (PATCH,BUDGET,PASS,ENERGY) if m in line),None)
        if not marker:
            continue
        t=None
        try:
            pairs=re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)=([^\s]+)",line)
            fields=dict(pairs)
            if len(pairs)!=len(fields):
                raise ValueError("duplicate key")
            t=number(fields["time_s"])
            if t<=0:
                raise ValueError("non-positive time")
            rec=records.setdefault(t,{"patches":{},"markers":set(),"invalid":False})
            if marker==PATCH:
                patch=fields["patch"]
                if patch in rec["patches"]:
                    raise ValueError("duplicate patch")
                values={k:number(fields[k]) for k in P_FIELDS}
                if min(values["liquidMetalIn_kg_s"],values["liquidMetalOut_kg_s"])<0:
                    raise ValueError("negative gross metal flow")
                rec["patches"][patch]=values
            else:
                if marker in rec["markers"]:
                    raise ValueError("duplicate marker")
                rec["markers"].add(marker)
                if marker==BUDGET:
                    rec["budget"]={k:number(fields[k]) for k in B_FIELDS}
        except (KeyError,ValueError) as exc:
            issues.append(f"line {line_no}: {exc}")
            if t is not None and t>0:
                records.setdefault(t,{"patches":{},"markers":set(),"invalid":False})["invalid"]=True
            else:
                ambiguous=True
    results=[]
    excluded={}
    totals={p:{k:0.0 for k in P_FIELDS} for p in expected_patches}
    cumulative=0.0
    contiguous=True
    prefix_end=0.0
    for t in sorted(set(states)|set(records)):
        state=states.get(t)
        rec=records.get(t)
        reason=None
        if ambiguous:
            reason="unattributable native marker"
        elif not state or not state["all_native_ledgers_present"] or not rec or rec["invalid"]:
            reason="incomplete or ambiguous state"
        elif not {BUDGET,PASS}.issubset(rec["markers"]) or (strict and ENERGY not in rec["markers"]):
            reason="missing acceptance marker"
        elif set(rec["patches"])!=set(expected_patches):
            reason="patch inventory mismatch"
        if reason:
            excluded[str(t)]=reason
            contiguous=False
            continue
        dt=state["dt_s"]
        b=rec["budget"]
        p=rec["patches"]
        sums={k:math.fsum(v[k] for v in p.values()) for k in P_FIELDS}
        # Native sign convention: outward from fluid. Mechanical work is
        # included with the sign used by the actual fluid energy equation.
        reconstructed=b["deltaInternalEnergy_J"]+dt*math.fsum(
            b[k] for k in ("nativeEnergySolveAdvectionOut_W","nativeEnergySolveConductionOut_W","nativeMechanicalWork_W"))
        result={"time_s":t,"dt_s":dt,"patches":p,"native_budget":b,
                "patch_sum_minus_native_conduction_W":sums["signedCHTHeatOut_W"]-b["nativeEnergySolveConductionOut_W"],
                "patch_sum_minus_native_advection_W":sums["energySolverAdvectedOut_W"]-b["nativeEnergySolveAdvectionOut_W"],
                "patch_sum_minus_native_gas_kg_s":sums["signedGasOut_kg_s"]-b["gasBoundaryOut_kg_s"],
                "patch_sum_minus_native_net_metal_kg_s":sums["liquidMetalOut_kg_s"]-sums["liquidMetalIn_kg_s"]-b["boundaryMetalOut_kg_s"],
                "reconstructed_printed_fluid_balance_J":reconstructed,
                "reconstruction_minus_printed_balance_J":reconstructed-b["totalInternalEnergyEquationBalance_J"]}
        results.append(result)
        if contiguous and abs((t-prefix_end)-dt)<=max(1e-14,1e-6*dt):
            for patch in expected_patches:
                for k in P_FIELDS:
                    totals[patch][k]+=dt*p[patch][k]
            cumulative+=b["totalInternalEnergyEquationBalance_J"]
            prefix_end=t
        else:
            contiguous=False
    return {"status":"FLUID_DIAGNOSTICS_AVAILABLE" if results else "NO_ELIGIBLE_FLUID_DIAGNOSTICS",
            "expected_fluid_patches":list(expected_patches),"strict_energy_marker_required":strict,
            "eligible_records":results,"excluded":excluded,"parser_issues":issues,"ledger_issues":ledger_issues,
            "contiguous_prefix_end_s":prefix_end,"prefix_reaches_last_observed_time":bool(results) and contiguous,
            "prefix_patch_integrals":({p:{"liquidMetalIn_kg":v["liquidMetalIn_kg_s"],
                "liquidMetalOut_kg":v["liquidMetalOut_kg_s"],"signedGasOut_kg":v["signedGasOut_kg_s"],
                "signedConductionOut_J":v["signedCHTHeatOut_W"],"advectedOut_J":v["energySolverAdvectedOut_W"]}
                for p,v in totals.items()} if prefix_end>0 else None),
            "prefix_sum_printed_fluid_balance_J":cumulative if prefix_end>0 else None,
            "global_CHT_energy_verified":False,"physical_shrinkage_validated":False,
            "missing_global_terms":["mold-side interface heat flux","mold energy inventory change",
                "mold external boundary energy flux","mold effective source terms and time discretization"],
            "scope":"Native dt-weighted printed fluid rates; no interpolation or gap bridging. Not independently verified saved fields or a discrete global energy certificate. Darcy dissipation not added a second time."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("log",type=Path)
    p.add_argument("--patch",action="append",required=True,help="Actual fluid mesh patch name; repeat for all")
    p.add_argument("--legacy-no-strict-energy",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    source=a.log.resolve(strict=True)
    out=a.out.expanduser().absolute()
    resolved=out.resolve()
    if out.is_symlink() or resolved.exists() or source.parent==resolved or source.parent in resolved.parents or resolved in source.parents:
        raise ValueError("output must be new and independent of log directory")
    raw=source.read_bytes()
    report=audit(raw.decode("utf-8"),a.patch,not a.legacy_no_strict_energy)
    report["source_log_sha256"]=hashlib.sha256(raw).hexdigest()
    resolved.mkdir(parents=True,exist_ok=False)
    (resolved/"FS_C08_FLUID_ENERGY_PATCH_AUDIT.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(report["status"],len(report["eligible_records"]),resolved)
    return 0 if report["eligible_records"] else 2

if __name__=="__main__":
    raise SystemExit(main())
