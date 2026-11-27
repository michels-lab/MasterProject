#!/usr/bin/env python3
"""Compare pinned C14 fixed 10 s archives; no CFD, no interpolation.

Four common 2D/A/B lines and thirteen additional A/B lines; use only
identical physical stations within each group and each saved time.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path
from analyze_c3d05_b_corrected_profiles import read_xy, REQUIRED

A_REF = "1ac7269161ce7f12c73d109571efbf35f572481a"
B_REF = "8f8135876275434363f8cd37a32f73190417f578"
C_REF = "03c543cad38bbc033a44d7d6c62b788f943116ed"
THRESHOLD = 1e-4
TOL = 1e-7
FIELDS = ("T", "phaseChangeSource:alpha1", "U_x", "U_y", "U_z")
SHARED = {"line_y10mm", "line_y20mm", "line_y30mm", "line_x20mm"}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def revision(path):
    return subprocess.check_output(
        ["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()

def nominal_lines(path):
    text = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", path.read_text())
    lines = {}
    for name, block in re.findall(r"(\w+)\s*\{([^{}]*\blineUniform\s*;[^{}]*)\}", text):
        require(name not in lines, "duplicate nominal line: " + name)
        item = {}
        for key in ("start", "end"):
            match = re.search(r"\b" + key + r"\s*\(([^)]*)\)\s*;", block)
            require(match is not None, "missing endpoint " + name)
            item[key] = [float(x) for x in match.group(1).split()]
            require(len(item[key]) == 3 and all(math.isfinite(x) for x in item[key]),
                    "invalid endpoint " + name)
        item["axis"] = re.search(r"\baxis\s+([xyz])\s*;", block).group(1)
        item["requested_points"] = int(re.search(r"\bnPoints\s+(\d+)\s*;", block).group(1))
        lines[name] = item
    return lines

def check_nominal(a, b, c):
    require(set(a) == set(b) and len(a) == 17 and set(c) == SHARED,
            "unexpected nominal line inventory")
    for name, x in a.items():
        for y, offset in [(b[name], (0,0,0))] + (
                [(c[name], (.0059,-.04,.0209))] if name in SHARED else []):
            require(x["axis"] == y["axis"] and x["requested_points"] == y["requested_points"] == 80,
                    "different line sampling contract " + name)
            for key in ("start", "end"):
                require(all(abs(i-j-k) <= 1e-9 for i,j,k in zip(x[key],y[key],offset)),
                        "different nominal line geometry " + name)

def classify(value):
    return -1 if value < -THRESHOLD else 1 if value > THRESHOLD else 0

def station_map(rows, axis, offset=0.0):
    result = {}
    for row in rows:
        x = row[axis] + offset
        key = round(x / TOL)
        require(key not in result, "ambiguous coordinate after quantization")
        require(0 <= row["phaseChangeSource:alpha1"] <= 1, "alpha1 out of bounds")
        require(row["T"] > 0, "non-positive absolute temperature")
        result[key] = (x, row)
    return result

def match_stations(maps):
    keys = sorted(set.intersection(*(set(m) for m in maps.values())))
    require(len(keys) > 1, "insufficient common stations")
    for k in keys:
        coords = [m[k][0] for m in maps.values()]
        require(max(coords)-min(coords) <= TOL, "coordinate mismatch")
    return {name: [m[k][1] for k in keys] for name,m in maps.items()}, keys

def mean(values):
    return math.fsum(values)/len(values)

def metrics(rows):
    u = [r["U_y"] for r in rows]
    flags = [classify(x) for x in u]
    return {"T_mean_K":mean([r["T"] for r in rows]),
            "alpha1_mean_line_samples":mean([r["phaseChangeSource:alpha1"] for r in rows]),
            "Uy_min_m_s":min(u), "Uy_max_m_s":max(u),
            "speed_max_m_s":max(math.hypot(r["U_x"],r["U_y"],r["U_z"]) for r in rows),
            "down_points":flags.count(-1), "up_points":flags.count(1),
            "deadband_points":flags.count(0)}

def differences(a,b):
    result = {}
    for field in FIELDS:
        d = [x[field]-y[field] for x,y in zip(a,b)]
        result["bias_"+field] = mean(d)
        result["rmse_"+field] = math.sqrt(mean([v*v for v in d]))
    result["opposite_Uy_sign_points"] = sum(
        classify(x["U_y"])*classify(y["U_y"]) == -1 for x,y in zip(a,b))
    return result

def csv_write(path, rows):
    require(bool(rows), "empty report")
    with path.open("x",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def run(a,b,c,out):
    roots = {k:p.resolve(strict=True) for k,p in {"A":a,"B":b,"2D":c}.items()}
    raw_out = out.absolute()
    out = raw_out.resolve()
    require(not raw_out.is_symlink() and not out.exists() and all(
        out != p and p not in out.parents and out not in p.parents for p in roots.values()),
        "output must be a new independent directory")
    refs = {k:revision(p) for k,p in roots.items()}
    require(refs == {"A":A_REF,"B":B_REF,"2D":C_REF}, "source revision mismatch")
    ap = roots["A"]/"system"
    cp = roots["2D"]/"system/lineProfiles"
    bp = roots["B"]/"C3D05_B_C14_CORRECTED_SAMPLING_REPORT.json"
    br = json.loads(bp.read_text())
    require(br["status"]=="CORRECTED_SAVED_TIME_SAMPLING_VALID" and
            br["checked_original_evidence_unchanged"] and
            not br["solver_rerun"] and br["archived_dt_s"] == .1,
            "unexpected B provenance")
    aa = nominal_lines(ap/"lineProfiles")
    extra = nominal_lines(ap/"additional3DProfiles")
    require(not set(aa)&set(extra), "duplicate A line")
    aa.update(extra)
    bb = {name:s for group in br["profiles"].values() for name,s in group.items()}
    check_nominal(aa,bb,nominal_lines(cp))
    manifest = {"A":{},"B":{},"2D":{}}
    for model,path in [("A",ap/"lineProfiles"),("A",ap/"additional3DProfiles"),
                       ("B",bp),("2D",cp)]:
        manifest[model][str(path.relative_to(roots[model]))]=sha(path)
    line_rows, pair_rows = [], []
    for group, lines in br["profiles"].items():
        ag = {"horizontalProfilesB3D":"horizontalProfiles",
              "verticalProfilesB3D":"verticalProfiles",
              "additional3DProfilesB":"additional3DProfiles"}[group]
        for name,s in lines.items():
            prior = None
            axis = s["axis"]
            for tick in range(101):
                t = tick/10
                label = format(t,"g")
                relative = {"A":Path("postProcessing/metal/C14CanonicalProfiles")/ag/label/(name+".xy"),
                            "B":Path("postProcessing/metal")/("C14Canonical"+group)/label/(name+".xy")}
                if name in SHARED:
                    relative["2D"]=Path("postProcessing/metal")/ag/label/(name+".xy")
                maps = {}
                for model,rel in relative.items():
                    path = roots[model]/rel
                    require(path.resolve().is_relative_to(roots[model]), "source path escapes archive")
                    rows = read_xy(path,axis,REQUIRED)
                    offset = (.0059 if axis=="x" else -.04) if model=="2D" else 0.
                    maps[model]=station_map(rows,axis,offset)
                    manifest[model][str(rel)]=sha(path)
                matched,keys=match_stations(maps)
                signature={k:tuple(m) for k,m in maps.items()}
                require(prior is None or prior==signature, "station grid changed "+name)
                prior=signature
                for model,rs in matched.items():
                    line_rows.append({"profile":name,"time_s":t,"model":model,
                        "n_native":len(maps[model]),"n_common":len(keys),**metrics(rs)})
                for x,y in itertools.combinations(matched,2):
                    pair_rows.append({"profile":name,"time_s":t,"first":x,"second":y,
                        "n_common":len(keys),**differences(matched[x],matched[y])})
    require(len(line_rows)==3838 and len(pair_rows)==2525, "incomplete report coverage")
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".c14_comparison_",dir=out.parent) as tmp:
        staged=Path(tmp)/"report"
        staged.mkdir()
        csv_write(staged/"line_metrics.csv",line_rows)
        csv_write(staged/"pair_metrics.csv",pair_rows)
        report={"status":"COMPARISON_COMPLETE_NOT_PHYSICALLY_VALIDATED","revisions":refs,
            "saved_times":101,"line_metrics":len(line_rows),"pair_metrics":len(pair_rows),
            "source_profiles":3838,"source_sha256":manifest,
            "output_sha256":{p.name:sha(p) for p in staged.iterdir()},
            "threshold_m_s":THRESHOLD,"coordinate_tolerance_m":TOL,
            "scope":"four triple-common lines and thirteen A/B lines; no area/volume averages",
            "physical_validation":False,"grid_independence":False,"solver_rerun":False}
        (staged/"REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
        require(not out.exists(), "output appeared during analysis")
        staged.rename(out)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("a","b","c","out"):
        parser.add_argument("--"+key,type=Path,required=True)
    args=parser.parse_args()
    run(args.a,args.b,args.c,args.out)

if __name__=="__main__":
    main()
