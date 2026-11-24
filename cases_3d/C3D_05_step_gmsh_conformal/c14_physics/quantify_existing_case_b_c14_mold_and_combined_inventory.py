#!/usr/bin/env python3
"""Case B C14 ORIGINAL 10 s: mold sensible inventory + metal phase proxy.

READ-ONLY: original native metal/mold CFD, original postrun CSV+SHA and the
already audited original C14 metal-reference energy inventory CSV+SHA.
A new, separate output holds 101 archived mold sensible deltas and the
combined-model STORAGE-CHANGE PROXY. NOT a source-term, heat-flux or energy
balance, NOT real JMatPro/QuickCup validation. NO SOLVER, remesh or overwrite.
"""
from __future__ import annotations

import argparse
from array import array
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze_existing_case_b_c14 as n
import volume_weighted_existing_case_b_c14 as v
import quantify_existing_case_b_c14_energy_inventory as en

CASE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
POST=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01"
METAL=Path.home()/"OpenFOAM/C3D05_B_C14_SENSIBLE_LATENT_EQUIVALENT_01"
OUT=Path.home()/"OpenFOAM/C3D05_B_C14_MOLD_COMBINED_REFERENCE_STORAGE_01"
CSV="C3D05_B_C14_REAL_MOLD_COMBINED_REFERENCE_101_STATES.csv"
JSON="C3D05_B_C14_REAL_MOLD_COMBINED_REFERENCE_REPORT.json"
MANIFEST="C3D05_B_C14_REAL_MOLD_COMBINED_REFERENCE_SHA256.json"
STATUS="C3D05_B_C14_REAL_MOLD_AND_METAL_REFERENCE_STORAGE_ONLY_NOT_ENERGY_CLOSURE"
MOLD_CELLS=178588
CHECKMESH_MOLD_M3=0.000102843380345
MESH_RELATIVE_GATE=0.005
COLUMNS=(
    "time_s","mold_volume_weighted_mean_T_K",
    "mold_sensible_change_from_t0_J",
    "metal_sensible_change_from_t0_J",
    "metal_liquid_latent_content_change_from_t0_J",
    "metal_latent_solid_equivalent_increase_from_t0_J",
    "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY",
    "mold_sensible_rate_saved_interval_W",
    "combined_storage_rate_saved_interval_W"
)


def require(ok:bool, reason:str)->None:
    if not ok:
        raise ValueError("C3D05_B_C14_MOLD_REFERENCE_INVENTORY_BLOCKED: "+reason)


def sha(path:Path)->str:
    require(path.is_file() and not path.is_symlink(),
            "native/previous report missing or symlink: "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as inp:
        while data:=inp.read(1024*1024):
            h.update(data)
    return h.hexdigest()


def native_mold_cell_volumes(poly:Path, expected_cells:int=MOLD_CELLS,
                             native_volume_m3:float=CHECKMESH_MOLD_M3)->tuple[array,dict]:
    """Compute volume from authentic owner-oriented quads, no OpenFOAM call.

    A single global origin is used; triangulation of warped quads may differ
    from OpenFOAM native per-cell algorithm. We check aggregate checkMesh
    volume but explicitly do NOT certify individual cell exactness.
    """
    require(expected_cells>=1 and native_volume_m3>0,"invalid mold volume contract")
    points=v.parse_points(poly/"points")
    owner=v.parse_labels(poly/"owner","owner")
    neighbour=v.parse_labels(poly/"neighbour","neighbour")
    faces_total=len(owner)
    ninternal=len(neighbour)
    require(faces_total>ninternal>0 and
            max(max(owner),max(neighbour))+1==expected_cells,
            "native owner/neighbour mold cell labels do not match accepted geometry")
    n,body=v.foam_ascii_list(poly/"faces","faces")
    require(n==faces_total,"original mold faces/owner lengths differ")
    regex=re.compile(r"(\d+)\s*\(\s*([\d\s]+?)\s*\)")
    accumulated=array("d",[0.0])*expected_cells
    origin=points[0]
    consumed=0
    for record in regex.finditer(body):
        require(consumed<faces_total,"extra original mold face")
        require(int(record.group(1))==4,"non-quad face in accepted HEX8 mold")
        idx=tuple(int(i) for i in record.group(2).split())
        require(len(idx)==4 and len(set(idx))==4
                and all(0<=i<len(points) for i in idx),
                "invalid original mold face vertices")
        six=v.quad_signed_six_volume(points,idx,origin)
        accumulated[owner[consumed]]+=six
        if consumed<ninternal:
            accumulated[neighbour[consumed]]-=six
        consumed+=1
    require(consumed==faces_total,"original mold face payload truncated")
    vols=array("d",(six/6.0 for six in accumulated))
    require(all(math.isfinite(vi) and vi>0 for vi in vols),
            "nonpositive/nonfinite original mold cell volume")
    total=math.fsum(vols)
    relative=abs(total-native_volume_m3)/native_volume_m3
    require(relative<=MESH_RELATIVE_GATE,
            f"original mold HEX8 volume sum != checkMesh (relative={relative:.8g}); stop")
    return vols,{
        "native_mold_hex8_cells":expected_cells,"points":len(points),
        "faces":faces_total,"internal_faces":ninternal,
        "total_reconstructed_mold_volume_m3":total,
        "native_checkMesh_mold_volume_m3":native_volume_m3,
        "relative_total_volume_discrepancy":relative,
        "min_cell_volume_m3":min(vols),"max_cell_volume_m3":max(vols),
        "native_per_cell_V_directly_verified":False,
        "warped_quad_triangulation_approximation_possible":True,
    }


def mold_storage(T0:list[float],T:list[float],volumes:array,
                 rho:float,Cv:float)->dict:
    require(len(T0)==len(T)==len(volumes)>0,"mold fields/volumes length mismatch")
    require(all(math.isfinite(x) and x>0 for x in T0+T),
            "mold native absolute T nonpositive/nonfinite")
    require(all(math.isfinite(x) and x>0 for x in volumes),
            "bad native mold cell volume")
    require(rho>0 and Cv>0 and math.isfinite(rho*Cv),
            "bad C14 original mold rho/Cv")
    vol=math.fsum(volumes)
    Tmean=math.fsum(vi*ti for vi,ti in zip(volumes,T))/vol
    delta=rho*Cv*math.fsum(vi*(ti-t0) for vi,ti,t0 in zip(volumes,T,T0))
    return {"mold_volume_weighted_mean_T_K":Tmean,
            "mold_sensible_change_from_t0_J":delta}


def combined_storage(mold_delta:float,metal_sensible_delta:float,
                     positive_solid_latent_equivalent:float)->dict:
    """Solid-phase equivalent positive -> LIQUID latent content delta negative.

    This is a reference-accounting identity, NOT conservation or measured
    thermal heat transfer. Do not claim missing heat/leak or q from this sum.
    """
    require(all(math.isfinite(x) for x in (
        mold_delta,metal_sensible_delta,positive_solid_latent_equivalent)),
        "nonfinite original metal/mold storage terms")
    liquid_latent_change=-positive_solid_latent_equivalent
    return {
        "metal_sensible_change_from_t0_J":metal_sensible_delta,
        "metal_liquid_latent_content_change_from_t0_J":liquid_latent_change,
        "metal_latent_solid_equivalent_increase_from_t0_J":positive_solid_latent_equivalent,
        "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY":
            mold_delta+metal_sensible_delta+liquid_latent_change,
    }


def verified_archived_sources(case:Path,post:Path,metal:Path)->tuple[list[tuple[float,str]],list[dict],dict]:
    require(case.name==CASE.name and post.name==POST.name
            and metal.name==METAL.name,
            "only genuine original 10s Case B C14 completed CFD and analysis accepted")
    stage,verified=n.validated_mesh_and_stage(case)
    require(sha(case/n.LOG)==stage["solver_log_sha256"],
            "completed native real solver log altered")
    require(post.is_dir() and not post.is_symlink()
            and metal.is_dir() and not metal.is_symlink(),
            "source analysis missing/symlinked")
    postdoc=json.loads((post/n.JSON).read_text(encoding="utf-8"))
    postsha=json.loads((post/n.MANIFEST).read_text(encoding="utf-8"))
    require(postdoc["status"]==n.STATUS
            and postdoc["native_CFD_solved_full_10s"] is True
            and postsha.get("analysis_csv_sha256")==sha(post/n.CSV)
            and postsha.get("analysis_json_sha256")==sha(post/n.JSON)
            and postsha.get("native_stage_report_sha256")==sha(case/n.REPORT),
            "101 original native postrun SHA/status differs")
    energy=json.loads((metal/en.JSON).read_text(encoding="utf-8"))
    energysha=json.loads((metal/en.MANIFEST).read_text(encoding="utf-8"))
    require(energy["status"]==en.STATUS
            and energy["nStates"]==101
            and energy["native_solver_latent_fvModels_integral_computed"] is False
            and energy["metal_sand_exterior_energy_balance_verified"] is False,
            "original energy inventory source incorrectly claims physical closure")
    require(Path(energy["real_native_archive_used"]).resolve()==case.resolve()
            and Path(energy["real_native_101_state_postrun_used"]).resolve()==post.resolve(),
            "metal inventory not from this completed case")
    require(energysha.get("result_CSV_SHA256")==sha(metal/en.CSV)
            and energysha.get("result_JSON_SHA256")==sha(metal/en.JSON)
            and energysha.get("source_native_CFD_report_SHA256")==sha(case/n.REPORT)
            and energysha.get("source_native_CFD_log_SHA256")==sha(case/n.LOG),
            "previous original metal inventory SHA mismatch")
    with (metal/en.CSV).open(encoding="utf-8",newline="") as fp:
        e_rows=list(csv.DictReader(fp))
    times=n.saved_times(case)
    require(len(times)==101 and len(e_rows)==101
            and [t for t,label in times]==[float(x["time_s"]) for x in e_rows],
            "metal inventory 101 time axis and original native CFD differ")
    constants=en.source_C14_constants()
    mold_ref=json.loads(n.physics.CONTRACT.read_text(encoding="utf-8"))["C14_exact_values"]["mold"]
    return times,e_rows,{
        "rho_mold_kg_m3":float(mold_ref["rho_kg_m3"]),
        "Cv_mold_J_kgK":float(mold_ref["Cv_J_kgK"]),
        "C14_contract_sha256":constants["source_sha256"],
        "metal_C14_inventory_status":energy["status"],
    }


def run(case:Path,post:Path,metal:Path,out:Path)->dict:
    case=case.expanduser().absolute()
    post=post.expanduser().absolute()
    metal=metal.expanduser().absolute()
    out=out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(),
            "existing output immutable, refuse replacement")
    require(all(out!=p and out not in p.parents and p not in out.parents
                for p in (case,post,metal)),
            "output cannot overlap source CFD or old archives")
    times,metal_series,c14=verified_archived_sources(case,post,metal)
    source_poly=case/"constant/mold/polyMesh"
    vols,geom=native_mold_cell_volumes(source_poly)
    original_T=n.source_reader.scalar_field_values(
        case/"0/mold/T",MOLD_CELLS)
    series=[]
    for i,((t,label),historical) in enumerate(zip(times,metal_series),1):
        T=n.source_reader.scalar_field_values(
            case/label/"mold/T",MOLD_CELLS)
        m=mold_storage(original_T,T,vols,c14["rho_mold_kg_m3"],
                       c14["Cv_mold_J_kgK"])
        old_sensible=float(historical["metal_sensible_change_from_t0_J"])
        old_latent=float(historical[
            "metal_latent_equivalent_solid_complement_change_from_t0_J"])
        combined=combined_storage(
            m["mold_sensible_change_from_t0_J"],old_sensible,old_latent)
        entry={"time_s":t,**m,**combined}
        if series:
            dt=t-series[-1]["time_s"]
            require(dt>0,"saved CFD time not increasing")
            entry["mold_sensible_rate_saved_interval_W"]=(
                entry["mold_sensible_change_from_t0_J"]-
                series[-1]["mold_sensible_change_from_t0_J"])/dt
            entry["combined_storage_rate_saved_interval_W"]=(
                entry["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"]-
                series[-1]["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"])/dt
        else:
            entry["mold_sensible_rate_saved_interval_W"]=None
            entry["combined_storage_rate_saved_interval_W"]=None
        series.append(entry)
        if i==1 or i%10==0 or i==len(times):
            print(f"C3D05_B_MOLD_REFERENCE_STORAGE_READONLY: {i}/{len(times)} "
                  f"states, t={t:g}s, NO_ENERGY_CLOSURE_NO_CFD",flush=True)
    require(abs(series[0]["mold_sensible_change_from_t0_J"])<1e-8
            and abs(series[0][
                "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"])<1e-8,
            "t0 energy reference should have zero change")
    final=series[-1]
    result={
        "schema":"C3D05_B_C14_REAL_MOLD_PLUS_METAL_REFERENCE_STORAGE_101_STATES_V1",
        "status":STATUS,
        "original_native_C14_run_readonly":str(case),
        "original_metal_reference_inventory_readonly":str(metal),
        "mold_C14_constant_reference":c14,
        "real_mold_HEX8_geometry":geom,
        "saved_states":len(series),
        "initial":series[0],"final":final,
        "mold_energy_is_rho_Cv_deltaT_reference_only":True,
        "metal_latent_liquid_content_delta_is_negative_solid_equivalent":True,
        "combined_change_is_NOT_calibrated_energy_leak_or_conservation":True,
        "native_fvModel_latent_heat_source_integral_verified":False,
        "native_mappedWall_interface_flux_integrated":False,
        "native_exterior_fluid_solid_flux_integrated":False,
        "native_convection_and_work_terms_verified":False,
        "overall_sensible_latent_energy_conservation_verified":False,
        "JMatPro_QuickCup_experimental_validation":False,
        "contraction_or_feeding_physics_enabled":False,
        "notes":[
            "Positive solid equivalent +rho L delta(1-alpha) is a loss of LIQUID latent stored content; combined reference delta uses its negative.",
            "Changing metal, mold or phase inventory is NOT a measured interfacial heat flux or true fvModel latent source time integral.",
            "Mold sensible delta uses original C14 rho=1500 kg/m3 and Cv=700 J/kg/K, not temperature-dependent experimental data.",
            "Distorted HEX8 nonplanar face geometry and 1826 severe nonorth faces remain unresolved for per-cell native volume equivalence.",
            "Without boundary q, radiation/convection, source terms and transport, combined stored-energy change is NOT a closure error.",
            "All previous native CFD and three postrun analysis archives preserved, no CFD executed.",
        ],
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(
            dir=str(out.parent),prefix="."+out.name+".staging.") as tmp:
        pending=Path(tmp)/"candidate"
        pending.mkdir()
        with (pending/CSV).open("x",encoding="utf-8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(series)
        (pending/JSON).write_text(json.dumps(result,indent=2,
                                   ensure_ascii=False)+"\n",encoding="utf-8")
        (pending/MANIFEST).write_text(json.dumps({
            "original_C14_contract_SHA256":c14["C14_contract_sha256"],
            "original_CFD_native_solver_report_SHA256":sha(case/n.REPORT),
            "original_CFD_native_solver_log_SHA256":sha(case/n.LOG),
            "original_native_101_states_CSV_SHA256":sha(post/n.CSV),
            "original_metal_inventory_CSV_SHA256":sha(metal/en.CSV),
            "mold_polyMesh_original_SHA256":{
                key:sha(source_poly/key)
                for key in ("points","faces","owner","neighbour")},
            "result_CSV_SHA256":sha(pending/CSV),
            "result_JSON_SHA256":sha(pending/JSON),
            "NEVER_REWRITE_PREVIOUS_CFD_OR_ANALYSES":True
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "someone created output; stop without overwrite")
        pending.rename(out)
    return result


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",type=Path,default=CASE)
    ap.add_argument("--postrun",type=Path,default=POST)
    ap.add_argument("--metal",type=Path,default=METAL)
    ap.add_argument("--out",type=Path,default=OUT)
    args=ap.parse_args()
    try:
        doc=run(args.case,args.postrun,args.metal,args.out)
        print(json.dumps({
            "status":doc["status"],
            "out":str(args.out),
            "states":doc["saved_states"],
            "mold_accepted_real_HEX8_volume":doc["real_mold_HEX8_geometry"],
            "mold_sensible_change_t10_J":doc["final"]["mold_sensible_change_from_t0_J"],
            "metal_sensible_change_t10_J":doc["final"]["metal_sensible_change_from_t0_J"],
            "metal_liquid_latent_content_change_t10_J":doc["final"][
                "metal_liquid_latent_content_change_from_t0_J"],
            "combined_reference_storage_change_t10_J_NOT_CLOSED_ENERGY":doc["final"][
                "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],
            "native_interface_exterior_energy_balance_verified":False,
            "physical_validation":False,
            "NO_CFD_RERUN":True
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        print("C3D05_B_C14_MOLD_REFERENCE_INVENTORY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
