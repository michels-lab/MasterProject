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
import math
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
    "phaseChangeClosure","mushyDarcyCu","mushyDarcyQ","rhoLiquidT",
    "rhoSolidT","solidMassFractionT","latentHeat",
    "energyReferenceT_K","cvLiquidT","cvSolidT",
    "kappaLiquidT","kappaSolidT",
)


def require(flag: bool, why: str) -> None:
    if not flag:
        raise ValueError("FS-C08 COUPLED STAGING BLOCKED: "+why)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_phase_mass_solvers(solution: str) -> str:
    """Install regular/final phase-mass and mixture-temperature solvers.

    The mass matrix is diagonal (implicit ddt, explicit face flux).
    The new energy matrix is symmetric: implicit Sp and scalar diffusion,
    with energy advection on the RHS. DILU is not a symmetric preconditioner.
    Preserve inherited pressure/momentum and other solver dictionaries.
    """
    pattern = r"(?m)^(\s*solvers\s*\{)"
    require(len(re.findall(pattern, solution)) == 1,
            "expected exactly one solvers dictionary in fluid fvSolution")
    require("rhoAlpha." not in solution,
            "source already has FS-C08 phase mass matrix entries")

    # Remove existing literal T/TFinal blocks, if any. Explicit new keys
    # also take precedence over inherited regex entries such as "T.*".
    # Refuse unexpectedly nested blocks instead of partially editing them.
    exact_T = re.compile(r'(?m)^[ \t]*(?:"T(?:Final)?"|T(?:Final)?)[ \t\r\n]*\{')
    while True:
        match = exact_T.search(solution)
        if match is None:
            break
        end = solution.find("}", match.end())
        require(end != -1 and "{" not in solution[match.end():end],
                "unexpected nested/unterminated literal T solver block")
        solution = solution[:match.start()] + solution[end+1:]

    entries = []
    for field in ("rhoAlpha.liquid", "rhoAlpha.solid", "T", "pVolumeCorrection.fsC08"):
        for final in (False, True):
            name = field + ("Final" if final else "")
            # Current mass equation is diagonal; diagonal is a valid
            # preconditioner for both matrix classes. Temperature uses
            # PCG/DIC for its symmetric diffusion-plus-diagonal operator.
            solver = "PCG" if field == "T" else "PBiCGStab"
            preconditioner = "DIC" if field == "T" else "diagonal"
            rel_tol = 0 if final or field in ("T", "pVolumeCorrection.fsC08") else 0.01
            entries.append(
                f"\n    {name}\n"
                "    {\n"
                f"        solver          {solver};\n"
                f"        preconditioner  {preconditioner};\n"
                "        tolerance       1e-10;\n"
                f"        relTol          {rel_tol};\n"
                "    }\n"
            )
    return re.sub(pattern, lambda m: m.group(1) + "".join(entries),
                  solution, count=1)


def laminar_reference_models(momentum: str, models: str) -> tuple[str, str]:
    """Explicit isolated molecular-transport reference; never alter source."""
    pattern = r"(?m)^(\s*simulationType\s+)(RAS|laminar)(\s*;)"
    require(len(re.findall(pattern, momentum)) == 1,
            "laminar reference requires explicit mixture RAS or laminar transport")
    momentum = re.sub(pattern, r"\g<1>laminar\g<3>", momentum, count=1)
    damping = r"(?ms)^\s*turbulenceDamping\s*\{[^{}]*\}\s*"
    require(len(re.findall(damping, models)) == 1,
            "expected one known turbulenceDamping block")
    models = re.sub(damping, "\n", models, count=1)
    models += ("\n// FS-C08 controlled laminar reference: native nut=0; "
               "VoFTurbulenceDamping not applicable.\n")
    return momentum, models


def startup_probe_controls(ctrl: str, dt: float, steps: int = 1) -> str:
    """A bounded sequence of real fixed-duration CFD steps, not a full casting simulation.

    A probe is an explicit numerical sensitivity experiment. It preserves
    the original maximum timestep and all material and pressure bounds.
    """
    require(math.isfinite(dt) and dt > 0, "invalid startup probe dt")
    require(isinstance(steps, int) and 1 <= steps <= 1000,
            "startup probe steps must be in [1,1000]")
    end = steps*dt
    require(math.isfinite(end) and end > 0, "invalid probe horizon")
    original_end = re.findall(r"(?m)^\s*endTime\s+([0-9.eE+-]+)\s*;", ctrl)
    require(len(original_end)==1 and end <= float(original_end[0]),
            "startup probe exceeds source horizon")
    number = r"[0-9]+(?:\.[0-9]*)?(?:[eE][+-]?[0-9]+)?"
    cap = re.findall(r"(?m)^\s*maxDeltaT\s+("+number+r")\s*;", ctrl)
    require(len(cap) == 1 and dt <= float(cap[0]),
            "startup probe dt exceeds original maxDeltaT or cap is ambiguous")
    require(len(re.findall(r"(?m)^\s*startTime\s+0(?:\.0*)?\s*;",ctrl))==1,
            "startup probe requires original startTime 0")
    replacements = {"startFrom": "startTime", "stopAt": "endTime",
                    "deltaT": format(dt, ".16g"), "endTime": format(end, ".15g"),
                    "adjustTimeStep": "no", "writeControl": "timeStep",
                    "writeInterval": "1"}
    for key, value in replacements.items():
        pattern = r"(?m)^([ \t]*"+re.escape(key)+r"\s+)[^;\n]+;"
        require(len(re.findall(pattern,ctrl))==1,
                "ambiguous startup probe control: "+key)
        ctrl=re.sub(pattern,lambda m: m.group(1)+value+";",ctrl,count=1)
    # Retain every positive-time output for independent per-step auditing.
    purge = r"(?m)^([ \t]*purgeWrite\s+)[^;\n]+;"
    require(len(re.findall(purge, ctrl))<=1, "ambiguous purgeWrite")
    ctrl = re.sub(purge, lambda m: m.group(1)+"0;", ctrl)
    return ctrl


def stage(source: Path, material: Path, output: Path,
          laminar_reference: bool = False,
          startup_probe_dt: float | None = None,
          startup_probe_steps: int = 1,
          momentum_face_mobility: str = "linear",
          momentum_matrix_coupling: str = "legacy",
          phase_pressure_mobility: str = "separate",
          momentum_flux_mode: str = "incremental",
          energy_donor_mode: str = "legacy",
          pressure_transport_support: str = "trial",
          metal_bulk_modulus_pa: float = 0.0,
          energy_linear_tolerance: float = 0.0) -> dict:
    require(math.isfinite(energy_linear_tolerance) and 0<=energy_linear_tolerance<=1,
            "invalid energy linear tolerance")
    require(energy_linear_tolerance==0 or
            (metal_bulk_modulus_pa>0 and laminar_reference and startup_probe_dt is not None),
            "residual-controlled energy is restricted to finite-K fixed-step probes")
    require(math.isfinite(metal_bulk_modulus_pa) and metal_bulk_modulus_pa>=0,
            "invalid metal bulk modulus")
    require(metal_bulk_modulus_pa==0 or
            (laminar_reference and startup_probe_dt is not None and momentum_face_mobility=="linear"
             and momentum_matrix_coupling=="refreshBeforePressure" and phase_pressure_mobility=="separate"
             and momentum_flux_mode=="incremental" and energy_donor_mode=="legacy"
             and pressure_transport_support=="trial"),
            "finite K restricted to the controlled reference startup probe")
    require(pressure_transport_support in ("trial","oldLiquid","oldGas","oldBoth"),
            "unknown pressure transport support")
    require(pressure_transport_support=="trial" or
            (laminar_reference and startup_probe_dt is not None and momentum_face_mobility=="linear"
             and phase_pressure_mobility=="separate" and momentum_flux_mode=="incremental"
             and energy_donor_mode=="legacy"),
            "old-time support requires reference fixed-step laminar probe")
    require(energy_donor_mode in ("legacy","oldGas","currentLiquid","oldGasCurrentLiquid"),
            "unknown energy donor mode")
    require(energy_donor_mode=="legacy" or
            (laminar_reference and startup_probe_dt is not None and momentum_face_mobility=="linear"
             and phase_pressure_mobility=="separate" and momentum_flux_mode=="incremental"),
            "energy donor alternatives require reference flux fixed-step laminar probe")
    require(momentum_flux_mode in ("incremental","totalUpwind","incrementalNoDdtCorr","totalUpwindNoDdtCorr"),
            "unknown momentum flux mode")
    require(momentum_flux_mode=="incremental" or
            (laminar_reference and startup_probe_dt is not None and momentum_face_mobility=="linear"
             and phase_pressure_mobility=="separate"),
            "flux alternatives require linear separate laminar fixed-step probe")
    require(phase_pressure_mobility in ("separate","phaseWeighted"),
            "unknown phase pressure mobility")
    require(phase_pressure_mobility=="separate" or
            (laminar_reference and startup_probe_dt is not None and momentum_face_mobility=="linear"),
            "phaseWeighted requires a controlled linear laminar fixed-dt probe")
    require(momentum_matrix_coupling in ("legacy","refreshBeforePressure"),
            "unknown momentum matrix coupling")
    require(momentum_matrix_coupling=="legacy" or
            (laminar_reference and startup_probe_dt is not None and momentum_face_mobility=="linear"),
            "matrix refresh requires a controlled linear laminar fixed-dt probe")
    require(momentum_face_mobility in ("linear","harmonic"),
            "unknown momentum face mobility")
    require(momentum_face_mobility=="linear" or (laminar_reference and startup_probe_dt is not None),
            "harmonic mobility is restricted to controlled laminar startup probes")
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
    require("experimentalBulkModulusPa" not in mt,"supply unmodified reference material; K is staged explicitly")
    for key in REQUIRED_MATERIAL:
        require(re.search(r"(?m)^\s*"+re.escape(key)+r"\s+",mt) is not None,
                "mandatory physical property entry absent: "+key)
    require("SYNTHETIC_ONLY_NOT_JMATPRO" not in mt
            and "PLACEHOLDER" not in mt and "TODO" not in mt
            and re.search(r"<[A-Z][^>]*>",mt) is None,
            "no synthetic or unfilled material properties allowed")
    # No numerical interface cutoff may hide positive metal mass.
    # All positive metal inventories need sourced phase properties.
    require("metalPresenceThreshold" not in mt,
            "metalPresenceThreshold would discard trace-metal physics; "
            "remove it and extend material curves to actual interface T")

    # Explicit physical closure, never an arbitrary per-step gamma multiplier.
    closure_matches=re.findall(
        r"(?m)^\s*phaseChangeClosure\s+(equilibrium|kineticRelaxation)\s*;",
        mt
    )
    require(len(closure_matches)==1,
            "phaseChangeClosure must be exactly equilibrium or "
            "kineticRelaxation")
    # Reject old effective-Cv-only input before staging real CFD.
    require("cvSolid [" not in mt,
            "old constant cvSolid is not a phase-resolved u(T) curve")

    if closure_matches[0]=="kineticRelaxation":
        require(re.search(r"(?m)^\s*tauPhaseChangeT\s+",mt) is not None,
                "kineticRelaxation requires sourced tauPhaseChangeT(T) [s]")

    ctrl=(source/"system/controlDict").read_text(encoding="utf-8")
    old=r"(?m)^(\s*fluid\s+)compressibleVoF(\s*;)"
    require(len(re.findall(old,ctrl))==1,
            "expected exact fluid compressibleVoF region solver")
    require("libfsC08ConservativeVoF" not in ctrl,
            "original C07 already contains an FS-C08 solver")
    ctrl=re.sub(old,r"\1fsC08ConservativeVoF\2",ctrl,count=1)
    ctrl=ctrl.replace("regionSolvers",
        'libs ("libfsC08ConservativeVoF.so");\n\nregionSolvers',1)

    require(startup_probe_dt is not None or startup_probe_steps == 1,
            "startup probe steps require an explicit dt")
    if startup_probe_dt is not None:
        require(laminar_reference, "startup probes require explicit laminar reference")
        ctrl=startup_probe_controls(ctrl,startup_probe_dt,startup_probe_steps)

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
        "// Phase energy contains latent only in u_liquid-u_solid reference.\n"
    )
    momentum_reference = None
    if laminar_reference:
        momentum_file = source/"constant/fluid/momentumTransport"
        require(momentum_file.is_file(), "missing explicit fluid momentumTransport")
        momentum_reference, newModels = laminar_reference_models(
            momentum_file.read_text(encoding="utf-8"), newModels
        )
    solution=(source/"system/fluid/fvSolution").read_text(encoding="utf-8")
    solution=add_phase_mass_solvers(solution)
    schemes=(source/"system/fluid/fvSchemes").read_text(encoding="utf-8")
    projection_scheme = (
        '    laplacian(fsC08VolumeMobility,pVolumeCorrection.fsC08) '
        'Gauss linear orthogonal;\n'
    )
    scheme_pattern = r"(?m)^(\s*laplacianSchemes\s*\{)"
    require(len(re.findall(scheme_pattern, schemes)) == 1,
            "expected one fluid laplacianSchemes block")
    require("fsC08VolumeMobility" not in schemes,
            "source already has experimental pressure projection scheme")
    schemes=re.sub(scheme_pattern,
        lambda m: m.group(1)+"\n"+projection_scheme,schemes,count=1)
    for need in (
        "FS_C08_VolumeProjection.C",
        "FS_C08_VolumeProjection.H",
        "FS_C08_PhaseMassTransport.C",
        "fsC08ConservativeVoF.C",
        "fsC08MushyMomentum.C",
        "fsC08PressureCorrector.C",
        "fsC08ThermophysicalPredictor.C",
        "Make/files","Make/options",
    ):
        require((BASE_MODULE/need).is_file(),"native solver source missing "+need)

    tracked=["0/fluid/alpha.metal","constant/fluid/fvModels","system/controlDict"]
    if laminar_reference:
        tracked.append("constant/fluid/momentumTransport")
    sourceSHA={k:sha(source/k) for k in tracked}
    output.mkdir(parents=True,exist_ok=False)
    for name in ("0","constant","system"):
        shutil.copytree(source/name,output/name,symlinks=False)
    (output/"system/controlDict").write_text(ctrl,encoding="utf-8")
    (output/"constant/fluid/fvModels").write_text(newModels,encoding="utf-8")
    if momentum_reference is not None:
        (output/"constant/fluid/momentumTransport").write_text(
            momentum_reference, encoding="utf-8")
    (output/"system/fluid/fvSolution").write_text(solution,encoding="utf-8")
    (output/"system/fluid/fvSchemes").write_text(schemes,encoding="utf-8")
    (output/"constant/fluid/fsC08Numerics").write_text(
        "FoamFile\n{\n    format ascii;\n    class dictionary;\n"
        "    object fsC08Numerics;\n}\n"
        f"momentumFaceMobility {momentum_face_mobility};\n"
        f"momentumMatrixCoupling {momentum_matrix_coupling};\n"
        f"phasePressureMobility {phase_pressure_mobility};\n"
        f"momentumFluxMode {momentum_flux_mode};\n"
        f"energyDonorMode {energy_donor_mode};\n"
        f"pressureTransportSupport {pressure_transport_support};\n"
        f"energyLinearTolerance {energy_linear_tolerance:.16g};\n",
        encoding="utf-8")
    staged_material=output/"constant/fluid/fsC08Material"
    shutil.copy2(material,staged_material)
    if metal_bulk_modulus_pa>0:
        with staged_material.open("a",encoding="utf-8") as fp:
            fp.write(f"\n// Experimental pure-Fe sensitivity; not calibrated alloy EOS.\nexperimentalBulkModulusPa {metal_bulk_modulus_pa:.16g};\n")
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
        "turbulenceDamping_retained":not laminar_reference,
        "transport_reference":"laminar_molecular" if laminar_reference else "inherited_RAS",
        "laminar_reference_is_controlled_experiment":laminar_reference,
        "momentum_face_mobility":momentum_face_mobility,
        "momentum_matrix_coupling":momentum_matrix_coupling,
        "phase_pressure_mobility":phase_pressure_mobility,
        "momentum_flux_mode":momentum_flux_mode,
        "energy_donor_mode":energy_donor_mode,
        "pressure_transport_support":pressure_transport_support,
        "metal_bulk_modulus_pa":metal_bulk_modulus_pa,
        "energy_linear_tolerance":energy_linear_tolerance,
        "staged_material_SHA256":sha(staged_material),
        "caloric_pressure_dependence_validated":False,
        "startup_probe_dt_s":startup_probe_dt,
        "startup_probe_steps":startup_probe_steps if startup_probe_dt is not None else None,
        "startup_probe_only":startup_probe_dt is not None,
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
    ap.add_argument("--laminar-reference", action="store_true",
                    help="Isolated molecular transport reference, not calibrated RAS")
    ap.add_argument("--startup-probe-dt",type=float,
                    help="One fixed real CFD step, numerical sensitivity only")
    ap.add_argument("--startup-probe-steps",type=int,default=1)
    ap.add_argument("--momentum-face-mobility",choices=("linear","harmonic"),default="linear")
    ap.add_argument("--momentum-matrix-coupling",choices=("legacy","refreshBeforePressure"),default="legacy")
    ap.add_argument("--phase-pressure-mobility",choices=("separate","phaseWeighted"),default="separate")
    ap.add_argument("--momentum-flux-mode",choices=("incremental","totalUpwind","incrementalNoDdtCorr","totalUpwindNoDdtCorr"),default="incremental")
    ap.add_argument("--energy-donor-mode",choices=("legacy","oldGas","currentLiquid","oldGasCurrentLiquid"),default="legacy")
    ap.add_argument("--pressure-transport-support",choices=("trial","oldLiquid","oldGas","oldBoth"),default="trial")
    ap.add_argument("--metal-bulk-modulus-pa",type=float,default=0.0)
    ap.add_argument("--energy-linear-tolerance",type=float,default=0.0)
    args=ap.parse_args(argv)
    output=args.destination or (
        Path.home()/"OpenFOAM"/"FS_C08_COUPLED_RUNS"/
        ("FS_C08_COUPLED_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
         +"_"+secrets.token_hex(4))
    )
    try:
        report=stage(args.source,args.material,output,args.laminar_reference,
                     args.startup_probe_dt,args.startup_probe_steps,args.momentum_face_mobility,args.momentum_matrix_coupling,args.phase_pressure_mobility,args.momentum_flux_mode,args.energy_donor_mode,args.pressure_transport_support,args.metal_bulk_modulus_pa,args.energy_linear_tolerance)
        print(json.dumps(report,indent=2))
        return 0
    except (ValueError,OSError) as e:
        print(str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
