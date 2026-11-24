#!/usr/bin/env python3
"""Complete recoverable C14-style *OFFLINE* postprocessing for existing B 10 s.

Use real 101 saved original C14-B CFD snapshots, never foamMultiRun or remesh.
Create one physically independent multi-region workspace with full COPY of
mesh, dictionaries, and native saved fields. OpenFOAM can safely write derived
fields there. Run selected original C14 Foundation14 functionObjects, probes,
horizontal/vertical profiles, thermal gradients, flow topology, density and
Courant summaries, top flow, momentum (where possible), foamLog, then open
ParaView. Every stage has a separate log and incomplete stages are identified.

NOT possible offline: original dt=.001s histories of probes, ddt(T/alpha1)
at every CFD step, native fvModels latent source inside original solver. Do
not substitute 101 saved samples and call them exact solver-step data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
C14=REPO/"cases_controlled_buoyancy/C14_topFixedFlux_explicitRef"
TOP=REPO/"analysis_tools/topSurfaceFlowPostProcessing"
ORIGINAL=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
WORK=Path.home()/"OpenFOAM/C3D05_B_C14_POSTPROCESAMIENTO_C14_101_TIEMPOS_01"
REPORT="C3D05_B_C14_C14_STYLE_POSTPROCESS_REPORT.json"
SOLVERLOG="log.foamMultiRun.C3D05_B_C14_10S"
STATE="CASE_B_C14_OFFLINE_101_SAVED_STATES_NO_CFD_RERUN"
TIME_RE=re.compile(r"\d+(?:\.\d+)?")
BASIC=("T","U","p_rgh","phaseChangeSource:alpha1")
RHO=("T","U","p_rgh","rho","phaseChangeSource:alpha1")
C14_RESEARCH={
    "velocity":("vorticityField","flowTopology"),
    "thermal":("temperatureGradient","temperatureGradientMagnitude"),
    "phase_summary":("metalMeanLiquidFraction",),
    "thermal_max":("metalMaxThermalGradient",),
    "density_gradient":("densityGradient","densityGradientMagnitude"),
    "density_courant":("cellCourantNumber","metalMaxCourant"),
    "density_summary":("metalMaxDensityGradient","metalTopPhiSum"),
    "energy_optional":(
        "energyAdvectiveFlux","heatFlux","energyFlux",
        "metalTopEnergyPower","metalMoldEnergyPower",
        "metalBoundaryEnergyPower","metalSensibleEnthalpy",
    ),
}
# Runtime-only C14 objects excluded deliberately, not silently approximated:
RUNTIME_ONLY={
    "temperatureTimeDerivative","coolingRate",
    "liquidFractionTimeDerivative","solidificationRate",
    "latentHeatField","latentHeatRateDensity","metalLatentHeatPower",
    "metalMeanCoolingRate","metalMeanSolidificationRate",
    "solidificationMeltingMomentumDiagnostics",
}
FIELD_OUTPUTS=("vorticity","flowType","gradT","magGradT","gradRho","magGradRho","CoCell")


def need(ok,why):
    if not ok:
        raise ValueError("POSTPRO_C14_B_EXISTENTE_BLOQUEADO: "+str(why))


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as fd:
        while part:=fd.read(1024*1024):
            h.update(part)
    return h.hexdigest()


def existing_states(source):
    need(source.is_dir() and source.name==ORIGINAL.name and
         not source.is_symlink(),"falta CFD original aceptado, no usar otro caso")
    need((source/"system/controlDict").is_file(),"falta controlDict original")
    need((source/"10/metal/T").is_file() and
         (source/"10/mold/T").is_file(),"no hay CFD C14 original terminado a 10 s")
    need((source/SOLVERLOG).is_file(),"falta log original 10s completado")
    require_report=source/"C3D05_B_C14_FLUID_SOLID_STAGE_REPORT.json"
    need(require_report.is_file(),"falta reporte del C14 original 3D-B")
    report=json.loads(require_report.read_text(encoding="utf-8"))
    need(report.get("status")==
         "C3D05_B_C14_ORIGINAL_FLUID_SOLID_FULL_10S_NATIVE_COMPLETED_NOT_PHYSICALLY_VALIDATED",
         "original no declarado CFD F14 completo")
    saved=sorted([(float(p.name),p.name) for p in source.iterdir()
                 if p.is_dir() and not p.is_symlink() and TIME_RE.fullmatch(p.name)])
    need(len(saved)==101 and len({i for i,n in saved})==101 and
         all(abs(t-i*.1)<1e-8 for i,(t,n) in enumerate(saved)),
         "se requieren 101 tiempos originales 0..10 con paso guardado .1 s")
    for _,name in saved:
        for region in ("metal","mold"):
            need((source/name/region/"T").is_file(),
                 "falta temperatura original "+name+"/"+region)
    need((source/"system/controlDict").read_bytes()==
         (C14/"system/controlDict").read_bytes(),
         "controlDict original Caso B ya no coincide con fuente C14")
    return saved,report


def object_blocks(path,names):
    """Read exact ORIGINAL F14 FO blocks by name; no other objects loaded."""
    s=path.read_text(encoding="utf-8")
    blocks={}
    for name in names:
        m=re.search(r"(?m)^"+re.escape(name)+r"\s*\n\s*\{",s)
        need(m is not None,"falta objeto de funcion C14 original: "+name)
        begin=s.index("{",m.start())
        level=0
        stop=None
        for i in range(begin,len(s)):
            if s[i]=="{":
                level+=1
            elif s[i]=="}":
                level-=1
                if level==0:
                    stop=i+1
                    break
        need(stop is not None,"diccionario C14 sin cierre "+name)
        blocks[name]=s[m.start():stop].strip()+"\n"
    return blocks


def fo_dict(path,blocks):
    header=(
        "FoamFile\n{\n"
        "    version 2.0;\n"
        "    format ascii;\n"
        "    class dictionary;\n"
        "    object "+path.name+";\n"
        "}\n\n"
    )
    path.write_text(header+"\n".join(blocks),encoding="utf-8")


def profile_block(name,original,fields):
    """Same C14 original 10/20/30mm and vertical 20mm/5mm sample lines.

    Only fields actually available in archived native CFD are requested.
    Absent/partial spatial samples are reported to user, never called
    full same fidelity when C14 2D coordinates miss B 3D geometry.
    """
    marker=re.search(r"\bfields\s*\(",original)
    need(marker is not None,"no fields in C14 "+name)
    start=original.index("(",marker.start())
    end=original.find(")",start)
    need(end>start,"malformed original C14 profile fields")
    text=original[:start+1]+"\n        "+"\n        ".join(fields)+"\n    "+original[end:]
    return text


def probe_block(source,fields):
    txt=object_blocks(source,("temperatureProbe",))["temperatureProbe"]
    marker=re.search(r"\bfields\s*\(",txt)
    need(marker is not None,"no original C14 probe fields")
    left=txt.index("(",marker.start())
    right=txt.find(")",left)
    need(right>left,"malformed C14 original probes")
    return txt[:left+1]+"\n        "+"\n        ".join(fields)+"\n    "+txt[right:]


def stage(source,work,saved):
    need(not work.exists() and not work.is_symlink(),"no sobreescribir postproceso previo")
    need(work!=source and work not in source.parents and source not in work.parents,
         "prohibido postprocesar dentro del CFD original")
    for sub in ("0","constant","system"):
        need(not any(p.is_symlink() for p in (source/sub).rglob("*")),
             "origen contiene symlinks; no arriesgar escritura contra CFD")
    work.parent.mkdir(parents=True,exist_ok=True)
    temp=work.parent/("."+work.name+".INCOMPLETE")
    need(not temp.exists(),"ya existe trabajo anterior INCOMPLETE: "+str(temp))
    temp.mkdir()
    try:
        for name in ("constant","system"):
            shutil.copytree(source/name,temp/name,symlinks=False)
        for _,name in saved:
            shutil.copytree(source/name,temp/name,symlinks=False)
        shutil.copy2(source/SOLVERLOG,temp/"log.foamMultiRun")
        fo=temp/"system"/"C14_B_OFFLINE"
        fo.mkdir()
        # A source case may already contain system/functions. We preserve
        # that unmodified INSIDE the copy but disable its implicit loading:
        # only our selected, explicit offline -dict objects may run.
        userfunctions=temp/"system"/"functions"
        if userfunctions.is_file():
            userfunctions.rename(fo/"PRESERVED_INPUT_system_functions")
        original_hashes={}
        for n in ("functions","researchDiagnostics","lineProfiles","momentumPostProcessing"):
            src=C14/"system"/n
            need(src.is_file(),"falta C14 original "+n)
            original_hashes[n]=sha(src)
            shutil.copy2(src,fo/("ORIGINAL_"+n))
        need(TOP.is_file(),"falta topSurfaceFlow original")
        original_hashes["topSurfaceFlowPostProcessing"]=sha(TOP)
        shutil.copy2(TOP,fo/"ORIGINAL_topSurfaceFlowPostProcessing")
        s=C14/"system"/"researchDiagnostics"
        for group,names in C14_RESEARCH.items():
            fo_dict(fo/("C14_B_"+group),list(object_blocks(s,names).values()))
        line=C14/"system"/"lineProfiles"
        lines=object_blocks(line,("horizontalProfiles","verticalProfiles"))
        # Original C14 spatial stations and nPoints preserved; choose
        # universally present native fields for 101 saved states.
        basic_profiles=[profile_block(k,lines[k],BASIC) for k in lines]
        fo_dict(fo/"C14_B_profiles",basic_profiles)
        rho_profiles=[profile_block(k,lines[k],RHO) for k in lines]
        fo_dict(fo/"C14_B_profiles_rho",rho_profiles)
        funcs=C14/"system"/"functions"
        fo_dict(fo/"C14_B_probe_101", [probe_block(funcs,BASIC)])
        fo_dict(fo/"C14_B_probe_rho_100", [probe_block(funcs,RHO)])
        # Original C14 top-surface numerical face flux actions selected; this
        # group requires rho/phi, so t=0 is NOT processed.
        top_names=("topPatchFaceFields","topPhiNet","topPhiAbsolute",
                   "topPhiMinimum","topPhiMaximum","nearTopInternalLine")
        topo=object_blocks(TOP,top_names)
        fo_dict(fo/"C14_B_topSurface",list(topo.values()))
        # Original C14 momentum FO requires replay solver/model fields; no
        # simulated native source-term data is fabricated, optional stage.
        shutil.copy2(C14/"system"/"momentumPostProcessing",
                     fo/"C14_B_momentum")
        marker=temp/"C3D05_B_C14_POSTPROCESADO_101_TIEMPOS.foam"
        marker.touch()
        initial={
            "status":STATE,
            "original_CFD_readonly":str(source),
            "output":str(work),
            "original_saved_times":101,
            "original_solver_dt_s":.001,
            "saved_field_dt_s":.1,
            "original_solver_rerun":False,
            "sample_locations_C14_2D_original_not_geometry_adjusted":True,
            "reference_C14_FO_SHA256":original_hashes,
            "source_controlDict_SHA256":sha(source/"system/controlDict"),
            "source_solver_log_SHA256":sha(source/SOLVERLOG),
            "source_10_metal_T_SHA256":sha(source/"10/metal/T"),
            "runtime_only_original_C14_objects_unrecoverable_sorted":
                sorted(RUNTIME_ONLY),
            "native_function_output_not_assumed_present":True,
            "stages":{},
            "original_solved_fields_untouched":True,
            "physical_energy_conservation_verified":False,
            "model_contraction_validated":False,
            "quickcup_or_JMatPro_validated":False
        }
        (temp/REPORT).write_text(json.dumps(initial,indent=2)+"\n")
        need(not work.exists(),"salida creada simultáneamente")
        temp.rename(work)
        return initial
    except BaseException:
        print("Se preserva copia de posprocesamiento incompleta: "+str(temp),
              file=sys.stderr)
        raise


def native(work,stage_name,dict_name,time_label,fields):
    """One standalone native Foundation14 postprocess, logfile and return code."""
    log=work/("log.C14B."+stage_name)
    done=work/("log.C14B."+stage_name+".DONE")
    if done.is_file():
        return {"name":stage_name,"result":"PREVIOUSLY_COMPLETED",
                "exit_code":0,"log":str(log)}
    if log.exists():
        # Never overwrite a failed native OpenFOAM log. Continue with all
        # independent remaining stages, including on --resume.
        return {"name":stage_name,"result":"PREVIOUS_INCOMPLETE_LOG_PRESERVED",
                "log":str(log),"exit_code":None}
    cmd=["foamPostProcess","-case",str(work),"-region","metal",
         "-dict",str(work/"system/C14_B_OFFLINE"/dict_name),
         "-time",time_label]
    if fields:
        cmd.extend(["-fields","("+" ".join(fields)+")"])
    print("OPENFOAM C14 B: "+stage_name+" ("+time_label+")",flush=True)
    with log.open("x",encoding="utf-8") as out:
        process=subprocess.run(cmd,cwd=work,stdout=out,
                               stderr=subprocess.STDOUT,check=False)
    if process.returncode==0:
        done.touch()
    else:
        print("Etapa parcial "+stage_name+"; revisa "+str(log),flush=True)
        # Do not conceal source failure or call this output a real native field.
    return {"name":stage_name,"result":"COMPLETE" if process.returncode==0
            else "NATIVE_OPENFOAM_ERROR","exit_code":process.returncode,
            "log":str(log),"cmd":cmd}


def run_foam_log(work):
    log=work/"log.C14B.foamLog"
    done=work/"log.C14B.foamLog.DONE"
    if done.is_file():
        return {"name":"foamLog","result":"PREVIOUSLY_COMPLETED"}
    if log.exists():
        return {"name":"foamLog","result":"INCOMPLETE_LOG_PRESERVED",
                "log":str(log)}
    with log.open("x",encoding="utf-8") as dest:
        result=subprocess.run(["foamLog","log.foamMultiRun"],cwd=work,
                              stdout=dest,stderr=subprocess.STDOUT,check=False)
    if result.returncode==0:
        done.touch()
    return {"name":"foamLog","result":"COMPLETE" if result.returncode==0
            else "NATIVE_OPENFOAM_ERROR","exit_code":result.returncode,
            "log":str(log)}


def audit_outputs(work):
    post=work/"postProcessing"
    summaries={}
    if post.is_dir():
        for p in sorted(post.rglob("*")):
            if p.is_dir() and p.parent==post:
                summaries[p.name]=sum(1 for z in p.rglob("*") if z.is_file())
            elif p.is_dir() and p.parent.name=="metal":
                summaries["metal/"+p.name]=sum(
                    1 for z in p.rglob("*") if z.is_file())
    found={}
    for name in FIELD_OUTPUTS:
        found[name]=sum(1 for p in work.iterdir()
                        if p.is_dir() and TIME_RE.fullmatch(p.name)
                        and (p/"metal"/name).is_file())
    return {"postProcessing_folders_and_file_counts":summaries,
            "actual_derived_fields_saved_count_101":found}


def finish(work,doc,steps):
    # The original CFD and its 101 data states are NEVER edited.
    doc["stages"]={s["name"]:s for s in steps}
    doc["outcomes"]=audit_outputs(work)
    doc["updated_utc"]=datetime.now(timezone.utc).isoformat()
    doc["failed_or_unavailable_stages"]=[s["name"] for s in steps
              if s.get("result") not in ("COMPLETE","PREVIOUSLY_COMPLETED")]
    doc["all_recoverable_stages_native_success"]=not doc[
        "failed_or_unavailable_stages"]
    doc["probe_101_data_points_are_saved_time_only_NOT_solver_10000_steps"]=True
    doc["original_C14_0_001s_temporal_probes_recovered"]=False
    doc["original_energy_flux_conservation_physically_verified"]=False
    doc["original_C14_solver_fvModels_source_integrated"]=False
    (work/REPORT).write_text(json.dumps(doc,indent=2,ensure_ascii=False)+"\n",
                             encoding="utf-8")
    print(json.dumps({
        "status":STATE,
        "output":str(work),
        "ParaView_foam":str(work/"C3D05_B_C14_POSTPROCESADO_101_TIEMPOS.foam"),
        "stage_statuses":{s["name"]:s["result"] for s in steps},
        "derived_fields_saved":doc["outcomes"][
            "actual_derived_fields_saved_count_101"],
        "postProcessing_folders":doc["outcomes"][
            "postProcessing_folders_and_file_counts"],
        "unavailable_stages":doc["failed_or_unavailable_stages"],
        "solver_reexecuted":False,
        "original_C14_1ms_probes_recovered":False,
    },indent=2,ensure_ascii=False),flush=True)
    return doc


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",type=Path,default=ORIGINAL)
    parser.add_argument("--out",type=Path,default=WORK)
    parser.add_argument("--no-open",action="store_true",
                        help="no abrir ParaView después del posprocesamiento")
    parser.add_argument("--resume",action="store_true",
                        help="continuar etapas no ejecutadas en copia existente")
    args=parser.parse_args()
    try:
        source=args.case.expanduser().absolute()
        work=args.out.expanduser().absolute()
        saved,_=existing_states(source)
        need(os.environ.get("WM_PROJECT_VERSION")=="14",
             "activa OpenFOAM Foundation14 antes de ejecutar")
        need(shutil.which("foamPostProcess") and shutil.which("foamLog"),
             "falta foamPostProcess/foamLog Foundation14")
        # Count real rho/phi on the actual saved labels, never infer from a
        # 100/101 summary which exact time is absent.
        rho_phi_times=[(t,n) for t,n in saved
                       if all((source/n/"metal"/name).is_file()
                              for name in ("rho","phi"))]
        rho_phi_on_all_saved_after_t0=(
            len(rho_phi_times)==100 and
            len([t for t,n in rho_phi_times if t>0])==100 and
            all(abs(t-i*.1)<1e-8 for i,(t,n)
                in enumerate(rho_phi_times,1))
        )
        if args.resume:
            need(work.is_dir() and (work/REPORT).is_file(),
                 "no existe copia previa para reanudar")
            doc=json.loads((work/REPORT).read_text())
            need(doc.get("original_CFD_readonly")==str(source) and
                 doc.get("status")==STATE,"copia no corresponde a este CFD")
        else:
            doc=stage(source,work,saved)
        steps=[]
        # Source selected from ORIGINAL C14 objects, not new invented fluid
        # models; basic fields available even at t=0.
        steps.append(native(work,"01_velocity","C14_B_velocity","0:10",BASIC))
        steps.append(native(work,"02_thermal","C14_B_thermal","0:10",BASIC))
        steps.append(native(work,"03_phase_summary","C14_B_phase_summary","0:10",BASIC))
        steps.append(native(work,"04_thermal_max","C14_B_thermal_max","0:10",BASIC))
        steps.append(native(work,"05_probes_101","C14_B_probe_101","0:10",BASIC))
        steps.append(native(work,"06_profiles_101","C14_B_profiles","0:10",BASIC))
        # rho and phi were archived only for 100 snapshots; never invent t0.
        if rho_phi_on_all_saved_after_t0:
            steps.append(native(work,"07_density_gradient","C14_B_density_gradient","0.1:10",
                                ("rho","phi","U")))
            steps.append(native(work,"08_density_courant","C14_B_density_courant","0.1:10",
                                ("rho","phi","U")))
            steps.append(native(work,"09_density_summary","C14_B_density_summary","0.1:10",
                                ("rho","phi","U")))
            steps.append(native(work,"10_probes_rho","C14_B_probe_rho_100","0.1:10",RHO))
            steps.append(native(work,"11_profiles_rho","C14_B_profiles_rho","0.1:10",RHO))
            steps.append(native(work,"12_topSurface","C14_B_topSurface","0.1:10",RHO+("phi",)))
        else:
            for label in ("07_density_gradient","08_density_courant",
                          "09_density_summary","10_probes_rho","11_profiles_rho",
                          "12_topSurface"):
                steps.append({"name":label,
                              "result":"UNAVAILABLE_NONCONTIGUOUS_OR_MISSING_RHO_PHI",
                              "available_joint_rho_phi_times":[x for x,n in rho_phi_times]})
        # These optional original C14 objects need transport h or native
        # momentum fvModels not archived. Try only on real rho/phi snapshots;
        # they are NOT grounds to call a partial postprocess complete.
        if rho_phi_on_all_saved_after_t0:
            steps.append(native(work,"13_energy_optional","C14_B_energy_optional",
                                "0.1:10",RHO+("phi",)))
            steps.append(native(work,"14_momentum_optional","C14_B_momentum",
                                "0.1:10",RHO+("phi",)))
        else:
            steps.extend(({"name":"13_energy_optional","result":"UNAVAILABLE_RHO_PHI"},
                          {"name":"14_momentum_optional","result":"UNAVAILABLE_RHO_PHI"}))
        steps.append(run_foam_log(work))
        finish(work,doc,steps)
        if not args.no_open:
            executable=shutil.which("paraview")
            if executable:
                subprocess.run([executable,"--data="+str(
                    work/"C3D05_B_C14_POSTPROCESADO_101_TIEMPOS.foam")],
                    check=False)
            else:
                print("Abre el .foam impreso en la salida desde ParaView.",flush=True)
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as e:
        print("CASO_B_C14_POSTPROCESS_ERROR: "+str(e),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
