#!/usr/bin/env python3
"""FS-C04 verify native initial T in TWO independent region copies. NO CFD.

Foundation OpenFOAM 14: foamPostProcess -region {fluid|mold} -time 0
  -func 'volAverage(T)' and -func 'volIntegrate(T)'.

Prerequisite: user-confirmed independent initial temperature stage.
Re-audits 3136 mappedWall contact faces, native alpha integrals, T phase
assignment, field SHA and region mesh provenance. Stage and previous runs
are READ ONLY. No solver, no contact flux, no cp/rho/k material model.
Calculated T patch boundary conditions remain NON-SOLVING placeholders.

A successful native postprocess plus volume integral comparison proves
only initial temperature fields, NOT physical heat transfer.
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
from audit_fs_c04_split_cells import (
    read_mesh, cell_volume_m3, FLUID_CELLS, SAND_CELLS,
)
from audit_fs_c04_thermal_interfaces import audit as audit_contact
from stage_fs_c04_initial_temperature import (
    check_T, FLUID_PATCHES, MOLD_PATCHES,
    T_METAL_K, T_AIR_K, T_MOLD_K,
)
from stage_fs_c04_initial_alpha import digest

SCHEMA="masterproject-fs-c04-native-T-screening-v1"
RUN_NAMESPACE="FS_C04_T_NATIVE_CHECK_"
SOURCE_NAMESPACE="FS_C04_T_INITIAL_STAGE_"
OPERATIONS=("volAverage","volIntegrate")
REGIONS=("fluid","mold")
RELATIVE_TOLERANCE=1e-7
ABS_TOLERANCE_AVERAGE_K=1e-5
ABS_TOLERANCE_INTEGRATE=1e-9


def guard_paths(source:Path,output:Path)->None:
    require(source.is_dir() and not source.is_symlink()
            and source.name.startswith(SOURCE_NAMESPACE),
            "not an isolated FS-C04 initial-T source")
    require(not output.exists() and not output.is_symlink(),
            "verification folder already exists; refuse overwrite")
    require(output.name.startswith(RUN_NAMESPACE),
            "verification destination outside designated namespace")
    require(source!=output and source not in output.parents
            and output not in source.parents,
            "verification folder cannot overlap original T stage")


def read_stage(source:Path)->dict:
    manifest=source/"FS_C04_INITIAL_T_SCREEN.json"
    require(manifest.is_file() and not manifest.is_symlink(),
            "temperature-screening provenance missing")
    record=json.loads(manifest.read_text())
    require(record.get("schema")==
            "masterproject-fs-c04-isolated-thermal-initial-screen-v1"
            and record.get("status")=="INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT"
            and record.get("destination")==str(source),
            "temperature stage not verified by its own readback")
    require(record.get("T_boundary_conditions_valid_for_solver") is False
            and record.get("CFD_executed") is False
            and record.get("CTH_or_VOF_solver_executed") is False
            and record.get("native_cases_modified") is False,
            "temperature stage incorrectly claims a CHT or CFD solution")
    accepted=Path(record["source_accepted_alpha_case"])
    prior=audit_contact(accepted)
    require(record.get("source_thermal_interface_audit")==prior,
            "contact geometry changed since T staging")
    require(record.get("source_alpha_sha256")==
            digest(source/"0/fluid/alpha.metal")==
            digest(accepted/"0/fluid/alpha.metal"),
            "original alpha field differs from approved source")
    require(record.get("source_native_alpha_manifest_sha256")==
            digest(accepted/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json"),
            "original native alpha acceptance changed")
    require(record.get("screening_initial_T_K")==
            {"metal":T_METAL_K,"air":T_AIR_K,"mold_sand":T_MOLD_K},
            "unreviewed initial thermal screening temperatures")
    fields=record.get("T_fields")
    require(isinstance(fields,list) and len(fields)==2,
            "two T fields from original screening step required")
    alpha=read_alpha(source/"0/fluid/alpha.metal",expected_cells=FLUID_CELLS)
    for region in REGIONS:
        current=check_T(source/"0"/region/"T",region,
                        alpha if region=="fluid" else None)
        require(sum(1 for x in fields if x==current)==1,
                "T field has changed since original readback: "+region)
        for part in ("points","faces","owner","neighbour","boundary"):
            own=source/"constant"/region/"polyMesh"/part
            original=accepted/"constant"/region/"polyMesh"/part
            require(own.is_file() and not own.is_symlink()
                    and digest(own)==digest(original),
                    "source mesh changed: "+region+"/"+part)
    for root,dirs,files in os.walk(source,followlinks=False):
        for name in dirs+files:
            require(not (Path(root)/name).is_symlink(),
                    "temperature source contains a symlink")
    require(not (source/"0/mold/alpha.metal").exists(),
            "mold solid may not receive VOF metal fraction")
    return record


def calculate_expected(source:Path)->dict:
    alpha=read_alpha(source/"0/fluid/alpha.metal",expected_cells=FLUID_CELLS)
    summary={}
    for region,n in (("fluid",FLUID_CELLS),("mold",SAND_CELLS)):
        mesh=read_mesh(source/"constant"/region/"polyMesh",n)
        vals=[T_METAL_K if a==1 else T_AIR_K for a in alpha] \
             if region=="fluid" else [T_MOLD_K]*SAND_CELLS
        require(len(vals)==n,"incomplete region temperature array")
        total_volume=0.
        temperature_integral=0.
        for i,t in enumerate(vals):
            volume=cell_volume_m3(mesh,i)
            total_volume+=volume
            temperature_integral+=t*volume
        require(total_volume>0 and
                math.isfinite(temperature_integral),
                "invalid source mesh volume or temperature integral")
        summary[region]={
            "region_cells":n,
            "expected_volume_m3":total_volume,
            "expected_volume_weighted_T_K":temperature_integral/total_volume,
            "expected_volIntegrate_T_K_m3":temperature_integral,
            "expected_from_native_mesh_geometry":True,
            "thermal_energy_balance_verified":False,
        }
    require(math.isclose(summary["mold"]["expected_volume_weighted_T_K"],
                         T_MOLD_K,abs_tol=1e-8),
            "sand initially nonuniform without approval")
    return summary


def parse_native_data(folder:Path,op:str)->dict:
    require(op in OPERATIONS,"unsupported native T operation")
    token=op+"(T)"
    root=folder/"postProcessing"
    require(root.is_dir(),"OpenFOAM produced no postProcessing output")
    candidates=[]
    for file in root.rglob("volFieldValue.dat"):
        require(file.is_file() and not file.is_symlink(),
                "native data missing or symlinked")
        rows=file.read_text(encoding="utf-8",errors="strict").splitlines()
        heads=[line for line in rows if line.lstrip().startswith("#")
               and token in line]
        if not heads:
            continue
        require(any(re.search(r"\bTime\b",x) for x in heads),
                "native T integration output lacks time header")
        data=[]
        for line in rows:
            line=line.strip()
            if not line or line.startswith("#"):
                continue
            values=line.split()
            require(len(values)==2,
                    "native T result must contain time and one value")
            time,value=tuple(float(x) for x in values)
            require(math.isfinite(time) and math.isfinite(value),
                    "nonfinite native T integral/average")
            data.append((time,value))
        require(len(data)==1 and abs(data[0][0])<1e-12,
                "expected exactly one native T result at time=0")
        candidates.append((file,data[0][1]))
    require(len(candidates)==1,
            "native "+token+" output missing/ambiguous")
    file,value=candidates[0]
    return {
        "native_function":token,
        "value":value,
        "path":str(file.relative_to(folder)),
        "sha256":digest(file),
        "time_s":0.,
    }


def check_value(actual:float,expected:float,op:str,region:str)->None:
    require(math.isfinite(actual) and math.isfinite(expected),
            "nonfinite postProcess result")
    if op=="volAverage":
        require(abs(actual-expected)<=
                max(ABS_TOLERANCE_AVERAGE_K,RELATIVE_TOLERANCE*abs(expected)),
                "native volume-weighted T differs from mesh geometry for "+region)
    else:
        require(abs(actual-expected)<=
                max(ABS_TOLERANCE_INTEGRATE,RELATIVE_TOLERANCE*abs(expected)),
                "native temperature volume integral disagrees for "+region)


def execute(source:Path,output:Path,native:bool)->dict:
    source=source.expanduser().resolve()
    output=output.expanduser().resolve()
    guard_paths(source,output)
    record=read_stage(source)
    expected=calculate_expected(source)
    if native:
        require(os.environ.get("WM_PROJECT_VERSION")=="14",
                "OpenFOAM Foundation 14 must be active")
        require(shutil.which("foamPostProcess") is not None,
                "Foundation14 foamPostProcess executable not found")
    output.mkdir(parents=True,exist_ok=False)
    result={
        "schema":SCHEMA,
        "status":"T_NATIVE_CHECK_STAGED_NO_OPENFOAM",
        "source":str(source),
        "output":str(output),
        "source_screening_manifest_sha256":
            digest(source/"FS_C04_INITIAL_T_SCREEN.json"),
        "T_geometry_expectations":expected,
        "native_postprocess":{},
        "T_field_read_natively":False,
        "native_volume_integrals_verified":False,
        "CFD_or_CHT_executed":False,
        "solver_thermal_BCs_implemented":False,
    }
    manifest=output/"FS_C04_NATIVE_T_ACCEPTANCE.json"
    def write_status():
        manifest.write_text(json.dumps(result,indent=2)+"\n")
    write_status()
    if not native:
        return result
    try:
        for region in REGIONS:
            case=output/("case_"+region)
            shutil.copytree(source,case)
            for key in ("T",):
                require(digest(case/"0"/region/key)==digest(source/"0"/region/key),
                        "region T changed when copied")
            for op in OPERATIONS:
                cmd=[
                    "foamPostProcess","-case",str(case),
                    "-region",region,"-time","0",
                    "-func",op+"(T)"
                ]
                completed=subprocess.run(
                    cmd,capture_output=True,text=True,
                    errors="replace",check=False
                )
                log=output/("log."+region+"."+op)
                log.write_text("COMMAND: "+" ".join(cmd)+"\n"
                               "EXIT: "+str(completed.returncode)+"\n"
                               +completed.stdout+"\n"+completed.stderr)
                require(completed.returncode==0,
                        "foamPostProcess failed; inspect log."+region+"."+op)
                info=parse_native_data(case,op)
                nominal=expected[region][
                    "expected_volume_weighted_T_K" if op=="volAverage"
                    else "expected_volIntegrate_T_K_m3"
                ]
                check_value(info["value"],nominal,op,region)
                info.update({"expected":nominal,
                             "abs_difference":abs(info["value"]-nominal),
                             "log_sha256":digest(log)})
                result["native_postprocess"][region+"."+op]=info
        require(len(result["native_postprocess"])==4,
                "missing native operation for one fluid/solid T field")
        result.update({
            "status":"NATIVE_2_REGION_T_INTEGRALS_VERIFIED_NO_CHT",
            "T_field_read_natively":True,
            "native_volume_integrals_verified":True,
        })
    except (OSError,ValueError) as exc:
        result["status"]="NATIVE_T_READ_OR_INTEGRAL_REJECTED_NO_CHT"
        result["failure_reason"]=str(exc)
        write_status()
        raise
    write_status()
    return result


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--copy-only",action="store_true",
                   help="validate geometry/fields without invoking OpenFOAM")
    a=p.parse_args(argv)
    name=RUN_NAMESPACE+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    out=a.out or Path.home()/"OpenFOAM"/"FS_C04_T_NATIVE_CHECKS"/name
    try:
        report=execute(a.stage,out,not a.copy_only)
        print("FS-C04 T: "+report["status"])
        print("Independent native-check folder:",report["output"])
        if report["native_volume_integrals_verified"]:
            for region in REGIONS:
                print(region,"volAverage(T) K:",
                      report["native_postprocess"][region+".volAverage"]["value"])
                print(region,"volIntegrate(T) K*m3:",
                      report["native_postprocess"][region+".volIntegrate"]["value"])
        print("NO CFD / NO CHT / NO SOLIDIFICATION / no solver-ready thermal BC.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C04 NATIVE T CHECK BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
