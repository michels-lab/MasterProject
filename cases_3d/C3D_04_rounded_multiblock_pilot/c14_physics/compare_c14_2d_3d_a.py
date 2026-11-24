#!/usr/bin/env python3
"""Compare authentic C14 2D and 3D-A snapshots at mapped physical stations.
One functional delivery, no solver, no changes to existing cases.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys

import run_c14_stage07_grouped_native_recovery as native
import run_c14_stage07_solver_backed_recovery as recovery
import continue_c14_stage07_grouped_evidence as evidence
import c14_3d_postprocess_parity as volume

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
NAME="C14_topFixedFlux_explicitRef"
FIELDS={"temperature":("T",1),"velocity":("U",3),"liquid":("phaseChangeSource:alpha1",1),
        "pressure":("p_rgh",1),"gradient":("gradT",3)}
STATIONS=("horizontal10","horizontal20","horizontal30","vertical","probe10","probe20","probe30")
REPORT="C3D04_A_C14_2D_3D_COMPARISON.json"
NEEDED=("T","U","p_rgh","phaseChangeSource:alpha1")

def need(ok,msg):
    if not ok: raise ValueError(msg)

def numeric_times(case):
    result={}
    if not case.is_dir(): return result
    for p in case.iterdir():
        if not p.is_dir() or not re.fullmatch(r"\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",p.name): continue
        t=round(float(p.name),9)
        if 0<=t<=10 and all((p/"metal"/f).is_file() for f in NEEDED):
            need(t not in result,"duplicate native time labels in "+str(case))
            result[t]=p.name
    return result

def discover(home,explicit):
    if explicit:
        return explicit.expanduser().resolve()
    preferred=[home/"MasterProject/cases_controlled_buoyancy"/NAME,ROOT/"cases_controlled_buoyancy"/NAME,home/NAME]
    found=set()
    for p in preferred:
        if len(numeric_times(p))>=2 and (p/"constant/metal/polyMesh/points").is_file():found.add(p.resolve())
    if not found:
        for root,dirs,files in os.walk(home):
            p=Path(root)
            depth=len(p.relative_to(home).parts)
            dirs[:]=[d for d in dirs if not d.startswith(".") and not re.match(r"^\d",d)
                      and not d.startswith("C3D") and d not in ("postProcessing","processor0","constant","system","dynamicCode")
                      and depth<5]
            if p.name.startswith(NAME) and len(numeric_times(p))>=2 and (p/"constant/metal/polyMesh/points").is_file():
                found.add(p.resolve())
                dirs[:]=[]
    if not found:
        raise ValueError("No existing C14 2D snapshots found. Supply --case2d /absolute/path/to/solved/C14; no CFD was launched.")
    # Prefer most complete time support, never silently choose two different complete runs.
    scores={p:len(set(numeric_times(p))&{round(i/10,9) for i in range(101)}) for p in found}
    best=max(scores.values())
    winners=sorted(p for p,n in scores.items() if n==best)
    need(len(winners)==1,"Multiple equally complete C14 2D runs; specify --case2d: "+str(winners))
    return winners[0]

def mesh(case):
    p=case/"constant/metal/polyMesh"
    pts=volume.stage.gate.load_points(p/"points")
    owners=volume.label_values(p/"owner")
    neighbours=volume.label_values(p/"neighbour")
    n=max(owners+neighbours)+1
    lo=[min(v[i] for v in pts) for i in range(3)]
    hi=[max(v[i] for v in pts) for i in range(3)]
    need(abs((hi[1]-lo[1])-.04)<1e-5,"expected 40 mm metal height")
    return {"n":n,"lo":lo,"hi":hi,"cx":(lo[0]+hi[0])/2,"cz":(lo[2]+hi[2])/2}

def lines(g):
    # C14 coordinates: common x=0..40 mm relative to geometric centre,
    # y=0..40 mm relative to nominal bottom. A is the central transverse plane.
    cx,cz=g["cx"],g["cz"]
    y0=g["lo"][1]
    ans={}
    for h in (10,20,30):
        y=y0+h/1000
        ans["horizontal"+str(h)]=("x",(cx-.01975,y,cz),(cx+.01975,y,cz),80)
        ans["probe"+str(h)]=("x",(cx-.0001,y,cz),(cx+.0001,y,cz),3)
    ans["vertical"]=("y",(cx,y0+.00025,cz),(cx,y0+.03975,cz),80)
    return ans

def vector(v): return "("+" ".join(format(x,".12g") for x in v)+")"

def dictionary(path,g,field_names):
    blocks=[]
    for key,field in field_names.items():
        sets=[]
        for name,(axis,a,b,n) in lines(g).items():
            sets.append("    "+name+"\n    { type lineUniform; axis "+axis+"; start "+vector(a)+"; end "+vector(b)+"; nPoints "+str(n)+"; }")
        blocks.append("cmp_"+key+"\n{\n type sets;\n libs (\"libsampling.so\");\n region metal;\n writeControl timeStep;\n writeInterval 1;\n interpolationScheme cellPoint;\n setFormat raw;\n fields ("+field+");\n sets\n {\n"+"\n".join(sets)+"\n }\n}\n")
    evidence.write_dictionary(path,blocks)

def copy_case(src,dst,times):
    dst.mkdir()
    for name in ("constant","system"):
        shutil.copytree(src/name,dst/name)
    for name in times:
        # Real directories, copied native fields. No original time-directory links.
        shutil.copytree(src/name,dst/name)

def run_checked(case,label,dct,selector,fields):
    item=native.run(case,label,dct,selector,False,"("+" ".join(fields)+")")
    if not item["passed"]:
        log=case/item["log"]
        raise ValueError("Native sampling failed: "+str(log)+"\n"+"\n".join(log.read_text(errors="replace").splitlines()[-35:]))
    return item

def sample(case,g,times):
    selector=",".join(times)
    # A and 2D use identical native cellPoint interpolation. Generate gradT
    # only if missing from archived states; never reconstruct solver-dt ddt.
    if not all((case/t/"metal/gradT").is_file() for t in times):
        dct=case/"system/cmpGradient"
        evidence.write_dictionary(dct,["cmpGradT\n{\n type grad;\n libs (\"libfieldFunctionObjects.so\");\n region metal;\n field T;\n result gradT;\n executeControl timeStep;\n writeControl timeStep;\n}\n"])
        run_checked(case,"compareGradient",dct,selector,["T"])
    field_names={k:f for k,(f,n) in FIELDS.items() if all((case/t/"metal"/f).is_file() for t in times)}
    need(set(field_names)>={"temperature","velocity","liquid","pressure"},"missing required native field")
    dct=case/"system/cmpProfiles"
    dictionary(dct,g,field_names)
    run_checked(case,"compareProfiles",dct,selector,list(field_names.values()))
    return field_names

def read_profile(case,t,key,station,g):
    p=case/"postProcessing/metal"/("cmp_"+key)/t/(station+".xy")
    axis,a,b,n=lines(g)[station]
    k=0 if axis=="x" else 1
    step=(b[k]-a[k])/(n-1)
    rows={}
    if not p.is_file(): return rows
    width=FIELDS[key][1]
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):continue
        vals=[float(v) for v in line.split()]
        need(len(vals)==width+1 and all(math.isfinite(v) for v in vals),"unexpected raw profile: "+str(p))
        i=round((vals[0]-a[k])/step)
        need(0<=i<n and abs(vals[0]-(a[k]+step*i))<=max(step*.03,1e-9) and i not in rows,
             "profile is not on common coordinate grid: "+str(p))
        rows[i]=vals[1:]
    return rows

def csvwrite(path,rows):
    need(bool(rows),"empty output "+str(path))
    with path.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def components(key,v):
    if v is None:return {k:None for k in keys(key)}
    if len(v)==1:return {keys(key)[0]:v[0]}
    return dict(zip(keys(key),[*v,math.sqrt(sum(x*x for x in v))]))

def keys(k):
    return {"temperature":["T_K"],"liquid":["alphaL"],"pressure":["p_rgh_Pa"],
            "velocity":["Ux_m_s","Uy_m_s","Uz_m_s","U_mag_m_s"],
            "gradient":["gradTx_K_m","gradTy_K_m","gradTz_K_m","gradT_mag_K_m"]}[k]

def position(station,i):
    if station.startswith("probe"): return 20+(i-1)*.1
    return .25+39.5*i/79

def rms(a,b):
    return math.sqrt(math.fsum((x-y)**2 for x,y in zip(a,b))/len(a)) if a else None

def compare(cases,geometries,tmap,out):
    profiles=[]
    curves=[]
    coverage=[]
    times=sorted(tmap)
    for t in times:
        names=tmap[t]
        for station in STATIONS:
            n=3 if station.startswith("probe") else 80
            data={}
            for dim in ("2D","3D"):
                data[dim]={k:read_profile(cases[dim],names[dim],k,station,geometries[dim]) for k in FIELDS}
            for dim in ("2D","3D"):
                coverage.append({"time_s":t,"station":station,"case":dim,
                                 "T_points":len(data[dim]["temperature"]),"requested_points":n})
            for i in ([1] if station.startswith("probe") else range(n)):
                row={"time_s":t,"station":station,"position_mm":position(station,i)}
                for key in FIELDS:
                    a=components(key,data["2D"][key].get(i))
                    b=components(key,data["3D"][key].get(i))
                    for v in a:
                        row[v+"_2D"]=a[v];row[v+"_3D"]=b[v]
                        row[v+"_delta_3D_minus_2D"]=b[v]-a[v] if a[v] is not None and b[v] is not None else None
                (curves if station.startswith("probe") else profiles).append(row)
    for station in ("probe10","probe20","probe30"):
        previous=None
        for row in [r for r in curves if r["station"]==station]:
            for dim in ("2D","3D"):
                now=row["T_K_"+dim]
                old=previous["T_K_"+dim] if previous else None
                row["cooling_K_s_"+dim]=(old-now)/(row["time_s"]-previous["time_s"]) if now is not None and old is not None else None
            previous=row
    csvwrite(out/"profiles_2D_3D.csv",profiles)
    csvwrite(out/"cooling_curves_2D_3D.csv",curves)
    csvwrite(out/"sampling_coverage.csv",coverage)
    metrics=[]
    for t in times:
        for station in STATIONS[:4]:
            rs=[r for r in profiles if r["time_s"]==t and r["station"]==station]
            pairs=[(r["T_K_2D"],r["T_K_3D"]) for r in rs if r["T_K_2D"] is not None and r["T_K_3D"] is not None]
            metrics.append({"time_s":t,"station":station,"common_points":len(pairs),
                            "T_RMSE_K":rms([a for a,b in pairs],[b for a,b in pairs]),
                            "T_max_abs_difference_K":max((abs(a-b) for a,b in pairs),default=None)})
    csvwrite(out/"profile_metrics.csv",metrics)
    return profiles,curves,coverage,metrics

def means(src,g,times):
    vols=volume.cell_volumes(src,"metal",g["n"])
    rows=[]
    for t,name in sorted(times.items()):
        p=src/name/"metal"
        a=volume.native.scalar_field_values(p/"T",g["n"])
        b=volume.native.scalar_field_values(p/"phaseChangeSource:alpha1",g["n"])
        rows.append({"time_s":t,"T_volume_mean_K":volume.weighted(a,vols),"alphaL_volume_mean":volume.weighted(b,vols)})
    return rows

def save_native_probe(src,out):
    found=[]
    root=src/"postProcessing"
    if root.is_dir():
        for p in sorted(root.rglob("T")):
            if p.is_file() and "temperatureProbe" in p.parts:
                target=out/"native_2D_probe"/p.relative_to(root)
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(p,target)
                found.append(str(target.relative_to(out)))
    return found

def dashboard(out,profiles,curves,meanrows,times):
    # Completely offline HTML, no Python plotting library or network needed.
    data=json.dumps({"profiles":profiles,"curves":curves,"means":meanrows,"times":times},allow_nan=False,separators=(",",":"))
    html=r"""<!doctype html><html lang="es"><meta charset="utf-8"><title>C14 2D vs 3D-A</title>
<style>body{font:15px system-ui;margin:24px auto;max-width:1180px;padding:0 16px;color:#182332;background:#f6f8fa}h1{font-size:26px}section{background:white;border:1px solid #dce2e9;border-radius:10px;padding:18px;margin:14px 0}label{margin-right:16px}select{padding:7px}svg{width:100%;height:auto}.note{color:#526275;font-size:13px}.legend{display:flex;gap:20px}.a{color:#2563eb}.b{color:#d97706}a{color:#2563eb}</style>
<h1>C14 original 2D vs C3D04-A</h1><p>Coordenadas físicas homologadas por centro de sección y altura desde la base; no se extrapola fuera del metal. Diferencias de geometría y discretización no equivalen a validación de malla.</p>
<section><h2>Curvas temporales</h2><label>Ubicación <select id="station"><option value="probe20">20 mm (centro)</option><option value="probe10">10 mm</option><option value="probe30">30 mm</option><option value="mean">Media volumétrica</option></select></label><label>Variable <select id="cv"><option value="T_K">Temperatura [K]</option><option value="cooling_K_s">Enfriamiento [K/s]</option><option value="alphaL">Fracción líquida</option><option value="U_mag_m_s">Velocidad [m/s]</option></select></label><div id="curve"></div></section>
<section><h2>Perfiles espaciales</h2><label>Tiempo <select id="time"></select></label><label>Variable <select id="pv"></select></label><div id="profiles"></div></section>
<p><a href="cooling_curves_2D_3D.csv">Curvas CSV</a> · <a href="profiles_2D_3D.csv">Perfiles CSV</a> · <a href="profile_metrics.csv">RMSE CSV</a> · <a href="sampling_coverage.csv">Cobertura CSV</a> · <a href="volume_means.csv">Medias volumétricas CSV</a></p>
<script>const D=__DATA__; const $=s=>document.getElementById(s);
const labels={T_K:"Temperatura [K]",alphaL:"Fracción líquida",p_rgh_Pa:"p_rgh [Pa]",Ux_m_s:"Ux [m/s]",Uy_m_s:"Uy [m/s]",Uz_m_s:"Uz [m/s]",U_mag_m_s:"|U| [m/s]",gradTx_K_m:"gradTx [K/m]",gradTy_K_m:"gradTy [K/m]",gradTz_K_m:"gradTz [K/m]",gradT_mag_K_m:"|gradT| [K/m]",cooling_K_s:"Enfriamiento [K/s]"};
function plot(rows,x,k,title){let vals=rows.flatMap(r=>[r[k+"_2D"],r[k+"_3D"]]).filter(Number.isFinite);if(!vals.length)return "<h3>"+title+"</h3><p>Sin datos disponibles.</p>";let xs=rows.map(r=>r[x]),lo=Math.min(...vals),hi=Math.max(...vals),xl=Math.min(...xs),xh=Math.max(...xs);if(hi===lo){lo-=.5;hi+=.5}if(xh===xl)xh=xl+1;
let X=v=>65+((v-xl)/(xh-xl))*795,Y=v=>240-(v-lo)/(hi-lo)*195;let s='<h3>'+title+'</h3><div class="legend"><span class="a">━━ 2D</span><span class="b">━━ 3D-A</span></div><svg viewBox="0 0 900 290" role="img">';
for(let i=0;i<=5;i++){let v=lo+(hi-lo)*i/5,y=Y(v);s+='<line x1="65" x2="860" y1="'+y+'" y2="'+y+'" stroke="#e0e4e9"/><text x="58" y="'+(y+4)+'" text-anchor="end" font-size="11">'+v.toPrecision(4)+'</text>';let z=xl+(xh-xl)*i/5,xx=X(z);s+='<text x="'+xx+'" y="258" text-anchor="middle" font-size="11">'+z.toPrecision(3)+'</text>'}
for(let [dim,color] of [["2D","#2563eb"],["3D","#d97706"]]){let p="",active=false;for(let r of rows){let v=r[k+"_"+dim];if(!Number.isFinite(v)){active=false;continue}p+=(active?" L":" M")+X(r[x]).toFixed(2)+" "+Y(v).toFixed(2);active=true}s+='<path d="'+p+'" fill="none" stroke="'+color+'" stroke-width="2"/>'}
s+='<text x="460" y="280" text-anchor="middle" font-size="12">'+(x==="time_s"?"Tiempo [s]":"Posición homologada [mm]")+'</text></svg>';return s}
for(let t of D.times){let o=document.createElement("option");o.value=t;o.textContent=t+" s";$("time").append(o)}$("time").value=D.times.at(-1);
for(let [k,v] of Object.entries(labels)){if(k==="cooling_K_s")continue;let o=document.createElement("option");o.value=k;o.textContent=v;$("pv").append(o)}
function redraw(){let k=$("cv").value,st=$("station").value,rs=st==="mean"?D.means:D.curves.filter(r=>r.station===st);$("curve").innerHTML=plot(rs,"time_s",k,labels[k]);let t=Number($("time").value),p=$("pv").value;$("profiles").innerHTML=["horizontal10","horizontal20","horizontal30","vertical"].map(st=>plot(D.profiles.filter(r=>r.station===st&&r.time_s===t),"position_mm",p,st==="vertical"?"Vertical central":st.replace("horizontal","Horizontal ")+" mm")).join("")}
for(let id of ["station","cv","time","pv"])$(id).onchange=redraw;redraw();</script></html>"""
    (out/"Comparacion_C14_2D_3D.html").write_text(html.replace("__DATA__",data),encoding="utf-8")

def execute(case2d,case3d,out,make_html=True):
    case2d,case3d=case2d.resolve(),case3d.resolve()
    out=out.expanduser().absolute()
    need(not out.exists() and not out.is_symlink() and not out.is_relative_to(ROOT)
         and all(out!=p and p not in out.parents and out not in p.parents for p in (case2d,case3d)),
         "fresh independent output required")
    t2,t3=numeric_times(case2d),numeric_times(case3d)
    common=sorted(set(t2)&set(t3)&{round(i/10,9) for i in range(101)})
    need(len(common)>=2,"No overlapping saved 2D/3D times; existing CFD snapshots required")
    g2,g3=mesh(case2d),mesh(case3d)
    need(g3["n"]==8960,"not accepted A V4/T02 mesh")
    need(abs(g2["lo"][1])<1e-6 and abs(g2["cx"]-.02)<1e-6 and abs(g2["cz"]-.005)<1e-6,
         "2D geometry does not match original C14 coordinates")
    # Read provenance, not assume local reference has unchanged physical inputs.
    original=ROOT/"cases_controlled_buoyancy"/NAME
    provenance={}
    for rel in ("system/controlDict","constant/metal/fvModels","constant/metal/materials/castIron","constant/mold/materials/silica"):
        p=case2d/rel;q=original/rel
        provenance[rel]={"local_sha256":recovery.sha(p) if p.is_file() else None,
                         "matches_repository":p.is_file() and q.is_file() and recovery.sha(p)==recovery.sha(q)}
    need(all(provenance[k]["matches_repository"] for k in provenance if k!="system/controlDict"),
         "2D C14 physical inputs differ from repository; choose exact original solved case")
    out.mkdir()
    cases={"2D":out/"sample_2D","3D":out/"sample_3D"}
    gs={"2D":g2,"3D":g3}
    times={t:{"2D":t2[t],"3D":t3[t]} for t in common}
    for dim,source in (("2D",case2d),("3D",case3d)):
        names=[times[t][dim] for t in common]
        copy_case(source,cases[dim],names)
        sample(cases[dim],gs[dim],names)
    profiles,curves,coverage,metrics=compare(cases,gs,times,out)
    usable={station:sum(r["station"]==station and r["T_K_2D"] is not None and r["T_K_3D"] is not None for r in curves) for station in STATIONS[4:]}
    need(usable["probe20"]>=2,"central common temperature curve unavailable; inspect preserved native sampling")
    need(all(any(r["station"]==station and r["common_points"]>=2 for r in metrics) for station in STATIONS[:4]),"one or more common spatial profiles unavailable; inspect native coverage")
    complete_coverage=all(r["common_points"]==80 for r in metrics) and all(n==len(common) for n in usable.values())
    m2=means(case2d,g2,{t:t2[t] for t in common})
    m3=means(case3d,g3,{t:t3[t] for t in common})
    m=[]
    for a,b in zip(m2,m3):
        r={"time_s":a["time_s"],"T_K_2D":a["T_volume_mean_K"],"T_K_3D":b["T_volume_mean_K"],
           "alphaL_2D":a["alphaL_volume_mean"],"alphaL_3D":b["alphaL_volume_mean"],
           "cooling_K_s_2D":None,"cooling_K_s_3D":None}
        if m:
            for d in ("2D","3D"):
                r["cooling_K_s_"+d]=(m[-1]["T_K_"+d]-r["T_K_"+d])/(r["time_s"]-m[-1]["time_s"])
        m.append(r)
    csvwrite(out/"volume_means.csv",m)
    probes=save_native_probe(case2d,out)
    if make_html:
        dashboard(out,profiles,curves,m,common)
    result={"status":"COMPARISON_READY" if complete_coverage and len(common)==101 else "COMPARISON_READY_PARTIAL_COVERAGE","case_2D":str(case2d),"case_3D_A":str(case3d),
            "reference_provenance":provenance,"common_saved_times":common,
            "full_101_time_coverage":len(common)==101,"full_spatial_coverage":complete_coverage,
            "common_temperature_curve_points_by_station":usable,"geometries":gs,
            "native_sampling_coordinates":{d:lines(g) for d,g in gs.items()},
            "mapping":"x relative to cross-section centre; y relative to metal bottom; z central plane; no geometric equivalence claimed",
            "common_profile_T_points_final":{r["station"]:r["common_points"] for r in metrics if r["time_s"]==common[-1]},
            "final_profile_metrics":[r for r in metrics if r["time_s"]==common[-1]],
            "final_cooling_stations":[r for r in curves if r["time_s"]==common[-1]],
            "final_volume_means":m[-1],"preserved_native_2D_temperature_probe_files":probes,
            "solver_rerun":False,"original_cases_written":False,"grid_independence_verified":False,
            "experimental_validation":False,"dashboard":str(out/"Comparacion_C14_2D_3D.html") if make_html else None}
    (out/REPORT).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    h=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case2d",type=Path)
    p.add_argument("--case3d",type=Path,default=h/"C3D04_A_C14_VISUALIZATION_01")
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    try:
        src=discover(h,a.case2d)
        print("Reference 2D: "+str(src),flush=True)
        print(json.dumps(execute(src,a.case3d,a.out),indent=2))
        return 0
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print("C14_COMPARISON_BLOCKED:",exc,file=sys.stderr)
        return 2
if __name__=="__main__":raise SystemExit(main())
