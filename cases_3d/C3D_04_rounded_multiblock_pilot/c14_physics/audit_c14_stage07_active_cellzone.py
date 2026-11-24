#!/usr/bin/env python3
"""Read-only mesh-instance forensic audit for actual C3D04-A Stage07 _03.

Real _03: core/energy/flow/momentum each emitted 100 F14 FATAL IO events
"Cannot find cellZone metal", even though an isolated copy-zone repair
was added. We cannot infer from a C14 zone text file alone that F14
actually loaded the zone at 0.1...10s.

This audit NEVER runs OpenFOAM, writes a report on disk, edits Git, creates
cellZones, makes a case copy, or modifies previous CFD/postprocessing.
Output: compact JSON to stdout with zone provenance, region instances,
time-local mesh overrides, existing energy rows and four 10s profiles.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import run_c14_stage07_solver_backed_recovery as recovery
import stage_c14_3d_case_a as stage


def ensure(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("C3D04_A_NATIVE_ZONE_READONLY_BLOCKED: " + why)


def hash_file(file: Path) -> str | None:
    if not file.is_file() or file.is_symlink():
        return None
    digest=hashlib.sha256()
    with file.open("rb") as stream:
        for buf in iter(lambda:stream.read(1<<18),b""):
            digest.update(buf)
    return digest.hexdigest()


def physical_mesh_inventory(path: Path, *, n: int, root: Path) -> dict:
    """Audit the exact file instances without interpreting guessed topology."""
    ret={
        "relative":str(path.relative_to(root)),
        "exists":path.is_dir() and not path.is_symlink(),
        "files":{},
        "cellzone_found":False,
        "full_metal_cellzone_verified":False,
    }
    if not ret["exists"]:
        return ret
    for name in (*stage.MESH,"cellZones","faceZones","pointZones"):
        file=path/name
        ret["files"][name]={
            "exists":file.is_file(),
            "symlink":file.is_symlink(),
            "sha256":hash_file(file)
        }
    cellzone=path/"cellZones"
    ret["cellzone_found"]=cellzone.is_file() and not cellzone.is_symlink()
    if ret["cellzone_found"]:
        try:
            ret["full_metal_cellzone_verified"]=stage.audit_existing_zone(cellzone,n)
        except (ValueError,UnicodeError,OSError) as exc:
            ret["cellzone_parse_error"]=str(exc)[:400]
    return ret


def time_is_numeric(name: str) -> bool:
    try:
        number=float(name)
        return math.isfinite(number) and number>=0
    except ValueError:
        return False


def saved_instances(copy: Path, n: int) -> dict:
    """Detect *possible* alternate zone instances; do NOT assert selected mesh."""
    entries=[]
    time_dirs=[]
    for child in copy.iterdir():
        if child.is_dir() and not child.is_symlink() and time_is_numeric(child.name):
            time_dirs.append(child)
    for child in sorted(time_dirs,key=lambda p:float(p.name)):
        for name in ("metal/polyMesh", "polyMesh"):
            mesh=child/name
            if mesh.is_dir() or mesh.is_symlink():
                entries.append({
                    "time_name":child.name,
                    **physical_mesh_inventory(mesh,n=n,root=copy),
                })
    # Time-local zone instances can take precedence over constant depending on
    # the active foam mesh instance. Presence alone is NOT proof of precedence.
    suspicious=[x for x in entries if x["relative"].endswith("metal/polyMesh")
                and not x["full_metal_cellzone_verified"]]
    return {
        "saved_time_directories":len(time_dirs),
        "time_local_mesh_directories_found":len(entries),
        "time_local_mesh_instances":entries[:35],
        "time_local_mesh_instances_truncated":len(entries)>35,
        "time_local_metal_mesh_missing_full_zone":len(suspicious),
        "time_local_metal_mesh_missing_full_zone_first_10":[
            x["relative"] for x in suspicious[:10]],
    }


def inspect(case: Path, copy: Path) -> dict:
    ensure(not copy.is_symlink() and copy.is_dir(),
           "native _03 copy absent or symlink")
    ensure(not case.is_symlink() and case.is_dir(),
           "original C14 10s CFD absent or symlink")
    case=case.resolve()
    copy=copy.resolve()
    ensure(case!=copy and case not in copy.parents and copy not in case.parents,
           "copy/source paths overlap")
    source_log=hash_file(case/"log.foamMultiRun")
    copy_log=hash_file(copy/"log.foamMultiRun")
    ensure(source_log is not None and source_log==copy_log,
           "authentic CFD source and native copy solver logs not identical")
    obj=copy/recovery.REPORT
    ensure(obj.is_file() and not obj.is_symlink(),
           "native six-group final report missing; do not misread partial output")
    report=json.loads(obj.read_text(encoding="utf-8"))
    ensure(report.get("schema")=="C3D04_A_C14_F14_SOLVER_BACKED_OFFLINE_RECOVERY_V1"
           and report.get("source_authentication",{}).get("case")==str(case)
           and report.get("isolated_new_workcopy")==str(copy),
           "native report belongs to another source/run")
    n=stage.EXPECTED["metal"]
    ensure(n==8960, "expected exact native C14 metal cell count changed")
    source_mesh=physical_mesh_inventory(
        case/"constant/metal/polyMesh",n=n,root=case)
    new_mesh=physical_mesh_inventory(
        copy/"constant/metal/polyMesh",n=n,root=copy)
    # No mesh writes. Only identity of known finite original mesh components.
    mesh_sha_equal={
        name:source_mesh["files"].get(name,{}).get("sha256")==
             new_mesh["files"].get(name,{}).get("sha256") and
             source_mesh["files"].get(name,{}).get("sha256") is not None
        for name in stage.MESH
    }
    ensure(all(mesh_sha_equal.values()),
           "mesh geometry/connectivity SHA differs between CFD and _03")
    old_zone=source_mesh["files"].get("cellZones",{}).get("sha256")
    new_zone=new_mesh["files"].get("cellZones",{}).get("sha256")
    groups={}
    prior=report.get("native_groups")
    ensure(isinstance(prior,list) and len(prior)==6,
           "native group report not complete")
    for entry in prior:
        g=entry.get("group")
        ensure(g in recovery.TASK_ORDER and g not in groups,
               "native group duplicate/missing identity")
        log=copy/("log.C14_3D_postprocess_solverBacked_"+g)
        ensure(hash_file(log)==entry.get("log_sha256"),
               "prior native group log changed: "+g)
        f=recovery.fatal_openfoam_log(log)
        groups[g]={
            "recorded_os_exit_code":entry.get("exit_code"),
            "semantic_pass":entry.get("exit_code")==0 and not f["foam_fatal_present"],
            "foam_fatal_occurrences":f["foam_fatal_occurrence_count"],
            "has_foam_fatal":f["foam_fatal_present"],
        }
    ensure(set(groups)==set(recovery.TASK_ORDER),
           "some native groups missing")
    instances=saved_instances(copy,n)
    try:
        energy=recovery.native_surface_table_coverage(copy)
    except (OSError,ValueError) as exc:
        energy={"error":str(exc)[:400]}
    try:
        profile=recovery.primitive_profile_coverage(copy)
    except (OSError,ValueError,KeyError) as exc:
        profile={"error":str(exc)[:400]}
    if not new_mesh["cellzone_found"]:
        classification="MISSING_CELLZONE_FILE_IN_PRESERVED_COPY"
    elif not new_mesh["full_metal_cellzone_verified"]:
        classification="CELLZONE_CONTENT_INVALID_OR_UNREADABLE_IN_COPY"
    elif instances["time_local_metal_mesh_missing_full_zone"]>0:
        classification="TIME_LOCAL_MESH_ZONE_OVERRIDE_POSSIBLE_NOT_PROVEN"
    elif any(not groups[g]["semantic_pass"] for g in
             ("core","energy","flow","momentum")):
        classification="CONSTANT_METAL_ZONE_VALID_BUT_F14_REGISTRY_EMPTY_ROOT_CAUSE_UNRESOLVED"
    else:
        classification="NATIVE_ZONE_NO_FATAL_OBSERVED"
    return {
        "schema":"C3D04_A_STAGE07_ACTIVE_MESH_ZONE_READONLY_WSL_V1",
        "case":"C3D04-A", "stage":"7/10","milestones_done":"6/10",
        "mode":"READ_ONLY_NO_FOAM_COMMANDS_NO_GIT_NO_WRITES",
        "source_CFD_solver_log_SHA256":source_log,
        "native_copy_report_SHA256":hash_file(obj),
        "zone_repair_recorded_in_original_report":
            report.get("metal_cellZone_copy_only_recovery"),
        "case_original_constant_metal_mesh":source_mesh,
        "copy_constant_metal_mesh":new_mesh,
        "native_mesh_connectivity_SHA_equal":mesh_sha_equal,
        "original_zone_SHA":old_zone,
        "copied_zone_SHA":new_zone,
        "saved_mesh_instance_evidence":instances,
        "native_group_semantic_status":groups,
        "metal_native_surface_power_coverage":energy,
        "final_primitive_80_point_profile_coverage":profile,
        "triage_classification":classification,
        "native_zone_repair_verified_in_actual_F14_runtime":False,
        "can_conclude_selected_F14_mesh_instance_from_files_only":False,
        "energy_conservation_verified":False,
        "new_CFD_run":False,
        "previous_copy_modified":False,
        "recommendation":"Use zone file and mesh instance evidence to select a minimal NEW "
          "copy-only F14 latestTime runtime probe before any 101-state retry. "
          "Do not delete _03 or create _04 until this root cause is established.",
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",type=Path,
        default=Path.home()/"OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    parser.add_argument("--copy",type=Path,
        default=Path.home()/"OpenFOAM/C3D04_A_C14_SOLVER_BACKED_POSTPROCESS_03")
    args=parser.parse_args()
    try:
        print(json.dumps(inspect(args.case,args.copy),indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("C3D04_A_ACTIVE_MESH_ZONE_AUDIT_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
