#!/usr/bin/env python3
"""Foundation14 NATIVE real postProcess smoke on disposable TWO-STEP 27-cell/region C14.

CI only. Uses the already computed 2-step C14 synthetic fluid/solid case from
native_c14_fluid_solid_smoke.py. Calls ONLY foamPostProcess with -solver fluid;
never invokes foamMultiRun in this file, not the real V4/T02 research CFD.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import run_c14_stage07_solver_backed_recovery as production


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,required=True)
    opt=p.parse_args()
    target=opt.case.expanduser().resolve()
    if os.environ.get("WM_PROJECT_VERSION")!="14":
        print("NATIVE_SOLVER_BACKED_SMOKE_BLOCKED: requires Foundation14",file=sys.stderr)
        return 2
    if not target.is_dir() or not (target/"0.002/metal/T").is_file():
        print("NATIVE_SOLVER_BACKED_SMOKE_BLOCKED: original synthetic 2-step case missing",file=sys.stderr)
        return 2
    # On synthetic fixture, the research probe sits outside 27-cell geometry.
    # Test the genuine C14 rho*h native vol-integral object independently.
    orig=production.C14/"system/researchDiagnostics"
    path=target/"system/stage07_C14_native_solver_backend_smoke"
    if path.exists(): raise FileExistsError(str(path))
    obj=production.selected_source_block(
        orig.read_text(encoding="utf-8"),"metalSensibleEnthalpy")
    path.write_text("FoamFile\n{\n format ascii;\n class dictionary;\n"
                    " location \"system\";\n object stage07_C14_native_solver_backend_smoke;\n}\n"
                    +obj,encoding="utf-8")
    cmd=["foamPostProcess","-region","metal","-solver","fluid",
         "-dict","system/"+path.name,"-latestTime"]
    r=subprocess.run(cmd,cwd=target,capture_output=True,text=True,
                     check=False,timeout=180)
    log=target/"log.stage07.native.thermo.rho.h.smoke"
    log.write_text("ARGS: "+" ".join(cmd)+"\nRC: "+str(r.returncode)
                   +"\nSTDOUT:\n"+r.stdout+"\nSTDERR:\n"+r.stderr,
                   encoding="utf-8")
    print("SOLVER_BACKED_RHO_H_OFFLINE_NATIVE_SMOKE_RESULT",json.dumps({
        "exit_code":r.returncode,"log":str(log),
        "contains_rho_missing":"Field rho not found in database" in
            (r.stdout+r.stderr),
        "tail":(r.stdout+r.stderr)[-1600:]}))
    if r.returncode or "Field rho not found in database" in r.stdout+r.stderr:
        return 3
    # The C14 table proves rho and enthalpy native fields available.
    files=list((target/"postProcessing/metal/metalSensibleEnthalpy").rglob(
        "volFieldValue.dat")) if (target/"postProcessing/metal/metalSensibleEnthalpy").exists() else []
    if not files:
        print("NATIVE_SOLVER_BACKED_SMOKE_FAILED: no C14 rho*h output table")
        return 4
    print("NATIVE_SOLVER_BACKED_RHO_H_REAL_FOUNDATION14_POSTPROCESS_PASS")
    # Test the actual dependency order required for contact/top face power.
    # This is a two-step disposable 27-cell/region CI case, NOT V4/T02.
    energy_dict,_=production.assembled_dict_for_native_smoke(target)
    run_energy=["foamPostProcess","-region","metal","-solver","fluid",
                "-dict","system/"+energy_dict.name,"-latestTime"]
    energy_process=subprocess.run(
        run_energy,cwd=target,capture_output=True,text=True,
        check=False,timeout=180)
    energy_log=target/"log.stage07.native.flux.energy.smoke"
    energy_log.write_text(
        "ARGS: "+" ".join(run_energy)+"\\nRC: "+str(energy_process.returncode)
        +"\\nSTDOUT:\\n"+energy_process.stdout
        +"\\nSTDERR:\\n"+energy_process.stderr,
        encoding="utf-8")
    print("SOLVER_BACKED_NATIVE_ENERGY_FLUX_SMOKE_RESULT",json.dumps({
        "exit_code":energy_process.returncode,"log":str(energy_log),
        "tail":(energy_process.stdout+energy_process.stderr)[-2000:]}))
    if energy_process.returncode:
        return 5
    # All 3 face-power output families must be produced, not merely execute.
    for name in ("metalTopEnergyPower","metalMoldEnergyPower",
                 "metalBoundaryEnergyPower"):
        root=target/"postProcessing/metal"/name
        if not root.is_dir() or not list(root.rglob("surfaceFieldValue.dat")):
            print("NATIVE_SOLVER_BACKED_SMOKE_FAILED: missing energy table "+name)
            return 6
    print("NATIVE_SOLVER_BACKED_3_SURFACE_ENERGY_POWER_TABLES_F14_PASS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
