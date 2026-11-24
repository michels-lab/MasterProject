#!/usr/bin/env python3
"""Case B C3D05: cell-volume-weighted alpha1 from archived real C14 CFD.

Pure Python, READ-ONLY native OpenFOAM Foundation14 ASCII polyMesh geometry
and existing SHA-verified postrun fields. No foamMultiRun, no mesh conversion,
no changes to solver data, no synthetic volume/fraction and no new CFD.

Computes signed per-cell volumes from owner-oriented quad face triangulation
and verifies positivity, total against real native checkMesh metadata, and
archived topology SHA. On genuine distorted/non-planar HEX8 these geometry
volumes may differ from exact native OpenFOAM cell volumes: explicitly reject
if aggregate error exceeds threshold, never conceal the approximation.
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
import analyze_existing_case_b_c14 as base

DEFAULT_CASE=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
DEFAULT_ANALYSIS=Path.home()/"OpenFOAM/C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01"
DEFAULT_OUTPUT=Path.home()/"OpenFOAM/C3D05_B_C14_VOLUME_WEIGHTED_PHASE_01"
CSV_NAME="C3D05_B_C14_VOLUME_WEIGHTED_ALPHA1_101_STATES.csv"
JSON_NAME="C3D05_B_C14_VOLUME_WEIGHTED_ALPHA1_REPORT.json"
SHA_NAME="C3D05_B_C14_VOLUME_WEIGHTED_SHA256.json"
STATUS="C3D05_B_C14_NATIVE_HEX8_VOLUME_WEIGHTED_ALPHA1_NOT_PHYSICALLY_VALIDATED"
EXPECTED_CELLS=92200
CHECKMESH_METAL_VOLUME_M3=4.79754032229e-05
MAX_RELATIVE_VOLUME_DIFFERENCE=0.005
HEADERS=(
    "time_s","mean_liquid_fraction_cell_unweighted",
    "mean_liquid_fraction_volume_weighted",
    "mean_solid_complement_volume_weighted",
    "volume_with_alpha1_below_0_999_m3",
    "volume_with_alpha1_below_0_999_fraction",
    "volume_fully_solid_alpha1_zero_m3"
)


def require(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError("C3D05_B_VOLUME_WEIGHTED_READONLY_BLOCKED: "+msg)


def sha(path: Path) -> str:
    require(path.is_file() and not path.is_symlink(),
            "missing/linked archived input "+str(path))
    h=hashlib.sha256()
    with path.open("rb") as stream:
        while block:=stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def foam_ascii_list(path: Path, kind: str) -> tuple[int,str]:
    """Return declared count and list payload after a validated FoamFile header.

    Read-only ASCII only. The outer count/list delimiters are not guessed from
    header comments. Supports FOAM's n(...) arrays incl n=0; labels can use
    compact n{label} representation.
    """
    require(path.is_file() and not path.is_symlink(),"native mesh source missing "+str(path))
    raw=path.read_text(encoding="utf-8")
    header=re.search(r"\bFoamFile\s*\{([^{}]*)\}",raw,re.S)
    require(header is not None,"no native FoamFile header "+kind)
    require(re.search(r"\bformat\s+ascii\s*;",header.group(1)) is not None,
            "binary mesh forbidden; no implicit binary decoding")
    expected_class={"points":"vectorField","faces":"faceList",
                    "owner":"labelList","neighbour":"labelList"}[kind]
    require(re.search(r"\bclass\s+"+expected_class+r"\s*;",header.group(1)) is not None,
            "unexpected native mesh class "+kind)
    rest=raw[header.end():]
    # Header/list comments in Foundation14; these have no token significance.
    rest=re.sub(r"/\*.*?\*/|//[^\n]*","",rest,flags=re.S)
    match=re.match(r"\s*(\d+)\s*([\(\{])",rest)
    require(match is not None,"native payload header absent "+kind)
    n=int(match.group(1))
    require(n>=0,"negative native mesh list length")
    if match.group(2)=="{":
        uniform=re.fullmatch(r"\s*(\d+)\s*\}\s*",rest[match.end():])
        require(uniform is not None and kind in ("owner","neighbour"),
                "invalid compact native label representation")
        return n,"{"+uniform.group(1)+"}"
    body=rest[match.end():]
    close=body.rfind(")")
    require(close>=0 and not body[close+1:].strip(),
            "native list does not close cleanly "+kind)
    return n,body[:close]


def parse_labels(path: Path, kind: str) -> array:
    n,body=foam_ascii_list(path,kind)
    labels=array("I")
    if body.startswith("{"):
        labels=array("I",[int(body[1:-1])])*n
    else:
        for match in re.finditer(r"\d+",body):
            labels.append(int(match.group()))
    require(len(labels)==n,"native "+kind+" label count mismatch")
    return labels


def parse_points(path: Path) -> list[tuple[float,float,float]]:
    n,body=foam_ascii_list(path,"points")
    points=[]
    number=r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
    rgx=re.compile(r"\(\s*("+number+r")\s+("+number+r")\s+("+number+r")\s*\)")
    for match in rgx.finditer(body):
        pt=tuple(float(x) for x in match.groups())
        require(all(math.isfinite(v) for v in pt),
                "nonfinite native mesh vertex")
        points.append(pt)
    require(len(points)==n and n>0,
            "native mesh points list corrupt or non-ASCII")
    return points


def quad_signed_six_volume(points: list[tuple[float,float,float]],
                           verts: tuple[int,int,int,int],
                           origin: tuple[float,float,float]) -> float:
    """6 * pyramid signed volume of an oriented four-point face.

    Splits each oriented quad into triangles (0,1,2) and (0,2,3).
    Orientation follows native owner outward; neighbour subtracts same flux.
    Shifting all vertices to a fixed local origin reduces cancellation.
    """
    x0,y0,z0=origin
    a,b,c,d=[(points[i][0]-x0,points[i][1]-y0,points[i][2]-z0)
             for i in verts]
    def tri(u,v,w):
        return (u[0]*(v[1]*w[2]-v[2]*w[1])
               +u[1]*(v[2]*w[0]-v[0]*w[2])
               +u[2]*(v[0]*w[1]-v[1]*w[0]))
    return tri(a,b,c)+tri(a,c,d)


def calculate_native_metal_cell_volumes(poly: Path) -> tuple[array,dict]:
    """Native owner/neighbour oriented face-flux divergence; no external tools."""
    points=parse_points(poly/"points")
    owners=parse_labels(poly/"owner","owner")
    neighbors=parse_labels(poly/"neighbour","neighbour")
    nfaces=len(owners)
    ninternal=len(neighbors)
    require(nfaces>0 and 0<ninternal<nfaces,
            "native internal/boundary face counts inconsistent")
    max_cell=max(max(owners),max(neighbors))
    require(max_cell+1==EXPECTED_CELLS,
            f"not original {EXPECTED_CELLS}-cell metal region")
    six_vol=array("d",[0.0])*EXPECTED_CELLS
    n,body=foam_ascii_list(poly/"faces","faces")
    require(n==nfaces,"native face count not equal to owner labels")
    # Each accepted HEX8 cell has quad faces. Reject non-quads rather than
    # approximate unknown polyhedra or count the final outer delimiter.
    face_pattern=re.compile(r"(\d+)\s*\(\s*([\d\s]+?)\s*\)")
    origin=points[0]
    consumed=0
    for face in face_pattern.finditer(body):
        require(consumed<nfaces,"extra face beyond native owner count")
        require(int(face.group(1))==4,"non-quad face: not accepted native HEX8")
        vert=tuple(int(x) for x in face.group(2).split())
        require(len(vert)==4 and len(set(vert))==4
                and all(0<=i<len(points) for i in vert),
                "invalid vertex index of native quadrilateral face")
        six=quad_signed_six_volume(points,vert,origin)
        owner=owners[consumed]
        six_vol[owner]+=six
        if consumed<ninternal:
            six_vol[neighbors[consumed]]-=six
        consumed+=1
    require(consumed==nfaces,"native face list count differs from owner count")
    # In hex mesh with right-handed owner/neighbor face orientation all
    # cell volumes must be strictly positive.
    volumes=array("d",(v/6.0 for v in six_vol))
    require(all(math.isfinite(v) and v>0 for v in volumes),
            "nonpositive/nonfinite cell volume; face orientation or mesh broken")
    total=math.fsum(volumes)
    relative=abs(total-CHECKMESH_METAL_VOLUME_M3)/CHECKMESH_METAL_VOLUME_M3
    require(relative<=MAX_RELATIVE_VOLUME_DIFFERENCE,
            "geometry/triangulation volumes do not reproduce accepted "
            f"checkMesh total (relative discrepancy {relative:.6g}); "
            "do NOT claim volume-weighted solidification")
    return volumes,{
        "source":"REAL_ORIGINAL_POLYMESH_QUAD_FACE_ORIENTED_TRIANGLE_PYRAMID_DIVERGENCE",
        "volume_method":"owner_plus_neighbor_minus_signed_face_6_volume",
        "nCells":EXPECTED_CELLS,"nFaces":nfaces,"nInternalFaces":ninternal,
        "nPoints":len(points),"cell_volume_min_m3":min(volumes),
        "cell_volume_max_m3":max(volumes),
        "total_volume_m3":total,
        "native_checkMesh_total_volume_m3":CHECKMESH_METAL_VOLUME_M3,
        "relative_discrepancy_vs_checkMesh":relative,
        "nonplanar_quad_triangulation_difference_possible":True
    }


def verified_existing_analysis(source: Path) -> tuple[list[dict],dict,dict]:
    require(source.is_dir() and not source.is_symlink()
            and source.name==DEFAULT_ANALYSIS.name,
            "not original Case B 10s saved native postrun")
    manifest=json.loads((source/base.MANIFEST).read_text(encoding="utf-8"))
    require(manifest.get("analysis_csv_sha256")==sha(source/base.CSV)
            and manifest.get("analysis_json_sha256")==sha(source/base.JSON),
            "original C14 postrun SHA mismatch")
    doc=json.loads((source/base.JSON).read_text(encoding="utf-8"))
    require(doc.get("status")==base.STATUS
            and doc.get("native_CFD_solved_full_10s") is True
            and doc.get("native_C14_solidificationMeltingSource_selected") is True
            and doc.get("phase_field_mean_is_cell_based_unweighted") is True
            and doc.get("JMatPro_QuickCup_physical_validation") is False,
            "source postrun does not certify native original C14 10s")
    require(doc.get("native_original_C14_metadata",{}).get("metal_cells")==EXPECTED_CELLS,
            "postrun native geometry not C3D05 accepted metal")
    with (source/base.CSV).open(encoding="utf-8",newline="") as inp:
        rows=list(csv.DictReader(inp))
    require(len(rows)==101 and len(doc.get("saved_times_s",[]))==101,
            "original 101 archived states missing")
    times=[float(r["time_s"]) for r in rows]
    require(times==doc["saved_times_s"] and times[0]==0 and times[-1]==10,
            "postrun saved time coordinates drifted")
    return rows,doc,manifest


def weighted_phase(alpha: list[float], volumes: array) -> dict:
    require(len(alpha)==len(volumes)==EXPECTED_CELLS,
            "native alpha1 does not cover 92200 real metal cells")
    require(all(math.isfinite(x) and 0<=x<=1 for x in alpha),
            "C14 alpha1 must be a physical liquid fraction")
    total=math.fsum(volumes)
    liquid=math.fsum(v*a for a,v in zip(alpha,volumes))/total
    require(0<=liquid<=1,"invalid weighted liquid fraction")
    below=math.fsum(v for a,v in zip(alpha,volumes) if a<0.999)
    fully=math.fsum(v for a,v in zip(alpha,volumes) if a<=1e-12)
    return {
        "mean_liquid_fraction_volume_weighted":liquid,
        "mean_solid_complement_volume_weighted":1-liquid,
        "volume_with_alpha1_below_0_999_m3":below,
        "volume_with_alpha1_below_0_999_fraction":below/total,
        "volume_fully_solid_alpha1_zero_m3":fully
    }


def analyze(case: Path, analysis: Path, out: Path) -> dict:
    case=case.expanduser().absolute()
    analysis=analysis.expanduser().absolute()
    out=out.expanduser().absolute()
    require(not out.exists() and not out.is_symlink(),"output already exists; preserve data")
    require(out!=case and out!=analysis and out not in case.parents
            and out not in analysis.parents and case not in out.parents
            and analysis not in out.parents,
            "output must not overlap original CFD or its archived postrun")
    require(case.name==DEFAULT_CASE.name,"wrong CFD source, must be real Case B 10s")
    original,verification=base.validated_mesh_and_stage(case)
    rows,doc,manifest=verified_existing_analysis(analysis)
    require(Path(doc["input_CFD_source_read_only"]).resolve()==case.resolve(),
            "postrun provenance does not match this real native CFD")
    require(doc["all_native_log_diagnostics"]["native_end_found"] is True
            and doc["all_native_log_diagnostics"]["time_last_s"]==10.0,
            "postrun lacks completed original C14 10s source")
    require(manifest.get("native_stage_report_sha256")==sha(case/base.REPORT)
            and manifest.get("native_log_sha256")==sha(case/base.LOG),
            "native report/log changed after original postrun analysis")
    for path,h in original["five_native_mesh_files_per_region_SHA256"].items():
        if path.startswith("constant/"):
            require(sha(case/path)==h,"original native accepted polyMesh altered: "+path)
    volumes,geometry=calculate_native_metal_cell_volumes(
        case/"constant/metal/polyMesh")
    saved=base.saved_times(case)
    require([t for t,label in saved]==[float(r["time_s"]) for r in rows],
            "native times do not match certified 101-state postrun")
    series=[]
    for index,((t,label),old) in enumerate(zip(saved,rows),1):
        alpha=base.source_reader.scalar_field_values(
            case/label/"metal/phaseChangeSource:alpha1",EXPECTED_CELLS)
        weighted=weighted_phase(alpha,volumes)
        unweighted=math.fsum(alpha)/len(alpha)
        require(math.isclose(unweighted,float(old["alpha1_mean"]),
                             abs_tol=1e-10,rel_tol=1e-10),
                "C14 alpha1 source does not match already audited native CSV at "+label)
        series.append({"time_s":t,
                      "mean_liquid_fraction_cell_unweighted":unweighted,
                      **weighted})
        if index==1 or index%10==0 or index==len(saved):
            print(f"C3D05_B_REAL_VOLUME_ALPHA1_READONLY: {index}/{len(saved)} "
                  f"saved native states; time={t:g}s; NO_SOLVER",flush=True)
    result={
        "schema":"C3D05_B_C14_HEX8_NATIVE_VOLUME_WEIGHTED_ALPHA1_V1",
        "status":STATUS,
        "original_case_CFD_read_only":str(case),
        "source_postrun_read_only":str(analysis),
        "geometry":geometry,
        "saved_states":len(series),
        "C14_phase_liquidus_solidus_source":"original historical C14 physical reference",
        "first_volume_with_alpha1_below_0_999_saved_time":next(
            ({"first_saved_s":x["time_s"],
              "previous_saved_s":series[i-1]["time_s"] if i else None}
             for i,x in enumerate(series)
             if x["volume_with_alpha1_below_0_999_m3"]>0),None),
        "first_fully_solid_volume_saved_time":next(
            ({"first_saved_s":x["time_s"],
              "previous_saved_s":series[i-1]["time_s"] if i else None}
             for i,x in enumerate(series)
             if x["volume_fully_solid_alpha1_zero_m3"]>0),None),
        "last":series[-1],
        "final_volume_weighted_solid_complement_is_not_measured_shrinkage":True,
        "C14_constant_density_means_mass_and_volume_mean_equivalent_in_model":True,
        "physical_validity_QuickCup_JMatPro":False,
        "latent_energy_flux_balance_verified":False,
        "mesh_and_timestep_convergence_verified":False,
        "volume_weighting_calculated_from_real_hex8_geometry":True,
        "notes":[
            "This is C14 model liquid fraction weighted by real HEX8 cell volume, NOT a measurement of physical solid mass.",
            "Volume extraction triangulates native quad faces, so an independent comparison with actual OpenFOAM cell-volume field remains desirable.",
            "The 10s original native CFD is never rerun or modified.",
            "Original C14 hConst/rhoConst does not represent temperature-dependent eight QuickCup casts.",
            "No enthalpy, latent heat, external q balance, recalescence, shrinkage or feeding acceptance.",
        ]
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(out.parent),
                                     prefix="."+out.name+".staging.") as folder:
        work=Path(folder)/"candidate"
        work.mkdir()
        with (work/CSV_NAME).open("x",encoding="utf-8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows(series)
        (work/JSON_NAME).write_text(json.dumps(
            result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        (work/SHA_NAME).write_text(json.dumps({
            "source_real_10s_stage_sha256":sha(case/base.REPORT),
            "source_real_10s_log_sha256":sha(case/base.LOG),
            "source_already_audited_CSV_sha256":sha(analysis/base.CSV),
            "native_metal_mesh_SHA256":{
                name:sha(case/"constant/metal/polyMesh"/name)
                for name in ("points","faces","owner","neighbour")},
            "result_CSV_sha256":sha(work/CSV_NAME),
            "result_JSON_sha256":sha(work/JSON_NAME),
            "source_CFD_and_postrun_immutable":True,
        },indent=2)+"\n",encoding="utf-8")
        require(not out.exists() and not out.is_symlink(),
                "output created concurrently; preserving original")
        work.rename(out)
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case",type=Path,default=DEFAULT_CASE)
    parser.add_argument("--analysis",type=Path,default=DEFAULT_ANALYSIS)
    parser.add_argument("--out",type=Path,default=DEFAULT_OUTPUT)
    args=parser.parse_args()
    try:
        result=analyze(args.case,args.analysis,args.out)
        print(json.dumps({
            "status":result["status"],
            "output":str(args.out),
            "geometry":result["geometry"],
            "saved_states":result["saved_states"],
            "first_alpha1_change":result["first_volume_with_alpha1_below_0_999_saved_time"],
            "first_fully_solid_cell":result["first_fully_solid_volume_saved_time"],
            "final_liquid_volume_weighted":result["last"]["mean_liquid_fraction_volume_weighted"],
            "final_solid_complement_volume_weighted":result["last"]["mean_solid_complement_volume_weighted"],
            "physical_or_energy_balance_accepted":False,
            "NO_CFD_REEXECUTION":True
        },indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as exc:
        print("C3D05_B_VOLUME_WEIGHTED_READONLY_BLOCKED:",exc,file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
