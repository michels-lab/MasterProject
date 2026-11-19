#!/usr/bin/env python3
"""FS-C05: read-only REAL OpenFOAM 14 two-step VOF+CHT field diagnostics.

Re-evaluates an ACCEPTED native foamMultiRun report, source provenance,
per-region mesh hashes, RAS transport scheme hashes and the solver log.
Reads actual ASCII 0,1e-7,2e-7 fluid alpha.metal/T and mold T snapshots;
uses each native hexahedron volume to report phase-specific VOF volumes,
volume drifts and temperature averages. Not energy/heat-flux validation.

No OpenFOAM executable is called, no directory is copied, no files written.
A finished two-step solver is not equivalent to physically validated CHT.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha, read_temperature
from audit_fs_c04_split_cells import (
    FLUID_CELLS, SAND_CELLS, read_mesh, cell_volume_m3,
)
from stage_fs_c04_initial_alpha import digest
from run_fs_c05_native_smoke import (
    preflight, validate_run_log, STOP_TIME,
)

EXPECTED_TIMES=(0.,1e-7,2e-7)
TIME_TOLERANCE_S=2e-12
ALPHA_BOUNDS_TOL=1e-6
DRIFT_ALERT_REL=1e-3
METAL_REFERENCE_VOLUME_M3=4.801191628e-5
REGIONS=("fluid","mold")
MESH_FILES=("points","faces","owner","neighbour","boundary")


def discover_saved_times(case:Path)->dict[float,Path]:
    found={}
    for folder in case.iterdir():
        if not folder.is_dir() or folder.is_symlink():
            continue
        try:
            value=float(folder.name)
        except ValueError:
            continue
        require(math.isfinite(value) and value>=0,
                "native case has invalid numeric time folder")
        matches=[t for t in EXPECTED_TIMES
                 if math.isclose(value,t,rel_tol=0,abs_tol=TIME_TOLERANCE_S)]
        if not matches:
            continue
        t=matches[0]
        require(t not in found,
                "multiple time folders for same native sample "+str(t))
        found[t]=folder
    require(set(found)==set(EXPECTED_TIMES),
            "missing t=0,1e-7 or 2e-7 saved native time field directories")
    return found


def summarize_fields(
    fluid_volumes:list[float],
    mold_volumes:list[float],
    alpha:list[float],
    fluid_T:list[float],
    mold_T:list[float],
)->dict:
    """Native hexa cell-volume weighted phase and region observables."""
    require(len(fluid_volumes)==len(alpha)==len(fluid_T)
            and len(mold_volumes)==len(mold_T)
            and len(alpha)>0 and len(mold_T)>0,
            "VOF and T field lengths inconsistent with region mesh")
    require(all(math.isfinite(x) and x>0 for x in fluid_volumes+mold_volumes),
            "cell volumes must be finite positive")
    require(all(math.isfinite(x) for x in alpha+fluid_T+mold_T),
            "nonfinite OpenFOAM VOF or T")
    require(all(x>0 for x in fluid_T+mold_T),
            "nonpositive absolute temperature detected")
    fluid_total=sum(fluid_volumes)
    mold_total=sum(mold_volumes)
    alpha_min=min(alpha)
    alpha_max=max(alpha)
    normalized=[min(1.,max(0.,a)) for a in alpha]
    metal_volume=sum(a*v for a,v in zip(normalized,fluid_volumes))
    unbounded_volume=sum(a*v for a,v in zip(alpha,fluid_volumes))
    air_volume=fluid_total-metal_volume
    require(metal_volume>0 and air_volume>0,
            "metal or air phase volume missing")
    metal_temp=sum(v*a*t for v,a,t
                   in zip(fluid_volumes,normalized,fluid_T))/metal_volume
    air_temp=sum(v*(1-a)*t for v,a,t
                 in zip(fluid_volumes,normalized,fluid_T))/air_volume
    mean_fluid=sum(v*t for v,t in zip(fluid_volumes,fluid_T))/fluid_total
    mean_mold=sum(v*t for v,t in zip(mold_volumes,mold_T))/mold_total
    return {
        "fluid_region_volume_m3":fluid_total,
        "mold_region_volume_m3":mold_total,
        "metal_phase_volume_clamped_m3":metal_volume,
        "metal_phase_volume_raw_m3":unbounded_volume,
        "air_phase_volume_clamped_m3":air_volume,
        "min_alpha":alpha_min,
        "max_alpha":alpha_max,
        "alpha_out_of_unit_interval_cells":sum(a<0 or a>1 for a in alpha),
        "alpha_within_tolerance":
            alpha_min>=-ALPHA_BOUNDS_TOL and alpha_max<=1+ALPHA_BOUNDS_TOL,
        "fluid_T_min_K":min(fluid_T),
        "fluid_T_max_K":max(fluid_T),
        "mold_T_min_K":min(mold_T),
        "mold_T_max_K":max(mold_T),
        "metal_alpha_volume_weighted_T_K":metal_temp,
        "air_alpha_volume_weighted_T_K":air_temp,
        "fluid_region_volume_weighted_T_K":mean_fluid,
        "mold_region_volume_weighted_T_K":mean_mold,
        "metal_alpha_volume_cell_count":sum(a>0 for a in alpha),
        "interfacial_alpha_0_to_1_cells":sum(0<a<1 for a in alpha),
        "heat_flux_integral_computed":False,
        "energy_or_mass_conservation_validated":False,
    }


def gate_successful_native_run(case:Path)->dict:
    require(case.is_dir() and not case.is_symlink()
            and case.name.startswith("FS_C05_NATIVE_SMOKE_"),
            "not an isolated FS-C05 native smoke case")
    manifest=case/"FS_C05_NATIVE_SMOKE_REPORT.json"
    require(manifest.is_file() and not manifest.is_symlink(),
            "missing native smoke acceptance report")
    record=json.loads(manifest.read_text())
    require(record.get("schema")==
            "masterproject-fs-c05-native-two-step-cht-smoke-v1"
            and record.get("status")==
            "NATIVE_TWO_STEP_VOF_CHT_STARTUP_COMPLETED_NOT_VALIDATED"
            and record.get("solver_ran") is True
            and record.get("output")==str(case)
            and record.get("expected_endTime_s")==STOP_TIME
            and record.get("physically_validated") is False,
            "native two-step smoke did not complete with accepted status")
    require(record.get("heat_flux_balance_verified") is False
            and record.get("energy_balance_verified") is False,
            "source falsely claims CHT conservation without verification")
    src_info=record.get("source",{})
    source=Path(src_info.get("source_case",""))
    require(preflight(source)==src_info,
            "native FS-C05 source no longer matches approved provenance")
    for region in REGIONS:
        for name in MESH_FILES:
            rel=Path("constant")/region/"polyMesh"/name
            old=source/rel
            new=case/rel
            require(new.is_file() and not new.is_symlink()
                    and digest(new)==digest(old),
                    "fluid/mold topology modified since validated pilot: "+str(rel))
    require(digest(case/"0/fluid/alpha.metal")==src_info["alpha_sha256"],
            "initial phase field changed")
    control=case/"system/controlDict"
    schemes=case/"system/fluid/fvSchemes"
    require(digest(control)==record["controlDict_after_shortening_sha256"],
            "two-step controls changed since native run")
    require(digest(schemes)==record["rhoPhi_turbulence_schemes_sha256"],
            "RAS rhoPhi transport schemes changed since run")
    require("div(rhoPhi,k)" in schemes.read_text()
            and "div(rhoPhi,epsilon)" in schemes.read_text(),
            "compressible RAS discretization unexpectedly absent")
    log=case/"log.FS_C05_foamMultiRun"
    require(log.is_file() and not log.is_symlink()
            and digest(log)==record["native_log_sha256"],
            "native solver log was modified or missing")
    raw=log.read_text(errors="replace")
    require("EXIT: 0" in raw and "foamMultiRun" in raw,
            "native log does not confirm successful solver invocation")
    measurements=validate_run_log(raw)
    require(measurements==record["startup_log"],
            "native log time markers differ from recorded successful startup")
    return {"source":str(source),"native_log_sha256":digest(log),
            "smoke_manifest_sha256":digest(manifest),
            "run_steps":measurements}


def audit(case:Path)->dict:
    case=case.expanduser().resolve()
    provenance=gate_successful_native_run(case)
    times=discover_saved_times(case)
    fluid_mesh=read_mesh(case/"constant/fluid/polyMesh",FLUID_CELLS)
    mold_mesh=read_mesh(case/"constant/mold/polyMesh",SAND_CELLS)
    fv=[cell_volume_m3(fluid_mesh,i) for i in range(FLUID_CELLS)]
    mv=[cell_volume_m3(mold_mesh,i) for i in range(SAND_CELLS)]
    reports={}
    for t,folder in sorted(times.items()):
        fields={
            "alpha":folder/"fluid/alpha.metal",
            "T_fluid":folder/"fluid/T",
            "T_mold":folder/"mold/T",
        }
        for key,p in fields.items():
            require(p.is_file() and not p.is_symlink(),
                    f"missing actual saved {key} at t={t:g}: "+str(p))
        a=read_alpha(fields["alpha"],expected_cells=FLUID_CELLS)
        tf=read_temperature(fields["T_fluid"],expected_cells=FLUID_CELLS)
        tm=read_temperature(fields["T_mold"],expected_cells=SAND_CELLS)
        measurements=summarize_fields(fv,mv,a,tf,tm)
        measurements["time_s"]=t
        measurements["native_field_sha256"]={
            name:digest(p) for name,p in fields.items()
        }
        reports[t]=measurements
    start=reports[0.]
    end=reports[STOP_TIME]
    initial_volume=start["metal_phase_volume_raw_m3"]
    change=end["metal_phase_volume_raw_m3"]-initial_volume
    drift=change/initial_volume
    source_drift=(initial_volume-METAL_REFERENCE_VOLUME_M3)/METAL_REFERENCE_VOLUME_M3
    require(abs(source_drift)<=2e-4,
            "initial alpha volume differs from proven FS-C04 initial VOF")
    status=(
        "NATIVE_TWO_STEP_FIELDS_MEASURED_WITH_WARNINGS_NO_CHT_VALIDATION"
        if abs(drift)>DRIFT_ALERT_REL or
           any(not x["alpha_within_tolerance"] for x in reports.values())
        else "NATIVE_TWO_STEP_FIELDS_MEASURED_NO_CHT_VALIDATION"
    )
    return {
        "schema":"masterproject-fs-c05-postrun-two-step-observables-v1",
        "status":status,
        "case":str(case),
        "native_success_provenance":provenance,
        "time_s":[0.,1e-7,STOP_TIME],
        "snapshots":[reports[t] for t in sorted(reports)],
        "initial_metal_volume_m3":initial_volume,
        "final_metal_volume_m3":end["metal_phase_volume_raw_m3"],
        "metal_volume_change_m3":change,
        "metal_volume_relative_change":drift,
        "drift_alert_threshold_fraction":DRIFT_ALERT_REL,
        "metal_volume_drift_below_alert":abs(drift)<=DRIFT_ALERT_REL,
        "metal_alpha_weighted_T_change_K":
            end["metal_alpha_volume_weighted_T_K"]-
            start["metal_alpha_volume_weighted_T_K"],
        "air_alpha_weighted_T_change_K":
            end["air_alpha_volume_weighted_T_K"]-
            start["air_alpha_volume_weighted_T_K"],
        "mold_volume_weighted_T_change_K":
            end["mold_region_volume_weighted_T_K"]-
            start["mold_region_volume_weighted_T_K"],
        "field_read_by_python_from_native_openfoam_output":True,
        "native_foamPostProcess_integrals_at_final_time":False,
        "metal_mass_flux_through_open_boundaries_measured":False,
        "interface_heat_flux_balance_measured":False,
        "total_energy_balance_measured":False,
        "cooling_curve_validated":False,
        "solidification_shrinkage_present":False,
        "original_files_modified":False,
        "notes":[
            "Only 0.2 microseconds of solver time; no physical cooling curve",
            "Metal volume is ∫alpha.metal dV, not ∫rho*alpha.metal dV",
            "Metal/air mean T uses cell V*alpha; not a mass/enthalpy weighted mean",
            "A short volume drift under alert is NOT proof of mass conservation",
            "No heat flux or conjugate energy closure can be inferred from T change alone",
        ],
    }


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",required=True,type=Path)
    args=parser.parse_args(argv)
    try:
        report=audit(args.case)
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C05 POSTRUN DIAGNOSTIC BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
