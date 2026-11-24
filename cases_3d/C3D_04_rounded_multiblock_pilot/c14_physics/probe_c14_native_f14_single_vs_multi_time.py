#!/usr/bin/env python3
"""Foundation14 ORIGINAL C14 rho*h: independent times vs multi-time loop.

Real WSL V4/T02 has authentic 8960-cell metal zone in both source and _03,
but a multi-time foamPostProcess fluid group writes t0, then 100 FATAL IO:
'Cannot find cellZone metal. Available cellZones: 0()'.
The Foundation14 foamPostProcess.C multi-time loop repeatedly instantiates
the selected solver and calls mesh.objectRegistry::clear() after each time.

This diagnostic compares -time t0, -time t1, -time tFinal individually
with one combined -time 't0,t1,tFinal'. Each test uses a distinct NEW,
minimal, PHYSICAL COPY (constant, system, three saved time directories).
No mesh or physical model is modified, no existing original CFD file or
old _01/_02/_03 postprocessing is written, NO foamMultiRun or CFD solving.
Logs and a single report are written only in fresh --out.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import stage_c14_3d_case_a as stage
import run_c14_3d_complete_postprocess as old
import run_c14_stage07_solver_backed_recovery as recovery

REPORT = "C3D04_A_F14_NATIVE_SINGLE_VS_MULTITIME_PROBE_REPORT.json"
GROUP = "metalSensibleEnthalpy"
TIME_TRIALS = ("standalone_t0", "standalone_t1", "standalone_tfinal", "combined_three_times")


class ProbeBlocked(ValueError):
    pass


def need(ok: bool, reason: str) -> None:
    if not ok:
        raise ProbeBlocked("C3D04_A_F14_TIME_ISOLATION_BLOCKED: " + reason)


def sha(path: Path) -> str:
    need(path.is_file() and not path.is_symlink(), "missing regular file: " + str(path))
    h = hashlib.sha256()
    with path.open("rb") as reader:
        for buffer in iter(lambda: reader.read(1 << 18), b""):
            h.update(buffer)
    return h.hexdigest()


def nrows_native(path: Path) -> dict:
    rows = []
    with path.open(encoding="utf-8", errors="replace") as reader:
        for line in reader:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            cols = line.split()
            if cols:
                try:
                    t = float(cols[0])
                except ValueError:
                    return {"valid_numeric_data": False, "rows": len(rows)}
                need(math.isfinite(t), "nonfinite C14 native table time")
                rows.append(t)
    return {"valid_numeric_data": True, "rows": len(rows),
            "saved_times_s": rows[:8], "last_time_s": rows[-1] if rows else None}


def validate_path(root: Path, candidate: Path, what: str) -> None:
    need(root.is_dir() and not root.is_symlink(), what + " not a regular directory")
    need(not any(p.is_symlink() for p in root.rglob("*")),
         what + " contains symlinks; refuse following external data")
    need(candidate != root and root not in candidate.parents
         and candidate not in root.parents,
         "requested output overlaps protected " + what)


def snapshots(case: Path, names: list[str], cells: int, out: Path) -> dict:
    case = case.expanduser().resolve()
    out = out.expanduser().absolute()
    need(cells in (27, 8960), "only synthetic F14 27 or native V4/T02 8960 supported")
    need(case.is_dir() and not case.is_symlink(), "source C14 case missing")
    need(not out.exists() and not out.is_symlink(),
         "new probe output already exists; NEVER overwrite evidence")
    need(out.parent.is_dir(), "probe output parent missing")
    need(case != out and case not in out.parents and out not in case.parents,
         "output inside original 10s source CFD")
    # Prevent accidental user supplied repo directory as a scratch target.
    need(not out.is_relative_to(Path(__file__).resolve().parents[3]),
         "cannot place probe inside MasterProject repository")
    need(len(names)==3 and len(set(names))==3, "exactly three distinct saved times required")
    values = [float(t) for t in names]
    need(values[0] == 0 and 0 < values[1] < values[2] <= 10,
         "require three ordered snapshots starting at 0")
    origin_ctrl=case/"system/controlDict"
    c14_ctrl=recovery.C14/"system/controlDict"
    if cells==8960:
        need(sha(origin_ctrl)==sha(c14_ctrl),
             "real source C14 controlDict differs from original research physics")
    else:
        need("actual_C14_fluid_solid_2step" in case.parts,
             "27-cell fixture only permitted in completed native C14 CI smoke")
    log=case/"log.foamMultiRun"
    need(log.is_file() and not log.is_symlink(), "source CFD log missing")
    geometry=stage.region_cells(case,"metal",cells)
    zone=case/"constant/metal/polyMesh/cellZones"
    need(stage.audit_existing_zone(zone,cells),
         "source is missing authentic full-metal cellZone (do not manufacture it)")
    source_files=[origin_ctrl, log, zone]
    source_files += [case/"constant/metal/polyMesh"/name for name in stage.MESH]
    for n in names:
        need(n not in (".","..") and "/" not in n and "\\" not in n,
             "unsafe selected time string")
        folder=case/n
        need(folder.is_dir() and not folder.is_symlink(),
             "selected saved time directory absent: " + n)
        need((folder/"metal/T").is_file() and (folder/"metal/U").is_file(),
             "selected saved time missing metal T/U: " + n)
        source_files.append(folder/"metal/T")
    # Validate EVERY selected directory before mkdir on the fresh output.
    # A single external symlink must NOT leave an occupied partial workcopy.
    for name in ("constant","system",*names):
        directory=case/name
        need(directory.is_dir() and not directory.is_symlink(),
             "source snapshot directory missing: "+name)
        need(not any(p.is_symlink() for p in directory.rglob("*")),
             "source has unexpected external symlink: "+name)
    digests={str(p.relative_to(case)):sha(p) for p in source_files}
    return {"case":case,"out":out,"names":names,"cells":cells,
            "nCells_native_mesh":geometry["nCells"],
            "source_sha256":digests}


def copy_one_trial(source: Path, folder: Path, times: list[str]) -> Path:
    need(not folder.exists() and not folder.is_symlink(),
         "recovery trial output occupied")
    folder.mkdir()
    for base in ("constant","system",*times):
        src=source/base
        need(src.is_dir() and not src.is_symlink(),
             "missing physical C14 source directory: "+base)
        # Strictly only a few snapshots, no symbolic links back to CFD.
        need(not any(p.is_symlink() for p in src.rglob("*")),
             "source has unexpected external symlink: "+base)
        shutil.copytree(src,folder/base,symlinks=False)
    native_dict=folder/"system/stage07TimeIsolationProbe"
    original=recovery.C14/"system/researchDiagnostics"
    block=recovery.selected_source_block(
        original.read_text(encoding="utf-8"),GROUP)
    need(not native_dict.exists(), "trial diagnostic already present")
    native_dict.write_text(
        "FoamFile\n{\n    format ascii;\n    class dictionary;\n"
        '    location "system";\n    object stage07TimeIsolationProbe;\n}\n\n'
        +block,encoding="utf-8")
    return native_dict


def native_probe_trial(work: Path, label: str, selector: str, times: list[str]) -> dict:
    d=copy_one_trial(work["case"],work["out"]/label,times)
    arguments=["foamPostProcess","-region","metal","-solver","fluid",
               "-dict","system/"+d.name,"-time",selector]
    process=old.run_native(d.parent,"f14TimeIsolation_"+label,arguments)
    log=d.parent/process["log"]
    fatal=recovery.fatal_openfoam_log(log)
    errors=recovery.forensic.error_excerpt(log,limit=5)
    root=d.parent/"postProcessing/metal"/GROUP
    table_files=sorted(root.rglob("volFieldValue.dat")) if root.is_dir() else []
    tables={str(p.relative_to(d.parent)):nrows_native(p) for p in table_files}
    valid_rows=all(v["valid_numeric_data"] for v in tables.values())
    return {
        "label":label, "selector":selector,
        "command_without_bootstrap":arguments,
        "return_code":process["exit_code"],
        "return_code_zero":process["exit_code"] == 0,
        **fatal,
        "no_FOAM_FATAL":not fatal["foam_fatal_present"],
        "native_semantic_success":
            process["exit_code"]==0 and not fatal["foam_fatal_present"]
            and bool(tables) and valid_rows
            and sum(v["rows"] for v in tables.values())>0,
        "log":str(log.relative_to(work["out"])),
        "log_sha256":sha(log),
        "log_error_signatures":errors["error_signatures"],
        "log_last_24_lines":errors.get("tail_last_24_lines",[]),
        "native_rho_h_tables":tables,
    }


def execute(case: Path, out: Path, times: list[str], cells: int) -> dict:
    work=snapshots(case,times,cells,out)
    work["out"].mkdir()
    results=[]
    for label,selector in zip(TIME_TRIALS,
                              (*times,",".join(times))):
        results.append(native_probe_trial(work,label,selector,times))
    before=work["source_sha256"]
    after={rel:sha(work["case"]/rel) for rel in before}
    need(before==after,"original source CFD file hashes changed during offline probe")
    solo=results[:3]
    mixed=results[3]
    alone_ok=all(x["native_semantic_success"] for x in solo)
    if alone_ok and mixed["foam_fatal_present"]:
        verdict="REPRODUCED_NATIVE_MULTITIME_REGISTRY_FAILURE_IN_SAME_SAVED_C14_FIELDS"
    elif alone_ok and mixed["native_semantic_success"]:
        verdict="SINGLE_AND_MULTITIME_NATIVE_PASS_NO_REGISTRY_FAILURE_REPRODUCED"
    elif alone_ok:
        verdict="INDIVIDUAL_TIMES_PASS_BUT_COMBINED_INCOMPLETE_UNCLASSIFIED"
    else:
        verdict="SINGLE_TIME_NATIVE_FAILURE_PRESENT_NOT_ONLY_MULTITIME"
    report={
        "schema":"C3D04_A_F14_NATIVE_MULTITIME_VS_STANDALONE_V1",
        "date_utc":datetime.now(timezone.utc).isoformat(),
        "source_run_read_only":str(work["case"]),
        "isolated_minimal_probe_out":str(work["out"]),
        "mesh_cells_metal":cells,
        "genuine_saved_states":times,
        "physical_model":"original C14 Foundation14 heRhoThermo plus fvModels and original metalSensibleEnthalpy function",
        "trial_results":results,
        "three_independent_times_all_pass":alone_ok,
        "combined_all_three_times_pass":mixed["native_semantic_success"],
        "combined_FOAM_FATAL_count":mixed["foam_fatal_occurrence_count"],
        "verdict":verdict,
        "source_SHA256_unchanged":True,
        "original_solver_rerun":False,
        "source_CFD_modified":False,
        "old_stage07_workcopies_modified":False,
        "native_energy_conservation_verified":False,
        "quickcup_verified":False,
        "stage":"07/10","milestones_done":"6/10",
        "limitations":[
            "Only three selected saved snapshots are copied; does not process all 101 states.",
            "Negative multi-time vs single-time test proves a symptom at selected times, not a complete C++ root cause.",
            "If individual times pass and combined fails, evaluate a new-copy per-time Foundation14 postprocessing design; do not edit CFD physics.",
            "Original in-solver ddt 0.001s history is not reconstructible from saved 0.1s snapshots.",
        ],
    }
    target=work["out"]/REPORT
    need(not target.exists(),"probe report output unexpectedly occupied")
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                      encoding="utf-8")
    return {
        "status":"THREE_TIME_ISOLATED_NATIVE_F14_PROBE_COMPLETED",
        "case":str(work["case"]),
        "probe_out":str(work["out"]),
        "verdict":verdict,
        "individual_results":[{
            "time":t,"pass":r["native_semantic_success"],
            "FATAL":r["foam_fatal_occurrence_count"],
            "native_tables":r["native_rho_h_tables"]}
            for t,r in zip(times,solo)],
        "combined_three_time":{
            "pass":mixed["native_semantic_success"],
            "FATAL":mixed["foam_fatal_occurrence_count"],
            "native_tables":mixed["native_rho_h_tables"],
            "log_last_24_lines":mixed["log_last_24_lines"]},
        "original_solver_rerun":False,
        "real_C14_original_controlDict_untouched":True,
        "global_energy_conservation_verified":False,
        "report":str(target),
        "stage":"07/10","milestones_done":"6/10",
    }


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",type=Path,default=Path.home()/
                    "OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--times",nargs=3,default=["0","0.1","10"],
                    metavar=("INITIAL","INTERMEDIATE","FINAL"))
    ap.add_argument("--metal-cells",type=int,default=8960)
    args=ap.parse_args()
    try:
        print(json.dumps(execute(args.case,args.out,args.times,args.metal_cells),
                         indent=2,ensure_ascii=False))
        return 0
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as exc:
        print("C3D04_A_F14_TIME_ISOLATION_PROBE_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
