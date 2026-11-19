#!/usr/bin/env python3
"""Small synthetic regression tests of native nonOrthoFaces topology report."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("c3d05_nonorth", ROOT / "audit_nonorthogonal_faces.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class NonorthTopology(unittest.TestCase):
    def test_classify_internal_and_contact_boundary_faces(self):
        # 2 internal faces then 2 coupled and 2 outer boundary faces.
        # owner=[0,1,0,1,2,3], neighbour=[1,2].
        patches = [
            {"name": "metal_to_mold", "startFace": 2, "nFaces": 2},
            {"name": "metalTop", "startFace": 4, "nFaces": 2},
        ]
        report = MOD.classify(
            [0, 2, 4], [0, 1, 0, 1, 2, 3], [1, 2], patches
        )
        self.assertEqual(report["severe_face_count"], 3)
        self.assertEqual(report["severe_internal_faces"], 1)
        self.assertEqual(report["severe_boundary_faces"], 2)
        self.assertEqual(report["severe_boundary_faces_by_patch"], {
            "metal_to_mold": 1, "metalTop": 1
        })
        self.assertEqual(report["severe_faces_incident_to_contact_patch_cells"], 2)
        self.assertEqual(report["severe_faces_incident_to_outer_patch_cells"], 1)

    def test_duplicate_and_invalid_face_rejected(self):
        patch = [{"name": "mold_to_metal", "startFace": 1, "nFaces": 1}]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MOD.classify([0, 0], [1, 2], [2], patch)
        with self.assertRaisesRegex(ValueError, "out-of-range"):
            MOD.classify([6], [1, 2], [2], patch)
        with self.assertRaisesRegex(ValueError, "coverage incomplete"):
            MOD.classify([0], [1, 2, 3], [2], patch)

    def test_native_missing_set_is_not_fabricated(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(FileNotFoundError, "Missing native"):
                MOD.find_native_set(Path(folder), "metal")


if __name__ == "__main__":
    unittest.main()
