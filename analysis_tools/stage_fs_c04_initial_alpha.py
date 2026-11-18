#!/usr/bin/env python3
"""FS-C04 prepare 0/fluid/alpha.metal on a NEW ISOLATED COPY. NO CFD.

Scientific gate (cannot bypass): independently rerun the validated FS-C03/
FS-C04 parent and split-region mesh geometry correspondence; 2368 metal,
32000 air, 7680 mold cells; compare geometry and source SHA hashes.

Only the split region 'fluid' receives alpha.metal. Sand is a distinct
solid, never initialized with alpha; internal metal-air interface remains
VOF, not a wall. The old native runs remain byte-for-byte untouched.

This writes only an INITIAL FIELD with geometric volume verification.
NO fluid velocity/temperature/thermo/CHT or actual OpenFOAM solver test.
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
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c04_native_metal_mapping import (
    native_status,read_ascii_zones,
)
from audit_fs_c04_split_cells import (
    analyze as audit_split, read_mesh,match_region,cell_volume_m3,
    FLUID_CELLS, METAL_CELLS,GAS_CELLS,
    MAX_RELATIVE_METAL_VOLUME_DIFFERENCE,
)
from audit_fs_c02_local import read_alpha

ATMOSPHERE_PATCHES={
    "atmosphereTop":448,
    "atmosphereSides":3040,
    "atmosphereLowerSides":256,
}
MOLD_CONTACT_NAME="fluid_to_mold"
MOLD_CONTACT_FACES=3136
SOURCE_FILES=("points","faces","owner","neighbour","boundary")


def digest(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metal_cell_ids(c03:Path,c04:Path,proof:dict) -> list[int]:
    """Recompute the split-native IDs from geometry, not guessed ordering."""
    old=native_status(c03,3)
    new=native_status(c04,2)
    zones3=read_ascii_zones(old["parent_mesh"]/"cellZones",
                            {"metal","air","mold"})
    zones4=read_ascii_zones(new["parent_mesh"]/"cellZones",{"fluid","mold"})
    parent=read_mesh(new["parent_mesh"],42048)
    fluid=read_mesh(new["run"]/"constant/fluid/polyMesh",FLUID_CELLS)
    correspondence=match_region(parent,fluid,zones4["fluid"])
    metal=sorted(i for i,j in correspondence.items() if j in zones3["metal"])
    gas=sorted(i for i,j in correspondence.items() if j in zones3["air"])
    require(len(metal)==METAL_CELLS and len(gas)==GAS_CELLS
            and len(set(metal).intersection(gas))==0
            and set(metal).union(gas)==set(range(FLUID_CELLS)),
            "fluid cell IDs do not cleanly partition into metal and air")
    sha=hashlib.sha256(",".join(map(str,metal)).encode()).hexdigest()
    require(sha==proof["seeded_split_fluid_cell_id_list_sha256"],
            "metal indices hash no longer matches native geometry audit")
    return metal


def boundary_patches(file:Path)->dict[str,dict[str,str]]:
    require(file.is_file() and not file.is_symlink(),
            "fluid native boundary file missing")
    raw=file.read_text()
    patches={}
    for match in re.finditer(r"(?m)^\s*(\w+)\s*\{([^{}]*)\}",raw,re.S):
        name=match.group(1)
        if name=="FoamFile":
            continue
        require(name not in patches,"duplicate fluid patch "+name)
        body=match.group(2)
        patches[name]=dict(re.findall(
            r"(\w+)\s+([^;]+?)\s*;",body
        ))
        patches[name]={k:v.strip().split()[0] for k,v in patches[name].items()}
    expected=set(ATMOSPHERE_PATCHES)|{MOLD_CONTACT_NAME}
    require(set(patches)==expected,
            "unexpected/missing fluid patches: "+str(sorted(set(patches)^expected)))
    for name,count in ATMOSPHERE_PATCHES.items():
        p=patches[name]
        require(p.get("type")=="patch" and
                p.get("nFaces")==str(count),
                "outlet atmosphere is not an OPEN patch: "+name)
    wall=patches[MOLD_CONTACT_NAME]
    require(wall.get("type")=="mappedWall" and
            wall.get("nFaces")==str(MOLD_CONTACT_FACES) and
            wall.get("neighbourRegion")=="mold" and
            wall.get("neighbourPatch")=="mold_to_fluid",
            "incorrect reciprocal interface to solid sand")
    return patches


def make_alpha(values:list[float], boundary:dict)->str:
    require(len(values)==FLUID_CELLS, "wrong fluid field cell count")
    require(set(values)<={0.0,1.0} and
            sum(values)==METAL_CELLS,
            "alpha must contain exactly 2368 full-metal cells and air elsewhere")
    require(set(boundary)==set(ATMOSPHERE_PATCHES)|{MOLD_CONTACT_NAME},
            "wrong fluid boundary patch set")
    out=[
        "/* FS-C04 isolated initial volume fraction only. NO CFD. */",
        "FoamFile",
        "{",
        "    version     2.0;",
        "    format      ascii;",
        "    class       volScalarField;",
        "    location    \"0/fluid\";",
        "    object      alpha.metal;",
        "}",
        "dimensions      [0 0 0 0 0 0 0];",
        "internalField   nonuniform List<scalar>",
        str(len(values)),
        "(",
        *["1" if x==1 else "0" for x in values],
        ");",
        "boundaryField",
        "{",
        "    fluid_to_mold",
        "    {",
        "        type       zeroGradient;",
        "    }",
    ]
    for name in ATMOSPHERE_PATCHES:
        out.extend([
            "    "+name,
            "    {",
            "        type       inletOutlet;",
            "        inletValue uniform 0;",
            "        value      uniform 0;",
            "    }"
        ])
    out.append("}")
    return "\n".join(out)+"\n"


def verify_alpha_file(file:Path,metal:list[int],mesh:dict,expected_volume:float
                      )->dict:
    vals=read_alpha(file,expected_cells=FLUID_CELLS)
    metal_set=set(metal)
    require(sum(v==1 for v in vals)==METAL_CELLS and
            sum(v==0 for v in vals)==GAS_CELLS and
            all((v==1)==(i in metal_set) for i,v in enumerate(vals)),
            "written alpha field incorrectly maps metal or air")
    raw=file.read_text()
    require(re.search(r"\bdimensions\s+\[0 0 0 0 0 0 0\]\s*;",raw)
            is not None,"alpha.metal must be dimensionless")
    require(re.search(r"\blocation\s+\"0/fluid\"\s*;",raw) is not None,
            "alpha.metal must be in 0/fluid, not mold")
    boundary_part=raw.split("boundaryField",1)[-1]
    for name in ATMOSPHERE_PATCHES:
        require(re.search(r"\b"+name+r"\s*\{\s*type\s+inletOutlet\s*;"
                          r"\s*inletValue\s+uniform\s+0\s*;"
                          r"\s*value\s+uniform\s+0\s*;",boundary_part) is not None,
                "atmospheric gas backflow must be alpha.metal=0")
    require(re.search(r"\bfluid_to_mold\s*\{\s*type\s+zeroGradient\s*;",
                      boundary_part) is not None,
            "no solid-wall alpha normal gradient should be imposed")
    volume=sum(cell_volume_m3(mesh,i) for i in metal)
    rel=abs(volume-expected_volume)/expected_volume
    require(rel<=MAX_RELATIVE_METAL_VOLUME_DIFFERENCE,
            "alpha-weighted geometric metal volume deviates from audited pilot")
    return {
        "field_sha256":digest(file),
        "fluid_cell_count":len(vals),
        "metal_cell_count":METAL_CELLS,
        "air_cell_count":GAS_CELLS,
        "alpha_min":min(vals),
        "alpha_max":max(vals),
        "sum_alpha":sum(vals),
        "geometric_sum_alphaV_m3":volume,
        "reference_split_geometric_metal_volume_m3":expected_volume,
        "relative_volume_difference":rel,
        "all_atmospheric_backflows_are_air":True,
        "native_OpenFOAM_field_read_verified":False,
        "native_OpenFOAM_volFieldValue_integral_verified":False,
        "physical_thermophysical_models_or_solver_executed":False,
    }


def stage(c03:Path,c04:Path,out:Path)->dict:
    c03,c04,out=tuple(p.expanduser().resolve() for p in (c03,c04,out))
    require(not out.exists(),"refuse existing destination; no overwrite")
    require(out!=c03 and out!=c04 and
            c03 not in out.parents and c04 not in out.parents and
            out not in c03.parents and out not in c04.parents,
            "output may not overlap original native runs")
    proof=audit_split(c03,c04)
    require(proof["status"]==
            "SPLIT_FLUID_METAL_MAPPING_VERIFIED_NO_FIELD_WRITTEN",
            "native split-region mapping not approved")
    metal=metal_cell_ids(c03,c04,proof)
    src_boundary=c04/"constant/fluid/polyMesh/boundary"
    boundary=boundary_patches(src_boundary)
    # SOURCE SAFETY: Reject ALL symlinks before copying a native mesh.
    for root,dirs,files in os.walk(c04,followlinks=False):
        for name in dirs+files:
            require(not (Path(root)/name).is_symlink(),
                    "source contains symlink, cannot copy safely")
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(c04,out,symlinks=False)
    for tag,path in (("parent",out/"constant/polyMesh"),
                     ("fluid",out/"constant/fluid/polyMesh"),
                     ("mold",out/"constant/mold/polyMesh")):
        for key in SOURCE_FILES:
            actual=path/key
            source=c04/"constant"/("polyMesh" if tag=="parent"
                                  else tag+"/polyMesh")/key
            require(digest(actual)==digest(source),
                    "copy changed native polyMesh "+tag+"/"+key)
    native_fluid=read_mesh(out/"constant/fluid/polyMesh",FLUID_CELLS)
    check_boundary=boundary_patches(out/"constant/fluid/polyMesh/boundary")
    require(check_boundary==boundary,
            "copy changed atmospheric outlet or mold interface patches")
    values=[0.0]*FLUID_CELLS
    for i in metal:
        values[i]=1.0
    field_dir=out/"0/fluid"
    require(not field_dir.is_symlink(),"unexpected symlink in fluid 0 directory")
    field_dir.mkdir(parents=True,exist_ok=True)
    field=field_dir/"alpha.metal"
    require(not field.exists() and not field.is_symlink(),
            "unexpected preexisting alpha field")
    field.write_text(make_alpha(values,boundary))
    verification=verify_alpha_file(
        field,metal,native_fluid,
        proof["metal_volume_from_split_fluid_polyhedron_m3"],
    )
    require(not (out/"0/mold/alpha.metal").exists(),
            "mold solid may not receive VOF alpha field")
    record={
        "schema":"masterproject-fs-c04-isolated-initial-alpha-v1",
        "status":"INITIAL_ALPHA_STAGED_GEOMETRY_ONLY_NO_CFD",
        "new_isolated_case":str(out),
        "source_original_FS_C03":str(c03),
        "source_original_FS_C04":str(c04),
        "source_FS_C04_native_status_sha256":
            digest(c04/"FS_C04_NATIVE_STATUS.json"),
        "source_FS_C03_native_status_sha256":
            digest(c03/"FS_C03_NATIVE_STATUS.json"),
        "source_split_proof":proof,
        "alpha_field":str(field.relative_to(out)),
        "field_check":verification,
        "original_cases_are_untouched":True,
        "can_run_CHT_or_VOF_now":False,
        "physical_CAD_surface_fidelity_verified":False,
        "solidification_and_shrinkage_not_modelled":True,
        "notes":[
            "Purely geometric initialization of two fluid phases, not a simulation",
            "OpenFOAM native read and volume integral still to be performed",
            "Only alpha.metal initialized; T, U, p, thermo, turbulence and CHT absent",
            "External air includes top and four mold sidewalls; support/base unresolved",
        ],
    }
    (out/"FS_C04_ALPHA_INITIALIZATION.json").write_text(
        json.dumps(record,indent=2)+"\n"
    )
    return record


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fs-c03",type=Path,required=True)
    p.add_argument("--fs-c04",type=Path,required=True)
    p.add_argument("--out",type=Path)
    a=p.parse_args(argv)
    name=("FS_C04_ALPHA_STAGE_"+datetime.now(timezone.utc).strftime(
          "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8])
    out=(a.out or Path.home()/"OpenFOAM"/"FS_C04_ALPHA_RUNS"/name)
    try:
        report=stage(a.fs_c03,a.fs_c04,out)
        v=report["field_check"]
        print("FS-C04 ALPHA: "+report["status"])
        print("New isolated copy: "+report["new_isolated_case"])
        print("metal cells:",v["metal_cell_count"],"air:",v["air_cell_count"])
        print("geometric sum(alpha*V) m3:",v["geometric_sum_alphaV_m3"])
        print("alpha field SHA256:",v["field_sha256"])
        print("NO CFD. Native field/volume acceptance not yet tested.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C04 ALPHA STAGING BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
