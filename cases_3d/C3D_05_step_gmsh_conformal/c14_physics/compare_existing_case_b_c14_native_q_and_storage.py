#!/usr/bin/env python3
"""C3D05 B C14 genuine real saved 101-state q versus real reference storage.

Source only, NO solver and NO CFD/old analysis edits. Validates SHA256 of BOTH
original native fluid/solid conductive q extraction and 101-state metal/mold
reference storage. Synchronizes 101 times and reports time trapezoids of four
native q patches along with independent model reference-energy inventories.

This is NOT an energy-balance solver, 'heat loss' / conservation 'residual',
or a true fvModel/radiation/advection/incremental solver-dt flux integral.
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
import analyze_existing_case_b_c14_native_flux as qmod
import run_existing_case_b_c14_native_flux as qr
import quantify_existing_case_b_c14_mold_and_combined_inventory as s

QDIR=Path.home()/"OpenFOAM/C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01"
STORAGE=Path.home()/"OpenFOAM/C3D05_B_C14_MOLD_COMBINED_REFERENCE_STORAGE_01"
OUTPUT=Path.home()/"OpenFOAM/C3D05_B_C14_Q_VS_REFERENCE_STORAGE_01"
CSV="C3D05_B_C14_101_TIME_Q_VS_STORAGE_REFERENCE_ONLY.csv"
JSON="C3D05_B_C14_Q_VS_STORAGE_NOT_ENERGY_CLOSURE_REPORT.json"
MANIFEST="C3D05_B_C14_Q_VS_STORAGE_SHA256.json"
STATUS="C3D05_B_C14_101_SAVED_Q_VS_REFERENCE_STORAGE_DIAGNOSTIC_NOT_ENERGY_CLOSURE"
Q_COLS=(
    "metal_to_mold_q_out_W","mold_to_metal_q_out_W",
    "interface_sum_outward_W","metalTop_q_out_W",
    "moldOuterUnclassified_q_out_W","external_total_q_out_W",
)
STORAGE_COLS=(
    "mold_sensible_change_from_t0_J",
    "metal_sensible_change_from_t0_J",
    "metal_liquid_latent_content_change_from_t0_J",
    "metal_latent_solid_equivalent_increase_from_t0_J",
    "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY",
)
INTEGRALS=(
    "metal_to_mold_q_out_W",
    "mold_to_metal_q_out_W",
    "interface_sum_outward_W",
    "metalTop_q_out_W",
    "moldOuterUnclassified_q_out_W",
    "external_total_q_out_W",
)
CUM_COLS={key:"saved_trapezoid_"+key.replace("_W","_J")+"_NOT_SOLVER_DT_INTEGRAL"
          for key in INTEGRALS}
CSV_KEYS=("time_s",)+STORAGE_COLS+Q_COLS+tuple(CUM_COLS.values())+(
    "reference_storage_change_plus_external_conduction_trapezoid_J_NOT_ENERGY_RESIDUAL",
    "interface_mismatch_relative_over_instantaneous_gross",
)


def require(ok:bool,detail:str)->None:
    if not ok:
        raise ValueError("C3D05_B_C14_Q_STORAGE_JOIN_BLOCKED: "+detail)


def sha(path:Path)->str:
    require(path.is_file() and not path.is_symlink(),
            "original source file unavailable or symlink: "+str(path))
    digest=hashlib.sha256()
    with path.open("rb") as fp:
        while piece:=fp.read(1024*1024):
            digest.update(piece)
    return digest.hexdigest()


def read_csv(path:Path,required:tuple[str,...])->list[dict]:
    require(path.is_file() and not path.is_symlink(),
            "missing source 101-state CSV: "+str(path))
    with path.open("r",encoding="utf-8",newline="") as fp:
        reader=csv.DictReader(fp)
        require(reader.fieldnames is not None and
                set(required).issubset(set(reader.fieldnames)),
                "original source CSV is missing needed fields "+str(path))
        return list(reader)


def parse101(rows:list[dict],needed:tuple[str,...],label:str)->list[dict]:
    require(len(rows)==101,label+" must contain exactly 101 saved states")
    parsed=[]
    for i,row in enumerate(rows):
        require(all(col in row and row[col] is not None for col in needed),
                label+" missing numeric source column")
        values={col:float(row[col]) for col in needed}
        require(all(math.isfinite(x) for x in values.values()),
                label+" has a nonfinite native number")
        t=values["time_s"]
        require(math.isclose(t,i*.1,rel_tol=0,abs_tol=1e-8),
                label+" native saved-time axis differs from 0..10s")
        values["time_s"]=round(i*.1,10)
        parsed.append(values)
    return parsed


def analysis_rows(q_rows:list[dict],stored_rows:list[dict])->list[dict]:
    """101 saved q(t) + source reference-energy deltas with guarded signs.

    Does NOT infer missing energy as leakage or a physical residual; the
    diagnostic is an intentionally incomplete accounting expression.
    """
    q=parse101(q_rows,("time_s",)+Q_COLS+
               ("interface_relative_instantaneous_mismatch_over_gross",),
               "original fluid/solid native q")
    stored=parse101(stored_rows,("time_s",)+STORAGE_COLS,
                    "original metal+mold reference inventory")
    accum={key:0.0 for key in INTEGRALS}
    records=[]
    for i,(qq,ss) in enumerate(zip(q,stored)):
        t=qq["time_s"]
        require(math.isclose(t,ss["time_s"],rel_tol=0,abs_tol=1e-9),
                "q and reference storage native time axis diverged")
        require(math.isclose(
            qq["interface_sum_outward_W"],
            qq["metal_to_mold_q_out_W"]+qq["mold_to_metal_q_out_W"],
            rel_tol=1e-9,abs_tol=1e-7),
            "native interface q sign/integral is inconsistent")
        require(math.isclose(
            qq["external_total_q_out_W"],
            qq["metalTop_q_out_W"]+qq["moldOuterUnclassified_q_out_W"],
            rel_tol=1e-9,abs_tol=1e-7),
            "native exterior q is inconsistent")
        require(math.isclose(
            ss["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],
            ss["mold_sensible_change_from_t0_J"]+
            ss["metal_sensible_change_from_t0_J"]+
            ss["metal_liquid_latent_content_change_from_t0_J"],
            rel_tol=1e-9,abs_tol=1e-6),
            "original source reference-storage sign/inventory inconsistent")
        require(math.isclose(
            ss["metal_liquid_latent_content_change_from_t0_J"],
            -ss["metal_latent_solid_equivalent_increase_from_t0_J"],
            rel_tol=1e-9,abs_tol=1e-6),
            "C14 model latent equivalent cannot be counted twice")
        instantaneous=qq["interface_relative_instantaneous_mismatch_over_gross"]
        expected_den=(abs(qq["metal_to_mold_q_out_W"])+
                      abs(qq["mold_to_metal_q_out_W"]))
        require(0<=instantaneous<=1 and math.isclose(
            instantaneous,
            abs(qq["interface_sum_outward_W"])/expected_den
            if expected_den>0 else 0,
            abs_tol=1e-9,rel_tol=1e-7),
            "native interface mismatch indicator inconsistent")
        if i:
            dt=t-q[i-1]["time_s"]
            require(dt>0,"original saved t is not increasing")
            for name in INTEGRALS:
                # Small roundoff changes are fine; this is a saved 0.1 s
                # trapezoid, NEVER the 0.001s solver-integrated q.
                accum[name]+=0.5*dt*(q[i-1][name]+qq[name])
        record={"time_s":t}
        record.update({key:ss[key] for key in STORAGE_COLS})
        record.update({key:qq[key] for key in Q_COLS})
        record.update({name:accum[key] for key,name in CUM_COLS.items()})
        record["reference_storage_change_plus_external_conduction_trapezoid_J_NOT_ENERGY_RESIDUAL"]=(
            ss["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"]+
            accum["external_total_q_out_W"]
        )
        record["interface_mismatch_relative_over_instantaneous_gross"]=instantaneous
        records.append(record)
    require(math.isclose(records[0][
        "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],0,
        abs_tol=1e-7),"original t0 reference storage not zero")
    return records


def verify_sources(qdir:Path,store:Path)->tuple[list[dict],list[dict],dict]:
    qdir=qdir.expanduser().absolute()
    store=store.expanduser().absolute()
    require(qdir.is_dir() and not qdir.is_symlink() and qdir.name==QDIR.name,
            "must use genuine native original Case B 101-time fluid-solid q archive")
    require(store.is_dir() and not store.is_symlink() and store.name==STORAGE.name,
            "must use actual original Case B 101-state reference-storage archive")
    qrpt=json.loads((qdir/qr.REPORT).read_text(encoding="utf-8"))
    qm=json.loads((qdir/qr.MANIFEST).read_text(encoding="utf-8"))
    srpt=json.loads((store/s.JSON).read_text(encoding="utf-8"))
    sm=json.loads((store/s.MANIFEST).read_text(encoding="utf-8"))
    require(qrpt.get("status")==qmod.STATUS
            and qrpt.get("stored_time_count")==101
            and qrpt.get("native_patch_count")==4
            and qrpt.get("native_interface_faces_each")==12636
            and qrpt.get("real_fluid_and_solid_heat_conduction_q_computed") is True
            and qrpt.get("overall_energy_conservation_verified") is False
            and qrpt.get("native_latent_fvModel_source_integral") is False,
            "original q archive not a qualified numerical-only F14 result")
    require(qrpt.get("per_face_geometry",{}).get(
                "interface_geometry_and_orientation_complete") is True
            and qrpt.get("per_face_geometry",{}).get(
                "matched_rounded_centres_at_1e_8_m")==12636,
            "original 12636-face native C14 interface geometry not audited")
    require(qrpt.get("q_only_shadow_fvSchemes_provenance",{}).get(
                "explicit_shadow_only_scheme")=="interpolate(kappa) harmonic;",
            "real q was not derived from isolated C14 harmonic q-only overlay")
    require(srpt.get("status")==s.STATUS
            and srpt.get("saved_states")==101
            and srpt.get("overall_sensible_latent_energy_conservation_verified") is False
            and srpt.get("metal_latent_liquid_content_delta_is_negative_solid_equivalent") is True,
            "reference-storage archive is not the original real C14 numerical-only record")
    require(qm.get("audited_report_SHA256")==sha(qdir/qr.REPORT)
            and qm.get("native_q_timeline_101_CSV_SHA256")==sha(qdir/qr.TIMELINE)
            and qm.get("native_integrated_101times_CSV_SHA256")==sha(qdir/qr.INTEGRALS)
            and qm.get("native_all_faces_t10_CSV_SHA256")==sha(qdir/qr.LAST_FACES)
            and sm.get("result_JSON_SHA256")==sha(store/s.JSON)
            and sm.get("result_CSV_SHA256")==sha(store/s.CSV),
            "original q or storage SHA manifests mismatch")
    require(qm.get("original_CFD_stage_SHA256")==
            sm.get("original_CFD_native_solver_report_SHA256")
            and qm.get("original_CFD_log_SHA256")==
            sm.get("original_CFD_native_solver_log_SHA256"),
            "q and reference storage not from identical original 10s C14 CFD")
    require(Path(qrpt["original_CFD_source_read_only"]).resolve()==
            Path(srpt["original_native_C14_run_readonly"]).resolve(),
            "source CFD paths disagree across the SHA-qualified archives")
    require(math.isclose(
        qrpt["signed_interface_sum_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL"],
        float(qrpt["signed_interface_sum_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL"]),
        rel_tol=0,abs_tol=0),
        "original interface signed heat flux not numeric")
    native_csv=read_csv(qdir/qr.TIMELINE,("time_s",)+Q_COLS+
                        ("interface_relative_instantaneous_mismatch_over_gross",))
    stored_csv=read_csv(store/s.CSV,("time_s",)+STORAGE_COLS)
    return native_csv,stored_csv,{
        "original_CFD_stage_SHA256":qm["original_CFD_stage_SHA256"],
        "original_CFD_log_SHA256":qm["original_CFD_log_SHA256"],
        "native_F14_q_report_SHA256":sha(qdir/qr.REPORT),
        "original_q_101_csv_SHA256":sha(qdir/qr.TIMELINE),
        "original_storage_report_SHA256":sha(store/s.JSON),
        "original_storage_101_csv_SHA256":sha(store/s.CSV),
        "q_shadow_harmonic_overlay_SHA256":qm["q_only_overlay_mold_fvSchemes_SHA256"],
        "native_q_10s_all_faces_SHA256":sha(qdir/qr.LAST_FACES)
    }


def run(qdir:Path,store:Path,out:Path)->dict:
    qdir=qdir.expanduser().absolute()
    store=store.expanduser().absolute()
    out=out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(),
            "output exists: no overwrites of previous analyses")
    require(all(out!=p and out not in p.parents and p not in out.parents
                for p in (qdir,store)),
            "new output must be separate from existing original q and storage")
    qrows,srows,provenance=verify_sources(qdir,store)
    combined=analysis_rows(qrows,srows)
    require(len(combined)==101,"101 original q/storage times did not join")
    qreport=json.loads((qdir/qr.REPORT).read_text(encoding="utf-8"))
    initial,final=combined[0],combined[-1]
    require(math.isclose(
        final[CUM_COLS["interface_sum_outward_W"]],
        float(qreport["signed_interface_sum_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL"]),
        abs_tol=1e-6,rel_tol=1e-8),
        "101-state independent interface q integral contradicts native q audit")
    require(math.isclose(
        final[CUM_COLS["external_total_q_out_W"]],
        float(qreport["signed_external_total_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL"]),
        abs_tol=1e-6,rel_tol=1e-8),
        "101-state independent exterior q integral contradicts native q audit")
    source_q_final=qreport["final"]
    require(all(math.isclose(final[key],float(source_q_final[key]),
                abs_tol=1e-6,rel_tol=1e-8) for key in Q_COLS),
            "recorded original t10 native patch q contradicts 101-time saved CSV")
    source_s_final=json.loads((store/s.JSON).read_text(encoding="utf-8"))["final"]
    require(all(math.isclose(final[key],float(source_s_final[key]),
                abs_tol=1e-5,rel_tol=1e-8) for key in STORAGE_COLS),
            "recorded original t10 storage contradicts 101-time saved CSV")
    report={
        "schema":"C3D05_B_C14_NATIVE_Q_VS_MODEL_REFERENCE_STORAGE_SAVED100MS_V1",
        "status":STATUS,
        "original_numerical_source_q_archive":str(qdir),
        "original_numerical_source_reference_storage_archive":str(store),
        "source_SHA256":provenance,
        "original_saved_time_count":len(combined),
        "saved_time_interval_s":0.1,
        "CFD_solver_time_step_s":0.001,
        "q_trapezoid_integral_not_native_solver_dt_integral":True,
        "original_q_computed_by_thermal_transport_models":True,
        "q_only_harmonic_overlay_on_shadow_not_original_CFD":True,
        "last_time_interface_faces_each":12636,
        "last_time_facewise_abs_interface_power_mismatch_W":
            qreport["per_face_geometry"]["matched_face_abs_power_sum_W"],
        "first":initial,"last":final,
        "max_instantaneous_signed_interface_mismatch_relative":max(
            r["interface_mismatch_relative_over_instantaneous_gross"]
            for r in combined),
        "signed_interface_mismatch_saved_trapezoid_J_NOT_SOLVER_DT":
            final[CUM_COLS["interface_sum_outward_W"]],
        "outward_exterior_conduction_saved_trapezoid_J_NOT_SOLVER_DT":
            final[CUM_COLS["external_total_q_out_W"]],
        "partial_reference_storage_plus_exterior_conduction_J_NOT_ENERGY_RESIDUAL":
            final["reference_storage_change_plus_external_conduction_trapezoid_J_NOT_ENERGY_RESIDUAL"],
        "valid_for_physically_calibrated_energy_conservation":False,
        "fvModels_source_integral_native_0_001s_verified":False,
        "total_thermal_energy_advection_pressure_work_verified":False,
        "external_radiation_convection_boundary_flux_terms_separately_verified":False,
        "grid_and_dt_convergence_verified":False,
        "JMatPro_QuickCup_experimental_validation":False,
        "CFD_rerun":False,
        "notes":[
            "This is a side-by-side diagnostic. Missing terms prevent physical energy closure.",
            "Original model reference storage is not native solver enthalpy; phase latent change is an equivalent proxy.",
            "Internal interface outward q from two regions largely cancels, but is not an external energy sink.",
            "A saved-0.1s trapezoid differs from integrals over actual 0.001s CFD solver steps.",
            "C14 metal is fluid (unityLewisFourier), mold is solid (isotropic).",
            "mold interpolate(kappa) harmonic was added only to a q-only shadow fvSchemes, never original CFD.",
            "Positive q is outward region conduction. It is not total enthalpy advection.",
            "The partial reference storage plus outer conduction number is explicitly NOT an energy conservation residual or a missing-heat estimate.",
            "Do not promote science gates G3-G7 or call the -1352.944 J change a leak.",
        ]
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=str(out.parent),prefix="."+out.name+".staging.") as staged:
        candidate=Path(staged)/"candidate"
        candidate.mkdir()
        with (candidate/CSV).open("x",encoding="utf-8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=CSV_KEYS)
            writer.writeheader()
            writer.writerows(combined)
        (candidate/JSON).write_text(
            json.dumps(report,indent=2,ensure_ascii=False)+"\n",
            encoding="utf-8")
        (candidate/MANIFEST).write_text(json.dumps({
            "original_native_q_report_SHA256":provenance["native_F14_q_report_SHA256"],
            "original_native_q_101_CSV_SHA256":provenance["original_q_101_csv_SHA256"],
            "original_storage_report_SHA256":provenance["original_storage_report_SHA256"],
            "original_storage_CSV_SHA256":provenance["original_storage_101_csv_SHA256"],
            "original_CFD_stage_SHA256":provenance["original_CFD_stage_SHA256"],
            "original_CFD_log_SHA256":provenance["original_CFD_log_SHA256"],
            "joined_reference_101_CSV_SHA256":sha(candidate/CSV),
            "joined_report_SHA256":sha(candidate/JSON),
            "all_original_archives_preserved":True,
            "no_recalculated_CFD_or_native_thermal_q":True
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "destination created concurrently; preserve it")
        candidate.rename(out)
    return report


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--q",type=Path,default=QDIR)
    p.add_argument("--storage",type=Path,default=STORAGE)
    p.add_argument("--out",type=Path,default=OUTPUT)
    args=p.parse_args()
    try:
        r=run(args.q,args.storage,args.out)
        print(json.dumps({
            "status":r["status"],
            "output":str(args.out),
            "saved_states_joined":r["original_saved_time_count"],
            "last_time_patch_conduction_and_model_reference_storage":r["last"],
            "q_out_exterior_saved_time_trapezoid_J_NOT_SOLVER_DT":
                r["outward_exterior_conduction_saved_trapezoid_J_NOT_SOLVER_DT"],
            "q_interface_mismatch_saved_time_trapezoid_J_NOT_SOLVER_DT":
                r["signed_interface_mismatch_saved_trapezoid_J_NOT_SOLVER_DT"],
            "partial_comparison_is_NOT_energy_residual":True,
            "full_CFD_energy_balance_validated":False,
            "NO_CFD_RERUN":True
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            OverflowError) as exc:
        print("C3D05_B_Q_STORAGE_JOIN_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
