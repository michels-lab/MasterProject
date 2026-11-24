#!/usr/bin/env python3
"""Publish existing C14 A sweeps in FoamLens-readable profile and temporal files.
No CFD, no sampling replay, no modification of original native fields.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile

COLUMNS={"T_K":"T","alphaL":"phaseChangeSource:alpha1","Ux_m_s":"U_x","Uy_m_s":"U_y","Uz_m_s":"U_z",
         "U_mag_m_s":"U_mag","p_rgh_Pa":"p_rgh","gradTx_K_m":"gradT_x","gradTy_K_m":"gradT_y",
         "gradTz_K_m":"gradT_z","gradT_mag_K_m":"magGradT","Ur_m_s":"Ur","Utheta_m_s":"Utheta"}
SECTION=("T_K","alphaL","Ux_m_s","Uy_m_s","Uz_m_s","U_mag_m_s")
TIMES=[i/10 for i in range(101)]
NAME="FoamLensSweeps"

def need(ok,msg):
    if not ok:raise ValueError(msg)

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def rows(path):
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def value(r,key):
    raw=r.get(key)
    if raw is None or raw=="":return None
    n=float(raw)
    need(math.isfinite(n),"nonfinite source "+key)
    return n

def num(x):return "NaN" if x is None else format(x,".16g")

def group(rs,keys):
    out={}
    for r in rs:out.setdefault(tuple(r[k] for k in keys),[]).append(r)
    return out

def label(t):return format(float(t),"g")

def xy(path,axis,rs,coord,keys,suffix="",comment=""):
    # A time directory and explicit header are required by FoamLens.
    # Numeric NaN tokens preserve missing values, never synthesize zero.
    cols=[k for k in keys if any(value(r,k+suffix) is not None for r in rs)]
    need(len(cols)>=2,"insufficient profile columns: "+str(path))
    ordered=sorted(rs,key=coord)
    xx=[coord(r) for r in ordered]
    need(all(b>a for a,b in zip(xx,xx[1:])),"nonmonotone profile axis "+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        f.write("# Derived from existing C14 3D-A sweep CSV; "+comment+"\n")
        f.write("# "+axis+" "+" ".join(COLUMNS[k] for k in cols)+"\n")
        for x,r in zip(xx,ordered):
            vals=[value(r,k+suffix) for k in cols]
            if not any(v is not None for v in vals):continue
            f.write(" ".join([num(x)]+[num(v) for v in vals])+"\n")

def temporal(path,rs,keys,op,description):
    path.parent.mkdir(parents=True,exist_ok=True)
    cols=[k for k in keys if any(value(r,k) is not None for r in rs)]
    need(cols,"no temporal values")
    with path.open("x",encoding="utf-8") as f:
        f.write("# Derived aggregate; not a point probe. "+description+"\n")
        f.write("# Time "+" ".join(op+"("+COLUMNS[k.removesuffix("_mean")]+")" for k in cols)+"\n")
        for r in sorted(rs,key=lambda x:float(x["time_s"])):
            f.write(" ".join([num(float(r["time_s"]))]+[num(value(r,k)) for k in cols])+"\n")

def execute(src,case):
    src,case=src.expanduser().resolve(),case.expanduser().resolve()
    need(src!=case and src.parent==case.parent,"expected independent sibling cases")
    report=json.loads((src/"C3D04_A_MULTIDIRECTIONAL_REPORT.json").read_text())
    need(report["status"]=="MULTIDIRECTIONAL_3D_READY" and report["saved_times"]==101,
         "successful existing multidirectional output required")
    need(Path(report["source"]).resolve()==case,"sweep source is a different visualization case")
    need(report.get("source_report_sha_unchanged") is True and report.get("source_sampled_fields_and_dictionaries_sha_unchanged") is True,
         "source provenance not verified")
    vis=json.loads((case/"C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json").read_text())
    need(vis["status"]=="VISUALIZATION_AND_SOLIDIFICATION_READY","accepted case required")
    pp=case/"postProcessing/metal"
    need(pp.is_dir() and not pp.is_symlink(),"expected metal postProcessing")
    dest=pp/NAME
    if dest.exists():
        manifest=dest/"manifest.json"
        need(manifest.is_file(),"existing destination without manifest; preserved")
        previous=json.loads(manifest.read_text())
        need(previous["source"]==str(src) and all(sha(src/k)==v for k,v in previous["source_sha256"].items())
             and all(sha(dest/k)==v for k,v in previous["published_sha256"].items()),"existing output differs; preserved")
        return previous
    files=["diameters_101.csv","vertical_lines_101.csv","radial_statistics_101.csv","section_statistics_101.csv",
           "section_quadrature_points.csv","C3D04_A_MULTIDIRECTIONAL_REPORT.json"]
    hashes={name:sha(src/name) for name in files}
    d,v,r,s=[rows(src/name) for name in files[:4]]
    for name,rs in zip(files[:4],(d,v,r,s)):
        need(sorted({float(x["time_s"]) for x in rs})==TIMES,"not 101 native times: "+name)
    stage=Path(tempfile.mkdtemp(prefix=".foamlens-sweeps-",dir=case.parent))
    try:
        count={}
        for (t,h,a),rs in group(d,("time_s","height_mm","angle_deg")).items():
            a0=int(a); axis="z" if a0==90 else "x" if a0==0 else "distance"
            p=stage/"diameterProfiles"/label(t)/("height"+h+"_angle"+a+".xy")
            xy(p,axis,rs,lambda q:float(q["position_mm"])/1000,tuple(COLUMNS),
               comment="signed distance from section center (m); angles in filename, 135 orientation per source")
            count["diameters"]=count.get("diameters",0)+1
        for (t,line),rs in group(v,("time_s","line")).items():
            # Avoid x10mm/z10mm filename collapsing distinct lines in parser.
            p=stage/"verticalProfiles"/label(t)/(line+".xy")
            xy(p,"y",rs,lambda q:float(q["position_mm"])/1000,tuple(COLUMNS),
               comment="height from metal base (m), physical offsets in source manifest")
            count["verticals"]=count.get("verticals",0)+1
        for (t,h),rs in group(r,("time_s","height_mm")).items():
            for suffix,kind in (("_mean","radialMeanProfiles"),("_min","radialMinProfiles"),("_max","radialMaxProfiles"),("_std","radialStdProfiles")):
                p=stage/kind/label(t)/("height"+h+".xy")
                xy(p,"distance",rs,lambda q:float(q["radius_mm"])/1000,tuple(COLUMNS),suffix,
                   "radius (m); angular "+kind+"; not a point field")
                count[kind]=count.get(kind,0)+1
        for (h,),rs in group(s,("height_mm",)).items():
            # The 'probes' path is the FoamLens fast temporal dispatch; the
            # explicit header and absence of # Probe correctly avoid fake
            # thermocouple coordinates. It is a section aggregate.
            p=stage/("sectionHeight"+h)/"probes"/"0"/"sectionAreaApprox.dat"
            temporal(p,rs,tuple(k+"_mean" for k in SECTION),"areaAverage",
                     "midpoint quadrature, height "+h+" mm; approximate area mean")
            count["section_temporal"]=count.get("section_temporal",0)+1
        need(count.get("diameters")==1212 and count.get("verticals")==505
             and all(count.get(k)==303 for k in ("radialMeanProfiles","radialMinProfiles","radialMaxProfiles","radialStdProfiles"))
             and count.get("section_temporal")==3,"unexpected profile family coverage")
        raw=stage/"source_data"
        raw.mkdir()
        for name in files:shutil.copy2(src/name,raw/name)
        need(all(sha(src/k)==h and sha(raw/k)==h for k,h in hashes.items()),"input changed during publishing")
        manifest={"status":"FOAMLENS_SWEEPS_PUBLISHED","source":str(src),"case":str(case),
                  "destination":str(dest),"source_sha256":hashes,"counts":count,
                  "saved_times":101,"coordinate_units":"meters; FoamLens displays mm",
                  "diameter_coordinate":"signed distance from center, not absolute global X",
                  "vertical_coordinate":"physical height from base",
                  "radial_coordinate":"radius; distinct mean/min/max/std groups; derived aggregates",
                  "section_coordinate":"time; approximate midpoint area average, not point probe",
                  "missing_data":"NaN excluded by profile parser; raw CSV retains coverage; no extrapolation",
                  "source_solver_rerun":False,"native_sampling_rerun":False,
                  "published_sha256":{str(p.relative_to(stage)):sha(p) for p in stage.rglob("*") if p.is_file()}}
        (stage/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        need(not dest.exists(),"destination appeared; preserved")
        stage.rename(dest)
        return manifest
    finally:
        if stage.exists():shutil.rmtree(stage)

def main():
    h=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sweeps",type=Path,default=h/"C3D04_A_C14_MULTIDIRECTIONAL_01")
    p.add_argument("--case",type=Path,default=h/"C3D04_A_C14_VISUALIZATION_01")
    a=p.parse_args()
    try:
        r=execute(a.sweeps,a.case)
        print(json.dumps({k:v for k,v in r.items() if k not in ("source_sha256","published_sha256")},indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("FOAMLENS_SWEEPS_BLOCKED:",exc)
        return 2
if __name__=="__main__":raise SystemExit(main())
