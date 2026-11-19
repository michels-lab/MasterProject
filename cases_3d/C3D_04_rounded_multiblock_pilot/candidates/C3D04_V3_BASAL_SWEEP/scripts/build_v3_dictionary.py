#!/usr/bin/env python3
"""Generate one isolated C3D-04 V3 mesh dictionary from the validated V2 source.

Only four *interior* iron-grid vertices at Y=-39.8 mm and the 108
radial-grading values in sand are modified. No metal/mold surface, arc,
block connectivity, Y station, CAD, C14 fields or boundary is modified.
V3 is an experiment, NOT an accepted native mesh.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

VERTEX_RE = re.compile(r"^(\s*)\(([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\)(\s*//\s*(\d+)\s*)$")
RING_RE = re.compile(
    r"^(.*\s+mold\s+\([\d\s]+\)\s+simpleGrading\s+)"
    r"\(1\.5 1 1\)(\s*//\s*slab=(\d+) ring (\d+)\s*)$"
)
CORE_INDICES = {89, 90, 93, 94}


def generate(source: Path, target: Path, delta: float, grading: float) -> dict:
    if not math.isfinite(delta) or not (-0.5 <= delta <= 0.5):
        raise ValueError("core delta must be finite between -0.5 and +0.5 mm")
    if not math.isfinite(grading) or not (1.5 <= grading <= 3.0):
        raise ValueError("sand grading must be finite in [1.5, 3.0]")
    if source.resolve() == target.resolve():
        raise ValueError("Must not overwrite the source dictionary")
    orig = source.read_text(encoding="utf-8")
    replaced_core = set()
    replaced_rings = set()
    out = []
    for line in orig.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        newline = line[len(body):]
        match = VERTEX_RE.fullmatch(body)
        if match and int(match.group(6)) in CORE_INDICES:
            indent, sx, sy, sz, suffix, idx = match.groups()
            idx = int(idx)
            if idx in replaced_core or float(sy) != -39.8:
                raise ValueError(f"Unexpected corner vertex declaration {idx}")
            if float(sx) not in (13.664759, 38.135241) or float(sz) not in (13.664759, 38.135241):
                raise ValueError(f"V2 core vertex has unexpected coordinates: {idx}")
            x = float(sx) + (delta if float(sx) < 25.9 else -delta)
            z = float(sz) + (delta if float(sz) < 25.9 else -delta)
            new_line = f"{indent}({x:.6f} {sy} {z:.6f}){suffix}"
            replaced_core.add(idx)
            out.append(new_line + newline)
            continue
        match = RING_RE.fullmatch(body)
        if match:
            lead, suffix, slab, ring = match.groups()
            key = (int(slab), int(ring))
            if key in replaced_rings:
                raise ValueError(f"Duplicate V2 sand ring slab: {key}")
            replaced_rings.add(key)
            out.append(f"{lead}({grading:.3f} 1 1){suffix}{newline}")
            continue
        out.append(line)
    if replaced_core != CORE_INDICES or len(replaced_rings) != 108:
        raise ValueError(
            f"Unexpected generator scope: {len(replaced_core)} internal vertices, "
            f"{len(replaced_rings)} sand rings"
        )
    # The expected 108 ring declarations are precisely 12 per each of the
    # 9 axial slabs, without changing any original ring connectivity.
    expected_rings = {(slab, ring) for slab in range(9) for ring in range(12)}
    if replaced_rings != expected_rings:
        raise ValueError("Sand grading layer/ring coverage is incomplete")

    result = "".join(out)
    # Geometry on the interface, curved arcs and external patches must be
    # byte-for-byte unchanged. Only radial division/inner mesh is altered.
    for section in ("edges", "boundary"):
        expression = re.compile(r"(?ms)^" + section + r"\s*\(\s*\n.*?^\);")
        a = expression.search(orig)
        b = expression.search(result)
        if not a or not b or a.group(0) != b.group(0):
            raise ValueError(f"Unauthorized change to {section}")
    if len(orig.splitlines()) != len(result.splitlines()):
        raise ValueError("Line count changed unexpectedly")

    # Never modify existing geometry or overwrite any previous candidate.
    with target.open("x", encoding="utf-8") as stream:
        stream.write(result)
    return {
        "status": "GENERATED_C3D04_V3_STATIC_ONLY",
        "reference": str(source),
        "output": str(target),
        "delta_internal_core_mm": delta,
        "radial_sand_grading": grading,
        "changed_interior_core_vertices": sorted(CORE_INDICES),
        "sand_ring_blocks": 108,
        "metal_interface_geometry_changed": False,
        "curved_arcs_changed": False,
        "native_checkmesh_required": True,
        "CFD_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--delta", type=float, required=True)
    parser.add_argument("--grading", type=float, required=True)
    args = parser.parse_args()
    meta = generate(args.source, args.target, args.delta, args.grading)
    print(json.dumps(meta, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
