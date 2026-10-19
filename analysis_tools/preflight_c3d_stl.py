#!/usr/bin/env python3
"""Read-only, stdlib-only inspection of preliminary C3D metal/mold binary STL.

This is a geometry sanity gate, NOT OpenFOAM checkMesh or CHT verification.
Validation requires both surfaces and a manifest with physical dimensions.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import struct

EPS_VERTEX = 1e-7  # 0.1 micron; only for coincident STL triangle vertices


@dataclass
class Surface:
    triangles: list[tuple[tuple[float, float, float], ...]]
    bounds: list[list[float]]
    volume_m3: float
    edge_count_nonmanifold: int
    edge_count_same_orientation: int
    digest: str


def vec(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def edge_key(p):
    return tuple(round(x/EPS_VERTEX) for x in p)


def inspect_binary_stl(path: Path, coordinate_scale_to_m: float = 1.0) -> Surface:
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path}: STL header truncated")
    n, = struct.unpack_from('<I', data, 80)
    if n <= 0 or len(data) != 84 + 50*n:
        raise ValueError(f"{path}: expected binary STL 84+50*n bytes, got {len(data)}")
    triangles = []
    edges = Counter()
    direction = Counter()
    volterms = []
    lower = [float('inf')]*3
    upper = [float('-inf')]*3
    for i in range(n):
        values = struct.unpack_from('<12fH', data, 84 + 50*i)
        verts = tuple(tuple(float(x)*coordinate_scale_to_m for x in values[j:j+3]) for j in (3, 6, 9))
        if any(not math.isfinite(x) for v in verts for x in v):
            raise ValueError(f"{path}: nonfinite coordinate in triangle {i}")
        a, b, c = verts
        area2 = math.sqrt(dot(cross(vec(b, a), vec(c, a)), cross(vec(b, a), vec(c, a))))
        if area2 <= 1e-22:
            raise ValueError(f"{path}: degenerate triangle {i}")
        for p in verts:
            for k in range(3):
                lower[k] = min(lower[k], p[k])
                upper[k] = max(upper[k], p[k])
        points = list(map(edge_key, verts))
        for v, w in ((points[0], points[1]), (points[1], points[2]), (points[2], points[0])):
            key = tuple(sorted((v, w)))
            edges[key] += 1
            direction[(v, w)] += 1
        triangles.append(verts)
        volterms.append(dot(a, cross(b, c))/6)
    open_edges = sum(v != 2 for v in edges.values())
    oriented_wrong = sum(1 for (v, w), count in direction.items() if direction[(w,v)] != count)
    return Surface(triangles, [lower, upper], math.fsum(volterms), open_edges,
                   oriented_wrong, hashlib.sha256(data).hexdigest())


def ray_hits(triangles, p, ray):
    hits = []
    tol = 1e-11
    for a, b, c in triangles:
        e1, e2 = vec(b,a), vec(c,a)
        h = cross(ray,e2)
        det = dot(e1,h)
        if abs(det) < 1e-16:
            continue
        inv = 1.0/det
        s = vec(p,a)
        u = inv*dot(s,h)
        if u < -tol or u > 1+tol:
            continue
        q = cross(s,e1)
        v = inv*dot(ray,q)
        if v < -tol or u+v > 1+tol:
            continue
        t = inv*dot(e2,q)
        if t > 1e-8:
            hits.append(t)
    hits.sort()
    unique = []
    for t in hits:
        if not unique or abs(t-unique[-1]) > 1e-7:
            unique.append(t)
    return len(unique)


def is_inside(surface, pt):
    dirs = ((0.91,0.27,0.11),(0.19,0.73,0.54),(0.37,-0.43,0.76))
    votes = [(ray_hits(surface.triangles,pt,d) % 2) == 1 for d in dirs]
    if len(set(votes)) != 1:
        raise ValueError(f"ambiguous ray cast at {pt}: {votes}")
    return votes[0]


def audit(directory: Path, manifest: dict, stl_units: str = 'm'):
    # Only the in-memory analysis is converted to SI; source STL bytes never change.
    scale_to_m = {'m': 1.0, 'mm': 0.001}[stl_units]
    names = ('metal', 'mold')
    problems = []
    result = {'status': 'FAIL', 'surfaces': {}, 'seed_checks': {},
              'notes': ["STL has no intrinsic unit; --stl-units specifies input units for an in-memory SI audit only.",
                        "This is NOT an OpenFOAM checkMesh/CFD/CHT interface validation."]}
    surfaces = {}
    result['input_stl_units'] = stl_units
    for name in names:
        stl = directory / (name+'.stl')
        if not stl.is_file():
            problems.append(f"Missing {stl}")
            continue
        try:
            s = inspect_binary_stl(stl, coordinate_scale_to_m=scale_to_m)
        except (ValueError, OSError) as e:
            problems.append(str(e))
            continue
        surfaces[name] = s
        expected = manifest[name]
        dims = [s.bounds[1][i] - s.bounds[0][i] for i in range(3)]
        edims = [v/1000 for v in expected['size_in_mm']]
        e_volume = expected['stl_volume_m3']
        if any(abs(v-e)>max(1e-6, 0.0005*e) for v,e in zip(dims,edims)):
            problems.append(f"{name}: dimensions outside 0.05%/1 micrometre nominal tolerance: {dims}")
        if abs(s.volume_m3-e_volume)>0.005*e_volume:
            problems.append(f"{name}: signed STL volume outside 0.5% of reference")
        if s.volume_m3 <= 0:
            problems.append(f"{name}: nonpositive oriented volume")
        if s.edge_count_nonmanifold or s.edge_count_same_orientation:
            problems.append(f"{name}: STL open/nonmanifold={s.edge_count_nonmanifold}, unoriented edges={s.edge_count_same_orientation}")
        result['surfaces'][name] = {'triangles': len(s.triangles),
            'size_m': dims, 'bounds_m': s.bounds, 'signed_volume_m3': s.volume_m3,
            'edge_count_nonmanifold': s.edge_count_nonmanifold,
            'edge_count_orientation_mismatch': s.edge_count_same_orientation,
            'sha256':s.digest}
    seeds = manifest.get('sampled_seed_points_m', {})
    if len(surfaces) == len(names):
        for name in names:
            p = tuple(seeds[name])
            try:
                location = {other:is_inside(surfaces[other],p) for other in names}
            except ValueError as e:
                problems.append(f"Seed {name}: {e}")
                continue
            result['seed_checks'][name] = {'point_m':p,'inside':location}
            if not location[name] or location[('mold' if name=='metal' else 'metal')]:
                problems.append(f"Seed {name} is not unambiguously in intended CAD region: {location}")
    else:
        problems.append("Seed classification skipped because one or both surfaces are absent")
    if manifest.get('scale_requires_real_measurement_confirmation'):
        result['notes'].append('Dimensional assumption must be confirmed on a real part/CAD before scientific use.')
    result['problems'] = problems
    result['status'] = 'PASS_PRELIMINARY_STL_ONLY' if not problems else 'FAIL'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stl-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--json', type=Path)
    parser.add_argument('--stl-units', choices=('m', 'mm'), default='m',
                        help='Declared units for stored STL coordinates; no STL file changes.')
    args=parser.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    res=audit(args.stl_dir, manifest, stl_units=args.stl_units)
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8')
    print('C3D preliminary geometry gate:',res['status'])
    for name,s in res['surfaces'].items():
        print(f"  {name}: {s['triangles']} triangles; bounds [m]={s['bounds_m']}; volume [m3]={s['signed_volume_m3']:.9g}")
    for name,s in res['seed_checks'].items():
        print(f"  seed {name}: {s['inside']}")
    for p in res['problems']:
        print('  ERROR:',p)
    for n in res['notes']:
        print('  NOTE:',n)
    return 1 if res['problems'] else 0


if __name__=='__main__':
    raise SystemExit(main())
