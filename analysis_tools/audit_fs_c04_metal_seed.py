#!/usr/bin/env python3
"""FS-C04 *STATIC* initial metal phase plan. READ ONLY, NO solver or field.

Use FS-C03's three original metal-labeled hexa blocks to identify the
INITIAL IRON volume within FS-C04's *single* region fluid (metal+air).
The metal/air interface is INTERNAL to that fluid mesh. Derive exact
block geometry volume (linear cross-section, Simpson quadrature).
DO NOT infer native split-region cell indices/order from block indices.
Writing 0/fluid/alpha.metal requires an independently verified
cell-to-block mapping, and is intentionally NOT provided by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

from audit_fs_c03_exterior_mesh import (
    SOURCE as ORIGINAL, parse, require, orientation_jacobian,
)
from audit_fs_c04_fluid_mold import (
    SOURCE as TWO_ZONE, audit as audit_two_zone, read_new_blocks,
)

REF_CAD_VOLUME_MM3 = 47987.697
METAL_BLOCKS=(9,14,19)
METAL_CELLS=2368
GAS_CELLS=32000
FLUID_CELLS=34368
SAND_CELLS=7680
MAX_RELATIVE_CAD_VOLUME_DEVIATION=0.01


def area_xz(poly: list[tuple[float,float,float]]) -> float:
    require(len(poly)==4,"expected quadrilateral horizontal slice")
    require(all(math.isclose(p[1],poly[0][1],abs_tol=1e-8) for p in poly),
            "non-horizontal metal cross-section")
    area=abs(sum(poly[i][0]*poly[(i+1)%4][2]
                 -poly[(i+1)%4][0]*poly[i][2]
                 for i in range(4)))/2
    require(area>0,"degenerate metal cross-section")
    return area


def calculate_metal_block(v: tuple[int,...], count: tuple[int,...],
                          vertices: list[tuple[float,...]], idx: int)->dict:
    require(len(v)==8 and len(count)==3,
            "incorrect hexa block indexing")
    points=[vertices[k] for k in v]
    a0=area_xz(points[:4])
    a1=area_xz(points[4:])
    y0,y1=points[0][1],points[4][1]
    require(y0<y1 and all(math.isclose(p[1],y0,abs_tol=1e-8)
                          for p in points[:4])
            and all(math.isclose(p[1],y1,abs_tol=1e-8)
                    for p in points[4:]),
            "metal volume formula requires two horizontal slices")
    require(orientation_jacobian(v,vertices)>0,
            "inverse metal hexa orientation")
    middle=[tuple((a+b)/2 for a,b in zip(points[i],points[i+4]))
            for i in range(4)]
    am=area_xz(middle)
    # Each cross section's vertices are linear in height; its
    # quadrilateral area is quadratic => Simpson integration exact.
    volume=(y1-y0)*(a0+4*am+a1)/6
    require(volume>0 and math.isfinite(volume),"invalid metal volume")
    return {
        "reference_original_block_index":idx,
        "fluid_region_initial_phase":"metal",
        "initial_alpha_metal_in_block":1,
        "expected_native_cell_count":math.prod(count),
        "y_lower_mm":y0,
        "y_upper_mm":y1,
        "area_bottom_mm2":a0,
        "area_middle_mm2":am,
        "area_top_mm2":a1,
        "analytic_volume_mm3":volume,
    }


def audit() -> dict:
    src=ORIGINAL.read_text()
    target=TWO_ZONE.read_text()
    comparison=audit_two_zone(target)
    vertices,source_blocks,_=parse(src)
    new_blocks=read_new_blocks(target)
    orig_metal=[i for i,(_,name,_) in enumerate(source_blocks)
                if name=="metal"]
    require(orig_metal==list(METAL_BLOCKS),
            "original pilot metal blocks changed")
    require(len(new_blocks)==len(source_blocks)==53,
            "original and fluid+solid block count mismatch")
    blocks=[]
    for i in METAL_BLOCKS:
        v,name,count=source_blocks[i]
        nv,nname,ncount=new_blocks[i]
        require((v,count)==(nv,ncount) and nname=="fluid" and name=="metal",
                "metal hexa no longer identical inside fluid region")
        blocks.append(calculate_metal_block(v,count,vertices,i))
    cells=sum(b["expected_native_cell_count"] for b in blocks)
    volume=sum(b["analytic_volume_mm3"] for b in blocks)
    require(cells==METAL_CELLS,"unexpected seed metal cell count")
    require(comparison["fluid_cell_count_predicted"]==FLUID_CELLS
            and comparison["mold_cell_count_predicted"]==SAND_CELLS,
            "fluid or sand mesh changed")
    require(FLUID_CELLS-cells==GAS_CELLS,
            "unassigned fluid cells must all be initial gas")
    frac=abs(volume-REF_CAD_VOLUME_MM3)/REF_CAD_VOLUME_MM3
    require(frac<MAX_RELATIVE_CAD_VOLUME_DEVIATION,
            "pilot block volume too different from reference CAD")
    return {
        "schema":"masterproject-fs-c04-initial-phase-geometry-plan-v1",
        "status":"ANALYTIC_METAL_SEED_IDENTIFIED_NO_FIELD_WRITTEN",
        "source_3_zone_sha256":hashlib.sha256(src.encode()).hexdigest(),
        "source_2_zone_sha256":hashlib.sha256(target.encode()).hexdigest(),
        "fluid_region":"fluid",
        "mold_region":"mold",
        "initial_iron_alpha_metal":1.0,
        "initial_air_alpha_metal":0.0,
        "original_metal_block_indices":list(METAL_BLOCKS),
        "initial_metal_cell_count_predicted":cells,
        "initial_air_cell_count_predicted":GAS_CELLS,
        "fluid_cells_predicted":FLUID_CELLS,
        "solid_mold_cells_predicted":SAND_CELLS,
        "pilot_initial_metal_volume_mm3":volume,
        "pilot_initial_metal_volume_m3":volume*1e-9,
        "reference_CAD_metal_volume_mm3":REF_CAD_VOLUME_MM3,
        "pilot_to_CAD_volume_difference_mm3":volume-REF_CAD_VOLUME_MM3,
        "pilot_to_CAD_relative_volume_difference":frac,
        "original_metal_block_details":blocks,
        "metal_air_internal_fluid_face_confirmed_by_zone_audit":True,
        "cell_volume_integral_from_native_mesh_verified":False,
        "native_cell_to_block_addressing_verified":False,
        "initial_alpha_field_written":False,
        "mold_region_contains_metal_alpha":False,
        "CAD_surface_fidelity_verified":False,
        "CFD_or_CHT_executed":False,
        "notes":[
            "Block-based phase plan, NOT a native OpenFOAM field or cell index mapping",
            "Do not use rectangular boxes to approximate tapered metal region without verifying each cell",
            "Before writing alpha.metal to 0/fluid, verify native region cell addressing and integrate phase-weighted volume",
            "No solid fraction, latent heat, shrinkage or graphite expansion modelled",
        ]
    }


def main(argv=None)->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    try:
        print(json.dumps(audit(),indent=2))
        return 0
    except (ValueError,OSError) as ex:
        print("FS-C04 INITIAL METAL SEED BLOCKED: "+str(ex),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
