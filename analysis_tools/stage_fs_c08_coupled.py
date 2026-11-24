#!/usr/bin/env python3
"""Stage a genuinely coupled FS-C08 OpenFOAM14 case, without running CFD.

Copies ONLY the accepted FS-C07 t=0 inputs, meshes and control files into
an independent new FS_C08_COUPLED_* directory. Requires the user's explicit
composition-specific thermo dictionary; never creates fabricated JMatPro.
Replaces inherited VoFSolidificationMelting to avoid double latent heating.
No physical validation or WSL compile is claimed by staging.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/"freesurface/FS-C06_vof_solidification/native/constant/fluid/fvModels"
BASE_MODULE=ROOT/"freesurface/FS-C08_conservative_phase_mass/coupled_solver/native"
REQUIRED_MATERIAL=(
    "materialId", "propertySource","Tmin_K","Tmax_K",
    "phaseRelaxation","metalPresenceThreshold","rhoLiquidT",
    "rhoSolidT","solidMassFractionT","latentHeat","cpSolid",
)


def require(flag: bool, why: str) -> None:
    if not flag:
        raise ValueError("FS-C08 COUPLED STAGING BLOCKED: "+why)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(source: Path, material: Path, output: Path) -> dict:
    source=source.expanduser().resolve()
    material=material.expanduser().resolve()
    output=output.expanduser().absolute()
    require(source.is_dir() and source.name.startswith("FS_C07_THERMAL_"),
            "requires preserved, accepted FS-C07 native input source")
    require(source!=ROOT and ROOT not in source.parents,
            "source cannot be Git worktree")
    require(not output.exists() and not output.is_symlink(),
            "destination already exists; never overwrite a CFD run")
    require(source!=output and source not in output.parents
            and output not in source.parents,"source/output overlap")
    require(output!=ROOT and ROOT not in output.parents,
            "new CFD case must be outside Git checkout")
    require(output.name.startswith("FS_C08_COUPLED_"),
            "destination must begin FS_C08_COUPLED_")
    for relative in (
        "0/fluid/alpha.metal", "constant/fluid/polyMesh/points",
        "constant/fluid/fvModels", "system/controlDict",
        "system/fluid/fvSolution", "system/fluid/fvSchemes",
    ):
        require((source/relative).is_file(),"missing "+relative)
    require((source/"0/fluid/T.metal").is_file()
            or (source/"0/fluid/T").is_file(),
            "native fluid initial metal temperature missing")
    require((source/"constant/fluid/fvModels").read_bytes()==MODEL.read_bytes(),
            "FS-C07 fvModels drifted; refuse to mutate unknown physics")
    require(material.is_file() and material != source,
            "sourced alloy property dictionary must exist outside case")
    mt=material.read_text(encoding="utf-8")
    for key in REQUIRED_MATERIAL:
        require(re.search(r"(?m)^\s*"+re.escape(key)+r"\s+",mt) is not None,
                "mandatory physical property entry absent: "+key)
    require("SYNTHETIC_ONLY_NOT_JMATPRO" not in mt
            and "PLACEHOLDER" not in mt and "TODO" not in mt
            and re.search(r"<[A-Z][^>]*>",mt) is None,
            "no synthetic or unfilled material properties allowed")
    ctrl=(source/"system/controlDict").read_text(encoding="utf-8")
    old=r"(?m)^(\s*fluid\s+)compressibleVoF(\s*;)"
    require(len(re.findall(old,ctrl))==1,
            "expected exact fluid compressibleVoF region solver")
    require("libfsC08ConservativeVoF" not in ctrl,
            "original C07 already contains an FS-C08 solver")
    ctrl=re.sub(old,r"\1fsC08ConservativeVoF\2",ctrl,count=1)
    ctrl=ctrl.replace("regionSolvers",
        'libs ("libfsC08ConservativeVoF.so");\n\nregionSolvers',1)

    originalModels=MODEL.read_text(encoding="utf-8")
    marker="/* FS-C06 numerical Foundation14 COMPATIBILITY candidate only."
    require(marker in originalModels and "FS_C06_vof_phase_change" in originalModels,
            "inherited latent source layout changed; refuse blind deletion")
    newModels=originalModels.split(marker,1)[0]
    require("turbulenceDamping" in newModels
            and "VoFTurbulenceDamping" in newModels
            and "VoFSolidificationMelting" not in newModels,
            "retained turbulence damping or removed old latent source incorrectly")
    newModels += (
        "\n// FS-C08: old alphaSolidT/VoFSolidificationMelting REMOVED.\n"
        "// Native coupled solver owns phase-mass Gamma and SINGLE Gamma*L.\n"
    )
    solution=(source/"system/fluid/fvSolution").read_text(encoding="utf-8")
    require(re.search(r"(?m)^\s*solvers\s*\{",solution) is not None,
            "no solvers dictionary in fluid fvSolution")
    require("rhoAlpha.liquid" not in solution and "rhoAlpha.solid" not in solution,
            "source already has FS-C08 phase mass matrix entries")
    solution=re.sub(
        r"(?m)^(\s*solvers\s*\{)",
        lambda m:m.group(1)+(
            '\n    "rhoAlpha.(liquid|solid)"\n'
            '    {\n'
            '        solver          PBiCGStab;\n'
            '        preconditioner  DILU;\n'
            '        tolerance       1e-10;\n'
            '        relTol          0.01;\n'
            '    }\n'
        ),solution,count=1
    )
    for need in (
        "FS_C08_PhaseMassTransport.C",
        "fsC08ConservativeVoF.C",
        "fsC08PressureCorrector.C",
        "fsC08ThermophysicalPredictor.C",
        "Make/files","Make/options",
    ):
        require((BASE_MODULE/need).is_file(),"native solver source missing "+need)

    tracked=["0/fluid/alpha.metal","constant/fluid/fvModels","system/controlDict"]
    sourceSHA={k:sha(source/k) for k in tracked}
    output.mkdir(parents=True,exist_ok=False)
    for name in ("0","constant","system"):
        shutil.copytree(source/name,output/name,symlinks=False)
    (output/"system/controlDict").write_text(ctrl,encoding="utf-8")
    (output/"constant/fluid/fvModels").write_text(newModels,encoding="utf-8")
    (output/"system/fluid/fvSolution").write_text(solution,encoding="utf-8")
    shutil.copy2(material,output/"constant/fluid/fsC08Material")
    # An old legacy solid field must NOT be misinterpreted as rhoAlpha.solid.
    legacy=output/"0/fluid/alpha.metal.solid"
    if legacy.is_file():
        legacy.unlink()
    report={
        "schema":"masterproject-fs-c08-coupled-stage-v1",
        "status":"FS_C08_REAL_CFD_INPUTS_STAGED__PHYSICS_UNVERIFIED_NO_CFD",
        "source_FS_C07":str(source),
        "case":str(output),
        "model_library":"libfsC08ConservativeVoF.so",
        "sourced_material_file":str(material),
        "sourced_material_SHA256":sha(material),
        "original_source_sha256_before":sourceSHA,
        "original_source_sha256_after":{k:sha(source/k) for k in tracked},
        "material_values_fabricated":False,
        "previous_VoFSolidificationMelting_removed":True,
        "turbulenceDamping_retained":True,
        "native_CFDSolver_compilation_verified":False,
        "native_CFD_executed":False,
        "physical_shrinkage_validated":False,
        "experimental_validation":False,
    }
    require(report["original_source_sha256_before"]==
            report["original_source_sha256_after"],
            "original FS-C07 source changed; stop")
    (output/"FS_C08_COUPLED_STAGE_REPORT.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",required=True,type=Path)
    ap.add_argument("--material",required=True,type=Path)
    ap.add_argument("--destination",type=Path,default=None)
    args=ap.parse_args(argv)
    output=args.destination or (
        Path.home()/"OpenFOAM"/"FS_C08_COUPLED_RUNS"/
        ("FS_C08_COUPLED_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
         +"_"+secrets.token_hex(4))
    )
    try:
        report=stage(args.source,args.material,output)
        print(json.dumps(report,indent=2))
        return 0
    except (ValueError,OSError) as e:
        print(str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
