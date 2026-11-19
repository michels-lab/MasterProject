#!/usr/bin/env python3
"""Fast no-Gmsh regressions for the acceptance review of saved HEX8 evidence."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "scripts" / "review_accepted_hex_mesh.py"
spec = importlib.util.spec_from_file_location("c3d05_hex_qa", SRC)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class TestAcceptedHEX8ReadOnlyReview(unittest.TestCase):
    def test_native_quality_reads_accepted_cell_determinant_and_high_nonorth(self):
        sample = """Mesh stats
    cells: 92200
    Number of regions: 1 (OK).
    Total volume = 4.79754032229e-05. Cell volumes OK.
    Mesh non-orthogonality Max: 76.798896286 average: 25.967
    *Number of severely non-orthogonal (> 70 degrees) faces: 595.
    Max skewness = 1.36064188814 OK.
    Cell determinant (wellposedness) : minimum: 0.0568401483702 average: 5.73
    Cell determinant check OK.
Mesh OK.
"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "log.checkMesh.metal"
            p.write_text(sample, encoding="utf-8")
            item = mod.native_quality(p, "metal")
            self.assertTrue(item["native_mesh_gate_passed"])
            self.assertEqual(item["cells"], 92200)
            self.assertEqual(item["severely_nonorthogonal_faces_above_70deg"], 595)
            self.assertGreater(item["minimum_cell_determinant"], 0.001)

    def test_native_quality_does_not_accept_failed_mesh(self):
        sample = """cells: 190365
Number of regions: 1 (OK).
Total volume = 4.79675605036e-05. Cell volumes OK.
Mesh non-orthogonality Max: 68.80 average: 20.7
*Number of severely non-orthogonal (> 70 degrees) faces: 0.
Max skewness = 0.889 OK.
Cell determinant (wellposedness) : minimum: 1.462e-18 average: 1.323
***Cells with small determinant (< 0.001) found, number of cells: 96
Failed 1 mesh checks.
"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "log.checkMesh.metal"
            p.write_text(sample, encoding="utf-8")
            item = mod.native_quality(p, "metal")
            self.assertFalse(item["native_mesh_gate_passed"])
            self.assertEqual(item["native_failed_checks"], 1)

    def test_mapped_patch_parsing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "boundary"
            p.write_text(
                "FoamFile\n{\nclass polyBoundaryMesh;\n}\n"
                "1\n(\nmetal_to_mold\n{\n"
                "type mappedWall;\nnFaces 12636;\nstartFace 252000;\n"
                "neighbourRegion mold;\nneighbourPatch mold_to_metal;\n"
                "}\n)\n", encoding="utf-8")
            item = mod.boundary_patch(p, "metal_to_mold")
            self.assertEqual(item["nFaces"], 12636)
            self.assertEqual(item["neighbourRegion"], "mold")
            self.assertEqual(item["type"], "mappedWall")
            with self.assertRaises(ValueError):
                mod.boundary_patch(p, "wrong_patch")

    def test_cad_provenance_seven_conditions_pass_when_matching(self):
        data = {
            "mesh_element_topology": "HEX8_QUAD4_ONLY",
            "subdivide_to_hex": True,
            "algorithm_3d": 1,
            "mesh_size_mm": 3.6,
            "source": {
                "metal_sha256": mod.SHA_METAL,
                "mold_sha256": mod.SHA_MOLD,
            },
            "post_subdivision_hex_count": 270788,
        }
        details = mod.cad_provenance_details(data, 270788)
        self.assertEqual(len(details), 7)
        self.assertTrue(all(item["passed"] for item in details.values()))

    def test_cad_provenance_reports_exact_failure_instead_of_waiving_it(self):
        data = {
            "mesh_element_topology": "HEX8_QUAD4_ONLY",
            "subdivide_to_hex": True,
            "algorithm_3d": 1,
            "mesh_size_mm": 3.6,
            "source": {
                "metal_sha256": mod.SHA_METAL,
                "mold_sha256": mod.SHA_MOLD,
            },
            "post_subdivision_hex_count": 270787,
        }
        details = mod.cad_provenance_details(data, 270788)
        self.assertFalse(details["post_subdivision_hex_count_vs_native_parent_cells"]["passed"])
        self.assertEqual(details["post_subdivision_hex_count_vs_native_parent_cells"]["observed"], 270787)
        self.assertEqual(details["post_subdivision_hex_count_vs_native_parent_cells"]["expected"], 270788)
        self.assertTrue(all(
            value["passed"] for name, value in details.items()
            if name != "post_subdivision_hex_count_vs_native_parent_cells"
        ))
        data["post_subdivision_hex_count"] = 270788
        data["source"]["mold_sha256"] = "bad-sha"
        details = mod.cad_provenance_details(data, 270788)
        self.assertFalse(details["source.mold_sha256"]["passed"])
        self.assertTrue(details["post_subdivision_hex_count_vs_native_parent_cells"]["passed"])

    def test_cad_provenance_missing_fields_stay_failed(self):
        details = mod.cad_provenance_details({}, 270788)
        self.assertFalse(any(item["passed"] for item in details.values()))
        self.assertIsNone(details["mesh_element_topology"]["observed"])

    def test_missing_native_log_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                mod.native_quality(Path(d) / "missing", "mold")


if __name__ == "__main__":
    unittest.main()
