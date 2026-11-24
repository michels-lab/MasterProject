#!/usr/bin/env python3
"""FS-C04 static pilot: ONE connected fluid=metal+air + mold-solid zone.

Compare every vertex, hexahedron and boundary against frozen FS-C03
three-zone source. ONLY the metal/air block-zone labels may merge into
'fluid'. Validate shared-face topology and fluid connectivity without
running OpenFOAM, assigning alpha.metal, or claiming CHT/VOF readiness.
"""
from __future__ import annotations
from collections import defaultdict, deque
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from audit_fs_c03_exterior_mesh import (
    SOURCE as THREE_ZONE, audit as reference_audit,
    faces_of, face_key, parse as parse_reference, section, require,
)

SOURCE=(Path(__file__).resolve().parents[1] /
        "freesurface/FS-C04_fluid_mold_mesh_pilot/system/blockMeshDict")
EXPECTED_CELLS={"fluid":34368,"mold":7680}
EXPECTED_BLOCKS={"fluid":32,"mold":21}
EXPECTED_INTERFACES=37
METAL_AIR_FACE_COUNT=1


def read_new_blocks(text: str) -> list[tuple]:
    part=section(text,"blocks")
    regex=(r"hex\s*\(\s*([0-9 ]+)\s*\)\s+"
           r"(fluid|mold)\s*\(\s*([0-9 ]+)\s*\)"
           r"\s+simpleGrading\s*\(\s*1\s+1\s+1\s*\)")
    blocks=[]
    for m in re.finditer(regex,part):
        v=tuple(int(x) for x in m.group(1).split())
        nc=tuple(int(x) for x in m.group(3).split())
        require(len(v)==8 and len(nc)==3 and all(n>0 for n in nc),
                "bad FS-C04 hexa block")
        blocks.append((v,m.group(2),nc))
    require(len(blocks)==53,"expected all 53 original hexa blocks")
    return blocks


def audit(source: str)->dict:
    baseline=THREE_ZONE.read_text()
    reference=reference_audit(baseline)
    ref_vertices,ref_blocks,_=parse_reference(baseline)
    # Guarantee there was no geometric change, including boundary patches,
    # level vertices, block resolution or grading.
    for part in ("vertices","edges","boundary"):
        require(section(source,part).strip()==section(baseline,part).strip(),
                "changed "+part+"; this must be a ZONE-ONLY experiment")
    blocks=read_new_blocks(source)
    require(len(blocks)==len(ref_blocks),"different number of blocks")
    for i,(new,ref) in enumerate(zip(blocks,ref_blocks)):
        vertices,zone,divisions=new
        old_vertices,old_zone,old_divisions=ref
        expected="mold" if old_zone=="mold" else "fluid"
        require((vertices,zone,divisions)==
                (old_vertices,expected,old_divisions),
                "block "+str(i)+" changed geometry/divisions or material grouping")
    zones=defaultdict(list)
    sizes=defaultdict(int)
    allfaces=defaultdict(list)
    for i,(v,zone,counts) in enumerate(blocks):
        zones[zone].append(i)
        sizes[zone]+=counts[0]*counts[1]*counts[2]
        for face in faces_of(v):
            allfaces[face_key(face)].append((i,zone))
    require(dict(sizes)==EXPECTED_CELLS,
            "wrong fluid/mold cell counts")
    require({k:len(v) for k,v in zones.items()}==EXPECTED_BLOCKS,
            "wrong zone block counts")
    interface=0
    graphs={region:defaultdict(set) for region in EXPECTED_BLOCKS}
    for owners in allfaces.values():
        require(len(owners) in (1,2),
                "overlapping face with more than two owners")
        if len(owners)!=2:
            continue
        (i,a),(j,b)=owners
        if a!=b:
            interface+=1
        else:
            graphs[a][i].add(j)
            graphs[a][j].add(i)
    require(interface==EXPECTED_INTERFACES,
            "incorrect fluid-solid mold interface block faces")
    for region,indices in zones.items():
        reached=set()
        q=deque([indices[0]])
        while q:
            i=q.popleft()
            if i in reached:
                continue
            reached.add(i)
            q.extend(graphs[region][i]-reached)
        require(reached==set(indices),
                "disconnected "+region+" zone; cannot use for VOF/CHT")
    metal_blocks=[i for i,b in enumerate(ref_blocks) if b[1]=="metal"]
    air_blocks=[i for i,b in enumerate(ref_blocks) if b[1]=="air"]
    require(len(metal_blocks)==3 and len(air_blocks)==29,
            "original material provenance changed")
    require(reference["shared_block_faces_by_interface"]["air_metal"]==
            METAL_AIR_FACE_COUNT,
            "original metal-air contact not a single top face")
    return {
        "schema":"masterproject-fs-c04-fluid-mold-static-v1",
        "status":"STATIC_2_ZONE_TOPOLOGY_CONSISTENT_NOT_NATIVE_CHECKMESH",
        "fluid_cell_count_predicted":sizes["fluid"],
        "mold_cell_count_predicted":sizes["mold"],
        "total_cell_count_predicted":sum(sizes.values()),
        "fluid_connected_blocks":len(zones["fluid"]),
        "mold_connected_blocks":len(zones["mold"]),
        "fluid_mold_shared_block_faces":interface,
        "original_top_metal_air_block_face_now_internal_to_fluid":True,
        "original_metal_block_indices":metal_blocks,
        "original_air_block_count":len(air_blocks),
        "exterior_top_and_four_sand_sidewalls":True,
        "atmosphere_external_patches_unchanged":True,
        "original_three_zone_source_sha256":
            hashlib.sha256(baseline.encode()).hexdigest(),
        "new_zone_only_source_sha256":
            hashlib.sha256(source.encode()).hexdigest(),
        "alpha_metal_initial_field_defined":False,
        "native_openfoam_2_region_checkmesh_verified":False,
        "fluid_mold_cht_coupling_verified":False,
        "physical_CAD_surface_fidelity_verified":False,
        "CFD_solver_executed":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mesh",type=Path,default=SOURCE)
    args=p.parse_args(argv)
    try:
        path=args.mesh.expanduser().resolve()
        require(path.is_file() and not path.is_symlink(),
                "source blockMeshDict missing")
        print(json.dumps(audit(path.read_text()),indent=2))
        return 0
    except (OSError,ValueError) as e:
        print("FS-C04 STATIC REJECTED: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
