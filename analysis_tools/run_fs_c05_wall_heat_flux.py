#!/usr/bin/env python3
"""FS-C05: instrument BOTH conjugate walls with Foundation14 wallHeatFlux.

Creates a NEW ISOLATED copy from the original staged FS-C05 candidate;
repairs compressible RAS schemes only in that copy, keeps the already
successful 2-step duration and runs foamMultiRun only when --native is set.

Requires BOTH *real* wallHeatFlux output tables, for fluid_to_mold and
mold_to_fluid at 1e-7 and 2e-7 s, after solver success. It reports the
heat power Q [W] from each region, Qfluid+Qmold and relative mismatch.
No fictitious heat transfer values, no claims of global energy balance,
no solver change in the previous accepted native case.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from audit_fs_c03_exterior_mesh import require
from stage_fs_c04_initial_alpha import digest
from stage_fs_c05_vof_cht import ensure_compressible_kepsilon_divergence
from run_fs_c05_native_smoke import (
    preflight, short_control, validate_run_log, MAX_NATIVE_SECONDS,
)

PREFIX="FS_C05_WALL_Q_PROBE_"
NATIVE_TIMES=(1e-7,2e-7)
REGION_PATCH={
    "fluid":"fluid_to_mold",
    "mold":"mold_to_fluid",
}
OBJECT_NAME={
    "fluid":"wallHeatFluxFluid",
    "mold":"wallHeatFluxMold",
}
TIME_TOL=1e-12
RECIPROCITY_ALERT_RATIO=0.05


def functions_dict()->str:
    """Exact wallHeatFlux grammar from the OpenFOAM14 Foundation class."""
    text=[
        "/* FS-C05 no-physical-validation conjugate heat-flux probe. */",
        "FoamFile",
        "{",
        "    version 2.0;",
        "    format ascii;",
        "    class dictionary;",
        '    location "system";',
        "    object functions;",
        "}",
    ]
    for region,patch in REGION_PATCH.items():
        text.extend([
            OBJECT_NAME[region],
            "{",
            "    type wallHeatFlux;",
            '    libs ("libfieldFunctionObjects.so");',
            "    region "+region+";",
            "    patches ("+patch+");",
            "    executeControl timeStep;",
            "    executeInterval 1;",
            "    writeControl timeStep;",
            "    writeInterval 1;",
            "    log true;",
            "}",
        ])
    return "\n".join(text)+"\n"


def read_wall_q(case:Path,region:str)->dict:
    """Read native wallHeatFlux.dat; never invent or infer flux from T."""
    require(region in REGION_PATCH,"unknown region")
    name=OBJECT_NAME[region]
    patch=REGION_PATCH[region]
    root=case/"postProcessing"
    require(root.is_dir(),"no native wallHeatFlux postProcessing directory")
    files=[p for p in root.rglob("*.dat") if name in p.parts]
    require(len(files)==1,
            "native wallHeatFlux file missing or ambiguous for "+region)
    path=files[0]
    require(path.is_file() and not path.is_symlink(),
            "native wallHeatFlux file must be a regular file")
    content=path.read_text(encoding="utf-8",errors="strict").splitlines()
    headings=[line for line in content if line.lstrip().startswith("#")]
    require(any("Time" in h for h in headings)
            and any("Q [W]" in h for h in headings),
            "wallHeatFlux table lacks real Time or Q [W] header")
    measured={}
    for line in content:
        x=line.strip()
        if not x or x.startswith("#"):
            continue
        parts=x.split()
        require(len(parts)==6,
                "wallHeatFlux table must have Time patch min max Q q columns")
        require(parts[1]==patch,"wallHeatFlux wrong wall patch for "+region)
        numbers=[float(parts[i]) for i in (0,2,3,4,5)]
        require(all(math.isfinite(v) for v in numbers),
                "nonfinite OpenFOAM wall heat flux")
        t=numbers[0]
        matched=[expect for expect in NATIVE_TIMES
                 if abs(t-expect)<=TIME_TOL]
        if not matched:
            # A possible t=0 functionObject initialization is not a solver step.
            require(abs(t)<=TIME_TOL,
                    "unexpected wallHeatFlux time: "+str(t))
            continue
        stamp=matched[0]
        require(stamp not in measured,"duplicate native wallHeatFlux time")
        measured[stamp]={
            "time_s":stamp,
            "patch":patch,
            "minimum_q_W_m2":numbers[1],
            "maximum_q_W_m2":numbers[2],
            "Q_W":numbers[3],
            "mean_q_W_m2":numbers[4],
        }
    require(set(measured)==set(NATIVE_TIMES),
            "missing native wallHeatFlux at 1e-7 or 2e-7s for "+region)
    return {
        "region":region,
        "function_object":name,
        "path":str(path.relative_to(case)),
        "sha256":digest(path),
        "measurements":[measured[t] for t in NATIVE_TIMES],
    }


def compare_power(a:dict,b:dict)->dict:
    values=[]
    for t,fluid,mold in zip(
        NATIVE_TIMES,a["measurements"],b["measurements"]
    ):
        require(fluid["time_s"]==mold["time_s"]==t,
                "wall heat-flux timestamps not aligned")
        qf,qm=fluid["Q_W"],mold["Q_W"]
        mismatch=qf+qm
        denom=max(abs(qf),abs(qm),1e-20)
        ratio=abs(mismatch)/denom
        values.append({
            "time_s":t,
            "Q_fluid_wall_W":qf,
            "Q_mold_wall_W":qm,
            "Q_sum_W":mismatch,
            "absolute_relative_reciprocity_mismatch":ratio,
            "wall_Q_opposite_signs":(qf*qm<0),
            "reciprocity_under_5pct_DIAGNOSTIC_ONLY":
                ratio<=RECIPROCITY_ALERT_RATIO,
        })
    return {
        "snapshot_power_comparison":values,
        "alert_mismatch_over_5pct":any(
            not x["reciprocity_under_5pct_DIAGNOSTIC_ONLY"]
            for x in values
        ),
        "energy_flux_physical_validation":False,
        "full_energy_balance_verified":False,
        "notes":[
            "wallHeatFlux reports power Q [W] per requested wall patch",
            "Opposite-sign wall power is expected by reciprocal normal orientation",
            "A per-patch power comparison is NOT global energy conservation",
            "Pressure work, enthalpy advection and open-atmosphere flux remain unmeasured",
        ],
    }


def prepare(source:Path,out:Path)->dict:
    source=source.expanduser().resolve()
    out=out.expanduser().resolve()
    require(out.name.startswith(PREFIX) and not out.exists()
            and not out.is_symlink(),
            "heat-flux probe requires a new isolated destination")
    require(source!=out and source not in out.parents
            and out not in source.parents,
            "probe destination must not overlap the staged solver source")
    provenance=preflight(source)
    out.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,out)
    schemes=out/"system/fluid/fvSchemes"
    repaired,added=ensure_compressible_kepsilon_divergence(
        schemes.read_text(encoding="utf-8"))
    if added:
        schemes.write_text(repaired,encoding="utf-8")
    require("div(rhoPhi,k)" in repaired and
            "div(rhoPhi,epsilon)" in repaired,
            "compressible RAS k and epsilon transport not installed")
    control=out/"system/controlDict"
    control.write_text(short_control(control.read_text()))
    f=out/"system/functions"
    f.write_text(functions_dict())
    return {
        "schema":"masterproject-fs-c05-wall-q-probe-v1",
        "status":"WALL_Q_PROBE_STAGED_NO_CFD",
        "source":provenance,
        "output":str(out),
        "instrumentation_object_names":OBJECT_NAME,
        "instrumentation_sha256":digest(f),
        "short_control_sha256":digest(control),
        "rhoPhi_divergence_sha256":digest(schemes),
        "rhoPhi_schemes_added_in_new_copy":added,
        "original_solver_source_untouched":True,
        "native_solver_executed":False,
        "wall_heat_flux_measured":False,
        "interface_energy_balance_validated":False,
        "global_energy_balance_validated":False,
    }


def run(source:Path,out:Path,native:bool)->dict:
    source=source.expanduser().resolve()
    out=out.expanduser().resolve()
    if native:
        require(os.environ.get("WM_PROJECT_VERSION")=="14",
                "Foundation OpenFOAM 14 is required")
        require(shutil.which("foamMultiRun") is not None,
                "foamMultiRun not available in Foundation14 PATH")
    report=prepare(source,out)
    manifest=out/"FS_C05_WALL_Q_REPORT.json"
    def save():
        manifest.write_text(json.dumps(report,indent=2)+"\n")
    save()
    if not native:
        return report
    cmd=["foamMultiRun","-case",str(out)]
    log=out/"log.FS_C05_wall_q_foamMultiRun"
    try:
        proc=subprocess.run(cmd,capture_output=True,text=True,
                            errors="replace",timeout=MAX_NATIVE_SECONDS,
                            check=False)
        log.write_text("COMMAND: "+" ".join(cmd)+
                       "\nEXIT: "+str(proc.returncode)+"\n"+
                       proc.stdout+"\n"+proc.stderr)
        report["native_solver_executed"]=True
        require(proc.returncode==0,"foamMultiRun returned nonzero exit code")
        report["native_steps"]=validate_run_log(proc.stdout+"\n"+proc.stderr)
        a=read_wall_q(out,"fluid")
        b=read_wall_q(out,"mold")
        report.update({
            "status":"TWO_STEP_FLUID_MOLD_WALL_Q_MEASURED_NO_ENERGY_VALIDATION",
            "wall_heat_flux_measured":True,
            "native_flux_records":{"fluid":a,"mold":b},
            "reciprocal_contact_power":compare_power(a,b),
            "native_log_sha256":digest(log),
        })
    except subprocess.TimeoutExpired as exc:
        raw=exc.stdout or b""
        err=exc.stderr or b""
        def show(x):
            return x.decode(errors="replace") if isinstance(x,bytes) else x
        log.write_text("TIMEOUT\n"+show(raw)+"\n"+show(err))
        report.update({
            "native_solver_executed":True,
            "status":"WALL_Q_PROBE_REJECTED",
            "failure_reason":"foamMultiRun timeout",
            "native_log_sha256":digest(log),
        })
        save()
        raise ValueError("native wall-flux run timed out") from exc
    except (OSError,ValueError) as exc:
        report.update({
            "status":"WALL_Q_PROBE_REJECTED",
            "failure_reason":str(exc),
            "native_log_sha256":digest(log) if log.is_file() else None,
        })
        save()
        raise
    save()
    return report


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path)
    p.add_argument("--native",action="store_true",
                   help="explicitly run two steps CFD in NEW copy")
    a=p.parse_args(argv)
    name=PREFIX+datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ")+"_"+uuid.uuid4().hex[:8]
    out=a.out or Path.home()/"OpenFOAM"/"FS_C05_WALL_Q_RUNS"/name
    try:
        result=run(a.source,out,a.native)
        print("FS-C05 WALL FLUX:",result["status"])
        print("isolated probe:",result["output"])
        if result["wall_heat_flux_measured"]:
            for line in result["reciprocal_contact_power"][
                "snapshot_power_comparison"
            ]:
                print("t:",line["time_s"],"Q_fluid W:",
                      line["Q_fluid_wall_W"],"Q_sand W:",
                      line["Q_mold_wall_W"],"Q_sum W:",
                      line["Q_sum_W"],"rel. mismatch:",
                      line["absolute_relative_reciprocity_mismatch"])
        print("No claim of mass/energy conservation, solidification or CAD fidelity.")
        return 0
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
        print("FS-C05 WALL-Q PROBE BLOCKED: "+str(exc),file=sys.stderr)
        log=out/"log.FS_C05_wall_q_foamMultiRun"
        if log.is_file() and not log.is_symlink():
            print("ISOLATED FAILURE CASE:",out,file=sys.stderr)
            print("REAL SOLVER LOG:",log,file=sys.stderr)
            print("\n".join(log.read_text(errors="replace").splitlines()[-50:]),
                  file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
