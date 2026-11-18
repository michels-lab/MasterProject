#!/usr/bin/env python3
"""FS-C04: prove EXACT split-fluid cell mapping; READ ONLY, NO CFD.

The Foundation14 parent meshes FS-C03 and FS-C04 passed, and the
metal+air labels in their parent cellZones are proven identical. A new
fluid/mold region from splitMeshRegions renumbers cells; therefore a
parent's cell label MUST NOT be assigned to 0/fluid/alpha.metal.

Recover a bijection by 8 corner COORDINATES of each *native* hexahedron
rather than by indices, comparing the separately numbered fluid/mold
mesh with the identical parent mesh. Sum actual 2368 metal CELL volumes
as nonoverlapping convex hexahedral tetrahedra from the split fluid
polyMesh, and compare against analytic CAD-approximation volume.

Never create fields, write to a run, invoke a solver, or alter FS-C03/4.
A test failure is a scientific gate, not a reason to assume ordering.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from audit_fs_c03_exterior_mesh import require
from audit_fs_c04_metal_seed import (
    audit as metal_plan, METAL_CELLS, GAS_CELLS,
    SAND_CELLS, FLUID_CELLS,
)
from audit_fs_c04_native_metal_mapping import (
    analyze as parent_match, native_status, read_ascii_zones,
)

# 1 nanometre quantization, while intended local cell edge dimensions
# are millimetres. Differences beyond this resolution cause a hard fail.
METRE_COORD_SCALE = 1_000_000_000
MAX_RELATIVE_METAL_VOLUME_DIFFERENCE = 0.002
MESH_FIELDS = ("points", "faces", "owner", "neighbour")


def _foam_list(path: Path, kind: str) -> list:
    require(path.is_file() and not path.is_symlink(),
            "missing/untrusted native polyMesh file: "+str(path))
    raw=path.read_text(encoding="utf-8",errors="strict")
    require(re.search(r"\bformat\s+ascii\s*;",raw[:1000]) is not None,
            "native "+kind+" file not ASCII; no guessed binary parsing")
    lines=raw.splitlines()
    begin=None
    expected=None
    for i in range(len(lines)-1):
        line=lines[i].split("//",1)[0].strip()
        nxt=lines[i+1].split("//",1)[0].strip()
        if line.isdigit() and nxt=="(":
            expected=int(line)
            begin=i+2
            break
    require(begin is not None,"no standard OpenFOAM "+kind+" List header")
    values=[]
    if kind=="points":
        rx=re.compile(
            r"^\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)$"
        )
        for line in lines[begin:]:
            t=line.split("//",1)[0].strip()
            if t==")":
                break
            if not t:
                continue
            m=rx.fullmatch(t)
            require(m is not None,"invalid point record: "+t[:80])
            xyz=tuple(float(v) for v in m.groups())
            require(all(math.isfinite(v) and abs(v)<10. for v in xyz),
                    "mesh coordinates not finite or outside safe metric bounds")
            values.append(tuple(int(round(v*METRE_COORD_SCALE))
                                for v in xyz))
    elif kind=="faces":
        rx=re.compile(r"^(?:(\d+)\s*)?\(\s*([\d\s]+?)\s*\)$")
        for line in lines[begin:]:
            t=line.split("//",1)[0].strip()
            if t==")":
                break
            if not t:
                continue
            m=rx.fullmatch(t)
            require(m is not None,"invalid hexa face record: "+t[:80])
            face=tuple(int(v) for v in m.group(2).split())
            require(len(face)==4 and len(set(face))==4,
                    "non-quad or degenerate face; topology changed")
            require(m.group(1) is None or int(m.group(1))==4,
                    "unexpected OpenFOAM face size")
            values.append(face)
    else:
        require(kind in ("owner","neighbour"),"unsupported mesh list type")
        for line in lines[begin:]:
            t=line.split("//",1)[0].strip()
            if t==")":
                break
            if not t:
                continue
            require(t.isdigit(),"invalid "+kind+" cell index")
            values.append(int(t))
    require(len(values)==expected,
            f"{kind}: list count {len(values)} != declared {expected}")
    require(expected>0 or (kind=="neighbour" and expected==0),
            "empty native mesh list "+kind)
    return values


def read_mesh(path: Path, expected_cells: int) -> dict:
    mesh=path.resolve()
    points=_foam_list(mesh/"points","points")
    faces=_foam_list(mesh/"faces","faces")
    owner=_foam_list(mesh/"owner","owner")
    neighbour=_foam_list(mesh/"neighbour","neighbour")
    require(len(owner)==len(faces) and len(neighbour)<len(faces),
            "native face owner/neighbor counts incompatible")
    require(len(set(points))==len(points),
            "duplicate point coordinates at nanometre precision")
    require(all(0<=x<expected_cells for x in owner+neighbour),
            "owner/neighbour cell label out of bounds")
    require(max(owner+neighbour)==expected_cells-1,
            "native region cell count/addressing inconsistent")
    require(all(0<=i<len(points) for face in faces for i in face),
            "invalid native face point address")
    cell_faces=[[] for _ in range(expected_cells)]
    cell_nodes=[set() for _ in range(expected_cells)]
    for face_id,(face,cell) in enumerate(zip(faces,owner)):
        cell_faces[cell].append(face_id)
        cell_nodes[cell].update(face)
        if face_id<len(neighbour):
            n=neighbour[face_id]
            require(cell!=n,"face owner and neighbour identical")
            cell_faces[n].append(face_id)
            cell_nodes[n].update(face)
    require(all(len(cell_faces[i])==6 and len(cell_nodes[i])==8
                for i in range(expected_cells)),
            "native mesh contains non-hexahedra or disconnected cell")
    signatures=[]
    index={}
    for cid,nodes in enumerate(cell_nodes):
        key=tuple(sorted(points[n] for n in nodes))
        require(key not in index,
                "duplicate geometric cell signatures")
        signatures.append(key)
        index[key]=cid
    return {
        "path":mesh, "points":points, "faces":faces,
        "cell_faces":cell_faces, "cell_nodes":cell_nodes,
        "signatures":signatures, "key_to_cell":index,
        "count":expected_cells,
    }


def cell_volume_m3(mesh:dict, cell_id:int)->float:
    """Volume of convex 8-vertex polyhedron triangulated from its centroid.

    Quadrilateral faces are triangulated; check agreement with analytical
    tapered pilot volume, NOT claimed as OpenFOAM's native V integral.
    """
    nodes=mesh["cell_nodes"][cell_id]
    p=mesh["points"]
    centroid=tuple(sum(p[v][j]/METRE_COORD_SCALE for v in nodes)/8
                   for j in range(3))
    volume=0.
    for fi in mesh["cell_faces"][cell_id]:
        face=mesh["faces"][fi]
        a=[p[face[0]][j]/METRE_COORD_SCALE-centroid[j] for j in range(3)]
        for k in (1,2):
            b=[p[face[k]][j]/METRE_COORD_SCALE-centroid[j]
               for j in range(3)]
            c=[p[face[k+1]][j]/METRE_COORD_SCALE-centroid[j]
               for j in range(3)]
            cross=(b[1]*c[2]-b[2]*c[1],
                   b[2]*c[0]-b[0]*c[2],
                   b[0]*c[1]-b[1]*c[0])
            volume+=abs(sum(a[j]*cross[j] for j in range(3)))/6.
    require(math.isfinite(volume) and volume>0,
            "nonpositive or invalid fluid cell volume")
    return volume


def match_region(parent: dict, child:dict, allowed_labels:set[int]
                 ) -> dict[int,int]:
    """Return child cell label -> parent cell label using hexa coordinates."""
    require(child["count"]==len(allowed_labels),
            "split region size != native parent cellZone")
    used=set()
    correspondence={}
    for child_id,key in enumerate(child["signatures"]):
        parent_id=parent["key_to_cell"].get(key)
        require(parent_id is not None and parent_id in allowed_labels,
                "split-region cell not found in allowed parent zone")
        require(parent_id not in used,"non-bijective geometric cell mapping")
        used.add(parent_id)
        correspondence[child_id]=parent_id
    require(used==allowed_labels,
            "native split region did not cover exactly all parent zone cells")
    return correspondence


def analyze(c03_dir: Path, c04_dir: Path) -> dict:
    parent_proof=parent_match(c03_dir,c04_dir)
    old=native_status(c03_dir,3)
    new=native_status(c04_dir,2)
    three=read_ascii_zones(old["parent_mesh"]/"cellZones",
                           {"metal","air","mold"})
    two=read_ascii_zones(new["parent_mesh"]/"cellZones",
                         {"fluid","mold"})
    require(three["metal"]|three["air"]==two["fluid"] and
            three["mold"]==two["mold"],
            "native parent zone labels not identical")
    parent=read_mesh(new["parent_mesh"],FLUID_CELLS+SAND_CELLS)
    fluid=read_mesh(new["run"]/"constant/fluid/polyMesh",FLUID_CELLS)
    mold=read_mesh(new["run"]/"constant/mold/polyMesh",SAND_CELLS)
    fluid_to_parent=match_region(parent,fluid,two["fluid"])
    mold_to_parent=match_region(parent,mold,two["mold"])
    seeded=[cid for cid,parent_id in fluid_to_parent.items()
            if parent_id in three["metal"]]
    gas=[cid for cid,parent_id in fluid_to_parent.items()
         if parent_id in three["air"]]
    require(len(seeded)==METAL_CELLS and len(gas)==GAS_CELLS
            and not(set(seeded)&set(gas)),
            "metal/air phases mapped incorrectly into FLUID split mesh")
    require(len(mold_to_parent)==SAND_CELLS,
            "sand cells not fully contained in mold split")
    geometric_volume_m3=sum(cell_volume_m3(fluid,cid) for cid in seeded)
    plan=metal_plan()
    expected_m3=plan["pilot_initial_metal_volume_m3"]
    err=abs(geometric_volume_m3-expected_m3)/expected_m3
    require(err<MAX_RELATIVE_METAL_VOLUME_DIFFERENCE,
            f"mesh-derived seed volume disagrees with analytic metal: rel={err}")
    source_hashes={}
    for tag,mesh in (("parent",new["parent_mesh"]),
                     ("fluid",new["run"]/"constant/fluid/polyMesh"),
                     ("mold",new["run"]/"constant/mold/polyMesh")):
        source_hashes[tag]={key:hashlib.sha256((mesh/key).read_bytes()).hexdigest()
                            for key in MESH_FIELDS}
    seeded.sort()
    return {
        "schema":"masterproject-fs-c04-split-fluid-metal-cell-map-v1",
        "status":"SPLIT_FLUID_METAL_MAPPING_VERIFIED_NO_FIELD_WRITTEN",
        "FS_C03_native_path":str(old["run"]),
        "FS_C04_native_path":str(new["run"]),
        "parent_cross_run_proof_status":parent_proof["status"],
        "parent_mesh_points_faces_owner_neighbour_sha256":
            parent_proof["matching_parent_polymesh_file_sha256"],
        "checked_polymesh_sha256":source_hashes,
        "parent_cells":parent["count"],
        "fluid_region_cells":fluid["count"],
        "mold_region_cells":mold["count"],
        "original_metal_cells_mapped_in_fluid":len(seeded),
        "original_air_cells_mapped_in_fluid":len(gas),
        "all_sand_cells_mapped_in_mold":len(mold_to_parent),
        "unmatched_cells":0,
        "metal_split_cell_id_min":min(seeded),
        "metal_split_cell_id_max":max(seeded),
        "seeded_split_fluid_cell_id_list_sha256":hashlib.sha256(
            ",".join(str(x) for x in seeded).encode()
        ).hexdigest(),
        "metal_volume_from_split_fluid_polyhedron_m3":geometric_volume_m3,
        "metal_volume_from_split_fluid_polyhedron_mm3":
            geometric_volume_m3*1e9,
        "reference_analytic_pilot_metal_volume_mm3":
            plan["pilot_initial_metal_volume_mm3"],
        "relative_mesh_vs_analytic_volume_difference":err,
        "reference_CAD_metal_volume_mm3":
            plan["reference_CAD_metal_volume_mm3"],
        "alpha_metal_initialized_in_fluid":False,
        "native_openfoam_volume_integration_verified":False,
        "thermophysical_and_CHT_properties_validated":False,
        "CFD_or_CHT_executed":False,
        "notes":[
            "This is a read-only geometric bijection, not a saved OpenFOAM alpha field",
            "The initial metal phase is alpha.metal=1 in mapped FLUID cells only",
            "No cell of MOLD is assigned initial metal; it is a separate solid region",
            "Geometric volume is independently reconstructed, NOT OpenFOAM postProcessing output",
            "No CFD, mold conduction, latent heat, shrinkage or graphitization",
        ],
    }


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fs-c03",type=Path,required=True)
    p.add_argument("--fs-c04",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        print(json.dumps(analyze(args.fs_c03,args.fs_c04),
                         indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C04 SPLIT CELL AUDIT BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
