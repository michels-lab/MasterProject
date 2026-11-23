#!/usr/bin/env python3
"""Caso B C3D-05: faithful C14 fluid+solid phase-change on accepted STEP/Gmsh HEX8.

Distinct from archived C14 T0 TWO-SOLID conduction. Uses all original 2D C14
research physics (metal fluid/enthalpy/U/p/p_rgh/solidificationMeltingSource,
mold solid/e, exterior exchange & layered contact); only geometry-required
3D mapping of mold exterior, pressure reference and metal cellZone differs.
NO made-up JMatPro/QuickCup material values, shrinkage or grid convergence.

Preflight reads only. Materialize creates an isolated native, unexecuted C14
10-second research reference; --run-full explicitly executes it, once, with
preserved original controlDict, and records actual solver evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
B = HERE.parent
ROOT = B.parents[1]
A = ROOT/"cases_3d/C3D_04_rounded_multiblock_pilot/c14_physics"
sys.path.insert(0, str(A))
import c14_source_fidelity as original
import stage_c14_3d_case_a as a
T0_B = B/"t0_conduction/scripts"
sys.path.insert(0, str(T0_B))
import run_t0_granada as bgate

SOURCE = Path.home()/"OpenFOAM/C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
DEST = Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
EXPECTED = {"metal": 92200, "mold": 178588}
PATCHES = {
    "metal": {"metalTop", "metal_to_mold"},
    "mold": {"moldOuterUnclassified", "mold_to_metal"},
}
ORIGINAL_MOLD_EXTERIORS = set(original.EXTERIOR["mold"])
REPORT = "C3D05_B_C14_FLUID_SOLID_STAGE_REPORT.json"
FIELDS_10 = (
    "10/metal/T", "10/metal/U", "10/metal/p_rgh",
    "10/metal/phaseChangeSource:alpha1", "10/mold/T",
)
FATAL = ("FOAM FATAL ERROR", "Floating point exception", "Segmentation fault",
         "Unknown patchField type", "cannot find file")


def require(ok: bool, detail: str) -> None:
    if not ok:
        raise ValueError("C3D05_B_C14_GATE_BLOCKED: " + detail)


def read_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "missing verifier "+str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(), "unsafe/missing native file "+str(path))
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024*1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def patch_names(native_boundary: Path) -> set[str]:
    """Read actual 3D Foam boundary dictionary patch names (not ParaView groups)."""
    text = native_boundary.read_text(encoding="utf-8")
    head = re.search(r"\bFoamFile\s*\{[^{}]*\}", text, re.S)
    require(head is not None, "native boundary FoamFile metadata missing")
    body = text[head.end():]
    found = re.findall(
        r"(?m)^\s*([A-Za-z][\w]*)\s*\{\s*type\s+([A-Za-z][\w]*)\s*;",
        body)
    require(found and len(found)==len(set(p for p,typ in found)),
            "ambiguous boundary patch records")
    require(set(p for p,typ in found) != {"FoamFile"}, "not real patch records")
    return {p for p, typ in found}


def native_cell_zone_state(source: Path) -> str:
    """Accept only absent/EMPTY or verified FULL original zone, never partial."""
    file=source/"constant/metal/polyMesh/cellZones"
    if not file.exists() and not file.is_symlink():
        return "ABSENT"
    require(file.is_file() and not file.is_symlink(),
            "source cellZones symlink or non-file forbidden")
    raw=file.read_text(encoding="utf-8")
    if re.search(r"(?s)\bFoamFile\s*\{[^{}]*\}",raw) is None:
        raise ValueError("source cellZones lacks OpenFOAM metadata")
    body=re.split(r"(?s)\bFoamFile\s*\{[^{}]*\}",raw,maxsplit=1)[-1]
    if re.fullmatch(r"\s*0\s*\(\s*\)\s*",body):
        return "EMPTY"
    require(a.audit_existing_zone(file,EXPECTED["metal"]),
            "real metal source has incomplete or unparseable cellZone")
    return "FULL"


def source_gate(source: Path) -> dict:
    require(source.name == SOURCE.name, "only real accepted Case B C3D05 mesh allowed")
    source = source.resolve()
    require(source.is_dir(), "accepted Case B source directory missing")
    original.verify()  # C14 source SHA + complete physical contract
    native = bgate.source_review(source)  # CAD STEP/Gmsh HEX8/checkMesh source identity
    counts = {r:a.region_cells(source,r,EXPECTED[r]) for r in EXPECTED}
    for region in ("metal","mold"):
        names = patch_names(source/"constant"/region/"polyMesh"/"boundary")
        require(names==PATCHES[region],
                f"Unexpected {region} patch topology {sorted(names)}, expected {sorted(PATCHES[region])}; NO blind patch mapping")
    for region, name in (("metal","metal_to_mold"),("mold","mold_to_metal")):
        info = bgate.load_module("case_b_reviewer_c14",B/"scripts/review_accepted_hex_mesh.py").boundary_patch(
            source/"constant"/region/"polyMesh"/"boundary", name)
        require(info["type"]=="mappedWall" and info["nFaces"]==12636,
                f"{region}: native mappedWall contact not accepted")
    zone_state=native_cell_zone_state(source)
    return {
        "C14_source_contract_passed":True,
        "Case_B_real_HEX8_acceptance":native["geometry_topology_gate_passed"],
        "source_polyMesh_SHA256_fingerprint":bgate.source_fingerprint(source),
        "nCells":{key:item["nCells"] for key,item in counts.items()},
        "region_patches":{key:sorted(PATCHES[key]) for key in PATCHES},
        "coupled_faces_each":12636,
        "metal_full_cellZone_exists":zone_state=="FULL",
        "original_metal_cell_zone_state":zone_state,
        "severe_nonorth_faces_total":1826,
    }


def map_mold_exterior(fields: dict[str,str]) -> dict[str,str]:
    """Replace identical C14 mold exterior boundaries with B's one CAD patch.

    Five exterior patch bodies in C3D04 Case A carry IDENTICAL C14 values and
    BCs. Case B has one exterior patch; no hidden default/adiabatic substitution.
    All other C14 fields/material/solvers remain byte-identical.
    """
    relative = "0/mold/T"
    source = fields[relative]
    matches = list(re.finditer(
        r"(?m)^    ([A-Za-z][\w]*)\n    \{\n(.*?)\n    \}\n",
        source, re.S))
    exterior = [(m.group(1),m.group(2),m.span()) for m in matches
                if m.group(1) in ORIGINAL_MOLD_EXTERIORS]
    require({p for p,body,span in exterior}==ORIGINAL_MOLD_EXTERIORS,
            "C14 mold exterior patch coverage changed")
    require(len({body for name,body,span in exterior})==1,
            "C14 mold exterior values differ; cannot merge 5 patches into 1")
    require("mold_to_metal" in [m.group(1) for m in matches],
            "C14 conjugate contact absent")
    body=exterior[0][1]
    new_patch="    moldOuterUnclassified\n    {\n"+body+"\n    }\n"
    start=min(x[2][0] for x in exterior)
    for name, body, span in sorted(exterior,key=lambda it:it[2][0],reverse=True):
        source=source[:span[0]]+source[span[1]:]
    source=source[:start]+new_patch+source[start:]
    require(all(not re.search(r"(?m)^\s*"+re.escape(p)+r"\s*$",source)
                for p in ORIGINAL_MOLD_EXTERIORS),
            "C14 Case A-only exterior patch survived")
    require(source.count("moldOuterUnclassified")==1
            and "type externalTemperature;" in source,
            "Case B mold exterior is not C14 externalTemperature")
    result=dict(fields)
    result[relative]=source
    return result


def files_for_real_mesh(nmetal: int, *, has_zone: bool) -> dict[str,str]:
    """Exactly original C14 physics, with B-only 3D geometry substitutions."""
    require(nmetal==EXPECTED["metal"], "wrong Case B metal cell count")
    source=original.assemble_unmaterialized_source_exact_fileset()
    files=map_mold_exterior(source)
    files["system/metal/fvSolution"]=a.three_d_pressure_solution(
        files["system/metal/fvSolution"],nmetal)
    if not has_zone:
        files["constant/metal/polyMesh/cellZones"]=a.whole_region_zone(nmetal)
    require(len(files)==22+(not has_zone),"unexpected C14 file count")
    for relative in source:
        if relative in ("system/metal/fvSolution", "0/mold/T"):
            continue
        require(files[relative]==source[relative],
                "C14 original/source-field drift outside geometry map: "+relative)
    require(files["system/controlDict"].encode("utf-8")==original.read_original(
        "system/controlDict").encode("utf-8"),
        "C14 10s/deltaT/writeInterval changed")
    require("solidificationMeltingSource;" in files["constant/metal/fvModels"],
            "C14 latent source missing")
    require("metal       fluid;" in files["system/controlDict"]
            and "mold        solid;" in files["system/controlDict"],
            "C14 original metal fluid/mold solid was replaced")
    require("heRhoThermo;" in files["constant/metal/materials/castIron"],
            "metal accidentally converted into a solid T0")
    require("externalTemperature;" in files["0/metal/T"]
            and "externalTemperature;" in files["0/mold/T"]
            and "coupledTemperature;" in files["0/metal/T"]
            and "coupledTemperature;" in files["0/mold/T"],
            "C14 contact/exterior boundaries altered")
    for relative in files:
        require("frontAndBack" not in files[relative] if relative.startswith("0/")
                else True,"2D empty patch should not exist in 3D fields")
    return files


def protect(source: Path, output: Path) -> None:
    s=source.resolve()
    o=output.absolute()
    require(o!=s and s not in o.parents and o not in s.parents,
            "source and target cannot overlap")
    require(not o.exists() and not o.is_symlink(),
            "output already exists; NO overwrite/no second solver run "+str(o))


def environment() -> None:
    require(os.environ.get("WM_PROJECT_VERSION")=="14",
            "source actual OpenFOAM Foundation14 first")
    for tool in ("foamDictionary","foamMultiRun"):
        require(shutil.which(tool) is not None, "Foundation14 "+tool+" unavailable")


def save_report(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc,indent=2,ensure_ascii=False,sort_keys=True)+"\n",
                    encoding="utf-8")


def stage(source: Path, output: Path) -> dict:
    source=source.expanduser().resolve()
    output=output.expanduser().absolute()
    protect(source,output)
    environment()
    gate=source_gate(source)
    files=files_for_real_mesh(EXPECTED["metal"],has_zone=gate["metal_full_cellZone_exists"])
    output.parent.mkdir(parents=True,exist_ok=True)
    require(not output.parent.is_symlink(),"unsafe output parent")
    candidate=Path(tempfile.mkdtemp(prefix="."+output.name+".staging.",dir=output.parent))
    # Failure leaves an isolated candidate and native parser logs, never edits originals.
    try:
        source_hashes={}
        for region in ("metal","mold"):
            mesh=Path("constant")/region/"polyMesh"
            shutil.copytree(source/mesh,candidate/mesh,symlinks=False)
            for name in a.MESH:
                rel=mesh/name
                h=sha256(source/rel)
                require(sha256(candidate/rel)==h,"copied HEX8 native mesh differs: "+str(rel))
                source_hashes[str(rel)]=h
        for rel,body in files.items():
            file=candidate/rel
            file.parent.mkdir(parents=True,exist_ok=True)
            if rel=="constant/metal/polyMesh/cellZones" and file.exists():
                require(gate["original_metal_cell_zone_state"]=="EMPTY",
                        "cannot replace any nonempty cellZone even in isolated copy")
                require(not file.is_symlink(),"cannot replace a linked cellZone")
                source_hashes["source_empty_metal_cellZones"]=sha256(source/rel)
                file.unlink()  # candidate ONLY; the original source remains immutable
            require(not file.exists(),"C14 files collide with source cellZones: "+rel)
            with file.open("x",encoding="utf-8",newline="") as stream:
                stream.write(body)
        parsers={}
        for rel in sorted(files):
            if rel.endswith("/cellZones"):
                continue
            log=candidate/("log.foamDictionary."+rel.replace("/","_"))
            with log.open("x",encoding="utf-8") as fp:
                result=subprocess.run(["foamDictionary",str(candidate/rel)],
                                      cwd=candidate,stdout=fp,stderr=subprocess.STDOUT,
                                      check=False)
            require(result.returncode==0,
                    "Foundation14 failed to parse "+rel+" (preserved in "+str(log)+")")
            parsers[rel]=sha256(log)
        result={
            "schema":"C3D05_B_C14_EXACT_SOURCE_3D_V1",
            "status":"C3D05_B_C14_FLUID_SOLID_STAGED_F14_NOT_EXECUTED",
            "source_real_accepted_C3D05_HEX8":str(source),
            "source_fingerprint":gate["source_polyMesh_SHA256_fingerprint"],
            "geometry_gate":gate,
            "five_native_mesh_files_per_region_SHA256":source_hashes,
            "native_foundation14_dicts_parsed_sha256":parsers,
            "source_C14_3D_only_adaptations":[
                "mold exterior five equivalent C14 thermal BC patches -> moldOuterUnclassified",
                "2D pRefPoint -> validated pRefCell 0 in real 92,200-cell metal region",
                "create full 92,200-cell metal cellZone on isolated copy if original lacks it"
            ],
            "original_C14_controlDict_sha256":sha256(candidate/"system/controlDict"),
            "original_C14_controlDict_unchanged":True,
            "original_C14_phase_model":"solidificationMeltingSource (all real metal cells)",
            "metal_thermo":"heRhoThermo/hConst/sensibleEnthalpy (fluid)",
            "mold_thermo":"heSolidThermo/eConst/sensibleInternalEnergy (solid)",
            "Cp_to_Cv_substitution":False,
            "same_C14_2D_physics_not_JMatPro_or_QuickCup":True,
            "native_solver_run":False,"solidification_observed":False,
            "energy_balance_validated":False,"grid_independence_validated":False,
            "experimentally_validated":False,"contraction_model_activated":False,
            "output":str(output)
        }
        save_report(candidate/REPORT,result)
        protect(source,output)
        os.rename(candidate,output)
        return result
    except Exception:
        print("C3D05_B_C14_STAGE_PRESERVED_FOR_DIAGNOSTICS:",candidate,
              file=sys.stderr)
        raise


def run_full(output: Path, report: dict) -> dict:
    """One and only original-source C14 10-second research reference execution."""
    log=output/"log.foamMultiRun.C3D05_B_C14_10S"
    require(not log.exists() and not log.is_symlink(),"solver log exists: never rerun")
    require(not any((output/t).exists() for t in ("0.1","1","10")),
            "solver time output already exists: refuse rerun")
    require(sha256(output/"system/controlDict")==report["original_C14_controlDict_sha256"],
            "original C14 native 10 s control has changed")
    require((output/"system/controlDict").read_bytes()==(original.C14/"system/controlDict").read_bytes(),
            "original C14 10-second control not byte-identical")
    try:
        with log.open("x",encoding="utf-8") as stream:
            cp=subprocess.run(["foamMultiRun","-case",str(output)],cwd=output,
                              stdout=stream,stderr=subprocess.STDOUT,check=False)
        require(cp.returncode==0,"foamMultiRun returned "+str(cp.returncode))
        seen={"End":False,"Time10":False,
              "fluid":False,"solid":False,"phase":False,
              "h":False,"e":False,"p_rgh":False}
        with log.open(encoding="utf-8",errors="replace") as inp:
            for line in inp:
                if re.fullmatch(r"\s*End\s*",line): seen["End"]=True
                if re.fullmatch(r"\s*Time\s*=\s*10(?:\.0+)?s\s*",line):seen["Time10"]=True
                for key,marker in (
                    ("fluid","Selecting solver fluid"),
                    ("solid","Selecting solver solid"),
                    ("phase","Selecting solidificationMeltingSource with name phaseChangeSource"),
                    ("h","Solving for h"),("e","Solving for e"),("p_rgh","Solving for p_rgh"),
                ):
                    if marker in line: seen[key]=True
                require(not any(item in line for item in FATAL),
                        "native solver log contains fatal marker: "+line.strip())
        require(all(seen.values()),"native C14 model, 10s or field evidence absent: "+str(seen))
        field_hashes={rel:sha256(output/rel) for rel in FIELDS_10}
        report["status"]="C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED"
        report["native_solver_run"]=True
        report["original_C14_endTime_s"]=10
        report["original_C14_deltaT_s"]=0.001
        report["source_C14_model_selected"]=seen
        report["solver_log_sha256"]=sha256(log)
        report["final_10s_native_fields_sha256"]=field_hashes
        report["solidification_observed"]=False  # requires postrun alpha1 timeline, not mere field existence
        return report
    except Exception as exc:
        report["status"]="C3D05_B_C14_NATIVE_RUN_FAILED_PRESERVED_NO_AUTOMATIC_RERUN"
        report["native_solver_run"]=False
        report["failure_reason"]=str(exc)
        raise
    finally:
        save_report(output/REPORT,report)


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,default=SOURCE)
    ap.add_argument("--out",type=Path,default=DEST)
    select=ap.add_mutually_exclusive_group(required=True)
    select.add_argument("--preflight",action="store_true")
    select.add_argument("--materialize",action="store_true")
    select.add_argument("--run-full",action="store_true")
    args=ap.parse_args()
    try:
        if args.preflight:
            print(json.dumps({
                "status":"C3D05_B_C14_NATIVE_3D_PREFLIGHT_NOT_EXECUTED",
                "geometry":source_gate(args.source.expanduser()),
                "C14_3D_input_files_count":len(files_for_real_mesh(EXPECTED["metal"],has_zone=False)),
            },indent=2))
            return 0
        result=stage(args.source,args.out)
        if args.run_full:
            result=run_full(args.out.expanduser().absolute(),result)
        print(json.dumps({
            "status":result["status"],"stage_report":str(args.out/REPORT),
            "native_C14_F14_solver_run":result["native_solver_run"],
            "solidification_or_experiment_accepted":False,
        },indent=2))
        return 0
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as exc:
        print("C3D05_B_C14_NATIVE_BLOCKED:",str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
