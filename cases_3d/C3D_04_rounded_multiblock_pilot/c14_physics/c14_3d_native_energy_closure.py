#!/usr/bin/env python3
"""Native C14 energy-flux and enthalpy/latent-power audit after offline postproc.

Reads REAL foamPostProcess volFieldValue and surfaceFieldValue tables from an
ISOLATED Case A copy. Compares energy stored with outward surface power and
latent release over saved 0.1s times; records closure residual WITHOUT
claiming physical validation. Does not execute solver, modify source or
infer model energy from temperature-only cell means.
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path
import sys

TABLES={
  "boundary":("metalBoundaryEnergyPower","surfaceFieldValue.dat"),
  "top":("metalTopEnergyPower","surfaceFieldValue.dat"),
  "contact":("metalMoldEnergyPower","surfaceFieldValue.dat"),
  "enthalpy":("metalSensibleEnthalpy","volFieldValue.dat"),
  "latent":("metalLatentHeatPower","volFieldValue.dat"),
  "alpha":("metalMeanLiquidFraction","volFieldValue.dat"),
}
OUT_CSV="C3D04_A_C14_3D_NATIVE_ENERGY_CLOSURE_101_STATES.csv"
OUT_JSON="C3D04_A_C14_3D_NATIVE_ENERGY_CLOSURE_REPORT.json"


def require(ok:bool,msg:str)->None:
    if not ok:
        raise ValueError("C14_NATIVE_ENERGY_BALANCE_BLOCKED: "+msg)


def parse_table(path:Path)->tuple[list[str],list[dict[str,float]]]:
    require(path.is_file() and not path.is_symlink(),"missing native table "+str(path))
    header=None
    result=[]
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.startswith("# Time"):
                # OpenFOAM C14: # Time <tab> sum(...), volIntegrate(...)
                header=line[1:].split()
            elif line.lstrip().startswith("#") or not line.strip():
                continue
            else:
                require(header is not None,"native fieldValue table has no named columns")
                parts=line.split()
                require(len(parts)==len(header),"native fieldValue data-column mismatch")
                row=dict(zip(header,(float(x) for x in parts)))
                require(all(math.isfinite(v) for v in row.values()),
                        "nonfinite native power/integral")
                result.append(row)
    require(len(result)==101 and header is not None,"need 101 native saved time rows")
    times=[r["Time"] for r in result]
    require(all(math.isclose(t,i/10,rel_tol=0,abs_tol=1e-8)
                for i,t in enumerate(times)),"native C14 saved times mismatch")
    return header,result


def calculate(case:Path)->dict:
    base=case/"postProcessing/metal"
    data={}
    columns={}
    for key,(folder,name) in TABLES.items():
        head,rows=parse_table(base/folder/"0"/name)
        columns[key]=head[1:]
        data[key]=rows
    expected={
        "boundary":{"sum(energyAdvectiveFlux)","sum(heatFlux)","sum(energyFlux)"},
        "top":{"sum(energyAdvectiveFlux)","sum(heatFlux)","sum(energyFlux)"},
        "contact":{"sum(energyAdvectiveFlux)","sum(heatFlux)","sum(energyFlux)"},
        "enthalpy":{"volIntegrate(rho,h)"},
        "latent":{"volIntegrate(latentHeatRateVol)"},
        "alpha":{"volAverage(phaseChangeSource:alpha1)"},
    }
    for key,need in expected.items():
        require(need.issubset(columns[key]),
                "missing exact native C14 output columns for "+key+": "+str(columns[key]))
    rows=[]
    cumulative_flux=0.0
    cumulative_latent=0.0
    first_H=data["enthalpy"][1]["volIntegrate(rho,h)"]
    for i in range(101):
        ptop=data["top"][i]["sum(energyFlux)"]
        pcontact=data["contact"][i]["sum(energyFlux)"]
        pbound=data["boundary"][i]["sum(energyFlux)"]
        lat=data["latent"][i]["volIntegrate(latentHeatRateVol)"]
        H=data["enthalpy"][i]["volIntegrate(rho,h)"]
        alpha=data["alpha"][i]["volAverage(phaseChangeSource:alpha1)"]
        need=abs(pbound-ptop-pcontact)
        scale=max(1.0,abs(pbound),abs(ptop)+abs(pcontact))
        require(need/scale < 5e-5,
                "C14 top + metal/mold power does not reconcile with summed boundary power at t="+str(i/10))
        if i>=2:
            dt=data["enthalpy"][i]["Time"]-data["enthalpy"][i-1]["Time"]
            prev_b=data["boundary"][i-1]["sum(energyFlux)"]
            prev_l=data["latent"][i-1]["volIntegrate(latentHeatRateVol)"]
            cumulative_flux+=.5*(pbound+prev_b)*dt
            cumulative_latent+=.5*(lat+prev_l)*dt
        # Start closure integration at t=0.1: t=0 native function
        # output can be uninitialized zeros and is not true wall flux.
        residual=(H-first_H)+cumulative_flux-cumulative_latent if i>=1 else None
        rows.append({
            "time_s":data["enthalpy"][i]["Time"],
            "metal_weighted_sensible_enthalpy_J":H,
            "metal_mean_alpha1_native":alpha,
            "top_energy_power_out_W":ptop,
            "metal_to_mold_energy_power_out_W":pcontact,
            "all_metal_boundary_energy_power_out_W":pbound,
            "native_latent_heat_release_power_W":lat,
            "boundary_minus_top_contact_W":pbound-ptop-pcontact,
            "cumulative_outward_energy_J_since_0p1s":cumulative_flux if i>=1 else None,
            "cumulative_latent_release_J_since_0p1s":cumulative_latent if i>=1 else None,
            "energy_closure_residual_J_since_0p1s":residual,
        })
    final=rows[-1]
    terms=(abs(final["metal_weighted_sensible_enthalpy_J"]-first_H)
           +abs(cumulative_flux)+abs(cumulative_latent))
    relative=abs(final["energy_closure_residual_J_since_0p1s"])/max(terms,1e-30)
    return {
        "schema":"C3D04_A_ORIGINAL_C14_REAL_3D_NATIVE_ENERGY_CLOSURE_CANDIDATE_V1",
        "status":"POSTRUN_NATIVE_INTEGRATED_ENERGY_DIAGNOSTIC_NOT_PHYSICAL_VALIDATION",
        "source_isolated_postProcessing":str(base),
        "time_reference_s":0.1,
        "final_time_s":10.0,
        "t0_flux_excluded_from_integral_due_to_uninitialized_function_object_risk":True,
        "energy_flux_direction":"surface outward positive as written by C14 OpenFOAM function object",
        "latent_source_sign":"solidificationRate is positive for decreasing alpha1, C14 positive latentHeatRateVol release",
        "final_integrated_terms":final,
        "final_relative_nominal_closure_residual":relative,
        "energy_conservation_physically_validated":False,
        "numerical_accuracy_validated":False,
        "other_region_mold_thermal_balance_checked":False,
        "time_step_resolution_s":0.1,
        "limitations":[
            "Nominal residual is diagnostic, not acceptance of exact discretized conservation/source identity.",
            "Native off-line 0.1s snapshot ddt may differ from in-solver 0.001s source time derivative.",
            "Metal-only boundary/enthalpy balance does not confirm full metal+mold conservation.",
            "Independent numerical, time step, experimental and both sides contact-flux checks remain pending.",
        ],
        "csv_rows":rows,
    }


def audit(case:Path)->dict:
    result=calculate(case)
    out=case/"C3D04_A_C14_NATIVE_ENERGY_AUDIT"
    require(not out.exists() and not out.is_symlink(),"cannot overwrite prior native energy audit")
    out.mkdir(parents=True,exist_ok=False)
    rows=result.pop("csv_rows")
    with (out/OUT_CSV).open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out/OUT_JSON).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",
                              encoding="utf-8")
    return result


def main()->int:
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--copy",type=Path,required=True)
    opts=ap.parse_args()
    try:
        print(json.dumps(audit(opts.copy.expanduser().resolve()),
                         indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print("C14_NATIVE_ENERGY_AUDIT_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
