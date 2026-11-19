#!/usr/bin/env python3
"""Read-only sampled bidirectional STL / native OpenFOAM boundary distance audit.

CASE A / C3D-04 only. This DOES NOT report a rigorous Hausdorff distance.
Distances are between deterministic *sampled points* on triangulated surfaces
and the nearest *continuous triangle* of the opposite surface. Reports the
maximum, p95 and p99 sampled residual for each direction and each material.

Standard-library Python; neither alters a mesh nor invokes CFD/OpenFOAM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
from collections import defaultdict
from pathlib import Path

from measure_interface_area import load_points, load_faces, patch_range

STL_SHA = {
    "metal": "f8c0fb90f9b5650261d39f1faa2430b3fc7fce462c0d44e460afb5a37b4ddccf",
    "mold": "ac52991eb254c1bcc65eaf546a25f663343e006e89aeff3ac26aa8e9a1d95a32",
}
STL_NAME = {"metal": "metal_v2.stl", "mold": "mold_v2.stl"}
PATCHES = {
    "metal": ("metalTop", "metal_to_mold"),
    "mold": (
        "moldTop", "moldExterior", "moldBottom", "moldRecessWall",
        "moldRecessRoof", "mold_to_metal"
    ),
}
Y_STATIONS_M = (-.0655, -.056, -.040, -.0398, -.0395, -.039, -.0385, -.038, -.020, 0.)
Point = tuple[float, float, float]
Triangle = tuple[Point, Point, Point]


def dot(a: Point, b: Point) -> float:
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]


def sub(a: Point, b: Point) -> Point:
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def sq(a: Point) -> float:
    return dot(a, a)


def dist_sq(a: Point, b: Point) -> float:
    return sq(sub(a, b))


def nearest_triangle_distance_sq(p: Point, t: Triangle) -> float:
    # Christer Ericson's triangle Voronoi-region closest-point formula.
    a, b, c = t
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        return sq(ap)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3:
        return sq(bp)
    vc = d1*d4 - d3*d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        v = d1 / (d1-d3)
        return dist_sq(p, (a[0]+v*ab[0], a[1]+v*ab[1], a[2]+v*ab[2]))
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6:
        return sq(cp)
    vb = d5*d2 - d1*d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        w = d2 / (d2-d6)
        return dist_sq(p, (a[0]+w*ac[0], a[1]+w*ac[1], a[2]+w*ac[2]))
    va = d3*d6 - d5*d4
    if va <= 0 and d4-d3 >= 0 and d5-d6 >= 0:
        bc = sub(c, b)
        w = (d4-d3) / ((d4-d3)+(d5-d6))
        return dist_sq(p, (b[0]+w*bc[0], b[1]+w*bc[1], b[2]+w*bc[2]))
    denom = va + vb + vc
    if abs(denom) < 1.e-28:
        return min(dist_sq(p, a), dist_sq(p, b), dist_sq(p, c))
    v = vb / denom
    w = vc / denom
    return dist_sq(p, (
        a[0] + ab[0]*v + ac[0]*w,
        a[1] + ab[1]*v + ac[1]*w,
        a[2] + ab[2]*v + ac[2]*w
    ))


def triangle_area(t: Triangle) -> float:
    a, b, c = t
    u, v = sub(b, a), sub(c, a)
    n = (
        u[1]*v[2]-u[2]*v[1],
        u[2]*v[0]-u[0]*v[2],
        u[0]*v[1]-u[1]*v[0],
    )
    return .5*math.sqrt(sq(n))


def from_stl(path: Path) -> list[Triangle]:
    # Approved reference STLs are binary, checked against versioned SHA256.
    blob = path.read_bytes()
    if len(blob) < 84:
        raise ValueError("STL truncated")
    n = struct.unpack_from("<I", blob, 80)[0]
    if n <= 0 or len(blob) != 84 + 50*n:
        raise ValueError("Expected a complete binary STL")
    result = []
    for i in range(n):
        # Skip the normal vector; read three XYZ vertices.
        data = struct.unpack_from("<12f", blob, 84+50*i)
        tri = tuple(tuple(float(x) for x in data[j:j+3]) for j in (3, 6, 9))
        if any(not math.isfinite(x) for p in tri for x in p):
            raise ValueError(f"Nonfinite STL coordinates at facet {i}")
        if triangle_area(tri) > 1.e-16:
            result.append(tri)
    if not result:
        raise ValueError("No nondegenerate STL triangles")
    return result


def from_openfoam(case: Path, region: str) -> list[Triangle]:
    poly = case/"constant"/region/"polyMesh"
    points, faces = load_points(poly/"points"), load_faces(poly/"faces")
    triangles = []
    for patch in PATCHES[region]:
        start, n = patch_range(poly/"boundary", patch)
        if n < 1 or start < 0 or start+n > len(faces):
            raise ValueError(f"Invalid boundary patch range {region}/{patch}")
        for ids in faces[start:start+n]:
            if len(ids) < 3 or any(i >= len(points) or i < 0 for i in ids):
                raise ValueError(f"Invalid face vertices in {region}/{patch}")
            polygon = [points[i] for i in ids]
            # Native OpenFOAM boundary polygon; fan triangles provide a
            # piecewise-planar approximation to potentially warped quads.
            for j in range(1, len(polygon)-1):
                t = (polygon[0], polygon[j], polygon[j+1])
                if triangle_area(t) > 1.e-20:
                    triangles.append(t)
    if not triangles:
        raise ValueError(f"Empty surface: {region}")
    return triangles


def extrema(tris: list[Triangle]):
    lo = [float("inf")]*3
    hi = [float("-inf")]*3
    for t in tris:
        for p in t:
            for axis in range(3):
                lo[axis] = min(lo[axis], p[axis])
                hi[axis] = max(hi[axis], p[axis])
    return lo, hi


def scale_stl(tris: list[Triangle], target: list[Triangle]):
    lo, hi = extrema(tris)
    tl, th = extrema(target)
    ext = [hi[i]-lo[i] for i in range(3)]
    tx = [th[i]-tl[i] for i in range(3)]
    choices = (1.0, .001, 1000.0)
    scale = min(
        choices, key=lambda s: sum(abs(s*ext[i]-tx[i]) / max(tx[i], 1e-10) for i in range(3))
    )
    dimension_error = max(abs(scale*ext[i]-tx[i])/max(tx[i], 1e-10) for i in range(3))
    if dimension_error > .20:
        raise ValueError("CAD/mesh bounding dimensions differ by >20%; refusing unit inference")
    scaled = [
        tuple(tuple(x*scale for x in p) for p in t)
        for t in tris
    ]
    sl, sh = extrema(scaled)
    center_gap = math.sqrt(sum(
        ((sl[i]+sh[i])*.5 - (tl[i]+th[i])*.5)**2 for i in range(3)
    ))
    if center_gap > .01:
        raise ValueError("CAD/mesh bounding centers differ by more than 10 mm")
    return scaled, scale, dimension_error


def box_of(tri: Triangle):
    return (
        (min(x[0] for x in tri), min(x[1] for x in tri), min(x[2] for x in tri)),
        (max(x[0] for x in tri), max(x[1] for x in tri), max(x[2] for x in tri)),
    )


def merge_boxes(boxes):
    return (
        tuple(min(b[0][d] for b in boxes) for d in range(3)),
        tuple(max(b[1][d] for b in boxes) for d in range(3)),
    )


def box_distance_sq(p: Point, box) -> float:
    return sum(
        max(box[0][i]-p[i], 0., p[i]-box[1][i])**2 for i in range(3)
    )


class BVH:
    def __init__(self, triangles: list[Triangle]):
        if not triangles:
            raise ValueError("Empty target surface")
        self.tris = triangles
        self.boxes = [box_of(t) for t in triangles]
        self.centroids = [
            tuple(sum(p[k] for p in t)/3 for k in range(3)) for t in triangles
        ]
        self.tree = self.build(list(range(len(triangles))))

    def build(self, ids):
        box = merge_boxes([self.boxes[i] for i in ids])
        if len(ids) <= 12:
            return (box, None, None, ids)
        axis = max(range(3), key=lambda i: box[1][i]-box[0][i])
        ids.sort(key=lambda j: self.centroids[j][axis])
        half = len(ids)//2
        return (box, self.build(ids[:half]), self.build(ids[half:]), None)

    def closest_sq(self, p: Point) -> float:
        best = float("inf")
        pending = [self.tree]
        while pending:
            box, left, right, ids = pending.pop()
            if box_distance_sq(p, box) >= best:
                continue
            if ids is not None:
                for i in ids:
                    if box_distance_sq(p, self.boxes[i]) < best:
                        best = min(best, nearest_triangle_distance_sq(p, self.tris[i]))
            else:
                # Visit the nearer spatial half first, prune farther half.
                assert left is not None and right is not None
                dl, dr = box_distance_sq(p, left[0]), box_distance_sq(p, right[0])
                if dl < dr:
                    pending.extend((right, left))
                else:
                    pending.extend((left, right))
        return best


def candidate_samples(tris: list[Triangle], cap: int) -> list[Point]:
    # Vertex + centroid samples; per-Y bucketing preserves the very thin
    # -40 to -39.5 mm basal transition even if it is a small surface fraction.
    buckets = defaultdict(set)
    for tri in tris:
        centroid = tuple(sum(p[j] for p in tri)/3 for j in range(3))
        for p in (*tri, centroid):
            axis_y = p[1]
            bin_id = next(
                (j for j in range(len(Y_STATIONS_M)-1)
                 if Y_STATIONS_M[j] <= axis_y < Y_STATIONS_M[j+1]),
                len(Y_STATIONS_M)-2
            )
            buckets[bin_id].add(p)
    total_bins = len(buckets)
    each = max(1, cap//total_bins)
    selected = []
    for j in sorted(buckets):
        # Sorting makes sample selection deterministic across Python hash seeds.
        points = sorted(buckets[j])
        if len(points) <= each:
            selected.extend(points)
        else:
            selected.extend(points[min(len(points)-1, int((k+.5)*len(points)/each))]
                            for k in range(each))
    return selected


def directed_samples(source: list[Triangle], target: BVH, cap: int):
    points = candidate_samples(source, cap)
    distances = sorted(math.sqrt(target.closest_sq(p))*1000 for p in points)
    def percentile(q):
        if not distances:
            return None
        return distances[min(len(distances)-1, math.ceil(q*len(distances))-1)]
    return {
        "samples": len(points),
        "max_mm_sampled": max(distances),
        "p95_mm_sampled": percentile(.95),
        "p99_mm_sampled": percentile(.99),
        "rms_mm_sampled": math.sqrt(sum(x*x for x in distances)/len(distances)),
        "percent_above_0_5mm_sampled": 100*sum(x > .5 for x in distances)/len(distances),
    }


def audit(case: Path, stl_root: Path, cap: int):
    status = case/"NATIVE_BUILD_STATUS.txt"
    if not status.is_file() or "MESH_TOPOLOGY_AND_CONTACT_AREA_PRELIMINARILY_ACCEPTED" not in status.read_text():
        raise ValueError("Case has not passed native mesh AND contact-area gates")
    result = {
        "status": "SAMPLED_BIDIRECTIONAL_SURFACE_DISTANCE_ONLY_NOT_HAUSDORFF",
        "case": str(case),
        "method": "deterministic stratified surface vertices/triangle centroids -> nearest continuous triangle",
        "sample_limit_per_region_and_direction": cap,
        "limitations": [
            "Sampled distances are NOT upper bounds of the true Hausdorff distance",
            "Fan-triangulating nonplanar native quad faces approximates their surface",
            "Approximate STL reference itself may differ from exact SolidWorks STEP",
            "No threshold or native CFD acceptance is inferred from this report",
        ],
        "regions": {},
    }
    for region in ("metal", "mold"):
        stl = stl_root/STL_NAME[region]
        digest = hashlib.sha256(stl.read_bytes()).hexdigest()
        if digest != STL_SHA[region]:
            raise ValueError(f"Reference STL hash mismatch: {region}")
        native = from_openfoam(case, region)
        cad, scale, dimension_error = scale_stl(from_stl(stl), native)
        print(f"Auditing {region}: {len(native)} native triangles, {len(cad)} CAD triangles", flush=True)
        region_result = {
            "stl_sha256": digest,
            "stl_scale_to_meters": scale,
            "cad_native_bbox_relative_max_error": dimension_error,
            "native_triangle_count": len(native),
            "cad_triangle_count": len(cad),
            "native_to_STL": directed_samples(native, BVH(cad), cap),
            "STL_to_native": directed_samples(cad, BVH(native), cap),
        }
        result["regions"][region] = region_result
    return result


def self_test():
    tri = ((0.,0.,0.), (1.,0.,0.), (0.,1.,0.))
    target = BVH([tri])
    assert nearest_triangle_distance_sq((.2,.3,0.), tri) < 1e-22
    assert abs(target.closest_sq((.2,.3,.1))-.01) < 1e-12
    assert abs(target.closest_sq((2.,0.,0.))-1.) < 1e-12
    shifted = tuple((p[0],p[1],p[2]+.002) for p in tri)
    assert abs(BVH([shifted]).closest_sq((.2,.3,0.))-.002**2) < 1e-12
    a = directed_samples([tri], BVH([tri]), 100)
    assert a["max_mm_sampled"] < 1e-8
    print("SELF_TEST_OK: triangle nearest-point, BVH pruning, sampled matching surfaces")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=Path.home()/"OpenFOAM/C3D04_V4_TRANSITION_REPAIR_01/T02")
    parser.add_argument("--stl-root", type=Path, default=Path(__file__).resolve().parents[1]/"C3D_02_metal_sand_clean"/"constant"/"geometry")
    parser.add_argument("--output", type=Path, default=Path.home()/"OpenFOAM/C3D04_V4_T02_CAD_SURFACE_AUDIT_01")
    parser.add_argument("--max-samples", type=int, default=5000)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not 100 <= args.max_samples <= 15000:
        parser.error("--max-samples must be in [100,15000]")
    target = args.output.expanduser()
    if target.exists() or target.is_symlink():
        parser.error(f"Preserving existing audit directory: {target}")
    case = args.case.expanduser().resolve(strict=True)
    stl_root = args.stl_root.expanduser().resolve(strict=True)
    report = audit(case, stl_root, args.max_samples)
    target.mkdir(parents=True, exist_ok=False)
    out = target/"SAMPLED_CAD_SURFACE_REPORT.json"
    with out.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"SAMPLED SURFACE AUDIT SAVED: {out}")
    print("NOT rigorous Hausdorff; further visual / exact CAD surface checks remain.")


if __name__ == "__main__":
    main()
