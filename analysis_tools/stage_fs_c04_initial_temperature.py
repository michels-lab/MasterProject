#!/usr/bin/env python3
"""FS-C04 screening initial T in both regions; ISOLATED COPY, NO CFD.

Prerequisite: accepted alpha.metal + reciprocal 3136-face native geometry
proof. This deliberately does NOT configure CHT/VOF solvers or claim an
energy-conserving physics model. Read-only relative to all existing runs.

Initial temperatures only: metal 1500 K, outside air 300 K, sand 300 K.
They reproduce screening/reference initial conditions, NOT validated
thermophysical data or measured thermal curves.

All T boundaryField entries are 'calculated' PLACEHOLDERS solely to allow
post-processing field reads: NOT VALID CHT/VOF thermal boundary conditions.
The future solver must replace them with compatible coupledTemperature
fluid/mold and physically open atmospheric inlet/outlet thermal BCs.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha, read_temperature
from audit_fs_c04_split_cells import FLUID_CELLS, SAND_CELLS, METAL_CELLS, GAS_CELLS
from audit_fs_c04_thermal_interfaces import audit as audit_contacts
from stage_fs_c04_initial_alpha import boundary_patches, digest
from run_fs_c04_mesh import patch_info

T_METAL_K=1500.
T_AIR_K=300.
T_MOLD_K=300.
SCHEMA="masterproject-fs-c04-isolated-thermal-initial-screen-v1"
EXPECTED_AREAS_CM2={
    "metal_sand":64.83795213891894,
    "air_sand_top":13.5099,
    "air_sand_lateral":128.34497383364842,
}
FLUID_PATCHES={"fluid_to_mold","atmosphereTop","atmosphereSides","atmosphereLowerSides"}
MOLD_PATCHES={"mold_to_fluid","moldBottom","moldRecessWall","moldRecessRoof"}
MESH_FILES=("points","faces","owner","neighbour","boundary")


def fluid_thermal_values(alpha:list[float])->list[float]:
    require(len(alpha)==FLUID_CELLS,"invalid fluid alpha length")
    require(set(alpha)<={0.,1.} and sum(alpha)==METAL_CELLS,
            "temperature map requires exact, initial binary VOF alpha")
    return [T_METAL_K if a==1. else T_AIR_K for a in alpha]


def create_T(values:list[float],region:str,patches:set[str])->str:
    expected=FLUID_CELLS if region=="fluid" else SAND_CELLS
    require(region in ("fluid","mold") and len(values)==expected,
            "invalid T region or cell count")
    require((region=="fluid" and patches==FLUID_PATCHES)
            or (region=="mold" and patches==MOLD_PATCHES),
            "incorrect thermal field patch set")
    require(all(math.isfinite(x) and x>0 for x in values),
            "nonphysical temperature field")
    initial=("nonuniform List<scalar>\n"+str(expected)+"\n(\n"
             +"\n".join(format(x,".12g") for x in values)+"\n);")
    result=[
        "/* FS-C04 initial temperature SCREENING DATA ONLY. NO CFD/CHT. */",
        "/* ALL BC calculated ARE NON-SOLVING PLACEHOLDERS: DO NOT RUN FOAMRUN. */",
        "FoamFile",
        "{",
        "    version 2.0;",
        "    format ascii;",
        "    class volScalarField;",
        f'    location "0/{region}";',
        "    object T;",
        "}",
        "dimensions [0 0 0 1 0 0 0];",
        "internalField "+initial,
        "boundaryField",
        "{",
    ]
    for name in sorted(patches):
        result+=(
            "    "+name,
            "    {",
            "        type calculated;",
            f"        value uniform {format(T_AIR_K if region=='fluid' else T_MOLD_K,'.12g')};",
            "    }",
        )
    result.append("}")
    return "\n".join(result)+"\n"


def check_T(path:Path,region:str,alpha:list[float]|None=None)->dict:
    require(path.is_file() and not path.is_symlink(),"T field missing/untrusted")
    raw=path.read_text(encoding="utf-8",errors="strict")
    require(re.search(r'\blocation\s+"0/'+region+r'"\s*;',raw) is not None,
            "T field region wrong")
    require(re.search(r"\bdimensions\s+\[0 0 0 1 0 0 0\]\s*;",raw) is not None,
            "T must be absolute temperature (K)")
    values=read_temperature(path,expected_cells=FLUID_CELLS if region=="fluid" else SAND_CELLS)
    expected=fluid_thermal_values(alpha) if region=="fluid" else [T_MOLD_K]*SAND_CELLS
    require(values==expected,
            "T interior not aligned with verified metal/air/sand initial phase")
    patches=FLUID_PATCHES if region=="fluid" else MOLD_PATCHES
    boundary=raw.split("boundaryField",1)[-1]
    found=set(re.findall(r"(?m)^\s*(\w+)\s*\{\s*type\s+calculated\s*;",boundary))
    require(found==patches and boundary.count("type calculated;")==len(patches),
            "non-placeholder or missing T boundary conditions")
    for name in patches:
        require(re.search(r"\b"+name+r"\s*\{\s*type\s+calculated\s*;"
                          r"\s*value\s+uniform\s+300\s*;",boundary) is not None,
                "T boundary data changed from non-solving 300K placeholder")
    return {
        "sha256":digest(path),
        "region":region,
        "cells":len(values),
        "min_T_K":min(values),
        "max_T_K":max(values),
        "mean_T_unweighted_K":sum(values)/len(values),
        "non_solving_boundary_placeholders":True,
    }


def guard_paths(src:Path,out:Path)->None:
    require(src.is_dir() and not src.is_symlink()
            and src.name.startswith("FS_C04_ALPHA_NATIVE_CHECK_"),
            "not an accepted native alpha source")
    require(not out.exists() and not out.is_symlink(),
            "thermal stage already exists; refusing overwrite")
    require(src!=out and src not in out.parents and out not in src.parents,
            "new thermal stage may not overlap verified source")
    require(out.name.startswith("FS_C04_T_INITIAL_STAGE_"),
            "new thermal stage must use its own namespace")


def stage(src:Path,out:Path)->dict:
    src=src.expanduser().resolve()
    out=out.expanduser().resolve()
    guard_paths(src,out)
    base=audit_contacts(src)
    require(base["status"]=="RECIPROCAL_THERMAL_CONTACT_GEOMETRY_VERIFIED_NO_CHT"
            and base["interface"]["interface_face_count"]==3136
            and all(math.isclose(base["interface"]["areas_by_initial_contact"][name]["area_cm2"],
                                 value,rel_tol=1e-8,abs_tol=1e-8)
                    for name,value in EXPECTED_AREAS_CM2.items()),
            "source thermal interface audit or measured areas changed")
    alpha=read_alpha(src/"0/fluid/alpha.metal",expected_cells=FLUID_CELLS)
    require(len(alpha)==FLUID_CELLS and alpha.count(1.)==METAL_CELLS
            and alpha.count(0.)==GAS_CELLS,
            "wrong initial metal/air alpha mask")
    fluid_boundary=boundary_patches(src/"constant/fluid/polyMesh/boundary")
    require(set(fluid_boundary)==FLUID_PATCHES,
            "fluid mesh not matched to approved exterior-air pilot")
    mold_mesh_boundary=src/"constant/mold/polyMesh/boundary"
    require(mold_mesh_boundary.is_file() and not mold_mesh_boundary.is_symlink(),
            "solid mold boundary missing")
    # patch_info checks real native material boundary; avoid assuming defaults.
    for name in MOLD_PATCHES:
        info=patch_info(mold_mesh_boundary,name)
        require(info.get("type")==("mappedWall" if name=="mold_to_fluid" else "wall"),
                "mold native patch type changed: "+name)
    for root,dirs,files in os.walk(src,followlinks=False):
        for name in dirs+files:
            require(not (Path(root)/name).is_symlink(),
                    "symlink in accepted source; copy refused")
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(src,out)
    for region in ("fluid","mold"):
        for name in MESH_FILES:
            before=src/"constant"/region/"polyMesh"/name
            after=out/"constant"/region/"polyMesh"/name
            require(digest(before)==digest(after),"thermal stage mesh copy corrupted")
    require(digest(src/"0/fluid/alpha.metal")==digest(out/"0/fluid/alpha.metal"),
            "thermal staging must not modify native accepted alpha")
    written=[]
    for region,values,patches in (
        ("fluid",fluid_thermal_values(alpha),FLUID_PATCHES),
        ("mold",[T_MOLD_K]*SAND_CELLS,MOLD_PATCHES),
    ):
        directory=out/"0"/region
        require(directory.is_dir() and not directory.is_symlink(),
                "split region initial data directory missing")
        field=directory/"T"
        require(not field.exists() and not field.is_symlink(),
                "T already exists in isolated copy; refusing overwrite")
        field.write_text(create_T(values,region,patches),encoding="utf-8")
        written.append(check_T(field,region,alpha if region=="fluid" else None))
    require(not (out/"0/mold/alpha.metal").exists(),
            "mold must have no metal-air VOF field")
    record={
        "schema":SCHEMA,
        "status":"INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT",
        "source_accepted_alpha_case":str(src),
        "source_thermal_interface_audit":base,
        "source_native_alpha_manifest_sha256":
            digest(src/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json"),
        "source_alpha_sha256":digest(src/"0/fluid/alpha.metal"),
        "destination":str(out),
        "screening_initial_T_K":{
            "metal":T_METAL_K,"air":T_AIR_K,"mold_sand":T_MOLD_K,
        },
        "phase_cell_counts":{"metal":METAL_CELLS,"air":GAS_CELLS,"sand":SAND_CELLS},
        "T_fields":written,
        "T_boundary_conditions_valid_for_solver":False,
        "T_thermophysical_properties_validated":False,
        "native_OpenFOAM_T_read_verified":False,
        "native_OpenFOAM_T_integrals_verified":False,
        "heat_flux_conservation_verified":False,
        "CTH_or_VOF_solver_executed":False,
        "CFD_executed":False,
        "native_cases_modified":False,
        "notes":[
            "T=1500K metal and 300K air/sand are screening assumptions, not measured profiles",
            "Calculated patch fields are non-solving placeholders; do NOT launch CFD",
            "Do not impose exterior 300K as a fixed mold-wall thermal condition",
            "CoupledTemperature/phase-dependent thermodynamics and mold support remain unimplemented",
            "Only static T initial fields; no meaningful sensible/latent energy balance yet",
        ],
    }
    (out/"FS_C04_INITIAL_T_SCREEN.json").write_text(json.dumps(record,indent=2)+"\n")
    return record


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--accepted",type=Path,required=True)
    p.add_argument("--out",type=Path)
    args=p.parse_args(argv)
    name=("FS_C04_T_INITIAL_STAGE_"+datetime.now(timezone.utc).strftime(
          "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8])
    out=args.out or Path.home()/"OpenFOAM"/"FS_C04_T_INITIAL_RUNS"/name
    try:
        result=stage(args.accepted,out)
        print("FS-C04: "+result["status"])
        print("Independent new screening-T case:",result["destination"])
        print("T initial (K):",result["screening_initial_T_K"])
        print("Cells by phase:",result["phase_cell_counts"])
        print("NO CFD, no coupled heat transfer, no solidification.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C04 INITIAL T STAGING BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
