#!/usr/bin/env python3
"""Analyze published corrected C14 B snapshots; stdlib only, never runs CFD.

Source trees are read-only. Outputs are a separate case-like postProcessing
tree, CSV metrics, and provenance. No spatial extrapolation or time interpolation.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess

CENTER=.0259
BOTTOM=-.04
THRESHOLD=.0001  # m/s; 0.1 mm/s
TIMES=[i/10 for i in range(101)]
REPORT="C3D05_B_C14_CORRECTED_SAMPLING_REPORT.json"
REQUIRED=("U_x","U_y","U_z","T","phaseChangeSource:alpha1")
def need(ok,msg):
    if not ok: raise ValueError(msg)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def revision(p):
    return subprocess.check_output(["git","-C",str(p),"rev-parse","HEAD"],text=True).strip()
def read_xy(p,axis,fields):
    lines=p.read_text().splitlines()
    need(lines and lines[0].lstrip().startswith("#"),f"missing header {p}")
    header=lines[0].lstrip().lstrip("#").split()
    need(header[0]==axis,f"wrong axis {p}")
    aliases={"phaseChang...":"phaseChangeSource:alpha1"}
    header=[aliases.get(x,x) for x in header]
    need(len(header)==len(set(header)) and all(k in header for k in fields),f"missing or duplicate columns {p}")
    rows=[]
    for s in lines[1:]:
        if not s.strip() or s.lstrip().startswith("#"): continue
        v=list(map(float,s.split()))
        need(len(v)==len(header) and all(math.isfinite(x) and abs(x)<1e100 for x in v),f"invalid sample {p}")
        rows.append(dict(zip(header,v)))
    need(len(rows)>1 and all(b[axis]>a[axis] for a,b in zip(rows,rows[1:])),f"invalid coordinate grid {p}")
    return rows
def xyz(row,s):
    axis="xyz".index(s["axis"])
    a,b=s["start"],s["end"]
    f=(row[s["axis"]]-a[axis])/(b[axis]-a[axis])
    need(-1e-5<=f<=1+1e-5,"coordinate outside requested line")
    return tuple(x+f*(y-x) for x,y in zip(a,b))
def components(row,s):
    x,y,z=xyz(row,s)
    dx,dz=x-CENTER,z-CENTER
    r=math.hypot(dx,dz)
    u,v,w=(row["U_"+k] for k in "xyz")
    # At r=0 radial/tangential directions are undefined, not zero.
    ur,ut=(None,None) if r<1e-10 else ((u*dx+w*dz)/r,(-u*dz+w*dx)/r)
    signed=None
    if s["axis"]!="y":
        a,b=s["start"],s["end"]
        L=math.hypot(b[0]-a[0],b[2]-a[2])
        signed=(dx*(b[0]-a[0])+dz*(b[2]-a[2]))/L
    return x,y,z,r,signed,math.hypot(u,v,w),ur,ut
def cls(v): return -1 if v<-THRESHOLD else 1 if v>THRESHOLD else 0
def rms(v): return math.sqrt(sum(x*x for x in v)/len(v)) if v else None
def mean(v): return sum(v)/len(v) if v else None
def fmt(x): return "" if x is None else format(x,".10g")
def dump_csv(p,rows):
    need(rows,f"no rows {p}")
    with p.open("x",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def compare(b,a,axis):
    # Both original nominal C14 lines use 0.5 mm spacing. Match coordinates
    # in physical m, no interpolation, only common sample stations.
    offset=.0059 if axis=="x" else -.04
    lookup={round(r[axis]+offset,7):r for r in a}
    pairs=[(r,lookup[round(r[axis],7)]) for r in b if round(r[axis],7) in lookup]
    need(len(pairs)>1,"no overlapping stations")
    out={"n_common":len(pairs)}
    for f in ("U_y","T","phaseChangeSource:alpha1"):
        diff=[r[f]-q[f] for r,q in pairs]
        out["rmse_"+f]=rms(diff)
        out["bias_"+f]=mean(diff)
    out["opposite_Uy_sign_points"]=sum(cls(r["U_y"])*cls(q["U_y"])==-1 for r,q in pairs)
    return out
def run(b,ref,out):
    b,ref,out=b.resolve(),ref.resolve(),out.resolve()
    need(not out.exists() and all(out!=p and p not in out.parents for p in (b,ref)),"output must be new, separate from sources")
    report=json.loads((b/REPORT).read_text())
    need(report["status"]=="CORRECTED_SAVED_TIME_SAMPLING_VALID" and report["checked_original_evidence_unchanged"],"unaccepted source")
    groups=report["profiles"]
    need(sum(map(len,groups.values()))==17,"unexpected profile count")
    metrics=[];comparisons=[];events=[];transitions=[];manifest={}
    out.mkdir(parents=True)
    for group,lines in groups.items():
        for name,s in lines.items():
            axis=s["axis"]
            history=[];prior=None;grid=None
            for t in TIMES:
                label=format(t,"g")
                p=b/"postProcessing/metal"/("C14Canonical"+group)/label/(name+".xy")
                rows=read_xy(p,axis,REQUIRED)
                coords=[r[axis] for r in rows]
                need(grid is None or coords==grid,f"grid changed {p}")
                grid=coords
                manifest[str(p.relative_to(b))]=sha(p)
                velocity=[r["U_y"] for r in rows]
                flags=[cls(v) for v in velocity]
                c=[components(r,s) for r in rows]
                radial=[x[6] for x in c if x[6] is not None]
                tangential=[x[7] for x in c if x[7] is not None]
                n=len(rows)
                rec={"group":group,"profile":name,"time_s":t,"n":n,
                     "Uy_min_m_s":min(velocity),"Uy_max_m_s":max(velocity),
                     "down_points":flags.count(-1),"up_points":flags.count(1),"deadband_points":flags.count(0),
                     "down_fraction":flags.count(-1)/n,"speed_max_m_s":max(x[5] for x in c),
                     "radial_rms_m_s":rms(radial),"tangential_rms_m_s":rms(tangential),
                     "T_min_K":min(r["T"] for r in rows),"T_max_K":max(r["T"] for r in rows),
                     "alpha1_mean_line_samples":mean([r["phaseChangeSource:alpha1"] for r in rows])}
                metrics.append(rec);history.append(rec)
                if prior is not None:
                    for i,(a,d) in enumerate(zip(prior,flags)):
                        if a*d==-1: events.append({"group":group,"profile":name,"coordinate_m":coords[i],
                            "previous_t_s":round(t-.1,1),"observed_t_s":t,"from_sign":a,"to_sign":d})
                prior=flags
                dst=out/"postProcessing/metal"/("C14Directional"+group)/label/(name+".xy")
                dst.parent.mkdir(parents=True,exist_ok=True)
                with dst.open("x") as f:
                    f.write("# "+axis+" U_x U_y U_z T phaseChangeSource:alpha1 U_mag U_radial U_tangential\n")
                    for r,x in zip(rows,c):
                        # All existing nominal sample lines omit r=0 or are off-axis,
                        # except central vertical: do not invent radial values there.
                        if x[6] is None: continue
                        f.write(" ".join(fmt(v) for v in [r[axis],r["U_x"],r["U_y"],r["U_z"],r["T"],r["phaseChangeSource:alpha1"],x[5],x[6],x[7]])+"\n")
                if not radial: dst.unlink()
                if group in ("horizontalProfilesB3D","verticalProfilesB3D"):
                    family="horizontalProfiles" if axis=="x" else "verticalProfiles"
                    q=ref/"postProcessing/metal"/family/label/(name+".xy")
                    a=read_xy(q,axis,REQUIRED)
                    comparisons.append({"group":group,"profile":name,"time_s":t,**compare(rows,a,axis)})
            last_down=max((r["time_s"] for r in history if r["down_points"]),default=None)
            transitions.append({"group":group,"profile":name,"last_observed_down_s":last_down,
                "first_subsequent_no_down_s":next((r["time_s"] for r in history if last_down is not None and r["time_s"]>last_down),None),
                "note":"threshold; only saved states; not section/volume fraction"})
    dump_csv(out/"line_temporal_metrics.csv",metrics)
    dump_csv(out/"c14_2d_common_station_metrics.csv",comparisons)
    dump_csv(out/"last_downward_observation.csv",transitions)
    if events: dump_csv(out/"adjacent_opposite_sign_events.csv",events)
    result={"status":"PUBLISHED_PROFILE_ANALYSIS_COMPLETE","source_revision":revision(b),"reference_revision":revision(ref),
            "source_report_sha256":sha(b/REPORT),"source_xy_sha256":manifest,"source_profiles":17,
            "saved_states":101,"profile_time_metrics":len(metrics),"comparison_time_metrics":len(comparisons),
            "adjacent_opposite_sign_events":len(events),"threshold_m_s":THRESHOLD,
            "direction_convention":"radial outward in XZ; tangential (-dz,0,dx)/r; undefined at axis",
            "limitations":["sampled lines not section averages","direct opposite-sign events exclude deadband-mediated transitions",
              "2D and B different geometries; no causal attribution","no new CFD; no native 1ms B histories","FoamLens import not verified"],
            "stage":"3/7","hitos":"2/7 = 29%"}
    (out/"ANALYSIS_REPORT.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="source_xy_sha256"},indent=2))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--b",type=Path,required=True)
    p.add_argument("--ref",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();run(a.b,a.ref,a.out)
if __name__=="__main__": main()
