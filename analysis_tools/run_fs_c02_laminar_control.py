#!/usr/bin/env python3
"""FS-C02 laminar-control A/B test; completely separate provisional 0.01s run.

Clones extended reference inputs into a NEW external run directory, switches
RAS kEpsilon to laminar and removes its dependent VoFTurbulenceDamping source.
No other physics, material constants, mesh, time controls or BCs are changed.
Old FS-C02, FS-C01, B14, C3D-02 and all existing run folders are immutable.
Tests/CI only stage; real CFD can run ONLY in user's Foundation 14 Ubuntu.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import uuid

from run_fs_c02_local import (
    CASE_ID, INITIAL_VOLUME, check, check_runtime, digest, execute,
    replace_once, stage, write_record,
)
from audit_fs_c02_local import CELL_VOLUME, read_alpha, read_temperature, read_volume
from inspect_fs_c02_thermal import classify

BASE_PROFILE = "EXTENDED_PROBE_0_01S_TIGHTER_CO"
LAMINAR_PROFILE = "LAMINAR_CONTROL_0_01S_TIGHTER_CO"
FOAM_MODEL = (
    "turbulenceDamping\n"
    "{\n"
    "    type            compressible::VoFTurbulenceDamping;\n\n"
    "    delta           1e-4;\n"
    "}"
)


def prepare(out: Path) -> tuple[Path, dict]:
    # Always new folder: stage refuses an existing directory.
    case, record = stage(out, extended_probe=True)
    manifest_path = case / "FS-C02_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    check(manifest["execution_profile"] == BASE_PROFILE,
          "source extended-probe profile changed")
    check(record["time_controls"]["endTime_s"] == .01 and
          record["time_controls"]["maxCo"] == .15 and
          record["time_controls"]["acceptance_maxCo"] == .20,
          "time controls have changed; comparison unsafe")

    # The reference case is RAS kEpsilon + VoFTurbulenceDamping.
    # Laminar experiment isolates the dependent RAS package.
    momentum_path = case / "constant" / "momentumTransport"
    model = momentum_path.read_text()
    check(model.count("simulationType  RAS;") == 1 and
          "model           kEpsilon;" in model,
          "unexpected RAS source; refusing silent model change")
    momentum_path.write_text(replace_once(
        model, "simulationType  RAS;", "simulationType  laminar;",
        "RAS-to-laminar model"
    ))
    fvmodel_path = case / "constant" / "fvModels"
    fvmodel = fvmodel_path.read_text()
    fvmodel_path.write_text(replace_once(
        fvmodel, FOAM_MODEL,
        "// No fvModels in laminar control; turbulent epsilon damping disabled.",
        "RAS-dependent free-surface turbulence damping"
    ))
    check("turbulenceDamping" not in fvmodel_path.read_text(),
          "fvModels turbulence source still present")
    check("simulationType  laminar;" in momentum_path.read_text(),
          "laminar momentumTransport not written")

    inputs = manifest["generated_input_sha256"]
    check(len(inputs) == 20, "unexpected input file count")
    for name in inputs:
        path = case / name
        check(path.is_file() and not path.is_symlink(), "missing solver input "+name)
        inputs[name] = digest(path)
    manifest["execution_profile"] = LAMINAR_PROFILE
    manifest["contrast_to_profile"] = BASE_PROFILE
    manifest["physical_assumptions"]["turbulence"] = (
        "laminar momentumTransport, zero eddy viscosity; "
        "VoFTurbulenceDamping disabled as RAS-dependent model"
    )
    manifest["physical_assumptions"]["unused_k_epsilon"] = (
        "files retained for 20-input trace; laminar model does not solve them"
    )
    manifest["changed_input_files_vs_extended_reference"] = [
        "constant/momentumTransport", "constant/fvModels"
    ]
    manifest["interpretation"] = (
        "A/B ablation of RAS kEpsilon AND dependent VoFTurbulenceDamping; "
        "not separate effects; no CHT, no solidification or shrinkage"
    )
    write_record(manifest_path, manifest)
    record["laminar_control"] = True
    record["profile"] = LAMINAR_PROFILE
    record["control_difference_from_reference"] = (
        "RAS kEpsilon + VoFTurbulenceDamping vs laminar without damping"
    )
    write_record(out / "FS-C02_RUN_STATUS.json", record)
    return case, record


def postrun_snapshot(case: Path) -> dict:
    field_dir = case / "0.01"
    alpha = read_alpha(field_dir / "alpha.metal")
    temperature = read_temperature(field_dir / "T")
    stats = classify(alpha, temperature)
    almost_pure = [t for a,t in zip(alpha,temperature) if a<=1e-6]
    check(bool(almost_pure), "no near-pure-air cells to compare")
    volume = read_volume(case / "postProcessing/metalVolume/0/volFieldValue.dat")
    check(abs(volume[-1][0] - .01) < 1e-5,
          "end time not recorded; cannot compare with existing 0.01s probe")
    first_v = volume[0][1]
    check(first_v > 0, "zero initial metal volume")
    return {
        "schema": "masterproject-fs-c02-laminar-thermal-snapshot-v1",
        "time_s": .01,
        "first_volume_m3": first_v,
        "last_volume_m3": volume[-1][1],
        "max_vol_drift_fraction":
            max(abs(v-first_v)/INITIAL_VOLUME for _,v in volume),
        "last_alpha_integral_m3": sum(alpha)*CELL_VOLUME,
        "near_pure_air_cell_count": len(almost_pure),
        "near_pure_air_mean_T_K": sum(almost_pure)/len(almost_pure),
        "near_pure_air_cells_T_gt_1000K": sum(t>1000 for t in almost_pure),
        "gas_like_cells_alpha_le_0_01": stats["gas_like_alpha_le_0_01"],
        "interface_like_cells_alpha_0_01_to_0_99":
            stats["interface_like_alpha_0_01_to_0_99"],
        "metal_like_cells_alpha_ge_0_99":
            stats["metal_like_alpha_ge_0_99"],
        "alpha_final_min": min(alpha),
        "alpha_final_max": max(alpha),
        "fluid_energy_balance_unverified": True,
        "absolute_thermal_validity_unverified": True,
        "solidification_and_shrinkage_not_modelled": True,
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage-only",action="store_true")
    p.add_argument("--out",type=Path,default=None)
    args=p.parse_args(argv)
    name=("FS-C02_LAMINAR_"+
          datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8])
    out=(args.out or Path.home()/"OpenFOAM"/"FS_C02_LAMINAR_RUNS"/name).expanduser().resolve()
    try:
        if not args.stage_only:
            check_runtime()
        case, status=prepare(out)
        print("FS-C02 laminar control staged: "+str(case),flush=True)
        if args.stage_only:
            print("LAMINAR CONTROL STAGED ONLY: NO CFD RUN.")
            return 0
        execute(out,case,status)
        stats=postrun_snapshot(case)
        status["laminar_thermal_summary"]=stats
        write_record(out/"FS-C02_RUN_STATUS.json",status)
        write_record(out/"FS-C02_LAMINAR_THERMAL_SCREEN.json",stats)
        print("FS-C02 LAMINAR Co gate: "+status["status"])
        print("FS-C02 LAMINAR Co peak: "+str(status["courant_probe"]["peak_max"]))
        print("FS-C02 LAMINAR near-pure air T mean K: "+
              str(stats["near_pure_air_mean_T_K"]))
        print("FS-C02 LAMINAR near-pure air >1000K cells: "+
              str(stats["near_pure_air_cells_T_gt_1000K"]))
        print("FS-C02 LAMINAR max relative volume drift: "+
              str(stats["max_vol_drift_fraction"]))
        print("No energy, phase mass, solidification, mold or shrinkage verification.")
        return 0 if status["status"]=="PROBE_COURANT_SCREEN_PASSED" else 1
    except (ValueError,OSError,TypeError,KeyError,ZeroDivisionError) as exc:
        print("FS-C02 LAMINAR BLOCKED: "+str(exc),flush=True)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
