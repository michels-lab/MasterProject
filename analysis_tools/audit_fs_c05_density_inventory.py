#!/usr/bin/env python3
"""FS-C05 native mixture-density inventory diagnostic, same CFD, no rerun.

Foundation 14 compressibleTwoPhaseVoFMixture stores 'rho' (AUTO_WRITE):
    rho = alpha.metal * rho_iron + (1-alpha.metal) * rho_air.
This reads ONLY native saved rho at t=1e-7 and t=2e-7 (t=0 rho
need not exist in the initial case), and integrates mixture mass. For
provisional CONSTANT iron rho=6820 only, residual gas mass is an
algebraic inventory derived from rho - alpha*rho_iron. No conclusion
about flux through atmosphere, pressure-work or true conservation.

Missing both snapshots => unmeasured status, never fabricated zeros.
One missing snapshot or malformed field => error and evidence retained.
"""
from __future__ import annotations

import math
from pathlib import Path
import re

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import FLUID_CELLS,read_mesh,cell_volume_m3
from audit_fs_c05_postrun_fields import discover_saved_times
from stage_fs_c04_initial_alpha import digest

IRON_RHO_KG_M3=6820.0
AFTER_START=(1e-7,2e-7)
RHO_DIMENSIONS=r"\[\s*1\s+-3\s+0\s+0\s+0\s+0\s+0\s*\]"


def read_native_rho(path:Path,n_cells:int)->list[float]:
    require(path.is_file() and not path.is_symlink(),
            "native rho field is not an ordinary file")
    raw=path.read_text(encoding="utf-8",errors="strict")
    require(re.search(r"\bobject\s+rho\s*;",raw),
            "native density field is not object rho")
    require(re.search(r"dimensions\s+"+RHO_DIMENSIONS+r"\s*;",raw),
            "mixture rho must have SI kg/m3 dimensions")
    internal=raw.split("boundaryField",1)[0]
    m=re.search(
        r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*"
        r"\((.*?)\)\s*;",internal,re.S)
    if m:
        require(int(m.group(1))==n_cells,
                "rho cell list does not match fluid mesh count")
        values=[float(v) for v in m.group(2).split()]
        require(len(values)==n_cells,
                "native density scalar list has wrong length")
    else:
        m=re.search(
            r"internalField\s+uniform\s+([+\-0-9.eE]+)\s*;",internal)
        require(m is not None,"unsupported native rho internal field")
        values=[float(m.group(1))]*n_cells
    require(all(math.isfinite(x) and x>0 for x in values),
            "rho must be finite and strictly positive")
    return values


def phase_inventory(vols:list[float],a:list[float],rho:list[float])->dict:
    require(len(vols)==len(a)==len(rho) and len(vols)>0,
            "density inventory has mismatched arrays")
    require(all(math.isfinite(x) and x>0 for x in vols+rho),
            "invalid native positive cell volumes/density")
    require(all(math.isfinite(x) and 0<=x<=1 for x in a),
            "native alpha outside physically bounded phase interval")
    mass_total=sum(v*r for v,r in zip(vols,rho))
    volume_metal=sum(v*x for v,x in zip(vols,a))
    iron_mass=IRON_RHO_KG_M3*volume_metal
    gas_mass=mass_total-iron_mass
    # For ideal gas >=0, allow only tiny ASCII round-off at initial phase.
    require(gas_mass > 0 and mass_total>0 and
            gas_mass<=mass_total,
            "mixture rho cannot be decomposed into positive gas inventory")
    gas_volume=sum(v*(1-x) for v,x in zip(vols,a))
    require(gas_volume>0,"no gas volume available")
    return {
        "mixture_inventory_kg":mass_total,
        "iron_mass_kg_ASSUMING_CONSTANT_IRON_RHO":iron_mass,
        "air_mass_kg_AS_RESIDUAL_OF_MIXTURE_RHO":gas_mass,
        "iron_volume_m3":volume_metal,
        "air_volume_m3":gas_volume,
        "air_mean_density_kg_m3_FROM_RESIDUAL":gas_mass/gas_volume,
        "real_open_boundary_mass_flux_measured":False,
        "mass_conservation_validated":False,
    }


def audit_density_inventory(case:Path)->dict:
    case=case.expanduser().resolve()
    times=discover_saved_times(case)
    paths={
        t:times[t]/"fluid/rho" for t in AFTER_START
    }
    present={t:p.is_file() and not p.is_symlink() for t,p in paths.items()}
    if not any(present.values()):
        return {
            "status":"NATIVE_RHO_NOT_WRITTEN_AT_BOTH_STEPS_NO_MASS_CLOSURE",
            "native_density_inventory_observed":False,
            "open_atmosphere_mass_flux_measured":False,
            "mass_conservation_validated":False,
            "reason":"Foundation14 did not write fluid/rho at 1e-7 or 2e-7; "
                     "do not invent density values.",
        }
    require(all(present.values()),
            "only one native rho snapshot exists; incomplete density inventory")
    mesh=read_mesh(case/"constant/fluid/polyMesh",FLUID_CELLS)
    volumes=[cell_volume_m3(mesh,i) for i in range(FLUID_CELLS)]
    data=[]
    for t in AFTER_START:
        alpha_path=times[t]/"fluid/alpha.metal"
        require(alpha_path.is_file() and not alpha_path.is_symlink(),
                "native alpha missing alongside rho at "+str(t))
        alpha=read_alpha(alpha_path,expected_cells=FLUID_CELLS)
        rho=read_native_rho(paths[t],FLUID_CELLS)
        inventory=phase_inventory(volumes,alpha,rho)
        inventory["time_s"]=t
        inventory["rho_file_sha256"]=digest(paths[t])
        data.append(inventory)
    initial,final=data
    delta=final["mixture_inventory_kg"]-initial["mixture_inventory_kg"]
    return {
        "status":"NATIVE_MIXTURE_RHO_INVENTORY_MEASURED_NO_MASS_CLOSURE",
        "native_density_inventory_observed":True,
        "time_s":list(AFTER_START),
        "measurements":data,
        "native_rho_inventory_change_kg":delta,
        "native_rho_inventory_relative_change":(
            delta/initial["mixture_inventory_kg"]
        ),
        "iron_phase_rho_kg_m3_ASSUMED_CONSTANT":IRON_RHO_KG_M3,
        "rho_mixture_model":"alpha*rho_metal+(1-alpha)*rho_air",
        "physical_mass_conservation_validated":False,
        "open_atmosphere_mass_flux_measured":False,
        "rho_at_time_zero_required":False,
        "disclaimer":"These are measured fluid mixture mass inventories, NOT "
                     "a closed continuity balance across open boundaries.",
    }
