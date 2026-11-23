#!/usr/bin/env python3
"""READ-ONLY analysis of an EXISTING authentic V4/T02 10 s C14 run.

This command NEVER executes foamMultiRun or redefines C14 thermo/phase/numerics.
It inspects saved ASCII OpenFOAM internalField data (0..10) and a real
foamMultiRun log, and writes reports to a SEPARATE new sibling directory.
Temperature/phase statistics are UNWEIGHTED over metal/mold cells: NOT energy
conservation, NOT a validated cooling curve, NOT spatial/time convergence.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import stage_c14_3d_case_a as original

NUM=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
SCALAR_UNIFORM=re.compile(r"\binternalField\s+uniform\s+("+NUM+r")\s*;")
SCALAR_NONUNIFORM=re.compile(
    r"\binternalField\s+nonuniform\s+List<scalar>\s*(\d+)\s*"
    r"(?:\((.*?)\)|\{\s*("+NUM+r")\s*\})\s*;",re.S
)
C14_TSOL=1423.0
C14_TLIQ=1473.0
ORIGINAL_META_STATUS="C3D04_A_C14_ORIGINAL_FULL_10S_NATIVE_EXECUTED_NOT_PHYSICALLY_VALIDATED"
HEADERS=(
    "time_s","metal_T_min_K","metal_T_mean_K","metal_T_max_K",
    "mold_T_min_K","mold_T_mean_K","mold_T_max_K",
    "metal_below_Tliq_cells","metal_below_Tliq_pct",
    "metal_below_Tsol_cells","metal_below_Tsol_pct",
    "metal_alpha1_min","metal_alpha1_mean","metal_alpha1_max",
    "metal_alpha1_below_0_999_cells",
    "metal_p_rgh_min_Pa","metal_p_rgh_mean_Pa","metal_p_rgh_max_Pa",
)


def require(value: bool, description: str) -> None:
    if not value:
        raise ValueError("C14_POSTRUN_READONLY_AUDIT_BLOCKED: "+description)


def file_digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        while block:=stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def scalar_field_values(path: Path, expected_cells: int) -> list[float]:
    """Read exact ASCII native OpenFOAM internalField; NEVER parse boundaries."""
    require(path.is_file() and not path.is_symlink(),
            "missing/unsafe native C14 scalar field "+str(path))
    source=path.read_text(encoding="utf-8")
    prefix=source.split("internalField",1)[0]
    require("format" in prefix and re.search(r"\bformat\s+ascii\s*;",prefix) is not None,
            "ASCII required for safe Python scanner (do not change source): "+str(path))
    single=SCALAR_UNIFORM.search(source)
    if single:
        values=[float(single.group(1))]*expected_cells
    else:
        many=SCALAR_NONUNIFORM.search(source)
        require(many is not None,
                "unsupported native scalar internalField serialization: "+str(path))
        declared=int(many.group(1))
        require(declared==expected_cells,
                f"field cell count differs ({declared}!={expected_cells}): "+str(path))
        if many.group(3) is not None:
            values=[float(many.group(3))]*declared
        else:
            values=[float(n) for n in (many.group(2) or "").split()]
            require(len(values)==declared,
                    "malformed internal scalar data length "+str(path))
    require(len(values)==expected_cells and all(math.isfinite(v) for v in values),
            "nonfinite native scalar values/incorrect count "+str(path))
    return values


def aggregate(values: list[float]) -> tuple[float,float,float]:
    return min(values),sum(values)/len(values),max(values)


def field_row(case: Path, time_label: str, metal_n: int, mold_n: int) -> dict:
    metal=case/time_label/"metal"
    mold=case/time_label/"mold"
    temperature=scalar_field_values(metal/"T",metal_n)
    sand=scalar_field_values(mold/"T",mold_n)
    alpha=scalar_field_values(metal/"phaseChangeSource:alpha1",metal_n)
    pressure=scalar_field_values(metal/"p_rgh",metal_n)
    tmin,tavg,tmax=aggregate(temperature)
    smin,savg,smax=aggregate(sand)
    amin,aavg,amax=aggregate(alpha)
    pmin,pavg,pmax=aggregate(pressure)
    below_liquidus=sum(t<C14_TLIQ for t in temperature)
    below_solidus=sum(t<C14_TSOL for t in temperature)
    return {
        "time_s":float(time_label),
        "metal_T_min_K":tmin,"metal_T_mean_K":tavg,"metal_T_max_K":tmax,
        "mold_T_min_K":smin,"mold_T_mean_K":savg,"mold_T_max_K":smax,
        "metal_below_Tliq_cells":below_liquidus,
        "metal_below_Tliq_pct":100*below_liquidus/metal_n,
        "metal_below_Tsol_cells":below_solidus,
        "metal_below_Tsol_pct":100*below_solidus/metal_n,
        "metal_alpha1_min":amin,"metal_alpha1_mean":aavg,"metal_alpha1_max":amax,
        "metal_alpha1_below_0_999_cells":sum(v<0.999 for v in alpha),
        "metal_p_rgh_min_Pa":pmin,"metal_p_rgh_mean_Pa":pavg,
        "metal_p_rgh_max_Pa":pmax,
    }


def parse_full_log(text: str) -> dict:
    require(bool(re.search(r"(?m)^\s*End\s*$",text)),
            "full native solver log does not contain normal End")
    times=[float(x) for x in re.findall(
        r"(?m)^\s*Time\s*=\s*("+NUM+r")s\s*$",text)]
    require(times and math.isclose(max(times),10.0,rel_tol=0,abs_tol=1e-10),
            "solver did not reach C14 original full 10 s")
    for token in ("Selecting solver fluid","Selecting solver solid",
                  "Selecting solidificationMeltingSource with name phaseChangeSource",
                  "Solving for h","Solving for e","Solving for p_rgh"):
        require(token in text,"source C14 solver/phase missing in native log: "+token)
    courant=[(float(a),float(b)) for a,b in re.findall(
        r"metal Courant Number mean:\s*("+NUM+r")\s+max:\s*("+NUM+r")",text)]
    require(bool(courant),"native Courant diagnostics absent")
    global_continuity=[(float(a),float(b),float(c)) for a,b,c in re.findall(
        r"metal time step continuity errors\s*:\s*sum local\s*=\s*("+NUM+
        r"),\s*global\s*=\s*("+NUM+r"),\s*cumulative\s*=\s*("+NUM+r")",text)]
    require(bool(global_continuity),"native continuity diagnostics absent")
    residuals={}
    for variable in ("h","e","p_rgh"):
        rgx=re.compile(
            r"Solving for "+re.escape(variable)+r",\s*"
            r"Initial residual\s*=\s*("+NUM+r"),\s*"
            r"Final residual\s*=\s*("+NUM+r")"
        )
        measurements=[(float(a),float(b)) for a,b in rgx.findall(text)]
        require(bool(measurements),"missing numeric solver residuals for "+variable)
        residuals[variable]={
            "count":len(measurements),
            "initial_max":max(v[0] for v in measurements),
            "final_max":max(v[1] for v in measurements),
            "final_last":measurements[-1][1],
        }
    require("FOAM FATAL" not in text,"FOAM FATAL found in log")
    require(re.search(
        r"(?:Initial residual|Final residual)\s*=\s*(?:nan|inf)\b",
        text,re.I) is None,"nonfinite native solver residual detected")
    return {
        "time_last_s":max(times),"n_time_steps_found_in_log":len(times),
        "courant_samples":len(courant),
        "courant_max_over_all_logged_steps":max(c[1] for c in courant),
        "courant_mean_last":courant[-1][0],
        "courant_max_last":courant[-1][1],
        "continuity_samples":len(global_continuity),
        "continuity_global_max_absolute":max(abs(c[1]) for c in global_continuity),
        "continuity_cumulative_last":global_continuity[-1][2],
        "residuals_over_entire_log":residuals,
        "native_end_found":True,
        "selected_C14_fluid_solid_phase_model":True
    }


def safe_new_output(case: Path, output: Path) -> None:
    require(output!=case and case not in output.parents
            and output not in case.parents,
            "output cannot overlap existing CFD results")
    require(not output.exists() and not output.is_symlink(),
            "output exists (refuse overwrite): "+str(output))


def analyze(case: Path, output: Path) -> dict:
    case=case.expanduser().resolve()
    output=output.expanduser().absolute()
    safe_new_output(case,output)
    original.physics.verify()
    metadata_file=case/original.REPORT
    require(metadata_file.is_file(),"missing C14 native completion JSON")
    stage=json.loads(metadata_file.read_text(encoding="utf-8"))
    require(stage.get("status")==ORIGINAL_META_STATUS
            and stage.get("native_solver_run") is True
            and stage.get("full_10s_original_controlDict_unchanged") is True,
            "actual original C14 10s solver completion cannot be established")
    require((case/"system/controlDict").read_bytes()==
            (original.physics.C14/"system/controlDict").read_bytes(),
            "actual C14 controlDict differs from original 10 s source")
    metal_n=original.region_cells(case,"metal",8960)["nCells"]
    mold_n=original.region_cells(case,"mold",12352)["nCells"]
    labels=sorted((
        child.name for child in case.iterdir()
        if child.is_dir() and re.fullmatch(r"\d+(?:\.\d+)?",child.name)
    ),key=float)
    require(len(labels)>=2 and labels[0]=="0"
            and math.isclose(float(labels[-1]),10.0),
            "saved time states must span initial t0 through final t10")
    require(len({float(t) for t in labels})==len(labels),
            "duplicate native time directories")
    log_file=case/"log.foamMultiRun"
    require(log_file.is_file() and log_file.stat().st_size>0,
            "native full solver log unavailable")
    summary_log=parse_full_log(log_file.read_text(encoding="utf-8",errors="replace"))
    rows=[field_row(case,lab,metal_n,mold_n) for lab in labels]
    final=rows[-1]
    analysis={
        "schema":"C3D04_A_ORIGINAL_C14_NATIVE_3D_READONLY_POSTRUN_V1",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "status":"EXISTING_REAL_V4_T02_C14_10S_FIELDS_AND_LOG_AUDITED_NOT_PHYSICALLY_VALIDATED",
        "source_case_read_only":str(case),
        "output_analysis_separate":str(output),
        "source_run_metadata_sha256":file_digest(metadata_file),
        "source_native_log_sha256":file_digest(log_file),
        "actual_C14_original_controlDict_sha256":file_digest(case/"system/controlDict"),
        "source_mesh_cells":{"metal":metal_n,"mold":mold_n},
        "time_states_count":len(labels),"saved_times_s":[float(x) for x in labels],
        "F14_native_log":summary_log,
        "initial_time_fields":rows[0],
        "final_time_fields":final,
        "minimum_metal_temperature_over_saved_times_K":
            min(x["metal_T_min_K"] for x in rows),
        "minimum_alpha1_over_saved_times":
            min(x["metal_alpha1_min"] for x in rows),
        "any_saved_cell_below_Tliq_C14":
            any(x["metal_below_Tliq_cells"]>0 for x in rows),
        "any_saved_cell_alpha1_below_0_999":
            any(x["metal_alpha1_below_0_999_cells"]>0 for x in rows),
        "temperature_cell_means_weighted_by_volume":False,
        "energy_balance_verified":False,
        "momentum_mass_flux_balance_verified":False,
        "mesh_time_independence_verified":False,
        "experimental_QuickCup_validation":False,
        "NOT_A_NEW_CFD":True,
        "C14_thermophysical_and_solver_settings_unchanged":True,
        "notes":[
            "Unweighted cell temperatures/phase values and all-log Courant/residuals only.",
            "T below Tliq is temperature threshold, not standalone proof of latent-heat balance.",
            "To claim conservation, obtain cell volumes, interface and exterior fluxes; don't infer from mean T.",
            "This script never runs foamMultiRun and never edits original V4/T02 or this existing CFD directory."
        ],
    }
    output.mkdir(parents=True,exist_ok=False)
    with (output/"C3D04_A_C14_10S_TIME_SERIES.csv").open(
            "w",encoding="utf-8",newline="") as stream:
        csvwriter=csv.DictWriter(stream,fieldnames=HEADERS)
        csvwriter.writeheader()
        csvwriter.writerows(rows)
    (output/"C3D04_A_C14_10S_DIAGNOSTICS.json").write_text(
        json.dumps(analysis,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return analysis


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",type=Path,
                        default=Path.home()/
                        "OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    parser.add_argument("--out",type=Path,
                        default=Path.home()/
                        "OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_ANALYSIS_01")
    args=parser.parse_args()
    try:
        result=analyze(args.case,args.out)
        print(json.dumps({
            "status":result["status"],
            "time_states":result["time_states_count"],
            "native_log":result["F14_native_log"],
            "final_field_stats":result["final_time_fields"],
            "out":result["output_analysis_separate"],
            "energy_balance_verified":False,
            "physical_validation":False
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,UnicodeError) as exc:
        print("C14_POSTRUN_READONLY_AUDIT_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
