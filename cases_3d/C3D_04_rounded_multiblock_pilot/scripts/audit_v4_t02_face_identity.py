#!/usr/bin/env python3
"""CASE A C3D-04 V4/T02: trace severe native checkMesh VTK faces to parent interfaces.

STRICT read-only. Requires prior native 3-region checkMesh/contact gates.
Maps every severe-face VTK polygon to its exact native polyMesh face geometry,
then maps regional severe faces and the metal_to_mold patch to parent face IDs.
No CFD, remesh, checkMesh, geometry modification or assumption that the 64
extra parent severe faces are on the interface. Verifies this hypothesis.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from audit_v4_t02_nonorth import audit as verify_native, SOURCE_VTK
from audit_v4_t02_vtk_faces import parse_legacy_polydata, locate_y
from measure_interface_area import load_points, load_faces, patch_range

CASE = Path.home() / "OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02"
OUTPUT = Path.home() / "OpenFOAM/C3D04_V4_T02_FACE_IDENTITY_AUDIT_01"

# VTK coordinates may be float32 rather than the double precision polyMesh.
# These are MATCHING tolerances, not acceptable geometry/CFD error limits.
BUCKET_MM = 0.1
VERTEX_TOL_MM = 0.0002
NEIGHBORS = tuple(itertools.product((-1, 0, 1), repeat=3))


def mm(point):
    return tuple(float(a)*1000.0 for a in point)


def centroid(vertices):
    return tuple(sum(p[j] for p in vertices)/len(vertices) for j in range(3))


def bucket(point):
    return tuple(math.floor(p/BUCKET_MM) for p in point)


def vertex_match(observed, target):
    """Unordered vertices bijection, with strict per-vertex Euclidean distance."""
    if len(observed) != len(target):
        return False
    remaining = set(range(len(target)))
    for a in observed:
        candidates = [
            (sum((a[k]-target[j][k])**2 for k in range(3)), j)
            for j in remaining
        ]
        if not candidates:
            return False
        d2, best = min(candidates)
        if d2 > VERTEX_TOL_MM**2:
            return False
        remaining.remove(best)
    return not remaining


class FaceIndex:
    def __init__(self, points, faces):
        self.points = [mm(p) for p in points]
        self.faces = faces
        self.lookup = defaultdict(list)
        self.centres = []
        for i, face in enumerate(faces):
            if len(face) < 3 or any(p < 0 or p >= len(points) for p in face):
                raise ValueError(f"Invalid polyMesh face geometry at index {i}")
            c = centroid([self.points[p] for p in face])
            self.centres.append(c)
            self.lookup[bucket(c)].append(i)

    def match(self, vertices):
        obs = [mm(p) for p in vertices]
        centre = centroid(obs)
        key = bucket(centre)
        candidates = []
        for dx, dy, dz in NEIGHBORS:
            candidates.extend(self.lookup.get(
                (key[0]+dx, key[1]+dy, key[2]+dz), ()
            ))
        found = []
        for i in candidates:
            if len(self.faces[i]) != len(obs):
                continue
            if vertex_match(obs, [self.points[p] for p in self.faces[i]]):
                found.append(i)
        if len(found) == 1:
            return found[0]
        if len(found) == 0:
            raise ValueError(
                f"No polyMesh face matches VTK/patch face centre {centre} mm "
                f"within vertex tolerance {VERTEX_TOL_MM} mm"
            )
        raise ValueError(f"Ambiguous face at {centre} mm: {found[:12]}")


def read_native(case, region):
    path = case/"constant"/"polyMesh" if region == "parent" else case/"constant"/region/"polyMesh"
    if not path.is_dir():
        raise FileNotFoundError(f"Missing native polyMesh {path}")
    points = load_points(path/"points")
    faces = load_faces(path/"faces")
    return FaceIndex(points, faces), path


def map_vtk(index, path, native_count):
    points, polygons = parse_legacy_polydata(path)
    if native_count is None or len(polygons) != native_count:
        raise ValueError(
            f"VTK face count inconsistent with saved checkMesh at {path}: "
            f"VTK={len(polygons)}, log={native_count}"
        )
    native_ids = []
    for polygon in polygons:
        native_ids.append(index.match([points[p] for p in polygon]))
    if len(set(native_ids)) != len(native_ids):
        raise ValueError(f"Repeated native face matched multiple times: {path}")
    return set(native_ids)


def map_native_face_to_parent(source_index, source_face_id, parent_index):
    face = source_index.faces[source_face_id]
    return parent_index.match([
        tuple(x/1000.0 for x in source_index.points[p]) for p in face
    ])


def inspect(case):
    evidence = verify_native(case)
    indexes = {}
    for region in ("parent", "metal", "mold"):
        indexes[region], _ = read_native(case, region)
        expected_total = evidence["regions"][region]["native_total_faces"]
        if expected_total != len(indexes[region].faces):
            raise ValueError(
                f"Native {region} polyMesh faces differ from checkMesh log: "
                f"{len(indexes[region].faces)} != {expected_total}"
            )

    severe_ids = {}
    mapped_parent_ids = {}
    for region in ("parent", "metal", "mold"):
        vtk_path = case / SOURCE_VTK[region]
        if not vtk_path.is_file():
            raise FileNotFoundError(f"Missing preserved native VTK {vtk_path}")
        severe_ids[region] = map_vtk(
            indexes[region], vtk_path,
            evidence["regions"][region]["severely_nonorthogonal_faces_above_70deg"]
        )
        if region == "parent":
            mapped_parent_ids[region] = severe_ids[region]
        else:
            mapped_parent_ids[region] = {
                map_native_face_to_parent(indexes[region], fid, indexes["parent"])
                for fid in severe_ids[region]
            }
            if len(mapped_parent_ids[region]) != len(severe_ids[region]):
                raise ValueError(f"{region} severe faces mapped to duplicate parent face IDs")

    # Classify the exact parent faces corresponding to one side of the
    # native split interface, not just to a nominal surface bounding box.
    metal_dir = case/"constant"/"metal"/"polyMesh"
    first, count = patch_range(metal_dir/"boundary", "metal_to_mold")
    if count != evidence["contact"]["faces_per_contact_side"]:
        raise ValueError("Actual metal patch count changed from saved contact gate")
    interface_ids = {
        map_native_face_to_parent(indexes["metal"], fid, indexes["parent"])
        for fid in range(first, first+count)
    }
    if len(interface_ids) != count:
        raise ValueError("Native interface faces did not map one-to-one to parent")

    # Verify the other side independently. Do not trust a metadata-only
    # mappedWall claim if geometry differs or does not map to the same faces.
    mold_dir = case/"constant"/"mold"/"polyMesh"
    other_start, other_count = patch_range(mold_dir/"boundary", "mold_to_metal")
    if other_count != count:
        raise ValueError("Mold interface patch face count differs")
    mold_interface = {
        map_native_face_to_parent(indexes["mold"], fid, indexes["parent"])
        for fid in range(other_start, other_start+other_count)
    }
    if mold_interface != interface_ids:
        raise ValueError("Metal and mold patch geometries map to different parent face sets")

    parent = mapped_parent_ids["parent"]
    union = mapped_parent_ids["metal"] | mapped_parent_ids["mold"]
    overlap = mapped_parent_ids["metal"] & mapped_parent_ids["mold"]
    parent_only = parent - union
    regional_only = union - parent
    interface_parent_only = parent_only & interface_ids
    non_interface_parent_only = parent_only - interface_ids

    y_hist = Counter(
        locate_y(indexes["parent"].centres[i][1]) for i in parent_only
    )
    parent_only_faces = [
        {
            "parent_face_id": i,
            "centroid_mm": [round(x, 7) for x in indexes["parent"].centres[i]],
            "on_mappedWall_contact_interface": i in interface_ids,
        }
        for i in sorted(parent_only)
    ]
    all_parent_only_are_interface = (
        len(parent_only) == 64
        and not regional_only and not overlap
        and len(interface_parent_only) == 64
    )
    return {
        "case": str(case),
        "status": (
            "FACE_IDENTITY_INTERFACE_HYPOTHESIS_VERIFIED_READONLY"
            if all_parent_only_are_interface else
            "FACE_IDENTITY_MAPPED_BUT_INTERFACE_HYPOTHESIS_NOT_CONFIRMED"
        ),
        "native_parent_regional_and_contact_gates_reverified": True,
        "coordinate_matching_tolerance_mm": VERTEX_TOL_MM,
        "face_centroid_search_bucket_mm": BUCKET_MM,
        "counts": {
            "parent_severe": len(parent),
            "metal_severe": len(severe_ids["metal"]),
            "mold_severe": len(severe_ids["mold"]),
            "regional_severe_parent_face_union": len(union),
            "regional_severe_overlap_on_parent": len(overlap),
            "parent_severe_absent_in_both_regions": len(parent_only),
            "regional_severe_absent_in_parent": len(regional_only),
            "parent_only_faces_on_mappedWall": len(interface_parent_only),
            "parent_only_faces_not_on_mappedWall": len(non_interface_parent_only),
            "interface_parent_faces": len(interface_ids),
        },
        "all_64_unmatched_parent_severe_faces_proven_on_interface": all_parent_only_are_interface,
        "parent_only_face_centroid_Y_bands": dict(sorted(y_hist.items())),
        "parent_only_native_faces": parent_only_faces,
        "limitations": [
            "Geometry vertex-bijection maps native faces; angles come only from saved checkMesh",
            "Interface attribution applies to the exact preserved V4/T02 mesh only",
            "Matching tolerance is an identification parameter, not geometry validation",
            "Even a verified origin of 64 severe faces does NOT prove numerical stability",
            "No CFD, no mesh-independence or discretization-scheme validation",
        ],
        "read_only": True,
    }


def self_test():
    # Native mm points -> metre-encoded VTK-like faces, order invariant.
    pts = [
        (0.,0.,0.), (.01,0.,0.), (.01,.01,0.), (0.,.01,0.),
        (0.,0.,.01), (.01,0.,.01), (.01,.01,.01), (0.,.01,.01)
    ]
    idx = FaceIndex(pts, [(0,1,2,3), (4,5,6,7)])
    f0 = [pts[i] for i in (3,2,1,0)]
    assert idx.match(f0) == 0
    f1 = [pts[i] for i in (7,6,5,4)]
    assert idx.match(f1) == 1
    shifted = list(f0)
    shifted[0] = (shifted[0][0]+.001, shifted[0][1], shifted[0][2])
    try:
        idx.match(shifted)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid face geometry was falsely matched")
    # Region-facing orientation must not affect matching, but face topology
    # cannot collapse distinct original face geometries.
    assert vertex_match(f0, list(reversed(f0)))
    assert not vertex_match(f0, f1)
    assert len({0, 1} - {1}) == 1
    with tempfile.TemporaryDirectory() as temp:
        p = Path(temp)/"test.vtk"
        p.write_text(
            "# vtk DataFile Version 3.0\nT\nASCII\nDATASET POLYDATA\n"
            "POINTS 4 float\n0 0 0 0.01 0 0 0.01 0.01 0 0 0.01 0\n"
            "POLYGONS 1 5\n4 0 1 2 3\n", encoding="ascii"
        )
        assert map_vtk(idx, p, 1) == {0}
        try:
            map_vtk(idx, p, 2)
        except ValueError:
            pass
        else:
            raise AssertionError("VTK / native count mismatch incorrectly accepted")
    print("SELF_TEST_OK: strict parent-native geometry mapping, reversed faces, false matches, VTK count rejection")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", type=Path, default=CASE)
    ap.add_argument("--out", type=Path, default=OUTPUT)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    case = a.case.expanduser().resolve(strict=True)
    out = a.out.expanduser()
    if out.exists() or out.is_symlink():
        ap.error(f"Refusing to overwrite historical face audit: {out}")
    result = inspect(case)
    out.mkdir(parents=True, exist_ok=False)
    path = out/"C3D04_V4_T02_SEVERE_FACE_IDENTITY.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print("C3D04 V4/T02: STRICT read-only face-identity audit")
    for key, value in result["counts"].items():
        print(f"{key}: {value}")
    print("Parent-only face Y bands:", result["parent_only_face_centroid_Y_bands"])
    print("ALL 64 PARENT-ONLY FACES PROVEN ON INTERFACE:",
          result["all_64_unmatched_parent_severe_faces_proven_on_interface"])
    print("STATUS:", result["status"])
    print("Saved new report:", path)
    print("NO CFD. Native quality/contact gates checked from preserved evidence.")


if __name__ == "__main__":
    main()
