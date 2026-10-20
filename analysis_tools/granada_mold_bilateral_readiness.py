#!/usr/bin/env python3
"""Read-only QuickCup coupled-interface preflight and optional mold-side comparison.

Does NOT run OpenFOAM, mutate a case, infer Sf normals, or validate thermodynamics.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

CASES = (
    "B14_topFixedFlux_explicitRef", "C14_topFixedFlux_explicitRef",
    "B15_adaptiveDt_fromB14", "C15_adaptiveDt_fromC14",
    "B16_phaseRelax025_fromB14", "C16_phaseRelax025_fromC14",
)
METAL_DAT = Path("postProcessing/metal/metalMoldEnergyPower/0/surfaceFieldValue.dat")


def stripped(text):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)


def block(text, name, opening="{", closing="}"):
    pat = re.search(r"\b" + re.escape(name) + r"\s*\" + opening, text)
    if pat is None:
        raise ValueError(f"missing block {name}")
    depth = 1
    for i in range(pat.end(), len(text)):
        if text[i] == opening:
            depth += 1
        elif text[i] == closing:
            depth -= 1
            if depth == 0:
                return text[pat.end():i]
    raise ValueError(f"unclosed block {name}")


def scalar(text, key):
    values = re.findall(r"\b" + re.escape(key) + r"\s+([^\s;]+)\s*;", text)
    if len(values) != 1:
        raise ValueError(f"missing/ambiguous {key}")
    value = float(values[0])
    if not math.isfinite(value):
        raise ValueError(f"nonfinite {key}")
    return value


def source(path, case, manifest):
    if not path.is_file():
        raise ValueError(f"missing original source: {path}")
    manifest.append({"relative_path": path.relative_to(case).as_posix(),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return path.read_text(encoding="utf8", errors="replace")


def coupling(case, manifest):
    metal = stripped(source(case/"0/metal/T", case, manifest))
    mold = stripped(source(case/"0/mold/T", case, manifest))
    mb = block(metal, "metal_to_mold")
    cb = block(mold, "mold_to_metal")
    if not re.search(r"\btype\s+coupledTemperature\s*;", mb):
        raise ValueError("metal_to_mold is not coupledTemperature")
    if not re.search(r"\btype\s+coupledTemperature\s*;", cb):
        raise ValueError("mold_to_metal is not coupledTemperature")
    h = block(mb, "h")
    if not re.search(r"\btype\s+wallLayersHeatTransferCoefficient\s*;", h):
        raise ValueError("unknown metal-side contact model; do not assume wall-layer resistance")
    layers = []
    for key in ("thicknessLayers", "kappaLayers"):
        m = re.search(r"\b"+key+r"\s*\(([^()]*)\)\s*;", h)
        if m is None:
            raise ValueError("missing "+key)
        vals = [float(v) for v in m.group(1).split()]
        if not vals or any(not math.isfinite(v) or v <= 0 for v in vals):
            raise ValueError("invalid positive layer data "+key)
        layers.append(vals)
    if len(layers[0]) != len(layers[1]):
        raise ValueError("contact layer lengths differ")
    r_nominal = math.fsum(t/k for t,k in zip(*layers))
    return {"metal_patch":"metal_to_mold","mold_patch":"mold_to_metal",
            "coupling":"coupledTemperature",
            "layer_count":len(layers[0]),
            "nominal_layer_R_m2K_W":r_nominal,
            "nominal_layer_h_W_m2K":1/r_nominal}


def geometry(case, manifest):
    data = stripped(source(case/"system/blockMeshDict",case,manifest))
    factor = scalar(data, "convertToMeters")
    if factor <= 0:
        raise ValueError("invalid geometric scale")
    verts = block(data, "vertices", "(", ")")
    v = [tuple(float(x)*factor for x in m.split())
         for m in re.findall(r"\(([-+0-9.eE\s]+)\)", verts)]
    if not v or any(len(p)!=3 or not all(math.isfinite(x) for x in p) for p in v):
        raise ValueError("invalid vertex list")
    metals = re.findall(r"\bhex\s*\(([\d\s]+)\)\s+metal\s*\(([\d\s]+)\)", data)
    if len(metals)!=1:
        raise ValueError("expected exactly one rectangular metal block")
    ids = [int(x) for x in metals[0][0].split()]
    cellnums = [int(x) for x in metals[0][1].split()]
    if len(ids)!=8 or len(set(ids))!=8 or len(cellnums)!=3 or min(cellnums)<1:
        raise ValueError("invalid metal hex/cell counts")
    if max(ids)>=len(v):
        raise ValueError("metal hex references invalid vertex")
    span = [max(v[j][k] for j in ids)-min(v[j][k] for j in ids) for k in range(3)]
    if min(span)<=0:
        raise ValueError("invalid metal dimensions")
    # This rectangular 2D slice has metalTop exposed on +Y; the other
    # three XY perimeter sides touch mold. NOMINAL geometry, not true Sf.
    nominal_area=(span[0]+2*span[1])*span[2]
    nominal_faces=(cellnums[0]+2*cellnums[1])*cellnums[2]
    return {"metal_extent_m":span, "slice_cells":cellnums,
            "nominal_three_contact_sides_area_m2":nominal_area,
            "nominal_contact_face_count":nominal_faces,
            "status":"RECTANGULAR_BLOCKMESHDICT_NOMINAL_NOT_CHECKMESH"}


def metal_flux(case, manifest):
    data=source(case/METAL_DAT,case,manifest).splitlines()
    metadata={}
    rows=[]
    for n,line in enumerate(data,1):
        x=line.strip()
        if not x:
            continue
        if x.startswith("#"):
            for key in ("Selection","Area","Faces"):
                m=re.match(r"#\s*"+key+r"\s*:\s*(.*)",x)
                if m: metadata[key]=m.group(1).strip()
            if x.startswith("# Time"):
                if tuple(x[1:].split()) != ("Time","sum(energyAdvectiveFlux)","sum(heatFlux)","sum(energyFlux)"):
                    raise ValueError("unrecognized original metal energy field identities")
            continue
        try:
            r=tuple(float(v) for v in x.split())
        except ValueError as ex:
            raise ValueError(f"nonnumeric metal-side energy at line {n}") from ex
        if len(r)!=4 or not all(math.isfinite(v) for v in r):
            raise ValueError(f"invalid metal-side energy row {n}")
        if r[0]<0 or (rows and r[0]<=rows[-1][0]):
            raise ValueError(f"duplicate/out of order physical time {n}")
        if abs(r[1]+r[2]-r[3])>1e-3+1e-5*max(abs(r[1]),abs(r[2]),abs(r[3])):
            raise ValueError(f"metal-side energyFlux decomposition mismatch at line {n}")
        rows.append(r)
    if len(rows)<2 or metadata.get("Selection")!="patch(metal_to_mold)":
        raise ValueError("insufficient source or wrong metal interface patch")
    if "Area" not in metadata or "Faces" not in metadata:
        raise ValueError("missing source Area/Faces metadata")
    area=float(metadata["Area"]); faces=int(metadata["Faces"])
    if not math.isfinite(area) or area<=0 or faces<1:
        raise ValueError("invalid source area/faces")
    return {"area_m2":area,"face_count":faces,"rows":rows,
            "last_time_s":rows[-1][0],"write_count":len(rows),
            "power_final_W":rows[-1][3]}


def read_optional_mold(evidence_root, name, metal_rows, metal_area, manifest):
    if evidence_root is None:
        return {"status":"NOT_OBSERVED_NO_MOLD_OUTPUT"}
    base=evidence_root/name
    report=base/"provenance.json"
    if not report.exists():
        if (base/"mold_interface_W.csv").exists():
            raise ValueError("mold measurement exists without provenance.json")
        return {"status":"NOT_OBSERVED_NO_MOLD_OUTPUT"}
    spec=json.loads(report.read_text(encoding="utf8"))
    required = {"case":name, "patch":"mold_to_metal", "units":"W",
                "orientation":"outward_from_mold", "quantity":"integrated_interface_power"}
    for key,val in required.items():
        if spec.get(key)!=val:
            raise ValueError(f"missing/mismatched provenance {key}")
    if spec.get("source_method") not in ("OpenFOAM_Foundation14",):
        raise ValueError("no specified supported original measurement method")
    raw=base/"mold_interface_W.csv"
    if not raw.is_file() or raw.is_symlink() or report.is_symlink():
        raise ValueError("source measurement missing or unsafe link")
    digest=hashlib.sha256(raw.read_bytes()).hexdigest()
    if spec.get("source_sha256")!=digest:
        raise ValueError("mold-side data checksum mismatch")
    with raw.open(newline="",encoding="utf8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=["time_s","outward_power_W"]:
            raise ValueError("unexpected mold CSV column contract")
        rows=[]
        for record in reader:
            try:
                t=float(record["time_s"]); p=float(record["outward_power_W"])
            except (ValueError,TypeError) as e:
                raise ValueError("invalid numeric mold power") from e
            if not math.isfinite(t) or not math.isfinite(p) or t<0 or (rows and t<=rows[-1][0]):
                raise ValueError("invalid, repeated or unordered mold time/power")
            rows.append((t,p))
    if len(rows)<2:
        raise ValueError("insufficient mold-side real measurements")
    area=spec.get("measured_area_m2")
    if not isinstance(area,(int,float)) or not math.isfinite(area) or area<=0:
        raise ValueError("missing measured mold-side mesh interface area")
    metal={round(r[0],8):r[3] for r in metal_rows}
    mold={round(t,8):p for t,p in rows}
    if len(metal)!=len(metal_rows) or len(mold)!=len(rows):
        raise ValueError("time precision aliasing; cannot pair safely")
    common=sorted(set(metal)&set(mold))
    if len(common)<2 or len(common)!=len(metal) or len(common)!=len(mold):
        raise ValueError("time grids do not agree; no extrapolation or partial acceptance")
    residual=[metal[t]+mold[t] for t in common]
    # Physical sign/topology and mesh normal validation are still independent.
    metrics={"compared_time_count":len(common),
             "max_abs_power_imbalance_W":max(map(abs,residual)),
             "rmse_power_imbalance_W":math.sqrt(math.fsum(r*r for r in residual)/len(residual)),
             "relative_area_difference":abs(area-metal_area)/metal_area,
             "first_time_s":common[0],"last_time_s":common[-1]}
    manifest.append({"relative_path":f"supplied-mold-evidence/{name}/mold_interface_W.csv",
                     "sha256":digest})
    return {"status":"PROVISIONAL_SOURCE_PAIR_NEEDS_MESH_NORMAL_VALIDATION",
            "numerical_metrics":metrics,
            "limitations":"metadata/sha confirm byte identity, not truthful physics, normals, mesh face mapping or power construction"}


def audit(root, evidence_root=None):
    result=[]
    for name in CASES:
        case=root/"cases_controlled_buoyancy"/name
        sources=[]
        alerts=[]
        outputs={}
        for key,fun in (("coupling",coupling),("nominal_geometry",geometry),
                        ("metal_side_power",metal_flux)):
            try:
                outputs[key]=fun(case,sources)
            except (ValueError,OSError,OverflowError) as e:
                alerts.append(f"{key}: {e}");outputs[key]=None
        if outputs["nominal_geometry"] and outputs["metal_side_power"]:
            geom=outputs["nominal_geometry"];power=outputs["metal_side_power"]
            if not math.isclose(geom["nominal_three_contact_sides_area_m2"],power["area_m2"],rel_tol=.01):
                alerts.append("nominal block area differs from source metal patch metadata")
            if geom["nominal_contact_face_count"]!=power["face_count"]:
                alerts.append("nominal interface face count differs from reported patch count")
        mold={"status":"NOT_OBSERVED_NO_MOLD_OUTPUT"}
        if outputs["metal_side_power"]:
            try:
                mold=read_optional_mold(evidence_root,name,outputs["metal_side_power"]["rows"],
                                        outputs["metal_side_power"]["area_m2"],sources)
                if mold.get("numerical_metrics",{}).get("relative_area_difference",0)>.01:
                    alerts.append("measured metal/mold interface areas differ by >1%")
            except (ValueError,OSError,json.JSONDecodeError) as e:
                alerts.append(f"mold_side: {e}");mold={"status":"INVALID_MOLD_EVIDENCE"}
        outputs["mold_side"]=mold
        if outputs["metal_side_power"]:
            outputs["metal_side_power"].pop("rows")
        result.append({"case":name,"source_manifest":sorted(sources,key=lambda x:x["relative_path"]),
                       "sections":outputs,"alerts":alerts,
                       "status":"SOURCE_REVIEW" if alerts else "METAL_SIDE_READINESS_PASSED_MOLD_UNVERIFIED"})
    return {"schema":"quickcup-bilateral-mold-readiness-v1",
            "scope":"source-level metal/mold boundary & nominal geometry, optional measured mold input",
            "global_physics_verdict":"NOT_VALIDATED",
            "no_CFD_executed":True,"no_mold_measurement_fabricated":True,
            "cases":result}


CANDIDATE = """// CANDIDATE ONLY: OpenFOAM FOUNDATION 14, DO NOT ENABLE WITHOUT LOCAL TESTING.
// Add to a *new copied test case* functions dictionary, not an original case.
// wallHeatFlux outputs a wall flux FIELD; it does not by itself provide
// integrated outward interface power in W. Validate Sf, orientation, units,
// physical time and patch presence before normalizing any bilateral CSV.
moldInterfaceWallHeatFlux
{
    type wallHeatFlux;
    libs ("libfieldFunctionObjects.so");
    region mold;
    patches (mold_to_metal);
    writeControl writeTime;
    writeToFile true;
}
"""


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mold-evidence-root",type=Path)
    p.add_argument("--strict",action="store_true",help="nonzero on source/contract alerts")
    p.add_argument("--require-bilateral",action="store_true",help="nonzero until authentic mold-side evidence supplied")
    args=p.parse_args(argv)
    root=args.root.resolve();out=args.out.resolve()
    cfds=root/"cases_controlled_buoyancy"
    if out==root or out==cfds or cfds in out.parents:
        p.error("will not write into original CFD cases")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        p.error("output must be a new/empty directory; no overwrite")
    evidence_root=args.mold_evidence_root.resolve() if args.mold_evidence_root else None
    report=audit(root,evidence_root)
    out.mkdir(parents=True,exist_ok=True)
    (out/"bilateral_readiness.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    with (out/"case_matrix.csv").open("w",newline="",encoding="utf8") as f:
        cols=["case","status","nominal_interface_m2","source_patch_m2","source_patch_faces",
              "layer_R_m2K_W","mold_status","alerts"]
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for c in report["cases"]:
            sec=c["sections"];geom=sec["nominal_geometry"] or {};power=sec["metal_side_power"] or {}
            w.writerow({"case":c["case"],"status":c["status"],
                "nominal_interface_m2":geom.get("nominal_three_contact_sides_area_m2"),
                "source_patch_m2":power.get("area_m2"),"source_patch_faces":power.get("face_count"),
                "layer_R_m2K_W":(sec["coupling"] or {}).get("nominal_layer_R_m2K_W"),
                "mold_status":sec["mold_side"]["status"],"alerts":"; ".join(c["alerts"])})
    (out/"mold_wall_heat_flux_CANDIDATE.foam").write_text(CANDIDATE,encoding="utf8")
    notes=["# Evidencia necesaria para cierre bilateral", "",
      "No existe postProcessing/mold en los casos versionados. No se inventa flujo complementario.",
      "El candidato wallHeatFlux en archivo .foam NO se instala ni ejecuta automáticamente.",
      "En una COPIA de la simulación, verificar con OpenFOAM Foundation 14: función,",
      "patch mold_to_metal, field y dimensiones, geometría Sf y normales, área real,",
      "signos, tiempos físicos, resistencia de contacto y presupuesto de energía.",
      "La salida de wallHeatFlux no equivale automáticamente a potencia integrada W.",
      "Construir potencia real ∑ q_i A_i con signo y normales correctamente documentados.",
      "Solo entonces entregar un CSV por caso: time_s,outward_power_W, y un provenance.json",
      "con case, patch=mold_to_metal, units=W, orientation=outward_from_mold,",
      "quantity=integrated_interface_power, source_method=OpenFOAM_Foundation14,",
      "measured_area_m2, source_sha256 (del CSV). Sin interpolación ni tiempos inventados.",
      "Incluso con CSV, el comparador solamente produce métricas NUMÉRICAS PROVISIONALES.",
      "Una coincidencia cercana no prueba malla/termodinámica o equivalencia de signos.", ""]
    (out/"CAPTURE_README.md").write_text("\n".join(notes),encoding="utf8")
    bad=sum(bool(c["alerts"]) for c in report["cases"])
    waiting=sum(c["sections"]["mold_side"]["status"]=="NOT_OBSERVED_NO_MOLD_OUTPUT" for c in report["cases"])
    print(f"QuickCup bilateral readiness: {len(report['cases'])} cases; source_alert_cases={bad}; mold_missing={waiting}")
    print("No CFD executed; no true mold-side flux assumed; global physics NOT VALIDATED")
    return int((args.strict and bad>0) or (args.require_bilateral and waiting>0))


if __name__=="__main__":
    raise SystemExit(main())
