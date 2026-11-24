#!/usr/bin/env python3
"""C14 3D-A multidirectional/radial/section analysis of saved states, no CFD."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import shutil
import sys

import compare_c14_2d_3d_a as cmp
import continue_c14_stage07_grouped_evidence as evidence
import run_c14_stage07_solver_backed_recovery as recovery

FIELDS={"T":("T",1),"U":("U",3),"alpha":("phaseChangeSource:alpha1",1),
        "gradT":("gradT",3),"p":("p_rgh",1)}
VARS=("T_K","alphaL","Ux_m_s","Uy_m_s","Uz_m_s","U_mag_m_s",
      "gradTx_K_m","gradTy_K_m","gradTz_K_m","gradT_mag_K_m","p_rgh_Pa")
HEIGHTS=(10,20,30)
ANGLES=(0,45,90,135)
REPORT="C3D04_A_MULTIDIRECTIONAL_REPORT.json"

def need(ok,msg):
    if not ok: raise ValueError(msg)

def geometry(g,grid):
    cx,cz=g["cx"],g["cz"]
    lo,hi=g["lo"],g["hi"]
    dx,dz=(hi[0]-lo[0])/grid,(hi[2]-lo[2])/grid
    sets={}
    for h in HEIGHTS:
        y=lo[1]+h/1000
        for a in ANGLES:
            rad=math.radians(a)
            ux,uz=math.cos(rad),math.sin(rad)
            # X axis for both diagonals, with 135 degrees reversed to keep
            # native sampling coordinate increasing; signed radius is saved.
            if a==135: ux,uz=-ux,-uz
            if abs(ux)<1e-10:ux=0
            if abs(uz)<1e-10:uz=0
            p=(cx-.020*ux,y,cz-.020*uz)
            q=(cx+.020*ux,y,cz+.020*uz)
            sets[f"h{h}_a{a}"]={"axis":"z" if a==90 else "x","start":p,"end":q,"n":81,
                                "kind":"diameter","height_mm":h,"angle_deg":a,"direction_xz":[ux,uz]}
        for j in range(grid):
            z=lo[2]+(j+.5)*dz
            sets[f"h{h}_grid{j:02d}"]={"axis":"x","start":(lo[0]+dx/2,y,z),
                "end":(hi[0]-dx/2,y,z),"n":grid,"kind":"section","height_mm":h,"grid_row":j}
    for name,x,z in (("v_center",cx,cz),("v_xplus10",cx+.01,cz),("v_xminus10",cx-.01,cz),
                     ("v_zplus10",cx,cz+.01),("v_zminus10",cx,cz-.01)):
        sets[name]={"axis":"y","start":(x,lo[1]+.00025,z),"end":(x,hi[1]-.00025,z),
                    "n":80,"kind":"vertical"}
    return sets,dx*dz

def make_dict(path,sets,fields):
    blocks=[]
    for key,(field,n) in fields.items():
        # Section quadrature uses T, U and alpha; gradient and pressure are
        # retained on all diameter and vertical profiles without extra grid IO.
        chosen={k:v for k,v in sets.items() if v["kind"]!="section" or key in ("T","U","alpha")}
        items=[]
        for name,s in chosen.items():
            items.append("    "+name+"\n    { type lineUniform; axis "+s["axis"]+
                         "; start "+cmp.vector(s["start"])+"; end "+cmp.vector(s["end"])+
                         "; nPoints "+str(s["n"])+"; }")
        blocks.append("sweep_"+key+"\n{\n type sets;\n libs (\"libsampling.so\");\n region metal;\n"
                      " writeControl timeStep;\n writeInterval 1;\n interpolationScheme cellPoint;\n"
                      " setFormat raw;\n fields ("+field+");\n sets\n {\n"+"\n".join(items)+"\n }\n}\n")
    evidence.write_dictionary(path,blocks)

def read(path,s,width):
    if not path.is_file():return {}
    k={"x":0,"y":1,"z":2}[s["axis"]]
    first=s["start"][k]
    step=(s["end"][k]-first)/(s["n"]-1)
    need(step>0,"nonincreasing sample axis")
    out={}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):continue
        v=[float(x) for x in line.split()]
        need(len(v)==width+1 and all(math.isfinite(x) for x in v),"invalid native line: "+str(path))
        i=round((v[0]-first)/step)
        need(0<=i<s["n"] and abs(v[0]-first-i*step)<=max(step*.03,1e-9) and i not in out,
             "native coordinate off grid: "+str(path))
        out[i]=v[1:]
    return out

def collect(case,t,name,s):
    dat={}
    for key,(field,width) in FIELDS.items():
        if s["kind"]=="section" and key not in ("T","U","alpha"):continue
        dat[key]=read(case/"postProcessing/metal"/("sweep_"+key)/t/(name+".xy"),s,width)
    rows={}
    for i in range(s["n"]):
        r=dict.fromkeys(VARS)
        for key,items in dat.items():
            v=items.get(i)
            if v is None:continue
            if key=="T":r["T_K"]=v[0]
            elif key=="alpha":r["alphaL"]=v[0]
            elif key=="p":r["p_rgh_Pa"]=v[0]
            elif key=="U":
                for j,a in enumerate("xyz"):r["U"+a+"_m_s"]=v[j]
                r["U_mag_m_s"]=math.sqrt(sum(x*x for x in v))
            elif key=="gradT":
                for j,a in enumerate("xyz"):r["gradT"+a+"_K_m"]=v[j]
                r["gradT_mag_K_m"]=math.sqrt(sum(x*x for x in v))
        rows[i]=r
    return rows

def stats(rows,keys=VARS):
    result={}
    for key in keys:
        vals=[r[key] for r in rows if r.get(key) is not None]
        m=math.fsum(vals)/len(vals) if vals else None
        result[key+"_n"]=len(vals)
        result[key+"_mean"]=m
        result[key+"_std"]=math.sqrt(math.fsum((v-m)**2 for v in vals)/len(vals)) if vals else None
        result[key+"_min"]=min(vals) if vals else None
        result[key+"_max"]=max(vals) if vals else None
    return result

def csv_open(path):
    return path.open("x",newline="",encoding="utf-8")

def append(writer,fp,rows):
    if not rows:return writer
    if writer is None:
        writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
        writer.writeheader()
    writer.writerows(rows)
    return writer

def analyze(case,sets,area,out,grid):
    diameter,radial,vertical,section=[],[],[],[]
    section_keys=("T_K","alphaL","Ux_m_s","Uy_m_s","Uz_m_s","U_mag_m_s")
    with csv_open(out/"section_quadrature_points.csv") as sf:
        sw=None
        for t in evidence.NAMES:
            time=float(t)
            current={}
            for name,s in sets.items():
                rows=collect(case,t,name,s)
                current[name]=rows
                if s["kind"]=="section":
                    points=[]
                    for i,r in rows.items():
                        if r["T_K"] is None:continue
                        x=s["start"][0]+(s["end"][0]-s["start"][0])*i/(s["n"]-1)
                        points.append({"time_s":time,"height_mm":s["height_mm"],"x_m":x,
                                       "z_m":s["start"][2],"area_weight_m2":area,
                                       **{k:r[k] for k in section_keys}})
                    sw=append(sw,sf,points)
                    continue
                for i,r in rows.items():
                    xyz=[a+(b-a)*i/(s["n"]-1) for a,b in zip(s["start"],s["end"])]
                    item={"time_s":time,"line":name,"position_mm":(i-40)*.5 if s["kind"]=="diameter" else .25+39.5*i/79,
                          "x_m":xyz[0],"y_m":xyz[1],"z_m":xyz[2],**r}
                    if s["kind"]=="diameter":
                        diameter.append({"height_mm":s["height_mm"],"angle_deg":s["angle_deg"],**item})
                    else:vertical.append(item)
            for h in HEIGHTS:
                for i in range(41):
                    rr=[]
                    for a in ANGLES:
                        r=current[f"h{h}_a{a}"]
                        # Center is one physical point; do not count it 8 times.
                        if i==0:
                            if a==0:rr.append(r[40])
                        else:rr.extend([r[40-i],r[40+i]])
                    radial.append({"time_s":time,"height_mm":h,"radius_mm":i*.5,
                                   "requested_angular_samples":1 if i==0 else 8,**stats(rr)})
                rr=[r for name,s in sets.items() if s["kind"]=="section" and s["height_mm"]==h
                    for r in current[name].values() if r["T_K"] is not None]
                need(len(rr)>0,"no valid section samples at "+t+" height "+str(h))
                need(all(r[k] is not None for r in rr for k in section_keys),"incomplete collocated section fields")
                section.append({"time_s":time,"height_mm":h,"grid_n":grid,"valid_points":len(rr),
                                "grid_points":grid*grid,"estimated_section_area_mm2":len(rr)*area*1e6,
                                **stats(rr,section_keys)})
    for name,rows in (("diameters_101.csv",diameter),("vertical_lines_101.csv",vertical),
                      ("radial_statistics_101.csv",radial),("section_statistics_101.csv",section)):
        cmp.csvwrite(out/name,rows)
    # Do not certify fully sampled lines at their requested outer endpoints;
    # those may lie outside the curved metal, and nulls are intentional.
    counts_by_line_time={}
    for row in diameter+vertical:
        if row["T_K"] is not None:
            k=(row["line"],row["time_s"])
            counts_by_line_time[k]=counts_by_line_time.get(k,0)+1
    coverage={}
    for name,s in sets.items():
        if s["kind"]=="section":continue
        counts=[counts_by_line_time.get((name,float(t)),0) for t in evidence.NAMES]
        coverage[name]={"min_valid_T_points":min(counts),"max_valid_T_points":max(counts),"requested":s["n"]}
        need(min(counts)>=2,"line has no usable support: "+name)
    return diameter,radial,vertical,section,coverage

def dashboard(out,d,r,v,s):
    # Keep compact chart data, with blank values for points outside the metal.
    def small(rows,meta,values):
        return [{k:x[k] for k in (*meta,*values) if k in x} for x in rows]
    variables=("T_K","alphaL","U_mag_m_s","Ux_m_s","Uy_m_s","Uz_m_s","gradT_mag_K_m","p_rgh_Pa")
    data={"d":small(d,("time_s","height_mm","angle_deg","position_mm"),variables),
          "r":small(r,("time_s","height_mm","radius_mm"),tuple(k+suffix for k in variables for suffix in ("_mean","_std","_min","_max","_n"))),
          "v":small(v,("time_s","line","position_mm"),variables),
          "s":small(s,("time_s","height_mm","estimated_section_area_mm2"),tuple(k+"_mean" for k in variables)),
          "times":[float(t) for t in evidence.NAMES]}
    html=r"""<!doctype html><html lang="es"><meta charset="utf-8"><title>C14 3D-A · barridos</title>
<style>body{font:15px system-ui;background:#f4f6f9;color:#182332;max-width:1200px;margin:24px auto;padding:0 16px}section{background:white;border:1px solid #dce2e9;border-radius:10px;padding:15px;margin:15px 0}select{padding:7px;margin:0 15px 0 5px}svg{width:100%;height:auto}h2{font-size:19px}.note{font-size:13px;color:#526275}.legend span{margin-right:16px}</style>
<h1>C14 3D-A | Barridos multidireccionales</h1><p>Datos nativos de los 101 estados. Alturas desde la base; no se extrapolan puntos fuera del metal. Promedios radiales: hasta ocho muestras angulares; secciones: cuadratura de puntos medios, no área exacta.</p>
<section><label>Tiempo<select id="time"></select></label><label>Altura<select id="height"><option>10</option><option selected>20</option><option>30</option></select> mm</label><label>Variable<select id="var"></select></label></section>
<section><h2>Diámetros XZ</h2><div id="diam"></div></section>
<section><h2>Promedio radial y rango angular</h2><div id="rad"></div></section>
<section><h2>Perfiles verticales</h2><div id="vert"></div></section>
<section><h2>Curvas temporales de sección transversal</h2><div id="sec"></div><p class="note">Promedio de magnitudes y componentes por separado. Solo T, alpha y U se muestrean en la cuadratura de área.</p></section>
<p><a href="diameters_101.csv">Diámetros</a> · <a href="radial_statistics_101.csv">Estadística radial</a> · <a href="vertical_lines_101.csv">Verticales</a> · <a href="section_statistics_101.csv">Secciones</a> · <a href="section_quadrature_points.csv">Puntos de cuadratura</a></p>
<script>const D=__DATA__,$=s=>document.getElementById(s);
const labels={T_K:"T [K]",alphaL:"Fracción líquida",U_mag_m_s:"|U| [m/s]",Ux_m_s:"Ux [m/s]",Uy_m_s:"Uy [m/s]",Uz_m_s:"Uz [m/s]",gradT_mag_K_m:"|gradT| [K/m]",p_rgh_Pa:"p_rgh [Pa]"};
const colors=["#2563eb","#d97706","#059669","#9333ea","#dc2626"];
function draw(id,series,xlabel,ylabel){let all=series.flatMap(s=>s.points),xs=all.map(p=>p[0]),ys=all.map(p=>p[1]).filter(Number.isFinite);if(!ys.length){$(id).innerHTML="<p>Sin datos para esta variable.</p>";return}
let xl=Math.min(...xs),xh=Math.max(...xs),lo=Math.min(...ys),hi=Math.max(...ys);if(lo===hi){let a=Math.max(Math.abs(lo)*.01,1e-9);lo-=a;hi+=a}if(xl===xh)xh=xl+1;
let X=x=>90+(x-xl)/(xh-xl)*780,Y=y=>230-(y-lo)/(hi-lo)*190;
let s='<div class="legend">'+series.map((a,i)=>'<span style="color:'+colors[i%5]+'">━━ '+a.name+'</span>').join("")+'</div><svg viewBox="0 0 900 282">';
for(let i=0;i<=5;i++){let y=lo+(hi-lo)*i/5,xx=xl+(xh-xl)*i/5;s+='<line x1="90" x2="870" y1="'+Y(y)+'" y2="'+Y(y)+'" stroke="#e1e6ed"/><text x="82" y="'+(Y(y)+4)+'" font-size="11" text-anchor="end">'+y.toPrecision(5)+'</text><text x="'+X(xx)+'" y="248" font-size="11" text-anchor="middle">'+xx.toPrecision(3)+'</text>'}
for(let [i,a] of series.entries()){let p="",active=false;for(let [x,y] of a.points){if(!Number.isFinite(y)){active=false;continue}p+=(active?" L":" M")+X(x).toFixed(2)+" "+Y(y).toFixed(2);active=true}s+='<path d="'+p+'" fill="none" stroke="'+colors[i%5]+'" stroke-width="2" '+(a.dash?'stroke-dasharray="5 4"':'')+'/>'}
s+='<text x="480" y="270" text-anchor="middle" font-size="12">'+xlabel+'</text><text x="15" y="25" font-size="12">'+ylabel+'</text></svg>';$(id).innerHTML=s}
for(let t of D.times){let o=document.createElement("option");o.value=t;o.textContent=t+" s";$("time").append(o)}$("time").value=10;
for(let [k,l] of Object.entries(labels)){let o=document.createElement("option");o.value=k;o.textContent=l;$("var").append(o)}
function redraw(){let t=Number($("time").value),h=Number($("height").value),k=$("var").value,l=labels[k];let ds=D.d.filter(r=>r.time_s===t&&r.height_mm===h),rs=D.r.filter(r=>r.time_s===t&&r.height_mm===h),vs=D.v.filter(r=>r.time_s===t);
draw("diam",[0,45,90,135].map(a=>({name:a+"°",points:ds.filter(r=>r.angle_deg===a).map(r=>[r.position_mm,r[k]])})),"Distancia firmada al centro [mm]",l);
draw("rad",[{name:"Media",points:rs.map(r=>[r.radius_mm,r[k+"_mean"]])},{name:"Mín.",dash:true,points:rs.map(r=>[r.radius_mm,r[k+"_min"]])},{name:"Máx.",dash:true,points:rs.map(r=>[r.radius_mm,r[k+"_max"]])}],"Radio [mm]",l);
draw("vert",["v_center","v_xplus10","v_xminus10","v_zplus10","v_zminus10"].map((n,i)=>({name:["Centro","X +10","X −10","Z +10","Z −10"][i],points:vs.filter(r=>r.line===n).map(r=>[r.position_mm,r[k]])})),"Altura desde base [mm]",l);
draw("sec",[10,20,30].map(h=>({name:h+" mm",points:D.s.filter(r=>r.height_mm===h).map(r=>[r.time_s,r[k+"_mean"]])})),"Tiempo [s]",l)}
for(let id of ["time","height","var"])$(id).onchange=redraw;redraw();</script></html>"""
    (out/"Barridos_C14_3D_A.html").write_text(html.replace("__DATA__",json.dumps(data,allow_nan=False,separators=(",",":"))),encoding="utf-8")

def execute(src,out,grid):
    src=src.expanduser().resolve()
    out=out.expanduser().absolute()
    need(out.parent.resolve()==src.parent and not out.exists() and not out.is_symlink(),"fresh sibling destination required")
    need(11<=grid<=81 and grid%2==1,"grid must be odd between 11 and 81")
    vis=recovery.read_json(src/"C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json")
    need(vis["status"]=="VISUALIZATION_AND_SOLIDIFICATION_READY" and vis["original_source_hashes_unchanged"],"accepted A visualization required")
    g=cmp.mesh(src)
    need(g["n"]==8960,"not accepted A mesh")
    sets,area=geometry(g,grid)
    before=recovery.sha(src/"C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json")
    tracked=[src/t/region/f for t in evidence.NAMES for region,fs in (("metal",tuple(v[0] for v in FIELDS.values())),("mold",("T",))) for f in fs]
    tracked.extend(p for folder in ("constant","system") for p in (src/folder).rglob("*") if p.is_file())
    source_hashes={str(p):recovery.sha(p) for p in tracked}
    out.mkdir()
    work=out/"sampling_case"
    report={"status":"INCOMPLETE_PRESERVED","source":str(src),"solver_rerun":False,
            "stage":"09/10","milestones_done":"8/10","grid_independence_verified":False,
            "section_quadrature":"uniform midpoint grid, approximate area and averages, no exact plane integral",
            "radial_method":"4 diameters, 8 angular samples per nonzero radius, population std; no assumption of axial symmetry",
            "angle_135_signed_axis":"negative 135-degree direction so x is increasing; unsigned radial statistics unchanged",
            "geometry":g,"native_sampling_lines":sets,"section_grid_n":grid,"section_point_weight_m2":area}
    try:
        work.mkdir()
        for name in ("constant","system"):
            shutil.copytree(src/name,work/name)
        for t in evidence.NAMES:
            for region,fields in (("metal",tuple(v[0] for v in FIELDS.values())),("mold",("T",))):
                dst=work/t/region
                dst.mkdir(parents=True)
                for field in fields:
                    p=src/t/region/field
                    need(p.is_file() and not p.is_symlink(),"missing archived field "+str(p))
                    shutil.copy2(p,dst/field)
        # Only fresh isolated sample case receives these dictionaries/results.
        dct=work/"system/c14Multidirectional"
        make_dict(dct,sets,FIELDS)
        cmp.run_checked(work,"multidirectional",dct,"0:10",[v[0] for v in FIELDS.values()])
        d,r,v,s,coverage=analyze(work,sets,area,out,grid)
        dashboard(out,d,r,v,s)
        report.update(status="MULTIDIRECTIONAL_3D_READY",saved_times=101,
                      diametral_lines=12,vertical_lines=5,section_heights_mm=list(HEIGHTS),
                      coverage=coverage,final_section_statistics=[x for x in s if x["time_s"]==10],
                      dashboard=str(out/"Barridos_C14_3D_A.html"))
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        report["error"]=str(exc)
    report["source_report_sha_unchanged"]=recovery.sha(src/"C3D04_A_VISUALIZATION_AND_SOLIDIFICATION_REPORT.json")==before
    report["source_sampled_fields_and_dictionaries_sha_unchanged"]=all(recovery.sha(Path(p))==h for p,h in source_hashes.items())
    (out/REPORT).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    h=Path.home()/"OpenFOAM"
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case",type=Path,default=h/"C3D04_A_C14_VISUALIZATION_01")
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--grid",type=int,default=41)
    a=p.parse_args()
    try:
        r=execute(a.case,a.out,a.grid)
        print(json.dumps({k:v for k,v in r.items() if k!="native_sampling_lines"},indent=2))
        return 0 if r["status"]=="MULTIDIRECTIONAL_3D_READY" and r["source_report_sha_unchanged"] and r["source_sampled_fields_and_dictionaries_sha_unchanged"] else 3
    except (OSError,ValueError,RuntimeError,KeyError,TypeError) as exc:
        print("C14_MULTIDIRECTIONAL_BLOCKED:",exc,file=sys.stderr)
        return 2
if __name__=="__main__":raise SystemExit(main())
