#!/usr/bin/env python3
"""B-FS-01: stage a Foundation 14 water/air VOF analogue; audit volume exports.

Only the official compressibleVoF/damBreak files supplied locally are cloned.
No solver run, metal thermophysics, solidification, or shrinkage is implied.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

# 40 x 60 x 10 mm closed sides/bottom + open atmosphere, 2D empty faces.
WIDTH, HEIGHT, DEPTH, FILL_HEIGHT = .04, .06, .01, .04
REFERENCE_VOLUME = WIDTH * DEPTH * FILL_HEIGHT
END_TIME = .1
SOURCE_FILES = (
    "system/controlDict", "system/fvSchemes", "system/fvSolution",
    "constant/phaseProperties", "constant/physicalProperties.water",
    "constant/physicalProperties.air", "constant/g", "constant/momentumTransport",
    "0/alpha.water", "0/T", "0/U", "0/p", "0/p_rgh",
)
BLOCK_MESH = """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object blockMeshDict;
}
scale 1;
vertices
(
    (0 0 0)
    (0.04 0 0)
    (0.04 0.06 0)
    (0 0.06 0)
    (0 0 0.01)
    (0.04 0 0.01)
    (0.04 0.06 0.01)
    (0 0.06 0.01)
);
blocks
(
    hex (0 1 2 3 4 5 6 7) (80 120 1) simpleGrading (1 1 1)
);
edges ();
boundary
(
    leftWall { type wall; faces ((0 4 7 3)); }
    rightWall { type wall; faces ((1 2 6 5)); }
    lowerWall { type wall; faces ((0 1 5 4)); }
    atmosphere { type patch; faces ((3 7 6 2)); }
    frontAndBack { type empty; faces ((0 3 2 1) (4 5 6 7)); }
);
mergePatchPairs ();
"""
ALPHA = """FoamFile
{
    version 2.0;
    format ascii;
    class volScalarField;
    location "0";
    object alpha.water;
}
dimensions [];
internalField
{
    type zonal;
    defaultValue 0;
    zones
    {
        waterColumn
        {
            type box;
            box (0 0 -1) (0.04 0.04 1);
            value 1;
        }
    }
}
boundaryField
{
    #includeEtc "caseDicts/setConstraintTypes"
    wall { type zeroGradient; }
    atmosphere
    {
        type inletOutlet;
        inletValue uniform 0;
    }
}
"""
FUNCTIONS = """
functions
{
    waterVolume
    {
        type volFieldValue;
        libs ("libfieldFunctionObjects.so");
        cellZone all;
        operation volIntegrate;
        fields (alpha.water);
        executeControl writeTime;
        writeControl writeTime;
        writeInterval 1;
        writeToFile true;
        log true;
    }
}
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(cond, reason):
    if not cond:
        raise ValueError(reason)


def one_replace(data, key, value):
    pattern = r"(?m)^(\s*" + re.escape(key) + r"\s+)([^;]+)(;)"
    hits = list(re.finditer(pattern, data))
    require(len(hits) == 1, f"unrecognized or ambiguous original {key}")
    return re.sub(pattern, lambda m: m.group(1) + value + m.group(3), data, count=1)


def check_upstream(src):
    require(src.is_dir(), "Foundation14 damBreak tutorial directory is missing")
    require(not src.is_symlink(), "upstream root must not be a symlink")
    for f in src.rglob("*"):
        require(not f.is_symlink(), f"refusing symlink in upstream source: {f}")
    for path in SOURCE_FILES:
        require((src / path).is_file(), f"missing required Foundation14 file: {path}")
    control = (src / "system/controlDict").read_text()
    phases = (src / "constant/phaseProperties").read_text()
    gravity = (src / "constant/g").read_text()
    require(bool(re.search(r"(?m)^\s*solver\s+compressibleVoF\s*;", control)),
            "upstream must be official compressibleVoF benchmark")
    require(bool(re.search(r"phases\s*\(\s*water\s+air\s*\)\s*;", phases)),
            "upstream must be water/air; metal is NOT being modelled")
    require(bool(re.search(r"value\s*\(\s*0\s+-9\.81\s+0\s*\)", gravity)),
            "upstream gravity does not point down -Y")
    require("wall" in (src / "0/U").read_text()
            and "atmosphere" in (src / "0/U").read_text(),
            "upstream boundary-field schema changed")
    return {p: sha(src / p) for p in SOURCE_FILES}


def stage(template, out):
    template = template.resolve()
    out = out.absolute()
    require(not out.exists(), "refusing to overwrite an existing path")
    require(out != template and template not in out.parents and out not in template.parents,
            "output and template must be independent")
    require("cases_controlled_buoyancy" not in out.parts and "cases_3d" not in out.parts,
            "never write in original research-case trees")
    upstream = check_upstream(template)
    # Copy only the official case inputs, no logs, processor directories or CFD results.
    out.mkdir(parents=True)
    for folder in ("0", "constant", "system"):
        shutil.copytree(template / folder, out / folder)
    (out / "system/blockMeshDict").write_text(BLOCK_MESH)
    (out / "0/alpha.water").write_text(ALPHA)
    control = (out / "system/controlDict").read_text()
    require("functions" not in control, "original controlDict contains function objects; review manually")
    for key, value in (
        ("endTime", str(END_TIME)), ("deltaT", "0.0001"),
        ("writeInterval", "0.01"), ("maxCo", "0.25"),
        ("maxAlphaCo", "0.25"), ("maxDeltaT", "0.001"),
    ):
        control = one_replace(control, key, value)
    control += "\n" + FUNCTIONS
    (out / "system/controlDict").write_text(control)
    sources = {}
    for folder in ("0", "constant", "system"):
        for f in (out / folder).rglob("*"):
            if f.is_file():
                sources[f.relative_to(out).as_posix()] = sha(f)
    result = {
        "schema": "quickcup-bfs01-hydro-analogue-v1",
        "status": "PREPARED_NOT_MESHED_OR_RUN",
        "template": "OpenFOAM Foundation 14 tutorials/compressibleVoF/damBreak",
        "upstream_sha256": upstream, "generated_sha256": sources,
        "geometry_m": {"width": WIDTH, "height": HEIGHT, "depth": DEPTH,
                       "water_fill_height": FILL_HEIGHT},
        "analytical_initial_water_volume_m3": REFERENCE_VOLUME,
        "end_time_s": END_TIME,
        "fluid_identity": "WATER_AIR_ANALOGUE_NOT_MOLTEN_IRON",
        "physics": {"vof": "requested but not executed",
                    "metal": False, "solidification": False,
                    "mold": False, "shrinkage": False},
        "acceptance": "volume-only numerical check on actual postProcessing; mass not measured",
    }
    (out / "BFS01_MANIFEST.json").write_text(json.dumps(result, indent=2) + "\n")
    (out / "HOW_TO_RUN.md").write_text(
        "# B-FS-01 | VOF water-air hydrodynamic analogue\n\n"
        "This deliberately does NOT model iron, shrinkage, latent heat or CHT.\n"
        "OpenFOAM Foundation v14 is required. In this new staged directory:\n\n"
        "    blockMesh\n    checkMesh\n    foamRun\n\n"
        "Do not invoke Allclean/Allrun in an original QuickCup case.\n"
        "Only a successful real Ubuntu run can establish runtime viability.\n"
        "Check mesh patch orientation, alpha bounds, mass closure and solver log.\n"
        "The postProcessing/waterVolume/0/volFieldValue.dat file is the expected\n"
        "volume reduction, NOT an integral of rho*alpha, and NOT a mass balance.\n"
        "Use the audit subcommand on the actual output once generated.\n")
    return result


def parse_volume(path):
    require(path.is_file(), f"missing original numerical output: {path}")
    rows = []
    headers = []
    for line_no, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        txt = raw.strip()
        if not txt:
            continue
        if txt.startswith("#"):
            if txt.startswith("# Time"):
                headers.append(tuple(txt[1:].split()))
            continue
        cols = txt.split()
        require(len(cols) == 2, f"line {line_no}: expected time + one integral")
        try:
            t, v = map(float, cols)
        except ValueError as err:
            raise ValueError(f"line {line_no}: nonnumerical volume row") from err
        require(all(map(math.isfinite, (t,v))) and t >= 0 and v >= 0,
                f"line {line_no}: invalid time/volume")
        require(not rows or t > rows[-1][0], f"line {line_no}: time not strictly increasing")
        rows.append((t,v))
    require(headers and all(h == ("Time","volIntegrate(alpha.water)") for h in headers),
            "missing/ambiguous OpenFOAM water volume field header")
    require(len(rows) >= 2, "insufficient volume times")
    return rows


def audit(case, out, limit=.005):
    require(isinstance(limit, float) and math.isfinite(limit) and 0 < limit < 1,
            "fractional tolerance must lie inside (0,1)")
    case = case.resolve()
    out = out.absolute()
    require(not out.exists(), "will not overwrite existing audit")
    require(case not in out.parents and out != case
            and "cases_controlled_buoyancy" not in out.parts,
            "audit must not write inside case/original CFD data")
    manifest = case / "BFS01_MANIFEST.json"
    require(manifest.is_file(), "missing BFS01 manifest")
    m = json.loads(manifest.read_text())
    require(m.get("schema") == "quickcup-bfs01-hydro-analogue-v1"
            and m.get("fluid_identity") == "WATER_AIR_ANALOGUE_NOT_MOLTEN_IRON",
            "wrong benchmark identity, not a B-FS-01 surrogate")
    require(math.isclose(m["analytical_initial_water_volume_m3"],REFERENCE_VOLUME),
            "benchmark geometry/provenance mismatch")
    source = case / "postProcessing/waterVolume/0/volFieldValue.dat"
    rows = parse_volume(source)
    errors = []
    if abs(rows[0][0]) > 1e-7:
        errors.append("no initial time-zero numerical volume measurement")
    if rows[-1][0] < END_TIME - .005:
        errors.append("endTime not reached in committed numerical data")
    if abs(rows[0][1] - REFERENCE_VOLUME) / REFERENCE_VOLUME > limit:
        errors.append("initial water volume does not match analytical fill")
    drift = max(abs(v - rows[0][1]) / REFERENCE_VOLUME for _,v in rows)
    if drift > limit:
        errors.append("observed maximum water VOF volume drift exceeds tolerance")
    rec = {
        "schema": "quickcup-bfs01-volume-screen-v1",
        "status": "VOLUME_SCREEN_PASSED" if not errors else "REVIEW",
        "only_surrogate_hydrodynamics": True, "not_mass_or_shrinkage_validation": True,
        "source_sha256": sha(source),
        "observed_points": len(rows), "start_time_s": rows[0][0],
        "last_time_s": rows[-1][0],
        "analytical_initial_volume_m3": REFERENCE_VOLUME,
        "first_measured_volume_m3": rows[0][1],
        "last_measured_volume_m3": rows[-1][1],
        "max_abs_volume_drift_fraction": drift,
        "equivalent_height_last_m": rows[-1][1] / (WIDTH * DEPTH),
        "equivalent_height_is_not_actual_surface_elevation": True,
        "threshold_fraction": limit, "alerts": errors,
    }
    out.mkdir(parents=True)
    (out / "volume_screen.json").write_text(json.dumps(rec, indent=2) + "\n")
    with (out / "volume_times.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(("time_s","water_integral_m3","relative_drift_from_initial"))
        for t,v in rows:
            w.writerow((t, v, (v-rows[0][1])/REFERENCE_VOLUME))
    return rec


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("stage", help="prepare fresh safe standalone B-FS-01 surrogate")
    s.add_argument("--tutorial",type=Path,required=True)
    s.add_argument("--out",type=Path,required=True)
    a = sub.add_parser("audit",help="read actual solver volume integral (no CFD)")
    a.add_argument("--case",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--max-relative-drift",type=float,default=.005)
    args = p.parse_args(argv)
    try:
        if args.command == "stage":
            result=stage(args.tutorial,args.out)
            print(f"B-FS-01 staged: {args.out}; STATUS {result['status']}")
            print("No OpenFOAM run; WATER/AIR analogue only. Execute locally and audit actual outputs.")
            return 0
        result=audit(args.case,args.out,float(args.max_relative_drift))
        print(f"B-FS-01 {result['status']}; max volume drift={result['max_abs_volume_drift_fraction']:.6g}")
        print("No proof of molten-iron mass closure, metal shrinkage or solidification.")
        return int(result["status"] != "VOLUME_SCREEN_PASSED")
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as err:
        p.error(str(err))


if __name__ == "__main__":
    raise SystemExit(main())
