#!/usr/bin/env python3
"""NATIVE Foundation14 (no CFD) two-region one-cell volFieldValue smoke.

Creates a private temporary case, independently runs Foundation14 blockMesh
and foamPostProcess on uniform 400K metal and 300K mold fields, then feeds the
ACTUAL native text files through postprocess_t0_energy.read_volume_average.
Nothing in the accepted C3D-05 mesh, C14, original cases or user's WSL is read.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

T0 = Path(__file__).resolve().parents[1]
module = T0 / "scripts/postprocess_t0_energy.py"
spec = importlib.util.spec_from_file_location("c3d05_native_energy_smoke", module)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

MESH_DICT = """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object blockMeshDict;
}
scale 1;
vertices
(
    (0 0 0) (1 0 0) (1 1 0) (0 1 0)
    (0 0 1) (1 0 1) (1 1 1) (0 1 1)
);
blocks
(
    hex (0 1 2 3 4 5 6 7) (1 1 1) simpleGrading (1 1 1)
);
edges ();
boundary
(
    walls
    {
        type wall;
        faces
        (
            (0 3 2 1)
            (4 5 6 7)
            (0 1 5 4)
            (1 2 6 5)
            (2 3 7 6)
            (3 0 4 7)
        );
    }
);
mergePatchPairs ();
"""
CONTROL = """FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object controlDict;
}
application foamPostProcess;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 0.1;
deltaT 0.1;
writeControl timeStep;
writeInterval 1;
runTimeModifiable false;
"""
def temperature_field(region: str, temperature: float) -> str:
    return f"""FoamFile
{{
    version 2.0;
    format ascii;
    class volScalarField;
    location "0/{region}";
    object T;
}}
dimensions [0 0 0 1 0 0 0];
internalField uniform {temperature};
boundaryField
{{
    walls
    {{
        type zeroGradient;
    }}
}}
"""


def run(cmd: list[str], cwd: Path):
    print("+", " ".join(cmd), flush=True)
    res = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, check=False, timeout=90)
    print(res.stdout[-3500:], flush=True)
    if res.returncode:
        raise AssertionError(f"native Foundation14 exited {res.returncode}: {' '.join(cmd)}")
    return res.stdout


def main() -> int:
    if os.environ.get("WM_PROJECT_VERSION") != "14":
        raise RuntimeError("Must source actual OpenFOAM Foundation14")
    for command in ("blockMesh","foamPostProcess","foamDictionary"):
        if shutil.which(command) is None:
            raise RuntimeError(f"Missing official F14 utility: {command}")
    with tempfile.TemporaryDirectory(prefix="c3d05_F14_synthetic_energy_") as dirname:
        case = Path(dirname)
        (case / "system").mkdir()
        (case / "system/controlDict").write_text(CONTROL, encoding="utf-8")
        for region, temperature in (("metal",400.0),("mold",300.0)):
            (case / "system" / region).mkdir()
            (case / "0" / region).mkdir(parents=True)
            (case / "system" / region / "blockMeshDict").write_text(MESH_DICT,encoding="utf-8")
            (case / "0" / region / "T").write_text(temperature_field(region,temperature),encoding="utf-8")
            (case / "system" / f"T0_energy_{region}").write_text(driver.functions_dict(region),encoding="utf-8")
            run(["foamDictionary",str(case/"system"/f"T0_energy_{region}")],case)
            run(["blockMesh","-case",str(case),"-region",region],case)
            run(["foamPostProcess","-case",str(case),"-region",region,
                 "-dict",f"system/T0_energy_{region}","-time","0:"],case)
            outfile, rows=driver.inspect_outputs(case,region)
            if len(rows)!=1 or rows[0]["time_decimal"]!=0:
                raise AssertionError(f"{region}: expected exact time-zero native field")
            if abs(rows[0]["volume_m3"]-1.0)>1e-9:
                raise AssertionError(f"{region}: wrong actual native mesh volume")
            if abs(rows[0]["T_volume_average_K"]-temperature)>1e-9:
                raise AssertionError(f"{region}: wrong actual native T field")
            print(f"FOUNDATION14_SYNTHETIC_{region.upper()}_PASS: native volume=1 m3, "
                  f"T={temperature}K file={outfile}",flush=True)
    print("FOUNDATION14_REAL_TWO_REGION_FOAMPOSTPROCESS_SMOKE_PASS__NO_CFD_NO_THESIS_MESH")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
