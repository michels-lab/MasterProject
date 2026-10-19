"""Dependency-free synthetic tests of the preliminary geometry gate.

Tests create only tiny temporary STL fixtures; never execute OpenFOAM or CFD.
"""
from __future__ import annotations
import struct
import tempfile
import unittest
from pathlib import Path
from preflight_c3d_stl import audit, inspect_binary_stl, is_inside


def make_cube(path: Path, origin=(0, 0, 0), side=0.01, drop_last=False):
    x, y, z = origin
    quads=[
        [(0,0,0),(0,1,0),(1,1,0),(1,0,0)],
        [(0,0,1),(1,0,1),(1,1,1),(0,1,1)],
        [(0,0,0),(0,0,1),(0,1,1),(0,1,0)],
        [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
        [(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
        [(0,1,0),(0,1,1),(1,1,1),(1,1,0)],
    ]
    triangles=[]
    for a,b,c,d in quads:
        triangles.extend(((a,b,c),(a,c,d)))
    if drop_last:
        triangles.pop()
    buf=b"Synthetic test cube".ljust(80,b" ")+struct.pack('<I',len(triangles))
    for tri in triangles:
        verts=[[x+u*side,y+v*side,z+w*side] for u,v,w in tri]
        flattened=[coord for p in verts for coord in p]
        buf+=struct.pack('<12fH', 0,0,0,*flattened,0)
    path.write_bytes(buf)


class GeometryPreflightTests(unittest.TestCase):
    def test_cube_watertight_signed_volume_and_seeds(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'cube.stl'
            make_cube(file)
            s=inspect_binary_stl(file)
            self.assertEqual(s.edge_count_nonmanifold,0)
            self.assertEqual(s.edge_count_same_orientation,0)
            self.assertAlmostEqual(s.volume_m3,1e-6,delta=1e-12)
            self.assertTrue(is_inside(s,(.005,.005,.005)))
            self.assertFalse(is_inside(s,(-.01,.005,.005)))

    def test_open_surface_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'cube.stl'
            make_cube(file,drop_last=True)
            s=inspect_binary_stl(file)
            self.assertGreater(s.edge_count_nonmanifold,0)

    def test_truncated_binary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'bad.stl'
            file.write_bytes(b'bad')
            with self.assertRaises(ValueError):
                inspect_binary_stl(file)

    def test_binary_stl_mm_preflight_is_read_only(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/'cube.stl'
            make_cube(src,side=10.0)
            before=src.read_bytes()
            surface=inspect_binary_stl(src,coordinate_scale_to_m=0.001)
            self.assertAlmostEqual(surface.volume_m3,1e-6,delta=1e-11)
            self.assertAlmostEqual(surface.bounds[1][0],0.01,delta=1e-8)
            self.assertEqual(src.read_bytes(),before)
            self.assertEqual(surface.digest,hashlib.sha256(before).hexdigest())

    def test_two_region_sanity_and_units(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            make_cube(p/'metal.stl',origin=(0,0,0),side=.01)
            make_cube(p/'mold.stl',origin=(.03,0,0),side=.01)
            expected={
                'metal':{'size_in_mm':[10,10,10],'stl_volume_m3':1e-6},
                'mold':{'size_in_mm':[10,10,10],'stl_volume_m3':1e-6},
                'sampled_seed_points_m':{'metal':[.005,.005,.005],'mold':[.035,.005,.005]}}
            self.assertEqual(audit(p,expected)['status'],'PASS_PRELIMINARY_STL_ONLY')
            expected['metal']['size_in_mm']=[10000,10000,10000]
            self.assertEqual(audit(p,expected)['status'],'FAIL')

if __name__=='__main__':
    unittest.main()
