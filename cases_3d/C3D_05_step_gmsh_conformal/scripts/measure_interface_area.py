#!/usr/bin/env python3
"""Read-only audit of OpenFOAM Foundation 14 ASCII polyMesh patch areas for the independent STEP/Gmsh route.

This is NOT a mesh generator or a CFD solver.  It reads the existing native
OpenFOAM regional meshes after blockMesh/splitMeshRegions and reports geometric
face areas from vertices and face connectivity using standard-library Python.
No files are changed except the requested JSON report (new destination).
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path

CAD_CONTACT_MM2 = 6352.633693770655
CAD_TOP_MM2 = 1326.8855035725214
NUMBER = r"[-+]?(?:(?:\d+\.?\d*)|(?:\.\d+))(?:[eE][-+]?\d+)?"
LIST_START = re.compile(r"(?m)^\s*(\d+)\s*\n\s*\(\s*\n")
LIST_END = re.compile(r"(?m)^\s*\)\s*$")
POINT_RE = re.compile(r"\(\s*(" + NUMBER + r")\s+(" + NUMBER + r")\s+(" + NUMBER + r")\s*\)")
FACE_RE = re.compile(r"(?m)^\s*(\d+)\s*\(\s*([\d\s]+)\)\s*$")


def payload(path: Path) -> tuple[int, str]:
    text = path.read_text(encoding="utf-8")
    head = LIST_START.search(text)
    if head is None:
        raise ValueError(f"Missing OpenFOAM ASCII list: {path}")
    tail = LIST_END.search(text, head.end())
    if tail is None:
        raise ValueError(f"Unterminated OpenFOAM list: {path}")
    return int(head.group(1)), text[head.end():tail.start()]


def load_points(path: Path) -> list[tuple[float, float, float]]:
    declared, text = payload(path)
    points = [tuple(map(float, m.groups())) for m in POINT_RE.finditer(text)]
    if len(points) != declared:
        raise ValueError(f"Points parse count mismatch {path}: {len(points)} != {declared}")
    return points


def load_faces(path: Path) -> list[list[int]]:
    declared, text = payload(path)
    faces = []
    for m in FACE_RE.finditer(text):
        n = int(m.group(1))
        indices = [int(x) for x in m.group(2).split()]
        if len(indices) != n or n < 3:
            raise ValueError(f"Invalid face with {n} vertices: {path}")
        faces.append(indices)
    if len(faces) != declared:
        raise ValueError(
            f"Face parse count mismatch {path}: {len(faces)} != {declared}; "
            "mesh must be ASCII faceList (not binary or compactFaceList)"
        )
    return faces


def patch_range(path: Path, patch: str) -> tuple[int, int]:
    content = path.read_text(encoding="utf-8")
    # OpenFOAM boundary format: patchName { type ...; nFaces N; startFace S; }
    match = re.search(r"(?m)^\s*" + re.escape(patch) + r"\s*\{([^}]*)\}", content, re.S)
    if not match:
        raise ValueError(f"Patch not found: {patch} in {path}")
    part = match.group(1)
    def field(key: str) -> int:
        m = re.search(r"\b" + key + r"\s+(\d+)\s*;", part)
        if not m:
            raise ValueError(f"Patch missing {key}: {patch}")
        return int(m.group(1))
    return field("startFace"), field("nFaces")


def patch_area(case: Path, region: str, patch: str) -> tuple[float, int]:
    mesh = case / "constant" / region / "polyMesh"
    points = load_points(mesh / "points")
    faces = load_faces(mesh / "faces")
    start, count = patch_range(mesh / "boundary", patch)
    if start < 0 or count < 1 or start + count > len(faces):
        raise ValueError(f"Patch face range out of bounds: {region}/{patch}")
    area = 0.0
    for indices in faces[start:start + count]:
        vertices = [points[i] for i in indices]
        # Area vector for a polygon, robust to ordering and translation.
        sx = sy = sz = 0.0
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            sx += a[1] * b[2] - a[2] * b[1]
            sy += a[2] * b[0] - a[0] * b[2]
            sz += a[0] * b[1] - a[1] * b[0]
        area += 0.5 * math.sqrt(sx * sx + sy * sy + sz * sz)
    return area, count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    case = args.case.resolve()
    if not case.is_dir():
        parser.error(f"Case missing: {case}")
    metal, nmetal = patch_area(case, "metal", "metal_to_mold")
    mold, nmold = patch_area(case, "mold", "mold_to_metal")
    top, ntop = patch_area(case, "metal", "metalTop")
    difference = abs(metal - mold) / max(metal, mold)
    cad = CAD_CONTACT_MM2 * 1e-6
    cadtop = CAD_TOP_MM2 * 1e-6
    contact_error = 100.0 * (metal / cad - 1.0)
    top_error = 100.0 * (top / cadtop - 1.0)
    result = {
        "status": "GEOMETRY_AUDIT_ONLY_NO_CFD",
        "case": str(case),
        "metal_to_mold": {"faces": nmetal, "area_m2": metal, "area_mm2": metal * 1e6},
        "mold_to_metal": {"faces": nmold, "area_m2": mold, "area_mm2": mold * 1e6},
        "metalTop": {"faces": ntop, "area_mm2": top * 1e6},
        "cad_reference": {"contact_mm2": CAD_CONTACT_MM2, "metalTop_mm2": CAD_TOP_MM2},
        "difference_between_coupled_sides_relative": difference,
        "contact_area_error_percent_vs_STL": contact_error,
        "top_area_error_percent_vs_STL": top_error,
        "contact_gate": bool(nmetal == nmold and nmetal > 0
                             and difference <= 0.001
                             and abs(contact_error) <= 3.0
                             and abs(top_error) <= 3.0),
        "method": "OpenFOAM ASCII points/faces/boundary; polygon area-vector magnitude; "
                  "not a full surface Hausdorff/CAD distance audit; number of contact faces is unstructured-mesh dependent",
    }
    # The report must be fresh, not an overwrite of historical evidence.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["contact_gate"]:
        raise SystemExit("REJECTED: contact area or reciprocal face count gate failed")


if __name__ == "__main__":
    main()
