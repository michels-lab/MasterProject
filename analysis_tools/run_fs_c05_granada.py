#!/usr/bin/env python3
"""FS-C05 OPERACION GRANADA: ONE isolated run, ALL available physics checks.

Single user invocation, no unit-test ritual or repetitive terminal commands:
  1. Provenance guard and safe NEW clone from original staged FS-C05.
  2. Foundation14 foamMultiRun two-step compressibleVoF+solid with BOTH wall
     heat-flux probes; only explicitly with --native.
  3. Check actual Qfluid, Qmold and reciprocity at both native times.
  4. Read ALL three native alpha/T snapshots from the SAME run, compute
     Vmetal(t), phase-weighted temperatures, mold temperature and anomalies.
  5. Produce a single JSON and human-readable Markdown report in that clone.

No solver or file edits on earlier FS-C04/FS-C05 results, no new
experiments hidden in this command, no false global-energy/mass validation.
Optional provisional constant-property thermal storage is explicitly NOT
an enthalpy/energy closure in compressible open-boundary two-phase CFD.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c05_postrun_fields import measure_saved_fields
from run_fs_c05_wall_heat_flux import run as run_wall_probe

RUN_PREFIX="FS_C05_WALL_Q_PROBE_"
RHO_IRON=6820.0
CV_IRON=827.0
RHO_SAND=1500.0
CV_SAND=700.0
RHO_AIR_REFERENCE=100000.0/(287.05*300.0)
CV_AIR_REFERENCE=718.0


def thermal_storage_proxies(first:dict,last:dict)->dict:
    """Constant-property ∆(rho Cv VT) only; NEVER an energy balance."""
    def capacity(volume_key:str,T_key:str,rho:float,Cv:float)->float:
        initial=rho*Cv*first[volume_key]*first[T_key]
        final=rho*Cv*last[volume_key]*last[T_key]
        require(math.isfinite(initial) and math.isfinite(final),
                "nonfinite thermal storage proxy")
        return final-initial
    metal=capacity("metal_phase_volume_raw_m3",
                   "metal_alpha_volume_weighted_T_K",
                   RHO_IRON,CV_IRON)
    # NOTE: constant *reference* gas density ignores ideal-gas compression!
    air=capacity("air_phase_volume_clamped_m3",
                 "air_alpha_volume_weighted_T_K",
                 RHO_AIR_REFERENCE,CV_AIR_REFERENCE)
    sand=capacity("mold_region_volume_m3",
                  "mold_region_volume_weighted_T_K",
                  RHO_SAND,CV_SAND)
    return {
        "metal_delta_sensible_J_PROVISIONAL":metal,
        "air_delta_sensible_J_FIXED_REFERENCE_RHO_ONLY":air,
        "sand_delta_sensible_J_PROVISIONAL":sand,
        "algebraic_sum_J_NOT_A_CONSERVATION_RESIDUAL":metal+air+sand,
        "assumed_metal_rho_kg_m3":RHO_IRON,
        "assumed_sand_rho_kg_m3":RHO_SAND,
        "assumed_air_reference_rho_kg_m3":RHO_AIR_REFERENCE,
        "constant_Cv_J_kgK":{
            "metal":CV_IRON,"air":CV_AIR_REFERENCE,"sand":CV_SAND,
        },
        "thermodynamic_energy_conservation_validated":False,
        "reason_NOT_energy_balance":
            "Density/enthalpy are temperature/pressure dependent; "
            "the air is compressible and the external boundaries are open; "
            "pressure work, gas enthalpy flux, kinetic energy, "
            "latent heat and time-integration effects are not included.",
    }


def assemble(probe:dict,observables:dict)->dict:
    require(probe.get("status")==
            "TWO_STEP_FLUID_MOLD_WALL_Q_MEASURED_NO_ENERGY_VALIDATION"
            and probe.get("wall_heat_flux_measured") is True
            and probe.get("native_solver_executed") is True,
            "actual native two-wall flux measurements required")
    require(observables.get("status") in (
        "NATIVE_TWO_STEP_FIELDS_MEASURED_NO_CHT_VALIDATION",
        "NATIVE_TWO_STEP_FIELDS_MEASURED_WITH_WARNINGS_NO_CHT_VALIDATION"),
        "actual native 3-time alpha/T field measurements required")
    require(observables.get("case")==probe["output"],
            "wall flux and saved field data belong to different cases")
    snapshots=observables["snapshots"]
    require(len(snapshots)==3 and
            [x["time_s"] for x in snapshots]==[0.,1e-7,2e-7],
            "native snapshots must contain exactly 0,1e-7,2e-7 s")
    power=probe["reciprocal_contact_power"]
    require(len(power["snapshot_power_comparison"])==2,
            "both native coupled wall power measurements required")
    first,last=snapshots[0],snapshots[-1]
    estimates=thermal_storage_proxies(first,last)
    alerts=[]
    if power["alert_mismatch_over_5pct"]:
        alerts.append("FLUID_SAND_CONTACT_Q_MISMATCH_GT_5PCT")
    if not observables["metal_volume_drift_below_alert"]:
        alerts.append("METAL_VOF_VOLUME_DRIFT_GT_0_1PCT")
    if any(not x["alpha_within_tolerance"] for x in snapshots):
        alerts.append("VOF_ALPHA_OUT_OF_RANGE")
    if observables["air_alpha_weighted_T_change_K"]>0.5:
        alerts.append("FAST_AIR_WARMING_REQUIRES_OPEN_BOUNDARY_AND_ENTHALPY_AUDIT")
    return {
        "schema":"masterproject-fs-c05-granada-integrated-two-step-v1",
        "status":(
            "FS_C05_GRANADA_INTEGRATED_MEASUREMENTS_WITH_WARNINGS"
            if alerts else "FS_C05_GRANADA_INTEGRATED_MEASUREMENTS_COMPLETED"
        ),
        "case":probe["output"],
        "actual_native_CFD_completed":True,
        "initial_to_final_s":2e-7,
        "native_heat_flux":probe["native_flux_records"],
        "reciprocal_contact_power":power,
        "all_phase_and_temperature_observables":observables,
        "constant_property_thermal_storage_PROXIES_ONLY":estimates,
        "attention_items":alerts,
        "scope":{
            "VOF_initial_volume_and_final_observed":True,
            "phase_T_observed":True,
            "fluid_mold_wall_power_Q_observed":True,
            "mass_conservation_verified":False,
            "global_energy_conservation_verified":False,
            "boundary_enthalpy_flux_verified":False,
            "physical_cooling_curve_validated":False,
            "material_properties_calibrated":False,
            "solidification_or_shrinkage_present":False,
        },
        "next_experiment_requires_NEW_instrumentation":
            "phase mass ∫rho_i*alpha_i dV, open-atmosphere mass/enthalpy "
            "flux, true thermo enthalpy storage, wall power time integration "
            "and convergence/mesh sensitivity before long transient.",
    }


def report_text(result:dict)->str:
    s=result["all_phase_and_temperature_observables"]
    q=result["reciprocal_contact_power"]["snapshot_power_comparison"]
    e=result["constant_property_thermal_storage_PROXIES_ONLY"]
    lines=[
        "# FS-C05 — Operación Granada · diagnóstico integrado de 2 pasos",
        "",
        "Estado: "+result["status"],
        "Caso: "+result["case"],
        "Duración simulada: 2 × 10⁻⁷ s (0.2 µs)",
        "",
        "## Campos nativos medidos (no predicciones de una corrida más larga)",
        "",
        "| Variable | t=0 | t=1e-7 s | t=2e-7 s |",
        "|---|---:|---:|---:|",
    ]
    props=[
        ("Volumen hierro VOF [m³]","metal_phase_volume_raw_m3"),
        ("Hierro T media alpha·V [K]","metal_alpha_volume_weighted_T_K"),
        ("Aire T media (1−alpha)·V [K]","air_alpha_volume_weighted_T_K"),
        ("Arena T media volumétrica [K]","mold_region_volume_weighted_T_K"),
        ("T mínima fluido [K]","fluid_T_min_K"),
        ("T máxima fluido [K]","fluid_T_max_K"),
        ("T máxima arena [K]","mold_T_max_K"),
    ]
    for title,key in props:
        vals=[f"{x[key]:.11g}" for x in s["snapshots"]]
        lines.append("| "+title+" | "+" | ".join(vals)+" |")
    lines.extend([
        "",
        f"Deriva relativa de volumen VOF: {s['metal_volume_relative_change']:.11g}",
        "El volumen de fase NO equivale a masa conservada en un fluido compresible.",
        "",
        "## Calor en las dos caras del contacto (Foundation14 wallHeatFlux)",
        "",
        "| Tiempo [s] | Q fluido [W] | Q arena [W] | Q fluid + Q arena [W] | Desajuste relativo |",
        "|---:|---:|---:|---:|---:|",
    ])
    for a in q:
        lines.append(
            f"| {a['time_s']:.7g} | {a['Q_fluid_wall_W']:.8g} | "
            f"{a['Q_mold_wall_W']:.8g} | {a['Q_sum_W']:.8g} | "
            f"{a['absolute_relative_reciprocity_mismatch']:.5g} |")
    lines.extend([
        "",
        "## Indicadores de almacenamiento sensible aproximados (NO balance global)",
        "",
        f"Hierro ΔE* = {e['metal_delta_sensible_J_PROVISIONAL']:.9g} J",
        f"Aire ΔE* = {e['air_delta_sensible_J_FIXED_REFERENCE_RHO_ONLY']:.9g} J",
        f"Arena ΔE* = {e['sand_delta_sensible_J_PROVISIONAL']:.9g} J",
        "",
        e["reason_NOT_energy_balance"],
        "",
        "## Alertas de diagnóstico",
    ])
    lines.extend(
        ["- "+a for a in result["attention_items"]]
        or ["- Sin alertas en estos indicadores; NO significa modelo validado."]
    )
    lines.extend([
        "",
        "NO VALIDADOS: conservación de masa, balance energético global, "
        "flujos de entalpía por atmósfera abierta, propiedades T-dependientes, "
        "solidificación, grafitización, contracción ni fidelidad CAD.",
    ])
    return "\n".join(lines)+"\n"


def run_granada(source:Path,out:Path,native:bool)->dict:
    source=source.expanduser().resolve()
    out=out.expanduser().resolve()
    require(out.name.startswith(RUN_PREFIX)
            and not out.exists() and not out.is_symlink(),
            "Granada requires a unique fresh FS-C05 wall-flux case")
    probe=run_wall_probe(source,out,native)
    if not native:
        return {
            "schema":"masterproject-fs-c05-granada-integrated-two-step-v1",
            "status":"GRANADA_PREPARED_NO_CFD",
            "case":str(out),
            "native_solver_executed":False,
            "no_physical_validation":True,
        }
    report=out/"FS_C05_GRANADA_REPORT.json"
    human=out/"FS_C05_GRANADA_REPORT.md"
    try:
        observables=measure_saved_fields(out)
        assembled=assemble(probe,observables)
        report.write_text(json.dumps(assembled,indent=2,ensure_ascii=False)+"\n")
        human.write_text(report_text(assembled))
        return assembled
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        failure={
            "schema":"masterproject-fs-c05-granada-integrated-two-step-v1",
            "status":"GRANADA_POSTRUN_INCOMPLETE",
            "case":str(out),
            "native_wall_flux_status":probe.get("status"),
            "reason":str(exc),
            "native_solver_executed":True,
            "original_cases_untouched":True,
            "no_physical_validation":True,
        }
        report.write_text(json.dumps(failure,indent=2)+"\n")
        raise


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--native",action="store_true",
                   help="run ONE two-step native CFD and all diagnostics in a fresh case")
    a=p.parse_args(argv)
    name=RUN_PREFIX+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    out=a.out or (
        Path.home()/"OpenFOAM"/"FS_C05_GRANADA_RUNS"/name
    )
    try:
        result=run_granada(a.source,out,a.native)
        print("FS-C05 GRANADA:",result["status"])
        print("Independent case:",result["case"])
        if a.native:
            s=result["all_phase_and_temperature_observables"]
            print("VOF metal ΔV/V:",s["metal_volume_relative_change"])
            print("Iron ΔT K:",s["metal_alpha_weighted_T_change_K"])
            print("Air ΔT K:",s["air_alpha_weighted_T_change_K"])
            print("Sand ΔT K:",s["mold_volume_weighted_T_change_K"])
            print("Wall-power reciprocity:",
                  result["reciprocal_contact_power"]["snapshot_power_comparison"])
            print("REPORT JSON:",out/"FS_C05_GRANADA_REPORT.json")
            print("REPORT MD:",out/"FS_C05_GRANADA_REPORT.md")
            print("NO global mass or enthalpy balance / NO solidification.")
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("FS-C05 GRANADA DIAGNOSTIC STOPPED:",str(exc),file=sys.stderr)
        print("ISOLATED CASE:",out,file=sys.stderr)
        for name in ("log.FS_C05_wall_q_foamMultiRun",
                     "FS_C05_WALL_Q_REPORT.json",
                     "FS_C05_GRANADA_REPORT.json"):
            pth=out/name
            if pth.is_file() and not pth.is_symlink():
                print("SAVED EVIDENCE:",pth,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
