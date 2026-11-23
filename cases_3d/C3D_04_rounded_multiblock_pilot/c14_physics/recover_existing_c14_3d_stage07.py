#!/usr/bin/env python3
"""Read-only recovery of genuine C14 3D-A saved-volume/phase kinetics.

Reads the archived C14 0..10s CFD, 101 saved-state volume CSV/report and any
partially completed native postProcessing workcopy. Publishes a new isolated
forensic JSON+101-state kinetics CSV. No solvers, mesh, checkout, copying or
modification of CFD or prior analysis. Does NOT assert energy conservation,
experimental validation, exact solidification onset or 0.001s sample recovery.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
C14 = REPO / "cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
CONTRACT = BASE / "C14_3D_PHYSICS_CONTRACT.json"
CSV_IN = "C3D04_A_C14_3D_VOLUMETRIC_101_STATES.csv"
JSON_IN = "C3D04_A_C14_3D_POSTPROCESS_REPORT.json"
NATIVE = "C3D04_A_C14_NATIVE_POSTPROCESS_REPORT.json"
CSV_OUT = "C3D04_A_STAGE07_KINETICS_101_STATES.csv"
JSON_OUT = "C3D04_A_STAGE07_RECOVERY_REPORT.json"
INPUTS = (
    "time_s", "metal_volume_m3", "mold_volume_m3",
    "metal_T_volMean_K", "mold_T_volMean_K",
    "metal_alpha1_volMean", "metal_solid_fraction_volMean",
    "metal_below_Tliq_volume_percent", "metal_below_Tsol_volume_percent",
    "metal_mean_speed_m_s", "metal_max_speed_m_s",
    "metal_sensible_delta_J", "metal_latent_inventory_delta_J",
    "mold_sensible_delta_J", "combined_estimated_stored_energy_delta_J",
)
OUTPUTS = (
    "time_s", "metal_T_volMean_K", "mold_T_volMean_K",
    "metal_alpha1_volMean", "metal_solid_fraction_volMean",
    "metal_below_Tliq_volume_percent", "metal_below_Tsol_volume_percent",
    "metal_mean_speed_m_s", "metal_max_speed_m_s",
    "metal_solid_inventory_kg", "metal_liquid_inventory_kg",
    "interval_start_s", "interval_end_s",
    "metal_cooling_rate_saved_K_s", "mold_warming_rate_saved_K_s",
    "model_liquid_fraction_decrease_saved_s_inv",
    "nominal_solid_inventory_gain_kg_s", "nominal_latent_release_W",
    "nominal_metal_sensible_storage_W", "nominal_mold_sensible_storage_W",
    "nominal_combined_storage_rate_W",
)


class Blocked(ValueError):
    pass


def check(ok: bool, message: str) -> None:
    if not ok:
        raise Blocked("C3D04_A_STAGE07_BLOCKED: " + message)


def file_ok(p: Path) -> bool:
    return p.is_file() and not p.is_symlink()


def hashfile(p: Path) -> str:
    check(file_ok(p), "missing or symlinked input " + str(p))
    d = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            d.update(chunk)
    return d.hexdigest()


def json_file(p: Path) -> dict:
    check(file_ok(p), "missing input JSON " + str(p))
    obj = json.loads(p.read_text(encoding="utf-8"))
    check(isinstance(obj, dict), "invalid JSON object " + str(p))
    return obj


def read_volume(case: Path, folder: Path) -> tuple[list[dict], dict, dict]:
    meta = json_file(folder / JSON_IN)
    check(meta.get("schema") == "C3D04_A_C14_3D_POSTPROCESS_VOLUME_PARITY_V1"
          and meta.get("CFD_rerun") is False
          and meta.get("energy_conservation_verified") is False,
          "not an auditable offline C14 3D volumetric report")
    check(Path(str(meta.get("source_case_read_only", ""))).resolve() == case,
          "volumetric report points at another CFD run")
    native_hash = hashfile(case / "log.foamMultiRun")
    check(native_hash == meta.get("native_log_sha256"),
          "saved volumetric report and original CFD log hashes disagree")
    p = folder / CSV_IN
    check(file_ok(p), "101-snapshot volume-weighted CSV does not exist")
    with p.open(newline="", encoding="utf-8") as f:
        table = csv.DictReader(f)
        check(table.fieldnames and all(x in table.fieldnames for x in INPUTS),
              "volume CSV missing required columns")
        raw = list(table)
    check(len(raw) == 101, "genuine archived 101 timestamps required")
    rows = []
    for i, entry in enumerate(raw):
        try:
            x = {key: float(entry[key]) for key in INPUTS}
        except (KeyError, ValueError, TypeError) as exc:
            raise Blocked("corrupt numeric volume row " + str(i)) from exc
        check(all(math.isfinite(v) for v in x.values()),
              "nonfinite volume CSV values at row " + str(i))
        check(math.isclose(x["time_s"], i * 0.1, abs_tol=1e-8),
              "unexpected recorded time in row " + str(i))
        check(x["metal_volume_m3"] > 0 and x["mold_volume_m3"] > 0,
              "nonpositive native integrated mesh volume")
        a = x["metal_alpha1_volMean"]
        check(-1e-7 <= a <= 1+1e-7 and math.isclose(
              1 - a, x["metal_solid_fraction_volMean"], abs_tol=1e-7),
              "C14 model solid/liquid fractions inconsistent")
        liq = x["metal_below_Tliq_volume_percent"]
        sol = x["metal_below_Tsol_volume_percent"]
        check(0 <= sol <= liq + 1e-7 and liq <= 100 + 1e-7,
              "liquidus/solidus volume percentages inconsistent")
        check(0 <= x["metal_mean_speed_m_s"] <=
              x["metal_max_speed_m_s"] + 1e-9,
              "metal speed mean and maxima inconsistent")
        rows.append(x)
    first = rows[0]
    for r in rows:
        check(math.isclose(r["metal_volume_m3"],first["metal_volume_m3"],
                           rel_tol=1e-10)
              and math.isclose(r["mold_volume_m3"],first["mold_volume_m3"],
                               rel_tol=1e-10),
              "native mesh volume unexpectedly varies across snapshots")
    check(math.isclose(float(meta["metal_volume_m3"]),
                       first["metal_volume_m3"], rel_tol=1e-9)
          and math.isclose(float(meta["mold_volume_m3"]),
                           first["mold_volume_m3"], rel_tol=1e-9),
          "volume CSV and native mesh-volume report inconsistent")
    check(isinstance(meta.get("peak_solver_final_residual_with_time"),dict),
          "missing actual source solver residual timestamps")
    hashes = {"source_CFD_log_sha256": native_hash,
              "existing_volumetric_CSV_sha256": hashfile(p),
              "existing_volumetric_report_sha256": hashfile(folder / JSON_IN)}
    return rows, meta, hashes


def onset(rows: list[dict], predicate) -> dict:
    """Return first SAVED state interval, never extrapolate continuous onset."""
    for i, r in enumerate(rows):
        if predicate(r, rows[0]):
            return {
                "first_saved_time_s": r["time_s"],
                "last_saved_time_before_event_s":
                    rows[i-1]["time_s"] if i else None,
                "already_present_at_initial_snapshot": i == 0,
                "exact_physical_onset_known": False,
            }
    return {"first_saved_time_s": None,
            "last_saved_time_before_event_s": None,
            "already_present_at_initial_snapshot": False,
            "exact_physical_onset_known": False}


def calculate(rows: list[dict], metal_mass: float, latent: float) -> tuple[list[dict],dict]:
    check(len(rows)==101 and metal_mass>0 and latent>0,
          "invalid original C14 mass/latent/101 snapshots")
    result=[]
    for i,r in enumerate(rows):
        a=r["metal_alpha1_volMean"]
        out = {key:r[key] for key in OUTPUTS[:9]}
        out.update({
            "metal_solid_inventory_kg": metal_mass*(1-a),
            "metal_liquid_inventory_kg": metal_mass*a,
            **{key:None for key in OUTPUTS[11:]},
        })
        if i:
            prev=rows[i-1]
            dt=r["time_s"]-prev["time_s"]
            check(dt>0,"non-increasing saved snapshot times")
            da=prev["metal_alpha1_volMean"]-a
            out.update({
                "interval_start_s":prev["time_s"],
                "interval_end_s":r["time_s"],
                "metal_cooling_rate_saved_K_s":
                    (prev["metal_T_volMean_K"]-r["metal_T_volMean_K"])/dt,
                "mold_warming_rate_saved_K_s":
                    (r["mold_T_volMean_K"]-prev["mold_T_volMean_K"])/dt,
                "model_liquid_fraction_decrease_saved_s_inv": da/dt,
                "nominal_solid_inventory_gain_kg_s": metal_mass*da/dt,
                "nominal_latent_release_W":metal_mass*latent*da/dt,
                "nominal_metal_sensible_storage_W":
                    (r["metal_sensible_delta_J"]-prev["metal_sensible_delta_J"])/dt,
                "nominal_mold_sensible_storage_W":
                    (r["mold_sensible_delta_J"]-prev["mold_sensible_delta_J"])/dt,
                "nominal_combined_storage_rate_W":
                    (r["combined_estimated_stored_energy_delta_J"]-
                     prev["combined_estimated_stored_energy_delta_J"])/dt,
            })
        result.append(out)
    def peak(key: str) -> dict:
        r=max(result[1:],key=lambda x:x[key])
        return {"from_s":r["interval_start_s"], "to_s":r["interval_end_s"],
                "value":r[key]}
    summary={
        "first_saved_below_liquidus":
            onset(rows,lambda r,first:r["metal_below_Tliq_volume_percent"]>1e-9),
        "first_saved_below_solidus":
            onset(rows,lambda r,first:r["metal_below_Tsol_volume_percent"]>1e-9),
        "first_saved_alpha1_decrease":
            onset(rows,lambda r,first:r["metal_alpha1_volMean"]<
                  first["metal_alpha1_volMean"]-1e-7),
        "peak_saved_interval_metal_cooling_K_s":
            peak("metal_cooling_rate_saved_K_s"),
        "peak_saved_interval_liquid_fraction_decrease":
            peak("model_liquid_fraction_decrease_saved_s_inv"),
        "peak_saved_interval_nominal_latent_release_W":
            peak("nominal_latent_release_W"),
        "start":result[0],"final":result[-1],
        "final_model_solid_inventory_kg":result[-1]["metal_solid_inventory_kg"],
        "estimated_latent_energy_released_J":metal_mass*latent*
            (rows[0]["metal_alpha1_volMean"]-rows[-1]["metal_alpha1_volMean"]),
        "combined_nominal_stored_energy_change_J":
            rows[-1]["combined_estimated_stored_energy_delta_J"]-
            rows[0]["combined_estimated_stored_energy_delta_J"],
    }
    return result,summary


def native_inspection(case:Path,copy:Path,log_hash:str)->dict:
    """Read and attest what actually exists, including incomplete prior runs."""
    result={"copy_exists":copy.is_dir(),"native_final_report_exists":False,
            "verified_native_success":False,
            "new_CFD_run":False,
            "log_inspection":{}}
    if not copy.is_dir() or copy.is_symlink():
        result["status"]="ABSENT_OR_UNSAFE_COPY"
        return result
    controls=copy/"system/controlDict"
    origin_ctrl=case/"system/controlDict"
    simlog=copy/"log.foamMultiRun"
    good_controls=(file_ok(controls) and file_ok(origin_ctrl) and
                   hashfile(controls)==hashfile(origin_ctrl))
    good_log=file_ok(simlog) and hashfile(simlog)==log_hash
    result["copy_original_controlDict_matches"]=good_controls
    result["copy_original_solver_log_matches"]=good_log
    result["preserved_original_postprocessing_snapshot"]=(
        copy/"_original_postProcessing_preserved_unmodified").is_dir()
    for name in ("c14_functions","momentum","top_surface","foamLog"):
        p=copy/("log.C14_3D_postprocess_"+name)
        result["log_inspection"][name]={
            "present":file_ok(p),
            "sha256":hashfile(p) if file_ok(p) else None,
            "exit_code_recoverable_from_log":False,
        }
    p=copy/NATIVE
    if file_ok(p):
        record=json_file(p)
        consistent=(
            record.get("source_log_sha256")==log_hash
            and Path(str(record.get("original_CFD_read_only",""))).resolve()==case
            and good_controls and good_log
        )
        result.update({
            "native_final_report_exists":True,
            "final_report_sha256":hashfile(p),
            "final_report_source_verified":consistent,
            "native_commands_all_passed":record.get("all_native_processing_commands_passed"),
            "missing_expected_C14_object_dirs":
                record.get("missing_expected_C14_object_dirs"),
            "missing_derived_C14_fields":
                record.get("missing_derived_C14_fields_at_final_time"),
            "incomplete_profiles_at_t10":record.get("incomplete_profiles_at_t10"),
            "nominal_energy_audit":record.get("native_energy_closure_audit"),
        })
        result["verified_native_success"]=bool(
            consistent and record.get("all_native_processing_commands_passed") is True
            and record.get("missing_expected_C14_object_dirs")==[]
            and record.get("missing_derived_C14_fields_at_final_time")==[]
            and record.get("incomplete_profiles_at_t10")==[])
        result["status"]=("NATIVE_REPORT_SOURCE_VERIFIED_NOT_PHYSICAL_VALIDATION"
                          if consistent else "UNTRUSTED_NATIVE_REPORT")
    else:
        result["status"]=("COPY_VALID_NATIVE_REPORT_NOT_YET_WRITTEN"
                          if good_controls and good_log else "INCOMPLETE_COPY")
    return result


def evaluate(case:Path,vol:Path,copy:Path)->tuple[dict,list[dict]]:
    case=case.expanduser().resolve()
    vol=vol.expanduser().resolve()
    copy=copy.expanduser().absolute()
    check(case.is_dir() and not case.is_symlink(), "real source run absent/unsafe")
    sourcectrl=case/"system/controlDict"
    c14ctrl=C14/"system/controlDict"
    check(hashfile(sourcectrl)==hashfile(c14ctrl),
          "original C14 CFD controlDict differs from source")
    data,meta,hashes=read_volume(case,vol)
    contract=json_file(CONTRACT)["C14_exact_values"]
    mass=float(meta["metal_total_mass_kg"])
    check(math.isclose(mass, data[0]["metal_volume_m3"]*
                       float(contract["metal"]["rho_kg_m3"]),rel_tol=1e-9),
          "reported C14 metal mass not matched to original rho and volume")
    timeline,kinetics=calculate(data,mass,float(contract["solidification"]["L_J_kg"]))
    native=native_inspection(case,copy,hashes["source_CFD_log_sha256"])
    # If native logs or the final report appear after the first analysis,
    # do not call a previous immutable report an unchanged-evidence rerun.
    # A new output directory must be explicitly selected, no overwrites.
    native_identity={
        "copy_exists":native["copy_exists"],
        "copy_original_controlDict_matches":
            native.get("copy_original_controlDict_matches"),
        "copy_original_solver_log_matches":
            native.get("copy_original_solver_log_matches"),
        "native_final_report_sha256":
            native.get("final_report_sha256"),
        "native_step_log_sha256":{
            k:v.get("sha256") for k,v in native["log_inspection"].items()
        },
    }
    report={
        "schema":"C3D04_A_C14_3D_STAGE07_EXISTING_EVIDENCE_V1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "status":"GENUINE_SAVED_101_STATE_KINETICS_RECOVERED_NATIVE_UNVERIFIED",
        "case_A_source_run_read_only":str(case),
        "source_volumetric_output_read_only":str(vol),
        "source_native_postprocess_copy_read_only":str(copy),
        "source_C14_fluid_solid":str(C14),
        "source_sha256":{**hashes,
             "source_C14_controlDict_sha256":hashfile(c14ctrl),
             "native_case_controlDict_sha256":hashfile(sourcectrl),
             "C14_contract_sha256":hashfile(CONTRACT),
             "existing_native_copy_inputs":native_identity},
        "original_residual_peak_timestamps":
            meta["peak_solver_final_residual_with_time"],
        "metal_mass_kg_nominal":mass,
        "latent_heat_J_kg_C14_nominal":contract["solidification"]["L_J_kg"],
        "kinetics":kinetics,
        "native_postprocess_existing_inspection":native,
        "stage":"7/10","milestones_done":"6/10",
        "operational_progress_percent":60,
        "not_a_percent_of_physical_validation":True,
        "solver_rerun":False,"prior_results_modified":False,
        "original_solver_time_step_s":contract["numerics"]["deltaT_s"],
        "available_saved_snapshot_interval_s":0.1,
        "global_energy_conservation_verified":False,
        "experiment_QuickCup_validated":False,
        "mesh_or_time_step_independence_verified":False,
        "exact_physical_phase_change_onset_known":False,
        "limits":[
          "Source model alpha1 is liquid fraction, not an experimental solid-fraction observation.",
          "Initial crossing and liquid-fraction changes are bounded by 0.1s stored snapshots, not a true exact onset at 0.001s.",
          "Nominal heat of solidification is rho*L times liquid-inventory change over saved snapshots; it is not the original native per-time-step latent power.",
          "Sensible/latent storage differences do not establish conservation without source, advective, surface energy and sand energy accounting.",
          "Native copy logs alone do not preserve subprocess exit codes; only a source-matched native final report can attest command success.",
          "The current audit hashes C14 controlDict, source solver log, volumetric CSV and report; it does not rehash all 101 saved field files.",
        ],
        "new_CSV":CSV_OUT,
    }
    return report,timeline


def publish(report:dict,rows:list[dict],out:Path)->str:
    out=out.expanduser().absolute()
    preserved=[Path(report["case_A_source_run_read_only"]).resolve(),
               Path(report["source_volumetric_output_read_only"]).resolve(),
               Path(report["source_native_postprocess_copy_read_only"]).resolve(),
               C14.resolve(),REPO.resolve()]
    check(all(out!=p and p not in out.parents and out not in p.parents
              for p in preserved),"out directory overlaps a preserved source tree")
    if out.exists() or out.is_symlink():
        prior=json_file(out/JSON_OUT)
        check(prior.get("schema")==report["schema"]
              and prior.get("source_sha256")==report["source_sha256"],
              "existing output is incompatible with source provenance")
        check(file_ok(out/CSV_OUT),"existing output missing 101-state kinetics CSV")
        return "EXISTING_SOURCE_MATCHED_DIAGNOSTIC_PRESERVED_NO_OVERWRITE"
    check(out.parent.is_dir(),"out parent directory missing")
    out.mkdir(exist_ok=False)
    with (out/CSV_OUT).open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=OUTPUTS)
        writer.writeheader()
        writer.writerows(rows)
    (out/JSON_OUT).write_text(json.dumps(
        report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return "NEW_101_STATE_DIAGNOSTIC_PUBLISHED_NO_CFD"


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",type=Path,default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    ap.add_argument("--volume",type=Path,default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_3D_VOLUMETRIC_POSTPROCESS_01")
    ap.add_argument("--copy",type=Path,default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01")
    ap.add_argument("--out",type=Path,default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_STAGE07_RECOVERY_KINETICS_01")
    arg=ap.parse_args()
    try:
        report,rows=evaluate(arg.case,arg.volume,arg.copy)
        status=publish(report,rows,arg.out)
        print(json.dumps({
            "status":status,"case":"C3D04-A","stage":"7/10",
            "milestones_done":"6/10","solver_rerun":False,
            "first_saved_alpha1_decrease":
                report["kinetics"]["first_saved_alpha1_decrease"],
            "max_saved_interval_latent_power_W":
                report["kinetics"]["peak_saved_interval_nominal_latent_release_W"],
            "final_metal_T_volume_mean_K":
                report["kinetics"]["final"]["metal_T_volMean_K"],
            "final_metal_solid_inventory_kg_model":
                report["kinetics"]["final_model_solid_inventory_kg"],
            "native_copy_forensic_status":
                report["native_postprocess_existing_inspection"]["status"],
            "native_commands_verified":
                report["native_postprocess_existing_inspection"]["verified_native_success"],
            "energy_conservation_verified":False,
            "report":str(arg.out/JSON_OUT),
            "kinetics_csv":str(arg.out/CSV_OUT),
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("C3D04_A_STAGE07_RECOVERY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
