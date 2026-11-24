#!/usr/bin/env python3
"""Native Foundation14 *synthetic only* cellZone failure/recovery regression.

Start from 2-step completed 27+27-cell disposable C14 native case. Make a
separate synthetic research source WITHOUT full metal zone (the user WSL _02
failure), execute real -solver fluid postProcess and observe fatal cellZone.
Then add C14 all-metal zone only to a NEW clone and ensure Foundation14
rho*h fieldValue completes on its existing saved 0.002s snapshot.
The 10-second V4/T02 thesis CFD is never used or rerun.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import run_c14_stage07_solver_backed_recovery as recovery


def run_native(case: Path, logfile: str) -> dict:
    cmd=["foamPostProcess","-region","metal","-solver","fluid",
         "-dict","system/stage07ZoneSmoke","-latestTime"]
    r=subprocess.run(cmd,cwd=case,capture_output=True,text=True,
                     check=False,timeout=180)
    p=case/logfile
    p.write_text("COMMAND: "+" ".join(cmd)+"\nRC: "+str(r.returncode)
                 +"\nSTDOUT:\n"+r.stdout+"\nSTDERR:\n"+r.stderr,
                 encoding="utf-8")
    content=r.stdout+r.stderr
    return {"exit_code":r.returncode,
            "log":str(p),
            "foam_fatal_marker_found":
                recovery.fatal_openfoam_log(p)["foam_fatal_present"],
            "missing_metal_cellZone":
                "Cannot find cellZone metal" in content,
            "tail":content[-1500:]}


def execute(saved: Path, root: Path) -> dict:
    saved=saved.expanduser().resolve()
    root=root.expanduser().absolute()
    if not (saved/"0.002/metal/T").is_file():
        raise ValueError("synthetic two-step saved T field absent")
    if root.exists() or root.is_symlink():
        raise FileExistsError("never overwrite synthetic evidence " + str(root))
    zone=saved/"constant/metal/polyMesh/cellZones"
    if not zone.is_file():
        raise ValueError("native synthetic C14 original full metal zone absent")
    original_hash=hashlib.sha256(zone.read_bytes()).hexdigest()
    root.mkdir(parents=True)
    source=root/"synthetic_saved_case_without_metal_zone"
    newcopy=root/"brand_new_metadata_repaired_copy"
    shutil.copytree(saved,source)
    (source/"constant/metal/polyMesh/cellZones").unlink()
    shutil.copytree(source,newcopy)
    generated=newcopy/"system/stage07ZoneSmoke"
    c14=recovery.C14/"system/researchDiagnostics"
    sourceblock=recovery.selected_source_block(
        c14.read_text(encoding="utf-8"),"metalSensibleEnthalpy")
    generated.write_text(
        "FoamFile\n{\n    format ascii;\n    class dictionary;\n"
        '    location "system";\n    object stage07ZoneSmoke;\n}\n\n'
        +sourceblock,encoding="utf-8")
    negative=run_native(newcopy,"log.native.missingZone.before")
    if not negative["missing_metal_cellZone"]:
        raise RuntimeError("native negative case did not reproduce WSL missing-zone error: "
                           +str(negative))
    clone_previously_missing = not (
        newcopy/"constant/metal/polyMesh/cellZones").exists()
    old_expected=recovery.stage.EXPECTED["metal"]
    try:
        recovery.stage.EXPECTED["metal"]=27
        metadata=recovery.verify_or_add_metal_zone_in_new_copy(source,newcopy)
    finally:
        recovery.stage.EXPECTED["metal"]=old_expected
    if not clone_previously_missing or not metadata["added_to_copy_only"]:
        raise RuntimeError("zone metadata was not confined to new synthetic copy")
    if (source/"constant/metal/polyMesh/cellZones").exists():
        raise RuntimeError("synthetic source no-zone unexpectedly mutated")
    postprocessing=newcopy/"postProcessing"
    if postprocessing.is_dir():
        shutil.rmtree(postprocessing)  # disposable synthetic COPY only
    positive=run_native(newcopy,"log.native.repairedZone.after")
    if positive["foam_fatal_marker_found"] or positive["exit_code"]!=0:
        raise RuntimeError("F14 solver-backed native still failed after zone repair "
                           +str(positive))
    table_root=newcopy/"postProcessing/metal/metalSensibleEnthalpy"
    if not table_root.is_dir() or not list(table_root.rglob("volFieldValue.dat")):
        raise RuntimeError("no native original rho*h enthalpy postProcessing output")
    if hashlib.sha256(zone.read_bytes()).hexdigest()!=original_hash:
        raise RuntimeError("original synthetic CFD zone changed")
    return {"status":"REAL_F14_C14_SYNTHETIC_CELLZONE_ABSENT_FATAL_THEN_NEW_COPY_PASS",
            "fixture":"27-metal + 27-mold cells, 0.002s, NOT real V4/T02",
            "negative_native_without_zone":negative,
            "new_copy_metal_zone":metadata,
            "positive_solver_backed_native":positive,
            "original_synthetic_CFD_zone_unchanged":True,
            "real_thesis_10s_CFD_rerun":False,
            "original_V4_T02_tested":False}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--case",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    try:
        record=execute(args.case,args.out)
        print(json.dumps(record,indent=2))
        return 0
    except (OSError,ValueError,RuntimeError) as exc:
        print("C14_F14_CELLZONE_NATIVE_SMOKE_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
