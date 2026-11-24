#!/usr/bin/env python3
"""Build and execute ONE synthetic FV Gamma!=0 step on preserved native FS-C07 mesh.

Actual OpenFOAM14 fvMesh geometry/owner/neighbour, prescribed SYNTHETIC initial
phase masses, nonzero opposite-sign phase-change Gamma, three phase internal
mass fluxes, thermal enthalpy with latent counted once; NO CFD pressure,
velocity, VOF, phase kinetics or physical 3D shrinkage.

Any diagnostic and build outputs belong outside the preserved FS-C07 case.
The original six native fields are SHA256-audited before and after.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from run_fs_c08_native_bridge import case_inputs, execute_checked
from verify_fs_c08_native_shadow import verify_shadow_stdout

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "freesurface/FS-C08_conservative_phase_mass/native_openfoam/shadow_step"
FIXTURE = NATIVE / "SYNTHETIC_ONLY_NOT_JMATPRO.dict"
EXPECTED_STATUS = "FS_C08_NATIVE_GAMMA_FV_SHADOW_PASS__SYNTHETIC_NO_CFD"


def require(condition: bool, why: str) -> None:
    if not condition:
        raise ValueError("FS-C08 GAMMA SHADOW PREFLIGHT: "+why)


def run(case: Path, output_root: Path | None = None) -> dict:
    case = case.expanduser().resolve()
    before = case_inputs(case)
    require(os.environ.get("WM_PROJECT_VERSION") == "14",
            "OpenFOAM Foundation14 not loaded (WM_PROJECT_VERSION != 14)")
    require(shutil.which("wmake") is not None,
            "wmake is not in PATH")
    bin_dir = os.environ.get("FOAM_USER_APPBIN")
    require(bool(bin_dir), "FOAM_USER_APPBIN missing")
    binary = Path(bin_dir).expanduser().resolve() / "fsC08NativeShadowStep"
    require(FIXTURE.is_file() and (NATIVE / "Make/files").is_file()
            and (NATIVE / "Make/options").is_file(),
            "native code or synthetic fixture missing")
    fixture_text = FIXTURE.read_text(encoding="utf-8")
    require("materialProvenance SYNTHETIC_ONLY_NOT_JMATPRO;" in fixture_text,
            "requires explicit synthetic provenance; never infer real iron properties")
    if output_root is None:
        output_root=Path.home()/"OpenFOAM"/"FS_C08_DIAGNOSTICS"
    output_root=output_root.expanduser().resolve()
    require(not (case == output_root or case in output_root.parents
                 or output_root in case.parents),
            "diagnostics must be entirely outside FS-C07 original")
    run_dir=output_root/(
        "FS_C08_NATIVE_GAMMA_SHADOW_"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+
        "_"+uuid.uuid4().hex[:8]
    )
    run_dir.mkdir(parents=True,exist_ok=False)
    build_log=run_dir/"wmake.log"
    native_log=run_dir/"fsC08NativeShadowStep.log"
    report_file=run_dir/"FS_C08_NATIVE_GAMMA_REPORT.json"
    report={
        "schema":"masterproject-fs-c08-native-gamma-network-wsl-evidence-v1",
        "source_fs_c07_case":str(case),
        "source_fs_c08_worktree":str(ROOT),
        "shadow_executable":str(binary),
        "versioned_fixture":str(FIXTURE),
        "fixture_provenance":"SYNTHETIC_ONLY_NOT_JMATPRO",
        "original_fields_SHA256_before":before,
        "original_fields_SHA256_after":None,
        "source_changed":None,
        "wmake_compiled":False,
        "native_shadow_executed":False,
        "conservation_and_native_mesh_gate_pass":False,
        "pressure_CFD_solved":False,
        "velocity_CFD_solved":False,
        "VOF_interface_solved":False,
        "physical_3d_shrinkage_validated":False,
        "status":"FS_C08_NATIVE_GAMMA_SHADOW_NOT_YET_VERIFIED",
        "last_error":None,
        "wmake_log":str(build_log),
        "native_log":str(native_log),
    }
    try:
        report_file.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        execute_checked(["wmake"],NATIVE,240,build_log)
        report["wmake_compiled"]=True
        require(binary.is_file(),
                "wmake reported 0 but expected shadow executable not found")
        execute_checked([
            str(binary),
            "-case",str(case),
            "-region","fluid",
            "-fixture",str(FIXTURE)
        ],ROOT,180,native_log)
        report["native_shadow_executed"]=True
        report["native_result"]=verify_shadow_stdout(
            native_log.read_text(encoding="utf-8")
        )
        report["conservation_and_native_mesh_gate_pass"]=True
        report["status"]=EXPECTED_STATUS
    except (ValueError,OSError) as err:
        report["status"]="FS_C08_NATIVE_GAMMA_SHADOW_INCOMPLETE_LOGS_PRESERVED"
        report["last_error"]=str(err)
    finally:
        try:
            after=case_inputs(case)
            report["original_fields_SHA256_after"]=after
            report["source_changed"]=before!=after
            if report["source_changed"]:
                report["status"]="FS_C08_NATIVE_GAMMA_SHADOW_SOURCE_CHANGED_CRITICAL"
                report["last_error"]="original FS-C07 saved field checksums changed"
        except (ValueError,OSError) as err:
            report["status"]="FS_C08_NATIVE_GAMMA_SHADOW_INTEGRITY_RECHECK_FAILED"
            report["last_error"]=str(err)
        report_file.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n",
                               encoding="utf-8")
        print("FS-C08 NATIVE GAMMA SHADOW REPORT:",report_file)
        print("FS-C08 STATUS:",report["status"])
        if report["last_error"]:
            print("FS-C08 DIAGNOSTIC:",report["last_error"],file=sys.stderr)
    return report


def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",type=Path,required=True)
    ap.add_argument("--output-root",type=Path,default=None)
    args=ap.parse_args(argv)
    try:
        result=run(args.case,args.output_root)
        return 0 if result["status"]==EXPECTED_STATUS else 2
    except (ValueError,OSError) as err:
        print("FS-C08 NATIVE GAMMA SHADOW BLOCKED:",err,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
