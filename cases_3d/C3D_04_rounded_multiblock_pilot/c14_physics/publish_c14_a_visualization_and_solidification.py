#!/usr/bin/env python3
"""Publish a standalone OpenFOAM/ParaView/FoamLens visualization case from real A results.
No CFD, no repeated native postprocessing, no changes to existing evidence.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import shutil
import sys

import continue_c14_stage07_grouped_evidence as evidence
import run_c14_stage07_grouped_native_recovery as grouped
import run_c14_stage07_bilateral_native_flux as bilateral
import run_c14_stage07_solver_backed_recovery as recovery
import c14_3d_postprocess_parity as volume

REPORT="C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json"
PHASE="solidification_101.csv"
REQUIRED_FIELDS=("T","U","p_rgh","phaseChangeSource:alpha1",
                 "phaseChangeSolidFraction","phaseChangeDarcyCoeff",
                 "magPhaseChangeDarcyAcceleration","magPhaseChangeBuoyancyAcceleration",
                 "magPRghAcceleration")

def need(ok,msg):
    if not ok: raise ValueError(msg)

def copy_regular(src,dst):
    need(src.is_file() and not src.is_symlink() and not dst.exists(),"unsafe copy: "+str(src))
    shutil.copy2(src,dst)

def copy_tree(src,dst):
    need(src.is_dir() and not src.is_symlink() and not dst.exists(),"unsafe tree: "+str(src))
    need(not any(p.is_symlink() for p in src.rglob("*")),"symlink in source "+str(src))
    shutil.copytree(src,dst)

def write_csv(path,rows):
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def phase_series(source,work,out):
    v=volume.cell_volumes(source,"metal",8960)
    vs=volume.cell_volumes(source,"mold",12352)
    total=math.fsum(v)
    contract=recovery.read_json(volume.CONTRACT)["C14_exact_values"]
    rho=contract["metal"]["rho_kg_m3"]
    pc=contract["solidification"]
    L=pc["L_J_kg"]
    Tsol,Tliq=pc["Tsol_K"],pc["Tliq_K"]
    def read(p,n=8960):return volume.native.scalar_field_values(p,n)
    def mean(values):return math.fsum(x*y for x,y in zip(values,v))/total
    rows=[]
    for i,t in enumerate(evidence.NAMES):
        m=source/t/"metal"
        s=source/t/"mold"
        d=work/t/"metal"
        T=read(m/"T")
        Ts=read(s/"T",12352)
        alpha=read(m/"phaseChangeSource:alpha1")
        need(all(-1e-7<=a<=1+1e-7 for a in alpha),"alpha out of range "+t)
        U=volume.vector_field(m/"U",8960)
        speed=[math.sqrt(sum(x*x for x in u)) for u in U]
        D=read(d/"phaseChangeDarcyCoeff")
        drag=read(d/"magPhaseChangeDarcyAcceleration")
        buoy=read(d/"magPhaseChangeBuoyancyAcceleration")
        pressure=read(d/"magPRghAcceleration")
        sf=1-mean(alpha)
        row={"time_s":i/10,"metal_T_min_K":min(T),"metal_T_volume_mean_K":mean(T),
             "metal_T_max_K":max(T),"mold_T_volume_mean_K":volume.weighted(Ts,vs),
             "liquid_fraction_volume_mean":mean(alpha),"solid_fraction_volume_mean":sf,
             "solid_inventory_nominal_kg":rho*total*sf,
             "latent_inventory_released_since_initial_nominal_J":rho*L*total*sf,
             "volume_below_Tsol_fraction":math.fsum(vv for tt,vv in zip(T,v) if tt<Tsol)/total,
             "volume_between_Tsol_Tliq_fraction":math.fsum(vv for tt,vv in zip(T,v) if Tsol<=tt<Tliq)/total,
             "volume_at_or_above_Tliq_fraction":math.fsum(vv for tt,vv in zip(T,v) if tt>=Tliq)/total,
             "speed_volume_mean_m_s":mean(speed),"speed_max_m_s":max(speed),
             "speed_rms_m_s":math.sqrt(mean([x*x for x in speed])),
             "Darcy_coeff_volume_mean_s_inv":mean(D),"Darcy_coeff_max_s_inv":max(D),
             "Darcy_accel_mag_volume_mean_m_s2":mean(drag),"Darcy_accel_mag_max_m_s2":max(drag),
             "buoyancy_accel_mag_volume_mean_m_s2":mean(buoy),"buoyancy_accel_mag_max_m_s2":max(buoy),
             "pressure_accel_mag_volume_mean_m_s2":mean(pressure),"pressure_accel_mag_max_m_s2":max(pressure),
             "cooling_rate_saved_interval_K_s":None,
             "solid_fraction_rate_saved_interval_s_inv":None,
             "latent_release_saved_interval_nominal_W":None}
        for label,ids in (
            ("liquidlike",[j for j,a in enumerate(alpha) if a>=.99]),
            ("mixed",[j for j,a in enumerate(alpha) if .01<a<.99]),
            ("solidlike",[j for j,a in enumerate(alpha) if a<=.01])):
            vv=math.fsum(v[j] for j in ids)
            row[label+"_volume_fraction"]=vv/total
            row[label+"_speed_volume_mean_m_s"]=math.fsum(v[j]*speed[j] for j in ids)/vv if vv else None
        if rows:
            prev=rows[-1]
            row["cooling_rate_saved_interval_K_s"]=(prev["metal_T_volume_mean_K"]-row["metal_T_volume_mean_K"])/.1
            row["solid_fraction_rate_saved_interval_s_inv"]=(sf-prev["solid_fraction_volume_mean"])/.1
            row["latent_release_saved_interval_nominal_W"]=(row["latent_inventory_released_since_initial_nominal_J"]-prev["latent_inventory_released_since_initial_nominal_J"])/.1
        rows.append(row)
    initial=rows[0]["latent_inventory_released_since_initial_nominal_J"]
    for row in rows:
        row["latent_inventory_released_since_initial_nominal_J"]-=initial
    write_csv(out/PHASE,rows)
    onset=next((i for i,r in enumerate(rows[1:],1) if r["solid_fraction_rate_saved_interval_s_inv"]>1e-9),None)
    peak=max(rows[1:],key=lambda r:r["latent_release_saved_interval_nominal_W"])
    peak_speed=max(rows,key=lambda r:r["speed_max_m_s"])
    return {"first":rows[0],"final":rows[-1],
            "first_observed_solid_fraction_increase_interval_s":[rows[onset-1]["time_s"],rows[onset]["time_s"]] if onset else None,
            "maximum_nominal_latent_release_saved_interval_W":peak["latent_release_saved_interval_nominal_W"],
            "maximum_nominal_latent_release_interval_s":[round(peak["time_s"]-.1,9),peak["time_s"]],
            "maximum_speed_saved_m_s":peak_speed["speed_max_m_s"],
            "maximum_speed_saved_time_s":peak_speed["time_s"],
            "time_resolution_s":.1,"solver_deltaT_s":.001,
            "phase_categories":"alpha thresholds 0.01/0.99 are descriptive only; not physical phase identities",
            "native_Darcy_fields_used":True,"true_native_solver_step_derivatives_recovered":False}

def execute(source,work,continuation,qdir,out):
    source,work,continuation,qdir=(p.expanduser().resolve() for p in (source,work,continuation,qdir))
    out=out.expanduser().absolute()
    need(out.parent.resolve()==source.parent and not out.exists() and not out.is_symlink(),"fresh sibling output required")
    need(not out.is_relative_to(HERE_REPO),"output inside repository")
    r=evidence.evidence_gate(source,work)
    prev=recovery.read_json(continuation/evidence.REPORT)
    q=recovery.read_json(qdir/bilateral.REPORT)
    need(prev["source"]==str(source) and prev["grouped_input"]==str(work)
         and prev["source_hashes_unchanged"] and prev["grouped_input_hashes_unchanged"]
         and prev["vertical"]["complete_101_by_80"],"missing real vertical evidence")
    need(q["status"]=="BILATERAL_NATIVE_Q_DIAGNOSTIC_COMPLETE_NOT_CLOSURE"
         and q["saved_times"]==101 and q["patch_rows"]==808
         and q["paired_geometry_faces_at_10s"]==2496
         and q["original_source_hashes_unchanged"] and q["previous_report_hash_unchanged"],"bilateral native q incomplete")
    before=grouped.snapshot_hashes(source)
    out.mkdir()
    result={"schema":"C3D04_A_VISUALIZATION_SOLIDIFICATION_V1","status":"INCOMPLETE_PRESERVED",
            "source":str(source),"grouped_source":str(work),"output":str(out),
            "stage":"08/10","milestones_done":"7/10","source_solver_rerun":False,
            "global_discrete_energy_conservation_verified":False,"quickcup_validated":False}
    try:
        for n in ("constant","system",*evidence.NAMES,"postProcessing"):
            copy_tree(work/n,out/n)
        analysis=out/"analysis"
        analysis.mkdir()
        archive=analysis/"previous_vertical_profiles"
        archive.mkdir()
        for family in ("verticalProfiles","momentumVerticalProfiles"):
            target=out/"postProcessing/metal"/family
            target.rename(archive/family)
            corrected=continuation/"vertical_case/postProcessing/metal"/family
            copy_tree(corrected,target)
            for t in evidence.NAMES:
                need(len(evidence.profile_rows(target/t/"line_x20mm.xy"))==80,"vertical profile incomplete: "+family+"/"+t)
        for src,dst in (
            (continuation/evidence.TABLE,"energy_inventory_101.csv"),
            (continuation/evidence.REPORT,"energy_vertical_report.json"),
            (qdir/"integrated.csv","boundary_native_q_101.csv"),
            (qdir/"last_faces.csv","boundary_native_q_faces_t10.csv"),
            (qdir/bilateral.REPORT,"bilateral_native_q_report.json"),
            (work/grouped.REPORT,"grouped_native_report.json"),
            (source/"log.foamMultiRun","log.foamMultiRun")):
            copy_regular(src,analysis/dst)
        copy_regular(source/"log.foamMultiRun",out/"log.foamMultiRun")
        result["solidification"]=phase_series(source,work,analysis)
        # Preserve all native fields, not just a small predefined subset.
        inventory={}
        for region in ("metal","mold"):
            per_time={t:sorted(p.name for p in (out/t/region).iterdir() if p.is_file()) for t in evidence.NAMES}
            common=set.intersection(*(set(v) for v in per_time.values()))
            inventory[region]={"present_all_101":sorted(common),"present_final":per_time["10"]}
        need(set(REQUIRED_FIELDS)<=set(inventory["metal"]["present_all_101"]),"required native fields incomplete")
        result["field_inventory"]=inventory
        result["postprocessing_families"]=sorted(p.name for p in (out/"postProcessing/metal").iterdir() if p.is_dir())
        result["nominal_combined_inventory_plus_exterior_q_J"]=q["nominal_combined_inventory_plus_exterior_q_J"]
        result["vertical_geometry"]=prev["vertical"]["corrected_profile"]
        result["original_source_hashes_unchanged"]=grouped.snapshot_hashes(source)==before
        need(result["original_source_hashes_unchanged"],"source hashes changed")
        foam=out/"C3D04_A_C14.foam"
        foam.touch(exist_ok=False)
        (out/"README_VISUALIZATION_ES.md").write_text(
            "# Caso 3D-A C14 — resultados reales 0–10 s\n\n"
            "Abrir C3D04_A_C14.foam en ParaView; en FoamLens abrir esta carpeta como caso OpenFOAM multirregión. "
            "Seleccionar metal y mold, tiempos 0 a 10 s. Los campos originales y derivados nativos se conservaron. "
            "Los perfiles verticales corregidos están en postProcessing/metal; la versión parcial original está en analysis/previous_vertical_profiles.\n\n"
            "analysis/solidification_101.csv: historia volumétrica de temperatura, alpha1, velocidades, Darcy, flotación, presión y tasas por intervalo guardado. "
            "energy_inventory_101.csv y boundary_native_q_101.csv: inventario y flujo bilateral. "
            "boundary_native_q_faces_t10.csv: caras de frontera a 10 s. "
            "log.foamMultiRun conserva el log de los 10000 pasos originales.\n\n"
            "Esta es una copia de visualización y postprocesamiento, NO un caso para relanzar CFD. "
            "fvModels contiene cellZone all solo por la equivalencia offline demostrada; el original conserva cellZone metal. "
            "No se recupera ddt de cada paso de 0.001 s a partir de snapshots de 0.1 s. "
            "El perfil vertical corresponde al tramo interior de 14.7 mm, no a la altura completa 2D. "
            "El residuo energético es nominal, no conservación discreta ni validación QuickCup.\n",encoding="utf-8")
        result["foam_file"]=str(foam)
        result["status"]="VISUALIZATION_AND_SOLIDIFICATION_READY"
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        result["error"]=str(exc)
    (out/REPORT).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

HERE_REPO=Path(__file__).resolve().parents[3]
def main():
    h=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    for flag,name in (("case","C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01"),
                      ("grouped","C3D04_A_C14_GROUPED_NATIVE_RECOVERY_01"),
                      ("continuation","C3D04_A_C14_ENERGY_VERTICAL_01"),
                      ("bilateral","C3D04_A_C14_BILATERAL_NATIVE_Q_01")):
        p.add_argument("--"+flag,type=Path,default=h/name)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        r=execute(a.case,a.grouped,a.continuation,a.bilateral,a.out)
        print(json.dumps(r,indent=2))
        return 0 if r["status"]=="VISUALIZATION_AND_SOLIDIFICATION_READY" else 3
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print("C3D04_A_VISUALIZATION_BLOCKED:",exc,file=sys.stderr)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
