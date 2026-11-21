#!/usr/bin/env python3
"""FS-C04 3D fluid/sand thermal interface geometry: READ-ONLY / NO CFD.

Requires the accepted Foundation14 alpha-native-copy and re-verifies:
  - exact 0/fluid/alpha.metal provenance and OpenFOAM native integral;
  - identical native fluid/mold mesh compared with isolated alpha source;
  - mappedWall reciprocal fluid_to_mold/mold_to_fluid;
  - 3136 matching polygon faces with opposite normals and matching areas;
  - 1248 initially liquid-metal/sand and 1888 air/sand faces;
  - 128 air/sand TOP and 1760 air/sand LATERAL faces.

Reports explicit areas, NOT heat-transfer coefficients or energy flux.
Never changes a run or starts an OpenFOAM executable.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import (
    _foam_list, read_mesh, FLUID_CELLS, SAND_CELLS, METRE_COORD_SCALE,
)
from run_fs_c04_mesh import patch_info
from verify_fs_c04_native_alpha import (
    check_source, read_native_integral, digest, TARGET_VOLUME_M3,
)

REQUIRED_INTERFACE_FACES = 3136
EXPECTED_GROUP_FACES = {
    "metal_sand": 1248,
    "air_sand_top": 128,
    "air_sand_lateral": 1760,
}
TOLERANCE_AREA_M2 = 1e-12
TOLERANCE_NORMAL_COSINE = 1e-7
TOP_Y_QUANTIZED = 0


def patch_window(mesh_dir:Path,name:str,total_faces:int,expected_n:int,
                 expected_neighbor:str,expected_neighbour_patch:str)->tuple[int,int]:
    boundary=patch_info(mesh_dir/"boundary",name)
    require(boundary.get("type")=="mappedWall"
            and boundary.get("neighbourRegion")==expected_neighbor
            and boundary.get("neighbourPatch")==expected_neighbour_patch,
            "wrong mappedWall reciprocal contact for "+name)
    try:
        start=int(boundary["startFace"])
        number=int(boundary["nFaces"])
    except (ValueError,KeyError) as e:
        raise ValueError("missing native interface face addresses "+name) from e
    require(number==expected_n and start>=0
            and start+number<=total_faces,
            "wrong native face range for "+name)
    return start,number


def polygon_area_vector(points:list[tuple[int,...]],
                        face:tuple[int,...])->tuple[float,float,float]:
    require(len(face)==4 and len(set(face))==4,
            "interface contact must be a quadrilateral")
    p=[[x/METRE_COORD_SCALE for x in points[k]] for k in face]
    require(len({tuple(v) for v in p})==4,
            "degenerate interface quad")
    x=y=z=0.0
    for i,a in enumerate(p):
        b=p[(i+1)%4]
        x+=a[1]*b[2]-a[2]*b[1]
        y+=a[2]*b[0]-a[0]*b[2]
        z+=a[0]*b[1]-a[1]*b[0]
    return x/2,y/2,z/2


def normalized_area(v:tuple[float,float,float])->float:
    return math.sqrt(sum(x*x for x in v))


def face_id(points:list[tuple[int,...]],face:tuple[int,...])->tuple:
    return tuple(sorted(points[k] for k in face))


def compare_interface(fluid:dict,mold:dict,
                      fluid_owner:list[int],mold_owner:list[int],
                      fluid_start:int,mold_start:int,count:int,
                      alpha:list[float], *,
                      enforce_pilot_counts:bool=True)->dict:
    """Compare two actual mappedWall face arrays and classify alpha-owner side."""
    require(len(fluid_owner)==len(fluid["faces"]) and
            len(mold_owner)==len(mold["faces"]),
            "owner array must address all mesh faces")
    require(len(alpha)==fluid["count"] and
            all(x in (0.,1.) for x in alpha),
            "initial liquid/air alpha mask not exact 0/1")
    require(count>0 and 0<=fluid_start<len(fluid_owner)
            and 0<=mold_start<len(mold_owner)
            and fluid_start+count<=len(fluid_owner)
            and mold_start+count<=len(mold_owner),
            "invalid fluid-sand contact face range")
    mold_map={}
    for face_i in range(mold_start,mold_start+count):
        f=mold["faces"][face_i]
        key=face_id(mold["points"],f)
        require(key not in mold_map,"duplicated sand contact face")
        area=polygon_area_vector(mold["points"],f)
        require(normalized_area(area)>0,"non-positive sand contact face area")
        mold_map[key]=(face_i,area)
    groups=defaultdict(lambda:{"faces":0,"area_m2":0.})
    seen=set()
    max_norm_cos_error=0.
    max_area_delta_m2=0.
    for face_i in range(fluid_start,fluid_start+count):
        f=fluid["faces"][face_i]
        key=face_id(fluid["points"],f)
        require(key in mold_map and key not in seen,
                "fluid-sand face mismatch or duplicate contact face")
        seen.add(key)
        _,sand_normal=mold_map[key]
        fluid_normal=polygon_area_vector(fluid["points"],f)
        af=normalized_area(fluid_normal)
        am=normalized_area(sand_normal)
        require(af>0 and am>0,"zero interface face area")
        delta=abs(af-am)
        require(delta<=TOLERANCE_AREA_M2,
                "non-reciprocal interface face area")
        cosine=sum(x*y for x,y in zip(fluid_normal,sand_normal))/(af*am)
        require(cosine<=-1.+TOLERANCE_NORMAL_COSINE,
                "interface normals are not opposite")
        max_area_delta_m2=max(max_area_delta_m2,delta)
        max_norm_cos_error=max(max_norm_cos_error,abs(-1.-cosine))
        own=fluid_owner[face_i]
        require(0<=own<len(alpha),"contact face owner is not a fluid cell")
        if alpha[own]==1.:
            category="metal_sand"
        elif all(fluid["points"][k][1]==TOP_Y_QUANTIZED for k in f):
            category="air_sand_top"
        else:
            category="air_sand_lateral"
        groups[category]["faces"]+=1
        groups[category]["area_m2"]+=af
    require(len(seen)==len(mold_map)==count,
            "fluid/mold interfaces are not a geometric bijection")
    if enforce_pilot_counts:
        require({name:groups[name]["faces"] for name in EXPECTED_GROUP_FACES}
                ==EXPECTED_GROUP_FACES,
                "pilot metal/sand and air/sand contact counts changed")
    total=sum(v["area_m2"] for v in groups.values())
    require(total>0 and math.isfinite(total),"invalid interface total area")
    report={name:{
        "faces":groups[name]["faces"],
        "area_m2":groups[name]["area_m2"],
        "area_cm2":groups[name]["area_m2"]*1e4,
    } for name in EXPECTED_GROUP_FACES}
    return {
        "interface_face_count":count,
        "total_area_m2":total,
        "total_area_cm2":total*1e4,
        "areas_by_initial_contact":report,
        "max_face_area_mismatch_m2":max_area_delta_m2,
        "max_opposite_unit_normal_error":max_norm_cos_error,
        "matched_faces":len(seen),
    }


def audit(accepted_dir:Path)->dict:
    accepted=accepted_dir.expanduser().resolve()
    require(accepted.is_dir() and not accepted.is_symlink()
            and accepted.name.startswith("FS_C04_ALPHA_NATIVE_CHECK_"),
            "not an accepted isolated native alpha-check folder")
    record_path=accepted/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json"
    require(record_path.is_file() and not record_path.is_symlink(),
            "native alpha volume acceptance manifest not found")
    record=json.loads(record_path.read_text())
    require(record.get("status")=="NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD"
            and record.get("native_field_read_verified") is True
            and record.get("native_integral_verified") is True
            and record.get("CFD_or_CHT_executed") is False
            and record.get("destination")==str(accepted),
            "source alpha stage was not natively accepted")
    native=read_native_integral(accepted)
    require(record.get("native_integral")==native,
            "native postProcess volume result changed since acceptance")
    source_record=record.get("source_staged",{})
    src=Path(source_record.get("stage",""))
    prior=check_source(src)
    require(prior==source_record,
            "provenance from alpha stage or native originals changed")
    require(digest(accepted/"0/fluid/alpha.metal")==prior["alpha_sha256"],
            "accepted alpha field differs from verified initial mask")
    for region in ("fluid","mold"):
        for key in ("points","faces","owner","neighbour","boundary"):
            p=accepted/"constant"/region/"polyMesh"/key
            q=src/"constant"/region/"polyMesh"/key
            require(p.is_file() and not p.is_symlink()
                    and digest(p)==digest(q),
                    "natively accepted mesh altered: "+region+"/"+key)
    fluid_path=accepted/"constant/fluid/polyMesh"
    mold_path=accepted/"constant/mold/polyMesh"
    fluid=read_mesh(fluid_path,FLUID_CELLS)
    mold=read_mesh(mold_path,SAND_CELLS)
    f_owner=_foam_list(fluid_path/"owner","owner")
    m_owner=_foam_list(mold_path/"owner","owner")
    fs,n=patch_window(fluid_path,"fluid_to_mold",len(fluid["faces"]),
                      REQUIRED_INTERFACE_FACES,"mold","mold_to_fluid")
    ms,m=patch_window(mold_path,"mold_to_fluid",len(mold["faces"]),
                      REQUIRED_INTERFACE_FACES,"fluid","fluid_to_mold")
    require(n==m==REQUIRED_INTERFACE_FACES,
            "invalid fluid/mold mappedWall face count")
    alpha=read_alpha(accepted/"0/fluid/alpha.metal",
                     expected_cells=FLUID_CELLS)
    areas=compare_interface(fluid,mold,f_owner,m_owner,fs,ms,n,alpha)
    return {
        "schema":"masterproject-fs-c04-native-cht-contact-audit-v1",
        "status":"RECIPROCAL_THERMAL_CONTACT_GEOMETRY_VERIFIED_NO_CHT",
        "native_accepted_alpha_dir":str(accepted),
        "native_acceptance_sha256":digest(record_path),
        "native_metal_volume_m3":native["native_integral_m3"],
        "native_initial_alpha_confirmed":True,
        "fluid_cells":FLUID_CELLS,
        "mold_cells":SAND_CELLS,
        "interface":areas,
        "open_atmosphere_on_domain_exterior_not_mold_wall":True,
        "mold_support_and_recess_geometry_resolved":False,
        "exact_STL_surface_fidelity_verified":False,
        "thermal_contact_conductance_validated":False,
        "air_sand_convective_heat_transfer_calculated":False,
        "interface_heat_flux_balance_verified":False,
        "CFD_CHT_or_solidification_executed":False,
        "notes":[
            "Metal and air refer to INITIAL VOF alpha.metal cell-side labels",
            "This measures geometric areas on native pilot mesh; no heat-flux solving",
            "Air/sand TOP and SIDE contacts must remain coupled walls, never artificial atmospheric openings",
            "Support/base and lower recess physical exposure remain unresolved",
            "Mesh is CAD-approximate, not a production-grade STL conforming QuickCup model",
        ],
    }


def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--accepted",type=Path,required=True)
    args=ap.parse_args(argv)
    try:
        result=audit(args.accepted)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("FS-C04 THERMAL CONTACT AUDIT BLOCKED: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
