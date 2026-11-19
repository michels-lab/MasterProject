#!/usr/bin/env python3
"""C3D-04 Caso A V4: surgical basal-transition experiments from native V3/T06.

Modes:
  inner_y: move ONLY four strictly interior metal vertices axially in Y.
  profile: interpolate the 12 metal/mold interface vertices and eight metal
           arc midpoints at Y=-39.8 between the -40 and -39.8 stations.

All runs are fresh, with full checkMesh and CAD-area gates. Surface-fit fidelity
is NOT automatically guaranteed by this operation. NO CFD.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

VERT = re.compile(r"^(\s*)\(([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\)(\s*//\s*(\d+)\s*)$")
ARC = re.compile(
    r"^(\s*arc\s+\d+\s+\d+\s+)\(([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\)"
    r"(\s*//\s*a\s+Y=([-\d.]+)\s*)$"
)
INNER = {89, 90, 93, 94}
OUTER = set(range(84, 100)) - INNER
CAD_SECTION_AT_MINUS39_8_MM2 = 909.900  # STL section quoted in C3D-04 source README
MAX_SECTION_ERROR_PERCENT = 3.0


def build(source: Path, target: Path, mode: str, value: float) -> dict:
    if mode not in ("inner_y", "profile") or not math.isfinite(value):
        raise ValueError("Expected mode=inner_y|profile and finite value")
    if mode == "inner_y" and not (-0.15 <= value <= 0.20):
        raise ValueError("Inner axial move must be [-0.15,+0.20] mm")
    if mode == "profile" and not (0.20 <= value <= 0.95):
        raise ValueError("Metal profile interpolation alpha must be [0.20,0.95]")
    # Profile edits must not silently pass an integral-area gate while
    # becoming inaccurate at the crucial basal CAD section Y=-39.8 mm.
    # The radius and width interpolate linearly for these rounded squares.
    section_area = None
    section_error_percent = None
    if mode == "profile":
        width = 28.280 + (30.178 - 28.280) * value
        corner_radius = 2.0 + (1.0 - 2.0) * value
        section_area = width**2 - (4.0 - math.pi) * corner_radius**2
        section_error_percent = 100 * (section_area / CAD_SECTION_AT_MINUS39_8_MM2 - 1)
        if abs(section_error_percent) > MAX_SECTION_ERROR_PERCENT:
            raise ValueError(
                f"Section Y=-39.8 mm departs from CAD by "
                f"{section_error_percent:+.3f}% (>3%): alpha={value}"
            )
    if source.resolve() == target.resolve():
        raise ValueError("Never overwrite native V3 baseline")
    data = source.read_text(encoding="utf-8")
    original_vertices = {}
    metal_arcs_by_station = {-40.0: [], -39.8: []}
    for raw in data.splitlines():
        m = VERT.fullmatch(raw)
        if m:
            idx = int(m.group(6))
            if idx in original_vertices:
                raise ValueError(f"Duplicate vertex {idx}")
            original_vertices[idx] = tuple(float(m.group(i)) for i in (2, 3, 4))
        a = ARC.fullmatch(raw)
        if a and float(a.group(6)) in metal_arcs_by_station:
            metal_arcs_by_station[float(a.group(6))].append(
                tuple(float(a.group(i)) for i in (2, 3, 4))
            )
    if len(original_vertices) != 280 or any(
        len(metal_arcs_by_station[y]) != 8 for y in metal_arcs_by_station
    ):
        raise ValueError("Unexpected source vertex and arc structure")
    for i in range(84, 100):
        p = original_vertices[i]
        p0 = original_vertices[i - 28]
        if abs(p[1] + 39.8) > 1e-8 or abs(p0[1] + 40.0) > 1e-8:
            raise ValueError(f"Original station mismatch for vertex {i}")

    moved_vertices = set()
    moved_arcs = 0
    next_arc = 0
    result = []
    for line in data.splitlines(keepends=True):
        plain = line.rstrip("\r\n")
        ending = line[len(plain):]
        m = VERT.fullmatch(plain)
        if m:
            indent, sx, sy, sz, suffix, num = m.groups()
            idx = int(num)
            x, y, z = map(float, (sx, sy, sz))
            if mode == "inner_y" and idx in INNER:
                if idx in moved_vertices:
                    raise ValueError("Duplicate inner vertex")
                y = -39.8 + value
                # Preserve the exact -39.8 surface and leave all boundary arcs.
                updated = f"{indent}({sx} {y:.6f} {sz}){suffix}"
                moved_vertices.add(idx)
                result.append(updated + ending)
                continue
            if mode == "profile" and idx in OUTER:
                if idx in moved_vertices:
                    raise ValueError("Duplicate transition boundary vertex")
                x0, _, z0 = original_vertices[idx - 28]
                x = x0 + value * (x - x0)
                z = z0 + value * (z - z0)
                updated = f"{indent}({x:.6f} {sy} {z:.6f}){suffix}"
                moved_vertices.add(idx)
                result.append(updated + ending)
                continue
        a = ARC.fullmatch(plain)
        if a and mode == "profile" and float(a.group(6)) == -39.8:
            if next_arc >= 8:
                raise ValueError("Unexpected ninth metal arc at -39.8 mm")
            low = metal_arcs_by_station[-40.0][next_arc]
            x = low[0] + value * (float(a.group(2)) - low[0])
            z = low[2] + value * (float(a.group(4)) - low[2])
            updated = f"{a.group(1)}({x:.6f} {a.group(3)} {z:.6f}){a.group(5)}"
            moved_arcs += 1
            next_arc += 1
            result.append(updated + ending)
            continue
        result.append(line)

    expected_vertices = INNER if mode == "inner_y" else OUTER
    if moved_vertices != expected_vertices:
        raise ValueError(f"Unexpected modified vertex IDs: {sorted(moved_vertices)}")
    if moved_arcs != (8 if mode == "profile" else 0):
        raise ValueError(f"Unexpected changed arc count {moved_arcs}")
    body = "".join(result)
    if len(body.splitlines()) != len(data.splitlines()):
        raise ValueError("Changed line count")
    # Enforce identical blocks, boundaries and zoning; even profile trials
    # preserve exact matching of metal/mold topology and patch names.
    for name in ("blocks", "boundary"):
        pattern = re.compile(
            r"(?ms)^" + re.escape(name) + r"\s*\(\s*\n.*?^\);"
        )
        left = pattern.search(data)
        right = pattern.search(body)
        if left is None or right is None or left.group() != right.group():
            raise ValueError(f"Unauthorized change to {name}")
    with target.open("x", encoding="utf-8") as stream:
        stream.write(body)
    return {
        "status": "STATIC_C3D04_V4_CANDIDATE_NOT_YET_NATIVE_TESTED",
        "mode": mode, "value": value,
        "changed_vertex_ids": sorted(moved_vertices),
        "changed_arc_midpoints": moved_arcs,
        "changed_block_connectivity": False,
        "changed_patch_topology": False,
        "changed_surface_geometry": mode == "profile",
        "section_y_minus39_8_area_mm2_analytic": section_area,
        "section_y_minus39_8_error_percent_vs_STL": section_error_percent,
        "original": str(source), "output": str(target),
        "require_native_checkMesh": True,
        "require_remeasured_contact_area": True,
        "CFD_executed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--mode", required=True, choices=["inner_y", "profile"])
    parser.add_argument("--value", required=True, type=float)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.target, args.mode, args.value), indent=2))


if __name__ == "__main__":
    main()
