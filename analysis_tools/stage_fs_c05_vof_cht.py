#!/usr/bin/env python3
"""FS-C05: stage a PROVISIONAL 3-D compressibleVoF+solid CHT solver case.

Source: local, INSTALLED OpenFOAM Foundation 14 tutorial
  $FOAM_TUTORIALS/multiRegion/CHT/VoFcoolingCylinder2D
The tutorial proves modular solver architecture: foamMultiRun with
'fluid compressibleVoF; mold solid;'.

Read-only source: accepted FS-C04 initial T/alpha/mapped-wall case. A
NEW output directory is mandatory. No FOAM utility is launched. The
stage may be syntactically plausible but remains UNTESTED ON THIS MESH
until an independent Foundation14 smoke and CHT energy audit succeeds.

Parameters are PROVISIONAL iron/air/sand screening values, NOT measured
JMatPro temperature-dependent properties, solidification or shrinkage.
Contrary to tutorial's laminar model, uses the previous FS-C01 RAS
kEpsilon + VoFTurbulenceDamping WITHOUT pretending calibration.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from audit_fs_c02_local import read_alpha
from audit_fs_c04_split_cells import FLUID_CELLS, SAND_CELLS
from audit_fs_c04_thermal_interfaces import audit as audit_contacts
from stage_fs_c04_initial_alpha import digest, boundary_patches
from stage_fs_c04_initial_temperature import (
    T_METAL_K, T_AIR_K, T_MOLD_K, check_T,
)
from verify_fs_c04_native_temperature import read_stage
from run_fs_c02_local import THERMO_METAL

CASE_PREFIX="FS_C05_VOF_CHT_SCREEN_"
OFFICIAL_REL=Path("multiRegion/CHT/VoFcoolingCylinder2D")
REGION_FIELDS={
    "fluid":("alpha.metal","T","T.air","T.metal","p","p_rgh","U",
             "k","epsilon","nut","alphat"),
    "mold":("T",),
}
ATMOSPHERES=("atmosphereTop","atmosphereSides","atmosphereLowerSides")
MOLD_PATCHES=("moldBottom","moldRecessWall","moldRecessRoof")


def header(object_name:str,region:str,kind:str)->str:
    return (f"FoamFile\n{{\n    version 2.0;\n    format ascii;\n"
            f"    class {kind};\n    location \"0/{region}\";\n"
            f"    object {object_name};\n}}\n")


def scalar_field(name:str,region:str,dimension:str,inside:str,
                 bc:dict[str,str])->str:
    out=[
        "/* FS-C05 thermal-VOF candidate: provisional, NOT CFD-validated. */",
        header(name,region,"volScalarField"),
        "dimensions "+dimension+";",
        "internalField "+inside+";",
        "boundaryField",
        "{",
    ]
    for patch,setting in bc.items():
        out.extend(["    "+patch,"    {","        "+setting+";","    }"])
    out.append("}")
    return "\n".join(out)+"\n"


def vector_field(bc:dict[str,str])->str:
    out=[
        "/* FS-C05 initial at-rest fluid, RAS screening only. */",
        header("U","fluid","volVectorField"),
        "dimensions [0 1 -1 0 0 0 0];",
        "internalField uniform (0 0 0);",
        "boundaryField",
        "{",
    ]
    for patch,setting in bc.items():
        out.extend(["    "+patch,"    {","        "+setting+";","    }"])
    out.append("}")
    return "\n".join(out)+"\n"


def patch_bcs(wall_setting:str,outer_setting:str)->dict[str,str]:
    return {"fluid_to_mold":wall_setting,**{p:outer_setting for p in ATMOSPHERES}}


def control_dict(src:str)->str:
    require("fluid           compressibleVoF;" in src
            and "solid           solid;" in src,
            "installed v14 tutorial no longer contains compatible region solvers")
    src=src.replace("solid           solid;","mold            solid;")
    # Never silently overwrite the original tutorial, all changes in new copy.
    replaces={
        "endTime         5;":"endTime         5e-06;",
        "deltaT          1e-4;":"deltaT          1e-07;",
        "writeInterval   0.1;":"writeInterval   1e-06;",
        "maxCo           2;":"maxCo           0.1;",
        "maxAlphaCo      1;":"maxAlphaCo      0.1;",
        "maxDeltaT       1;":"maxDeltaT       1e-07;",
        "writePrecision  8;":"writePrecision  12;",
    }
    for a,b in replaces.items():
        require(src.count(a)==1,"v14 tutorial controlDict differs: "+a)
        src=src.replace(a,b,1)
    return ("/* FS-C05 5us feasibility smoke, RAS screening, no solidification. */\n"
            +src)


def stage(source:Path,acceptance:Path,tutorial:Path,out:Path)->dict:
    source=source.expanduser().resolve()
    acceptance=acceptance.expanduser().resolve()
    tutorial=tutorial.expanduser().resolve()
    out=out.expanduser().resolve()
    require(source.is_dir() and source.name.startswith("FS_C04_T_INITIAL_STAGE_"),
            "source must be validated FS-C04 initial T")
    require(out.name.startswith(CASE_PREFIX)
            and not out.exists() and not out.is_symlink(),
            "new FS-C05 destination required; never overwrite")
    for old in (source,acceptance,tutorial):
        require(old not in out.parents and out not in old.parents and old!=out,
                "new output cannot overlap any existing source or tutorial")
    record=read_stage(source)
    require(record["status"]=="INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT",
            "FS-C04 T fields not approved")
    state=acceptance/"FS_C04_NATIVE_T_ACCEPTANCE.json"
    require(state.is_file() and not state.is_symlink()
            and acceptance.name.startswith("FS_C04_T_NATIVE_CHECK_"),
            "native T acceptance is missing")
    check=json.loads(state.read_text())
    require(check.get("status")=="NATIVE_2_REGION_T_INTEGRALS_VERIFIED_NO_CHT"
            and check.get("source")==str(source)
            and check.get("T_field_read_natively") is True
            and check.get("native_volume_integrals_verified") is True
            and check.get("CFD_or_CHT_executed") is False
            and len(check.get("native_postprocess",{}))==4,
            "native T integrals not accepted for the source")
    old_contact=audit_contacts(Path(record["source_accepted_alpha_case"]))
    require(record["source_thermal_interface_audit"]==old_contact,
            "thermal contact geometry changed")
    alpha=read_alpha(source/"0/fluid/alpha.metal",
                     expected_cells=FLUID_CELLS)
    require(len(alpha)==34368 and alpha.count(1.)==2368
            and alpha.count(0.)==32000,
            "source VOF alpha fraction altered")
    require(check_T(source/"0/fluid/T","fluid",alpha)["cells"]==FLUID_CELLS
            and check_T(source/"0/mold/T","mold")["cells"]==SAND_CELLS,
            "initial temperature fields invalid")
    for p in (tutorial/"system/controlDict",
              tutorial/"system/fvSolution",
              tutorial/"system/fluid/fvSchemes",
              tutorial/"system/fluid/fvSolution",
              tutorial/"system/solid/fvSchemes",
              tutorial/"system/solid/fvSolution",
              tutorial/"constant/solid/physicalProperties"):
        require(p.is_file() and not p.is_symlink(),
                "required installed OpenFOAM v14 template missing: "+str(p))
    # Fail closed BEFORE creating the destination if official solver grammar
    # changed or if the kEpsilon transport entry cannot be installed.
    control_dict((tutorial/"system/controlDict").read_text(encoding="utf-8"))
    fv_schemes_source=(tutorial/"system/fluid/fvSchemes").read_text(
        encoding="utf-8")
    require(len(re.findall(r"div\(phi,k\)\s+\$turbulence;",fv_schemes_source))==1,
            "official Foundation14 turbulence transport scheme changed")
    source_hashes={}
    for root,dirs,files in os.walk(source,followlinks=False):
        for name in dirs+files:
            require(not (Path(root)/name).is_symlink(),
                    "source stage contains symlink; refuse unsanitized copy")
    for root,dirs,files in os.walk(tutorial,followlinks=False):
        for name in dirs+files:
            if (Path(root)/name).is_symlink():
                # Only selected listed files are read; do not follow symlinks.
                continue
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,out,symlinks=False)
    # The original stage included old postProcessing, don't falsely re-use it.
    for stale in (out/"postProcessing",out/"0"/"postProcessing"):
        if stale.is_dir():
            shutil.rmtree(stale)
    for name in ("constant","system","0"):
        (out/name).mkdir(exist_ok=True)
    def write(path:str,content:str):
        dest=out/path
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(content,encoding="utf-8")
        source_hashes[path]=hashlib.sha256(content.encode()).hexdigest()
    def official(path:str)->str:
        p=tutorial/path
        require(p.is_file() and not p.is_symlink(),"missing trusted tutorial template "+path)
        return p.read_text(encoding="utf-8")
    write("system/controlDict",control_dict(official("system/controlDict")))
    write("system/fvSolution",official("system/fvSolution"))
    fluid_schemes,changed=re.subn(
        r"div\(phi,k\)\s+\$turbulence;",
        "div(phi,k)         $turbulence;\n"
        "    div(phi,epsilon)   $turbulence;",
        official("system/fluid/fvSchemes"))
    require(changed==1 and "div(phi,epsilon)" in fluid_schemes,
            "could not install kEpsilon energy/divergence transport scheme")
    write("system/fluid/fvSchemes",fluid_schemes)
    fv=official("system/fluid/fvSolution")
    require(fv.count('"alpha.water.*"')==1
            and fv.count('"(T|k|B|nuTilda).*"')==1,
            "unexpected official fluid solver settings")
    fv=fv.replace('"alpha.water.*"','"alpha.metal.*"')
    fv=fv.replace('"(T|k|B|nuTilda).*"',
                  '"(T|k|epsilon|B|nuTilda).*"')
    write("system/fluid/fvSolution",fv)
    write("system/mold/fvSchemes",official("system/solid/fvSchemes"))
    write("system/mold/fvSolution",official("system/solid/fvSolution"))
    # Physically distinct 2 regions, not three separate solver regions.
    write("constant/fluid/phaseProperties",
          "FoamFile { version 2.0; format ascii; class dictionary; "
          'location "constant/fluid"; object phaseProperties; }\n'
          "phases (metal air);\n"
          "sigma { type constant; sigma 1.0; }\n")
    write("constant/fluid/physicalProperties.metal",
          THERMO_METAL.replace('location "constant";',
                               'location "constant/fluid";'))
    original_air=Path(__file__).resolve().parents[1]/"freesurface/FS-C01/constant/physicalProperties.air"
    require(original_air.is_file(),"FS-C01 original perfectGas air thermo missing")
    write("constant/fluid/physicalProperties.air",
          original_air.read_text().replace(
              'location    "constant";','location    "constant/fluid";'))
    write("constant/fluid/momentumTransport",
          (Path(__file__).resolve().parents[1]/
           "freesurface/FS-C01/constant/momentumTransport").read_text()
          .replace('location    "constant";','location    "constant/fluid";'))
    write("constant/fluid/fvModels",
          (Path(__file__).resolve().parents[1]/
           "freesurface/FS-C01/constant/fvModels").read_text()
          .replace('location    "constant";','location    "constant/fluid";'))
    write("constant/fluid/g",
          'FoamFile { version 2.0; format ascii; class uniformDimensionedVectorField;'
          ' location "constant/fluid"; object g; }\n'
          'dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);\n')
    # Preliminary solid material only: real QuickCup silica Cp/k(T) pending.
    write("constant/mold/physicalProperties",
          'FoamFile { version 2.0; format ascii; class dictionary;'
          ' location "constant/mold"; object physicalProperties; }\n'
          'thermoType constSolidThermo;\n'
          'rho { type uniform; value 1500; }\n'
          'Cv { type uniform; value 700; }\n'
          'kappa { type uniform; value 2; }\n')
    # Explicit NO heat source: initially hot liquid metal is the only thermal reservoir.
    write("constant/mold/fvModels",
          'FoamFile { version 2.0; format ascii; class dictionary;'
          ' location "constant/mold"; object fvModels; }\n')
    # Fixed fluid variable T and solid T coupled physically at material interface.
    write("0/fluid/T",scalar_field("T","fluid","[0 0 0 1 0 0 0]",
        (source/"0/fluid/T").read_text().split("internalField",1)[1]
          .split("boundaryField",1)[0].strip().removesuffix(";"),
        patch_bcs("type coupledTemperature; value uniform 300",
                  "type inletOutlet; inletValue uniform 300; value uniform 300")))
    write("0/mold/T",scalar_field("T","mold","[0 0 0 1 0 0 0]",
        "uniform 300",
        {"mold_to_fluid":"type coupledTemperature; value uniform 300",
         **{p:"type zeroGradient" for p in MOLD_PATCHES}}))
    # The phase enthalpy sub-fields are derived/calculated, like the Foundation14 tutorial.
    for phase,temp in (("metal",1500),("air",300)):
        write("0/fluid/T."+phase,
              scalar_field("T."+phase,"fluid","[0 0 0 1 0 0 0]",
                "uniform "+str(temp),
                patch_bcs("type calculated; value uniform "+str(temp),
                          "type calculated; value uniform "+str(temp))))
    write("0/fluid/U",vector_field(
        patch_bcs("type noSlip",
            "type pressureInletOutletVelocity; value uniform (0 0 0)")))
    write("0/fluid/p",scalar_field("p","fluid","[1 -1 -2 0 0 0 0]",
        "uniform 100000",patch_bcs("type calculated; value uniform 100000",
                                  "type calculated; value uniform 100000")))
    write("0/fluid/p_rgh",scalar_field("p_rgh","fluid","[1 -1 -2 0 0 0 0]",
        "uniform 100000",patch_bcs(
            "type fixedFluxPressure; value uniform 100000",
            "type prghTotalPressure; p0 uniform 100000; value uniform 100000")))
    for name,dimensions,initial,wall,atm in (
        ("k","[0 2 -2 0 0 0 0]","0.1",
         "type kqRWallFunction; value uniform 0.1",
         "type inletOutlet; inletValue uniform 0.1; value uniform 0.1"),
        ("epsilon","[0 2 -3 0 0 0 0]","0.1",
         "type epsilonWallFunction; value uniform 0.1",
         "type inletOutlet; inletValue uniform 0.1; value uniform 0.1"),
        ("nut","[0 2 -1 0 0 0 0]","0",
         "type nutkWallFunction; value uniform 0",
         "type calculated; value uniform 0"),
        ("alphat","[1 -1 -1 0 0 0 0]","0",
         "type compressible::alphatWallFunction; value uniform 0",
         "type calculated; value uniform 0"),
    ):
        write("0/fluid/"+name,scalar_field(name,"fluid",dimensions,
              "uniform "+initial,patch_bcs(wall,atm)))
    require((out/"0/fluid/alpha.metal").is_file()
            and digest(out/"0/fluid/alpha.metal")==
            digest(source/"0/fluid/alpha.metal"),
            "FS-C05 altered previously validated alpha.metal")
    require(not (out/"0/mold/alpha.metal").exists(),
            "the solid sand cannot contain a VOF field")
    bc=boundary_patches(out/"constant/fluid/polyMesh/boundary")
    require("fluid_to_mold" in bc
            and all(x in bc for x in ATMOSPHERES),
            "air-sand mappedWall or open atmosphere patch lost")
    for name in REGION_FIELDS["fluid"]:
        require((out/"0/fluid"/name).is_file(),
                "FS-C05 missing fluid field: "+name)
    for name in REGION_FIELDS["mold"]:
        require((out/"0/mold"/name).is_file(),
                "FS-C05 missing mold field: "+name)
    # Reconfirm native geometries unaltered: no change to mesh after staging.
    for region in ("fluid","mold"):
        for file in ("points","faces","owner","neighbour","boundary"):
            rel=f"constant/{region}/polyMesh/{file}"
            require(digest(out/rel)==digest(source/rel),
                    "FS-C05 changed approved mesh: "+rel)
    record_out={
        "schema":"masterproject-fs-c05-vof-cht-physics-candidate-v1",
        "status":"VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD",
        "new_case":str(out),
        "source_temperature_case":str(source),
        "native_temperature_acceptance":str(acceptance),
        "native_temperature_acceptance_sha256":digest(state),
        "official_Foundation14_tutorial":str(tutorial),
        "regionSolvers":{"fluid":"compressibleVoF","mold":"solid"},
        "pilot_reference":{
            "phase_metal_initial_cells":2368,
            "phase_air_initial_cells":32000,
            "mold_cells":7680,
            "initial_metal_volume_m3":4.801191628e-5,
            "fluid_sand_contact_faces":3136,
            "coupled_temperature_solid_walls":["fluid_to_mold","mold_to_fluid"],
            "open_gas_far_boundaries":list(ATMOSPHERES),
            "mold_support_and_lower_recess_unresolved":True,
        },
        "screening_assumptions_UNVALIDATED":{
            "metal":{"rho_kg_m3":6820,"Cv_J_kgK":827,
                     "mu_Pa_s":0.0055,"Pr":0.14,
                     "sigma_N_m":1.0},
            "air":{"ideal_gas":True,"Cp_J_kgK":1007,"Pr":0.7},
            "sand":{"rho_kg_m3":1500,"Cv_J_kgK":700,"k_W_mK":2},
            "initial_T_K":{"metal":T_METAL_K,"air":T_AIR_K,"sand":T_MOLD_K},
            "RAS":"kEpsilon UNCALIBRATED",
            "VoFTurbulenceDamping_delta_m":0.0001,
            "sand_bottom_and_recess":"zeroGradient (adiabatic screening, NOT physically validated)",
            "end_time_s":5e-6,
        },
        "written_files_sha256":source_hashes,
        "mesh_and_alpha_initial_integrity_preserved":True,
        "solver_executed":False,
        "native_dictionary_validation_done":False,
        "VOF_CHT_energy_balance_validated":False,
        "physical_CAD_surface_fidelity_verified":False,
        "latent_heat_solidification_graphitization_shrinkage":False,
        "do_not_execute_without_native_review":True,
        "warnings":[
            "UNTESTED CHT screening solver inputs; syntax/model compatibility must pass in Foundation14 first",
            "1500K metal / 300K gas/sand and material data are provisional",
            "The 3136 mapped wall faces encode conjugate interface but thermal flux has NOT been solved",
            "Air at 300K reentry is provisional; open top and lateral boundaries require flow verification",
            "The physical mold base, support and lower cavity remain unresolved",
            "No heat source, no phase change, no latent heat and no shrinkage",
        ],
    }
    (out/"FS_C05_PHYSICS_CANDIDATE.json").write_text(
        json.dumps(record_out,indent=2)+"\n"
    )
    return record_out


def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--native-T-accepted",type=Path,required=True)
    parser.add_argument("--tutorial",type=Path,default=None)
    parser.add_argument("--out",type=Path,default=None)
    a=parser.parse_args(argv)
    tutorial=a.tutorial or Path(os.environ.get(
        "FOAM_TUTORIALS","/opt/openfoam14/tutorials"))/OFFICIAL_REL
    out=a.out or (Path.home()/"OpenFOAM"/"FS_C05_VOF_CHT_RUNS"/(
        CASE_PREFIX+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        +"_"+uuid.uuid4().hex[:8]))
    try:
        record=stage(a.source,a.native_T_accepted,tutorial,out)
        print("FS-C05:",record["status"])
        print("New untouched copy with physics candidate:",record["new_case"])
        print("Region solvers:",record["regionSolvers"])
        print("Still UNTESTED: no CFD, no CHT energy/temperature evolution accepted.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,
            json.JSONDecodeError) as exc:
        print("FS-C05 STAGING BLOCKED: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
