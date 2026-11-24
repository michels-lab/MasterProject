#!/usr/bin/env python3
"""Grouped F14 C14-A offline recovery; no original CFD or mesh changes."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import sys

import probe_c14_native_f14_single_vs_multi_time as probe
import run_c14_stage07_solver_backed_recovery as recovery
import run_c14_3d_complete_postprocess as old
import stage_c14_3d_case_a as stage

REPORT = "C3D04_A_C14_GROUPED_NATIVE_RECOVERY.json"
H = "volIntegrate(rho,h)"
TIMES = [i/10 for i in range(101)]
SELECTED = [0., .1, 10.]
PATTERN = re.compile(rb"(?m)^([ \t]*cellZone[ \t]+)metal([ \t]*;)")

def need(ok, message):
    if not ok:
        raise ValueError(message)

def replace_selection(original):
    changed, n = PATTERN.subn(rb"\g<1>all\g<2>", original)
    need(n == 1, "expected exactly one active cellZone metal entry")
    return changed

def scalar_table(path, column, expected):
    need(path.is_file() and not path.is_symlink(), "missing table: "+str(path))
    header = None
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Time"):
            need(header is None, "duplicate header: "+str(path))
            header = line[1:].split()
        elif line.strip() and not line.lstrip().startswith("#"):
            need(header is not None, "missing header: "+str(path))
            parts = line.split()
            need(len(parts)==len(header), "column mismatch: "+str(path))
            values = [float(x) for x in parts]
            need(all(math.isfinite(x) for x in values), "nonfinite table: "+str(path))
            rows.append(dict(zip(header,values)))
    need(header is not None and column in header and len(rows)==len(expected),
         "incomplete native table: "+str(path))
    need(all(math.isclose(r["Time"],t,rel_tol=0,abs_tol=1e-8)
             for r,t in zip(rows,expected)), "wrong native time axis: "+str(path))
    return [r[column] for r in rows]

def compare(got, expected):
    need(len(got)==len(expected), "reference count mismatch")
    need(all(math.isfinite(a) and math.isfinite(b) and
             math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-6)
             for a,b in zip(got,expected)), "native enthalpy equivalence failed")
    return {"reference_J":expected,"grouped_J":got,
            "absolute_differences_J":[abs(a-b) for a,b in zip(got,expected)]}

def reference_values(source, directory):
    report = recovery.read_json(directory/probe.REPORT)
    need(report["schema"]=="C3D04_A_F14_NATIVE_MULTITIME_VS_STANDALONE_V1"
         and report["source_run_read_only"]==str(source)
         and report["isolated_minimal_probe_out"]==str(directory)
         and report["mesh_cells_metal"]==8960
         and report["source_SHA256_unchanged"]
         and report["verdict"]=="REPRODUCED_NATIVE_MULTITIME_REGISTRY_FAILURE_IN_SAME_SAVED_C14_FIELDS",
         "real WSL reference provenance mismatch")
    results=report["trial_results"]
    need(len(results)==4 and results[3]["foam_fatal_occurrence_count"]==2,
         "missing controlled failure evidence")
    values=[]
    for label,time,item in zip(probe.TIME_TRIALS[:3],SELECTED,results[:3]):
        need(item["label"]==label and item["native_semantic_success"]
             and not item["foam_fatal_present"], "invalid standalone reference")
        log=directory/item["log"]
        need(log.resolve().is_relative_to(directory) and recovery.sha(log)==item["log_sha256"],
             "reference native log hash mismatch")
        root=directory/label
        for rel in ("system/controlDict","constant/metal/fvModels",
                    "constant/metal/polyMesh/cellZones"):
            need(recovery.sha(root/rel)==recovery.sha(source/rel),
                 "reference model mismatch: "+rel)
        name=next(iter(item["native_rho_h_tables"]))
        table=root/name
        need(table.resolve().is_relative_to(root), "reference table escaped clone")
        values.extend(scalar_table(table,H,[time]))
    return values

def run(copy, label, dictionary, selector, solver=True, fields=None):
    args=["foamPostProcess","-region","metal"]
    if solver:
        args+=["-solver","fluid"]
    else:
        args+=["-fields",fields]
    args+=["-dict","system/"+dictionary.name,"-time",selector]
    item=old.run_native(copy,label,args)
    fatal=recovery.fatal_openfoam_log(copy/item["log"])
    return {**item,**fatal,"passed":item["exit_code"]==0 and not fatal["foam_fatal_present"]}

def snapshot_hashes(source):
    paths=[source/"log.foamMultiRun"]
    for name in ("constant","system",*[str(i//10) if i%10==0 else str(i/10) for i in range(101)]):
        root=source/name
        need(root.is_dir() and not root.is_symlink(), "missing source directory: "+name)
        for p in sorted(root.rglob("*")):
            need(not p.is_symlink(), "unexpected source symlink: "+str(p))
            if p.is_file():
                paths.append(p)
    return {str(p.relative_to(source)):recovery.sha(p) for p in paths}

def execute(source, reference, out):
    source=source.expanduser().resolve()
    reference=reference.expanduser().resolve()
    out=out.expanduser().absolute()
    need(not out.exists() and not out.is_symlink(), "output occupied; preserve it")
    need(out.parent.is_dir() and out.parent.resolve()==source.parent,
         "output must be a new sibling of original CFD")
    need(out!=source and out!=reference and not out.is_relative_to(reference),
         "output overlaps evidence")
    need(not out.is_relative_to(Path(__file__).resolve().parents[3]),"output inside repository")
    need(recovery.sha(source/"system/controlDict")==recovery.sha(recovery.C14/"system/controlDict"),
         "source controlDict differs from C14")
    need(stage.region_cells(source,"metal",8960)["nCells"]==8960 and
         stage.audit_existing_zone(source/"constant/metal/polyMesh/cellZones",8960),
         "original zone does not select every metal cell")
    expected=reference_values(source,reference)
    before=snapshot_hashes(source)
    names=[str(i//10) if i%10==0 else str(i/10) for i in range(101)]
    for t in names:
        need(all((source/t/"metal"/f).is_file() for f in ("T","U","phaseChangeSource:alpha1")),
             "missing genuine saved state "+t)
    out.mkdir()
    result={"schema":"C3D04_A_GROUPED_OFFLINE_V1","stage":"07/10",
            "milestones_done":"6/10","source":str(source),"reference":str(reference),
            "copy":str(out),"source_solver_rerun":False,"global_energy_conservation_verified":False,
            "quickcup_validated":False,"native_runtime_ddt_recovered":False,
            "native_0p001s_probe_history_recovered":False,"groups":{}}
    try:
        for name in ("constant","system",*names):
            shutil.copytree(source/name,out/name)
        model=out/"constant/metal/fvModels"
        original=model.read_bytes()
        changed=replace_selection(original)
        model.write_bytes(changed)
        need(model.read_bytes()==changed,"copy-only model edit mismatch")
        result["offline_only_selection"]={"original":"metal","copy":"all",
            "original_sha256":before["constant/metal/fvModels"],
            "copy_sha256":recovery.sha(model),"all_metal_cells":8960}
        geometry=old.sample_geometry(old.cell_centres(out))
        result["geometry"]=geometry
        result["diagnostic_source_hashes"]=old.adapt_diagnostic_files(out,geometry)
        gate=out/"system/stage07GroupedEquivalence"
        block=recovery.selected_source_block(
            (recovery.C14/"system/researchDiagnostics").read_text(encoding="utf-8"),
            "metalSensibleEnthalpy")
        gate.write_text('FoamFile\n{\n format ascii;\n class dictionary;\n object stage07GroupedEquivalence;\n}\n'+block,encoding="utf-8")
        result["equivalence_run"]=run(out,"groupedEquivalence",gate,"0,0.1,10")
        need(result["equivalence_run"]["passed"],"grouped equivalence native failure")
        table=out/"postProcessing/metal/metalSensibleEnthalpy/0/volFieldValue.dat"
        result["equivalence"]=compare(scalar_table(table,H,SELECTED),expected)
        (out/"postProcessing").rename(out/"_equivalence_postProcessing_preserved")
        for group in recovery.TASK_ORDER:
            dictionary, provenance=recovery.assembled_dict(out,group)
            solver=group not in ("phase","profiles")
            fields="(phaseChangeSource:alpha1)" if group=="phase" else "(U T p_rgh phaseChangeSource:alpha1)"
            result["groups"][group]=run(out,"grouped_"+group,dictionary,"0:",solver,fields)
            result["groups"][group]["objects"]=provenance
        result["groups"]["top_surface"]=run(out,"grouped_top_surface",
            out/"system/topSurfaceFlowPostProcessing","0:")
        result["surface_energy"]=recovery.surface_energy_summary(out)
        result["profile_coverage_at_10s"]=old.profile_coverage(out)
        series={}
        for name,column,filename in [
            ("metalSensibleEnthalpy",H,"volFieldValue.dat"),
            ("metalMeanLiquidFraction","volAverage(phaseChangeSource:alpha1)","volFieldValue.dat"),
            *[(n,"sum(energyFlux)","surfaceFieldValue.dat") for n in
              ("metalTopEnergyPower","metalMoldEnergyPower","metalBoundaryEnergyPower")]]:
            path=out/"postProcessing/metal"/name/"0"/filename
            try:
                v=scalar_table(path,column,TIMES)
                series[name]={"rows":len(v),"pass":True,"sha256":recovery.sha(path)}
                if name=="metalSensibleEnthalpy":
                    result["full_series_equivalence"]=compare([v[i] for i in (0,1,100)],expected)
            except (OSError,ValueError,KeyError) as exc:
                series[name]={"pass":False,"error":str(exc)}
        result["scalar_series"]=series
        result["status"]="GROUPED_POSTPROCESS_ATTEMPT_COMPLETE"
        result["all_groups_without_fatal"]=all(x["passed"] for x in result["groups"].values())
        result["all_required_scalar_series_101"]=all(x["pass"] for x in series.values())
        result["all_final_profiles_80"]=all(x["status"]=="PASS" for x in result["profile_coverage_at_10s"].values())
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        result["status"]="GROUPED_RECOVERY_BLOCKED_PRESERVED"
        result["error"]=str(exc)
    finally:
        result["source_hashes_unchanged"]=snapshot_hashes(source)==before
        result["copy_controlDict_unchanged"]=recovery.sha(out/"system/controlDict")==before["system/controlDict"] if (out/"system/controlDict").is_file() else False
        if not result["source_hashes_unchanged"] or not result["copy_controlDict_unchanged"]:
            result["status"]="SOURCE_OR_COPY_INTEGRITY_FAILURE"
        (out/REPORT).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    home=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,default=home/"C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    p.add_argument("--reference",type=Path,default=home/"C3D04_A_C14_F14_THREE_TIME_ISOLATION_PROBE_01")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        result=execute(a.case,a.reference,a.out)
        brief={k:v for k,v in result.items() if k not in ("groups","geometry","diagnostic_source_hashes")}
        brief["group_pass"]={k:v["passed"] for k,v in result["groups"].items()}
        brief["report"]=str(a.out/REPORT)
        print(json.dumps(brief,indent=2))
        return 0 if result["status"]=="GROUPED_POSTPROCESS_ATTEMPT_COMPLETE" else 2
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print("GROUPED_RECOVERY_BLOCKED:",exc,file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
