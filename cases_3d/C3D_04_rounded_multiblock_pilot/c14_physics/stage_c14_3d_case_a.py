#!/usr/bin/env python3
"""Caso A C3D-04: stage original C14 fluid+solid on preserved native V4/T02.

Only mandatory 2D->3D adaptations: pressure gauge cell index, complete metal
cellZone, 3D patch BC and Foundation14 externalTemperature syntax. Source
C14 materials, U, p, p_rgh, thermo, phaseChangeSource, dt remain unchanged.

--preflight: no writes; --materialize: full 10s inputs no CFD; --smoke:
isolated two-step real foamMultiRun and preserved evidence even upon failure.
Never overwrites accepted V4/T02, never blockMesh/remesh.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
CASE_A = HERE.parent
sys.path.insert(0, str(CASE_A/"t0_conduction"/"scripts"))
import prepare_case_a_t0 as gate
import c14_source_fidelity as physics

SOURCE = Path.home()/"OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02"
DEST = Path.home()/"OpenFOAM/C3D04_A_C14_FLUID_SOLID_NATIVE_01"
EXPECTED = {"metal": 8960, "mold": 12352}
MESH = ("points", "faces", "owner", "neighbour", "boundary")
REPORT = "C14_3D_A_NATIVE_STAGE_REPORT.json"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError("C3D04_A_C14_NATIVE_GATE_BLOCKED: "+message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_labels(path: Path) -> tuple[int, int]:
    """OpenFOAM Foundation14 labelList: n(...), n{uniformLabel} or 0().

    Source-verified 2026-11-20: native blockMesh writes compact 6{0} in
    owner and 0() in neighbour; assuming n/(...)/ only is incorrect.
    Never infer cell counts from arbitrary text/comments.
    """
    raw=path.read_text(encoding="utf-8")
    require("class       labelList;" in raw or
            re.search(r"\bclass\s+labelList\s*;",raw) is not None,
            "expected native labelList in "+str(path))
    # Search the payload AFTER the complete FoamFile metadata dictionary.
    head=re.search(r"\bFoamFile\s*\{[^{}]*\}",raw,re.S)
    require(head is not None,"native FoamFile header missing in "+str(path))
    rest=raw[head.end():]
    m=re.search(r"(?m)^\s*(\d+)\s*(?:\{\s*(\d+)\s*\}|\(\s*([\d\s]*)\))",rest,re.S)
    require(m is not None,"native labelList payload absent "+str(path))
    declared=int(m.group(1))
    require(declared>=0,"negative list length "+str(path))
    if m.group(2) is not None:
        # Foam::UList compressed uniform form, e.g. 6{0}.
        value=int(m.group(2))
        require(value>=0,"negative compressed cell label")
        return declared, value if declared else -1
    values=[int(x) for x in (m.group(3) or "").split()]
    require(len(values)==declared and all(x>=0 for x in values),
            "polyMesh expanded list length/labels invalid "+str(path))
    return declared, max(values,default=-1)


def region_cells(case: Path, region: str, expected: int | None) -> dict:
    root = case/"constant"/region/"polyMesh"
    for name in MESH:
        require((root/name).is_file() and not (root/name).is_symlink(),
                "missing source native mesh "+str(root/name))
    n_owners, max_owner = read_labels(root/"owner")
    n_neighbours, max_neighbour = read_labels(root/"neighbour")
    n_cells = max(max_owner, max_neighbour)+1
    require(n_cells > 0 and n_owners >= n_cells and n_neighbours < n_owners,
            "invalid cell topology inferred from actual polyMesh "+region)
    if expected is not None:
        require(n_cells == expected,
                f"actual {region} region cells {n_cells}, expected {expected}")
    return {"nCells":n_cells,"ownerFaces":n_owners,"internalFaces":n_neighbours,
            "region":region,"basis":"actual polyMesh owner+neighbour"}


def whole_region_zone(n: int) -> str:
    require(type(n) is int and 1 <= n <= 10000000,
            "invalid full metal region count")
    return (
        "FoamFile\n{\n    version 2.0;\n    format ascii;\n"
        "    class regIOobject;\n"
        '    location "constant/metal/polyMesh";\n'
        "    object cellZones;\n}\n"
        "1\n(\nmetal\n{\n    type cellZone;\n"
        f"    cellLabels List<label> {n}\n    (\n"
        + "\n".join(map(str, range(n))) +
        "\n    );\n}\n)\n"
    )


def audit_existing_zone(path: Path, n: int) -> bool:
    if not path.exists():
        return False
    require(path.is_file() and not path.is_symlink(),
            "preexisting zone is not a regular file")
    source = path.read_text(encoding="utf-8")
    matches = re.findall(r"(?m)^\s*metal\s*\{\s*(.*?)\s*\}",source,re.S)
    require(len(matches)==1,"preexisting zones lack a unique metal zone")
    found = re.search(
        r"\bcellLabels\s+List<label>\s+(\d+)\s*\(\s*([\d\s]*)\s*\)\s*;",
        matches[0],re.S)
    require(found is not None,"cannot parse original zone cell labels")
    labels = [int(x) for x in found.group(2).split()]
    require(int(found.group(1))==n and len(labels)==n
            and len(set(labels))==n and set(labels)==set(range(n)),
            "existing metal cellZone does not cover precisely all real metal cells")
    return True


def three_d_pressure_solution(text: str, n: int) -> str:
    """pRefCell 0 is inside [0,nCells) by construction, unlike 2D pRefPoint."""
    require(n>0,"cannot select reference in empty metal region")
    pattern = r"(?m)^(\s*)pRefPoint\s*\(\s*0\.02\s+0\.04\s+0\.005\s*\)\s*;"
    text, count = re.subn(pattern,lambda m:m.group(1)+"pRefCell          0;",text)
    require(count==1,"original 2D pRefPoint absent/duplicated")
    require(re.search(r"\bpRefValue\s+1e5\s*;",text) is not None,
            "C14 reference pressure 1e5 changed")
    require("pRefPoint" not in physics.strip_comments(text),
            "old 2D point still in native 3D regional dictionary")
    return text


def smoke_control(text: str) -> str:
    for key,pattern,value in (
        ("endTime",r"(?m)^(\s*)endTime\s+10\s*;","endTime 0.002;"),
        ("writeInterval",r"(?m)^(\s*)writeInterval\s+100\s*;","writeInterval 1;")
    ):
        text,count = re.subn(pattern,lambda m:m.group(1)+value,text)
        require(count==1,"C14 original "+key+" not recognized")
    require(re.search(r"\bdeltaT\s+0\.001\s*;",text) is not None,
            "original C14 time step changed")
    return text


def enforce_C14_3D_only_delta(
    files: dict[str,str], original: dict[str,str], n: int,
    *, smoke: bool, existing_zone: bool,
) -> None:
    """Fail closed: C14 may change ONLY where its 2D mesh requires it.

    For the full 10-second research input, the only alterations to the
    ORIGINAL 14 C14 dictionaries are the mesh-indexed pressure reference
    in system/metal/fvSolution; the other 13 remain byte-identical.
    The 8 initial field files reflect the same C14 initial/boundary
    values on real 3D patches. A new all-metal cellZone is mesh metadata.
    A synthetic-only two-step smoke may shorten endTime/writeInterval,
    but must NEVER be interpreted as the full C14 3D experiment.
    """
    additions=set() if existing_zone else {"constant/metal/polyMesh/cellZones"}
    require(set(files)==set(original)|additions,
            "unexpected file added/removed: only 3D mesh zone is allowed")
    required_pressure=three_d_pressure_solution(
        original["system/metal/fvSolution"],n)
    for relative, historical in original.items():
        actual=files[relative]
        if relative=="system/metal/fvSolution":
            require(actual==required_pressure,
                    "only pRefPoint -> valid 3D pRefCell is allowed")
        elif relative=="system/controlDict" and smoke:
            require(actual==smoke_control(historical),
                    "synthetic smoke may adjust ONLY horizon and writing")
        else:
            require(actual.encode("utf-8")==historical.encode("utf-8"),
                    "C14 original values/models/dictionaries changed: "+relative)
    if additions:
        require(files["constant/metal/polyMesh/cellZones"]==whole_region_zone(n),
                "metal zone must be exactly all native metal region cells")
    require(files["system/controlDict"]==original["system/controlDict"] if not smoke else True,
            "FULL 3D case must preserve C14 timing exactly")


def input_files(n: int, *, smoke: bool, existing_zone: bool=False) -> dict[str,str]:
    original=physics.assemble_unmaterialized_source_exact_fileset()
    files=dict(original)
    files["system/metal/fvSolution"] = three_d_pressure_solution(
        files["system/metal/fvSolution"],n)
    if not existing_zone:
        files["constant/metal/polyMesh/cellZones"] = whole_region_zone(n)
    if smoke:
        files["system/controlDict"] = smoke_control(files["system/controlDict"])
    enforce_C14_3D_only_delta(
        files,original,n,smoke=smoke,existing_zone=existing_zone)
    return files


def protect_source(source: Path, output: Path) -> None:
    source=source.resolve()
    output=output.absolute()
    require(source!=output and source not in output.parents
            and output not in source.parents,"output overlaps accepted V4/T02")
    require(not output.exists() and not output.is_symlink(),
            "refusing to overwrite output "+str(output))


def environment() -> dict:
    require(os.environ.get("WM_PROJECT_VERSION")=="14",
            "source OpenFOAM Foundation14 before this native step")
    tools={name:shutil.which(name)
           for name in ("foamDictionary","foamMultiRun","checkMesh")}
    require(all(tools.values()),"missing native F14 binaries")
    return tools


def native(cmd: list[str], work: Path, logname: str, limit: int) -> dict:
    r=subprocess.run(cmd,cwd=work,capture_output=True,text=True,
                     errors="replace",check=False,timeout=limit)
    log=work/logname
    log.write_text(
        "COMMAND: "+" ".join(cmd)+"\nRC: "+str(r.returncode)+
        "\nSTDOUT:\n"+r.stdout+"\nSTDERR:\n"+r.stderr,
        encoding="utf-8")
    if r.returncode!=0 or "FOAM FATAL" in r.stdout+r.stderr:
        raise RuntimeError("Foundation14 failure "+logname+
                           " (log preserved): "+(r.stdout+r.stderr)[-2200:])
    return {"log":logname,"sha256":digest(log),"rc":r.returncode}


def inspect(source: Path, expected: dict[str,int|None]) -> dict:
    source=source.expanduser().resolve()
    physics.verify()
    evidence=gate.native_case_gate(source) if expected==EXPECTED else {}
    counts={region:region_cells(source,region,expected[region])
            for region in ("metal","mold")}
    complete=audit_existing_zone(
        source/"constant/metal/polyMesh/cellZones",counts["metal"]["nCells"])
    return {"case":str(source),"gate":evidence,"counts":counts,
            "preexisting_full_metal_cellZone":complete,
            "pRefCell":0,"pRefValue":100000}


def stage(source: Path, output: Path, *, smoke: bool,
          expected: dict[str,int|None]|None=None) -> dict:
    source=source.expanduser().resolve()
    output=output.expanduser().absolute()
    protect_source(source,output)
    tools=environment()
    details=inspect(source,EXPECTED if expected is None else expected)
    counts=details["counts"]
    files=input_files(counts["metal"]["nCells"],smoke=smoke,
                      existing_zone=details["preexisting_full_metal_cellZone"])
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="."+output.name+".staging.",
                                     dir=output.parent) as folder:
        root=Path(folder)/"candidate"
        root.mkdir()
        source_hashes={}
        for region in ("metal","mold"):
            rel=Path("constant")/region/"polyMesh"
            shutil.copytree(source/rel,root/rel,symlinks=False)
            for name in MESH:
                path=rel/name
                source_hashes[str(path)]=digest(source/path)
                require(source_hashes[str(path)]==digest(root/path),
                        "region mesh copy differs from accepted polyMesh")
        for rel,body in files.items():
            path=root/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            require(not path.exists(),"candidate collides with original "+rel)
            with path.open("x",encoding="utf-8",newline="") as stream:
                stream.write(body)
        parsed=[]
        for rel in sorted(files):
            if rel.endswith("/cellZones"):
                continue
            native([tools["foamDictionary"],str(root/rel)],
                   root,"log.dict."+rel.replace("/", "."),45)
            parsed.append(rel)
        result={
            "status":"C3D04_A_C14_FLUID_SOLID_STAGED_F14_DICTS_PARSED_NOT_CFD",
            "accepted_native_mesh_read_only":str(source),
            "native_geometry_gate":details,
            "mesh_topology_hashes_source_equals_copy":source_hashes,
            "pressure_gauge_adaptation":"2D point -> existing regional cell index 0",
            "pRefCell":0,"pRefValue_Pa_original_C14":100000,
            "phase_source":"Original C14 solidificationMeltingSource, all metal cells",
            "physics":"metal fluid heRhoThermo hConst sensibleEnthalpy; mold solid eConst",
            "Cp_to_Cv_metal_substitution":False,
            "files_count":len(files),"parsed_dicts":parsed,
            "smoke_time_only_changes":smoke,
            "native_solver_run":False,"physical_validation":False,
            "source_C14_git_blob_validation":True,
            "output":str(output)
        }
        (root/REPORT).write_text(json.dumps(result,indent=2)+"\n",
                                 encoding="utf-8")
        protect_source(source,output)
        os.rename(root,output)
    return result


def run_smoke(output: Path, info: dict) -> dict:
    try:
        result=native([environment()["foamMultiRun"],"-case",str(output)],
                      output,"log.foamMultiRun",600)
        log=(output/"log.foamMultiRun").read_text(encoding="utf-8")
        require(re.search(r"(?m)^\s*End\s*$",log) is not None,
                "two-step native foamMultiRun did not terminate normally")
        # The original physics is active ONLY if native Foundation14 loaded
        # phase-change and solved metal enthalpy, mold energy and pressure.
        for marker in (
            "Selecting solver fluid",
            "Selecting solver solid",
            "Selecting solidificationMeltingSource with name phaseChangeSource",
            "Solving for h",
            "Solving for e",
            "Solving for p_rgh",
            "Time = 0.001s",
            "Time = 0.002s",
        ):
            require(marker in log,"missing C14 solver evidence: "+marker)
        fields=(
            "0.002/metal/T","0.002/metal/U","0.002/metal/p_rgh",
            "0.002/metal/phaseChangeSource:alpha1","0.002/mold/T"
        )
        sha={}
        for relative in fields:
            path=output/relative
            require(path.is_file(),"missing C14 native field "+relative)
            sha[relative]=digest(path)
        info["native_phase_change_model_selected"]=True
        info["native_metal_enthalpy_and_mold_internal_energy_solved"]=True
        info["native_pressure_equations_solved"]=True
        info["native_fields_sha256"]=sha
        info["native_solidification_onset_demonstrated"]=False
        info["status"]="C3D04_A_C14_FLUID_SOLID_TWO_STEP_NATIVE_SMOKE_PASS"
        info["native_solver_run"]=True
        info["foamMultiRun_log"]=result
    except Exception as exc:
        info["status"]="C3D04_A_C14_FLUID_SOLID_SMOKE_FAILED_LOG_PRESERVED"
        info["error"]=str(exc)
        raise
    finally:
        (output/REPORT).write_text(json.dumps(info,indent=2)+"\n",
                                   encoding="utf-8")
    return info


def run_full_C14_original_10s(output: Path, info: dict) -> dict:
    """Execute EXACT historical C14 10-second horizon on an isolated 3D mesh.

    No time/model/property/solver modification. A successful native solver run
    is NOT automatically a physically validated cooling/solidification curve.
    """
    original_control=(physics.C14/"system/controlDict").read_bytes()
    require((output/"system/controlDict").read_bytes()==original_control,
            "full 10s execution requires BYTE-IDENTICAL C14 controlDict")
    require(not info.get("smoke_time_only_changes",True),
            "full original C14 solver cannot run shortened smoke inputs")
    require(not info.get("native_solver_run",False),
            "full original case must be an unexecuted staged candidate")
    fields=(
        "10/metal/T","10/metal/U","10/metal/p","10/metal/p_rgh",
        "10/metal/phaseChangeSource:alpha1","10/mold/T",
    )
    try:
        result=native([environment()["foamMultiRun"],"-case",str(output)],
                      output,"log.foamMultiRun",None)
        full_log=(output/"log.foamMultiRun").read_text(encoding="utf-8")
        require(re.search(r"(?m)^\s*End\s*$",full_log) is not None,
                "full C14 native solver did not terminate with End")
        require(re.search(r"(?m)^\s*Time\s*=\s*10(?:\.0+)?s\s*$",full_log) is not None,
                "full C14 native solver did not reach exactly 10 seconds")
        for marker in (
            "Selecting solver fluid",
            "Selecting solver solid",
            "Selecting solidificationMeltingSource with name phaseChangeSource",
            "Solving for h","Solving for e","Solving for p_rgh",
        ):
            require(marker in full_log,
                    "full C14 solver omitted essential original physics "+marker)
        field_hashes={}
        for relative in fields:
            file=output/relative
            require(file.is_file() and file.stat().st_size>0,
                    "10s output missing/empty physically required field "+relative)
            field_hashes[relative]=digest(file)
        info["status"]="C3D04_A_C14_ORIGINAL_FULL_10S_NATIVE_EXECUTED_NOT_PHYSICALLY_VALIDATED"
        info["native_solver_run"]=True
        info["full_10s_original_controlDict_unchanged"]=True
        info["full_10s_fluid_solid_phase_model_selected"]=True
        info["full_10s_fields_sha256"]=field_hashes
        info["full_10s_solver_log"]=result
        info["native_solidification_onset_demonstrated"]=False
        info["energy_balance_or_numerical_independence_validated"]=False
    except Exception as exc:
        info["status"]="C3D04_A_C14_FULL_10S_NATIVE_FAILED_LOG_PRESERVED"
        info["native_solver_run"]=False
        info["error"]=str(exc)
        raise
    finally:
        (output/REPORT).write_text(
            json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return info


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--out",type=Path,default=DEST)
    choice=p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--preflight",action="store_true")
    choice.add_argument("--materialize",action="store_true")
    choice.add_argument("--smoke",action="store_true")
    choice.add_argument("--run-full",action="store_true")
    args=p.parse_args()
    try:
        if args.preflight:
            print(json.dumps({"status":"C14_V4_T02_REAL_NATIVE_PREFLIGHT_NOT_CFD",
                              "details":inspect(args.source,EXPECTED)},indent=2))
        else:
            result=stage(args.source,args.out,smoke=args.smoke)
            if args.smoke:
                result=run_smoke(args.out.expanduser().absolute(),result)
            elif args.run_full:
                result=run_full_C14_original_10s(
                    args.out.expanduser().absolute(),result)
            print(json.dumps({"status":result["status"],
                              "full_10s_C14_3D_executed":bool(args.run_full and result.get("native_solver_run")),
                              "full_10s_C14_3D_physically_validated":False,
                              "report":str(args.out/REPORT)},indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print("C3D04_A_C14_NATIVE_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
