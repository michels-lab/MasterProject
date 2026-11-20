#!/usr/bin/env python3
"""FS-C05: audit ALREADY SAVED real Granada fields/Q; NEVER re-run CFD.

The sand subdomain uses constant rho/Cv, no sources, adiabatic supports
and Euler ddt: delta(rho*Cv*V*T) = Q_mold(tn)*delta_t.
Compare at t1 and t2 against the actual wallHeatFlux tables, check
previous successful Granada JSON, solver log/hash, source provenance,
snapshots alpha/T, and rho inventory. Write only into a NEW sibling
diagnostics directory. This is NOT a global energy/mass balance.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import re
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c05_postrun_fields import measure_saved_fields
from audit_fs_c05_density_inventory import audit_density_inventory
from run_fs_c05_native_smoke import preflight, validate_run_log
from run_fs_c05_wall_heat_flux import read_wall_q, compare_power
from stage_fs_c04_initial_alpha import digest

PREFIX="FS_C05_WALL_Q_PROBE_"
EULER_DT=1e-7
SAND_WARN_REL=0.01
SAND_ADIABATIC=("moldBottom","moldRecessWall","moldRecessRoof")


def sand_model(case:Path)->dict:
    physics=case/"constant/mold/physicalProperties"
    schemes=case/"system/mold/fvSchemes"
    initial=case/"0/mold/T"
    model=case/"constant/mold/fvModels"
    for path in (physics,schemes,initial,model):
        require(path.is_file() and not path.is_symlink(),
                "missing native sand model input: "+str(path))
    txt=physics.read_text()
    require(re.search(r"\bthermoType\s+constSolidThermo\s*;",txt),
            "solid energy closure assumes constant Cv")
    props={}
    for name in ("rho","Cv"):
        matches=re.findall(
            rf"\b{name}\s*\{{\s*type\s+uniform\s*;\s*value\s+([+\-0-9.eE]+)\s*;\s*\}}",
            txt)
        require(len(matches)==1,"missing uniform sand "+name)
        props[name]=float(matches[0])
        require(math.isfinite(props[name]) and props[name]>0,
                "nonphysical sand "+name)
    require(props=={"rho":1500.,"Cv":700.},
            "sand properties differ from approved FS-C05 screening")
    require(re.search(r"\bddtSchemes\s*\{[^}]*\bdefault\s+Euler\s*;",
                      schemes.read_text(),re.S),
            "sand time discretization is no longer Euler")
    boundary=initial.read_text()
    for patch in SAND_ADIABATIC:
        m=re.search(rf"\b{patch}\s*\{{([^}}]*)\}}",boundary,re.S)
        require(m is not None
                and re.search(r"\btype\s+zeroGradient\s*;",m.group(1)),
                "nonadiabatic mold boundary not accounted for: "+patch)
    require(re.search(r"\bmold_to_fluid\s*\{[^}]*\btype\s+coupledTemperature\s*;",
                      boundary,re.S),
            "mold wall coupling missing")
    require(re.search(r"\bobject\s+fvModels\s*;",model.read_text())
            and "heatSource" not in model.read_text(),
            "unaccounted solid heat source")
    return {
        "rho_kg_m3":props["rho"],"Cv_J_kgK":props["Cv"],
        "Euler_dt_expected_s":EULER_DT,
        "other_sand_patches_adiabatic":list(SAND_ADIABATIC),
        "constant_property_screening_ONLY":True,
        "source_digests":{
            str(p.relative_to(case)):digest(p)
            for p in (physics,schemes,initial,model)
        },
    }


def solid_energy_steps(snapshots:list[dict],
                       wall:list[dict],rho:float,Cv:float)->dict:
    require(len(snapshots)==3 and len(wall)==2,
            "sand requires three T snapshots and two Q snapshots")
    require([s["time_s"] for s in snapshots]==[0.,1e-7,2e-7]
            and [s["time_s"] for s in wall]==[1e-7,2e-7],
            "invalid chronology of native solver snapshots")
    require(math.isfinite(rho*Cv) and rho>0 and Cv>0,
            "invalid solid density or Cv")
    steps=[]
    for n in (1,2):
        t0,t1=snapshots[n-1],snapshots[n]
        a,b=t0["mold_region_volume_m3"],t1["mold_region_volume_m3"]
        require(a>0 and math.isfinite(a)
                and math.isclose(a,b,rel_tol=1e-12,abs_tol=0),
                "solid volumes do not match")
        old,new=t0["mold_region_volume_weighted_T_K"],t1["mold_region_volume_weighted_T_K"]
        q=wall[n-1]["Q_mold_wall_W"]
        require(all(math.isfinite(v) for v in (old,new,q))
                and old>0 and new>0,
                "nonfinite native T or Q data")
        dt=t1["time_s"]-t0["time_s"]
        require(abs(dt-EULER_DT)<1e-13,
                "wrong Euler step length")
        C=rho*Cv*a
        internal=C*(new-old)
        incoming=q*dt
        residual=internal-incoming
        relative=abs(residual)/max(abs(internal),abs(incoming),1e-15)
        steps.append({
            "time_s":t1["time_s"],
            "sand_heat_capacity_J_K":C,
            "delta_internal_energy_J":internal,
            "incoming_wall_Q_times_dt_J":incoming,
            "energy_residual_J":residual,
            "relative_discrete_error":relative,
            "under_1pct_DIAGNOSTIC":relative<SAND_WARN_REL,
        })
    e=sum(s["delta_internal_energy_J"] for s in steps)
    q=sum(s["incoming_wall_Q_times_dt_J"] for s in steps)
    return {
        "status":(
            "SAND_EULER_ENERGY_CLOSES_WITHIN_1PCT_DIAGNOSTIC"
            if all(s["under_1pct_DIAGNOSTIC"] for s in steps)
            else "SAND_EULER_ENERGY_RESIDUAL_WARNING"),
        "steps":steps,
        "t0_to_t2_delta_internal_energy_J":e,
        "t0_to_t2_incoming_wall_heat_J":q,
        "t0_to_t2_residual_J":e-q,
        "t0_to_t2_relative_discrepancy":
            abs(e-q)/max(abs(e),abs(q),1e-15),
        "local_sand_equation_check_only":True,
        "global_energy_balance_validated":False,
        "experimentally_validated":False,
    }


def verify_native(case:Path)->dict:
    require(case.is_dir() and not case.is_symlink()
            and case.name.startswith(PREFIX),
            "not the saved FS-C05 Granada CFD case")
    a_file=case/"FS_C05_GRANADA_REPORT.json"
    b_file=case/"FS_C05_WALL_Q_REPORT.json"
    require(a_file.is_file() and b_file.is_file(),
            "missing accepted Granada and heat-flux reports")
    a,b=json.loads(a_file.read_text()),json.loads(b_file.read_text())
    require(a.get("status") in (
        "FS_C05_GRANADA_INTEGRATED_MEASUREMENTS_WITH_WARNINGS",
        "FS_C05_GRANADA_INTEGRATED_MEASUREMENTS_COMPLETED")
        and a.get("case")==str(case) and a.get("actual_native_CFD_completed") is True,
        "original CFD Granada was not accepted")
    require(b.get("status")=="TWO_STEP_FLUID_MOLD_WALL_Q_MEASURED_NO_ENERGY_VALIDATION"
            and b.get("output")==str(case)
            and b.get("native_solver_executed") is True
            and b.get("wall_heat_flux_measured") is True,
            "no accepted two-wall native Q measurement")
    old=Path(b.get("source",{}).get("source_case",""))
    require(preflight(old)==b["source"],"source solver inputs not verified")
    log=case/"log.FS_C05_wall_q_foamMultiRun"
    require(log.is_file() and not log.is_symlink()
            and digest(log)==b.get("native_log_sha256"),
            "native solver log not genuine")
    raw=log.read_text(errors="replace")
    require("EXIT: 0" in raw and validate_run_log(raw)["completed_time_steps"]>=2,
            "native solver did not complete 2 steps")
    fluid=read_wall_q(case,"fluid")
    mold=read_wall_q(case,"mold")
    for region,actual in (("fluid",fluid),("mold",mold)):
        require(actual["sha256"]==
                b.get("native_flux_records",{}).get(region,{}).get("sha256"),
                "native wall Q file altered: "+region)
    wall=compare_power(fluid,mold)
    require(wall["snapshot_power_comparison"]==
            a["reciprocal_contact_power"]["snapshot_power_comparison"],
            "old Granada wall Q numbers differ from native file")
    live=measure_saved_fields(case)
    recorded=a["all_phase_and_temperature_observables"]
    require(live["snapshots"]==recorded["snapshots"]
            and live["status"]==recorded["status"],
            "native T/alpha has changed since original Granada")
    density=audit_density_inventory(case)
    require(density==a["native_mixture_density_mass_inventory"],
            "native mixture rho does not match original report")
    return {
        "source_case":str(old),
        "old_granada_sha256":digest(a_file),
        "native_log_sha256":digest(log),
        "rho_inventory":density,
        "fields":live,
        "wall":wall,
    }


def audit(case:Path)->dict:
    case=case.expanduser().resolve()
    native=verify_native(case)
    solid=sand_model(case)
    result=solid_energy_steps(
        native["fields"]["snapshots"],
        native["wall"]["snapshot_power_comparison"],
        solid["rho_kg_m3"],solid["Cv_J_kgK"],
    )
    return {
        "schema":"masterproject-fs-c05-existing-native-sand-energy-v1",
        "case":str(case),"status":result["status"],
        "model":solid,"discrete_sand_energy":result,
        "CFD_log_sha256":native["native_log_sha256"],
        "original_granada_report_sha256":native["old_granada_sha256"],
        "wall_reciprocity":native["wall"],
        "real_density_inventory":native["rho_inventory"],
        "metal_vof_relative_drift":native["fields"]["metal_volume_relative_change"],
        "no_new_CFD_executed":True,
        "global_mass_conservation_validated":False,
        "global_energy_conservation_validated":False,
        "phase_resolved_wall_Q_validated":False,
        "solidification_or_shrinkage":False,
        "limitations":[
            "The boundary Q covers BOTH metal-to-sand and air-to-sand faces",
            "This checks the discrete sand energy equation, NOT a global enthalpy balance",
            "rho/Cv of sand and adiabatic support are provisional, not experimental",
            "Open atmospheric boundary mass/enthalpy and pressure work still unmeasured",
        ],
    }


def report_md(x:dict)->str:
    s=x["discrete_sand_energy"]
    lines=[
        "# FS-C05 · Granada: energía de arena SIN volver a correr CFD",
        "",
        "Estado: "+s["status"],
        "",
        "| Tiempo [s] | ΔE arena [J] | Q arena × Δt [J] | Residuo [J] | Error relativo |",
        "|---:|---:|---:|---:|---:|",
    ]
    for step in s["steps"]:
        lines.append(
            f'| {step["time_s"]:.7g} | {step["delta_internal_energy_J"]:.10g} '
            f'| {step["incoming_wall_Q_times_dt_J"]:.10g} '
            f'| {step["energy_residual_J"]:.8g} '
            f'| {step["relative_discrete_error"]:.8g} |')
    lines.extend([
        "",
        "Energía total recibida por arena [J]: "+
        str(s["t0_to_t2_incoming_wall_heat_J"]),
        "Aumento de energía interna arena [J]: "+
        str(s["t0_to_t2_delta_internal_energy_J"]),
        "",
        "Inventario de rho real: "+x["real_density_inventory"]["status"],
        "",
        "No hay validación de masa/energía global, propiedades experimentales, "
        "solidificación o contracción. Esta revisión no ejecutó CFD.",
    ])
    return "\n".join(lines)+"\n"


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",required=True,type=Path)
    p.add_argument("--out",type=Path)
    args=p.parse_args(argv)
    case=args.case.expanduser().resolve()
    dest=args.out or (case.parent/"FS_C05_READ_ONLY_REVIEWS"/(
        "SAND_ENERGY_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid.uuid4().hex[:8]))
    dest=dest.expanduser().resolve()
    try:
        require(not dest.exists() and not dest.is_symlink()
                and dest!=case and case not in dest.parents
                and dest not in case.parents,
                "review output must be NEW and separate from existing CFD")
        result=audit(case)
        dest.mkdir(parents=True)
        (dest/"FS_C05_SAND_ENERGY_REVIEW.json").write_text(
            json.dumps(result,indent=2)+"\n")
        (dest/"FS_C05_SAND_ENERGY_REVIEW.md").write_text(report_md(result))
        s=result["discrete_sand_energy"]
        print("SAND ENERGY:",s["status"])
        print("DELTA ENERGY [J]:",s["t0_to_t2_delta_internal_energy_J"])
        print("INCOMING WALL HEAT [J]:",s["t0_to_t2_incoming_wall_heat_J"])
        print("RELATIVE DISCREPANCY:",s["t0_to_t2_relative_discrepancy"])
        print("REPORTS:",dest)
        print("NO CFD RERUN / NO GLOBAL ENERGY OR MASS CLOSURE.")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("SAND ENERGY REVIEW BLOCKED:",str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
