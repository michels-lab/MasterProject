#!/usr/bin/env python3
"""C3D05 B original 10s C14: archived REAL rho/phi and rho-weighted phase.

READ ONLY, no CFD and no fabricated missing h/e or t0 rho/phi. Uses
source-authenticated original HEX8 owner/neighbor mesh and archived 101 alpha1
snapshots, then evaluates saved native metal rho on exactly the states where
rho exists. Carefully inspects native surfaceScalarField phi boundary patches
for mass flux kg/s: unavailable/malformed/unsupported saved phi is reported
as unavailable, NEVER treated as zero or as a mass-conservation result.

Source outputs preserve all original input archives; any sampled phi integral
uses saved times, NOT the 0.001 s solver step or a true continuity closure.
"""
from __future__ import annotations

import argparse
from array import array
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import analyze_existing_case_b_c14 as native
import audit_existing_case_b_c14_energy_closure_readiness as readiness
import volume_weighted_existing_case_b_c14 as volume
import quantify_existing_case_b_c14_energy_inventory as inventory

CASE=native.DEFAULT_CASE
JOIN=readiness.JOIN
Q=readiness.Q
STORAGE=readiness.STORAGE
OUT=Path.home()/"OpenFOAM/C3D05_B_C14_NATIVE_RHO_PHI_MASS_01"
CSV="C3D05_B_C14_REAL_METAL_RHO_PHI_MASS_101_TIME_COVERAGE.csv"
JSON="C3D05_B_C14_REAL_METAL_RHO_PHI_MASS_AND_MODELED_PHASE_REPORT.json"
MANIFEST="C3D05_B_C14_REAL_METAL_RHO_PHI_MASS_SHA256.json"
STATUS="C3D05_B_C14_REAL_METAL_RHO_PHI_MASS_SCREENING_NO_CONSERVATION"
CELL_COUNT=92200
HEADER=(
    "time_s","rho_file_exists","phi_file_exists",
    "rho_mass_kg","rho_min_kg_m3","rho_max_kg_m3",
    "rho_mean_volume_weighted_kg_m3",
    "rho_weighted_liquid_mass_fraction",
    "rho_weighted_solid_complement_mass_fraction_MODELED",
    "modeled_solid_complement_mass_kg",
    "model_rhoL_solid_equivalent_inventory_J_NOT_NATIVE_FVMODEL",
    "phi_metalTop_kg_s_if_readable",
    "phi_metal_to_mold_kg_s_if_readable",
    "phi_surface_kg_s_supported",
    "phi_parse_note",
    "sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL",
    "mass_change_from_first_readable_rho_kg",
    "mass_delta_plus_sampled_exterior_phi_kg_NOT_CONTINUITY_RESIDUAL"
)


def require(valid:bool, msg:str)->None:
    if not valid:
        raise ValueError("C3D05_B_REAL_RHO_PHI_MASS_BLOCKED: "+msg)


def sha(path:Path)->str:
    require(path.is_file() and not path.is_symlink(),
            "immutable original archive missing or linked: "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as inp:
        while chunk:=inp.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def strip_comments(source:str)->str:
    return re.sub(r"/\*.*?\*/|//[^\n]*","",source,flags=re.S)


def curly_block(source:str,name:str)->str:
    """Find exactly one real Foam dictionary block and respect nested braces."""
    src=strip_comments(source)
    candidates=list(re.finditer(r"(?<![A-Za-z0-9_])"+
                                re.escape(name)+r"\s*\{",src))
    require(len(candidates)==1,
            "expected one OpenFOAM dictionary block: "+name)
    start=candidates[0].end()
    depth=1
    for i in range(start,len(src)):
        if src[i]=="{":
            depth+=1
        elif src[i]=="}":
            depth-=1
            if depth==0:
                return src[start:i]
    raise ValueError("OpenFOAM dictionary brace imbalance: "+name)


def mesh_patch_counts(path:Path)->dict[str,int]:
    require(path.is_file() and not path.is_symlink(),
            "original C14 metal mesh boundary missing")
    contents=path.read_text(encoding="utf-8")
    source=strip_comments(contents)
    require("polyBoundaryMesh" in source and
            re.search(r"\bformat\s+ascii\s*;",source) is not None,
            "original native mesh boundary not ASCII polyBoundaryMesh")
    counts={}
    for name in ("metalTop","metal_to_mold"):
        body=curly_block(source,name)
        m=re.search(r"\bnFaces\s+(\d+)\s*;",body)
        require(m is not None and int(m.group(1))>0,
                "original native mesh patch face count unavailable: "+name)
        counts[name]=int(m.group(1))
    require(counts["metal_to_mold"]==12636,
            "not the original 12636-face authentic Case B metal interface")
    return counts


def rho_mass_snapshot(rho:list[float],alpha:list[float],
                      volumes:array,latent:float)->dict:
    """Source-conforming real rho field, with modeled alpha1 complement."""
    require(len(rho)==len(alpha)==len(volumes)>0,
            "original metal rho alpha1 native per-cell lengths differ")
    require(all(math.isfinite(x) and x>0 for x in rho),
            "nonphysical original archived rho values")
    require(all(math.isfinite(x) and 0<=x<=1 for x in alpha),
            "invalid source-native model alpha1 liquid fraction")
    require(all(math.isfinite(x) and x>0 for x in volumes),
            "original source metal mesh contains bad cell volume")
    require(latent>0 and math.isfinite(latent),
            "invalid original C14 latent heat constant")
    mass=math.fsum(ri*vi for ri,vi in zip(rho,volumes))
    modeled_solid=math.fsum(
        ri*vi*(1-ai) for ri,vi,ai in zip(rho,volumes,alpha))
    liquid=mass-modeled_solid
    mean=mass/math.fsum(volumes)
    require(0<=modeled_solid<=mass and liquid>=0,
            "modeled density-weighted phase bound invalid")
    return {
        "rho_mass_kg":mass,
        "rho_min_kg_m3":min(rho),
        "rho_max_kg_m3":max(rho),
        "rho_mean_volume_weighted_kg_m3":mean,
        "rho_weighted_liquid_mass_fraction":liquid/mass,
        "rho_weighted_solid_complement_mass_fraction_MODELED":
            modeled_solid/mass,
        "modeled_solid_complement_mass_kg":modeled_solid,
        "model_rhoL_solid_equivalent_inventory_J_NOT_NATIVE_FVMODEL":
            modeled_solid*latent,
    }


def phi_patch_mass_flux(path:Path,patch_counts:dict[str,int])->dict:
    """Read signed ORIGINAL boundary phi mass flux if valid ASCII format.

    If unsupported, caller reports unavailable; it MUST NOT become zero.
    The boundary field q may be original kg/s surface flux of user solver:
    verify dimensions and native surfaceScalarField header beforehand.
    """
    require(path.is_file() and not path.is_symlink(),
            "actual original saved phi field absent")
    text=path.read_text(encoding="utf-8")
    source=strip_comments(text)
    prefix=curly_block(source,"FoamFile")
    require(re.search(r"\bformat\s+ascii\s*;",prefix) is not None
            and re.search(r"\bclass\s+surfaceScalarField\s*;",prefix) is not None,
            "original phi not an ASCII surfaceScalarField")
    dims=re.search(r"\bdimensions\s+\[\s*([^\]]+)\s*\]\s*;",source)
    require(dims is not None,"phi native units unavailable")
    units=[float(x) for x in dims.group(1).split()]
    require(units==[1,0,-1,0,0,0,0],
            "original saved phi dimensions not kg/s; no mass flux inference")
    boundary=curly_block(source,"boundaryField")
    results={}
    float_num=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    for name,n in patch_counts.items():
        body=curly_block(boundary,name)
        # Some native surfaceScalarField patches can be calculated, fixedValue
        # or other models; inspect the actual archived values, not BC labels.
        uniform=re.search(r"\bvalue\s+uniform\s+("+float_num+r")\s*;",body)
        nonuniform=re.search(
            r"\bvalue\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;",
            body,re.S)
        compact=re.search(
            r"\bvalue\s+nonuniform\s+List<scalar>\s+(\d+)\s*\{\s*("+
            float_num+r")\s*\}\s*;",body,re.S)
        matches=sum(x is not None for x in (uniform,nonuniform,compact))
        require(matches==1,
                "original phi boundary does not expose one readable "
                "numeric value: "+name)
        if uniform:
            val=float(uniform.group(1))
            require(math.isfinite(val),"nonfinite native phi uniform "+name)
            signed=n*val
        elif compact:
            require(int(compact.group(1))==n,
                    "original phi compact face count mismatch "+name)
            val=float(compact.group(2))
            require(math.isfinite(val),"nonfinite native compact phi "+name)
            signed=n*val
        else:
            declared=int(nonuniform.group(1))
            require(declared==n,
                    "original phi face count differs from polyMesh "+name)
            numbers=nonuniform.group(2).split()
            require(len(numbers)==n,
                    "truncated original phi face entries "+name)
            data=[float(x) for x in numbers]
            require(all(math.isfinite(x) for x in data),
                    "nonfinite original phi boundary entries "+name)
            signed=math.fsum(data)
        results[name]=signed
    return results


def temporal_mass_screening(records:list[dict])->dict:
    """Integrate native saved-time exterior phi (if available) from FIRST valid.

    Breaks in rho/phi and serialization errors result in NOT ASSESSABLE,
    NEVER fill a missing time or infer phi=0. t0 is not invented.
    """
    withrho=[r for r in records if r["rho_mass_kg"] is not None]
    require(len(withrho)>=2,"insufficient archived actual rho to screen mass")
    base=withrho[0]
    for r in records:
        if r["rho_mass_kg"] is not None:
            r["mass_change_from_first_readable_rho_kg"]=(
                r["rho_mass_kg"]-base["rho_mass_kg"])
        else:
            r["mass_change_from_first_readable_rho_kg"]=None
        r["sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"]=None
        r["mass_delta_plus_sampled_exterior_phi_kg_NOT_CONTINUITY_RESIDUAL"]=None
    valid=[r for r in records if r["rho_mass_kg"] is not None
           and r["phi_metalTop_kg_s_if_readable"] is not None
           and r["phi_metal_to_mold_kg_s_if_readable"] is not None]
    screened={
        "rho_states":len(withrho),
        "phi_and_rho_joint_readable_states":len(valid),
        "first_rho_time_s":base["time_s"],
        "first_joint_valid_time_s":valid[0]["time_s"] if valid else None,
        "first_time_t0_rho_assumed_or_fabricated":False,
        "native_phi_kg_s_total_flux_includes_metalTop_and_metal_to_mold":True,
        "total_0_to_10s_native_solver_mass_integral_computed":False,
        "mass_conservation_verified":False,
    }
    if len(valid)<2:
        screened["saved_time_screening_available"]=False
        screened["unavailable_reason"]="Too few joint numeric saved rho+phi times"
        return screened
    first=valid[0]
    cumulative=0.0
    contiguous=True
    prev=None
    for r in records:
        if r["time_s"]<first["time_s"]:
            continue
        if r["rho_mass_kg"] is None or r["phi_metalTop_kg_s_if_readable"] is None:
            contiguous=False
            continue
        if not contiguous:
            continue
        if prev is not None:
            dt=r["time_s"]-prev["time_s"]
            if not math.isclose(dt,.1,rel_tol=0,abs_tol=1e-8):
                contiguous=False
                continue
            oldflux=(prev["phi_metalTop_kg_s_if_readable"]+
                     prev["phi_metal_to_mold_kg_s_if_readable"])
            curflux=(r["phi_metalTop_kg_s_if_readable"]+
                     r["phi_metal_to_mold_kg_s_if_readable"])
            cumulative+=.5*dt*(oldflux+curflux)
        r["sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"]=cumulative
        r["mass_delta_plus_sampled_exterior_phi_kg_NOT_CONTINUITY_RESIDUAL"]=(
            r["rho_mass_kg"]-first["rho_mass_kg"]+cumulative)
        prev=r
    last=prev
    screened.update({
        "saved_time_screening_available":last is not None,
        "last_contiguous_joint_time_s":last["time_s"] if last else None,
        "sampled_cumulative_exterior_phi_kg":
            last["sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"]
            if last else None,
        "mass_delta_from_first_joint_rho_kg":
            last["rho_mass_kg"]-first["rho_mass_kg"] if last else None,
        "partial_mass_delta_plus_sampled_q_kg_NOT_CONTINUITY_RESIDUAL":
            last["mass_delta_plus_sampled_exterior_phi_kg_NOT_CONTINUITY_RESIDUAL"]
            if last else None,
        "complete_uninterrupted_joint_coverage_to_10s":
            last is not None and last["time_s"]==10.0,
    })
    return screened


def run(case:Path,join:Path,q:Path,storage:Path,out:Path)->dict:
    case=case.expanduser().absolute()
    join=join.expanduser().absolute()
    q=q.expanduser().absolute()
    storage=storage.expanduser().absolute()
    out=out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(),
            "immutable output already exists, no overwrite")
    require(all(out!=p and out not in p.parents and p not in out.parents
                for p in (case,join,q,storage)),
            "output overlaps real source CFD or prior data archives")
    _,provenance=readiness.verify_archives(join,q,storage,case)
    source,checks=native.validated_mesh_and_stage(case)
    saved=native.saved_times(case)
    require(len(saved)==101,"original archived C14 0..10s grid incomplete")
    coverage=readiness.field_coverage(case,saved)
    require(coverage["metal_rho"]["saved_states_with_field"]>=2,
            "not enough actual original metal rho fields")
    counts=mesh_patch_counts(case/"constant/metal/polyMesh/boundary")
    cells,geometry=volume.calculate_native_metal_cell_volumes(
        case/"constant/metal/polyMesh")
    C14=inventory.source_C14_constants()
    latent=float(C14["L_metal_J_kg"])
    reference_rho=float(C14["rho_metal_kg_m3"])
    require(geometry["nCells"]==CELL_COUNT,"wrong original 92200 hex cells")
    require(reference_rho>0,"invalid source C14 metal rho reference")
    records=[]
    field_digests=[]
    unparseable=[]
    for index,(t,label) in enumerate(saved,1):
        base=case/label/"metal"
        phi_path=base/"phi"
        rho_path=base/"rho"
        alpha_path=base/"phaseChangeSource:alpha1"
        isrho=rho_path.is_file() and not rho_path.is_symlink()
        isphi=phi_path.is_file() and not phi_path.is_symlink()
        row={key:None for key in HEADER}
        row.update({
            "time_s":t,"rho_file_exists":isrho,
            "phi_file_exists":isphi,
            "phi_surface_kg_s_supported":False,
            "phi_parse_note":"original native phi field not saved" if not isphi else None,
        })
        if isrho:
            rho=native.source_reader.scalar_field_values(rho_path,CELL_COUNT)
            alpha=native.source_reader.scalar_field_values(alpha_path,CELL_COUNT)
            row.update(rho_mass_snapshot(rho,alpha,cells,latent))
            field_digests.append({"time_s":t,"rho_SHA256":sha(rho_path),
                                  "alpha1_SHA256":sha(alpha_path)})
        if isphi:
            field_digests.append({"time_s":t,"phi_SHA256":sha(phi_path)})
            try:
                ph=phi_patch_mass_flux(phi_path,counts)
                row["phi_metalTop_kg_s_if_readable"]=ph["metalTop"]
                row["phi_metal_to_mold_kg_s_if_readable"]=ph["metal_to_mold"]
                row["phi_surface_kg_s_supported"]=True
                row["phi_parse_note"]="native kg/s outward patch surfaceScalarField"
            except (OSError,ValueError,UnicodeError,OverflowError) as exc:
                # The original phi field may not contain a parseable boundary
                # serialization or may not have kg/s units; evidence still
                # matters, but never substitute guessed phi=0 values.
                row["phi_parse_note"]="NOT_AVAILABLE: "+str(exc)[:320]
                if len(unparseable)<6:
                    unparseable.append({"time_s":t,
                                        "reason":row["phi_parse_note"]})
        records.append(row)
        if index==1 or index%10==0 or index==len(saved):
            print("C3D05_B_REAL_RHO_PHI_READONLY "
                  f"{index}/{len(saved)} t={t:g}s, NOT_MASS_CLOSURE",
                  flush=True)
    require(sum(r["rho_file_exists"] for r in records)==
            coverage["metal_rho"]["saved_states_with_field"],
            "rho existence diverges from original C14 field readiness")
    require(sum(r["phi_file_exists"] for r in records)==
            coverage["metal_phi"]["saved_states_with_field"],
            "phi existence diverges from original C14 field readiness")
    screening=temporal_mass_screening(records)
    real_rho=[r for r in records if r["rho_mass_kg"] is not None]
    result={
        "schema":"C3D05_B_C14_GENUINE_NATIVE_METAL_RHO_PHI_MASS_101_TIMES_V1",
        "status":STATUS,
        "original_C14_CFD_10s_read_only":str(case),
        "original_C14_CFD_completion_log_SHA256":provenance["original_CFD_log_SHA256"],
        "original_C14_CFD_completion_report_SHA256":provenance["original_CFD_stage_SHA256"],
        "native_101_q_storage_provenance":provenance,
        "original_C14_contract_sha256":C14["source_sha256"],
        "native_metal_hex8_geometry":geometry,
        "C14_original_reference_rho_kg_m3":reference_rho,
        "C14_original_reference_mass_kg_NOT_ACTUAL_T0_RHO":
            reference_rho*math.fsum(cells),
        "original_metal_rho_archived_states":len(real_rho),
        "original_metal_phi_archived_states":sum(r["phi_file_exists"] for r in records),
        "original_metal_phi_kg_s_parsed_states":sum(
            r["phi_surface_kg_s_supported"] for r in records),
        "original_101_time_label_axis":[t for t,label in saved],
        "first_archived_rho_observation":real_rho[0],
        "last_archived_rho_observation":real_rho[-1],
        "native_patch_expected_face_counts":counts,
        "sample_phi_parse_problems_not_inferred_as_zero":unparseable,
        "sampled_saved_time_mass_phi_screening":screening,
        "model_alpha1_density_weighted_solid_complement_only":True,
        "original_h_e_archived_or_integrated":False,
        "actual_native_fvModel_latent_source_integrated":False,
        "native_solver_mass_conservation_verified":False,
        "no_original_t0_rho_or_phi_fabricated":True,
        "original_rhoT_and_alpha_are_not_JMatPro_or_QuickCup_validation":True,
        "source_CFD_untouched_no_CFD_or_wmake":True,
        "limitations":[
            "rho_i V_i mass uses reconstructed HEX8 per-cell volumes; good global checkMesh agreement does not certify cell-by-cell native volume identity.",
            "No missing rho/phi field is reconstructed; the C14 reference rhoRef is NOT true saved t0 rho.",
            "Surface phi boundary can be absent/unreadable despite file existence; missing values are NULL not zero.",
            "Phi is accepted as kg/s only if source field declares [1 0 -1 0 0 0 0] and patches have correct per-face serialization.",
            "Outward saved-time surface phi trapezoids are NOT solver-dt mass conservation and source boundary algorithms are not recalculated.",
            "Density-weighted solid fraction and rho L solid equivalent are modeled proxies, not shrinkage or native fvModels source energy.",
            "Original C14 10s run has no direct saved h/e histories and this analysis makes no energy-conservation claim.",
        ]
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=str(out.parent),prefix="."+out.name+".staging.") as folder:
        pending=Path(folder)/"candidate"
        pending.mkdir()
        with (pending/CSV).open("x",newline="",encoding="utf-8") as f:
            writer=csv.DictWriter(f,fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(records)
        (pending/JSON).write_text(json.dumps(
            result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        (pending/"C3D05_B_C14_ORIGINAL_RHO_PHI_ALPHA1_INPUT_SHA256.json").write_text(
            json.dumps(field_digests,indent=2)+"\n",encoding="utf-8")
        (pending/MANIFEST).write_text(json.dumps({
            "source_CFD_original_stage_SHA256":provenance["original_CFD_stage_SHA256"],
            "source_CFD_original_log_SHA256":provenance["original_CFD_log_SHA256"],
            "source_C14_exact_contract_SHA256":C14["source_sha256"],
            "source_original_HEX8_owner_SHA256":
                sha(case/"constant/metal/polyMesh/owner"),
            "source_original_HEX8_face_list_SHA256":
                sha(case/"constant/metal/polyMesh/faces"),
            "original_100_rho_phi_input_digests_SHA256":
                sha(pending/"C3D05_B_C14_ORIGINAL_RHO_PHI_ALPHA1_INPUT_SHA256.json"),
            "mass_phi_101_time_csv_SHA256":sha(pending/CSV),
            "mass_phi_report_SHA256":sha(pending/JSON),
            "all_original_CFD_and_q_archives_immutable":True,
            "no_solver_or_postprocess_q_reexecution":True
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "new mass output appeared; refuse overwrite")
        pending.rename(out)
    return result


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,default=CASE)
    p.add_argument("--join",type=Path,default=JOIN)
    p.add_argument("--q",type=Path,default=Q)
    p.add_argument("--storage",type=Path,default=STORAGE)
    p.add_argument("--out",type=Path,default=OUT)
    args=p.parse_args()
    try:
        r=run(args.case,args.join,args.q,args.storage,args.out)
        print(json.dumps({
            "status":r["status"],
            "out":str(args.out),
            "saved_states":len(r["original_101_time_label_axis"]),
            "genuine_rho_states":r["original_metal_rho_archived_states"],
            "saved_phi_files":r["original_metal_phi_archived_states"],
            "real_phi_kg_s_parsed_states":
                r["original_metal_phi_kg_s_parsed_states"],
            "first_actual_rho_time_s":
                r["first_archived_rho_observation"]["time_s"],
            "last_actual_rho_time_s":
                r["last_archived_rho_observation"]["time_s"],
            "last_actual_rho_metal_mass_kg":
                r["last_archived_rho_observation"]["rho_mass_kg"],
            "last_actual_rho_weighted_model_solid_mass_fraction":
                r["last_archived_rho_observation"][
                    "rho_weighted_solid_complement_mass_fraction_MODELED"],
            "real_rho_saved_time_phi_mass_screening":
                r["sampled_saved_time_mass_phi_screening"],
            "phi_parse_sample_errors":r["sample_phi_parse_problems_not_inferred_as_zero"],
            "actual_native_mass_conservation_verified":False,
            "actual_native_energy_balance_verified":False,
            "CFD_RERUN":False
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,OverflowError) as e:
        print("C3D05_B_REAL_RHO_PHI_MASS_BLOCKED:",e,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
