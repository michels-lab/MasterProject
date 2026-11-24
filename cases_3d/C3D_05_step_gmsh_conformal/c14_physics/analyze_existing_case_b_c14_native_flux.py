#!/usr/bin/env python3
"""Validate C14 REAL fluid/solid native 4-patch q extractor WITHOUT energy-closure claims.

Inputs must be produced by compiled Foundation14 c3d05C14FluidSolidFlux
on the original 101-state genuine C14 fluid+solid case. This parser is
deliberately not a numerical q model and never calls OpenFOAM. JSON reports
mean instantaneous mismatch and SAVED-TIME trapezoids, never native solver
step-integrated fluxes or a physically accepted conservation residual.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

PATCHES={
    ("metal","metal_to_mold"):12636,
    ("metal","metalTop"):None,
    ("mold","mold_to_metal"):12636,
    ("mold","moldOuterUnclassified"):None,
}
SUM_FIELDS=("time_s","region","patch","nFaces","area_m2","q_out_W","gross_abs_face_power_W")
FACE_FIELDS=("time_s","region","patch","face_local","center_x_m","center_y_m",
             "center_z_m","area_m2","normal_x","normal_y","normal_z",
             "q_out_W_m2","q_out_face_W")
STATUS="C3D05_B_C14_REAL_FLUID_SOLID_NATIVE_Q_EXTRACTED_ANALYZED_NOT_ENERGY_CLOSURE"


def require(ok:bool,reason:str)->None:
    if not ok:
        raise ValueError("C3D05_B_C14_NATIVE_Q_AUDIT_BLOCKED: "+reason)


def rows_from(path:Path,fields:tuple[str,...])->list[dict]:
    require(path.is_file() and not path.is_symlink(),"missing native CSV "+str(path))
    with path.open("r",encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        require(reader.fieldnames is not None and tuple(reader.fieldnames)==fields,
                "wrong native q CSV header "+str(path))
        return list(reader)


def float_field(row:dict,key:str)->float:
    val=float(row[key])
    require(math.isfinite(val),"nonfinite q/geometry "+key)
    return val


def signed_interval_integral(rows:list[dict],key:str)->float:
    """Trapezoid over SAVED time step (0.1s), NOT solver-step integrated."""
    return math.fsum(
        .5*(b["time_s"]-a["time_s"])*(a[key]+b[key])
        for a,b in zip(rows,rows[1:])
    )


def native_flux_analysis(sumfile:Path,facefile:Path)->dict:
    raw=rows_from(sumfile,SUM_FIELDS)
    require(len(raw)==101*4,
            "must have 404 original 101 x 4 patch rows")
    bytime:dict[float,dict[tuple[str,str],dict]]={}
    for r in raw:
        t=float_field(r,"time_s")
        key=(r["region"],r["patch"])
        require(key in PATCHES,"C14 actual patch not recognized: "+repr(key))
        require(round(t,9)==t and 0<=t<=10,
                "native stored time outside [0,10] or not exact 0.1s")
        count=int(r["nFaces"])
        expected=PATCHES[key]
        require(count>0 and (expected is None or count==expected),
                "native accepted patch count mismatch: "+repr(key))
        area=float_field(r,"area_m2")
        power=float_field(r,"q_out_W")
        gross=float_field(r,"gross_abs_face_power_W")
        require(area>0 and gross>=0 and gross+1e-7>=abs(power),
                "native patch area or gross flux inconsistent")
        trow=bytime.setdefault(t,{})
        require(key not in trow,"duplicate C14 patch at saved time")
        trow[key]={"time_s":t,"region":key[0],"patch":key[1],
                   "nFaces":count,"area_m2":area,"q_out_W":power,
                   "gross_abs_face_power_W":gross}
    times=sorted(bytime)
    require(len(times)==101 and all(
        math.isclose(t,i*.1,rel_tol=0,abs_tol=1e-9)
        for i,t in enumerate(times)), "original C14 saved 0..10s time axis incomplete")
    require(all(set(items)==set(PATCHES) for items in bytime.values()),
            "native C14 four-patch coverage incomplete at some saved times")
    for key in PATCHES:
        if PATCHES[key] is not None:
            require(all(
                bytime[t][key]["nFaces"]==12636 for t in times),
                "real 12636 mappedWall faces not present at every saved time")
        areas=[bytime[t][key]["area_m2"] for t in times]
        require(max(areas)-min(areas)<1e-8*max(areas),
                "C14 source geometry patch area changes over saved times")
    summary=[]
    for t in times:
        records=bytime[t]
        fm=records[("metal","metal_to_mold")]["q_out_W"]
        fs=records[("mold","mold_to_metal")]["q_out_W"]
        mt=records[("metal","metalTop")]["q_out_W"]
        me=records[("mold","moldOuterUnclassified")]["q_out_W"]
        denominator=abs(fm)+abs(fs)
        summary.append({
            "time_s":t,
            "metal_to_mold_q_out_W":fm,
            "mold_to_metal_q_out_W":fs,
            "interface_sum_outward_W":fm+fs,
            "interface_relative_instantaneous_mismatch_over_gross":
                abs(fm+fs)/denominator if denominator else 0.0,
            "metalTop_q_out_W":mt,
            "moldOuterUnclassified_q_out_W":me,
            "external_total_q_out_W":mt+me,
        })
    rawFaces=rows_from(facefile,FACE_FIELDS)
    final_by_patch:dict[tuple[str,str],dict]={}
    interface_geo={}
    for item in rawFaces:
        t=float_field(item,"time_s")
        require(math.isclose(t,10,abs_tol=1e-9),"face-level flux must be final t=10s")
        key=(item["region"],item["patch"])
        require(key in PATCHES,"unrecognized original C14 patch in per-face output")
        local=int(item["face_local"])
        expected_count=bytime[10.0][key]["nFaces"]
        require(0<=local<expected_count,"face local label outside native patch range")
        area=float_field(item,"area_m2")
        power=float_field(item,"q_out_face_W")
        q=float_field(item,"q_out_W_m2")
        xyz=tuple(float_field(item,c) for c in
                  ("center_x_m","center_y_m","center_z_m"))
        normal=tuple(float_field(item,c) for c in
                     ("normal_x","normal_y","normal_z"))
        require(area>0 and math.isclose(power,area*q,rel_tol=1e-8,abs_tol=1e-10),
                "native per-face flux power differs from q*area")
        require(math.isclose(sum(v*v for v in normal),1.0,abs_tol=1e-7),
                "native face outward normal not unit length")
        block=final_by_patch.setdefault(key,{"ids":set(),"net":0.0,
                                              "gross":0.0,"area":0.0})
        require(local not in block["ids"],
                "duplicate original face local index")
        block["ids"].add(local)
        block["net"]+=power
        block["gross"]+=abs(power)
        block["area"]+=area
        if key[1] in ("metal_to_mold","mold_to_metal"):
            # Geometrically conformal STEP/Gmsh faces. Never assert heat-flux
            # symmetry merely because centers coincide.
            pos=tuple(round(c,8) for c in xyz)
            patch_data=interface_geo.setdefault(key,{})
            require(pos not in patch_data,
                    "duplicated interface center at 10^-8m quantization")
            patch_data[pos]={"normal":normal,"area":area,"q":q}
    require(set(final_by_patch)==set(PATCHES),
            "per-face 10s data does not cover original four C14 patches")
    for key,entry in final_by_patch.items():
        expected=bytime[10.0][key]
        require(len(entry["ids"])==expected["nFaces"]
                and all(i in entry["ids"] for i in range(expected["nFaces"])),
                "missing actual per-face native C14 values")
        for k,expectedvalue in (
            ("area",expected["area_m2"]),
            ("net",expected["q_out_W"]),
            ("gross",expected["gross_abs_face_power_W"]),
        ):
            require(math.isclose(entry[k],expectedvalue,
                                 rel_tol=1e-8,abs_tol=1e-8),
                    "integrated and face-resolved q mismatch "+repr(key)+":"+k)
    metal=interface_geo[("metal","metal_to_mold")]
    mold=interface_geo[("mold","mold_to_metal")]
    common=set(metal)&set(mold)
    opposed=sum(
        1 for face in common
        if sum(a*b for a,b in zip(metal[face]["normal"],mold[face]["normal"]))<-.99
    )
    areaMatched=sum(
        1 for face in common if math.isclose(
            metal[face]["area"],mold[face]["area"],
            rel_tol=1e-6,abs_tol=1e-12)
    )
    qdiff=sum(
        abs(metal[face]["q"]*metal[face]["area"]+
            mold[face]["q"]*mold[face]["area"])
        for face in common)
    interfaceGeometry={
        "matched_rounded_centres_at_1e_8_m":len(common),
        "faces_each":12636,
        "opposing_normals_count_dot_below_minus_0_99":opposed,
        "matched_face_areas_count":areaMatched,
        "matched_face_abs_power_sum_W":qdiff,
        "interface_geometry_and_orientation_complete":
            len(common)==12636 and opposed==12636 and areaMatched==12636,
        "centre_quantization_rounding_m":1e-8,
        "flux_equality_is_NOT_implied_by_geometric_pairing":True
    }
    interfaceSignedSavedIntegral=signed_interval_integral(
        summary,"interface_sum_outward_W")
    externalSavedIntegral=signed_interval_integral(
        summary,"external_total_q_out_W")
    return {
        "schema":"C3D05_B_C14_REAL_F14_FLUID_SOLID_BOUNDARY_Q_101_TIMES_V1",
        "status":STATUS,
        "stored_time_count":len(summary),
        "time_axis_s":[t for t in times],
        "native_original_C14_metal_transport":"fluidThermoThermophysicalTransportModel::q()",
        "native_original_C14_sand_transport":"solidThermophysicalTransportModel::q()",
        "native_patch_count":4,
        "native_interface_faces_each":12636,
        "per_face_native_last_time_count":len(rawFaces),
        "per_face_geometry":interfaceGeometry,
        "first":summary[0],
        "final":summary[-1],
        "max_interface_instantaneous_mismatch_over_gross":max(
            item["interface_relative_instantaneous_mismatch_over_gross"]
            for item in summary),
        "signed_interface_sum_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL":
            interfaceSignedSavedIntegral,
        "signed_external_total_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL":
            externalSavedIntegral,
        "patch_time_history":summary,
        "all_source_original_CFD_fields_read_only":True,
        "real_fluid_and_solid_heat_conduction_q_computed":True,
        "native_latent_fvModel_source_integral":False,
        "native_pressure_advection_work_terms":False,
        "boundary_flux_native_time_step_integral":False,
        "overall_energy_conservation_verified":False,
        "JMatPro_QuickCup_experiment_validated":False,
        "notes":[
            "Four patch conduction fluxes only, metal model is FLUID not the T0 all-solid extractor.",
            "Outward flux is positive leaving each named region. Both mappedWall sides reported independently.",
            "Heat q() is not advective mass/enthalpy flux or integrated native fvModel latent energy.",
            "101 saved 0.1s snapshots are coarser than the actual 0.001s CFD time step; trapezoids are approximations.",
            "Exterior convective/radiative conditions may contain additional terms not captured by conduction q alone.",
            "The earlier combined -1352.944 J reference change is NOT energy leakage; no closure residual is accepted.",
            "No solver reruns or original CFD input/data changes.",
        ],
    }
