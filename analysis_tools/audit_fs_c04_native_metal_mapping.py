#!/usr/bin/env python3
"""FS-C04 native INITIAL METAL cell identity proof, READ ONLY, NO CFD.

Compare the existing successful FS-C03 (three zones) and FS-C04 (two zones)
native parent blockMesh output. Require identical points/faces/owner/neighbour
bytes and matching zone labels. Only then is the list of 2368 C03 metal
cell labels valid as a proposed FS-C04 PARENT MESH metal seed.

Does NOT establish FLUID REGION split cell ordering and intentionally
DOES NOT write a phase field. No CHT/VOF solver or alterations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from audit_fs_c03_exterior_mesh import SOURCE as C03_SOURCE, require
from audit_fs_c04_fluid_mold import SOURCE as C04_SOURCE
from audit_fs_c04_metal_seed import audit as phase_geometry

ORIGINAL_CELLS=42048
EXPECTED_COUNTS_3={"metal":2368,"mold":7680,"air":32000}
EXPECTED_COUNTS_2={"fluid":34368,"mold":7680}
POLYMESH_ITEMS=("points","faces","owner","neighbour")


def sha(path:Path)->str:
    require(path.is_file() and not path.is_symlink(),
            "missing/untrusted native mesh file: "+str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_status(run:Path,region_count:int)->dict:
    root=run.expanduser().resolve()
    require(root.is_dir() and not root.is_symlink(),"native run missing")
    prefix="FS_C03_AIR_TOPOLOGY_" if region_count==3 \
           else "FS_C04_FLUID_MOLD_TOPOLOGY_"
    require(root.name.startswith(prefix),"unexpected native run namespace")
    name="FS_C03_NATIVE_STATUS.json" if region_count==3 \
         else "FS_C04_NATIVE_STATUS.json"
    sf=root/name
    require(sf.is_file() and not sf.is_symlink(),"native status missing")
    record=json.loads(sf.read_text())
    expected="NATIVE_3_REGION_TOPOLOGY_PASSED_NO_CFD" if region_count==3 \
             else "NATIVE_2_REGION_FLUID_MOLD_TOPOLOGY_PASSED_NO_CFD"
    counts=EXPECTED_COUNTS_3 if region_count==3 else EXPECTED_COUNTS_2
    require(record.get("status")==expected and
            record.get("native_mesh_checks_passed") is True and
            record.get("solver_executed") is False and
            record.get("region_cells")==counts,
            "native run did not pass expected mesh-only region gates")
    source=C03_SOURCE if region_count==3 else C04_SOURCE
    require(sha(root/"system/blockMeshDict")==sha(source),
            "native source geometry changed or not from tracked FS-C03/FS-C04")
    return {"run":root,"status_sha256":sha(sf),
            "parent_mesh":root/"constant/polyMesh",
            "native_regions":counts}


def read_ascii_zones(file:Path,required_names:set[str])->dict[str,set[int]]:
    require(file.is_file() and not file.is_symlink(),
            "native parent cellZones file missing")
    raw=file.read_text(encoding="utf-8",errors="strict")
    header=raw.split("FoamFile",1)[-1].split(")",1)[0]
    require(re.search(r"\bformat\s+ascii\s*;",raw[:800]) is not None,
            "binary cellZones unsupported: requires explicit ASCII export")
    groups={}
    for name in required_names:
        # Cell zone output produced by blockMesh Foundation14, e.g.
        # metal { type cellZone; cellLabels List<label> 2368 ( ... ); }
        pattern=(r"(?m)^\s*"+re.escape(name)+r"\s*\{([^{}]*)\}")
        match=re.search(pattern,raw,re.S)
        require(match is not None,"native cellZone missing: "+name)
        body=match.group(1)
        label=re.search(
            r"\bcellLabels\s+(?:List<label>\s*)?(\d+)\s*"
            r"\(\s*([0-9\s+-]*)\s*\)\s*;",body,re.S
        )
        require(label is not None,"cellLabels not readable in zone "+name)
        declared=int(label.group(1))
        values=[int(x) for x in label.group(2).split()]
        require(declared==len(values),
                "declared zone size inconsistent: "+name)
        require(declared==(EXPECTED_COUNTS_3.get(name) if
                          required_names==set(EXPECTED_COUNTS_3)
                          else EXPECTED_COUNTS_2.get(name)),
                "wrong number of native cells in "+name)
        require(all(0<=i<ORIGINAL_CELLS for i in values),
                "native cell label outside expected 42048 mesh")
        require(len(set(values))==len(values),
                "duplicate cell label in zone "+name)
        groups[name]=set(values)
    for a in required_names:
        for b in required_names:
            if a<b:
                require(not groups[a].intersection(groups[b]),
                        "overlapping native material zones "+a+"/"+b)
    require(set().union(*groups.values())==set(range(ORIGINAL_CELLS)),
            "native parent mesh zones do not partition all cells")
    return groups


def analyze(c03:Path,c04:Path)->dict:
    old=native_status(c03,3)
    new=native_status(c04,2)
    require(old["run"] != new["run"],"cannot compare same native run")
    meshes={}
    for filename in POLYMESH_ITEMS:
        a=sha(old["parent_mesh"]/filename)
        b=sha(new["parent_mesh"]/filename)
        require(a==b,
                "parent mesh "+filename+" differs: native cell addressing not proven")
        meshes[filename]=a
    a=read_ascii_zones(old["parent_mesh"]/"cellZones",
                       set(EXPECTED_COUNTS_3))
    b=read_ascii_zones(new["parent_mesh"]/"cellZones",
                       set(EXPECTED_COUNTS_2))
    require(a["metal"] | a["air"] == b["fluid"],
            "fluid zone != original metal+air cell labels")
    require(a["mold"]==b["mold"],
            "mold zone label addresses differ")
    p=phase_geometry()
    require(p["original_metal_block_indices"]==[9,14,19] and
            len(a["metal"])==p["initial_metal_cell_count_predicted"],
            "analytic metal seed and native metal zone disagree")
    return {
        "schema":"masterproject-fs-c04-native-parent-metal-seed-mapping-v1",
        "status":"PARENT_MESH_METAL_CELL_LABELS_MATCH_NO_FIELD_WRITTEN",
        "source_native_FS_C03_run":str(old["run"]),
        "source_native_FS_C04_run":str(new["run"]),
        "C03_status_sha256":old["status_sha256"],
        "C04_status_sha256":new["status_sha256"],
        "matching_parent_polymesh_file_sha256":meshes,
        "metal_parent_cell_label_count":len(a["metal"]),
        "air_parent_cell_label_count":len(a["air"]),
        "mold_parent_cell_label_count":len(a["mold"]),
        "verified_metal_plus_air_equals_fluid":True,
        "verified_mold_labels_unchanged":True,
        "metal_parent_cell_label_min":min(a["metal"]),
        "metal_parent_cell_label_max":max(a["metal"]),
        "metal_parent_cell_label_list_sha256":hashlib.sha256(
            ",".join(str(x) for x in sorted(a["metal"])).encode()
        ).hexdigest(),
        "source_metal_zone_file_sha256":
            sha(old["parent_mesh"]/"cellZones"),
        "phase_volume_reference_analytic_mm3":
            p["pilot_initial_metal_volume_mm3"],
        "fluid_region_split_cell_addressing_verified":False,
        "native_metal_cell_volumes_summed":False,
        "initial_alpha_field_written":False,
        "CFD_or_CHT_executed":False,
        "notes":[
            "Label mapping is only for PARENT blockMesh cell IDs, not the separated fluid region",
            "Do not write alpha.metal into fluid using parent IDs without verified split mapping",
            "Both original FS-C03 and FS-C04 native cases are read-only",
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
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
        print("FS-C04 NATIVE METAL MAPPING BLOCKED: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
