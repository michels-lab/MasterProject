#!/usr/bin/env python3
"""Read-only OpenFOAM 14 topology audit of underdeterminedCells on saved C3D-05.

Loads labelLists (not point coordinates or faces), counts how many boundary and
internal faces touch each native checkMesh-rejected cell and groups by patch.
Read-only, standard-library Python, no Gmsh, no OpenFOAM, no CFD or remeshing.
The diagnostic DOES NOT equate boundary-face count with the exact determinant
value: the native algorithm also uses face-area vectors and coupled status.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re


HEADER = re.compile(r"(?m)^\s*(\d+)\s*\n\s*\(\s*\n")
SINGLE_INT = re.compile(r"(?m)^\s*(\d+)\s*$")
BOUNDARY = re.compile(
    r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\n\s*\{([^}]*)\}", re.S
)


def load_labels(path: Path) -> list[int]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing native ASCII labelList/cellSet {path}")
    text = path.read_text(encoding="utf-8", errors="strict")
    head = HEADER.search(text)
    if head is None:
        raise ValueError(f"No ASCII label list found in {path}")
    end = re.search(r"(?m)^\s*\)\s*;?\s*$", text[head.end():])
    if end is None:
        raise ValueError(f"Unterminated list in {path}")
    data = text[head.end():head.end() + end.start()]
    numbers = [int(m.group(1)) for m in SINGLE_INT.finditer(data)]
    if len(numbers) != int(head.group(1)):
        raise ValueError(
            f"Expected {head.group(1)} labels, found {len(numbers)} in {path}; "
            "check file format and whether mesh was written binary"
        )
    return numbers


def load_patches(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    patches = []
    for match in BOUNDARY.finditer(text):
        name, contents = match.groups()
        def field(key: str) -> str | None:
            v = re.search(r"\b" + re.escape(key) + r"\s+([^;\s]+)\s*;", contents)
            return v.group(1) if v else None
        first, count = field("startFace"), field("nFaces")
        if first is None or count is None:
            continue
        patches.append(
            {
                "name": name,
                "startFace": int(first),
                "nFaces": int(count),
                "type": field("type"),
                "neighbourRegion": field("neighbourRegion"),
            }
        )
    return sorted(patches, key=lambda p: p["startFace"])


def find_bad_set(case: Path, region: str) -> Path:
    # OpenFOAM checkMesh often writes this as a native cellSet under polyMesh/sets.
    # Local selected time / pointsInstance can vary; never guess if ambiguous.
    candidates = list(case.glob(f"constant/{region}/polyMesh/sets/underdeterminedCells"))
    candidates += list(case.glob(f"[0-9]*/{region}/polyMesh/sets/underdeterminedCells"))
    candidates += list(case.glob(f"constant/{region}/polyMesh/underdeterminedCells"))
    candidates = list(dict.fromkeys(p for p in candidates if p.is_file()))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(
            f"No underdeterminedCells set found for {region}; run "
            f"'find {case} -name underdeterminedCells -print' to locate native evidence"
        )
    raise ValueError(f"Ambiguous underdetermined cellSets for {region}: {candidates}")


def audit_region(case: Path, region: str) -> dict:
    mesh = case / "constant" / region / "polyMesh"
    bad_file = find_bad_set(case, region)
    bad_cells = set(load_labels(bad_file))
    if not bad_cells:
        raise ValueError(f"Unexpected empty cell set for {region}")
    owner = load_labels(mesh / "owner")
    neighbor = load_labels(mesh / "neighbour")
    patches = load_patches(mesh / "boundary")
    n_internal = len(neighbor)
    if any(p["startFace"] < n_internal for p in patches):
        raise ValueError("Boundary patch starts before last internal face")
    if patches and max(p["startFace"] + p["nFaces"] for p in patches) != len(owner):
        raise ValueError("Boundary patch coverage does not reach last face")
    cell_counts = {c: {"internal": 0, "boundary": 0, "patches": Counter()} for c in bad_cells}
    for face_index in range(n_internal):
        own = owner[face_index]
        nei = neighbor[face_index]
        if own in cell_counts:
            cell_counts[own]["internal"] += 1
        if nei in cell_counts:
            cell_counts[nei]["internal"] += 1
    for patch in patches:
        for face_index in range(patch["startFace"], patch["startFace"] + patch["nFaces"]):
            if face_index >= len(owner):
                raise ValueError(f"Invalid face range: {patch['name']}")
            own = owner[face_index]
            if own in cell_counts:
                cell_counts[own]["boundary"] += 1
                cell_counts[own]["patches"][patch["name"]] += 1
    hist_boundary = Counter(x["boundary"] for x in cell_counts.values())
    hist_internal = Counter(x["internal"] for x in cell_counts.values())
    by_patch = Counter()
    for x in cell_counts.values():
        for name in x["patches"]:
            by_patch[name] += 1
    missing = [c for c, x in cell_counts.items() if not (x["internal"] or x["boundary"])]
    if missing:
        raise ValueError(f"Cells missing from owner/neighbour lists: {missing[:8]}")
    examples = [
        {
            "cell_index": index,
            "internal_faces": cell_counts[index]["internal"],
            "boundary_faces": cell_counts[index]["boundary"],
            "boundary_patches": dict(cell_counts[index]["patches"]),
        }
        for index in sorted(cell_counts)
        if cell_counts[index]["boundary"] >= 2
    ][:12]
    return {
        "region": region,
        "bad_cell_set_file": str(bad_file),
        "underdetermined_count": len(bad_cells),
        "total_internal_faces": n_internal,
        "total_faces": len(owner),
        "boundary_face_count_distribution": dict(sorted(hist_boundary.items())),
        "internal_face_count_distribution": dict(sorted(hist_internal.items())),
        "cells_touching_each_patch": dict(by_patch),
        "cells_with_two_or_more_boundary_faces": sum(
            n for count, n in hist_boundary.items() if count >= 2
        ),
        "cells_without_boundary_faces": hist_boundary.get(0, 0),
        "example_cells_with_multiple_boundary_faces": examples,
        "notes": (
            "A native 'small determinant' can be caused by insufficient independent "
            "internal-or-coupled face-area directions, even when volumes/skewness "
            "are otherwise acceptable. Patch adjacency alone is not proof."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    case = args.case.expanduser().resolve()
    if not case.is_dir():
        parser.error(f"Missing saved mesh case: {case}")
    print("READ-ONLY: NO MESH CHANGES, NO CFD, NO SOURCE CHANGES")
    for region in ("metal", "mold"):
        try:
            report = audit_region(case, region)
        except (ValueError, OSError) as exc:
            print(json.dumps({"region": region, "error": str(exc)}, indent=2))
            continue
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
