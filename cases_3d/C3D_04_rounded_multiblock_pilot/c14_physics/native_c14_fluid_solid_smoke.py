#!/usr/bin/env python3
"""Native F14 C14 fluid-solid + phase-change loading on isolated two 3D cubes.

This is a genuine two-step foamMultiRun in CI, never the real V4/T02 thesis
case. Uses exact original C14 fluid/solid/material/phase source, except native
3D patches, gauge reference cell and a full all-cell metal zone.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"t0_conduction"/"scripts"))
import native_f14_coupled_runtime_smoke as mesh_fixture
import stage_c14_3d_case_a as native_case
import c14_source_fidelity as physics


def do_smoke(root: Path) -> dict:
    root=root.expanduser().absolute()
    native_case.protect_source(root,root) if False else None
    if root.exists() or root.is_symlink():
        raise FileExistsError("Synthetic test directory already exists: "+str(root))
    tools=native_case.environment()
    physics.verify()
    reference=root/"isolated_native_mesh_only"
    candidate=root/"actual_C14_fluid_solid_2step"
    reference.mkdir(parents=True)
    # Original C14 controlled time & regions, no new physical parameters.
    (reference/"system").mkdir()
    (reference/"system/controlDict").write_bytes(
        (physics.C14/"system/controlDict").read_bytes()
    )
    logs=[]
    for region in ("metal","mold"):
        path=reference/"system"/region/"blockMeshDict"
        path.parent.mkdir(parents=True,exist_ok=True)
        # Eight or more control volumes are required for the fluid-pressure
        # equation; a one-cell cube has a zero pressure matrix diagonal.
        block=mesh_fixture.block_mesh_dict(region)
        marker="(1 1 1) simpleGrading"
        assert block.count(marker)==1, "synthetic mesh blockMeshDict drift"
        block=block.replace(marker,"(3 3 3) simpleGrading")
        path.write_text(block)
        logs.append(native_case.native(
            ["blockMesh","-case",str(reference),"-region",region,
             "-dict",str(path)],reference,"log.blockMesh."+region,120))
    n_metal=native_case.region_cells(reference,"metal",27)
    n_mold=native_case.region_cells(reference,"mold",27)
    record=native_case.stage(reference,candidate,smoke=True,
                             expected={"metal":27,"mold":27})
    try:
        record=native_case.run_smoke(candidate,record)
    except Exception:
        print("Synthetic C14 F14 CFD fails: logs at "+str(candidate))
        raise
    assert record["status"]=="C3D04_A_C14_FLUID_SOLID_TWO_STEP_NATIVE_SMOKE_PASS"
    record["real_V4_T02_mesh_used"]=False
    record["full_10s_C14_case_executed"]=False
    record["source_fixture"]="TWO_3D_27_CELL_SYNTHETIC_REGIONS_NOT_QUICKCUP"
    record["blockMesh_native_logs"]=logs
    record["synthetic_cell_counts"]={"metal":n_metal,"mold":n_mold}
    (candidate/native_case.REPORT).write_text(
        json.dumps(record,indent=2)+"\n",encoding="utf-8")
    return record


def main()->int:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    try:
        record=do_smoke(args.out)
        print(json.dumps({
            "status":record["status"],"real_V4_T02_mesh_used":False,
            "foamMultiRun":record["foamMultiRun_log"],
            "C14_physics_parameters_original":True,
            "C14_3D_thesis_validated":False
        },indent=2))
        return 0
    except (OSError,ValueError,RuntimeError) as e:
        print("C3D04_C14_NATIVE_SYNTHETIC_BLOCKED: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
