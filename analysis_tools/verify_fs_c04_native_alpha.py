#!/usr/bin/env python3
"""FS-C04 native Foundation14 alpha.metal volume integral on a NEW COPY.

Requires the previously approved isolated 0/fluid/alpha.metal stage:
  INITIAL_ALPHA_STAGED_GEOMETRY_ONLY_NO_CFD.
READ-ONLY against source FS-C03, FS-C04 and staged alpha folder.
Copies the last folder to a new, unique independent location. Then uses
ONLY Foundation14 foamPostProcess -func 'volIntegrate(alpha.metal)' in
fluid region at t=0; NO foamRun, no CFD, no heat solver.
Parses actual postProcessing volFieldValue.dat; never treats zero errors,
missing field output, or a process return code alone as verification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
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
from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import analyze as prove_split, read_mesh, FLUID_CELLS
from stage_fs_c04_initial_alpha import (
    boundary_patches, digest, metal_cell_ids, verify_alpha_file,
)

TARGET_VOLUME_M3 = 4.801191628e-5
RELATIVE_TOLERANCE = .002
FUNCTION_NAME="volIntegrate(alpha.metal)"


def guard_paths(stage:Path, destination:Path)->None:
    require(stage.is_dir() and not stage.is_symlink(),"alpha stage missing/untrusted")
    require(stage.name.startswith("FS_C04_ALPHA_STAGE_"),
            "not an isolated FS-C04 alpha stage")
    require(not destination.exists() and not destination.is_symlink(),
            "destination already exists; never overwrite")
    require(destination!=stage and stage not in destination.parents and
            destination not in stage.parents,
            "destination may not overlap original alpha stage")
    require("FS_C04_ALPHA_NATIVE_CHECK_" in destination.name,
            "destination does not use dedicated native-check namespace")


def check_source(stage:Path)->dict:
    record_file=stage/"FS_C04_ALPHA_INITIALIZATION.json"
    require(record_file.is_file() and not record_file.is_symlink(),
            "missing isolated alpha staging manifest")
    record=json.loads(record_file.read_text())
    require(record.get("status")=="INITIAL_ALPHA_STAGED_GEOMETRY_ONLY_NO_CFD"
            and record.get("new_isolated_case")==str(stage),
            "unapproved stage or mismatch to source location")
    require(record.get("can_run_CHT_or_VOF_now") is False and
            record.get("original_cases_are_untouched") is True,
            "alpha stage contradicts geometric-only scope")
    c03=Path(record["source_original_FS_C03"])
    c04=Path(record["source_original_FS_C04"])
    # Provenance/geometry verified AGAIN immediately before native postProcess.
    proof=prove_split(c03,c04)
    require(proof["status"]=="SPLIT_FLUID_METAL_MAPPING_VERIFIED_NO_FIELD_WRITTEN"
            and record.get("source_split_proof")==proof,
            "stale or changed native split-cell provenance")
    metal=metal_cell_ids(c03,c04,proof)
    field=stage/"0/fluid/alpha.metal"
    require(field.is_file() and not field.is_symlink(),
            "staged alpha.metal field missing/untrusted")
    require(record.get("alpha_field")=="0/fluid/alpha.metal" and
            digest(field)==record["field_check"]["field_sha256"],
            "alpha field SHA mismatch; refuse untrusted physical state")
    boundary=boundary_patches(stage/"constant/fluid/polyMesh/boundary")
    check=verify_alpha_file(field,metal,
                            read_mesh(stage/"constant/fluid/polyMesh",FLUID_CELLS),
                            proof["metal_volume_from_split_fluid_polyhedron_m3"])
    require(check==record["field_check"],
            "staged alpha field and geometric volume have changed")
    require(abs(check["geometric_sum_alphaV_m3"]-TARGET_VOLUME_M3)/
            TARGET_VOLUME_M3 < RELATIVE_TOLERANCE,
            "geometric seed volume not the accepted pilot")
    for name in ("points","faces","owner","neighbour"):
        expected=proof["checked_polymesh_sha256"]["fluid"][name]
        require(digest(stage/"constant/fluid/polyMesh"/name)==expected,
                "staged fluid mesh differs from accepted native split")
    require(boundary["fluid_to_mold"]["type"]=="mappedWall",
            "solid mold interface no longer native mappedWall")
    require(not (stage/"0/mold/alpha.metal").exists(),
            "alpha.metal must never be assigned to solid sand")
    for root,dirs,files in os.walk(stage,followlinks=False):
        for name in dirs+files:
            require(not (Path(root)/name).is_symlink(),
                    "source contains symlink; never clone untrusted source")
    return {
        "stage":str(stage),
        "manifest_sha256":digest(record_file),
        "alpha_sha256":digest(field),
        "geometric_volume_m3":check["geometric_sum_alphaV_m3"],
        "alpha_metal_cells":check["metal_cell_count"],
        "alpha_air_cells":check["air_cell_count"],
        "origin_FS_C03":str(c03),
        "origin_FS_C04":str(c04),
    }


def read_native_integral(folder:Path)->dict:
    post=folder/"postProcessing"
    require(post.is_dir(),"foamPostProcess produced no postProcessing folder")
    candidates=[]
    for file in post.rglob("volFieldValue.dat"):
        require(not file.is_symlink(),"untrusted native integral data")
        lines=file.read_text(encoding="utf-8",errors="strict").splitlines()
        heads=[s for s in lines if s.lstrip().startswith("#")
               and FUNCTION_NAME in s]
        if heads:
            require(any("Time" in s for s in heads),
                    "native integral header lacks time")
            values=[]
            for line in lines:
                stripped=line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                parts=stripped.split()
                require(len(parts)==2,
                        "native volFieldValue must contain time + one integral")
                t,v=(float(x) for x in parts)
                require(math.isfinite(t) and math.isfinite(v),
                        "non-finite native integral")
                values.append((t,v))
            require(len(values)==1 and math.isclose(values[0][0],0.,abs_tol=1e-12),
                    "native result must have exactly one t=0 integral")
            candidates.append((file,values[0][1]))
    require(len(candidates)==1,
            "missing or ambiguous native volIntegrate(alpha.metal) data")
    file,volume=candidates[0]
    rel=abs(volume-TARGET_VOLUME_M3)/TARGET_VOLUME_M3
    require(volume>0 and rel<=RELATIVE_TOLERANCE,
            "OpenFOAM native integrated metal volume disagrees with pilot: "
            +str(volume))
    return {
        "native_function":FUNCTION_NAME,
        "native_result_file":str(file.relative_to(folder)),
        "native_result_sha256":digest(file),
        "native_integral_m3":volume,
        "expected_geom_m3":TARGET_VOLUME_M3,
        "relative_difference":rel,
        "within_0_2_percent_tolerance":True,
    }


def execute(stage:Path,destination:Path,run_native:bool)->dict:
    stage=stage.expanduser().resolve()
    destination=destination.expanduser().resolve()
    guard_paths(stage,destination)
    proof=check_source(stage)
    if run_native:
        require(os.environ.get("WM_PROJECT_VERSION")=="14",
                "requires activated OpenFOAM Foundation14")
        require(shutil.which("foamPostProcess") is not None,
                "foamPostProcess (Foundation14) is not on PATH")
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(stage,destination)
    log_file=destination/"FS_C04_NATIVE_ALPHA_POSTPROCESS.log"
    manifest_file=destination/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json"
    output={
        "schema":"masterproject-fs-c04-native-alpha-integral-v1",
        "status":"CLONED_NOT_NATIVE_VALIDATED",
        "source_staged":proof,
        "destination":str(destination),
        "native_field_read_verified":False,
        "native_integral_verified":False,
        "CFD_or_CHT_executed":False,
        "no_original_cases_modified":True,
    }
    manifest_file.write_text(json.dumps(output,indent=2)+"\n")
    if not run_native:
        return output
    cmd=[
        "foamPostProcess","-case",str(destination),"-region","fluid",
        "-time","0","-func",FUNCTION_NAME
    ]
    run=subprocess.run(cmd,capture_output=True,text=True,errors="replace",
                       check=False)
    log_file.write_text("COMMAND: "+" ".join(cmd)+"\n"+
                        "EXIT: "+str(run.returncode)+"\n"+
                        run.stdout+"\n"+run.stderr)
    try:
        require(run.returncode==0,
                "foamPostProcess returned nonzero status; inspect native log")
        integral=read_native_integral(destination)
        output.update({
            "status":"NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD",
            "native_field_read_verified":True,
            "native_integral_verified":True,
            "native_integral":integral,
            "native_command":cmd,
            "native_log_sha256":digest(log_file),
        })
    except (OSError,ValueError) as exc:
        output["status"]="NATIVE_ALPHA_INTEGRAL_REJECTED_NO_CFD"
        output["failure_reason"]=str(exc)
        output["native_log_sha256"]=digest(log_file)
        manifest_file.write_text(json.dumps(output,indent=2)+"\n")
        raise
    manifest_file.write_text(json.dumps(output,indent=2)+"\n")
    return output


def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--copy-only",action="store_true",
                    help="clone & audit, do not execute foamPostProcess")
    args=ap.parse_args(argv)
    name="FS_C04_ALPHA_NATIVE_CHECK_"+datetime.now(timezone.utc).strftime(
         "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    out=args.out or Path.home()/"OpenFOAM"/"FS_C04_ALPHA_NATIVE_CHECKS"/name
    try:
        result=execute(args.stage,out,not args.copy_only)
        print("FS-C04: "+result["status"])
        print("New verified-copy path: "+result["destination"])
        if result.get("native_integral_verified"):
            print("OpenFOAM native volume m3:",
                  result["native_integral"]["native_integral_m3"])
        print("NO CFD / no CHT / no solidification / no shrinkage.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C04 NATIVE ALPHA BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
