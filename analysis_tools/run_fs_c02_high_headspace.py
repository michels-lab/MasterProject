#!/usr/bin/env python3
"""FS-C02: 120mm vertical-only atmospheric geometry study, STAGE-ONLY.

Geometry sensitivity A/B relative to existing FS-C02_EXTENDED 60mm domain:
- same 40mm initial metal column, same 40mm horizontal span and 10mm depth;
- original 60mm fluid domain remains unchanged in the first 120 y-cells;
- ADD an exterior air zone from y=0.060 to 0.120m, 120 additional y cells;
- same 0.5mm cell resolution; 80x240x1=19200 total cells;
- atmosphere patch is MOVED to y=0.120m, not changed into a wall;
- RAS kEpsilon and VoFTurbulenceDamping unchanged (NO laminar);
- initial air 300K, metal 1500K, Co target .15, tolerance .20, 0.01s.

Not approved for CFD: air is NOT extended over the physical sand mold.\nOpenFOAM Foundation 14 only. Does NOT change any earlier run and does NOT
represent a real mold solid / CHT / solidification / shrinkage. The upper
extension is an OUTSIDE air plenum, not an artificial increase in mold cavity.
A signed patch phi sum is NOT independently measured phase-resolved air mass.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys
import uuid

from run_fs_c02_local import (
    INITIAL_VOLUME, check, check_runtime, digest, execute, replace_once,
    stage, write_record,
)
from audit_fs_c02_local import read_alpha, read_temperature, read_volume
from audit_fs_c02_open_top import verify as verify_open_top

PROFILE="HIGH_HEADSPACE_0_01S_RAS_ATMOSPHERE"
EXTENDED_BASE_PROFILE="EXTENDED_PROBE_0_01S_TIGHTER_CO"
TOTAL_HEIGHT_M=.12
METAL_HEIGHT_M=.04
DOMAIN_WIDTH_M=.04
DOMAIN_DEPTH_M=.01
NX=80
NY=240
NZ=1
EXPECTED_CELLS=NX*NY*NZ
CELL_VOLUME=DOMAIN_WIDTH_M*TOTAL_HEIGHT_M*DOMAIN_DEPTH_M/EXPECTED_CELLS
MAX_CO_ACCEPT=.20

# OpenFOAM Foundation14 source:
# etc/caseDicts/functions/surfaceFieldValue/patchFlowRate
# patch atmosphere; fields (phi); operation sum;
# Signed patch phi: positive = net outward MIXTURE volumetric flux in
# Foundation14 compressibleVoF, not independently phase-resolved air flux.
FUNCTION_OBJECT = """    atmosphereFlux
    {
        type            surfaceFieldValue;
        libs            ("libfieldFunctionObjects.so");
        patch           atmosphere;
        operation       sum;
        fields          (phi);
        writeFields     false;
        executeControl  writeTime;
        writeControl    writeTime;
        writeToFile     true;
        log             true;
    }

"""


def prepare(out: Path) -> tuple[Path,dict]:
    case, status=stage(out,extended_probe=True)
    manifest_file=case/"FS-C02_MANIFEST.json"
    manifest=json.loads(manifest_file.read_text())
    check(manifest["execution_profile"] == EXTENDED_BASE_PROFILE,
          "reference extended controls changed")
    check(manifest["time_controls"] == status["time_controls"] and
          status["time_controls"]["endTime_s"] == .01 and
          status["time_controls"]["maxCo"] == .15 and
          status["time_controls"]["acceptance_maxCo"] == .20,
          "unknown time controls; do not compare")

    path=case/"system/blockMeshDict"
    geometry=path.read_text()
    for old,new in (
        ("(0.04 0.06 0)", "(0.04 0.12 0)"),
        ("(0 0.06 0)", "(0 0.12 0)"),
        ("(0.04 0.06 0.01)", "(0.04 0.12 0.01)"),
        ("(0 0.06 0.01)", "(0 0.12 0.01)"),
        ("(80 120 1)", "(80 240 1)"),
    ):
        geometry=replace_once(geometry,old,new,"high-headspace mesh geometry")
    check("atmosphere { type patch; faces ((3 7 6 2)); }" in geometry,
          "lost open-air top patch; refusing artificial roof")
    path.write_text(geometry)

    control=case/"system/controlDict"
    original=control.read_text()
    check("atmosphereFlux" not in original,"unexpected duplicate flux monitor")
    updated=replace_once(
        original,"    metalVolume\n    {",
        FUNCTION_OBJECT+"    metalVolume\n    {",
        "atmospheric patch flux monitoring"
    )
    control.write_text(updated)
    manifest["execution_profile"]=PROFILE
    manifest["contrast_to_profile"]=EXTENDED_BASE_PROFILE
    manifest["geometry"]={
        "physical_scope":"EXTERIOR_AIR_EXTENSION_ONLY_NO_MOLD_SOLID",
        "domain_y_m": [0.,TOTAL_HEIGHT_M],
        "initial_metal_y_m": [0.,METAL_HEIGHT_M],
        "original_outer_top_y_m":.06,
        "new_outer_top_y_m":TOTAL_HEIGHT_M,
        "extension_air_y_m":[.06,TOTAL_HEIGHT_M],
        "initial_air_headspace_m":TOTAL_HEIGHT_M-METAL_HEIGHT_M,
        "initial_air_headspace_reference_m":.02,
        "grid":[NX,NY,NZ],
        "dy_m":.0005,
        "same_lower_60mm_grid":True,
        "atmosphere_patch":"y=0.120m, open top",
        "flux_monitor":"signed sum(phi) on atmosphere, mixture not air-only",
    }
    manifest["changed_inputs_relative_to_60mm_reference"]=[
        "system/blockMeshDict","system/controlDict"
    ]
    inputs=manifest["generated_input_sha256"]
    check(len(inputs)==20,"expected frozen 20 inputs")
    for key in inputs:
        p=case/key
        check(p.is_file() and not p.is_symlink(),"missing input "+key)
        inputs[key]=digest(p)
    write_record(manifest_file,manifest)
    status["profile"]=PROFILE
    status["high_headspace"]=True
    status["geometry"]=manifest["geometry"]
    write_record(out/"FS-C02_RUN_STATUS.json",status)
    # Static atmospheric BC check is independent of solver run/mesh.
    report=verify_open_top(out)
    check(report["top_y_m"]==TOTAL_HEIGHT_M and
          report["initial_air_headspace_m"] > .0799 and
          report["top_is_open_patch"] is True,
          "top is blocked/mislocated")
    return case,status


def read_patch_flux(case: Path) -> dict:
    candidates=sorted((case/"postProcessing/atmosphereFlux").rglob("surfaceFieldValue.dat"))
    if not candidates:
        return {"measured":False,
                "warning":"No atmosphereFlux saved; cannot claim gas escaped"}
    check(len(candidates)==1,"multiple atmospheric flux series")
    file=candidates[0]
    check(not file.is_symlink(),"untrusted atmospheric flux output")
    lines=file.read_text(encoding="utf-8", errors="replace").splitlines()
    header=[s.strip() for s in lines if s.strip().startswith("#") and "Time" in s]
    check(any("sum(phi)" in h for h in header),"expected sum(phi) header absent")
    rows=[]
    for line in lines:
        s=line.strip()
        if not s or s.startswith("#"):
            continue
        parts=s.split()
        check(len(parts)==2,"atmosphereFlux expected exactly time and sum(phi)")
        t,q=map(float,parts)
        check(math.isfinite(t) and math.isfinite(q),"bad atmospheric phi")
        check(not rows or t>rows[-1][0],"nonmonotone atmospheric flux times")
        rows.append((t,q))
    check(rows and abs(rows[-1][0]-.01)<1e-6,
          "atmospheric flux final time missing")
    integral=sum(.5*(qb+qa)*(tb-ta)
                 for (ta,qa),(tb,qb) in zip(rows,rows[1:]))
    return {
        "measured":True,
        "field":"phi, MIXTURE volumetric flux; not phase-resolved air mass",
        "units_assumed":"m3/s for volumetric phi; verify field dimensions",
        "sign_convention":"positive outward, negative inward to the domain",
        "rows":len(rows),
        "positive_flux_samples":sum(q>0 for _,q in rows),
        "negative_flux_samples":sum(q<0 for _,q in rows),
        "maximum_outward_m3_per_s":max(q for _,q in rows),
        "minimum_signed_m3_per_s":min(q for _,q in rows),
        "last_signed_m3_per_s":rows[-1][1],
        "trapezoid_integrated_net_phi_m3":integral,
        "source_sha256":digest(file),
        "outgoing_AIR_mass_or_heat_verified":False,
        "interpolation_warning":"integral from saved 0.001s snapshots, not full timestep flux",
    }


def summarize(case: Path) -> dict:
    last=case/"0.01"
    alpha=read_alpha(last/"alpha.metal",expected_cells=EXPECTED_CELLS)
    T=read_temperature(last/"T",expected_cells=EXPECTED_CELLS)
    check(all(-1e-6<=a<=1+1e-6 for a in alpha),"VOF outside [0,1]")
    check(all(math.isfinite(t) and t>0 for t in T),"bad temperature")
    near_air=[t for a,t in zip(alpha,T) if a<=1e-6]
    near_metal=[t for a,t in zip(alpha,T) if a>=.99]
    check(near_air and near_metal,"no resolved gas/metal regions")
    vol=read_volume(case/"postProcessing/metalVolume/0/volFieldValue.dat")
    check(abs(vol[-1][0]-.01)<1e-6,"0.01s metalVolume missing")
    first_v=vol[0][1]
    check(first_v>0,"invalid initial metalVolume")
    fieldvol=sum(alpha)*CELL_VOLUME
    maxdrift=max(abs(v-first_v)/INITIAL_VOLUME for _,v in vol)
    flux=read_patch_flux(case)
    return {
        "schema":"masterproject-fs-c02-high-headspace-numeric-trace-v1",
        "profile":PROFILE,
        "status":"PROVISIONAL_NO_PHYSICAL_VALIDATION",
        "time_s":.01,
        "domain_y_m":[0,.12],
        "initial_metal_y_m":[0,.04],
        "open_top_boundary_y_m":.12,
        "original_open_top_boundary_y_m":.06,
        "air_headspace_original_m":.02,
        "air_headspace_new_m":.08,
        "cell_count":EXPECTED_CELLS,
        "cell_size_vertical_m":.0005,
        "volume_field_m3":fieldvol,
        "volume_function_m3":vol[-1][1],
        "max_relative_metal_volume_drift":maxdrift,
        "field_vs_function_relative_mismatch":abs(fieldvol-vol[-1][1])/INITIAL_VOLUME,
        "alpha_min":min(alpha),
        "alpha_max":max(alpha),
        "interface_cells_0_01_to_0_99":sum(.01<a<.99 for a in alpha),
        "gas_near_pure_cells":len(near_air),
        "gas_near_pure_mean_T_K":sum(near_air)/len(near_air),
        "gas_near_pure_hot_over_1000K_cells":sum(t>1000 for t in near_air),
        "metal_like_mean_T_K":sum(near_metal)/len(near_metal),
        "atmosphere_flux":flux,
        "outflow_bc_validated_static":True,
        "air_outflow_physically_verified":False,
        "energy_balance_verified":False,
        "solidification_and_shrinkage_not_modelled":True,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage-only",action="store_true")
    p.add_argument("--out",type=Path,default=None)
    args=p.parse_args(argv)
    newname=("FS-C02_HIGH_AIR_"+
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8])
    out=(args.out or Path.home()/"OpenFOAM"/"FS_C02_HIGH_AIR_RUNS"/newname).expanduser().resolve()
    try:
        # Do not run this old 40mm-wide air column as a substitute for
        # exterior air over the REAL 51.8mm-wide QuickCup sand mold.
        # Keep stage-only for geometry/provenance studies; no CFD until a
        # conforming metal+sand+exterior-air multiregion mesh is designed.
        check(args.stage_only,
              "GEOMETRY BLOCK: 120mm pilot is only a 40mm-wide vertical air column; "
              "it omits air above the 51.8mm sand mold. Use --stage-only "
              "for historical geometry inspection; do not run this as physical CFD.")
        case,status=prepare(out)
        print("FS-C02 HIGH-AIR stage: "+str(case),flush=True)
        print("TOP open patch at y=0.12 m; metal 0-0.04 m; 80 mm of air above.",flush=True)
        if args.stage_only:
            print("STAGED ONLY. NO CFD WAS EXECUTED.")
            return 0
        execute(out,case,status)
        numeric=summarize(case)
        status["high_headspace_numeric_screen"]=numeric
        status["top_flux_observed"]=numeric["atmosphere_flux"]["measured"]
        write_record(out/"FS-C02_RUN_STATUS.json",status)
        write_record(out/"FS-C02_HIGH_AIR_NUMERICAL_SCREEN.json",numeric)
        print("FS-C02 HIGH-AIR Co gate: "+status["status"])
        print("FS-C02 HIGH-AIR Co peak: "+str(status["courant_probe"]["peak_max"]))
        print("FS-C02 HIGH-AIR gas mean T K: "+str(numeric["gas_near_pure_mean_T_K"]))
        print("FS-C02 HIGH-AIR top patch signed flux: "+
              str(numeric["atmosphere_flux"]),flush=True)
        print("NO mold, CHT, solidification, or shrinkage validation.")
        return 0 if (status["status"]=="PROBE_COURANT_SCREEN_PASSED" and
                     numeric["atmosphere_flux"]["measured"]) else 1
    except (OSError,ValueError,TypeError,KeyError,ZeroDivisionError) as e:
        print("FS-C02 HIGH-AIR BLOCKED: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
