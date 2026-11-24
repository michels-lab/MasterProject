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
import re
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



def prepare_isolated_c14_flux_case(
    original:Path, shadow:Path, saved:list[tuple[float,str]]
)->dict:
    """An ORIGINAL-FIELDS read-only mirror with one explicit q-only scheme.

    The completed CFD's original system/mold/fvSchemes has
        interpolate((kappa|Cv)) harmonic;
    which does not satisfy F14 solidTransport.q() exact lookup
        interpolate(kappa).
    We ADD this explicit harmonic entry ONLY to the COPIED system file. All
    101 real time/region directories are recreated with field-file symlinks;
    constant is symlinked READ-ONLY-INTENT
    to original source (the extractor has NO write to input). Never insert
    this into the thesis CFD's real fvSchemes or rewrite archived fields.
    """
    original=original.expanduser().absolute()
    shadow=shadow.expanduser().absolute()
    require(original.is_dir() and original.name==CASE.name
            and not original.is_symlink(),
            "shadow source must be the source-verified real C14 B case")
    require(shadow!=original and shadow not in original.parents
            and original not in shadow.parents,
            "shadow must be separate from old CFD case")
    require(not shadow.exists() and not shadow.is_symlink(),
            "never replace existing isolated shadow")
    require(len(saved)==101 and saved[0][0]==0 and saved[-1][0]==10,
            "shadow requires exactly the 101 original native 0..10s time states")
    require(len({label for _,label in saved})==101,
            "original CFD saved time names duplicated")
    source_schemes=original/"system/mold/fvSchemes"
    require(source_schemes.is_file() and not source_schemes.is_symlink(),
            "original mold fvSchemes not a regular source dictionary")
    original_text=source_schemes.read_text(encoding="utf-8")
    # Require exactly one real interpolationSchemes dictionary and harmonic
    # C14 mold baseline; do NOT choose a numeric scheme arbitrarily.
    blocks=list(re.finditer(
        r"\binterpolationSchemes\s*\{([^{}]*)\}",original_text,re.S))
    require(len(blocks)==1,"C14 native mold interpolationSchemes not unique/simple")
    body=blocks[0].group(1)
    non_comments=re.sub(r"/\*.*?\*/|//[^\n]*","",body,flags=re.S)
    require(re.search(
        r"\binterpolate\(\(kappa\|Cv\)\)\s+harmonic\s*;",
        non_comments) is not None,
        "real original C14 harmonic kappa/Cv intent absent; no invented scheme")
    require(re.search(
        r"\binterpolate\(kappa\)\s+\w+\s*;",non_comments) is None,
        "real original scheme already specifies interpolate(kappa); "
        "unexpected WSL IO error, do not inject duplicate")
    original_sha=sha(source_schemes)
    insertion="\n    interpolate(kappa) harmonic; // POSTPROCESSING ONLY, original C14 harmonic scheme\n"
    at=blocks[0].end()-1
    copied_text=original_text[:at]+insertion+original_text[at:]
    require(copied_text.count(insertion)==1,
            "q-only harmonic insertion did not happen exactly once")
    shadow.mkdir(parents=True)
    source_system=original/"system"
    require(source_system.is_dir() and not source_system.is_symlink(),
            "native original system dictionary not a directory")
    shutil.copytree(source_system,shadow/"system",symlinks=False)
    target=shadow/"system/mold/fvSchemes"
    require(target.is_file() and not target.is_symlink(),
            "unexpected copied system/mold/fvSchemes")
    target.write_text(copied_text,encoding="utf-8")
    for name in ("constant",):
        source_dir=original/name
        require(source_dir.is_dir() and not source_dir.is_symlink(),
                "original CFD constant directory unsafe/missing")
        (shadow/name).symlink_to(source_dir,target_is_directory=True)
    for time,label in saved:
        require(re.fullmatch(r"\d+(?:\.\d+)?",label) is not None
                and 0<=time<=10,
                "unsafe original native CFD saved time label")
        original_dir=original/label
        require(original_dir.is_dir() and not original_dir.is_symlink(),
                "missing/nonregular original archived time directory: "+label)
        # OpenFOAM Time::findTimes enumerates real directories; symlinked
        # TOP-LEVEL time directories may not be enumerated as saved times.
        # Create real time/region directories containing READ-ONLY-INTENT
        # symlinks to ORIGINAL FIELD FILES, not to time directories.
        shadow_time=shadow/label
        shadow_time.mkdir()
        for region in ("metal","mold"):
            source_region=original_dir/region
            require(source_region.is_dir() and not source_region.is_symlink(),
                    "missing original time/region: "+label+"/"+region)
            shadow_region=shadow_time/region
            shadow_region.mkdir()
            for entry in source_region.iterdir():
                require(not entry.is_symlink() and
                        (entry.is_file() or entry.is_dir()),
                        "unsafe original C14 region entry: "+str(entry))
                (shadow_region/entry.name).symlink_to(
                    entry,target_is_directory=entry.is_dir())
        for entry in original_dir.iterdir():
            if entry.name in ("metal","mold"):
                continue
            require(not entry.is_symlink() and
                    (entry.is_file() or entry.is_dir()),
                    "unsafe original CFD time directory entry: "+str(entry))
            (shadow_time/entry.name).symlink_to(
                entry,target_is_directory=entry.is_dir())
    require(sha(source_schemes)==original_sha,
            "original mold fvSchemes SHA altered during shadow creation")
    require(sha(target)!=original_sha,
            "q-only shadow scheme not distinguished from source")
    return {
        "schema":"C3D05_B_C14_ISOLATED_Q_ONLY_MOLD_INTERPOLATION_OVERLAY_V1",
        "original_CFD_source_unchanged":str(original),
        "original_mold_fvSchemes_SHA256":original_sha,
        "temporary_overlay_mold_fvSchemes_SHA256":sha(target),
        "original_mold_scheme":"interpolate((kappa|Cv)) harmonic;",
        "explicit_shadow_only_scheme":"interpolate(kappa) harmonic;",
        "saved_real_time_directories_reconstructed":len(saved),
        "each_region_file_symlinked_to_original_read_only_intent":True,
        "constant_linked_read_only_intent":True,
        "system_copied_and_ONLY_mold_fvSchemes_amended":True,
        "original_CFD_not_remeshed_or_resolved":True,
        "notes":[
            "One explicit F14 interpolate(kappa) harmonic entry is added to isolated q-only fvSchemes.",
            "This exact postprocessing scheme was NOT in original solver dictionary; "
            "the postrun q reconstruction is not a solver-dt native flux history.",
            "The source CFD case's original thermos, fvModels, archived fields and mesh are unchanged.",
        ],
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
    # Shadow contains COPIED system dictionaries (only mold interpolate(kappa)
    # added) + real 101 time/region dirs with symlinks to archived original
    # field files; original constant stays linked read-only-intent.
    # Never insert a scheme into ORIGINAL $HOME/OpenFOAM/.../system/mold/fvSchemes.
    saved=native.saved_times(case)
    overlay=prepare_isolated_c14_flux_case(
        case,work/"shadow_postrun_case",saved)
    (staging/"C3D05_B_C14_FLUX_Q_ONLY_SHADOW_SCHEME.json").write_text(
        json.dumps(overlay,indent=2)+"\n",encoding="utf-8")
    print("C3D05_B_C14_Q_ONLY_SHADOW_HARMONIC_FVSCHEMES: "
          +str(work/"shadow_postrun_case"),flush=True)
    invoke([
        str(binary),"-case",str(work/"shadow_postrun_case"),"-time","0:10",
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
    q["q_only_shadow_fvSchemes_provenance"]=overlay
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
        "source_isolated":True,
        "original_mold_fvSchemes_SHA256":overlay["original_mold_fvSchemes_SHA256"],
        "q_only_overlay_mold_fvSchemes_SHA256":
            overlay["temporary_overlay_mold_fvSchemes_SHA256"],
        "q_only_overlay_report_SHA256":sha(
            staging/"C3D05_B_C14_FLUX_Q_ONLY_SHADOW_SCHEME.json")
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
