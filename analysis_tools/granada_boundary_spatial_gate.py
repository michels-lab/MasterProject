#!/usr/bin/env python3
"""QuickCup per-face top boundary, metal-side interface and spatial-phase gate.

Read-only, source-backed numerical inspection. No OpenFOAM execution, no mesh
fabrication, no inferred mold-side measurements, no experimental validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

CASES = ("B14_topFixedFlux_explicitRef", "C14_topFixedFlux_explicitRef",
         "B15_adaptiveDt_fromB14", "C15_adaptiveDt_fromC14",
         "B16_phaseRelax025_fromB14", "C16_phaseRelax025_fromC14")
PROFILE_FILES = (("horizontalProfiles", "line_y10mm.xy"),
                 ("horizontalProfiles", "line_y20mm.xy"),
                 ("horizontalProfiles", "line_y30mm.xy"),
                 ("verticalProfiles", "line_x20mm.xy"))
FLOW_HEADER = ("face_x", "face_y", "face_z", "U_x", "U_y", "U_z", "phi")
POWER_HEADER = ("sum(energyAdvectiveFlux)", "sum(heatFlux)", "sum(energyFlux)")
TOP_HEADER = ("sum(phi)",)


def table(path: Path, expected=None, columns=None):
    """Numerical rows with required exact header, finite cells, ordered time."""
    if not path.is_file():
        raise ValueError(f"missing original: {path}")
    header = None
    data = []
    for lineno, line in enumerate(path.read_text(encoding="utf8", errors="replace").splitlines(), 1):
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            words = s[1:].split()
            if words and words[0] in ("Time", "face_x", "x", "y"):
                header = tuple(words)
            continue
        try:
            row = tuple(map(float, s.split()))
        except ValueError as err:
            raise ValueError(f"{path}:{lineno}: nonnumeric source row") from err
        if (columns is not None and len(row) != columns) or (expected is not None and len(row) != len(expected)):
            raise ValueError(f"{path}:{lineno}: wrong number of columns ({len(row)})")
        if not all(math.isfinite(v) for v in row):
            raise ValueError(f"{path}:{lineno}: NaN/Infinity in source")
        data.append(row)
    if not data:
        raise ValueError(f"{path}: no numeric samples")
    if expected is not None and header != tuple(expected):
        raise ValueError(f"{path}: unexpected field header {header}")
    return header, data


def time_dirs(path: Path):
    if not path.is_dir():
        raise ValueError(f"no original time directory: {path}")
    found = {}
    for p in path.iterdir():
        if not p.is_dir():
            continue
        try:
            t = float(p.name)
        except ValueError:
            continue
        if not math.isfinite(t) or t < 0:
            raise ValueError(f"invalid source time directory: {p}")
        key = round(t, 8)
        if key in found:
            raise ValueError(f"ambiguous duplicate time directory at {key}: {p}")
        found[key] = p
    if not found:
        raise ValueError(f"no physical-time folders: {path}")
    return dict(sorted(found.items()))


def keyed_times(path: Path, header):
    _, rows = table(path, ("Time",) + tuple(header))
    output = {}
    prev = -1
    for row in rows:
        t = round(row[0], 8)
        if t <= prev or row[0] < 0:
            raise ValueError(f"{path}: repeated/out-of-order times")
        prev = t
        output[t] = row[1:]
    return output


def read_hash(path: Path, provenance):
    provenance.append({"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})


def all_face_evidence(case: Path, provenance):
    root = case/"postProcessing"/"metal"
    flow = time_dirs(root/"topFlow")
    patch = time_dirs(root/"topPatchFaceFields")
    top_phi = keyed_times(root/"metalTopPhiSum"/"0"/"surfaceFieldValue.dat", TOP_HEADER)
    for n in ("metalTopPhiSum",):
        read_hash(root/n/"0"/"surfaceFieldValue.dat", provenance)
    snapshots = []
    alerts = []
    first_geometry = None
    total_compared = 0
    for t, directory in flow.items():
        source = directory/"patch(metalTop).xy"
        _, data = table(source, FLOW_HEADER)
        read_hash(source, provenance)
        xyz = [tuple(row[:3]) for row in data]
        if len(set(xyz)) != len(xyz):
            alerts.append(f"{t}s: duplicate face coordinates")
        if first_geometry is None:
            first_geometry = xyz
        elif xyz != first_geometry:
            alerts.append(f"{t}s: changed top face centroid sequence; verify moving mesh and mapping")
        net = math.fsum(r[6] for r in data)
        absolute = math.fsum(abs(r[6]) for r in data)
        if t not in top_phi:
            alerts.append(f"{t}s: no matching source metalTopPhiSum")
        elif abs(net - top_phi[t][0]) > 1e-12 + 1e-6*max(abs(net), abs(top_phi[t][0])):
            alerts.append(f"{t}s: per-face phi differs from summed diagnostic")
        extra_phi = None
        if t in patch:
            other = patch[t]/"patch(metalTop).xy"
            hdr, other_rows = table(other)
            read_hash(other, provenance)
            if len(other_rows) != len(data):
                alerts.append(f"{t}s: top patch face count differs")
            elif hdr is None or any(x not in hdr for x in ("face_x","face_y","face_z","U_x","U_y","U_z")):
                alerts.append(f"{t}s: patch diagnostic lacks documented field identities")
            elif [tuple(x[hdr.index(c)] for c in ("face_x","face_y","face_z")) for x in other_rows] != xyz:
                alerts.append(f"{t}s: patch face centroid order differs")
            else:
                total_compared += 1
                for i, (a, b) in enumerate(zip(data, other_rows)):
                    for c, j in (("U_x",3),("U_y",4),("U_z",5)):
                        if abs(a[j] - b[hdr.index(c)]) > 1e-9 + 1e-5*max(abs(a[j]),abs(b[hdr.index(c)])):
                            alerts.append(f"{t}s face {i}: inconsistent {c} between diagnostic sources")
                            break
                if "phi" in hdr:
                    extra_phi = sum(abs(a[6]-b[hdr.index("phi")]) > 1e-12 for a,b in zip(data,other_rows))
                    if extra_phi:
                        alerts.append(f"{t}s: phi differs on {extra_phi} face(s)")
        else:
            alerts.append(f"{t}s: topPatchFaceFields output missing")
        snapshots.append({
            "time_s":t, "face_count":len(data),
            "net_phi_kg_s":net, "sum_abs_face_phi_kg_s":absolute,
            "max_abs_face_phi_kg_s":max(abs(r[6]) for r in data),
            "max_abs_face_Uy_m_s":max(abs(r[4]) for r in data),
            "max_abs_tangential_U_m_s":max(math.hypot(r[3],r[5]) for r in data),
            "net_phi_cancellation_ratio":abs(net)/absolute if absolute else None,
            "patch_phi_differences":extra_phi,
        })
    if len(flow) != len(patch):
        alerts.append("topFlow and topPatchFaceFields have different snapshot counts")
    if any(s["sum_abs_face_phi_kg_s"] > 1e-12 for s in snapshots):
        alerts.append("nonzero facewise top mass flux: net sum could hide cancellation")
    if any(s["max_abs_face_Uy_m_s"] > 1e-9 for s in snapshots):
        alerts.append("nonzero facewise top normal velocity Uy: inspect BC and normals")
    return {"snapshots":snapshots,"checked_patch_times":total_compared,
            "face_count":len(first_geometry or []),"alerts":alerts,
            "source_time_count":len(flow),"reference_sum_times":len(top_phi)}


def powers(case: Path, provenance):
    root = case/"postProcessing"/"metal"
    names = ("metalMoldEnergyPower", "metalTopEnergyPower", "metalBoundaryEnergyPower")
    samples = {}
    for name in names:
        source=root/name/"0"/"surfaceFieldValue.dat"
        samples[name]=keyed_times(source, POWER_HEADER)
        read_hash(source, provenance)
    common = sorted(set.intersection(*(set(x) for x in samples.values())))
    issues = []
    if len(common) < 2:
        issues.append("insufficient common energy write times")
    if any(len(data) != len(common) for data in samples.values()):
        issues.append("energy diagnostics have unmatched source time grids")
    max_flux_disagreement = 0.
    rows=[]
    for t in common:
        top, mold, boundary=(samples[n][t] for n in names)
        for j, label in enumerate(("advective","heat","total")):
            difference=boundary[j]-top[j]-mold[j]
            max_flux_disagreement=max(max_flux_disagreement,abs(difference))
            if abs(difference) > 1e-3 + 1e-5*max(abs(boundary[j]),abs(top[j]),abs(mold[j])):
                issues.append(f"{t}s: metal boundary partition mismatch {label}")
        for name, source in zip(names, (mold, top, boundary)):
            if abs(source[0]+source[1]-source[2])>1e-3 + 1e-5*abs(source[2]):
                issues.append(f"{t}s: energyFlux arithmetic mismatch {name}")
        rows.append({"time_s":t,"metal_to_mold_total_W":mold[2],
                     "metal_top_total_W":top[2],"metal_boundary_total_W":boundary[2]})
    return {"metal_side":rows, "max_partition_abs_difference_W":max_flux_disagreement,
            "mold_side_status":"NOT_OBSERVED_NO_MOLD_POSTPROCESSING",
            "bilateral_reciprocity_verified":False, "alerts":issues}


def phase_profiles(case: Path, provenance, liquid_limit=0.95, solid_limit=0.05):
    base=case/"postProcessing"/"metal"
    records=[]
    alerts=[]
    for folder, filename in PROFILE_FILES:
        tdirs=time_dirs(base/folder)
        for t, d in tdirs.items():
            path=d/filename
            hdr, data=table(path, columns=27)
            read_hash(path, provenance)
            # This QuickCup-specific index is verified against native profile
            # definitions: coord, U(3), T, p_rgh, rho, phaseChangeSource:alpha1.
            if hdr is None or not hdr[0] in ("x","y") or len(hdr)!=27:
                alerts.append(f"{t}s {filename}: unknown profile field header")
                continue
            alpha=[r[7] for r in data]
            if any(a < -1e-6 or a > 1+1e-6 for a in alpha):
                alerts.append(f"{t}s {filename}: invalid liquid fraction")
            records.append({
                "time_s":t,"profile":filename,"samples":len(alpha),
                "min_alphaL":min(alpha),"max_alphaL":max(alpha),
                "mean_sample_alphaL":math.fsum(alpha)/len(alpha),
                "solid_sample_fraction":sum(a<=solid_limit for a in alpha)/len(alpha),
                "mushy_sample_fraction":sum(solid_limit<a<liquid_limit for a in alpha)/len(alpha),
                "liquid_sample_fraction":sum(a>=liquid_limit for a in alpha)/len(alpha),
            })
    return {"profiles":records,"source_profile_count":len(records),
            "classification":{"solid_at_or_below":solid_limit,"liquid_at_or_above":liquid_limit},
            "interpretation":"sampled 2D line values only, not cell-volume fractions, dendrite morphology or true front velocity",
            "alerts":alerts}


def inspect(root: Path):
    cases=[]
    for name in CASES:
        original = root/"cases_controlled_buoyancy"/name
        sources=[]
        issues=[]
        sections={}
        for label, fn in (("top_boundary",all_face_evidence),("metal_interface",powers),("spatial_phase",phase_profiles)):
            try:
                result=fn(original,sources)
                sections[label]=result
                issues.extend(f"{label}: {issue}" for issue in result.get("alerts",[]))
            except (ValueError,OSError) as err:
                sections[label]=None
                issues.append(f"{label}: {err}")
        digest=hashlib.sha256()
        for s in sorted(sources,key=lambda x:x["path"]):
            digest.update((s["path"].removeprefix(str(original))+" "+s["sha256"]+"\n").encode())
        cases.append({"case":name,"sections":sections,"source_file_count":len(sources),
                      "source_manifest_sha256":digest.hexdigest(),
                      "status":"REVIEW" if issues else "NUMERIC_SCREEN_PASSED",
                      "alerts":issues})
    return {"schema":"quickcup-boundary-spatial-evidence-v1",
            "data_source":"original committed QuickCup OpenFOAM postProcessing only",
            "scientific_status":"PARTIAL_METAL_SIDE_AND_LINE_SAMPLE_EVIDENCE_ONLY",
            "mold_interface_reciprocity":"NOT_OBSERVED",
            "cfd_executed":False,"experimental_validation":False,"cases":cases}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args(argv)
    root=args.root.resolve()
    out=args.out.resolve()
    if out==root or root/"cases_controlled_buoyancy"==out or root/"cases_controlled_buoyancy" in out.parents:
        parser.error("refusing to write into original CFD case tree")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("destination is not empty; refusing to overwrite prior evidence")
    report=inspect(root)
    out.mkdir(parents=True,exist_ok=True)
    (out/"evidence.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    with (out/"summary.csv").open("w",encoding="utf8",newline="") as f:
        cols=("case","status","top_snapshots","top_face_count","max_abs_phi_kg_s",
              "mold_energy_samples","spatial_profiles","source_files","alerts")
        writer=csv.DictWriter(f,fieldnames=cols)
        writer.writeheader()
        for c in report["cases"]:
            b=c["sections"]["top_boundary"] or {}
            p=c["sections"]["metal_interface"] or {}
            s=c["sections"]["spatial_phase"] or {}
            writer.writerow({"case":c["case"],"status":c["status"],"top_snapshots":b.get("source_time_count"),
                            "top_face_count":b.get("face_count"),
                            "max_abs_phi_kg_s":max((x["max_abs_face_phi_kg_s"] for x in b.get("snapshots",[])),default=None),
                            "mold_energy_samples":len(p.get("metal_side",[])),
                            "spatial_profiles":s.get("source_profile_count"),
                            "source_files":c["source_file_count"],"alerts":"; ".join(c["alerts"])[:1600]})
    n=sum(bool(c["alerts"]) for c in report["cases"])
    print(f"Boundary/spatial evidence: {len(report['cases'])} cases; cases_with_alerts={n}")
    print("Mold-side flux: NOT OBSERVED; no CFD or experimental validation")
    return int(args.strict and n>0)


if __name__=="__main__":
    raise SystemExit(main())
