#!/usr/bin/env python3
"""REAL Foundation14 foamMultiRun 2-solid coupledTemperature shakedown in CI.

Construct two separate tiny blockMesh regions meeting at one *mappedWall*
patch; all 10 T0 dictionaries come from the actual production prepare_t0
file_map and original C14 provenance. Does NOT read/mutate accepted 270788
HEX8 geometry; does NOT validate the thesis, JMatPro or experimental curves.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

T0 = Path(__file__).resolve().parents[1]
LENGTH = 0.01
VOLUME = LENGTH ** 3

def load(name: str, file: Path):
    spec = importlib.util.spec_from_file_location(name, file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"missing production module {file}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

C14 = load("c3d05_native_c14_solver", T0/"scripts/c14_numerical_reference.py")
PREP = load("c3d05_native_prepare_solver", T0/"scripts/prepare_t0.py")
ENERGY = load("c3d05_native_energy_solver", T0/"scripts/postprocess_t0_energy.py")

def block_mesh(region: str) -> str:
    if region not in ("metal","mold"):
        raise ValueError(region)
    x = 0 if region == "metal" else LENGTH
    a = x
    b = x + LENGTH
    p = [(a,0,0),(b,0,0),(b,LENGTH,0),(a,LENGTH,0),
         (a,0,LENGTH),(b,0,LENGTH),(b,LENGTH,LENGTH),(a,LENGTH,LENGTH)]
    vertices = "\n".join("    ({:.9g} {:.9g} {:.9g})".format(*point) for point in p)
    interface = "metal_to_mold" if region=="metal" else "mold_to_metal"
    opposite = "mold_to_metal" if region=="metal" else "metal_to_mold"
    other = "mold" if region=="metal" else "metal"
    ext = "metalTop" if region=="metal" else "moldOuterUnclassified"
    # x+ face for metal, x- face for mold; normals naturally oppose.
    coupling = "(1 2 6 5)" if region=="metal" else "(0 4 7 3)"
    outside = "(0 4 7 3)" if region=="metal" else "(1 2 6 5)"
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object blockMeshDict;
}}
scale 1;
vertices
(
{vertices}
);
blocks (hex (0 1 2 3 4 5 6 7) (1 1 1) simpleGrading (1 1 1));
edges ();
boundary
(
    {interface}
    {{
        type mappedWall;
        neighbourRegion {other};
        neighbourPatch {opposite};
        faces ({coupling});
    }}
    {ext}
    {{
        type patch;
        faces
        (
            {outside}
            (0 3 2 1)
            (4 5 6 7)
            (0 1 5 4)
            (2 3 7 6)
        );
    }}
);
mergePatchPairs ();
"""

def exec_native(args: list[str], cwd: Path, timeout=75) -> str:
    print("+", " ".join(args),flush=True)
    res=subprocess.run(args,cwd=cwd,encoding="utf-8",errors="replace",
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    # Capture complete original output for root-cause diagnostics, but limit CI UI.
    print(res.stdout[-9000:],flush=True)
    if res.returncode:
        raise AssertionError(f"Native Foundation14 exit={res.returncode}: {args}")
    return res.stdout

def main() -> int:
    if os.environ.get("WM_PROJECT_VERSION") != "14":
        raise RuntimeError("Must use real Foundation14 before smoke")
    for cmd in ("foamMultiRun","blockMesh","foamPostProcess","foamDictionary"):
        if not shutil.which(cmd):
            raise RuntimeError("Native Foundation14 command missing: "+cmd)
    inputs=C14.build()
    issues=PREP.validate(inputs)
    if issues:
        raise ValueError("Original archived C14 numeric inputs invalid: "+"; ".join(issues))
    config=PREP.file_map(inputs)
    if len(config)!=10:
        raise ValueError("Expected 10 production dictionaries")
    with tempfile.TemporaryDirectory(prefix="C3D05_REAL_F14_TWO_SOLIDS_") as dirname:
        case=Path(dirname)
        for rel, body in config.items():
            target=case/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(body,encoding="utf-8")
        for region in ("metal","mold"):
            target=case/"system"/region/"blockMeshDict"
            target.write_text(block_mesh(region),encoding="utf-8")
            exec_native(["foamDictionary",str(target)],case)
            exec_native(["blockMesh","-case",str(case),"-region",region],case)
        # This is not just a parser check: actually construct two regional
        # thermos, initialise coupledTemperature and perform the time loop.
        out=exec_native(["foamMultiRun","-case",str(case)],case,timeout=90)
        if re.search(r"FOAM FATAL|Floating point exception|nan",out,re.I):
            raise AssertionError("Native solver log contains FATAL/FPE/NaN")
        if "End" not in out:
            raise AssertionError("Native multi-region solver did not terminate")
        final=float(inputs["simulation"]["endTime_s"])
        last=case/f"{final:.9g}"
        # Foundation14 writes time dirs as 0.02,0.04,... in both regions.
        if not ((last/"metal"/"T").is_file() and (last/"mold"/"T").is_file()):
            raise AssertionError(f"Native solver did not write final T for BOTH solids at {last}")
        for region in ("metal","mold"):
            dict_path=case/"system"/f"T0_energy_{region}"
            dict_path.write_text(ENERGY.functions_dict(region),encoding="utf-8")
            exec_native(["foamPostProcess","-case",str(case),"-region",region,
                         "-dict",f"system/T0_energy_{region}","-time","0:"],case)
            file,rows=ENERGY.inspect_outputs(case,region)
            observed_times=[float(x["time_decimal"]) for x in rows]
            if len(rows)<2 or abs(observed_times[0])>1e-12 or abs(observed_times[-1]-final)>1e-9:
                raise AssertionError(f"Bad native {region} time series {observed_times}")
            t0=rows[0]["T_volume_average_K"]
            expected=float(inputs[region]["T_initial_K"])
            if abs(t0-expected)>1e-3:
                raise AssertionError(f"Initial native {region} temperature is {t0} vs {expected}")
            if not all(math.isfinite(x["T_volume_average_K"]) and x["T_volume_average_K"]>0 for x in rows):
                raise AssertionError(f"Invalid native temperature in region {region}")
            if not all(abs(x["volume_m3"]/VOLUME-1)<1e-6 for x in rows):
                raise AssertionError(f"Invalid native {region} volume, wanted {VOLUME}")
            print(f"FOUNDATION14_NATIVE_COUPLED_{region.upper()}_PASS "
                  f"samples={len(rows)} volume={VOLUME:g}m3 "
                  f"T0={t0:g}K Tend={rows[-1]['T_volume_average_K']:g}K",
                  flush=True)
        print("C3D05_F14_REAL_TWO_SOLID_COUPLED_TEMPERATURE_SOLVER_SMOKE_PASS_"
              "SYNTHETIC_MESH_NOT_ACCEPTED_QUICKCUP",flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
