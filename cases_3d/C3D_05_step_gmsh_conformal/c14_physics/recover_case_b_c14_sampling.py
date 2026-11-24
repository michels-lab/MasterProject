#!/usr/bin/env python3
"""Recover geometry-correct C14-B sampling from saved fields; never run CFD.

Uses the existing independent offline workspace, not the original CFD.
New function object names preserve failed historical samples. Raw XY output,
explicit coordinate metadata and an audit are stored inside the offline case.
Optional publication uses a separate detached worktree and results branch.
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
import time

import POSTPROCESAR_CASO_B_C14_EXISTENTE as old

CENTER = .0259
BOTTOM = -.04
TIMES = [i/10 for i in range(101)]
BASIC = ("U", "T", "p_rgh", "phaseChangeSource:alpha1",
         "vorticity", "flowType", "gradT", "magGradT")
DENSITY = ("rho", "gradRho", "magGradRho", "CoCell")
VECTORS = {"U", "vorticity", "gradT", "gradRho"}
PROBE = "temperatureProbeB3D"
REPORT = "C3D05_B_C14_CORRECTED_SAMPLING_REPORT.json"
FOLDER = "C14_B_CORRECTED_SAMPLING"
PUBLISHED_PARENT = "2257ac295981c081391a23b318ee9f766bd32145"

def need(ok, message):
    if not ok:
        raise ValueError(message)

def vec(p):
    return "(" + " ".join(format(v, ".12g") for v in p) + ")"

def mapping():
    groups = {"horizontalProfilesB3D": {}, "verticalProfilesB3D": {},
              "additional3DProfilesB": {}}
    for h in (10,20,30):
        y = BOTTOM+h/1000
        for angle in (0,45,90,135):
            rad=math.radians(angle)
            dx,dz=math.cos(rad),math.sin(rad)
            if angle==135: dx,dz=-dx,-dz
            if abs(dx)<1e-12: dx=0.
            if abs(dz)<1e-12: dz=0.
            a=(CENTER-.01975*dx,y,CENTER-.01975*dz)
            b=(CENTER+.01975*dx,y,CENTER+.01975*dz)
            group="horizontalProfilesB3D" if angle==0 else "additional3DProfilesB"
            name=f"line_y{h}mm" if angle==0 else f"height{h}_angle{angle}"
            groups[group][name]={"start":a,"end":b,"axis":"z" if angle==90 else "x",
                                 "requested_points":80,"height_mm":h,"angle_deg":angle}
    for name,x,z in (("line_x20mm",CENTER,CENTER),
                     ("vertical_xplus10",CENTER+.01,CENTER),
                     ("vertical_xminus10",CENTER-.01,CENTER),
                     ("vertical_zplus10",CENTER,CENTER+.01),
                     ("vertical_zminus10",CENTER,CENTER-.01)):
        group="verticalProfilesB3D" if name=="line_x20mm" else "additional3DProfilesB"
        groups[group][name]={"start":(x,BOTTOM+.00025,z),"end":(x,-.00025,z),
                             "axis":"y","requested_points":80}
    return (CENTER,-.02,CENTER),groups

def names(fields):
    return [n for field in fields for n in (
        [field+"_x",field+"_y",field+"_z"] if field in VECTORS else [field])]

def blocks(probe,groups,fields,suffix):
    out=[]
    out.append(f"""{PROBE}{suffix}
{{
 type probes;
 libs ("libfieldFunctionObjects.so");
 region metal;
 fields ({" ".join(fields)});
 probeLocations ({vec(probe)});
 executeControl timeStep;
 executeInterval 1;
 writeControl timeStep;
 writeInterval 1;
 writeToFile true;
}}
""")
    for group,lines in groups.items():
        body=f"""{group}{suffix}
{{
 type sets;
 libs ("libsampling.so");
 region metal;
 writeControl writeTime;
 interpolationScheme cellPoint;
 setFormat raw;
 fields ({" ".join(fields)});
 sets
 {{
"""
        for name,s in lines.items():
            body+=f"""  {name}
  {{
   type lineUniform;
   axis {s["axis"]};
   start {vec(s["start"])};
   end {vec(s["end"])};
   nPoints 80;
  }}
"""
        out.append(body+" }\n}\n")
    return out

def numeric_rows(path,width):
    need(path.is_file(),f"missing output {path}")
    result=[]
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        row=[float(v) for v in line.replace("("," ").replace(")"," ").split()]
        # OpenFOAM's outside-domain sentinel is finite, so isfinite alone fails.
        need(len(row)==width and all(math.isfinite(v) and abs(v)<1e100 for v in row),
             f"invalid/sentinel data {path}")
        result.append(row)
    need(result,f"empty output {path}")
    return result

def exact_times(rows,expected):
    return len(rows)==len(expected) and all(abs(row[0]-t)<1e-8 for row,t in zip(rows,expected))

def canonical_header(path,axis,fields):
    header=path.read_text().splitlines()[0].lstrip("#").split()
    expected=[axis]+names(fields)
    # Raw writer can truncate long names; only accept matching ordered prefixes.
    need(len(header)==len(expected),f"unexpected raw width: {path}: {header}")
    for observed,target in zip(header,expected):
        prefix=observed.removesuffix("...")
        need(observed==target or (observed.endswith("...") and len(prefix)>=8 and target.startswith(prefix)),
             f"unexpected raw column {observed} vs {target}: {path}")
    return expected

def sha(path):
    return old.sha(path)

def write_report(path,report):
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

def audit(work,groups,fields,suffix,expected):
    pp=work/"postProcessing/metal"
    result={"probes":{},"profiles":{}}
    for field in fields:
        candidates=list((pp/(PROBE+suffix)).glob("*/"+field))
        need(len(candidates)==1,f"ambiguous/missing probe {field}: {candidates}")
        rows=numeric_rows(candidates[0],4 if field in VECTORS else 2)
        need(exact_times(rows,expected),f"wrong probe cadence {field}")
        if field=="T": need(all(250<r[1]<2500 for r in rows),"unphysical probe T")
        if field=="phaseChangeSource:alpha1":
            need(all(-1e-6<=r[1]<=1+1e-6 for r in rows),"invalid liquid fraction")
        result["probes"][field]={"samples":len(rows),"first":rows[0],"last":rows[-1]}
    for group,lines in groups.items():
        for name,s in lines.items():
            counts=[]
            for t in expected:
                path=pp/(group+suffix)/format(t,"g")/(name+".xy")
                header=canonical_header(path,s["axis"],fields)
                rows=numeric_rows(path,len(header))
                need(1<len(rows)<=80,f"bad spatial coverage {path}")
                need(all(b[0]>a[0] for a,b in zip(rows,rows[1:])),
                     f"nonmonotone raw coordinate {path}")
                lo,hi=sorted((s["start"]["xyz".index(s["axis"])],
                              s["end"]["xyz".index(s["axis"])]))
                need(all(lo-1e-6<=r[0]<=hi+1e-6 for r in rows),f"coordinate outside requested line {path}")
                counts.append(len(rows))
                # Explicit canonical header for FoamLens, same native samples.
                target=pp/("C14Canonical"+group+suffix)/format(t,"g")/path.name
                target.parent.mkdir(parents=True,exist_ok=True)
                raw=path.read_text().splitlines(keepends=True)
                with target.open("x") as f: f.write("# "+" ".join(header)+"\n"+"".join(raw[1:]))
            result["profiles"][group+"/"+name]={"time_files":len(counts),"min_points":min(counts),
                "max_points":max(counts),"partial_spatial_coverage":any(n<80 for n in counts)}
    return result

def self_test():
    import tempfile
    probe,groups=mapping()
    need(probe==(.0259,-.02,.0259),"center mapping")
    need(sum(map(len,groups.values()))==17,"profile count")
    need(abs(groups["horizontalProfilesB3D"]["line_y10mm"]["start"][1]+.03)<1e-12,"height")
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"probe"
        p.write_text("# test\n0 -1.79769e+307\n")
        try: numeric_rows(p,2)
        except ValueError: pass
        else: raise AssertionError("sentinel accepted")
        p.write_text("# x phaseChang...\n0.01 1\n")
        need(canonical_header(p,"x",("phaseChangeSource:alpha1",))==["x","phaseChangeSource:alpha1"],"raw header abbreviation")
        p.write_text("# test\n0 1500\n0.1 1499\n")
        need(exact_times(numeric_rows(p,2),[0,.1]),"valid samples rejected")
    print("Sampling mapping and invalid-data regression PASS",flush=True)

def publish(work,repo,groups):
    stamp=time.strftime("%Y%m%d-%H%M%S")
    pub=work.parent/("C3D05_B_SAMPLING_PUBLICATION_"+stamp)
    branch="results/c3d05-b-c14-corrected-"+stamp
    def git(*args,cwd=repo):
        subprocess.run(["git","-C",str(cwd),*args],check=True)
    git("fetch","origin")
    git("worktree","add","--detach",str(pub),PUBLISHED_PARENT)
    dest=pub/"analysis_results/C3D05_B_C14"/("corrected-"+stamp)
    dest.mkdir(parents=True)
    pp=work/"postProcessing/metal"
    for suffix in ("","Density"):
        for group in (PROBE,*groups,*("C14Canonical"+g for g in groups)):
            src=pp/(group+suffix)
            shutil.copytree(src,dest/"postProcessing/metal"/src.name)
    shutil.copytree(work/"system"/FOLDER,dest/"system"/FOLDER)
    shutil.copy2(work/REPORT,dest/REPORT)
    for path in work.glob("log.C14B.corrected.*"): shutil.copy2(path,dest/path.name)
    need(all(p.stat().st_size<90_000_000 for p in dest.rglob("*") if p.is_file()),"oversized publication")
    git("add","--",str(dest.relative_to(pub)),cwd=pub)
    git("--no-pager","diff","--cached","--stat",cwd=pub)
    git("commit","-m","results: recovered geometry-correct B C14 sampling",cwd=pub)
    git("push","origin","HEAD:refs/heads/"+branch,cwd=pub)
    print("PUBLICACION COMPLETADA\nRAMA: "+branch,flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--publish",action="store_true")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--publish-only",action="store_true",help="retry publication after a successful local audit")
    args=p.parse_args()
    self_test()
    if args.self_test: return 0
    source,work=old.ORIGINAL,old.WORK
    if args.publish_only:
        report=json.loads((work/REPORT).read_text())
        need(report.get("status")=="CORRECTED_SAVED_TIME_SAMPLING_VALID","no accepted correction to publish")
        publish(work,old.REPO,mapping()[1])
        return 0
    saved,_=old.existing_states(source)
    need(work.is_dir() and not work.is_symlink(),"offline workspace missing")
    prior=json.loads((work/old.REPORT).read_text())
    need(prior["source_solver_log_SHA256"]==sha(source/old.SOLVERLOG),"source mismatch")
    need(prior["source_controlDict_SHA256"]==sha(work/"system/controlDict")==sha(source/"system/controlDict"),"controlDict mismatch")
    need(os.environ.get("WM_PROJECT_VERSION")=="14" and shutil.which("foamPostProcess"),"activate Foundation14")
    for name in ("points","faces","owner","neighbour","boundary"):
        rel=Path("constant/metal/polyMesh")/name
        need(sha(work/rel)==sha(source/rel),"mesh mismatch "+name)
    tracked=[source/old.SOLVERLOG,source/"system/controlDict",source/"10/metal/T",work/"system/controlDict"]
    before={str(p):sha(p) for p in tracked}
    for fields,states in ((BASIC,saved),(DENSITY,saved[1:])):
        for _,name in states:
            for field in fields:
                path=work/name/"metal"/field
                need(path.is_file() and not path.is_symlink(),f"saved field missing {path}")
    probe,groups=mapping()
    folder=work/"system"/FOLDER
    pp=work/"postProcessing/metal"
    need(not folder.exists() and not (work/REPORT).exists(),"previous correction exists; preserve it")
    for suffix in ("","Density"):
        for group in (PROBE,*groups,*("C14Canonical"+g for g in groups)):
            need(not (pp/(group+suffix)).exists(),f"prior output {group+suffix}")
    folder.mkdir()
    report={"status":"RUNNING","source":str(source),"workspace":str(work),
            "source_publication_commit":PUBLISHED_PARENT,"probe_xyz_m":probe,"profiles":groups,
            "original_solver_dt_s":.001,"archived_dt_s":.1,"solver_rerun":False,
            "runtime_1ms_recovered":False,"rho_at_t0_available":False,
            "axis_note":"Global XYZ in m; diagonal X projection, not radial distance. Height is Y+0.04 m.",
            "native_source_fields_only":True,"foamLens_import_verified":False,
            "stage":"3/7","hitos":"2/7 = 29%","coverage":{}}
    try:
        for fields,suffix,expected,label in ((BASIC,"",TIMES,"0:10"),(DENSITY,"Density",TIMES[1:],"0.1:10")):
            dictionary=folder/("sampling"+suffix)
            old.fo_dict(dictionary,blocks(probe,groups,fields,suffix))
            print("Recovering native saved samples "+label,flush=True)
            with (work/("log.C14B.corrected."+("density" if suffix else "basic"))).open("x") as log:
                subprocess.run(["foamPostProcess","-case",str(work),"-region","metal",
                     "-dict",str(dictionary),"-time",label,"-fields","("+" ".join(fields)+")"],
                     cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
            report["coverage"][suffix or "basic"]=audit(work,groups,fields,suffix,expected)
        need(all(sha(Path(k))==v for k,v in before.items()),"original evidence changed")
        report["status"]="CORRECTED_SAVED_TIME_SAMPLING_VALID"
        report["checked_original_evidence_unchanged"]=True
        write_report(work/REPORT,report)
        if args.publish: publish(work,old.REPO,groups)
        print(json.dumps(report,indent=2))
        return 0
    except Exception as exc:
        if report["status"]!="CORRECTED_SAVED_TIME_SAMPLING_VALID":
            report["status"]="BLOCKED_OR_PARTIAL_PRESERVED"
            report["error"]=str(exc)
            write_report(work/REPORT,report)
        raise

if __name__=="__main__":
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,subprocess.SubprocessError) as exc:
        print("C14 B sampling blocked:",exc,file=sys.stderr)
        sys.exit(2)
