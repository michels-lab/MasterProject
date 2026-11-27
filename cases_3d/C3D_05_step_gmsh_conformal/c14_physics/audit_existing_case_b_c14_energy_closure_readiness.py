#!/usr/bin/env python3
"""C3D05-B C14 authentic 101-state source-term AVAILABILITY + q quadrature audit.

Uses the already computed, SHA-verified real B C14 F14 fluid/solid conductive
q(t), metal/mold reference storage and their published join. Reads only the
archived CFD's existing files; it never executes OpenFOAM or rewrites a CFD
case. Reports regional conductive-vs-storage PARTIAL differences, saved-time
trapezoid sensitivity, and the field availability for a future true h/e,
latent-source, advection/work and boundary transport conservation audit.

A matching 0.1s saved-snapshot quadrature is NOT the 0.001s solver dt
integration. The numerical reference storage is NOT an exact solver enthalpy.
NO number produced here is a validated conservation residual / heat loss.
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

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze_existing_case_b_c14 as native
import analyze_existing_case_b_c14_native_flux as qmod
import compare_existing_case_b_c14_native_q_and_storage as joined
import run_existing_case_b_c14_native_flux as qrun

JOIN=joined.OUTPUT
Q=joined.QDIR
STORAGE=joined.STORAGE
CASE=native.DEFAULT_CASE
OUT=Path.home()/"OpenFOAM/C3D05_B_C14_ENERGY_TERMS_READINESS_01"
CSV="C3D05_B_C14_SAVED_TIME_Q_QUADRATURE_SENSITIVITY_NOT_SOLVER_DT.csv"
JSON="C3D05_B_C14_REAL_ENERGY_TERM_COVERAGE_AND_PARTIAL_DIAGNOSTICS.json"
MANIFEST="C3D05_B_C14_ENERGY_READINESS_SHA256.json"
STATUS="C3D05_B_C14_REAL_C14_ENERGY_TERM_COVERAGE_AND_SAVED_Q_QUADRATURE_NOT_CLOSURE"
QKEYS=(
    "metal_to_mold_q_out_W","mold_to_metal_q_out_W",
    "interface_sum_outward_W","metalTop_q_out_W",
    "moldOuterUnclassified_q_out_W","external_total_q_out_W"
)
FIELDS={
    "metal_T":"metal/T",
    "metal_U":"metal/U",
    "metal_h":"metal/h",
    "metal_he":"metal/he",
    "metal_rho":"metal/rho",
    "metal_phi":"metal/phi",
    "metal_p":"metal/p",
    "metal_p_rgh":"metal/p_rgh",
    "metal_alpha1":"metal/phaseChangeSource:alpha1",
    "mold_T":"mold/T",
    "mold_e":"mold/e",
    "mold_he":"mold/he",
    "mold_rho":"mold/rho",
}
ESSENTIAL=("metal_T","metal_alpha1","mold_T")


def require(ok:bool, reason:str)->None:
    if not ok:
        raise ValueError("C3D05_B_C14_REAL_ENERGY_TERMS_READINESS_BLOCKED: "+reason)


def sha(path:Path)->str:
    require(path.is_file() and not path.is_symlink(),
            "original source or evidence file unavailable or symlinked: "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as src:
        while data:=src.read(1024*1024):
            h.update(data)
    return h.hexdigest()


def independent_output(out:Path, sources)->Path:
    """Resolve ancestor aliases before permitting any output creation."""
    raw=out.expanduser().absolute()
    require(not raw.is_symlink(),"destination is a symlink")
    out=raw.resolve()
    roots=[p.expanduser().resolve(strict=True) for p in sources]
    require(not out.exists() and all(
        out!=p and out not in p.parents and p not in out.parents for p in roots),
        "new results must be fully separate from source CFD and old analyses")
    return out


def validate_saved_axis(times):
    require(len(times)==101 and all(
        math.isfinite(t) and math.isclose(t,i*.1,rel_tol=0,abs_tol=1e-8)
        for i,(t,label) in enumerate(times)),
        "original saved 101-time CFD axis absent or unordered")
    require(len({label for _,label in times})==101 and all(
        Path(label).name==label and label not in (".","..") and
        math.isclose(float(label),t,rel_tol=0,abs_tol=1e-8)
        for t,label in times), "invalid or duplicate native time labels")


def field_coverage(case:Path,times:list[tuple[float,str]])->dict:
    """Counts ORIGINAL time/region paths; never invents missing h/e/phi fields."""
    require(case.is_dir() and not case.is_symlink(),"original CFD source absent")
    validate_saved_axis(times)
    data={}
    for name,rel in FIELDS.items():
        present=[]
        sample=[]
        for t,label in times:
            source=case/label/rel
            has=source.is_file() and not source.is_symlink()
            if has:
                present.append(t)
            elif len(sample)<4:
                sample.append(label)
        data[name]={
            "original_relative_field":rel,
            "saved_states_with_field":len(present),
            "expected_states":101,
            "all_101_states_available":len(present)==101,
            "first_saved_time_s":present[0] if present else None,
            "last_saved_time_s":present[-1] if present else None,
            "sample_missing_time_labels":sample,
            "values_not_loaded_or_guessed":True,
        }
    require(all(data[k]["all_101_states_available"] for k in ESSENTIAL),
            "essential original C14 real metal/mold T and alpha fields missing")
    return data


def quadrature_sensitivity(rows:list[dict])->list[dict]:
    """Saved q samples at 0.1s vs decimated 0.2,0.5,1.0s only.

    It does not evaluate, bound, estimate or replace the 0.001s true CFD
    time-step integrated fvModel, boundary q or thermal energy equation.
    """
    require(len(rows)==101,
            "requires 101 real saved native C14 q states")
    for i,r in enumerate(rows):
        t=float(r["time_s"])
        require(math.isclose(t,i*.1,rel_tol=0,abs_tol=1e-8),
                "100ms original saved time axis missing")
        for key in QKEYS:
            require(math.isfinite(float(r[key])),
                    "nonfinite native q sampled term "+key)
    coarse={}
    for skip in (1,2,5,10):
        subset=rows[::skip]
        require(math.isclose(float(subset[-1]["time_s"]),10,abs_tol=1e-8),
                "subsampling omitted final 10s boundary")
        traces=[{"time_s":float(row["time_s"]),
                 **{key:float(row[key]) for key in QKEYS}} for row in subset]
        d={
            "saved_time_step_s":skip*.1,
            "count_saved_snapshots":len(subset),
            "source_is_101_real_saved_snapshots":True,
            "not_original_solver_dt_integral":True,
        }
        for key in QKEYS:
            d[key.replace("_W","_J")+"_SAVED_TIME_TRAPEZOID"] = (
                qmod.signed_interval_integral(traces,key))
        coarse[skip]=d
    baseline=coarse[1]
    for skip,row in coarse.items():
        for key in QKEYS:
            name=key.replace("_W","_J")+"_SAVED_TIME_TRAPEZOID"
            row[name+"_difference_vs_0_1s_J"]=row[name]-baseline[name]
            if skip==1:
                require(math.isclose(row[name+"_difference_vs_0_1s_J"],0,
                                      abs_tol=1e-10), "baseline difference !=0")
    return [coarse[k] for k in (1,2,5,10)]


def per_region_reference_diagnostic(last:dict)->dict:
    """Reference storage + all conductive boundary powers per region.

    These are intentionally NOT conservation residuals (source, advection,
    exterior boundary radiation etc. missing). No equality is expected.
    """
    v=lambda key:float(last[key])
    required=(
        "metal_sensible_change_from_t0_J",
        "metal_liquid_latent_content_change_from_t0_J",
        "mold_sensible_change_from_t0_J",
        "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY",
        joined.CUM_COLS["metal_to_mold_q_out_W"],
        joined.CUM_COLS["mold_to_metal_q_out_W"],
        joined.CUM_COLS["metalTop_q_out_W"],
        joined.CUM_COLS["moldOuterUnclassified_q_out_W"],
        joined.CUM_COLS["interface_sum_outward_W"],
        joined.CUM_COLS["external_total_q_out_W"],
    )
    require(all(k in last and math.isfinite(v(k)) for k in required),
            "native source join missing/nonfinite C14 thermal term")
    metal_stored=v("metal_sensible_change_from_t0_J")+v(
        "metal_liquid_latent_content_change_from_t0_J")
    mold_stored=v("mold_sensible_change_from_t0_J")
    metal_conductive=v(joined.CUM_COLS["metal_to_mold_q_out_W"])+v(
        joined.CUM_COLS["metalTop_q_out_W"])
    mold_conductive=v(joined.CUM_COLS["mold_to_metal_q_out_W"])+v(
        joined.CUM_COLS["moldOuterUnclassified_q_out_W"])
    regional={
        "metal":{
            "reference_storage_change_J":metal_stored,
            "outward_conductive_q_saved_trapezoid_J":metal_conductive,
            "sum_reference_storage_plus_outward_conduction_J_NOT_ENERGY_RESIDUAL":
                metal_stored+metal_conductive,
        },
        "mold":{
            "reference_storage_change_J":mold_stored,
            "outward_conductive_q_saved_trapezoid_J":mold_conductive,
            "sum_reference_storage_plus_outward_conduction_J_NOT_ENERGY_RESIDUAL":
                mold_stored+mold_conductive,
        },
    }
    regional["summed_region_partials_including_internal_q_J_NOT_ENERGY_RESIDUAL"]=(
        regional["metal"][
            "sum_reference_storage_plus_outward_conduction_J_NOT_ENERGY_RESIDUAL"]+
        regional["mold"][
            "sum_reference_storage_plus_outward_conduction_J_NOT_ENERGY_RESIDUAL"]
    )
    regional["internal_interface_signed_q_saved_trapezoid_J"]=v(
        joined.CUM_COLS["interface_sum_outward_W"])
    regional["domain_exterior_only_reference_comparison_J_NOT_ENERGY_RESIDUAL"]=(
        metal_stored+mold_stored+v(joined.CUM_COLS["external_total_q_out_W"])
    )
    require(math.isclose(metal_stored+mold_stored,
                         v("combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"),
                         abs_tol=1e-5,rel_tol=1e-8),
            "region reference storage sum does not match original archived values")
    require(math.isclose(
        regional["summed_region_partials_including_internal_q_J_NOT_ENERGY_RESIDUAL"],
        regional["domain_exterior_only_reference_comparison_J_NOT_ENERGY_RESIDUAL"]+
        regional["internal_interface_signed_q_saved_trapezoid_J"],
        abs_tol=1e-5,rel_tol=1e-8),
        "original bilateral internal q signed cancellation is inconsistent")
    return regional


def verify_archives(join:Path,q:Path,storage:Path,case:Path)->tuple[list[dict],dict]:
    join=join.expanduser().absolute()
    q=q.expanduser().absolute()
    storage=storage.expanduser().absolute()
    case=case.expanduser().absolute()
    require(join.is_dir() and not join.is_symlink() and join.name==JOIN.name,
            "must use original complete source-C14 q-storage join")
    require(case.is_dir() and not case.is_symlink() and case.name==CASE.name,
            "must use original existing 10s CFD, no copies or regenerated CFD")
    jr=json.loads((join/joined.JSON).read_text(encoding="utf-8"))
    jm=json.loads((join/joined.MANIFEST).read_text(encoding="utf-8"))
    require(jr.get("status")==joined.STATUS and jr.get("original_saved_time_count")==101,
            "original q vs reference storage join is not fully verified 101 times")
    require(jr.get("q_trapezoid_integral_not_native_solver_dt_integral") is True
            and jr.get("valid_for_physically_calibrated_energy_conservation") is False,
            "original q-storage join wrongly claims closed conservation")
    require(jm.get("joined_report_SHA256")==sha(join/joined.JSON)
            and jm.get("joined_reference_101_CSV_SHA256")==sha(join/joined.CSV),
            "published original 101-state q-storage join SHA mismatch")
    qr,ss,provenance=joined.verify_sources(q,storage)
    require(provenance["original_CFD_stage_SHA256"]==
            jm.get("original_CFD_stage_SHA256")
            and provenance["original_CFD_log_SHA256"]==
            jm.get("original_CFD_log_SHA256"),
            "join, q and storage do not originate from exactly same source CFD")
    require(provenance["original_CFD_stage_SHA256"]==
            sha(case/native.REPORT) and provenance["original_CFD_log_SHA256"]==
            sha(case/native.LOG),
            "real original C14 CFD files changed or source provenance wrong")
    checked=joined.analysis_rows(qr,ss)
    require(len(checked)==101,
            "original q/storage old archives could not independently rejoin")
    with (join/joined.CSV).open(encoding="utf-8",newline="") as fp:
        published=list(csv.DictReader(fp))
    require(len(published)==101,
            "published 101 snapshots missing")
    for old,new in zip(published,checked):
        for key in joined.CSV_KEYS:
            require(key in old and math.isclose(
                float(old[key]),float(new[key]),abs_tol=1e-7,rel_tol=1e-8),
                "published 101-time q/storage join mismatches independently "
                "computed old immutable q and storage fields: "+key)
    return checked,{
        "joined_101_CSV_SHA256":sha(join/joined.CSV),
        "joined_report_SHA256":sha(join/joined.JSON),
        "original_101_state_q_CSV_SHA256":provenance["original_q_101_csv_SHA256"],
        "original_101_state_storage_CSV_SHA256":provenance["original_storage_101_csv_SHA256"],
        "original_CFD_log_SHA256":provenance["original_CFD_log_SHA256"],
        "original_CFD_stage_SHA256":provenance["original_CFD_stage_SHA256"],
    }


def run(join:Path,q:Path,storage:Path,case:Path,out:Path)->dict:
    paths=[p.expanduser().absolute() for p in (join,q,storage,case)]
    out=independent_output(out,paths)
    records,provenance=verify_archives(*paths)
    source_case=paths[-1]
    original,_=native.validated_mesh_and_stage(source_case)
    times=native.saved_times(source_case)
    require(len(times)==101,"source CFD original 101 saved time states incomplete")
    fields=field_coverage(source_case,times)
    scheme=source_case/"constant/metal/fvModels"
    require(scheme.is_file() and not scheme.is_symlink(),
            "actual original C14 fvModels source missing/symlinked")
    source_text=scheme.read_text(encoding="utf-8")
    require("solidificationMeltingSource" in source_text
            and "energy          h;" in source_text
            and "cellZone        metal;" in source_text,
            "original source is not exact C14 h-based all-metal solidificationMeltingSource")
    boundary_names=(
        ("metal","metalTop"),("metal","metal_to_mold"),
        ("mold","mold_to_metal"),("mold","moldOuterUnclassified")
    )
    bc_files={}
    for region,patch in boundary_names:
        path=source_case/"0"/region/"T"
        require(path.is_file() and not path.is_symlink(),
                "C14 source initial thermal boundary field absent "+str(path))
        contents=path.read_text(encoding="utf-8")
        require(patch in contents,
                "Original C14 thermal patch missing "+region+"/"+patch)
        bc_files[region+"/"+patch]={
            "source_initial_T_field_SHA256":sha(path),
            "patch_name_confirmed":True,
            "source_thermal_BC_types_observed":
                sorted([kind for kind in
                ("externalWallHeatFluxTemperature","coupledTemperature",
                 "externalTemperature","fixedValue")
                if kind in contents]),
            "potential_radiation_model_mentions_emissivity":
                "emissivity" in contents,
            "separate_convection_radiation_flux_integral_not_verified":True,
        }
    sensitivity=quadrature_sensitivity(records)
    regional=per_region_reference_diagnostic(records[-1])
    report={
        "schema":"C3D05_B_C14_F14_REAL_ENERGY_TERMS_READINESS_V1",
        "status":STATUS,
        "source_original_C14_10s_CFD_read_only":str(source_case),
        "source_101_native_q_storage_join_read_only":str(paths[0]),
        "source_SHA256":provenance,
        "source_C14_fvModels_SHA256":sha(scheme),
        "source_C14_energy_h_solidification_model_declaration_verified":True,
        "saved_states":len(records),
        "q_native_101_times_success":True,
        "source_fields_availability":fields,
        "original_thermal_BC_dictionary_source_evidence":bc_files,
        "region_reference_storage_plus_saved_time_conduction_partial_diagnostics":
            regional,
        "saved_time_trapezoid_subsampling_sensitivity":sensitivity,
        "saved_time_quadrature_at_0_1s_is_NOT_solver_0_001s_flux_integral":True,
        "no_native_fvModels_internal_time_integral":True,
        "no_original_enthalpy_transport_pressure_work_source_integral":True,
        "no_separately_integrated_radiation_convection_boundary_terms":True,
        "overall_F14_solver_energy_conservation_verified":False,
        "C14_reference_properties_not_JMatPro_or_QuickCup_calibrated":True,
        "severe_nonorthogonal_geometry_and_dt_sensitivity_unresolved":True,
        "NO_SOLVER_NO_POSTRUN_Q_REEXECUTION":True,
        "notes":[
            "All comparisons are source-only reference inventories and patch conductive flux; no physical leak or conservation residual is computed.",
            "The source uses metal fluid sensibleEnthalpy h and solid mold sensibleInternalEnergy e.",
            "C14 latent h source fvModels was identified from exact original dictionary, NOT integrated from native solver energy equation.",
            "Field coverage checks existence, not calibrated thermodynamic fidelity or physical values.",
            "Quadrature sensitivity at saved times 0.1/0.2/0.5/1.0s cannot bound error against original 0.001s CFD time stepping.",
            "Original q-only shadow has separate interpolate(kappa) harmonic in COPIED mold fvSchemes; source CFD not changed.",
        ]
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=str(out.parent),prefix="."+out.name+".staging.") as staging:
        pending=Path(staging)/"candidate"
        pending.mkdir()
        columns=list(sensitivity[0])
        with (pending/CSV).open("x",encoding="utf-8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=columns)
            writer.writeheader()
            writer.writerows(sensitivity)
        (pending/JSON).write_text(json.dumps(
            report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        (pending/MANIFEST).write_text(json.dumps({
            "source_original_CFD_stage_SHA256":provenance["original_CFD_stage_SHA256"],
            "source_original_CFD_solver_log_SHA256":provenance["original_CFD_log_SHA256"],
            "source_join_101_CSV_SHA256":provenance["joined_101_CSV_SHA256"],
            "source_join_report_SHA256":provenance["joined_report_SHA256"],
            "source_original_C14_fvModels_SHA256":sha(scheme),
            "q_quadrature_sensitivity_CSV_SHA256":sha(pending/CSV),
            "energy_terms_readiness_JSON_SHA256":sha(pending/JSON),
            "NO_CFD_REEXECUTION_AND_NO_SOURCE_MUTATION":True,
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "another process created destination; no overwrites")
        pending.rename(out)
    return report


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--join",type=Path,default=JOIN)
    parser.add_argument("--q",type=Path,default=Q)
    parser.add_argument("--storage",type=Path,default=STORAGE)
    parser.add_argument("--case",type=Path,default=CASE)
    parser.add_argument("--out",type=Path,default=OUT)
    args=parser.parse_args()
    try:
        doc=run(args.join,args.q,args.storage,args.case,args.out)
        print(json.dumps({
            "status":doc["status"],
            "out":str(args.out),
            "saved_states":doc["saved_states"],
            "source_C14_h_based_latent_fvModel_declared":True,
            "field_availability_101_states":{
                name:info["saved_states_with_field"]
                for name,info in doc["source_fields_availability"].items()},
            "per_region_partial_NOT_energy_residual":
                doc["region_reference_storage_plus_saved_time_conduction_partial_diagnostics"],
            "subsampled_saved_q_trapezoids_summary_J_NOT_solver_dt":
                [{
                    "sample_interval_s":r["saved_time_step_s"],
                    "snapshots":r["count_saved_snapshots"],
                    "external_J":r["external_total_q_out_J_SAVED_TIME_TRAPEZOID"],
                    "external_vs_0_1s_J":r[
                        "external_total_q_out_J_SAVED_TIME_TRAPEZOID_difference_vs_0_1s_J"],
                } for r in doc["saved_time_trapezoid_subsampling_sensitivity"]],
            "true_energy_conservation_verified":False,
            "NO_CFD_RERUN":True,
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,OverflowError) as exc:
        print("C3D05_B_C14_ENERGY_READINESS_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
