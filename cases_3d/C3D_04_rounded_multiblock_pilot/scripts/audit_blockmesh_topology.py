#!/usr/bin/env python3
"""Static topology contract for C3D-04's native OpenFOAM blockMeshDict.

Does NOT generate a mesh, execute OpenFOAM, change CAD, or run CFD.
Checks block/vertex/edge declarations, matching subdivisions and complete
explicit ownership of every exterior block face. Native checkMesh remains mandatory.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

FACE_SPECS = (
    ((0, 1, 2, 3), (0, 1)),
    ((4, 5, 6, 7), (0, 1)),
    ((0, 1, 5, 4), (0, 2)),
    ((1, 2, 6, 5), (1, 2)),
    ((2, 3, 7, 6), (0, 2)),
    ((3, 0, 4, 7), (1, 2)),
)
EDGE_SPECS = (
    (0, 1, 0), (1, 2, 1), (2, 3, 0), (3, 0, 1),
    (4, 5, 0), (5, 6, 1), (6, 7, 0), (7, 4, 1),
    (0, 4, 2), (1, 5, 2), (2, 6, 2), (3, 7, 2),
)
NUM = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def section(source: str, name: str) -> str:
    match = re.search(
        r"(?ms)^" + re.escape(name) + r"\s*\(\s*\n(.*?)^\);",
        source,
    )
    if match is None:
        raise ValueError(f"Missing or unterminated section: {name}")
    return match.group(1)


def canonical(indices: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted(indices))


def audit(path: Path) -> dict:
    source = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    source = re.sub(r"//[^\n]*", "", source)
    vertices = [
        tuple(float(x) for x in found)
        for found in re.findall(
            r"(?m)^\s*\(\s*(" + NUM + r")\s+(" + NUM + r")\s+(" + NUM + r")\s*\)\s*$",
            section(source, "vertices"),
        )
    ]
    blocks = []
    for match in re.finditer(
        r"(?m)^\s*hex\s+\(([\d\s]+)\)\s+(metal|mold)\s+"
        r"\(([\d\s]+)\)\s+simpleGrading\s+\([^)]*\)\s*$",
        section(source, "blocks"),
    ):
        corners = tuple(map(int, match.group(1).split()))
        divisions = tuple(map(int, match.group(3).split()))
        if len(corners) != 8 or len(divisions) != 3:
            raise ValueError("Incorrect hex connectivity or subdivision count")
        if any(v >= len(vertices) or v < 0 for v in corners):
            raise ValueError("Hex vertex outside declared vertex list")
        if len(set(corners)) != 8 or any(v <= 0 for v in divisions):
            raise ValueError("Degenerate hex connectivity or nonpositive division")
        blocks.append((corners, match.group(2), divisions))
    arcs = [
        (int(m.group(1)), int(m.group(2)), tuple(map(float, m.group(3).split())))
        for m in re.finditer(
            r"(?m)^\s*arc\s+(\d+)\s+(\d+)\s+\(([^)]+)\)\s*$",
            section(source, "edges"),
        )
    ]

    # Every mesh edge must have the same number of subdivisions in all blocks.
    edges: dict[tuple[int, ...], int] = {}
    faces: dict[tuple[int, ...], list[tuple[str, int]]] = {}
    regions = Counter()
    cells = Counter()
    for corners, region, n in blocks:
        regions[region] += 1
        cells[region] += n[0] * n[1] * n[2]
        for a, b, axis in EDGE_SPECS:
            key = canonical((corners[a], corners[b]))
            if key in edges and edges[key] != n[axis]:
                raise ValueError(f"Inconsistent subdivision on shared edge {key}")
            edges[key] = n[axis]
        for indices, axes in FACE_SPECS:
            key = canonical(tuple(corners[i] for i in indices))
            faces.setdefault(key, []).append((region, n[axes[0]] * n[axes[1]]))
    if any(len(owners) > 2 for owners in faces.values()):
        raise ValueError("Non-manifold block face shared by >2 blocks")
    for key, owners in faces.items():
        if len(owners) == 2 and owners[0][1] != owners[1][1]:
            raise ValueError(f"Different face subdivisions across blocks: {key}")
    for a, b, midpoint in arcs:
        key = canonical((a, b))
        if key not in edges:
            raise ValueError(f"Arc not present on any hex edge: {key}")
        if len(midpoint) != 3:
            raise ValueError(f"Arc midpoint does not have XYZ: {key}")
        if abs(vertices[a][1] - vertices[b][1]) > 1e-7:
            raise ValueError(f"Declared arc has different endpoint Y: {key}")
        if abs(midpoint[1] - vertices[a][1]) > 1e-7:
            raise ValueError(f"Arc midpoint not in intended horizontal plane: {key}")
    if len({canonical((a, b)) for a, b, _ in arcs}) != len(arcs):
        raise ValueError("Duplicate arc on the same edge")

    # Every exposed block face must appear once in the explicit boundary list.
    boundary = section(source, "boundary")
    declared = Counter()
    patches = Counter()
    patch_expr = re.compile(
        r"(?ms)^[ \t]{4}([A-Za-z]\w*)\s*\n[ \t]{4}\{\s*\n"
        r"(.*?)[ \t]{4}\}",
    )
    for patch in patch_expr.finditer(boundary):
        name, body = patch.groups()
        face_match = re.search(r"(?ms)^[ \t]*faces\s*\n[ \t]*\(\s*\n(.*?)^[ \t]*\);", body)
        if face_match is None:
            raise ValueError(f"Patch has no parseable faces list: {name}")
        for line in face_match.group(1).splitlines():
            line = line.strip()
            if not line:
                continue
            face = re.fullmatch(r"\(\s*([\d\s]+)\s*\)", line)
            if not face:
                raise ValueError(f"Unrecognized boundary face in {name}: {line}")
            indices = tuple(map(int, face.group(1).split()))
            if len(indices) != 4:
                raise ValueError(f"Expected quadrilateral boundary face: {name}")
            declared[canonical(indices)] += 1
            patches[name] += 1
    exposed = {key for key, owners in faces.items() if len(owners) == 1}
    if any(declared[key] != 1 for key in exposed):
        raise ValueError("A block exterior face is missing or duplicated in boundary")
    if set(declared) != exposed:
        raise ValueError("Boundary lists include faces that are not exterior block faces")
    interface_faces = sum(
        owners[0][1]
        for owners in faces.values()
        if len(owners) == 2 and owners[0][0] != owners[1][0]
    )
    result = {
        "status": "STATIC_TOPOLOGY_ONLY_NATIVE_CHECKMESH_REQUIRED",
        "vertices": len(vertices), "blocks": len(blocks),
        "blocks_by_region": dict(regions),
        "cells_by_region_expected": dict(cells),
        "arcs": len(arcs), "unique_edges": len(edges),
        "unique_faces": len(faces),
        "exterior_faces": len(exposed),
        "exterior_patches": dict(patches),
        "interface_faces_per_side_expected": interface_faces,
    }
    expected = {
        "vertices": 280, "blocks": 180, "arcs": 144,
        "interface_faces_per_side_expected": 2496,
        "exterior_faces": 162,
    }
    if any(result[key] != value for key, value in expected.items()):
        raise ValueError(f"Unexpected structural contract: {result}")
    if regions != Counter({"metal": 63, "mold": 117}):
        raise ValueError(f"Unexpected material blocks: {dict(regions)}")
    if cells != Counter({"metal": 8960, "mold": 12352}):
        raise ValueError(f"Unexpected cell totals: {dict(cells)}")
    if patches.get("unexpectedFaces", 0):
        raise ValueError("Unexpected faces were explicitly assigned")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dict_path", type=Path, help="C3D-04 system/blockMeshDict"
    )
    args = parser.parse_args()
    try:
        report = audit(args.dict_path)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"REJECTED: {exc}\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
