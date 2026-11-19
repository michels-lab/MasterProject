#!/usr/bin/env python3
"""C3D-05 Caso B: distance in CELL-ADJACENCY HOPS of severe nonOrth faces.

Read-only on accepted HEX8 preserved native OpenFOAM mesh. Uses faceSet,
owner, neighbour, and boundary from OpenFOAM 14. Reports shortest topological
cell hops to contact and outer walls for both cells incident on each severe
internal face. NOT Euclidean distance, not conduction error, not CFD.
No Gmsh, no mesh editing, no checkMesh calls, no solver.
"""
from __future__ import annotations

import argparse
from array import array
from collections import Counter, deque
import json
from pathlib import Path

from audit_underdetermined_topology import load_labels, load_patches
from audit_nonorthogonal_faces import find_native_set, NATIVE_LOG
from audit_nonorthogonal_faces import classify


def build_graph(owner: list[int], neighbour: list[int]):
    """Compressed sparse row, O(nCells+nInternalFaces) memory."""
    n_internal = len(neighbour)
    if len(owner) <= n_internal:
        raise ValueError("owner must include both internal and boundary faces")
    if min(owner, default=-1) < 0 or min(neighbour, default=-1) < 0:
        raise ValueError("owner/neighbour contains negative cell label")
    cells = max(max(owner), max(neighbour, default=0)) + 1
    if cells > 5_000_000:
        raise ValueError("Resource gate: implausible cell count > 5 million")
    degree = array("I", [0]) * cells
    for a, b in zip(owner, neighbour):
        if a == b:
            raise ValueError("Internal face owner==neighbour")
        degree[a] += 1
        degree[b] += 1
    offsets = array("I", [0]) * (cells + 1)
    for i in range(cells):
        offsets[i + 1] = offsets[i] + degree[i]
    adjacency = array("I", [0]) * offsets[-1]
    positions = array("I", offsets[:-1])
    for a, b in zip(owner, neighbour):
        adjacency[positions[a]] = b
        adjacency[positions[b]] = a
        positions[a] += 1
        positions[b] += 1
    return offsets, adjacency


def bfs_hops(offsets: array, adjacency: array, roots: set[int]) -> array:
    n = len(offsets) - 1
    if not roots or any(x < 0 or x >= n for x in roots):
        raise ValueError("Missing/invalid contact or outer boundary source cells")
    dist = array("i", [-1]) * n
    queue = deque(sorted(roots))
    for root in roots:
        dist[root] = 0
    while queue:
        u = queue.popleft()
        for j in range(offsets[u], offsets[u + 1]):
            v = adjacency[j]
            if dist[v] == -1:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def boundary_roots(owner: list[int], neighbour: list[int], patches: list[dict]):
    n_internal = len(neighbour)
    contact, outer = set(), set()
    expected = {p["name"] for p in patches}
    if not expected.intersection({"metal_to_mold", "mold_to_metal"}):
        raise ValueError("Interface mappedWall patch not found")
    for patch in patches:
        start, count = patch["startFace"], patch["nFaces"]
        if start < n_internal or start + count > len(owner):
            raise ValueError(f"Invalid patch face range for {patch['name']}")
        if patch["name"] in ("metal_to_mold", "mold_to_metal"):
            contact.update(owner[start:start + count])
        elif patch["name"] in ("metalTop", "moldOuterUnclassified"):
            outer.update(owner[start:start + count])
    if not contact or not outer:
        raise ValueError("Missing contact or outer wall-adjacent cells")
    return contact, outer


def percentile(values: list[int], pct: float) -> int:
    if not values:
        raise ValueError("No severe face distances")
    vals = sorted(values)
    return vals[min(len(vals) - 1, int((len(vals) - 1) * pct))]


def summarise_distances(values: list[int]) -> dict:
    counts = Counter(values)
    return {
        "min": min(values), "median": percentile(values, 0.5),
        "p90": percentile(values, 0.9), "max": max(values),
        "by_hops": {str(k): v for k, v in sorted(counts.items())},
        "within_1_hop": sum(v for k, v in counts.items() if k <= 1),
        "within_2_hops": sum(v for k, v in counts.items() if k <= 2),
        "within_5_hops": sum(v for k, v in counts.items() if k <= 5),
    }


def compute_face_hops(
    severe_faces: list[int], owner: list[int], neighbour: list[int], patches: list[dict]
) -> dict:
    n_internal = len(neighbour)
    # The 2026-11-19 audit found 100% severe faces internal, verify again
    # rather than silently discarding different topology.
    if len(set(severe_faces)) != len(severe_faces):
        raise ValueError("Duplicate severe face index")
    if not severe_faces or any(f < 0 or f >= n_internal for f in severe_faces):
        raise ValueError("Expected only VALID internal nonOrthoFaces for this baseline")
    roots_contact, roots_outer = boundary_roots(owner, neighbour, patches)
    offsets, adjacency = build_graph(owner, neighbour)
    dist_contact = bfs_hops(offsets, adjacency, roots_contact)
    dist_outer = bfs_hops(offsets, adjacency, roots_outer)
    to_contact, to_outer, to_any = [], [], []
    for face in severe_faces:
        a, b = owner[face], neighbour[face]
        c = min(dist_contact[a], dist_contact[b])
        o = min(dist_outer[a], dist_outer[b])
        if c < 0 or o < 0:
            raise ValueError("Disconnected graph: source-to-severe-face distance unknown")
        to_contact.append(c)
        to_outer.append(o)
        to_any.append(min(c, o))
    return {
        "n_cells": len(offsets) - 1,
        "n_internal_faces": n_internal,
        "n_contact_wall_adjacent_cells": len(roots_contact),
        "n_outer_wall_adjacent_cells": len(roots_outer),
        "severe_face_count": len(severe_faces),
        "distance_in_cell_hops_to_contact": summarise_distances(to_contact),
        "distance_in_cell_hops_to_outer": summarise_distances(to_outer),
        "distance_in_cell_hops_to_nearest_wall": summarise_distances(to_any),
        "direct_contact_adjacency_zero": all(x > 0 for x in to_contact),
        "direct_outer_adjacency_zero": all(x > 0 for x in to_outer),
    }


def audit_one(case: Path, region: str) -> dict:
    import re
    mesh = case / "constant" / region / "polyMesh"
    log = case / f"log.checkMesh.{region}"
    if not log.is_file():
        raise FileNotFoundError(f"Missing native log: {log}")
    m = NATIVE_LOG.search(log.read_text(encoding="utf-8", errors="replace"))
    if not m:
        raise ValueError(f"No native severe-nonorth count in {log}")
    expected = int(m.group(1))
    severe_faces = load_labels(find_native_set(case, region))
    if len(severe_faces) != expected:
        raise ValueError(f"{region}: native faceSet count mismatches checkMesh log")
    owner, neighbour = load_labels(mesh / "owner"), load_labels(mesh / "neighbour")
    patches = load_patches(mesh / "boundary")
    initial = classify(severe_faces, owner, neighbour, patches)
    if initial["severe_boundary_faces"] or initial["severe_faces_incident_to_contact_patch_cells"] or initial["severe_faces_incident_to_outer_patch_cells"]:
        raise ValueError(
            f"{region}: saved topology differs from accepted prior zero-boundary "
            "nonOrthoFaces; preserve evidence and investigate."
        )
    summary = compute_face_hops(severe_faces, owner, neighbour, patches)
    summary["region"] = region
    summary["native_faceSet_matches_checkMesh"] = True
    summary["source"] = "NATIVE_POLYMESH_AND_CHECKMESH_FACESETS_ONLY"
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("case", type=Path)
    ap.add_argument("--out", type=Path, help="New JSON only, exclusive-create, never overwrite.")
    args = ap.parse_args()
    case = args.case.expanduser().resolve()
    results = {region: audit_one(case, region) for region in ("metal", "mold")}
    total = sum(results[region]["severe_face_count"] for region in results)
    parent_log = case / "log.checkMesh.parent"
    if not parent_log.is_file():
        raise FileNotFoundError("Missing native parent checkMesh")
    m = NATIVE_LOG.search(parent_log.read_text(encoding="utf-8", errors="replace"))
    if not m or total != int(m.group(1)):
        raise ValueError("Regional severe count does not match native parent")
    print("C3D-05 CASE B — NATIVE SEVERE NONORTH CELL-HOP DISTANCES; NO CFD")
    for region, result in results.items():
        contact = result["distance_in_cell_hops_to_contact"]
        outer = result["distance_in_cell_hops_to_outer"]
        nearest = result["distance_in_cell_hops_to_nearest_wall"]
        print(
            f"{region.upper()}: severe={result['severe_face_count']} "
            f"contact hops min/median/p90/max="
            f"{contact['min']}/{contact['median']}/{contact['p90']}/{contact['max']}; "
            f"outer hops min/median/p90/max="
            f"{outer['min']}/{outer['median']}/{outer['p90']}/{outer['max']}; "
            f"within 2 hops of ANY wall={nearest['within_2_hops']}"
        )
        print("  contact hop histogram:", contact["by_hops"])
        print("  outer hop histogram:", outer["by_hops"])
    result = {
        "status": "NATIVE_NONORTH_FACE_CELL_HOP_AUDIT",
        "case": str(case), "total_severe_faces": total,
        "cfD": "NOT_RUN", "mesh_modified": False,
        "method_note": (
            "Topological shortest path via INTERNAL cell faces (graph hops). "
            "It does not measure physical distance in mm, heat-flux error, "
            "solver stability or grid independence."
        ), "regions": results,
    }
    if args.out:
        out = args.out.expanduser().resolve()
        if out.parent != case:
            raise ValueError("Report output must remain in preserved case folder")
        with out.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
        print(f"NEW read-only evidence report: {out}")
    print("PASS: preserved nonOrthoFaces counts and cell-hop distances, no remesh or solver.")


if __name__ == "__main__":
    main()
