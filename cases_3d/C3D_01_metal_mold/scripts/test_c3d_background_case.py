"""Static/synthetic C3D-01 tests. CI never runs OpenFOAM, blockMesh or CFD."""
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import unittest

CASE = Path(__file__).resolve().parents[1]
DICT = (CASE/"system"/"blockMeshDict").read_text(encoding="utf-8")
REF = json.loads((CASE/"geometry_reference.json").read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("prepare_geometry", CASE/"scripts"/"prepare_geometry.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def vectors():
    raw = re.search(r"\bvertices\s*\((.*?)\);", DICT, re.S).group(1)
    return [tuple(map(float,m.split())) for m in
            re.findall(r"\(([-+.0-9eE ]+)\)", raw)]


def surface_faces():
    raw = re.search(r"\bfaces\s*\((.*?)\);", DICT, re.S).group(1)
    return [tuple(map(int,nums.split())) for nums in
            re.findall(r"\((\d+(?:\s+\d+){3})\)", raw)]


def subtract(a,b):
    return tuple(x-y for x,y in zip(a,b))


def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


class C3DMeshInputTests(unittest.TestCase):
    def test_exact_box_size_and_cells(self):
        v=vectors()
        self.assertEqual(len(v),8)
        extent=[max(p[i] for p in v)-min(p[i] for p in v) for i in range(3)]
        for measured,expected in zip(extent,(58.0,72.0,58.0)):
            self.assertAlmostEqual(measured,expected)
        self.assertIn("hex (0 1 2 3 4 5 6 7) (29 36 29)",DICT)
        self.assertIn("units [mm];",DICT)
        self.assertNotIn("convertToMeters",DICT)
        self.assertEqual(29*36*29,30276)
        self.assertEqual(REF["background_mesh"]["cells_nxyz"],[29,36,29])

    def test_six_boundary_face_normals_point_outwards(self):
        v=vectors()
        faces=surface_faces()
        self.assertEqual(len(faces),6)
        bounds_center=tuple(sum(p[k] for p in v)/8 for k in range(3))
        for f in faces:
            a,b,c=[v[i] for i in f[:3]]
            face_mid=tuple(sum(v[i][k] for i in f)/4 for k in range(3))
            n=cross(subtract(b,a),subtract(c,a))
            outward=subtract(face_mid,bounds_center)
            self.assertGreater(sum(n[k]*outward[k] for k in range(3)),0,
                               f"Boundary face {f} is pointing inward")

    def test_corrected_solidworks_fingerprints_are_stable(self):
        self.assertEqual(REF["mold"]["triangle_count"],3084)
        self.assertEqual(REF["metal"]["triangle_count"],3896)
        self.assertEqual(REF["stl_coordinate_conversion_factor"],0.001)  # SI audit factor, not file conversion
        self.assertEqual(REF["sampled_seed_points_m"]["metal"],[0.0259,-0.02,0.0259])

    def test_original_binary_stl_is_kept_in_mm_unchanged(self):
        # A synthetic STL is inspected by Python, never rescaled/rewritten.
        raw = bytearray(b"Synthetic STL test".ljust(80,b" "))
        raw += struct.pack("<I",1)
        raw += struct.pack("<12fH",0.0,0.0,1.0,
                           100.0,-40.0,0.0,200.0,-40.0,0.0,
                           100.0,0.0,50.0,0)
        baseline = bytes(raw)
        self.assertEqual(mod.validate_binary_stl(baseline),1)
        self.assertEqual(bytes(raw),baseline)
        self.assertEqual(struct.unpack_from("<f",baseline,96)[0],100.0)
        prepare=(CASE/"scripts"/"prepare_geometry.py").read_text()
        self.assertIn('(temporary/(name+".stl")).write_bytes(raw)',prepare)
        self.assertNotIn("scalePoints",prepare)
        self.assertNotIn("convert_binary_stl_mm_to_m",prepare)

    def test_bad_binary_stl_is_rejected(self):
        with self.assertRaises(ValueError):
            mod.validate_binary_stl(b"short")

    def test_native_units_in_mesh_and_pending_snappy(self):
        self.assertIn("units [mm];",DICT)
        self.assertTrue((CASE/"constant"/"geometry"/"README.md").is_file())
        self.assertEqual(REF["stl_original_units"],"mm")

    def test_scripts_never_run_cfd_or_cleanup(self):
        content=(CASE/"scripts"/"run_blockMesh_only.sh").read_text()
        for command in ("Allrun","Allclean","foamMultiRun","rm -rf"):
            self.assertNotIn(command,content)
        self.assertIn("checkMesh",content)
        self.assertIn("blockMesh",content)
        self.assertNotIn("python3 ",content)
        self.assertNotIn("preflight_c3d_stl.py",content)
        self.assertNotIn("prepare_geometry.py",content)
        self.assertNotIn("--stl-units",content)
        self.assertIn("log.blockMesh",content)
        self.assertIn("log.checkMesh.background",content)
        self.assertIn("constant/polyMesh",content)


if __name__=="__main__":
    unittest.main()
