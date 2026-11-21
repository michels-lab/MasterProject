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
    declared, body = gate.payload(path)
    labels = [int(x) for x in body.split()]
    require(declared == len(labels) and all(n >= 0 for n in labels),
            "polyMesh ASCII labels invalid: "+str(path))
    return declared, max(labels, default=-1)


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


def input_files(n: int, *, smoke: bool, existing_zone: bool=False) -> dict[str,str]:
    files = physics.assemble_unmaterialized_source_exact_fileset()
    files["system/metal/fvSolution"] = three_d_pressure_solution(
        files["system/metal/fvSolution"],n)
    if not existing_zone:
        files["constant/metal/polyMesh/cellZones"] = whole_region_zone(n)
    if smoke:
        files["system/controlDict"] = smoke_control(files["system/controlDict"])
    for relative in ("constant/metal/materials/castIron",
                     "constant/mold/materials/silica",
                     "constant/metal/fvModels",
                     "constant/metal/momentumTransport"):
        require(files[relative]==physics.read_original(relative),
                "physical C14 source altered "+relative)
    require("metal       fluid;" in files["system/controlDict"]
            and "mold        solid;" in files["system/controlDict"],
            "C14 model cannot be replaced by two solids")
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
        for reg in ("metal","mold"):
            require((output/"0.002"/reg/"T").is_file(),
                    "missing native final region field T: "+reg)
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


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    p.add_argument("--out",type=Path,default=DEST)
    choice=p.add_mutually_exclusive_group(required=True)
    choice.add_argument("--preflight",action="store_true")
    choice.add_argument("--materialize",action="store_true")
    choice.add_argument("--smoke",action="store_true")
    args=p.parse_args()
    try:
        if args.preflight:
            print(json.dumps({"status":"C14_V4_T02_REAL_NATIVE_PREFLIGHT_NOT_CFD",
                              "details":inspect(args.source,EXPECTED)},indent=2))
        else:
            result=stage(args.source,args.out,smoke=args.smoke)
            if args.smoke:
                result=run_smoke(args.out.expanduser().absolute(),result)
            print(json.dumps({"status":result["status"],
                              "full_10s_C14_3D_validated":False,
                              "report":str(args.out/REPORT)},indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
        print("C3D04_A_C14_NATIVE_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
