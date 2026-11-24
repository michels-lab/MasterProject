#!/usr/bin/env python3
"""Isolated Foundation14 C14 FLUID+SOLID native q on existing completed 10s CFD.

Do not invoke foamMultiRun, gmsh, change original mesh, modify old 101 state
analysis, nor replace existing new outputs. Compiles source in isolated
directory with wmake and reads only saved 101 fields, producing 4-patch heat
q timeline and t=10s full per-face q, then SHA-bound diagnostics.

--preflight: strict source, mesh, log, time and C14 original selection audit.
--extract: native POSTPROCESS-ONLY wmake+q; needs OpenFOAM-14 environment.
Failure keeps isolated logs under hidden attempt path outside CFD. Success
atomic-publishes the verified output directory, without CFD mutation.
"""
from __future__ import annotations

import argparse
import csv
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze_existing_case_b_c14 as native
import analyze_existing_case_b_c14_native_flux as audit

CASE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
OUTPUT=Path.home()/"OpenFOAM/C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01"
SOURCE=HERE/"native_flux"
SRC_FILES=(
    "c3d05C14FluidSolidFlux.C",
    "Make/files",
    "Make/options",
)
INTEGRALS="C3D05_B_C14_NATIVE_Q_101X4_PATCHES.csv"
LAST_FACES="C3D05_B_C14_NATIVE_Q_T10_ALL_FACES.csv"
TIMELINE="C3D05_B_C14_NATIVE_Q_101_TIMES.csv"
REPORT="C3D05_B_C14_NATIVE_Q_FLUID_SOLID_REPORT.json"
MANIFEST="C3D05_B_C14_NATIVE_Q_SOURCE_AND_RESULTS_SHA256.json"
LOG_BUILD="log.wmake.C3D05_B_C14_NATIVE_FLUX"
LOG_EXTRACT="log.C3D05_B_C14_NATIVE_FLUX"


def require(ok:bool, reason:str)->None:
    if not ok:
        raise ValueError("C3D05_B_C14_NATIVE_FLUX_BLOCKED: "+reason)


def sha(path:Path)->str:
    require(path.is_file() and not path.is_symlink(),
            "missing/symlinked input "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as fp:
        while b:=fp.read(1024*1024):
            h.update(b)
    return h.hexdigest()


def preflight(case:Path,output:Path)->dict:
    case=case.expanduser().absolute()
    output=output.expanduser().absolute()
    require(case.is_dir() and not case.is_symlink()
            and case.name==CASE.name,
            "only accepted original completed C3D05 Case B real fluid+solid CFD allowed")
    require(output!=case and output not in case.parents
            and case not in output.parents,
            "new q destination must never be in old CFD case")
    require(not output.exists() and not output.is_symlink(),
            "q output already exists; preserve it, no overwrite")
    original,verification=native.validated_mesh_and_stage(case)
    require(original.get("native_solver_run") is True
            and original.get("status")==native.SUCCESS
            and original.get("contraction_model_activated") is False,
            "not completed original C14 10s source-faithful fluid+solid")
    require(sha(case/native.LOG)==original["solver_log_sha256"],
            "original complete native foamMultiRun log changed")
    logdata=native.source_reader.parse_full_log(
        (case/native.LOG).read_text(encoding="utf-8",errors="replace"))
    require(logdata["native_end_found"] is True
            and logdata["time_last_s"]==10.0
            and logdata["selected_C14_fluid_solid_phase_model"] is True,
            "original C14 model/foamMultiRun completion not verified")
    require(len(native.saved_times(case))==101,
            "101 native snapshots 0-10s not present")
    require(verification["metal_cells"]==92200 and
            verification["mold_cells"]==178588,
            "not accepted original 270788 HEX8 region sizes")
    source_hashes={}
    for path in SRC_FILES:
        source_hashes[path]=sha(SOURCE/path)
    cpp=(SOURCE/SRC_FILES[0]).read_text(encoding="utf-8")
    require("fluidThermoThermophysicalTransportModel::New(momentum(),tm())" in cpp
            and "solidThermophysicalTransportModel::New(td())" in cpp
            and "dirs.size()!=101" in cpp
            and "metal_to_mold" in cpp and "mold_to_metal" in cpp
            and "metalTop" in cpp and "moldOuterUnclassified" in cpp,
            "compiled source does not use the original two different C14 thermal transport models")
    require("foamMultiRun(" not in cpp and "gmsh" not in cpp.lower(),
            "unexpected CFD solver or mesh-changing code in flux exporter")
    return {
        "source_read_only_case":str(case),
        "expected_new_output":str(output),
        "native_real_C14_solver_10s_complete":True,
        "source_fluid_metal_solid_mold_verified":True,
        "source_cpp_sha256":source_hashes,
        "native_solver_log_sha256":sha(case/native.LOG),
        "native_stage_report_sha256":sha(case/native.REPORT),
        "native_mesh_270788_hex8":True,
        "saved_states":101,
        "original_CFD_no_rerun":True,
        "native_compiler_checked":False,
        "native_q_extracted":False,
        "physical_energy_closure":False
    }


def invoke(argv:list[str],cwd:Path,env:dict,log:Path)->None:
    require(not log.exists() and not log.is_symlink(),
            "preserved prior isolated log must never be overwritten")
    recent=deque(maxlen=80)
    with log.open("x",encoding="utf-8") as fp:
        p=subprocess.Popen(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,bufsize=1,
                           text=True,errors="replace")
        assert p.stdout is not None
        for line in p.stdout:
            fp.write(line)
            recent.append(line.rstrip("\n"))
            if ("C3D05_B_C14_FLUID_SOLID_NATIVE_Q_READONLY" in line or
                "Error" in line or "error:" in line or
                "FAILED" in line or "FOAM FATAL" in line):
                print(line.rstrip(),flush=True)
        rc=p.wait()
    if rc:
        # The original runner printed only "FOAM FATAL IO ERROR" and hid the
        # essential dictionary/file/line details on following log lines.
        # Only print preserved stderr log context, NEVER retry the solver.
        print("C3D05_B_C14_NATIVE_Q_FAILURE_FULL_LOG_TAIL_BEGIN",file=sys.stderr)
        for line in recent:
            print(line,file=sys.stderr)
        print("C3D05_B_C14_NATIVE_Q_FAILURE_FULL_LOG_TAIL_END",file=sys.stderr)
    require(rc==0,"native tool failed rc="+str(rc)+"; preserved log at "+str(log))


def diagnose_attempt(attempt:Path)->dict:
    """READ ONLY: find the actual fatal IO diagnosis from a PRESERVED attempt.

    No source, CFD, compile or q extraction. Reject any unrelated path.
    """
    path=attempt.expanduser().resolve(strict=True)
    home=OUTPUT.parent.resolve(strict=True)
    require(path.is_dir() and not path.is_symlink()
            and path.parent==home
            and path.name.startswith("."+OUTPUT.name+".ATTEMPT_"),
            "diagnostic path must be an existing isolated C3D05 B q attempt")
    build=path/LOG_BUILD
    extract=path/LOG_EXTRACT
    require(extract.is_file() and not extract.is_symlink(),
            "native extractor log not present; inspect build log instead")
    lines=extract.read_text(encoding="utf-8",errors="replace").splitlines()
    markers=("FOAM FATAL","Fatal IO","FATAL ERROR",
             "Cannot find","cannot find","Unknown","error:",
             "Entry","keyword","dictionary")
    indices=[i for i,line in enumerate(lines)
             if any(marker in line for marker in markers)]
    if indices:
        first=next((i for i in indices if
                    "FOAM FATAL" in lines[i] or "FATAL ERROR" in lines[i]),
                   indices[0])
        start=max(0,first-12)
        end=min(len(lines),first+36)
        context=lines[start:end]
    else:
        context=lines[-65:]
    return {
        "status":"C3D05_B_C14_PRESERVED_FAILED_NATIVE_Q_LOG_DIAGNOSED_ONLY",
        "attempt":str(path),
        "build_log":str(build) if build.is_file() else None,
        "runtime_log":str(extract),
        "compiled_native_binary_exists":(path/"bin/c3d05C14FluidSolidFlux").is_file(),
        "native_q_successfully_published":False,
        "fatal_error_context_lines":context,
        "original_CFD_untouched":True,
        "NO_CFD_NO_REBUILD_NO_NEW_EXTRACTION":True,
    }


def run(case:Path,output:Path)->dict:
    case=case.expanduser().absolute()
    output=output.expanduser().absolute()
    state=preflight(case,output)
    require(os.getenv("WM_PROJECT_VERSION")=="14",
            "source /opt/openfoam14/etc/bashrc; ONLY native Foundation14 is allowed")
    require(shutil.which("wmake") is not None,
            "OpenFOAM Foundation14 wmake not found")
    output.parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(
        prefix="."+output.name+".ATTEMPT_",dir=output.parent))
    print("C3D05_B_C14_NATIVE_Q_BUILD_ATTEMPT_PRESERVED: "+str(work),
          flush=True)
    source=work/"source"
    shutil.copytree(SOURCE,source)
    bin_dir=work/"bin"
    bin_dir.mkdir()
    env=os.environ.copy()
    env["FOAM_USER_APPBIN"]=str(bin_dir)
    invoke(["wmake",str(source)],work,env,work/LOG_BUILD)
    binary=bin_dir/"c3d05C14FluidSolidFlux"
    require(binary.is_file() and os.access(binary,os.X_OK),
            "real native C14 fluid+solid flux binary not produced: "+str(work))
    staging=work/"published"
    staging.mkdir()
    invoke([
        str(binary),"-case",str(case),"-time","0:10",
        "-outIntegrated",str(staging/INTEGRALS),
        "-outLastFaces",str(staging/LAST_FACES)
    ],work,env,work/LOG_EXTRACT)
    q=audit.native_flux_analysis(staging/INTEGRALS,staging/LAST_FACES)
    require(q["stored_time_count"]==101
            and q["native_interface_faces_each"]==12636
            and q["real_fluid_and_solid_heat_conduction_q_computed"] is True,
            "C14 actual native q source output does not meet original 101x4 contract")
    with (staging/TIMELINE).open("x",encoding="utf-8",newline="") as stream:
        rows=q.pop("patch_time_history")
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    q["patch_time_history_file"]=TIMELINE
    q["native_q_method_compiled_in_user_environment_not_verified_until_execution"]=True
    q["original_CFD_source_read_only"]=str(case)
    q["source_preflight"]=state
    (staging/REPORT).write_text(json.dumps(
        q,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    shutil.copy2(work/LOG_BUILD,staging/LOG_BUILD)
    shutil.copy2(work/LOG_EXTRACT,staging/LOG_EXTRACT)
    (staging/MANIFEST).write_text(json.dumps({
        "original_CFD_log_SHA256":state["native_solver_log_sha256"],
        "original_CFD_stage_SHA256":state["native_stage_report_sha256"],
        "source_C14_compiled_CPP_SHA256":sha(source/SRC_FILES[0]),
        "compiled_native_tool_SHA256":sha(binary),
        "native_integrated_101times_CSV_SHA256":sha(staging/INTEGRALS),
        "native_all_faces_t10_CSV_SHA256":sha(staging/LAST_FACES),
        "native_q_timeline_101_CSV_SHA256":sha(staging/TIMELINE),
        "audited_report_SHA256":sha(staging/REPORT),
        "wmake_log_SHA256":sha(staging/LOG_BUILD),
        "native_q_log_SHA256":sha(staging/LOG_EXTRACT),
        "original_CFD_untouched":True,
        "source_isolated":True
    },indent=2)+"\n",encoding="utf-8")
    require(not output.exists() and not output.is_symlink(),
            "another q result appeared; do not replace")
    staging.rename(output)
    # Source build artifacts and original (successful) compiler stage are
    # discarded only after all immutable q evidence has been published.
    shutil.rmtree(work)
    return q


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--preflight",action="store_true")
    choice.add_argument("--extract",action="store_true")
    choice.add_argument("--diagnose-attempt",type=Path,metavar="EXISTING_DIR")
    parser.add_argument("--case",type=Path,default=CASE)
    parser.add_argument("--out",type=Path,default=OUTPUT)
    args=parser.parse_args()
    try:
        report=(diagnose_attempt(args.diagnose_attempt)
                if args.diagnose_attempt is not None else
                preflight(args.case,args.out) if args.preflight
                else run(args.case,args.out))
        if args.diagnose_attempt is not None or args.preflight:
            print(json.dumps(report,indent=2,ensure_ascii=False))
        else:
            print(json.dumps({
                "status":report["status"],
                "out":str(args.out),
                "saved_states":report["stored_time_count"],
                "native_patch_count":report["native_patch_count"],
                "native_interface_faces_each":report["native_interface_faces_each"],
                "last_time_patch_fluxes_W":report["final"],
                "last_time_interface_face_geometry":report["per_face_geometry"],
                "native_latent_source_integrated":False,
                "overall_energy_conservation_verified":False,
                "CFD_RERUN":False
            },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        print("C3D05_B_C14_NATIVE_Q_RUN_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
