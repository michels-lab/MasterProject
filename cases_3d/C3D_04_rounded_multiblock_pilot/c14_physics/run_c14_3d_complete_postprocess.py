#!/usr/bin/env python3
"""One-shot isolated OFFLINE C14-native postProcessing on existing 3D-A 10s.

Creates a full physical COPY of the authentic finished V4/T02 CFD case, then
adapts ONLY sample/probe locations to ACTUAL metal 3D cell coordinates,
copies ORIGINAL C14 research functionObjects into the separate clone, and
calls foamPostProcess/foamLog (NEVER foamMultiRun, blockMesh, checkMesh).
The original C14 source/mesh/10s fields/controlDict stay immutable.
Incomplete native functionObjects are explicitly reported, never validated
by declaration. Derived ddt from saved 0.1s states is NOT the original
time-step-sampled 0.001s research history.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import c14_3d_postprocess_parity as volume
import c14_3d_native_energy_closure as energy
import stage_c14_3d_case_a as stage

C14=stage.physics.C14
BASE=Path(__file__).resolve().parent
METAL_CELLS=8960
COPY_NAME="C3D04_A_C14_FULL_POSTPROCESS_WORKCOPY_01"
VOLUME_NAME="C3D04_A_C14_3D_VOLUMETRIC_POSTPROCESS_01"
F14_ENV="export HWLOC_COMPONENTS=-gl; source /opt/openfoam14/etc/bashrc; exec \"$@\""


def need(cond:bool,why:str)->None:
    if not cond:
        raise ValueError("C14_NATIVE_3D_POSTPROCESS_BLOCKED: "+why)


def cell_centres(case:Path)->list[tuple[float,float,float]]:
    mesh=case/"constant/metal/polyMesh"
    pts=stage.gate.load_points(mesh/"points")
    faces=stage.gate.load_faces(mesh/"faces")
    owner=volume.label_values(mesh/"owner")
    neighbour=volume.label_values(mesh/"neighbour")
    need(len(faces)==len(owner) and max(owner+neighbour)==METAL_CELLS-1,
         "metal polyMesh topology must be authentic accepted V4/T02")
    indices=[set() for _ in range(METAL_CELLS)]
    for i,face in enumerate(faces):
        indices[owner[i]].update(face)
        if i<len(neighbour):
            indices[neighbour[i]].update(face)
    need(all(len(ids)>=4 for ids in indices),"degenerate 3D metal cell")
    return [tuple(math.fsum(pts[j][axis] for j in ids)/len(ids)
                  for axis in range(3)) for ids in indices]


def quantile(values:list[float],fraction:float)->float:
    x=sorted(values)
    need(bool(x),"missing centroid candidates")
    return x[min(len(x)-1,max(0,round((len(x)-1)*fraction)))]


def fmt(value:float)->str:
    return f"{value:.12g}"


def vector(p:tuple[float,float,float])->str:
    return "("+ " ".join(fmt(x) for x in p) +")"


def sample_geometry(centres:list[tuple[float,float,float]])->dict:
    """Prefer literal C14 metric stations if within true 3D mesh extents."""
    need(len(centres)==METAL_CELLS,"metal cell-centre count invalid")
    axes=list(zip(*centres))
    lo=[min(a) for a in axes]
    hi=[max(a) for a in axes]
    span=[b-a for a,b in zip(lo,hi)]
    need(all(s>0 for s in span),"3D metal region degenerate extent")
    source_probe=(0.02,0.02,0.005)
    probe=min(centres,key=lambda p:sum((p[i]-source_probe[i])**2 for i in range(3)))
    def near_slice(axis:int,target:float)->list[tuple[float,float,float]]:
        thickness=max(span[axis]*0.06,1e-9)
        cand=[p for p in centres if abs(p[axis]-target)<=thickness
              and abs(p[2]-probe[2])<=max(span[2]*0.12,1e-9)]
        if len(cand)<6:
            cand=[p for p in centres if abs(p[axis]-target)<=span[axis]*0.13]
        need(len(cand)>=6,"insufficient actual 3D cells for sampling slice")
        return cand
    profiles={}
    levels=(("line_y10mm",0.01,0.25),
            ("line_y20mm",0.02,0.50),
            ("line_y30mm",0.03,0.75),
            ("line_topNear",0.03975,0.92))
    for name,requested_y,fraction in levels:
        metric_ok=(lo[1]+0.01*span[1]<requested_y<
                   hi[1]-0.01*span[1] and name!="line_topNear")
        target=requested_y if metric_ok else lo[1]+span[1]*fraction
        cand=near_slice(1,target)
        actual_y=target if metric_ok else quantile([p[1] for p in cand],0.5)
        original_z_ok=(lo[2]<source_probe[2]<hi[2])
        actual_z=source_probe[2] if original_z_ok else quantile([p[2] for p in cand],0.5)
        xl=quantile([p[0] for p in cand],0.12)
        xr=quantile([p[0] for p in cand],0.88)
        need(xr-xl>span[0]*0.10,"horizontal sampling chord too short")
        profiles[name]={"axis":"x",
                        "start":(xl,actual_y,actual_z),
                        "end":(xr,actual_y,actual_z),"nPoints":80,
                        "requested_C14_y_m":requested_y,
                        "actual_y_m":actual_y,"actual_z_m":actual_z,
                        "sampling_method":(
                            "PRESERVED_C14_METRIC_Y_WITHIN_3D_BBOX_NEEDS_NATIVE_INSIDE_CHECK"
                            if metric_ok else
                            "NORMALIZED_3D_HEIGHT_FALLBACK_NOT_SAME_METRIC_Y"),
                        "normalized_y_fallback":fraction}
    cand=[p for p in centres if
          abs(p[0]-probe[0])<=span[0]*0.12 and
          abs(p[2]-probe[2])<=span[2]*0.12]
    if len(cand)<6:
        cand=centres
    bottom=quantile([p[1] for p in cand],0.12)
    top=quantile([p[1] for p in cand],0.88)
    need(top-bottom>span[1]*0.10,"vertical sampling chord too short")
    actual_x=source_probe[0] if lo[0]<source_probe[0]<hi[0] else probe[0]
    actual_z=source_probe[2] if lo[2]<source_probe[2]<hi[2] else probe[2]
    profiles["line_x20mm"]={"axis":"y",
        "start":(actual_x,bottom,actual_z),
        "end":(actual_x,top,actual_z),"nPoints":80,
        "requested_C14_x_m":source_probe[0],
        "actual_x_m":actual_x,"actual_z_m":actual_z}
    return {"method":"PRESERVE_C14_METRIC_STATIONS_WHERE_POSSIBLE_3D_MESH_CENTROIDS",
            "requested_C14_probe_m":source_probe,
            "probe_actual_m":probe,
            "mesh_bbox_min_m":lo,"mesh_bbox_max_m":hi,
            "profiles":profiles,
            "warnings":[
              "Exact C14 10/20/30mm heights are preferred only when within 3D metal extents; otherwise report normalized 25/50/75 percent fallback.",
              "A coordinate inside a bounding box does NOT ensure a full chord lies inside a curved 3D mesh: check native profile point counts.",
              "Probe actual point is a native cell-vertex centroid nearest C14 original probe, not the exact original experimental coordinate.",
            ]}


def balanced(source:str,open_pos:int)->int:
    depth=0
    for i in range(open_pos,len(source)):
        if source[i]=="{":depth+=1
        elif source[i]=="}":
            depth-=1
            if depth==0:return i
    raise ValueError("unclosed OpenFOAM diagnostic dictionary block")


def replace_sets(source:str,object_name:str,profiles:list[tuple[str,dict]])->str:
    m=re.search(r"(?m)^\s*"+re.escape(object_name)+r"\s*\{",source)
    need(m is not None,"missing C14 functionObject "+object_name)
    obj_open=source.index("{",m.start())
    obj_end=balanced(source,obj_open)
    body=source[obj_open:obj_end]
    sets=re.search(r"\bsets\s*\{",body)
    need(sets is not None,"missing sets block in "+object_name)
    begin=obj_open+sets.end()-1
    end=balanced(source,begin)
    sections=[]
    for name,p in profiles:
        sections.append("        "+name+"\n        {\n"
                        "            type lineUniform;\n"
                        "            axis "+p["axis"]+";\n"
                        "            start "+vector(p["start"])+";\n"
                        "            end "+vector(p["end"])+";\n"
                        "            nPoints "+str(p["nPoints"])+";\n"
                        "        }")
    return source[:begin+1]+"\n"+"\n\n".join(sections)+"\n    "+source[end:]


def adapt_diagnostic_files(copy:Path,geometry:dict)->dict:
    src=C14/"system"
    names=("functions","researchDiagnostics","lineProfiles",
           "lineProfilesDict","momentumPostProcessing")
    hashes={}
    for name in names:
        payload=src/name
        need(payload.is_file(),"source C14 postprocessing missing "+name)
        hashes[name]=volume.sha(payload)
        shutil.copy2(payload,copy/"system"/name)
    # Edit COPY ONLY, nothing in source.
    f=copy/"system"/"functions"
    txt=f.read_text(encoding="utf-8")
    matcher=r"(\bprobeLocations\s*\(\s*)\([^()]*\)(\s*\)\s*;)"
    txt,count=re.subn(matcher,
                      lambda m:m.group(1)+vector(tuple(geometry["probe_actual_m"]))+
                      m.group(2),txt,count=1,flags=re.S)
    need(count==1,"C14 original temperatureProbe location cannot be safely adapted")
    f.write_text(txt,encoding="utf-8")
    horiz=[(k,geometry["profiles"][k]) for k in
           ("line_y10mm","line_y20mm","line_y30mm")]
    vertical=[("line_x20mm",geometry["profiles"]["line_x20mm"])]
    f=copy/"system"/"lineProfiles"
    txt=f.read_text(encoding="utf-8")
    txt=replace_sets(txt,"horizontalProfiles",horiz)
    txt=replace_sets(txt,"verticalProfiles",vertical)
    f.write_text(txt,encoding="utf-8")
    f=copy/"system"/"momentumPostProcessing"
    txt=f.read_text(encoding="utf-8")
    txt=replace_sets(txt,"momentumHorizontalProfiles",horiz)
    txt=replace_sets(txt,"momentumVerticalProfiles",vertical)
    f.write_text(txt,encoding="utf-8")
    top_src=BASE.parents[2]/"analysis_tools"/"topSurfaceFlowPostProcessing"
    need(top_src.is_file(),"missing actual C14 top-face diagnostic recipe")
    hashes["topSurfaceFlowPostProcessing"]=volume.sha(top_src)
    txt=top_src.read_text(encoding="utf-8")
    top=[("line_topNear",geometry["profiles"]["line_topNear"])]
    txt=replace_sets(txt,"nearTopInternalLine",top)
    (copy/"system"/"topSurfaceFlowPostProcessing").write_text(
        txt,encoding="utf-8")
    return hashes


def run_native(copy:Path,name:str,args:list[str])->dict:
    logfile=copy/("log.C14_3D_postprocess_"+name)
    cmd=["bash","-c",F14_ENV,"c14_3d_offline_postprocess"]+args
    with logfile.open("x",encoding="utf-8") as log:
        result=subprocess.run(cmd,cwd=copy,stdout=log,stderr=subprocess.STDOUT,
                              check=False)
    return {"name":name,"command_without_bootstrap":args,
            "exit_code":result.returncode,
            "passed":result.returncode==0,"log":logfile.name}


def main()->int:
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--case",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    a.add_argument("--analysis",type=Path,default=Path.home()/
                   "OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_ANALYSIS_01")
    a.add_argument("--copy",type=Path,default=Path.home()/("OpenFOAM/"+COPY_NAME))
    a.add_argument("--volume-out",type=Path,default=Path.home()/("OpenFOAM/"+VOLUME_NAME))
    args=a.parse_args()
    copy=args.copy.expanduser().absolute()
    case=args.case.expanduser().resolve()
    analysis=args.analysis.expanduser().resolve()
    vol=args.volume_out.expanduser().absolute()
    try:
        need(case.is_dir() and analysis.is_dir(),
             "authentic 10s CFD and audited 101-state analysis directories required")
        need(not copy.exists() and not copy.is_symlink(),
             "never overwrite an existing native postprocessing copy")
        need(not vol.exists() and not vol.is_symlink(),
             "never overwrite prior volume analysis")
        need(copy!=case and vol!=case and copy!=vol and
             case not in copy.parents and case not in vol.parents,
             "postprocessing output must be isolated from authentic original CFD")
        need(not any(p.is_symlink() for p in case.rglob("*")),
             "input symlinks forbidden: no accidental copy of external CFD artifacts")
        need((case/"system/controlDict").read_bytes()==
             (C14/"system/controlDict").read_bytes(),
             "native C14 original controlDict is not unchanged")
        result=volume.analyze(case,analysis,vol)
        centres=cell_centres(case)
        geom=sample_geometry(centres)
        shutil.copytree(case,copy,symlinks=False)
        # The CFD clone can contain old postProcessing snapshots. Preserve
        # them separately to prevent false positives in new native parity.
        prior=copy/"postProcessing"
        if prior.exists():
            prior.rename(copy/"_original_postProcessing_preserved_unmodified")
        hashes=adapt_diagnostic_files(copy,geom)
        need((copy/"system/controlDict").read_bytes()==
             (C14/"system/controlDict").read_bytes(),
             "original C14 controls changed in postprocess copy")
        steps=[]
        steps.append(run_native(copy,"c14_functions",[
            "foamPostProcess","-region","metal","-dict",
            "system/functions","-time","0:"]))
        steps.append(run_native(copy,"momentum",[
            "foamPostProcess","-region","metal","-dict",
            "system/momentumPostProcessing","-time","0:"]))
        steps.append(run_native(copy,"top_surface",[
            "foamPostProcess","-region","metal","-dict",
            "system/topSurfaceFlowPostProcessing","-time","0:"]))
        steps.append(run_native(copy,"foamLog",[
            "foamLog","log.foamMultiRun"]))
        energy_report={"attempted":True,"passed":False,
                       "physically_validated":False}
        try:
            closure=energy.audit(copy)
            energy_report["passed"]=True
            energy_report["final_relative_nominal_residual"]=(
                closure["final_relative_nominal_closure_residual"])
            energy_report["report"]=str(
                copy/"C3D04_A_C14_NATIVE_ENERGY_AUDIT"/energy.OUT_JSON)
        except (OSError,ValueError,KeyError) as exc:
            energy_report["error"]=str(exc)
        actual=copy/"postProcessing"/"metal"
        dirs=sorted(p.name for p in actual.iterdir() if p.is_dir()) if actual.is_dir() else []
        # Compare output directories only against ACTUALLY written C14 2D output
        # directories. Objects that write time-varying volFields instead of
        # postProcessing/ directories must not be misclassified as failures.
        reference_post=C14/"postProcessing"/"metal"
        need(reference_post.is_dir(),"original C14 postProcessing baseline missing")
        expected={p.name for p in reference_post.iterdir() if p.is_dir()}
        populated={p.name for p in actual.iterdir() if p.is_dir()
                   and any(q.is_file() and q.stat().st_size>0
                           for q in p.rglob("*"))} if actual.is_dir() else set()
        missing=sorted(expected-populated)
        # Some C14 function objects write directly to time/region rather
        # than to a postProcessing directory. Audit those files separately.
        derived=("vorticity","flowType","gradT","magGradT","dTdt",
                 "coolingRate","gradRho","magGradRho","dAlphaLdt",
                 "solidificationRate","latentHeatRateVol","CoCell",
                 "phaseChangeSolidFraction","phaseChangeDarcyCoeff",
                 "phaseChangeModelDeltaT","phaseChangeDarcyAcceleration",
                 "phaseChangeBuoyancyAcceleration","pRghAcceleration",
                 "phaseChangeDragToBuoyancy","phaseChangeDragToPressure")
        derived_found=[k for k in derived if
                       (copy/"10"/"metal"/k).is_file()
                       and (copy/"10"/"metal"/k).stat().st_size>0]
        derived_missing=sorted(set(derived)-set(derived_found))
        info={
            "schema":"C3D04_A_C14_3D_NATIVE_FUNCTION_OBJECT_PARITY_V1",
            "created_utc":datetime.now(timezone.utc).isoformat(),
            "status":"NATIVE_OFFLINE_PARITY_CHECKED_NOT_CFD_RERUN",
            "original_CFD_read_only":str(case),
            "isolated_copy":str(copy),
            "source_log_sha256":result["native_log_sha256"],
            "original_C14_diagnostic_source_hashes":hashes,
            "mesh_based_probe_and_profile_geometry":geom,
            "original_C14_parameters_unchanged":True,
            "solver_CFD_rerun":False,
            "all_native_processing_commands_passed":all(x["passed"] for x in steps),
            "steps":steps,
            "native_energy_closure_audit":energy_report,
            "native_postprocessing_object_dirs":dirs,
            "missing_expected_C14_object_dirs":missing,
            "derived_C14_fields_at_final_time":derived_found,
            "missing_derived_C14_fields_at_final_time":derived_missing,
            "all_original_C14_function_objects_observed":not missing and not derived_missing,
            "energy_conservation_verified":False,
            "QuickCup_validation":False,
            "phase_rate_at_each_0_001s_recovered":False,
            "parity_complete":False,
            "limits":[
                "A function-object directory name alone is not numeric acceptance; each output requires physical and numerical audit.",
                "Spatial sample geometry differs from the original 2D C14 coordinates and requires 3D native inside-mesh/output checks.",
                "ddt over 0.1s snapshots cannot be represented as true 0.001s in-run diagnostics.",
                "Even success of native offline commands does not imply energy closure, independent mesh, or experiment validated.",
            ],
        }
        report=copy/"C3D04_A_C14_NATIVE_POSTPROCESS_REPORT.json"
        report.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n",
                          encoding="utf-8")
        print(json.dumps({
            "native_commands_all_passed":info["all_native_processing_commands_passed"],
            "object_dirs":len(dirs),
            "missing_C14_objects":missing,
            "missing_derived_fields":derived_missing,
            "energy_conservation_verified":False,
            "native_energy_audit_passed":energy_report["passed"],
            "new_CFD_run":False,
            "volume_report":str(vol/"C3D04_A_C14_3D_POSTPROCESS_REPORT.json"),
            "native_report":str(report),
        },ensure_ascii=False,indent=2))
        return 0 if info["all_native_processing_commands_passed"] and energy_report["passed"] and not missing and not derived_missing else 3
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("C14_NATIVE_3D_POSTPROCESS_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
