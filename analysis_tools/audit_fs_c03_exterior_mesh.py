#!/usr/bin/env python3
"""FS-C03: STATIC 3D metal/mold/air blockMesh topology verification (NO CFD).

The source is a coarse C3D-03 derived topology proof, NOT CAD-conformal.
Checks each face exactly once/twice, all exposed faces named, one air region
connected over the iron/sand top and four mold sidewalls, and actual material
contact faces. No mesh, no OpenFOAM, no mutation or physical heat validation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import json
import math
from pathlib import Path
import re
import sys

NUMBER=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
SOURCE=Path(__file__).resolve().parents[1]/"freesurface/FS-C03_exterior_air_pilot/system/blockMeshDict"
EXPECTED_REGIONS={"metal":2368,"mold":7680,"air":32000}
EXPECTED_INTERFACES={"air_metal":1,"air_mold":24,"metal_mold":13}
EXPECTED_PATCHES={
    "moldBottom":4,"moldRecessWall":4,"moldRecessRoof":1,
    "atmosphereSides":24,"atmosphereTop":9,"atmosphereLowerSides":4,
}


def section(text: str, name: str) -> str:
    match=re.search(r"(?m)^\s*"+re.escape(name)+r"\s*\(",text)
    require(match is not None,"missing section "+name)
    pos=match.end()
    depth=1
    for j in range(pos,len(text)):
        if text[j]=="(":depth+=1
        elif text[j]==")":
            depth-=1
            if depth==0:
                return text[pos:j]
    raise ValueError("FS-C03: unmatched parentheses in "+name)


def require(condition: bool, message: str)->None:
    if not condition:
        raise ValueError("FS-C03 STATIC GATE: "+message)


def face_key(face):
    return tuple(sorted(face))


def orientation_jacobian(v, coordinates):
    p0, p1, p3, p4=(coordinates[v[k]] for k in (0,1,3,4))
    ax,ay,az=(a-b for a,b in zip(p1,p0))
    bx,by,bz=(a-b for a,b in zip(p3,p0))
    cx,cy,cz=(a-b for a,b in zip(p4,p0))
    return ((ay*bz-az*by)*cx
            +(az*bx-ax*bz)*cy
            +(ax*by-ay*bx)*cz)


def subdivisions_for_faces(n):
    nx,ny,nz=n
    return ((nx,ny),(nx,ny),(nx,nz),
            (ny,nz),(nx,nz),(ny,nz))


def faces_of(v):
    return (
        (v[0],v[3],v[2],v[1]),
        (v[4],v[5],v[6],v[7]),
        (v[0],v[1],v[5],v[4]),
        (v[1],v[2],v[6],v[5]),
        (v[2],v[3],v[7],v[6]),
        (v[3],v[0],v[4],v[7]),
    )


def parse(text: str):
    vs=section(text,"vertices")
    coordinates=[tuple(float(x) for x in match)
                 for match in re.findall(
                    r"\(\s*("+NUMBER+r")\s+("+NUMBER+r")\s+("+NUMBER+r")\s*\)",vs)]
    require(len(coordinates)==84,"expected 84 CAD-approximate plus outer-air vertices")
    bs=section(text,"blocks")
    pattern=r"hex\s*\(\s*([0-9 ]+)\s*\)\s+(metal|mold|air)\s*\(\s*([0-9 ]+)\s*\)\s+simpleGrading\s*\(\s*1\s+1\s+1\s*\)"
    blocks=[]
    for m in re.finditer(pattern,bs):
        v=tuple(map(int,m.group(1).split()))
        nc=tuple(map(int,m.group(3).split()))
        require(len(v)==8 and len(set(v))==8
                and all(0<=i<len(coordinates) for i in v)
                and len(nc)==3 and all(n>0 for n in nc),
                "invalid hexahedron vertices/divisions")
        blocks.append((v,m.group(2),nc))
    require(len(blocks)==53,"expected 24 original material + 29 surrounding air blocks")
    psec=section(text,"boundary")
    patches={}
    for m in re.finditer(
        r"(?m)^\s*(\w+)\s*\{\s*type\s+(wall|patch)\s*;\s*faces\s*\((.*?)\)\s*;\s*\}",
        psec,re.S,
    ):
        name,typ,inside=m.group(1),m.group(2),m.group(3)
        faces=[tuple(map(int,z.split()))
               for z in re.findall(r"\(\s*([\d ]+?)\s*\)",inside)]
        require(all(len(v)==4 and len(set(v))==4 for v in faces),
                "invalid boundary quadrilateral")
        require(name not in patches,"duplicate patch name")
        patches[name]=(typ,faces)
    require(set(patches)==set(EXPECTED_PATCHES),
            "unknown/missing external patches")
    require(sum(len(v[1]) for v in patches.values())==46,
            "expected 46 named exposed faces")
    require(re.search(r"\bname\s+unexpectedFaces\s*;",text) is not None and
            re.search(r"\btype\s+wall\s*;",text) is not None,
            "unexpectedFaces reject patch missing")
    return coordinates,blocks,patches


def audit(text: str) -> dict:
    vertices,blocks,patches=parse(text)
    nbyregion=defaultdict(int)
    faces=defaultdict(list)
    for idx,(v,region,nc) in enumerate(blocks):
        jac=orientation_jacobian(v,vertices)
        require(math.isfinite(jac) and jac>0,
                "block "+str(idx)+" has non-positive reference-corner Jacobian")
        nbyregion[region]+=math.prod(nc)
        for side,face_div in zip(faces_of(v),subdivisions_for_faces(nc)):
            faces[face_key(side)].append((idx,region,side,face_div))
    require(dict(nbyregion)==EXPECTED_REGIONS,
            "material cell counts changed: "+str(dict(nbyregion)))
    require(all(len(owners) in (1,2) for owners in faces.values()),
            "face has more than two neighboring blocks")
    for owners in faces.values():
        if len(owners)==2:
            require(sorted(owners[0][3])==sorted(owners[1][3]),
                    "non-conformal subdivisions on shared block face")
    uncovered={key for key,owners in faces.items() if len(owners)==1}
    named={}
    for name,(typ,fs) in patches.items():
        require(len(fs)==EXPECTED_PATCHES[name],
                name+" boundary face-count changed")
        require(typ==("patch" if name.startswith("atmosphere") else "wall"),
                name+" has incorrect patch type")
        for v in fs:
            key=face_key(v)
            require(key not in named,"duplicate boundary face")
            require(key in uncovered,"boundary patch is not external")
            named[key]=name
    require(set(named)==uncovered,
            "unclassified external faces: "+str(len(uncovered-set(named))))
    interfaces=defaultdict(int)
    graph=defaultdict(set)
    airblocks={i for i,(_,mat,_) in enumerate(blocks) if mat=="air"}
    for owners in faces.values():
        if len(owners)!=2:
            continue
        (i,a,_,_),(j,b,_,_)=owners
        if a==b=="air":
            graph[i].add(j);graph[j].add(i)
        if a!=b:
            k="_".join(sorted((a,b)))
            interfaces[k]+=1
    require(dict(interfaces)==EXPECTED_INTERFACES,
            "metal/sand/air shared interfaces mismatch: "+str(dict(interfaces)))
    reached=set()
    start=next(iter(airblocks))
    q=deque([start])
    while q:
        u=q.popleft()
        if u in reached:
            continue
        reached.add(u)
        q.extend(graph[u]-reached)
    require(reached==airblocks,
            "air sidewalls not connected to air above entire mold")
    def y_at(ids):
        return [vertices[i][1] for i in ids]
    require(all(all(math.isclose(y,80,abs_tol=1e-8) for y in y_at(v))
                for v in patches["atmosphereTop"][1]),
            "atmosphere top not at y=+80mm or artificial roof")
    require(all(all(math.isclose(y,-65.5,abs_tol=1e-8) for y in y_at(v))
                for v in patches["atmosphereLowerSides"][1]),
            "air lower side boundary misplaced")
    require(all(all((math.isclose(vertices[i][0],-30,abs_tol=1e-8)
                     or math.isclose(vertices[i][0],81.8,abs_tol=1e-8)
                     or math.isclose(vertices[i][2],-30,abs_tol=1e-8)
                     or math.isclose(vertices[i][2],81.8,abs_tol=1e-8))
                    for i in v)
                for v in patches["atmosphereSides"][1]),
            "far side boundary incorrectly placed against mold")
    # Same CAD-approximate lower 24 hexa blocks; all air added externally.
    # Sand top is 4 mold/air faces, metal top is 1 metal/air face.
    at_top_contacts=defaultdict(int)
    side_mold_contacts=0
    for owners in faces.values():
        if len(owners)!=2:
            continue
        r={owners[0][1],owners[1][1]}
        if r=={"mold","air"}:
            ys=[vertices[i][1] for i in owners[0][2]]
            if all(math.isclose(y,0.,abs_tol=1e-8) for y in ys):
                at_top_contacts["mold"]+=1
            else:
                side_mold_contacts+=1
        if r=={"metal","air"}:
            ys=[vertices[i][1] for i in owners[0][2]]
            require(all(math.isclose(y,0.,abs_tol=1e-8) for y in ys),
                    "unexpected metal/air contact away from opening")
            at_top_contacts["metal"]+=1
    require(at_top_contacts=={"mold":4,"metal":1} and
            side_mold_contacts==20,
            "air must cover metal & sand TOP and ALL 20 exposed sidewall slabs")
    upper=[i for i in airblocks if any(vertices[k][1]>0 for k in blocks[i][0])]
    lateral=[i for i in airblocks if all(vertices[k][1]<=0 for k in blocks[i][0])]
    require(len(upper)==9 and len(lateral)==20,"wrong upper and lateral air blocks")
    return {
        "schema":"masterproject-fs-c03-3region-static-topology-v1",
        "status":"STATIC_TOPOLOGY_CONSISTENT_NOT_NATIVE_CHECKMESH",
        "vertices":len(vertices),
        "blocks":len(blocks),
        "material_cells_predicted":dict(nbyregion),
        "cell_count_predicted":sum(nbyregion.values()),
        "shared_block_faces_by_interface":dict(interfaces),
        "external_patch_block_faces":{k:len(v[1]) for k,v in patches.items()},
        "air_connected_block_count":len(reached),
        "air_block_count":len(airblocks),
        "air_above_top_block_count":len(upper),
        "air_around_four_sidewalls_block_count":len(lateral),
        "mold_top_air_contact_block_faces":at_top_contacts["mold"],
        "metal_top_air_contact_block_faces":at_top_contacts["metal"],
        "mold_side_air_contact_block_faces":side_mold_contacts,
        "outer_air_boundary":{
            "top_y_mm":80,
            "lateral_xz_min_mm":-30,
            "lateral_xz_max_mm":81.8,
            "bottom_y_mm":-65.5
        },
        "source_C3D03_lower_material_topology_preserved":True,
        "solid_mold_base_and_recess_exposure_resolved":False,
        "physical_CAD_surface_fidelity_verified":False,
        "reference_corner_jacobians_all_positive":True,
        "shared_face_subdivisions_all_match":True,
        "native_OpenFOAM_mesh_quality_verified":False,
        "energy_or_thermal_physics_verified":False,
        "solver_executed":False,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mesh",type=Path,default=SOURCE)
    args=p.parse_args(argv)
    try:
        path=args.mesh.expanduser().resolve()
        require(path.is_file() and not path.is_symlink(),"mesh file missing")
        print(json.dumps(audit(path.read_text()),indent=2))
        return 0
    except (OSError,ValueError) as e:
        print("FS-C03 STATIC MESH BLOCKED: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
