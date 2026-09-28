#!/usr/bin/env python3
from pathlib import Path
import math, statistics

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"cases_controlled_buoyancy"
CASES=["B9_topFixedFlux","C9_topFixedFlux"]
PROFILES={
 "y20mm":("horizontalProfiles","line_y20mm.xy"),
 "y30mm":("horizontalProfiles","line_y30mm.xy"),
 "vertical_x20mm":("verticalProfiles","line_x20mm.xy"),
}
TARGETS=[0.1,1.0,2.5,5.0,7.5,10.0]

def read(path):
    rows=[]
    for line in path.read_text().splitlines():
        s=line.strip()
        if not s or s.startswith("#"): continue
        rows.append([float(x) for x in s.split()])
    return rows

def nearest_dir(root,t):
    ds=[]
    for p in root.iterdir():
        if p.is_dir():
            try: ds.append((abs(float(p.name)-t),float(p.name),p))
            except: pass
    return min(ds,key=lambda x:x[0])[2],min(ds,key=lambda x:x[0])[1]

def sign_crossings(xs,ys):
    z=[]
    for i in range(len(xs)-1):
        a,b=ys[i],ys[i+1]
        if a==0: z.append(xs[i])
        elif a*b<0:
            x=xs[i]+(-a)/(b-a)*(xs[i+1]-xs[i])
            z.append(x)
    return z

def extremum(xs,ys,mode):
    i=max(range(len(ys)),key=lambda k:ys[k]) if mode=="max" else min(range(len(ys)),key=lambda k:ys[k])
    return ys[i],xs[i]

def rms(v): return math.sqrt(sum(x*x for x in v)/len(v))

def symmetry_error(xs,ys):
    # assumes monotonic equally spaced line; compare mirrored samples
    n=len(ys)
    even=[abs(ys[i]-ys[n-1-i]) for i in range(n//2)]
    odd=[abs(ys[i]+ys[n-1-i]) for i in range(n//2)]
    scale=max(rms(ys),1e-30)
    return 100*rms(even)/scale,100*rms(odd)/scale

out=["# V9 velocity-profile morphology","",
     "Coordinates are reported in mm; velocities in m/s. Even/odd symmetry errors compare each profile with its mirror about the line midpoint and are normalized by profile RMS.",""]

for case in CASES:
    out += [f"## {case}",""]
    for pname,(folder,file) in PROFILES.items():
        out += [f"### {pname}","",
                "| t s | Ux min @ mm | Ux max @ mm | Uy min @ mm | Uy max @ mm | |U| max @ mm | Uy RMS | Uy zero crossings mm | Uy even err % | Uy odd err % |",
                "|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|"]
        root=BASE/case/"postProcessing"/"metal"/folder
        for t in TARGETS:
            d,actual=nearest_dir(root,t)
            r=read(d/file)
            x=[q[0] for q in r]; ux=[q[1] for q in r]; uy=[q[2] for q in r]
            um=[math.hypot(a,b) for a,b in zip(ux,uy)]
            uxmn=extremum(x,ux,"min"); uxmx=extremum(x,ux,"max")
            uymn=extremum(x,uy,"min"); uymx=extremum(x,uy,"max")
            umx=extremum(x,um,"max")
            z=sign_crossings(x,uy)
            ev,od=symmetry_error(x,uy)
            out.append(
              f"| {actual:g} | {uxmn[0]:.5g} @ {uxmn[1]*1000:.2f} | {uxmx[0]:.5g} @ {uxmx[1]*1000:.2f} | "
              f"{uymn[0]:.5g} @ {uymn[1]*1000:.2f} | {uymx[0]:.5g} @ {uymx[1]*1000:.2f} | "
              f"{umx[0]:.5g} @ {umx[1]*1000:.2f} | {rms(uy):.5g} | "
              f"{', '.join(f'{v*1000:.2f}' for v in z) if z else 'none'} | {ev:.2f} | {od:.2f} |"
            )
        out.append("")
( ROOT/"analysis_results"/"v9_velocity_profiles").mkdir(parents=True,exist_ok=True)
p=ROOT/"analysis_results"/"v9_velocity_profiles"/"summary.md"
p.write_text("\n".join(out)+"\n")
print(p.read_text())
