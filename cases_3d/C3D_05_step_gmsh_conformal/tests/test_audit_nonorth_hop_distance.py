#!/usr/bin/env python3
"""Gmsh- and OpenFOAM-free regressions of the nonorth cell-hop metric."""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT))
SPEC = importlib.util.spec_from_file_location(
    "c3d05_nonorth_hops", SCRIPT / "audit_nonorth_hop_distance.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


class HopDistance(unittest.TestCase):
    def test_chain_of_four_cells_contact_vs_outer(self):
        # Three internal faces: 0-1, 1-2, 2-3.
        # Contact boundary face=3 on cell0; outer face=4 on cell3.
        owner = [0, 1, 2, 0, 3]
        neighbour = [1, 2, 3]
        patches = [
            {"name": "metal_to_mold", "startFace": 3, "nFaces": 1},
            {"name": "metalTop", "startFace": 4, "nFaces": 1},
        ]
        result = mod.compute_face_hops([1], owner, neighbour, patches)
        self.assertEqual(result["n_cells"], 4)
        self.assertEqual(result["distance_in_cell_hops_to_contact"]["min"], 1)
        self.assertEqual(result["distance_in_cell_hops_to_outer"]["min"], 1)
        self.assertTrue(result["direct_contact_adjacency_zero"])
        self.assertTrue(result["direct_outer_adjacency_zero"])

    def test_boundary_incident_face_has_zero_hops_and_is_not_claimed_safe(self):
        owner = [0, 1, 2, 0, 2]
        neighbour = [1, 2, 0]
        patches = [
            {"name": "metal_to_mold", "startFace": 3, "nFaces": 1},
            {"name": "metalTop", "startFace": 4, "nFaces": 1},
        ]
        result = mod.compute_face_hops([0], owner, neighbour, patches)
        self.assertEqual(result["distance_in_cell_hops_to_contact"]["min"], 0)
        self.assertFalse(result["direct_contact_adjacency_zero"])

    def test_missing_wall_roots_and_invalid_faces_reject(self):
        with self.assertRaisesRegex(ValueError, "Interface"):
            mod.compute_face_hops(
                [0], [0, 0, 2], [1],
                [{"name": "metalTop", "startFace": 1, "nFaces": 2}],
            )
        patches = [
            {"name": "mold_to_metal", "startFace": 1, "nFaces": 1},
            {"name": "moldOuterUnclassified", "startFace": 2, "nFaces": 1},
        ]
        with self.assertRaisesRegex(ValueError, "only VALID internal"):
            mod.compute_face_hops([1], [0, 0, 2], [1], patches)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            mod.compute_face_hops([0, 0], [0, 0, 2], [1], patches)

    def test_percentile_and_histogram_exact(self):
        sample = mod.summarise_distances([1, 1, 2, 5, 7])
        self.assertEqual(sample["median"], 2)
        self.assertEqual(sample["p90"], 5)
        self.assertEqual(sample["within_2_hops"], 3)
        self.assertEqual(sample["by_hops"]["7"], 1)


if __name__ == "__main__":
    unittest.main()
