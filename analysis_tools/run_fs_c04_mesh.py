#!/usr/bin/env python3
"""FS-C04 Foundation14 fluid(metal+air)/mold mesh runner; STAGE ONLY by default.

Copies the standalone blockMesh into a NEW folder outside MasterProject.
--native runs blockMesh, parent/region checkMesh and splitMeshRegions (NO CFD).
Geometric source is an exact 2-zone relabeling of passed FS-C03 geometry.
NO physics dictionaries or alpha.metal initial phase yet. NO CFD.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

from audit_fs_c04_fluid_mold import SOURCE, audit
from audit_fs_c03_exterior_mesh import require

ROOT=SOURCE.parents[1]
CONTROL=ROOT/"system/controlDict"
EXPECTED={"fluid":34368,"mold":7680}
CONTACTS={
    ("fluid","mold"):3136,
}
AIR_PATCHES={"atmosphereTop":448,"atmosphereSides":3040,
             "atmosphereLowerSides":256}
MOLD_UNRESOLVED={"moldBottom":128,"moldRecessWall":256,
                 "moldRecessRoof":64}


def patch_info(file: Path, name: str) -> dict[str,str]:
    require(file.is_file() and not file.is_symlink(),
            "native boundary file missing "+str(file))
    raw=file.read_text(encoding="utf-8",errors="replace")
    matches=list(re.finditer(r"(?m)^\s*"+re.escape(name)
                            +r"\s*\{([^{}]*)\}",raw,re.S))
    require(len(matches)==1,"native patch not uniquely present: "+name)
    return dict(re.findall(r"(\w+)\s+([^\s;]+)\s*;",matches[0].group(1)))


def stage(path: Path)->dict:
    path=path.expanduser().resolve()
    require(not path.exists(),"pre-existing pilot directory; never overwrite")
    report=audit(SOURCE.read_text())
    require(CONTROL.is_file(),"missing mesh-only controlDict")
    (path/"system").mkdir(parents=True,exist_ok=False)
    shutil.copyfile(SOURCE,path/"system/blockMeshDict")
    shutil.copyfile(CONTROL,path/"system/controlDict")
    record={
        "schema":"masterproject-fs-c04-2region-native-mesh-only-v1",
        "status":"STAGED_NO_OPENFOAM",
        "run":str(path),
        "cad_surface_fidelity_verified":False,
        "solver_executed":False,
        "two_geometric_regions_only_not_cht_or_vof":True,
        "alpha_metal_not_initialized":True,
        "topology":report,
    }
    (path/"FS_C04_NATIVE_STATUS.json").write_text(json.dumps(record,indent=2)+"\n")
    return record


def native_run(path:Path,record:dict)->dict:
    require(os.environ.get("WM_PROJECT_VERSION")=="14",
            "must activate OpenFOAM Foundation 14 before native mesh test")
    for cmd in ("blockMesh","checkMesh","splitMeshRegions"):
        require(shutil.which(cmd) is not None,
                "Foundation14 executable not on PATH: "+cmd)

    def run(label:str,cmd:list[str])->str:
        record["status"]="RUNNING_"+label
        (path/"FS_C04_NATIVE_STATUS.json").write_text(json.dumps(record,indent=2)+"\n")
        output=subprocess.run(cmd,capture_output=True,text=True,errors="replace",
                              check=False)
        text=output.stdout+"\n"+output.stderr
        (path/("log."+label)).write_text(text)
        require(output.returncode==0,
                "native "+label+" failed; inspect log."+label)
        return text

    def checkmesh(label:str,args:list[str])->str:
        log=run(label,["checkMesh","-case",str(path),*args,
                       "-allGeometry","-allTopology","-writeSets"])
        require(re.search(r"\bMesh OK\b",log) is not None
                and re.search(r"Failed\s+[1-9]\d*\s+mesh checks",log) is None,
                "native checkMesh FAILED for "+label)
        return log

    try:
        run("blockMesh",["blockMesh","-case",str(path)])
        zones=(path/"constant/polyMesh/cellZones").read_text()
        for region in EXPECTED:
            require(re.search(r"\b"+region+r"\b",zones) is not None,
                    "missing native cellZone "+region)
        checkmesh("checkMesh.parent",[])
        run("splitMeshRegions",["splitMeshRegions","-case",str(path),
                                "-cellZones","fluid mold","-noFields"])
        regions={}
        for region,expected in EXPECTED.items():
            log=checkmesh("checkMesh."+region,["-region",region])
            require(re.search(r"Number of regions:\s*1(?:\D|$)",log) is not None,
                    "disconnected cellZone "+region)
            counts=re.findall(r"(?m)^\s*cells:\s*(\d+)",log)
            require(counts and int(counts[0])==expected,
                    "native "+region+" cells mismatch")
            regions[region]=int(counts[0])

        contacts={}
        for (a,b),expected in CONTACTS.items():
            for region,other in ((a,b),(b,a)):
                bd=path/"constant"/region/"polyMesh/boundary"
                name=region+"_to_"+other
                meta=patch_info(bd,name)
                require(meta.get("type")=="mappedWall"
                        and meta.get("neighbourRegion")==other
                        and meta.get("neighbourPatch")==other+"_to_"+region
                        and int(meta.get("nFaces","-1"))==expected,
                        "native mappedWall contact failed: "+name)
            contacts[a+"-"+b]=expected

        fluid_bd=path/"constant/fluid/polyMesh/boundary"
        for absent in ("metal_to_air","air_to_metal","fluid_to_air",
                       "air_to_fluid"):
            try:
                patch_info(fluid_bd,absent)
            except ValueError as e:
                require("not uniquely present" in str(e),
                        "unrecognized internal-phase patch problem")
            else:
                require(False, "metal-air must be INTERNAL fluid faces: "+absent)
        for patch,count in AIR_PATCHES.items():
            p=patch_info(fluid_bd,patch)
            require(p.get("type")=="patch" and
                    int(p.get("nFaces","-1"))==count,
                    "atmospheric opening missing/changed: "+patch)
        for patch,count in MOLD_UNRESOLVED.items():
            p=patch_info(path/"constant/mold/polyMesh/boundary",patch)
            require(p.get("type")=="wall" and
                    int(p.get("nFaces","-1"))==count,
                    "mold base/recess boundary unexpected: "+patch)
        unk=path/"constant/polyMesh/boundary"
        try:
            u=patch_info(unk,"unexpectedFaces")
            require(int(u.get("nFaces","-1"))==0,
                    "unclassified external faces in native mesh")
        except ValueError as e:
            if "not uniquely present" not in str(e):
                raise
        record.update({
            "status":"NATIVE_2_REGION_FLUID_MOLD_TOPOLOGY_PASSED_NO_CFD",
            "region_cells":regions,
            "mappedWall_contact_face_counts":contacts,
            "air_exterior_faces":AIR_PATCHES,
            "native_mesh_checks_passed":True,
        })
    except (OSError,ValueError) as e:
        record.update({"status":"REJECTED_NATIVE_MESH","reason":str(e),
                       "native_mesh_checks_passed":False})
        (path/"FS_C04_NATIVE_STATUS.json").write_text(json.dumps(record,indent=2)+"\n")
        raise
    (path/"FS_C04_NATIVE_STATUS.json").write_text(json.dumps(record,indent=2)+"\n")
    return record


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native",action="store_true",
                   help="RUN actual blockMesh/checkMesh/split; never CFD")
    p.add_argument("--out",type=Path)
    a=p.parse_args(argv)
    dirname="FS_C04_FLUID_MOLD_TOPOLOGY_"+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    out=(a.out or Path.home()/"OpenFOAM"/dirname).expanduser().resolve()
    try:
        if a.native:
            require(os.environ.get("WM_PROJECT_VERSION")=="14",
                    "source Foundation14 environment before native mesh")
        record=stage(out)
        print("FS-C04 2-zone mesh-only pilot staged: "+str(out),flush=True)
        if a.native:
            record=native_run(out,record)
        else:
            print("STATIC TOPOLOGY PASSED. NATIVE MESH NOT RUN. NO CFD.")
        print("FS-C04 status: "+record["status"])
        print("NO CFD. Alpha metal initial field, real CAD fit and mold support unresolved.")
        return 0
    except (OSError,ValueError) as e:
        print("FS-C04 BLOCKED: "+str(e),file=sys.stderr)
        if out.exists():
            print("Preserved work at "+str(out),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
