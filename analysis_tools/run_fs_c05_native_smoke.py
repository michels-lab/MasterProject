#!/usr/bin/env python3
"""FS-C05: FIRST TWO-TIME-STEP 3D compressibleVoF+solid CHT STARTUP SMOKE.

Runs ONLY on a fresh copy of a prior staged/untested FS-C05 candidate,
with exact SHA/provenance gates, 2 tiny time steps, bounded runtime and
complete logs. This is NOT thermophysical calibration, NOT evidence of
realistic curves/heat flux, and NOT solidification/shrinkage.

By default --stage-only does NOT execute OpenFOAM.
--native explicitly runs FOUNDATION14 foamMultiRun ON THE NEW COPY ONLY.
A nonzero return, timeout, fatal log or missing time outputs is a FAIL.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha, read_temperature
from audit_fs_c04_split_cells import FLUID_CELLS, SAND_CELLS
from stage_fs_c04_initial_alpha import boundary_patches,digest
from stage_fs_c05_vof_cht import (
    CASE_PREFIX, REGION_FIELDS, ATMOSPHERES, MOLD_PATCHES,
    ensure_compressible_kepsilon_divergence,
)

OUTPUT_PREFIX="FS_C05_NATIVE_SMOKE_"
EXPECTED_SOLVERS={"fluid":"compressibleVoF","mold":"solid"}
STOP_TIME=2e-7
MAX_NATIVE_SECONDS=480
SOURCE_STATUS="VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD"


def preflight(source:Path)->dict:
    require(source.is_dir() and not source.is_symlink()
            and source.name.startswith(CASE_PREFIX),
            "not a staged isolated FS-C05 candidate")
    path=source/"FS_C05_PHYSICS_CANDIDATE.json"
    require(path.is_file() and not path.is_symlink(),
            "FS-C05 source physics manifest missing")
    data=json.loads(path.read_text())
    require(data.get("status")==SOURCE_STATUS
            and data.get("new_case")==str(source)
            and data.get("regionSolvers")==EXPECTED_SOLVERS
            and data.get("solver_executed") is False
            and data.get("native_dictionary_validation_done") is False
            and data.get("do_not_execute_without_native_review") is True,
            "FS-C05 source has unapproved or mutated solver status")
    require(data["pilot_reference"]["fluid_sand_contact_faces"]==3136
            and data["pilot_reference"]["mold_support_and_lower_recess_unresolved"] is True,
            "pilot source no longer matches verified contact mesh")
    # The test only runs with the original exact files declared by FS-C05.
    file_hashes=data["written_files_sha256"]
    require(len(file_hashes)>=15,"incomplete native input provenance")
    for relative,expected in file_hashes.items():
        require(not Path(relative).is_absolute() and ".." not in Path(relative).parts,
                "unsafe path in FS-C05 manifest")
        f=source/relative
        require(f.is_file() and not f.is_symlink() and digest(f)==expected,
                "FS-C05 generated input differs from manifest: "+relative)
    for region,fields in REGION_FIELDS.items():
        for name in fields:
            require((source/"0"/region/name).is_file(),
                    "missing "+region+" initial field "+name)
    alpha=source/"0/fluid/alpha.metal"
    values=read_alpha(alpha,expected_cells=FLUID_CELLS)
    require(values.count(1.)==2368 and values.count(0.)==32000,
            "initial metal/air fraction changed")
    initial_T=read_temperature(source/"0/fluid/T",expected_cells=FLUID_CELLS)
    sand_T=read_temperature(source/"0/mold/T",expected_cells=SAND_CELLS)
    require(all((t==1500 if a==1 else t==300)
                for a,t in zip(values,initial_T))
            and set(sand_T)=={300.0},
            "initial temperature-to-VOF map or mold baseline changed")
    mesh=source/"constant/fluid/polyMesh/boundary"
    info=boundary_patches(mesh)
    require(info["fluid_to_mold"]["type"]=="mappedWall"
            and info["fluid_to_mold"]["neighbourRegion"]=="mold"
            and info["fluid_to_mold"]["nFaces"]=="3136",
            "fluid-to-sand interface changed")
    require(all(info[name]["type"]=="patch" for name in ATMOSPHERES),
            "outer gas atmosphere is not open")
    textT=(source/"0/fluid/T").read_text()
    solidT=(source/"0/mold/T").read_text()
    require("type coupledTemperature;" in textT
            and "type coupledTemperature;" in solidT
            and "type inletOutlet;" in textT,
            "missing conjugate heat transfer or atmosphere thermal BC")
    control=(source/"system/controlDict").read_text()
    require(re.search(r"\bfluid\s+compressibleVoF\s*;",control)
            and re.search(r"\bmold\s+solid\s*;",control)
            and re.search(r"\bendTime\s+5e-06\s*;",control)
            and re.search(r"\bdeltaT\s+1e-07\s*;",control)
            and re.search(r"\bmaxCo\s+0\.1\s*;",control),
            "solver pair or original short-run time controls modified")
    require("simulationType  RAS;" in
            (source/"constant/fluid/momentumTransport").read_text()
            and "kEpsilon" in
            (source/"constant/fluid/momentumTransport").read_text(),
            "expected uncalibrated RAS kEpsilon source missing")
    for root,dirs,files in os.walk(source,followlinks=False):
        for name in dirs+files:
            require(not (Path(root)/name).is_symlink(),
                    "symbolic link in FS-C05 source is not accepted")
    return {
        "source_case":str(source),
        "manifest_sha256":digest(path),
        "alpha_sha256":digest(alpha),
        "mesh_contact_faces":3136,
        "input_file_count":len(file_hashes),
        "physical_validation":False,
    }


def short_control(original:str)->str:
    replacements={
        r"(\bendTime\s+)5e-06(\s*;)":r"\g<1>2e-07\2",
        r"(\bwriteControl\s+)adjustableRunTime(\s*;)":r"\g<1>timeStep\2",
        r"(\bwriteInterval\s+)1e-06(\s*;)":r"\g<1>1\2",
        r"(\brunTimeModifiable\s+)true(\s*;)":r"\g<1>false\2",
    }
    control=original
    for pattern,value in replacements.items():
        control,count=re.subn(pattern,value,control)
        require(count==1,"unexpected FS-C05 controlDict: "+pattern)
    require(re.search(r"\bendTime\s+2e-07\s*;",control)
            and re.search(r"\bdeltaT\s+1e-07\s*;",control)
            and re.search(r"\bwriteControl\s+timeStep\s*;",control),
            "native two-step smoke control invalid")
    return control


def validate_run_log(log:str)->dict:
    require("FOAM FATAL" not in log and "Floating point exception" not in log
            and "Segmentation fault" not in log
            and re.search(r"(?m)^\s*End\s*$",log) is not None,
            "OpenFOAM log reports a fatal error, crash or lacks End")
    raw=re.findall(
        r"(?m)^\s*Time\s*=\s*([+\-0-9.eE]+)\s*s?\s*$",log
    )
    times=[float(t) for t in raw]
    require(len(times)>=2 and all(math.isfinite(t) and t>0 for t in times),
            "no two positive native time steps found")
    require(all(b>a for a,b in zip(times,times[1:])),
            "nonmonotone time iteration output")
    require(abs(times[-1]-STOP_TIME) < 1e-10,
            "solver did not finish requested 2e-7s startup")
    # Log provenance is only evidence of execution, NOT conservation of energy.
    return {"completed_time_steps":len(times),
            "last_time_s":times[-1],
            "seen_end_marker":True,
            "conservation_of_energy_verified":False,
            "alpha_mass_conservation_verified":False}


def run(source:Path,dest:Path,native:bool)->dict:
    source=source.expanduser().resolve()
    dest=dest.expanduser().resolve()
    require(dest.name.startswith(OUTPUT_PREFIX)
            and not dest.exists() and not dest.is_symlink(),
            "new isolated FS-C05 native smoke destination required")
    require(source!=dest and dest not in source.parents
            and source not in dest.parents,
            "native smoke cannot run inside the original case or overwrite it")
    proof=preflight(source)
    if native:
        require(os.environ.get("WM_PROJECT_VERSION")=="14",
                "OpenFOAM Foundation 14 not activated")
        require(shutil.which("foamMultiRun") is not None,
                "foamMultiRun not present in Foundation 14 PATH")
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,dest)
    # Remove old postprocess; only preserve fresh solver outputs.
    for p in (dest/"postProcessing",):
        if p.is_dir():
            shutil.rmtree(p)
    # Preserve the fully SHA-verified source. Only the new, disposable
    # run-copy receives the two actual compressible RAS divergence schemes.
    # The old FS-C05 staged case has div(phi,epsilon) but the Foundation14
    # compressible kEpsilon transport calls div(rhoPhi,epsilon) (and k).
    schemes=dest/"system/fluid/fvSchemes"
    repaired,added=ensure_compressible_kepsilon_divergence(
        schemes.read_text(encoding="utf-8"))
    if added:
        schemes.write_text(repaired,encoding="utf-8")
    require("div(rhoPhi,k)" in repaired
            and "div(rhoPhi,epsilon)" in repaired,
            "missing verified compressible kEpsilon RAS transport schemes")
    control=dest/"system/controlDict"
    control.write_text(short_control(control.read_text()))
    data={
        "schema":"masterproject-fs-c05-native-two-step-cht-smoke-v1",
        "status":"NATIVE_TWO_STEP_CH_T_STAGED_NO_SOLVER",
        "source":proof,
        "output":str(dest),
        "foundation14_required":True,
        "region_solvers":EXPECTED_SOLVERS,
        "expected_endTime_s":STOP_TIME,
        "controlDict_after_shortening_sha256":digest(control),
        "rhoPhi_turbulence_schemes_sha256":digest(schemes),
        "rhoPhi_turbulence_schemes_added_in_COPY_only":added,
        "source_FS_C05_schemes_unchanged":True,
        "solver_ran":False,
        "initial_VOF_volume_m3":4.801191628e-05,
        "alpha_field_verified_after_run":False,
        "heat_flux_balance_verified":False,
        "energy_balance_verified":False,
        "solidification_enabled":False,
        "physically_validated":False,
    }
    report=dest/"FS_C05_NATIVE_SMOKE_REPORT.json"
    def save():
        report.write_text(json.dumps(data,indent=2)+"\n")
    save()
    if not native:
        return data
    cmd=["foamMultiRun","-case",str(dest)]
    log=dest/"log.FS_C05_foamMultiRun"
    try:
        proc=subprocess.run(cmd,capture_output=True,text=True,errors="replace",
                            check=False,timeout=MAX_NATIVE_SECONDS)
        log.write_text("COMMAND: "+" ".join(cmd)+"\nEXIT: "+
                       str(proc.returncode)+"\n"+proc.stdout+"\n"+proc.stderr)
        data["solver_ran"]=True
        require(proc.returncode==0,
                "foamMultiRun returned nonzero exit code; inspect log.FS_C05_foamMultiRun")
        metrics=validate_run_log(proc.stdout+"\n"+proc.stderr)
        data.update({
            "status":"NATIVE_TWO_STEP_VOF_CHT_STARTUP_COMPLETED_NOT_VALIDATED",
            "native_log_sha256":digest(log),
            "startup_log":metrics,
        })
    except subprocess.TimeoutExpired as exc:
        log.write_text("TIMEOUT after "+str(MAX_NATIVE_SECONDS)+"s\n"+
                       str(exc.stdout or "")+"\n"+str(exc.stderr or ""))
        data.update({"solver_ran":True,"status":"NATIVE_SMOKE_REJECTED",
                     "failure_reason":"time limit reached",
                     "native_log_sha256":digest(log)})
        save()
        raise ValueError("foamMultiRun timed out; inspect saved log") from exc
    except (OSError,ValueError) as exc:
        data.update({"status":"NATIVE_SMOKE_REJECTED",
                     "failure_reason":str(exc),
                     "native_log_sha256":digest(log) if log.is_file() else None})
        save()
        raise
    save()
    return data


def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--out",type=Path)
    group=ap.add_mutually_exclusive_group()
    group.add_argument("--stage-only",action="store_true",default=False)
    group.add_argument("--native",action="store_true",
                       help="RUN two short coupled VOF+solid solver steps on the NEW copy")
    args=ap.parse_args(argv)
    name=OUTPUT_PREFIX+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    output=args.out or Path.home()/"OpenFOAM"/"FS_C05_NATIVE_SMOKE_RUNS"/name
    try:
        result=run(args.source,output,native=args.native)
        print("FS-C05 STATUS: "+result["status"])
        print("ISOLATED output:",result["output"])
        print("Native CFD executed:",result["solver_ran"])
        print("NO physical CHT balance, metal mass conservation, or solidification VALIDATION.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C05 NATIVE STARTUP BLOCKED: "+str(exc),file=sys.stderr)
        log=output/"log.FS_C05_foamMultiRun"
        if log.is_file() and not log.is_symlink():
            print("FAILED NATIVE COPY:",output,file=sys.stderr)
            print("REAL SOLVER LOG:",log,file=sys.stderr)
            print("--- last 45 native log lines ---",file=sys.stderr)
            for line in log.read_text(errors="replace").splitlines()[-45:]:
                print(line,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
