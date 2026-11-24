#!/usr/bin/env python3
"""FS-C02 exploratory gas thermal-state check (READ ONLY; no solver).

Inspect archived p, rho, U, T and alpha.metal to test whether gas-like cells
are heated with strong pressure/velocity excursions. Provisional air ideal
gas comparison is a consistency proxy, NOT a phase energy or mass balance.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re
import sys
from audit_fs_c02_local import (
    EXPECTED_CELLS, digest, read_alpha, read_temperature, require,
)
from inspect_fs_c02_thermal import inspect as validate_thermal_run, snapshots

NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
R_AIR = 8314.462618 / 28.9
NEAR_PURE_AIR = 1e-6

def internal_text(path: Path, name: str) -> str:
    require(path.is_file() and not path.is_symlink(),
            "saved field missing: "+name)
    raw = path.read_text(encoding="utf-8", errors="replace")
    require(re.search(r"\bobject\s+"+re.escape(name)+r"\s*;", raw) is not None,
            "field identity not "+name)
    return raw.split("boundaryField", 1)[0]

def read_scalar(path: Path, name: str) -> list[float]:
    raw = internal_text(path, name)
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",raw,re.S)
    if m:
        require(int(m.group(1)) == EXPECTED_CELLS, "wrong cell count for "+name)
        values = [float(s) for s in m.group(2).split()]
    else:
        m = re.search(r"internalField\s+uniform\s+("+NUMBER+r")\s*;",raw)
        require(m is not None, "unsupported internal scalar format: "+name)
        values = [float(m.group(1))]*EXPECTED_CELLS
    require(len(values)==EXPECTED_CELLS and all(math.isfinite(x) for x in values),
            "nonfinite or incomplete "+name)
    return values

def read_vector_magnitude(path: Path, name: str="U") -> list[float]:
    raw = internal_text(path, name)
    m = re.search(r"internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\((.*?)\)\s*;",raw,re.S)
    if m:
        require(int(m.group(1))==EXPECTED_CELLS, "wrong vector cell count")
        triples = re.findall(r"\(\s*("+NUMBER+r")\s+("+NUMBER+r")\s+("+NUMBER+r")\s*\)", m.group(2))
        require(len(triples)==EXPECTED_CELLS, "unsupported vector format")
        values = [math.sqrt(sum(float(x)**2 for x in triple)) for triple in triples]
    else:
        m = re.search(r"internalField\s+uniform\s+\(\s*("+NUMBER+r")\s+("+NUMBER+r")\s+("+NUMBER+r")\s*\)\s*;", raw)
        require(m is not None, "unsupported vector field format")
        values = [math.sqrt(sum(float(x)**2 for x in m.groups()))]*EXPECTED_CELLS
    require(all(math.isfinite(x) for x in values), "nonfinite U magnitudes")
    return values

def simple_stats(values: list[float]) -> dict:
    if not values:
        return {"count":0, "mean":None, "max":None, "min":None}
    return {"count":len(values), "mean":sum(values)/len(values),
            "min":min(values), "max":max(values)}

def evaluate_cells(alpha: list[float], temps: list[float],
                   pressures: list[float], densities: list[float],
                   speeds: list[float]) -> dict:
    require(all(len(x)==EXPECTED_CELLS for x in
                (alpha, temps, pressures, densities, speeds)),
            "wrong mesh/field dimensions")
    require(all(0<t<1e7 for t in temps),"nonpositive/unphysical T")
    require(all(p>0 for p in pressures),"nonpositive absolute p")
    require(all(d>0 for d in densities),"nonpositive mixture rho")
    require(all(s>=0 for s in speeds),"negative speed")
    gas = [i for i,a in enumerate(alpha) if a<=.01]
    pure = [i for i,a in enumerate(alpha) if a<=NEAR_PURE_AIR]
    hot = [i for i in pure if temps[i]>1000]
    require(bool(pure), "no near-pure-air cells; cannot test ideal gas")
    ratios = [pressures[i]/(densities[i]*R_AIR*temps[i]) for i in pure]
    return {
        "gas_like_cells_alpha_le_0_01":len(gas),
        "near_pure_air_cells_alpha_le_1e_minus_6":len(pure),
        "near_pure_air_T_K":simple_stats([temps[i] for i in pure]),
        "near_pure_air_p_Pa":simple_stats([pressures[i] for i in pure]),
        "near_pure_air_rho_mixture_kg_m3":simple_stats([densities[i] for i in pure]),
        "near_pure_air_speed_m_s":simple_stats([speeds[i] for i in pure]),
        "near_pure_air_hot_gt1000K_cells":len(hot),
        "hot_p_Pa":simple_stats([pressures[i] for i in hot]),
        "hot_speed_m_s":simple_stats([speeds[i] for i in hot]),
        "ideal_gas_p_over_rhoRT_near_pure_air":simple_stats(ratios),
        "ratio_is_only_a_proxy_with_mixture_rho":True,
    }

def run_analysis(root: Path) -> dict:
    root=root.expanduser().resolve()
    # Existing integrity gate validates all the archived inputs and saved
    # alpha/T fields, not just a requested quick snapshot.
    validated=validate_thermal_run(root)
    times=snapshots(root/"FS-C02")
    indices=sorted({0,len(times)//2,len(times)-1})
    outputs=[]
    for i in indices:
        t, folder=times[i]
        alpha=read_alpha(folder/"alpha.metal")
        T=read_temperature(folder/"T")
        p=read_scalar(folder/"p","p")
        rho=read_scalar(folder/"rho","rho")
        speed=read_vector_magnitude(folder/"U")
        outputs.append({
            "time_s":t,
            "p_sha256":digest(folder/"p"),
            "rho_sha256":digest(folder/"rho"),
            "U_sha256":digest(folder/"U"),
            **evaluate_cells(alpha,T,p,rho,speed),
        })
    return {
        "schema":"masterproject-fs-c02-air-gas-proxy-v1",
        "case_id":"FS-C02",
        "status":"GAS_STATE_DESCRIPTIVE_NOT_PHYSICALLY_VALIDATED",
        "source_run":str(root),
        "source_manifest_sha256":validated["source_manifest_sha256"],
        "archived_times_checked":len(times),
        "sampled_times":[r["time_s"] for r in outputs],
        "air_specific_gas_constant_J_kgK":R_AIR,
        "assumption":"rho is mixture rho; ideal-gas ratio useful only if alpha.metal<=1e-6",
        "not_energy_or_phase_mass_balance":True,
        "solidification_or_shrinkage_not_modelled":True,
        "records":outputs
    }

def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        print(json.dumps(run_analysis(args.run),indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C02 GAS STATE BLOCKED: "+str(exc),file=sys.stderr)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
