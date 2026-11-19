#!/usr/bin/env python3
"""C3D-05 case B: read-only localization of native >70-degree nonOrthoFaces.

Uses only the ASCII faceSet saved by the existing OpenFOAM-14 checkMesh
-writeSets, and the region's preserved owner/neighbour/boundary. No OpenFOAM
executables, no Gmsh, no remeshing, no CFD. Does not alter old evidence.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from audit_underdetermined_topology import load_labels, load_patches

NATIVE_LOG = re.compile(
    r"Number of severely non-orthogonal[^\n]*faces:\s*(\d+)", re.I
)


def find_native_set(case: Path, region: str) -> Path:
    candidates = [
        case / "constant" / region / "polyMesh" / "sets" / "nonOrthoFaces",
        case / "constant" / region / "polyMesh" / "nonOrthoFaces",
    ]
    candidates.extend(
        sorted(case.glob(f"[0-9]*/{region}/polyMesh/sets/nonOrthoFaces"))
    )
    candidates = list(dict.fromkeys(p for p in candidates if p.is_file()))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(
            f"Missing native OpenFOAM checkMesh faceSet 'nonOrthoFaces' "
            f"for {region}; cannot locate severe faces without source set."
        )
    raise ValueError(f"Multiple native faceSet candidates for {region}: {candidates}")


def classify(
    bad_faces: list[int],
    owner: list[int],
    neighbour: list[int],
    patches: list[dict],
) -> dict:
    """Count severe faces and adjacency to metal/arena contact; no geometry guessed."""
    total_faces = len(owner)
    n_internal = len(neighbour)
    face_set = set(bad_faces)
    if len(face_set) != len(bad_faces):
        raise ValueError("nonOrthoFaces set has duplicate face indices")
    if any(f < 0 or f >= total_faces for f in face_set):
        raise ValueError("nonOrthoFaces contains out-of-range face index")
    if n_internal > total_faces:
        raise ValueError("neighbour length larger than owner length")
    # Check that boundary regions cover every non-internal face exactly once.
    by_boundary_face = {}
    patch_names = [p["name"] for p in patches]
    if len(set(patch_names)) != len(patch_names):
        raise ValueError("Duplicate patch name in boundary mesh")
    contact_cells, outer_cells = set(), set()
    for p in patches:
        first, count = p["startFace"], p["nFaces"]
        if first < n_internal or first + count > total_faces:
            raise ValueError(f"Patch {p['name']} has invalid face range")
        for face in range(first, first + count):
            if face in by_boundary_face:
                raise ValueError(f"Overlapping boundary patches at face {face}")
            by_boundary_face[face] = p["name"]
            if p["name"] in ("metal_to_mold", "mold_to_metal"):
                contact_cells.add(owner[face])
            elif p["name"] in ("metalTop", "moldOuterUnclassified"):
                outer_cells.add(owner[face])
    if len(by_boundary_face) != total_faces - n_internal:
        raise ValueError("Boundary patch coverage incomplete")
    n_bad_internal = 0
    n_bad_boundary = 0
    bad_on_patch = Counter()
    touching_contact = 0
    touching_outer = 0
    touching_both = 0
    samples = []
    for face in sorted(face_set):
        cells = {owner[face]}
        if face < n_internal:
            cells.add(neighbour[face])
            n_bad_internal += 1
        else:
            n_bad_boundary += 1
            bad_on_patch[by_boundary_face[face]] += 1
        contact = not cells.isdisjoint(contact_cells)
        outer = not cells.isdisjoint(outer_cells)
        touching_contact += int(contact)
        touching_outer += int(outer)
        touching_both += int(contact and outer)
        if len(samples) < 8:
            samples.append({
                "face_index": face,
                "internal": face < n_internal,
                "boundary_patch": by_boundary_face.get(face),
                "owner": owner[face],
                "neighbour": neighbour[face] if face < n_internal else None,
                "incident_cell_touches_contact": contact,
                "incident_cell_touches_outer": outer,
            })
    return {
        "severe_face_count": len(face_set),
        "severe_internal_faces": n_bad_internal,
        "severe_boundary_faces": n_bad_boundary,
        "severe_boundary_faces_by_patch": dict(sorted(bad_on_patch.items())),
        "severe_faces_incident_to_contact_patch_cells": touching_contact,
        "severe_faces_incident_to_outer_patch_cells": touching_outer,
        "severe_faces_incident_to_both_contact_and_outer_patch_cells": touching_both,
        "contact_wall_adjacent_cells": len(contact_cells),
        "outer_wall_adjacent_cells": len(outer_cells),
        "total_faces": total_faces,
        "n_internal_faces": n_internal,
        "example_native_faces": samples,
        "method_note": (
            "Adjacency means one endpoint cell owns a contact/outer boundary "
            "face. This does NOT measure Euclidean face-to-interface distance "
            "or prove numerical error magnitude."
        ),
    }


def audit_region(case: Path, region: str) -> dict:
    mesh = case / "constant" / region / "polyMesh"
    saved_set = find_native_set(case, region)
    log = case / f"log.checkMesh.{region}"
    if not log.is_file():
        raise FileNotFoundError(f"Native region checkMesh log missing: {log}")
    log_text = log.read_text(encoding="utf-8", errors="replace")
    match = NATIVE_LOG.search(log_text)
    if not match:
        raise ValueError(f"No severe nonorth count found in {log}")
    expected = int(match.group(1))
    bad = load_labels(saved_set)
    if len(bad) != expected:
        raise ValueError(
            f"Native set/log mismatch: {region}: {len(bad)} faceSet "
            f"vs {expected} faces in {log}"
        )
    owner = load_labels(mesh / "owner")
    neighbour = load_labels(mesh / "neighbour")
    patches = load_patches(mesh / "boundary")
    report = classify(bad, owner, neighbour, patches)
    report.update({
        "region": region,
        "face_set": str(saved_set),
        "source": "NATIVE_SAVED_FACESET_AND_POLYMESH_NO_REMESH_NO_CFD",
        "native_checkMesh_count": expected,
        "faceSet_matches_native_checkMesh": True,
    })
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case", type=Path)
    p.add_argument("--out", type=Path, help="Optional NEW JSON, never overwrite.")
    opts = p.parse_args()
    case = opts.case.expanduser().resolve()
    if not case.is_dir():
        p.error(f"No saved case: {case}")
    reports = [audit_region(case, region) for region in ("metal", "mold")]
    total = sum(item["severe_face_count"] for item in reports)
    expected_parent = 1826
    native_parent = case / "log.checkMesh.parent"
    if native_parent.is_file():
        m = NATIVE_LOG.search(native_parent.read_text(encoding="utf-8", errors="replace"))
        if not m:
            raise ValueError("No native parent severe-nonorth count")
        expected_parent = int(m.group(1))
    if total != expected_parent:
        raise ValueError(
            f"Metal+arena severe nonorth faces {total} != "
            f"parent's native checkMesh count {expected_parent}"
        )
    result = {
        "case": str(case), "status": "PRESERVED_NATIVE_NONORTH_TOPOLOGY_AUDIT",
        "CFD": "NOT_RUN", "parent_severe_nonorth_count": expected_parent,
        "sum_region_severe_nonorth_count": total,
        "regional_counts_match_parent": True,
        "regions": {r["region"]: r for r in reports},
    }
    for region, x in result["regions"].items():
        print(
            f"{region.upper()}: severe={x['severe_face_count']} "
            f"internal={x['severe_internal_faces']} "
            f"boundary={x['severe_boundary_faces']} "
            f"contact-adjacent={x['severe_faces_incident_to_contact_patch_cells']} "
            f"outer-adjacent={x['severe_faces_incident_to_outer_patch_cells']}"
        )
        print("  native severe faces by boundary patch:", x["severe_boundary_faces_by_patch"])
    print(
        f"NATIVE_FACESET_AUDIT: PASSED (metal+mold={total} / parent={expected_parent}). "
        "NO REMESH, NO SOLVER."
    )
    if opts.out is not None:
        output = opts.out.expanduser().resolve()
        if output == case / "CONTACT_AREA_REPORT.json":
            raise ValueError("Refusing to modify original contact evidence")
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
        print(f"New diagnostic JSON (exclusive write): {output}")


if __name__ == "__main__":
    main()
