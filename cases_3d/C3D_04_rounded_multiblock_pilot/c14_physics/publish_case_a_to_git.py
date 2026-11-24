#!/usr/bin/env python3
"""Publish the completed faithful A run under the same Git policy as C14 2D."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HOME=Path.home()/"OpenFOAM"
ROOT=Path(__file__).resolve().parents[3]
PARENT=Path("cases_3d/C3D_04_rounded_multiblock_pilot")
REL=PARENT/"C14_3D_A_faithful"
SOURCE=HOME/"C3D04_A_C14_FAITHFUL_RUNTIME_10S_01"
REPORT="C14_A_FAITHFUL_RUNTIME_REPORT.json"
MANIFEST="analysis_results/GIT_PUBLICATION_MANIFEST.json"
TIMES=[i/10 for i in range(101)]
PROBE_TIMES=[i/1000 for i in range(10001)]

def need(ok,msg):
    if not ok:raise ValueError(msg)
def git(root,*args):
    p=subprocess.run(["git","-C",str(root),*map(str,args)],capture_output=True,text=True,errors="replace")
    if p.returncode:raise RuntimeError("git "+" ".join(map(str,args))+"\n"+p.stdout+p.stderr)
    return p.stdout.strip()
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def save(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def series(p,expected):
    ts=[float(l.split()[0]) for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.lstrip().startswith("#")]
    need(len(ts)==len(expected) and all(abs(a-b)<1e-8 for a,b in zip(ts,expected)),"cadence differs "+str(p))
def verify(source):
    r=load(source/REPORT)
    need(r["status"]=="FAITHFUL_C14_RUNTIME_READY" and r["solver_completed"] and r["native_diagnostic_parity"]
         and r["input_hashes_unchanged"] and r["base_evidence_unchanged"],"accepted faithful runtime required")
    need(Path(r["case"]).resolve()==source and r["solver"]["native_solver_steps"]==10000,"wrong run")
    need(sha(source/"log.foamMultiRun")==r["solver"]["log_sha256"],"solver log changed")
    need(r["solver"]["last_time_s"]==10 and r["foamLog"]["returncode"]==0,"incomplete native run")
    for rel,digest in r["input_sha256"].items():
        p=source/rel
        need(p.is_file() and not p.is_symlink() and sha(p)==digest,"input drift: "+rel)
    pp=source/"postProcessing/metal"
    for name in ("T","U","p_rgh","rho","phaseChangeSource:alpha1"):
        series(pp/"temperatureProbe/0"/name,PROBE_TIMES)
    for name in r["coverage"]["reductions"]:
        tables=list((pp/name/"0").glob("*.dat"))
        need(len(tables)==1,"missing reduction "+name);series(tables[0],TIMES)
    for key in r["coverage"]["profiles"]:
        family,line=key.split("/")
        for t in TIMES:
            path=pp/family/format(t,"g")/(line+".xy")
            alias=pp/"C14CanonicalProfiles"/family/format(t,"g")/(line+".xy")
            need(path.is_file() and alias.is_file() and path.stat().st_size and alias.stat().st_size,"missing profile "+str(path))
    need(sum(1 for _ in (pp/"C14CanonicalProfiles").rglob("*.xy"))==1717,"wrong canonical profile count")
    need(any((source/"logs").iterdir()),"foamLog results empty")
    return r
def selected(source):
    for folder in ("0","constant","system","postProcessing","logs"):
        root=source/folder
        need(root.is_dir() and not root.is_symlink(),"missing folder "+str(root))
        for p in sorted(root.rglob("*")):
            rel=p.relative_to(source)
            if "polyMesh" in rel.parts or "dynamicCode" in rel.parts or p.name=="cellToRegion":continue
            need(not p.is_symlink(),"refusing symlink "+str(p))
            if p.is_file():yield p,rel
    for p in sorted(source.glob("log.*")):
        if p.is_file() and not p.is_symlink():yield p,p.relative_to(source)
    for name in (REPORT,"C14_3D_A_NATIVE_STAGE_REPORT.json"):
        p=source/name;need(p.is_file(),"missing evidence "+name);yield p,Path(name)
def copy_one(p,dst):
    need(p.stat().st_size<95*1024**2,"file above safe Git limit; not silently omitted: "+str(p))
    dst.parent.mkdir(parents=True,exist_ok=True)
    need(not dst.exists(),"publication collision "+str(dst))
    shutil.copy2(p,dst)
    digest=sha(p);need(sha(dst)==digest,"copy changed "+str(p))
    return {"bytes":p.stat().st_size,"sha256":digest}

README="""# C14_3D_A_faithful — Caso A
Reference: C14_topFixedFlux_explicitRef (2D), transferred to accepted V4/T02
3D mesh, 8960 metal and 12352 mold cells. Native faithful run reached 10 s
(10000 steps, dt=.001, 101 saved states) with original controlDict and
researchDiagnostics, adapted sampling coordinates, 17 lines and 10001
samples per native probe variable. Preferred A scientific reference.

## Versioning
Same policy as the 2D cases: 0/, constant/, system/, postProcessing/, logs/,
raw solver logs and scientific evidence. Calculated volume directories
0.1..10, generated polyMesh, dynamicCode and ParaView marker stay in the
original WSL run unchanged. analysis_results/GIT_PUBLICATION_MANIFEST.json
records file hashes, mesh hashes and provenance. Import this folder in
FoamLens for spatial/temporal data; full 3D visualization needs local
native mesh and calculated fields. If available, the previous baseline
comparison with C14 2D is archived in analysis_results/previous_A_baseline_vs_C14_2D,
explicitly distinct from this new faithful run.

## Reproduction
Allrun uses the parent faithful runtime executor with accepted V4/T02 and
the validated local A baseline, creating a new out-of-tree run. The parent
geometry workflow (../README.md, ../AGENTS.md) documents the mesh provenance.
Allclean intentionally does not delete scientific evidence in this archive.

## Status
Native diagnostic parity confirmed in WSL. Discrete energy closure,
same-geometry mesh/time independence and QuickCup validation remain open.
"""
ALLRUN='''#!/usr/bin/env bash
set -eo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$#" -ne 1 ]]; then
  echo "Usage: bash Allrun /absolute/path/to/new/OpenFOAM_case" >&2; exit 2
fi
if [[ "${WM_PROJECT_VERSION:-}" != 14 ]]; then source /opt/openfoam14/etc/bashrc; fi
export HWLOC_COMPONENTS=-gl
python3 -B "$HERE/../c14_physics/run_c14_a_faithful_runtime.py" --out "$1"
'''
ALLCLEAN='''#!/usr/bin/env sh
echo "Immutable scientific archive: no tracked postProcessing, logs or inputs are deleted."
echo "Use a fresh out-of-tree directory for each new run."
'''
def add_notes(wt,m):
    path=wt/"docs/C3D04_CASE_A_STATUS.json"
    j=load(path)
    j["stage09_C14_full_runtime_parity"]["git_archive"]={
        "status":"SCIENTIFIC_ARCHIVE_INCLUDED_IN_PUBLICATION_COMMIT","path":str(REL),
        "manifest":str(REL/MANIFEST),"files":m["file_count"],"bytes":m["total_bytes"],
        "excluded_calculated_volume_times":True,"excluded_generated_mesh":True}
    save(path,j)
    p=wt/"docs/PROJECT_STAGE_STATUS.json";j=load(p)
    a=next(x for x in j["other_cases"] if x["case_id"]=="C3D-04 Caso A")
    a["git_archive"]=str(REL);save(p,j)
    notes={
        "PROJECT_AUDIT_LOG_ES.md":"> **Caso A publicación científica:** réplica fiel C14 3D incorporada con estándares 2D: entradas, postProcessing, logs y evidencia SHA; malla generada y campos calculados preservados localmente. No CFD. Etapa09/10, 8/10=80%.",
        "PROJECT_AUDIT_LOG_EN.md":"> **Case A scientific archive:** faithful C14 3D inputs, postProcessing, logs and SHA evidence under 2D Git policy. Generated mesh and calculated volume fields preserved locally. No CFD. Stage09/10, 8/10=80%.",
        str(PARENT/"README.md"):"> **Archivo científico C14 3D-A:** [C14_3D_A_faithful](C14_3D_A_faithful/README.md), entradas y resultados nativos según política 2D. Etapa09/10, 8/10=80%; validación pendiente."
    }
    for rel,prefix in notes.items():
        p=wt/rel;p.write_text(prefix+"\n\n"+p.read_text(encoding="utf-8"),encoding="utf-8")
    return [str(path.relative_to(wt)),"docs/PROJECT_STAGE_STATUS.json",*notes]
def execute(source):
    source=source.expanduser().resolve()
    repo=ROOT.resolve()
    need(repo.name=="C3D04_A_WORKTREE","use isolated A worktree")
    r=verify(source)
    print("Caso fiel verificado; preparando expediente Git sin modificar corridas.",flush=True)
    url=git(repo,"remote","get-url","origin")
    need(re.search(r"github\.com[:/]michels-lab/MasterProject(?:\.git)?/?$",url,re.I) is not None,"unexpected remote")
    git(repo,"fetch","origin","main")
    base=git(repo,"rev-parse","origin/main")
    staging=Path(tempfile.mkdtemp(prefix="C3D04_A_GIT_PUBLISH_",dir=HOME))
    wt=staging/"worktree"
    git(repo,"worktree","add","--detach",wt,base)
    print("Worktree de publicación: "+str(wt),flush=True)
    try:
        dest=wt/REL
        need(not dest.exists(),"archive already exists in origin/main; no overwrite")
        dest.mkdir(parents=True)
        inventory={}
        originals={}
        for p,rel in selected(source):
            inventory[str(rel)]=copy_one(p,dest/rel);originals[str(rel)]=p
        for filename,body in (("README.md",README),("CASE_VARIANT.md",README),("Allrun",ALLRUN),("Allclean",ALLCLEAN)):
            p=dest/filename;p.write_text(body,encoding="utf-8")
            if filename.startswith("All"):p.chmod(0o755)
            inventory[filename]={"bytes":p.stat().st_size,"sha256":sha(p)}
        # The already completed 2D-vs-A comparison concerns the previous
        # same-mesh baseline, not the new faithful runtime. Archive it as
        # distinct provenance, never as new-run native results.
        previous=HOME/"C3D04_A_C14_VISUALIZATION_01/analysis/C14_2D_3D_ARCHIVED_COMPARISON_01"
        prior_status="not_present_locally"
        if previous.is_dir():
            report=load(previous/"C14_ARCHIVED_COMPARISON_REPORT.json")
            need(report["status"]=="ARCHIVED_C14_2D_3D_COMPARISON_READY","prior comparison not accepted")
            for name in ("C14_ARCHIVED_COMPARISON_REPORT.json","cooling_curves_101.csv","global_thermal_101.csv","spatial_profiles_common_grid.csv","profile_metrics.csv"):
                p=previous/name
                rel="analysis_results/previous_A_baseline_vs_C14_2D/"+name
                inventory[rel]=copy_one(p,dest/rel);originals[rel]=p
            prior_status="included_separately_not_faithful_runtime"
        mesh={k:v for k,v in r["input_sha256"].items() if "/polyMesh/" in k}
        need(all(f"constant/{reg}/polyMesh/{name}" in mesh for reg in ("metal","mold")
                 for name in ("points","faces","owner","neighbour","boundary")),"missing mesh hashes")
        m={"schema":"C3D04_A_C14_GIT_ARCHIVE_V1","source_run":str(source),
           "source_report_sha256":sha(source/REPORT),"solver_log_sha256":r["solver"]["log_sha256"],
           "source_native_control_sha256":r["sampling"]["runtime_hashes"]["controlDict"],
           "mesh_sha256_not_versioned":mesh,"native_saved_times":101,"probe_samples_per_field":10001,
           "canonical_profiles":1717,"prior_baseline_comparison":prior_status,"file_count":len(inventory),"total_bytes":sum(v["bytes"] for v in inventory.values()),
           "files":inventory,"volume_states_stay_local":True,"generated_mesh_stays_local":True,
           "no_solver_rerun":True,"physical_validation":False}
        save(dest/MANIFEST,m)
        notes=add_notes(wt,m)
        git(wt,"add","--",REL,*notes)
        staged=set(git(wt,"diff","--cached","--name-only","--no-renames").splitlines())
        actual=set(git(wt,"ls-files","--",REL).splitlines())
        expected={str(REL/k) for k in inventory}|{str(REL/MANIFEST)}
        need(actual==expected,"Git policy mismatch: missing="+str(sorted(expected-actual)[:20])+" extra="+str(sorted(actual-expected)[:20]))
        need(staged<=expected|set(notes),"unrelated staged changes")
        # Verify staged blob identity too; detect line-ending or clean-filter changes.
        indexed={}
        for line in git(wt,"ls-files","--stage","--",REL).splitlines():
            meta,name=line.split("\t",1);indexed[name]=meta.split()[1]
        ordered=sorted(expected)
        hashed=subprocess.run(["git","hash-object","--no-filters","--stdin-paths"],cwd=wt,input="\n".join(ordered)+"\n",capture_output=True,text=True,check=True).stdout.splitlines()
        need(len(hashed)==len(ordered) and all(indexed[k]==h for k,h in zip(ordered,hashed)),"staged blob differs from exact archive bytes")
        need(all(sha(dest/k)==v["sha256"] for k,v in inventory.items()),"copied file changed")
        need(all(sha(p)==inventory[k]["sha256"] for k,p in originals.items()),"source changed during archive")
        print("Archivos: "+str(m["file_count"])+"; bytes: "+str(m["total_bytes"]),flush=True)
        git(wt,"commit","-m","data(C3D04-A): archive faithful C14 3D native results under 2D scientific Git policy")
        commit=git(wt,"rev-parse","HEAD")
        print("Commit local: "+commit,flush=True)
        try:
            git(wt,"push","origin","HEAD:refs/heads/main")
            git(wt,"fetch","origin","main")
            git(wt,"merge-base","--is-ancestor",commit,"origin/main")
            status="CASE_A_GIT_MAIN_PUBLISHED";branch="main"
        except RuntimeError as exc:
            branch="archive/c3d04-a-faithful-"+commit[:12]
            print("Main no confirmado: "+str(exc),flush=True)
            git(wt,"push","origin","HEAD:refs/heads/"+branch)
            remote=git(wt,"ls-remote","origin","refs/heads/"+branch).split()[0]
            need(remote==commit,"archive branch not verified")
            status="CASE_A_ARCHIVE_BRANCH_PUBLISHED_MAIN_PENDING"
        print(json.dumps({"status":status,"commit":commit,"branch":branch,"repository_path":str(REL),
                          "files":m["file_count"],"bytes":m["total_bytes"],"remote_verified":True,
                          "source_preserved":True,"worktree":str(wt)},indent=2),flush=True)
        return 0
    except BaseException:
        print("PUBLICATION_WORKTREE_PRESERVED: "+str(wt),file=sys.stderr);raise
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=SOURCE)
    a=p.parse_args()
    try:return execute(a.source)
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError) as e:
        print("CASE_A_GIT_PUBLICATION_BLOCKED:",e,file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
