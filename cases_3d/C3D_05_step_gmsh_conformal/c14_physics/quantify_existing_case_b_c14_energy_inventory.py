#!/usr/bin/env python3
"""Real B C14 10s: SOURCE-REFERENCED metal sensible/latent-EQUIVALENT inventory.

Uses the existing, SHA-verified native CFD, 101-state postrun and original
REAL polyMesh volumes / volume-weighted alpha1 series. Pure Python, NO solver,
mesh changes, JMatPro or manufactured physical energy-balance assertions.

Sensible delta(t) [J] = rho_C14 * Cp_C14 * sum_i Vi*(Ti(t)-Ti(0)).
Latent-equivalent solid-complement delta(t) [J] =
    rho_C14 * L_C14 * sum_i Vi*(alpha_i(0)-alpha_i(t)).

Both quantities are numerical C14 reference INVENTORIES, not actual native
fvModel source-term integration or a closed interface/exterior energy budget.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
from array import array

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze_existing_case_b_c14 as native
import volume_weighted_existing_case_b_c14 as v

SOURCE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
POSTRUN=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01"
VOLUME=Path.home()/"OpenFOAM/C3D05_B_C14_VOLUME_WEIGHTED_PHASE_01"
OUT=Path.home()/"OpenFOAM/C3D05_B_C14_SENSIBLE_LATENT_EQUIVALENT_01"
CSV="C3D05_B_C14_METAL_SENSIBLE_LATENT_EQUIVALENT_101_STATES.csv"
JSON="C3D05_B_C14_METAL_SENSIBLE_LATENT_EQUIVALENT_REPORT.json"
MANIFEST="C3D05_B_C14_METAL_SENSIBLE_LATENT_EQUIVALENT_SHA256.json"
STATUS="C3D05_B_C14_REAL_METAL_C14_SENSIBLE_LATENT_EQUIVALENT_INVENTORY_NO_ENERGY_CLOSURE"
HEADERS=(
    "time_s","mean_metal_temperature_volume_weighted_K",
    "mean_liquid_fraction_volume_weighted",
    "mean_solid_complement_volume_weighted",
    "metal_sensible_change_from_t0_J",
    "metal_latent_equivalent_solid_complement_change_from_t0_J",
    "latent_equivalent_instantaneous_inventory_J",
    "metal_sensible_change_rate_saved_interval_W",
    "metal_latent_equivalent_change_rate_saved_interval_W",
)


def require(ok: bool,detail: str) -> None:
    if not ok:
        raise ValueError("CASE_B_C14_REAL_METAL_ENERGY_INVENTORY_BLOCKED: "+detail)


def sha(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(),
            "missing/symlinked native input "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as inp:
        while chunk:=inp.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def source_C14_constants() -> dict:
    native.physics.verify()
    doc=json.loads(native.physics.CONTRACT.read_text(encoding="utf-8"))
    params=doc["C14_exact_values"]
    rho=float(params["metal"]["rho_kg_m3"])
    cp=float(params["metal"]["Cp_J_kgK"])
    L=float(params["solidification"]["L_J_kg"])
    T0=float(params["metal"]["T_initial_K"])
    require(all(math.isfinite(x) and x>0 for x in (rho,cp,L,T0)),
            "bad original C14 baseline constants")
    return {"rho_metal_kg_m3":rho,"Cp_metal_J_kgK":cp,"L_metal_J_kg":L,
            "reference_initial_temperature_K":T0,
            "source_sha256":sha(native.physics.CONTRACT),
            "provenance":"ORIGINAL C14 archive, NOT QuickCup/JMatPro calibrated"}


def validate_weighted_archive(where:Path,case:Path,post:Path) -> list[dict]:
    require(where.is_dir() and not where.is_symlink() and where.name==VOLUME.name,
            "requires original completed 101-state REAL cell-volume analysis")
    archive=json.loads((where/v.JSON_NAME).read_text(encoding="utf-8"))
    manifest=json.loads((where/v.SHA_NAME).read_text(encoding="utf-8"))
    require(archive.get("status")==v.STATUS
            and archive.get("saved_states")==101
            and archive.get("volume_weighting_calculated_from_real_hex8_geometry") is True
            and archive.get("physical_validity_QuickCup_JMatPro") is False
            and archive.get("latent_energy_flux_balance_verified") is False,
            "source volume-weighted alpha1 report is not the real C14 numerical-only output")
    require(Path(archive["original_case_CFD_read_only"]).resolve()==case.resolve()
            and Path(archive["source_postrun_read_only"]).resolve()==post.resolve(),
            "archived volume-weighted report does not match original CASE B CFD")
    require(manifest.get("result_CSV_sha256")==sha(where/v.CSV_NAME)
            and manifest.get("result_JSON_sha256")==sha(where/v.JSON_NAME)
            and manifest.get("source_real_10s_stage_sha256")==sha(case/native.REPORT)
            and manifest.get("source_real_10s_log_sha256")==sha(case/native.LOG),
            "weighted series original SHA provenance mismatch")
    with (where/v.CSV_NAME).open(encoding="utf-8",newline="") as stream:
        rows=list(csv.DictReader(stream))
    require(len(rows)==101,"original weighted alpha1 series did not save 101 times")
    return rows


def storage_at_time(volumes:array, T:list[float], alpha:list[float],
                    T_initial:list[float],alpha_initial:list[float],
                    rho:float,Cp:float,L:float) -> dict:
    n=len(volumes)
    require(n>0 and n==len(T)==len(alpha)==len(T_initial)==len(alpha_initial),
            "temperature/phase and real cell volumes do not align")
    require(all(math.isfinite(x) and x>0 for x in T)
            and all(math.isfinite(x) and x>0 for x in T_initial),
            "nonpositive/nonfinite native absolute temperatures")
    require(all(math.isfinite(x) and -1e-8<=x<=1+1e-8 for x in alpha)
            and all(math.isfinite(x) and -1e-8<=x<=1+1e-8 for x in alpha_initial),
            "native C14 liquid fraction outside [0,1]")
    require(all(math.isfinite(x) and x>0 for x in volumes),
            "nonpositive or nonfinite native real cell volumes")
    require(all(math.isfinite(x) and x>0 for x in (rho,Cp,L)),
            "original C14 metal constants not physically positive")
    V=math.fsum(volumes)
    weighted_T=math.fsum(w*t for w,t in zip(volumes,T))/V
    weighted_liquid=math.fsum(w*a for w,a in zip(volumes,alpha))/V
    sensible=rho*Cp*math.fsum(w*(t-t0) for w,t,t0 in
                             zip(volumes,T,T_initial))
    latent_change=rho*L*math.fsum(w*(a0-a) for w,a,a0 in
                                 zip(volumes,alpha,alpha_initial))
    instantaneous_latent_solid_proxy=rho*L*math.fsum(
        w*(1-a) for w,a in zip(volumes,alpha))
    return {
        "mean_metal_temperature_volume_weighted_K":weighted_T,
        "mean_liquid_fraction_volume_weighted":weighted_liquid,
        "mean_solid_complement_volume_weighted":1-weighted_liquid,
        "metal_sensible_change_from_t0_J":sensible,
        "metal_latent_equivalent_solid_complement_change_from_t0_J":latent_change,
        "latent_equivalent_instantaneous_inventory_J":instantaneous_latent_solid_proxy
    }


def validate_existing_postrun(case:Path,post:Path)->tuple[list[tuple[float,str]],list[dict]]:
    require(case.name==SOURCE.name and post.name==POSTRUN.name,
            "source must be archived original Case B metal fluid/sand solid C14")
    stage,verified=native.validated_mesh_and_stage(case)
    require(stage["native_solver_run"] is True,"original 10s CFD not completed")
    require(sha(case/native.LOG)==stage["solver_log_sha256"],
            "archived original solver log SHA changed")
    require(post.is_dir() and not post.is_symlink(),
            "original first native postrun missing")
    postdoc=json.loads((post/native.JSON).read_text(encoding="utf-8"))
    manifest=json.loads((post/native.MANIFEST).read_text(encoding="utf-8"))
    require(postdoc.get("status")==native.STATUS
            and postdoc.get("native_CFD_solved_full_10s") is True
            and postdoc.get("phase_field_mean_is_cell_based_unweighted") is True,
            "original source 101-state postrun not native C14")
    require(manifest.get("analysis_csv_sha256")==sha(post/native.CSV)
            and manifest.get("analysis_json_sha256")==sha(post/native.JSON)
            and manifest.get("native_log_sha256")==sha(case/native.LOG)
            and manifest.get("native_stage_report_sha256")==sha(case/native.REPORT),
            "original archived native postrun SHA changed")
    with (post/native.CSV).open(encoding="utf-8",newline="") as fp:
        rows=list(csv.DictReader(fp))
    times=native.saved_times(case)
    require(len(times)==len(rows)==101
            and [x[0] for x in times]==[float(x["time_s"]) for x in rows],
            "original C14 archived time series does not align with native 101 snapshots")
    return times,rows


def run(case:Path,post:Path,weighted:Path,out:Path)->dict:
    case=case.expanduser().absolute()
    post=post.expanduser().absolute()
    weighted=weighted.expanduser().absolute()
    out=out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(),
            "output exists: refuse overwrite and preserve previous research")
    require(all(out!=p and out not in p.parents and p not in out.parents
                for p in (case,post,weighted)),
            "result must be separate from old CFD/analysis archives")
    coeff=source_C14_constants()
    times,rows=validate_existing_postrun(case,post)
    prior=validate_weighted_archive(weighted,case,post)
    require([x[0] for x in times]==[float(r["time_s"]) for r in prior],
            "weighted source 101 times differ from old native C14 times")
    # SHA-checked REAL points/faces/owner/neighbour directly from archived
    # native case, NOT a new mesh or a mass/volume guessed from mean cells.
    volumes,geometry=v.calculate_native_metal_cell_volumes(
        case/"constant/metal/polyMesh")
    assert len(volumes)==92200
    t0=times[0][1]
    first_T=native.source_reader.scalar_field_values(
        case/t0/"metal/T",92200)
    first_alpha=native.source_reader.scalar_field_values(
        case/t0/"metal/phaseChangeSource:alpha1",92200)
    require(math.isclose(math.fsum(first_T)/92200,
                         float(rows[0]["metal_T_mean_K"]),
                         abs_tol=1e-10,rel_tol=1e-10),
            "initial original C14 metal T differs from audited source")
    require(math.isclose(math.fsum(first_alpha)/92200,
                         float(rows[0]["alpha1_mean"]),
                         abs_tol=1e-10,rel_tol=1e-10),
            "initial original C14 alpha1 differs from audited source")
    series=[]
    for i,((t,label),audited,old_weight) in enumerate(zip(times,rows,prior),1):
        T=native.source_reader.scalar_field_values(
            case/label/"metal/T",92200)
        a=native.source_reader.scalar_field_values(
            case/label/"metal/phaseChangeSource:alpha1",92200)
        require(math.isclose(math.fsum(T)/92200,
                             float(audited["metal_T_mean_K"]),
                             abs_tol=1e-8,rel_tol=1e-10)
                and math.isclose(math.fsum(a)/92200,
                                 float(audited["alpha1_mean"]),
                                 abs_tol=1e-10,rel_tol=1e-10),
                "native intermediate field changed from audited saved state t="+label)
        record=storage_at_time(volumes,T,a,first_T,first_alpha,
                               coeff["rho_metal_kg_m3"],
                               coeff["Cp_metal_J_kgK"],
                               coeff["L_metal_J_kg"])
        require(math.isclose(
                    record["mean_liquid_fraction_volume_weighted"],
                    float(old_weight["mean_liquid_fraction_volume_weighted"]),
                    rel_tol=1e-11,abs_tol=1e-11),
                "weighted alpha from native geometry disagrees with 8/8-tested archive t="+label)
        if series:
            dt=t-series[-1]["time_s"]
            require(dt>0,"native saved times not increasing")
            dQ=(record["metal_sensible_change_from_t0_J"]-
                series[-1]["metal_sensible_change_from_t0_J"])
            dL=(record["metal_latent_equivalent_solid_complement_change_from_t0_J"]-
                series[-1]["metal_latent_equivalent_solid_complement_change_from_t0_J"])
            record["metal_sensible_change_rate_saved_interval_W"]=dQ/dt
            record["metal_latent_equivalent_change_rate_saved_interval_W"]=dL/dt
        else:
            record["metal_sensible_change_rate_saved_interval_W"]=None
            record["metal_latent_equivalent_change_rate_saved_interval_W"]=None
        series.append({"time_s":t,**record})
        if i==1 or i%10==0 or i==len(times):
            print(f"C3D05_B_METAL_C14_INVENTORY_READONLY: {i}/{len(times)} "
                  f"native states; t={t:g}s; NOT_ENERGY_BALANCE; NO_CFD",flush=True)
    require(math.isclose(series[0]["metal_sensible_change_from_t0_J"],0,abs_tol=1e-8)
            and math.isclose(
                series[0]["metal_latent_equivalent_solid_complement_change_from_t0_J"],
                0,abs_tol=1e-8),
            "initial energy inventory difference not zero")
    final=series[-1]
    result={
        "schema":"C3D05_B_C14_REAL_10S_METAL_REFERENCE_INVENTORY_V1",
        "status":STATUS,
        "reference_C14_metal_constants":coeff,
        "real_native_metal_hex8_geometry":geometry,
        "real_native_archive_used":str(case),
        "real_native_101_state_postrun_used":str(post),
        "real_native_101_state_volume_weighted_phase_used":str(weighted),
        "nStates":len(series),
        "start_s":series[0]["time_s"],
        "end_s":final["time_s"],
        "initial":series[0],
        "final":final,
        "absolute_energy_stored_J_computed":False,
        "native_solver_latent_fvModels_integral_computed":False,
        "solidification_heat_actually_released_J_verified":False,
        "metal_sand_exterior_energy_balance_verified":False,
        "mass_or_momentum_flux_accounting_verified":False,
        "material_properties_JMatPro_QuickCup_calibrated":False,
        "mesh_and_time_step_convergence":False,
        "notes":[
            "rho_C14 Cp_C14 sum Vi*(T(t)-T(0)) is a REFERENCE metal sensible difference, not full OpenFOAM enthalpy conservation.",
            "rho_C14 L_C14 sum Vi*(alpha(0)-alpha(t)) is a MODEL LATENT-EQUIVALENT phase-change proxy, NOT native fvModel integrated latent heat release.",
            "A positive latent proxy is not a measured transfer of energy across metal-to-mold interface; do not sum with sand heating or claim closure.",
            "Closed energy conservation needs time-resolved native enthalpy source, metal-mold interface and exterior fluxes, other terms and spatial/time convergence.",
            "Model C14 rho/Cp/L are constant historical inputs, not calibrated for the eight real QuickCup alloys.",
            "Original research CFD, 101 postrun fields and previous weighted analysis are never overwritten or recalculated with foamMultiRun."
        ]
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(out.parent),
                                     prefix="."+out.name+".staging.") as folder:
        candidate=Path(folder)/"candidate"
        candidate.mkdir()
        with (candidate/CSV).open("x",encoding="utf-8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(series)
        (candidate/JSON).write_text(json.dumps(
            result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        (candidate/MANIFEST).write_text(json.dumps({
            "source_C14_contract_SHA256":coeff["source_sha256"],
            "source_native_CFD_report_SHA256":sha(case/native.REPORT),
            "source_native_CFD_log_SHA256":sha(case/native.LOG),
            "source_original_postrun_CSV_SHA256":sha(post/native.CSV),
            "source_original_volume_weighted_CSV_SHA256":sha(weighted/v.CSV_NAME),
            "result_CSV_SHA256":sha(candidate/CSV),
            "result_JSON_SHA256":sha(candidate/JSON),
            "archived_CFD_and_existing_analyses_never_modified":True
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "destination appeared concurrently; no overwrite permitted")
        candidate.rename(out)
    return result


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",type=Path,default=SOURCE)
    parser.add_argument("--postrun",type=Path,default=POSTRUN)
    parser.add_argument("--weighted",type=Path,default=VOLUME)
    parser.add_argument("--out",type=Path,default=OUT)
    p=parser.parse_args()
    try:
        result=run(p.case,p.postrun,p.weighted,p.out)
        print(json.dumps({
            "status":result["status"],"out":str(p.out),
            "states":result["nStates"],
            "reference_metal_sensible_delta_from_t0_J":
                result["final"]["metal_sensible_change_from_t0_J"],
            "modeled_latent_equivalent_solid_change_from_t0_J":
                result["final"]["metal_latent_equivalent_solid_complement_change_from_t0_J"],
            "final_alpha1_liquid_volume_weighted":
                result["final"]["mean_liquid_fraction_volume_weighted"],
            "actual_CFD_native_fvModel_source_integral_computed":False,
            "interfacial_external_energy_balance_validated":False,
            "experimental_validation":False,
            "NO_NEW_CFD":True,
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        print("CASE_B_C14_REAL_METAL_ENERGY_INVENTORY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
