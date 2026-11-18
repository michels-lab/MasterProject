#!/usr/bin/env python3
"""FS-C02: verify the top is an OPEN atmospheric boundary, NOT a fake lid.

READ ONLY. Reviews frozen OpenFOAM Foundation 14 input and actual blockMesh
patch type if mesh exists. Checks gravity, 60mm domain / 40mm metal column,
atmospheric pressure+velocity+thermal/VOF backflow BCs.

IMPORTANT: Correct boundary TYPES permit outflow; they do not establish
outward gas flux, absence of reflections, or correct thermal predictions.
This diagnostic never runs CFD or writes to the source run.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import sys

from audit_fs_c02_local import SCHEMA, digest, require

FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
REQUIRED_PATCHES = {
    "0/U": ("pressureInletOutletVelocity", None),
    "0/p_rgh": ("prghTotalPressure", None),
    "0/T": ("inletOutlet", "300"),
    "0/alpha.metal": ("inletOutlet", "0"),
}


def block(text: str, label: str) -> str:
    """Read simple non-nested OpenFOAM named dictionary block.

    The actual atmosphere patches here contain no inner dictionaries.
    Refuse missing/duplicated patch instead of guessing.
    """
    pattern = re.compile(r"\b"+re.escape(label)+r"\s*\{([^{}]*)\}", re.S)
    found = list(pattern.finditer(text))
    require(len(found) == 1, "missing/ambiguous " + label + " patch")
    return found[0].group(1)


def token(text: str, name: str) -> str:
    m = re.findall(r"\b"+re.escape(name)+r"\s+([^\s;]+)\s*;",text)
    require(len(m)==1, "missing/ambiguous "+name)
    return m[0]


def parse_geometry(case: Path, *, expected_top_y: float = .06) -> tuple[float, float, float]:
    mesh = (case/"system/blockMeshDict").read_text()
    section = re.search(r"\bvertices\s*\(\s*(.*?)\s*\)\s*;",mesh,re.S)
    require(section is not None, "blockMesh vertices absent")
    coords = re.findall(
        r"\(\s*("+FLOAT+r")\s+("+FLOAT+r")\s+("+FLOAT+r")\s*\)",
        section.group(1)
    )
    require(len(coords)==8, "unexpected geometry, not 8-vertex FS-C02")
    xyz = [[float(v) for v in c] for c in coords]
    top = max(v[1] for v in xyz)
    bottom = min(v[1] for v in xyz)
    require(math.isclose(top,expected_top_y,abs_tol=1e-9) and
            math.isclose(bottom,0.,abs_tol=1e-9),
            "unexpected FS-C02 top height; no fake roof allowed")
    face=block(mesh,"atmosphere")
    require(token(face,"type") == "patch",
            "top is NOT a generic open patch in blockMeshDict")
    require(re.search(r"\bfaces\s*\(\(3\s+7\s+6\s+2\)\)\s*;",face) is not None,
            "atmosphere faces not the outward +Y plane")
    alpha = (case/"0/alpha.metal").read_text()
    metal_box = re.search(
        r"\bbox\s*\(\s*"+FLOAT+r"\s+("+FLOAT+r")\s+"+FLOAT+r"\s*\)\s*"
        r"\(\s*"+FLOAT+r"\s+("+FLOAT+r")\s+"+FLOAT+r"\s*\)\s*;",
        alpha
    )
    require(metal_box is not None, "missing metalColumn box")
    metal_y = float(metal_box.group(2))
    require(math.isclose(float(metal_box.group(1)),0.,abs_tol=1e-9)
            and math.isclose(metal_y,.04,abs_tol=1e-9),
            "unexpected reference metal column (0-0.04m)")
    return top,bottom,metal_y


def verify(run: Path) -> dict:
    root=run.expanduser().resolve()
    case=root/"FS-C02"
    require(root.name.startswith(("FS-C02_", "FS-C02_LAMINAR_"))
            and case.is_dir() and not case.is_symlink(),
            "not an isolated FS-C02 run")
    mf=case/"FS-C02_MANIFEST.json"
    require(mf.is_file() and not mf.is_symlink(),"manifest missing")
    manifest=json.loads(mf.read_text())
    require(manifest.get("schema")==SCHEMA and
            manifest.get("case_id")=="FS-C02",
            "unexpected run schema or case id")
    inputs=manifest.get("generated_input_sha256")
    require(isinstance(inputs,dict) and len(inputs)==20,
            "expected original 20 inputs")
    for rel,hash_value in inputs.items():
        p=Path(rel)
        require(not p.is_absolute() and ".." not in p.parts
                and len(p.parts)>1 and p.parts[0] in ("0","constant","system")
                and (case/p).is_file() and not (case/p).is_symlink(),
                "invalid/missing frozen solver input")
        require(digest(case/p)==hash_value,
                "solver input has changed: "+rel)
    profile=manifest.get("execution_profile")
    extended_air = profile == "HIGH_HEADSPACE_0_01S_RAS_ATMOSPHERE"
    expected_top = .12 if extended_air else .06
    top,bottom,metal_y=parse_geometry(case,expected_top_y=expected_top)
    patch_types={}
    for rel,(expected_type,inflow_value) in REQUIRED_PATCHES.items():
        raw=(case/rel).read_text()
        patch=block(raw,"atmosphere")
        typ=token(patch,"type")
        require(typ==expected_type,
                rel+" top is not open atmospheric "+expected_type)
        if inflow_value is not None:
            m=re.search(r"\binletValue\s+uniform\s+("+FLOAT+r")\s*;",patch)
            require(m is not None and
                    math.isclose(float(m.group(1)),float(inflow_value)),
                    rel+" lacks prescribed ambient backflow")
        if rel=="0/p_rgh":
            require(re.search(r"\bp0\s+\$internalField\s*;",patch) is not None,
                    "p_rgh top does not reference ambient total pressure")
        patch_types[rel]=typ
    p=(case/"0/p").read_text()
    require(re.search(r"\binternalField\s+uniform\s+1e5\s*;",p) is not None,
            "initial absolute pressure not 100kPa")
    grav=(case/"constant/g").read_text()
    require(re.search(r"\bvalue\s+\(\s*0\s+-9\.81\s+0\s*\)\s*;",grav)
            is not None, "gravity not aligned with vertical -Y")
    # blockMesh generates its own boundary file: test actual patch when present.
    mesh_boundary=case/"constant/polyMesh/boundary"
    actual_patch_type=None
    if mesh_boundary.is_file():
        require(not mesh_boundary.is_symlink(),"symlink mesh boundary refused")
        actual_patch_type=token(block(mesh_boundary.read_text(),"atmosphere"),"type")
        require(actual_patch_type=="patch",
                "ACTUAL mesh atmosphere is a wall; invalid outflow")

    return {
        "schema":"masterproject-fs-c02-open-top-static-audit-v1",
        "status":"OPEN_ATMOSPHERIC_BOUNDARY_TYPES_VERIFIED",
        "source_run":str(root),
        "manifest_sha256":digest(mf),
        "top_y_m":top,
        "domain_height_m":top-bottom,
        "initial_metal_surface_y_m":metal_y,
        "initial_air_headspace_m":top-metal_y,
        "top_is_wall":False,
        "top_is_open_patch":True,
        "mesh_atmosphere_patch_type_when_available":actual_patch_type,
        "pressure_reference_initial_Pa":100000.,
        "atmosphere_boundary_conditions":patch_types,
        "T_ambient_inflow_K":300,
        "alpha_metal_atmospheric_inflow":0,
        "gravity_m_s2":[0,-9.81,0],
        "open_boundary_allows_air_out_and_backflow":True,
        "outgoing_air_flux_actually_measured":False,
        "effect_of_20mm_top_proximity_verified":False,
        "physics_of_gas_heating_validated":False,
        "notes":[
            "OPEN patch does not mean atmospheric gas actually leaves in a saved time window",
            "Need face flux phi/rhoPhi or explicit patch flux monitoring to prove air outflow",
            f"{(top-metal_y)*1000:.0f}mm initial air gap; boundary placement sensitivity remains unverified",
            "Does not model mold, solidification, feeding, porosity or shrinkage",
        ],
    }


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        print(json.dumps(verify(args.run),indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("FS-C02 OPEN TOP BLOCKED: "+str(e),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
