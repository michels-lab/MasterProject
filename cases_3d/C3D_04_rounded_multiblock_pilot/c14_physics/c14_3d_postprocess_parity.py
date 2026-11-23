#!/usr/bin/env python3
"""Postprocesamiento volumétrico 3D-A del C14 ORIGINAL, sin volver a correr CFD.

Lee EXCLUSIVAMENTE los 101 estados 0..10 s existentes y el informe nativo
previo. Calcula integrales por volumen de T, fracción líquida, umbrales,
velocidad y variaciones aproximadas de energía sensible/latente. Audita el
inventario exacto de functionObjects de C14 para exigir paridad pendiente.
NO edita el caso, NO toca su controlDict, NO ejecuta foamMultiRun, NO concluye
conservación de energía ni validación experimental; no reconstruye 10,001 probes.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from datetime import datetime, timezone

import analyze_existing_c14_3d_results as native
import stage_c14_3d_case_a as stage

BASE = Path(__file__).resolve().parent
CONTRACT = BASE / "C14_3D_PHYSICS_CONTRACT.json"
REFERENCE = stage.physics.C14
ANALYSIS_CSV = "C3D04_A_C14_10S_TIME_SERIES.csv"
ANALYSIS_JSON = "C3D04_A_C14_10S_DIAGNOSTICS.json"
REQUIRED_STATUS = "EXISTING_REAL_V4_T02_C14_10S_FIELDS_AND_LOG_AUDITED_NOT_PHYSICALLY_VALIDATED"
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
VECTOR = re.compile(r"\(\s*("+NUM+r")\s+("+NUM+r")\s+("+NUM+r")\s*\)")
FIELDS = ("T","phaseChangeSource:alpha1","U","p_rgh")
CSV_COLUMNS = (
    "time_s","metal_volume_m3","mold_volume_m3",
    "metal_T_volMean_K","mold_T_volMean_K",
    "metal_alpha1_volMean","metal_solid_fraction_volMean",
    "metal_below_Tliq_volume_percent","metal_below_Tsol_volume_percent",
    "metal_mean_speed_m_s","metal_max_speed_m_s","metal_rms_speed_m_s",
    "metal_p_rgh_volMean_Pa",
    "metal_sensible_delta_J","metal_latent_inventory_delta_J",
    "mold_sensible_delta_J","combined_estimated_stored_energy_delta_J",
    "saved_interval_metal_cooling_K_per_s",
    "saved_interval_alpha1_decrease_per_s",
    "saved_interval_latent_inventory_change_W",
)


def ensure(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError("C14_3D_PARITY_BLOCKED: "+msg)


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def label_values(path: Path) -> list[int]:
    ensure(path.is_file() and not path.is_symlink(),
           "missing/unsafe mesh labelList "+str(path))
    raw=path.read_text(encoding="utf-8")
    meta=re.search(r"\bFoamFile\s*\{[^{}]*\}",raw,re.S)
    ensure(meta is not None and re.search(r"\bclass\s+labelList\s*;",meta.group(0)),
           "not an ASCII OpenFOAM labelList "+str(path))
    m=re.match(r"\s*(\d+)\s*(?:\{\s*(\d+)\s*\}|\(\s*([\d\s]*)\))",
               raw[meta.end():],re.S)
    ensure(m is not None,"malformed native polyMesh list "+str(path))
    count=int(m.group(1))
    if m.group(2) is not None:
        data=[int(m.group(2))]*count
    else:
        data=[int(n) for n in (m.group(3) or "").split()]
    ensure(len(data)==count and all(n>=0 for n in data),
           "native labelList count/negative labels "+str(path))
    return data


def cell_volumes(case: Path, region: str, expected: int) -> list[float]:
    """Face-wise signed tetrahedra: + owner, - neighbour on internal faces."""
    from math import fsum
    root=case/"constant"/region/"polyMesh"
    pts=stage.gate.load_points(root/"points")
    faces=stage.gate.load_faces(root/"faces")
    owners=label_values(root/"owner")
    neighbours=label_values(root/"neighbour")
    ensure(len(faces)==len(owners) and len(neighbours)<len(owners),
           "faces/owner/neighbour mismatch in "+region)
    ensure(max(owners+neighbours,default=-1)==expected-1,
           "unexpected native cell count in "+region)
    origin=pts[0]
    sums=[[] for _ in range(expected)]
    for i,face in enumerate(faces):
        ensure(len(face)>=3 and all(0<=j<len(pts) for j in face),
               "bad 3D polyMesh face "+region)
        verts=[(pts[j][0]-origin[0],
                pts[j][1]-origin[1],
                pts[j][2]-origin[2]) for j in face]
        a=verts[0]
        terms=[]
        for j in range(1,len(verts)-1):
            b,c=verts[j],verts[j+1]
            terms.append((a[0]*(b[1]*c[2]-b[2]*c[1])
                         +a[1]*(b[2]*c[0]-b[0]*c[2])
                         +a[2]*(b[0]*c[1]-b[1]*c[0]))/6.0)
        signed=fsum(terms)
        sums[owners[i]].append(signed)
        if i<len(neighbours):
            sums[neighbours[i]].append(-signed)
    vols=[fsum(row) for row in sums]
    ensure(all(math.isfinite(v) and v>0 for v in vols),
           "nonpositive/nonfinite per-cell volume in "+region)
    true_total=stage.gate.native_region_volume(case,region)
    ensure(math.isclose(fsum(vols),true_total,rel_tol=2e-6,abs_tol=1e-12),
           "cell volumes do not close against independent boundary integral "+region)
    return vols


def vector_field(path: Path, n: int) -> list[tuple[float,float,float]]:
    ensure(path.is_file() and not path.is_symlink(),
           "missing/unsafe saved U field "+str(path))
    raw=path.read_text(encoding="utf-8")
    head=raw.split("internalField",1)
    ensure(len(head)==2 and re.search(r"\bformat\s+ascii\s*;",head[0]),
           "U must be a saved native ASCII volVectorField")
    inner=head[1].split("boundaryField",1)[0]
    single=re.search(r"\buniform\s*("+VECTOR.pattern+r")\s*;",inner)
    if single:
        vals=[tuple(map(float,single.groups()[1:]))]*n
    else:
        many=re.search(r"\bnonuniform\s+List<vector>\s*(\d+)\s*\(\s*(.*?)\s*\)\s*;",
                       inner,re.S)
        ensure(many is not None,"unsupported U internalField serialization")
        ensure(int(many.group(1))==n,"native U count differs from mesh")
        vals=[tuple(map(float,m.groups())) for m in VECTOR.finditer(many.group(2))]
        ensure(len(vals)==n,"native U vector count mismatch")
    ensure(all(all(math.isfinite(x) for x in v) for v in vals),"nonfinite U")
    return vals


def weighted(values:list[float],vols:list[float])->float:
    ensure(len(values)==len(vols),"field volume count mismatch")
    return math.fsum(x*v for x,v in zip(values,vols))/math.fsum(vols)


def scan_log_extrema(log:Path)->dict:
    """Locate time of maximum final linear residual; no foamLog replay."""
    ensure(log.is_file() and not log.is_symlink(),"missing native log")
    current=None
    found={key:{"final_residual_max":-1,"time_s":None,"occurrences":0}
           for key in ("h","e","p_rgh")}
    time_re=re.compile(r"^\s*Time\s*=\s*("+NUM+r")s\s*$")
    solver_re=re.compile(r"Solving for (h|e|p_rgh),\s*Initial residual\s*=\s*"+
                         NUM+r",\s*Final residual\s*=\s*("+NUM+r")")
    for line in log.open(encoding="utf-8",errors="replace"):
        m=time_re.match(line)
        if m: current=float(m.group(1))
        m=solver_re.search(line)
        if not m or current is None: continue
        key=m.group(1)
        val=float(m.group(2))
        ensure(math.isfinite(val),"nonfinite final residual "+key)
        found[key]["occurrences"]+=1
        if val>found[key]["final_residual_max"]:
            found[key]["final_residual_max"]=val
            found[key]["time_s"]=current
    ensure(all(d["occurrences"] for d in found.values()),
           "native log lacks solver residuals h/e/p_rgh")
    return found


def original_inventory()->dict:
    """Exact C14 objects from baseline files, without rewriting their physics."""
    answer={}
    for name in ("functions","researchDiagnostics","lineProfiles","momentumPostProcessing"):
        src=REFERENCE/"system"/name
        ensure(src.is_file(),"missing original C14 diagnostic "+name)
        text=src.read_text(encoding="utf-8")
        names=[x.group(1) for x in re.finditer(r"^([A-Za-z]\w*)\s*\n\s*\{",text,re.M)]
        names=[n for n in names if n!="FoamFile"]
        answer[name]={"source_sha256":sha(src),"function_objects":names}
    return answer


def analyze(case:Path,analysis:Path,out:Path)->dict:
    case=case.expanduser().resolve()
    analysis=analysis.expanduser().resolve()
    out=out.expanduser().absolute()
    ensure(out!=case and out!=analysis and case not in out.parents
           and analysis not in out.parents and not out.exists()
           and not out.is_symlink(),"output must be a fresh separate sibling")
    stage.physics.verify()
    source_meta=analysis/ANALYSIS_JSON
    source_csv=analysis/ANALYSIS_CSV
    ensure(source_meta.is_file() and source_csv.is_file(),
           "missing previous 101-state native analysis")
    baseline=json.loads(source_meta.read_text(encoding="utf-8"))
    ensure(baseline.get("status")==REQUIRED_STATUS
           and baseline.get("NOT_A_NEW_CFD") is True
           and baseline.get("time_states_count")==101
           and baseline.get("source_mesh_cells")=={"metal":8960,"mold":12352},
           "only real existing 101-state C14 3D evidence allowed")
    ensure(Path(baseline.get("source_case_read_only","")).resolve()==case,
           "analysis is from a different CFD source")
    ensure(sha(case/"log.foamMultiRun")==baseline["source_native_log_sha256"],
           "native CFD log changed since prior audit")
    ensure(sha(case/"system/controlDict")==baseline["actual_C14_original_controlDict_sha256"],
           "original C14 runtime controls changed")
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))["C14_exact_values"]
    meta_m=contract["metal"]
    meta_s=contract["mold"]
    phase=contract["solidification"]
    with source_csv.open(newline="",encoding="utf-8") as f:
        saved=list(csv.DictReader(f))
    ensure(len(saved)==101,"100 stored intervals plus initial required")
    labels=[f"{i/10:g}" for i in range(101)]
    for i,row in enumerate(saved):
        ensure(math.isclose(float(row["time_s"]),i/10,abs_tol=1e-8),
               "source saved times not C14 0.1s grid")
        ensure((case/labels[i]/"metal"/"U").is_file(),
               "missing stored native U at "+labels[i])
    v_m=cell_volumes(case,"metal",8960)
    v_s=cell_volumes(case,"mold",12352)
    V_m=math.fsum(v_m)
    V_s=math.fsum(v_s)
    density_m=meta_m["rho_kg_m3"]
    density_s=meta_s["rho_kg_m3"]
    cp=meta_m["Cp_J_kgK"]
    cv=meta_s["Cv_J_kgK"]
    latent=phase["L_J_kg"]
    output=[]
    for i,t in enumerate(labels):
        m=case/t/"metal"
        s=case/t/"mold"
        temp=native.scalar_field_values(m/"T",8960)
        sand=native.scalar_field_values(s/"T",12352)
        alpha=native.scalar_field_values(m/"phaseChangeSource:alpha1",8960)
        pr=native.scalar_field_values(m/"p_rgh",8960)
        U=vector_field(m/"U",8960)
        ensure(all(-1e-7<=a<=1+1e-7 for a in alpha),
               "nonphysical alpha1 in "+t)
        speed=[math.sqrt(sum(a*a for a in u)) for u in U]
        Tm=weighted(temp,v_m)
        Ts=weighted(sand,v_s)
        al=weighted(alpha,v_m)
        sens_m=density_m*cp*math.fsum((a-meta_m["T_initial_K"])*v
                                      for a,v in zip(temp,v_m))
        sens_s=density_s*cv*math.fsum((a-meta_s["T_initial_K"])*v
                                      for a,v in zip(sand,v_s))
        phase_change=density_m*latent*math.fsum((a-1)*v
                                                for a,v in zip(alpha,v_m))
        below_l=100*math.fsum(v for a,v in zip(temp,v_m) if a<phase["Tliq_K"])/V_m
        below_s=100*math.fsum(v for a,v in zip(temp,v_m) if a<phase["Tsol_K"])/V_m
        row=dict(
            time_s=float(t),metal_volume_m3=V_m,mold_volume_m3=V_s,
            metal_T_volMean_K=Tm,mold_T_volMean_K=Ts,
            metal_alpha1_volMean=al,
            metal_solid_fraction_volMean=1-al,
            metal_below_Tliq_volume_percent=below_l,
            metal_below_Tsol_volume_percent=below_s,
            metal_mean_speed_m_s=weighted(speed,v_m),
            metal_max_speed_m_s=max(speed),
            metal_rms_speed_m_s=math.sqrt(weighted([u*u for u in speed],v_m)),
            metal_p_rgh_volMean_Pa=weighted(pr,v_m),
            metal_sensible_delta_J=sens_m,
            metal_latent_inventory_delta_J=phase_change,
            mold_sensible_delta_J=sens_s,
            combined_estimated_stored_energy_delta_J=sens_m+sens_s+phase_change,
            saved_interval_metal_cooling_K_per_s=None,
            saved_interval_alpha1_decrease_per_s=None,
            saved_interval_latent_inventory_change_W=None,
        )
        if output:
            prev=output[-1]
            dt=row["time_s"]-prev["time_s"]
            ensure(dt>0,"nonincreasing native save times")
            row["saved_interval_metal_cooling_K_per_s"]=(prev["metal_T_volMean_K"]-Tm)/dt
            row["saved_interval_alpha1_decrease_per_s"]=(prev["metal_alpha1_volMean"]-al)/dt
            row["saved_interval_latent_inventory_change_W"]=(
                 phase_change-prev["metal_latent_inventory_delta_J"])/dt
        output.append(row)
    inventory=original_inventory()
    extrema=scan_log_extrema(case/"log.foamMultiRun")
    res={
      "schema":"C3D04_A_C14_3D_POSTPROCESS_VOLUME_PARITY_V1",
      "created_utc":datetime.now(timezone.utc).isoformat(),
      "scope":"CASE_A_3D_ORIGINAL_C14_REAL_V4_T02_ONLY",
      "status":"EXISTING_10S_101_STATES_VOLUME_WEIGHTED_PARTIAL_C14_PARITY_NO_NEW_CFD",
      "source_case_read_only":str(case),
      "previous_native_analysis_read_only":str(analysis),
      "native_log_sha256":sha(case/"log.foamMultiRun"),
      "original_C14_diagnostic_inventory":inventory,
      "metal_volume_m3":V_m,"mold_volume_m3":V_s,
      "metal_total_mass_kg":density_m*V_m,
      "mold_total_mass_kg":density_s*V_s,
      "initial":output[0],
      "final":output[-1],
      "peak_solver_final_residual_with_time":extrema,
      "time_resolution_s":0.1,
      "C14_solver_deltaT_s":contract["numerics"]["deltaT_s"],
      "C14_probe_equivalent_every_solver_step":False,
      "volume_weighting_verified_on_real_mesh":True,
      "estimated_sensible_and_latent_storage_computed":True,
      "energy_flux_integral_verified":False,
      "energy_conservation_verified":False,
      "native_C14_function_objects_3D_replayed":False,
      "momentum_Darcy_buoyancy_native_3D_diagnostics_verified":False,
      "QuickCup_validated":False,
      "grid_or_time_step_independence_verified":False,
      "CFD_rerun":False,
      "missing_for_full_C14_parity":[
        "Exact C14 probes at every 0.001 s cannot be retroactively recovered from 0.1s snapshots",
        "3D geometry-valid horizontal/vertical profiles and spatial slices at saved times",
        "Boundary face phi impermeability and top-surface U/phi fields",
        "Native face heatFlux/energyFlux/energyAdvectiveFlux and separate external/contact power integrals",
        "Native vorticity, flowType, velocity gradients, gradT, gradRho, CoCell",
        "Native solidificationMelting Darcy, pressure and buoyancy acceleration fields",
        "True C14 phase-rate/energy-rate functionObjects and their physically consistent numerical settings",
        "Boundary-flux-constrained conservation and model/mesh/time-step/experiment validation",
      ],
      "interpretation":[
        "Volume-weighted α1 is not interchangeable with unweighted cell mean; 1-α1 is a model-defined solid inventory.",
        "Latent inventory = ρL∫(α1(t)-α1(0))dV uses original C14 constants; its change rate is NOT a measured interface heat flux.",
        "Sensible storage estimates from T with ORIGINAL C14 Cp and Cv are NOT independently verified thermo enthalpy h/e integrals.",
        "Total stored-energy change does NOT prove conservation without native face energy fluxes and model source-term accounting.",
        "Saved first crossing or finite difference is limited to 0.1s; cannot label it exact physical onset or recalescence.",
        "Volume-weighted time histories and log residual peaks are actual postrun diagnostics, not independent scientific validation.",
      ],
      "time_series_csv":"C3D04_A_C14_3D_VOLUMETRIC_101_STATES.csv",
    }
    out.mkdir(parents=True,exist_ok=False)
    with (out/res["time_series_csv"]).open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(output)
    (out/"C3D04_A_C14_3D_POSTPROCESS_REPORT.json").write_text(
        json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return res


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,
                   default=Path.home()/"OpenFOAM/C3D04_A_C14_FLUID_SOLID_FULL_10S_RUN_01")
    p.add_argument("--analysis",type=Path,
                   default=Path.home()/"OpenFOAM/C3D04_A_C14_FLUID_SOLID_10S_ANALYSIS_01")
    p.add_argument("--out",type=Path,
                   default=Path.home()/"OpenFOAM/C3D04_A_C14_3D_VOLUMETRIC_POSTPROCESS_01")
    args=p.parse_args()
    try:
        report=analyze(args.case,args.analysis,args.out)
        print(json.dumps({
          "status":report["status"],
          "metal_volume_m3":report["metal_volume_m3"],
          "final":report["final"],
          "time_of_peak_residuals":report["peak_solver_final_residual_with_time"],
          "full_C14_parity":False,
          "energy_conservation_verified":False,
          "report":str(args.out/"C3D04_A_C14_3D_POSTPROCESS_REPORT.json"),
        },ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("C14_3D_POSTPROCESS_PARITY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
