#!/usr/bin/env python3
"""Continue real grouped C14-A evidence: energy inventory and native vertical chord.
Read-only original/grouped inputs; one new isolated analysis; no CFD solve.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import shutil
import sys

import c14_3d_postprocess_parity as volume
import run_c14_3d_complete_postprocess as old
import run_c14_stage07_solver_backed_recovery as recovery
import run_c14_stage07_grouped_native_recovery as grouped
import stage_c14_3d_case_a as stage

REPORT="C3D04_A_GROUPED_ENERGY_AND_VERTICAL_REPORT.json"
TABLE="C3D04_A_NATIVE_METAL_MOLD_ENERGY_INVENTORY_101.csv"
NAMES=[f"{i/10:g}" for i in range(101)]
PRIMITIVE=("U","T","p_rgh","phaseChangeSource:alpha1")
MOMENTUM=("phaseChangeSolidFraction","phaseChangeDarcyCoeff","phaseChangeModelDeltaT",
          "phaseChangeDarcyAcceleration","phaseChangeBuoyancyAcceleration","pRghAcceleration",
          "magPhaseChangeDarcyAcceleration","magPhaseChangeBuoyancyAcceleration","magPRghAcceleration",
          "phaseChangeDragToBuoyancy","phaseChangeDragToPressure")

def need(ok,msg):
    if not ok:
        raise ValueError(msg)

def profile_rows(path):
    need(path.is_file() and not path.is_symlink(),"missing profile "+str(path))
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        values=[float(x) for x in line.split()]
        need(len(values)>=2 and all(math.isfinite(x) for x in values),"invalid profile")
        rows.append(values)
    need(rows and all(len(r)==len(rows[0]) for r in rows),"empty/ragged profile")
    return rows

def longest_sample_interval(coords,lo,hi,count):
    """Identify contiguous native sampled grid coordinates, without interpolating a gap."""
    need(count>=3 and hi>lo,"invalid scan interval")
    step=(hi-lo)/(count-1)
    indices=[]
    for y in coords:
        idx=round((y-lo)/step)
        need(0<=idx<count and abs(y-(lo+idx*step))<=max(step*0.02,1e-9),
             "native profile axis does not match requested y grid")
        indices.append(idx)
    indices=sorted(set(indices))
    need(len(indices)>=3,"no supported vertical chord")
    runs=[[indices[0]]]
    for idx in indices[1:]:
        if idx==runs[-1][-1]+1:
            runs[-1].append(idx)
        else:
            runs.append([idx])
    best=max(runs,key=len)
    need(len(best)>=3,"native scan has no contiguous three-point interior")
    # Exclude one sampled spacing at each end, use exact supported grid coordinates.
    a,b=lo+best[0]*step+step*.5,lo+best[-1]*step-step*.5
    need(b>a,"degenerate interior chord")
    return {"start_y_m":a,"end_y_m":b,"length_m":b-a,
            "scan_spacing_m":step,"valid_scan_points":len(indices),
            "contiguous_runs":[[lo+r[0]*step,lo+r[-1]*step,len(r)] for r in runs],
            "native_sampled_coverage_is_not_exact_boundary_intersection":True}

def integrate(times,values,start=1):
    need(len(times)==len(values) and 0<=start<len(times),"invalid time grid")
    need(all(math.isfinite(x) for x in times+values),"nonfinite integrand")
    need(all(b>a for a,b in zip(times,times[1:])),"nonmonotone time grid")
    result=[None]*start+[0.]
    for i in range(start+1,len(times)):
        result.append(result[-1]+.5*(values[i-1]+values[i])*(times[i]-times[i-1]))
    return result

def evidence_gate(source,work):
    r=recovery.read_json(work/grouped.REPORT)
    need(r["schema"]=="C3D04_A_GROUPED_OFFLINE_V1" and r["source"]==str(source)
         and r["copy"]==str(work) and r["status"]=="GROUPED_POSTPROCESS_ATTEMPT_COMPLETE"
         and r["all_groups_without_fatal"] and r["all_required_scalar_series_101"]
         and r["source_hashes_unchanged"] and r["copy_controlDict_unchanged"],
         "real grouped report not successful or source mismatch")
    need(recovery.sha(source/"system/controlDict")==recovery.sha(work/"system/controlDict")
         ==recovery.sha(recovery.C14/"system/controlDict"),"controlDict mismatch")
    a=source/"constant/metal/fvModels"
    b=work/"constant/metal/fvModels"
    need(recovery.sha(a)==r["offline_only_selection"]["original_sha256"]
         and recovery.sha(b)==r["offline_only_selection"]["copy_sha256"]
         and grouped.replace_selection(a.read_bytes())==b.read_bytes(),
         "offline model differs beyond all-cell selector")
    need(stage.audit_existing_zone(source/"constant/metal/polyMesh/cellZones",8960),
         "original zone no longer covers all metal cells")
    for region in ("metal","mold"):
        for n in stage.MESH:
            rel=Path("constant")/region/"polyMesh"/n
            need(recovery.sha(source/rel)==recovery.sha(work/rel),"mesh mismatch "+str(rel))
    for t in NAMES:
        for field in PRIMITIVE:
            rel=Path(t)/"metal"/field
            need(recovery.sha(source/rel)==recovery.sha(work/rel),"saved primitive changed "+str(rel))
    for group,item in r["groups"].items():
        need(item["passed"] and not recovery.fatal_openfoam_log(work/item["log"])["foam_fatal_present"],
             "group fatal: "+group)
    for name,record in r["scalar_series"].items():
        fn="surfaceFieldValue.dat" if name.endswith("Power") else "volFieldValue.dat"
        path=work/"postProcessing/metal"/name/"0"/fn
        need(record["pass"] and record["rows"]==101 and recovery.sha(path)==record["sha256"],
             "native table drift: "+name)
    return r

def inventory(source,work,out):
    root=work/"postProcessing/metal"
    def series(name,column,fn="surfaceFieldValue.dat"):
        return grouped.scalar_table(root/name/"0"/fn,column,grouped.TIMES)
    H=series("metalSensibleEnthalpy",grouped.H,"volFieldValue.dat")
    alpha=series("metalMeanLiquidFraction","volAverage(phaseChangeSource:alpha1)","volFieldValue.dat")
    names={"top":"metalTopEnergyPower","contact":"metalMoldEnergyPower","total":"metalBoundaryEnergyPower"}
    powers={k:{c:series(n,c) for c in ("sum(energyFlux)","sum(heatFlux)","sum(energyAdvectiveFlux)")} for k,n in names.items()}
    contract=recovery.read_json(volume.CONTRACT)["C14_exact_values"]
    Vm=math.fsum(volume.cell_volumes(source,"metal",8960))
    vs=volume.cell_volumes(source,"mold",12352)
    rho=contract["metal"]["rho_kg_m3"]
    L=contract["solidification"]["L_J_kg"]
    sand=contract["mold"]
    ref=volume.native.scalar_field_values(source/"0.1/mold/T",12352)
    mold=[sand["rho_kg_m3"]*sand["Cv_J_kgK"]*math.fsum((a-b)*v for a,b,v in zip(
        volume.native.scalar_field_values(source/t/"mold/T",12352),ref,vs)) for t in NAMES]
    latent=[rho*L*Vm*(a-alpha[1]) for a in alpha]
    cumulative={k:{c:integrate(grouped.TIMES,vals) for c,vals in q.items()} for k,q in powers.items()}
    rows=[]
    for i,t in enumerate(grouped.TIMES):
        row={"time_s":t,"metal_native_enthalpy_J":H[i],"alpha1_volume_mean":alpha[i],
             "metal_native_enthalpy_delta_since_0p1s_J":H[i]-H[1],
             "metal_nominal_liquid_latent_inventory_delta_J":latent[i],
             "mold_nominal_sensible_inventory_delta_J":mold[i]}
        for k,q in powers.items():
            for c,v in q.items():
                label=c[4:-1]
                row[k+"_"+label+"_out_W"]=v[i]
                row[k+"_"+label+"_integrated_since_0p1s_J"]=cumulative[k][c][i]
        row["metal_nominal_inventory_plus_outward_energy_residual_J"]=(H[i]-H[1]+latent[i]+cumulative["total"]["sum(energyFlux)"][i]) if i>=1 else None
        rows.append(row)
    with (out/TABLE).open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return {"status":"NATIVE_FLUX_AND_NOMINAL_INVENTORY_DIAGNOSTIC_NOT_ENERGY_CLOSURE",
            "time_reference_s":.1,"saved_states":len(rows),"metal_volume_m3":Vm,"mold_volume_m3":math.fsum(vs),
            "latent_inventory_uses_original_constant_rho_and_L":True,
            "mold_inventory_uses_original_constant_rho_and_Cv":True,
            "final_terms":rows[-1],"csv":str(out/TABLE),
            "limitations":["Saved-state trapezoidal integration, not exact solver time integration.",
                           "EnergyFlux includes heat and advective contributions; both reported separately.",
                           "Latent inventory is not the original discretized fvModel source.",
                           "Mold exterior and mold-side interface flux not recovered by this analysis.",
                           "No global energy conservation conclusion."]}

def write_dictionary(path,blocks):
    need(not path.exists(),"generated dictionary occupied")
    path.write_text("FoamFile\n{\n format ascii;\n class dictionary;\n object "+path.name+";\n}\n\n"+"\n".join(blocks),encoding="utf-8")

def recover_vertical(source,work,out,r):
    # Copy only physical cases and saved fields, never old postProcessing.
    case=out/"vertical_case"
    case.mkdir()
    for n in ("constant","system",*NAMES):
        folder=work/n
        need(folder.is_dir() and not folder.is_symlink() and
             not any(p.is_symlink() for p in folder.rglob("*")),"unsafe grouped input "+n)
        shutil.copytree(folder,case/n)
    p=r["geometry"]["profiles"]["line_x20mm"]
    x,z=p["actual_x_m"],p["actual_z_m"]
    pts=stage.gate.load_points(source/"constant/metal/polyMesh/points")
    ymin,ymax=min(v[1] for v in pts),max(v[1] for v in pts)
    margin=(ymax-ymin)*1e-5
    lo,hi=ymin+margin,ymax-margin
    scan={"axis":"y","start":(x,lo,z),"end":(x,hi,z),"nPoints":401}
    primitive=recovery.selected_source_block((work/"system/lineProfiles").read_text(encoding="utf-8"),"verticalProfiles")
    primitive=recovery.strip_profile_unsupported_fields(primitive)
    block=old.replace_sets(primitive,"verticalProfiles",[("line_x20mm",scan)])
    d=case/"system/stage07VerticalScan"
    write_dictionary(d,[block])
    a=grouped.run(case,"verticalDenseScan",d,"10",False,"(U T p_rgh phaseChangeSource:alpha1)")
    need(a["passed"],"native vertical scan failed")
    path=case/"postProcessing/metal/verticalProfiles/10/line_x20mm.xy"
    rows=profile_rows(path)
    span=longest_sample_interval([row[0] for row in rows],lo,hi,401)
    (case/"postProcessing").rename(case/"_dense_scan_preserved")
    corrected={"axis":"y","start":(x,span["start_y_m"],z),
               "end":(x,span["end_y_m"],z),"nPoints":80}
    momentum=recovery.selected_source_block((work/"system/momentumPostProcessing").read_text(encoding="utf-8"),"momentumVerticalProfiles")
    blocks=[old.replace_sets(primitive,"verticalProfiles",[("line_x20mm",corrected)]),
            old.replace_sets(momentum,"momentumVerticalProfiles",[("line_x20mm",corrected)])]
    d=case/"system/stage07VerticalInterior"
    write_dictionary(d,blocks)
    fields=PRIMITIVE+MOMENTUM
    # These momentum fields were explicitly written by the already successful
    # grouped native diagnostics. Reuse them, never recompute the seven groups.
    for t in NAMES:
        for field in fields:
            need((case/t/"metal"/field).is_file(),"missing recovered field "+t+"/"+field)
    a=grouped.run(case,"verticalGrouped101",d,"0:",False,"("+" ".join(fields)+")")
    coverage={}
    for family in ("verticalProfiles","momentumVerticalProfiles"):
        counts=[]
        for t in NAMES:
            path=case/"postProcessing/metal"/family/t/"line_x20mm.xy"
            try:
                values=profile_rows(path)
                expected=[span["start_y_m"]+(span["end_y_m"]-span["start_y_m"])*i/79 for i in range(80)]
                step=(span["end_y_m"]-span["start_y_m"])/79
                need(len(values)==80 and all(abs(row[0]-y)<=max(step*.02,1e-9)
                     for row,y in zip(values,expected)),"incomplete/wrong vertical coordinates")
                counts.append(t)
            except (OSError,ValueError):
                pass
        coverage[family]={"complete_80_point_times":len(counts),
                          "missing_or_invalid_times":[t for t in NAMES if t not in counts]}
    return {"status":"INTERIOR_CHORD_SAMPLED_NOT_FULL_ORIGINAL_2D_HEIGHT",
            "original_request":p,"fixed_x_m":x,"fixed_z_m":z,"dense_native_scan":span,
            "physical_mesh_y_extent_m":[ymin,ymax],"corrected_profile":corrected,
            "original_requested_y_span_m":abs(p["end"][1]-p["start"][1]),
            "native_group_pass":a["passed"],"coverage":coverage,
            "complete_101_by_80":a["passed"] and all(c["complete_80_point_times"]==101 for c in coverage.values()),
            "original_2D_vertical_coordinate_coverage_equivalent":False,
            "new_case":str(case)}

def execute(source,work,out):
    source,work=source.expanduser().resolve(),work.expanduser().resolve()
    out=out.expanduser().absolute()
    need(not out.exists() and not out.is_symlink() and out.parent.resolve()==source.parent
         and work.parent==source.parent and source!=work,"require fresh sibling output")
    need(not out.is_relative_to(Path(__file__).resolve().parents[3]),"output inside repository")
    r=evidence_gate(source,work)
    before=grouped.snapshot_hashes(source)
    previous=grouped.snapshot_hashes(work) if (work/"log.foamMultiRun").is_file() else None
    # grouped copy does not include original solver log; authenticate all relevant
    # input fields and original group report in all cases.
    files=[work/grouped.REPORT]
    files.extend(work/t/"metal"/field for t in NAMES for field in PRIMITIVE+MOMENTUM)
    identities={str(p):recovery.sha(p) for p in files if p.is_file()}
    out.mkdir()
    result={"schema":"C3D04_A_GROUPED_STAGE07_CONTINUATION_V1","stage":"07/10","milestones_done":"6/10",
            "source":str(source),"grouped_input":str(work),"source_solver_rerun":False,
            "global_energy_conservation_verified":False,"quickcup_validated":False}
    for name,fn in (("energy",lambda:inventory(source,work,out)),
                    ("vertical",lambda:recover_vertical(source,work,out,r))):
        try:
            result[name]=fn()
        except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
            result[name]={"status":"BLOCKED_PRESERVED","error":str(exc)}
    result["source_hashes_unchanged"]=grouped.snapshot_hashes(source)==before
    result["grouped_input_hashes_unchanged"]=all(recovery.sha(Path(p))==h for p,h in identities.items())
    if previous is not None:
        result["grouped_input_hashes_unchanged"] &= grouped.snapshot_hashes(work)==previous
    result["report"]=str(out/REPORT)
    (out/REPORT).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    home=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,default=home/"C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    p.add_argument("--grouped",type=Path,default=home/"C3D04_A_C14_GROUPED_NATIVE_RECOVERY_01")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        result=execute(a.case,a.grouped,a.out)
        print(json.dumps(result,indent=2))
        return 0 if (result["source_hashes_unchanged"] and result["grouped_input_hashes_unchanged"]
             and result["energy"]["status"]=="NATIVE_FLUX_AND_NOMINAL_INVENTORY_DIAGNOSTIC_NOT_ENERGY_CLOSURE"
             and result["vertical"].get("complete_101_by_80")) else 3
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print("STAGE07_CONTINUATION_BLOCKED:",exc,file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
