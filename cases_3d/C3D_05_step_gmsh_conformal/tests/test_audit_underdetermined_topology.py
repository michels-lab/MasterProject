#!/usr/bin/env python3
"""Synthetic read-only test for C3D-05 underdetermined-cell connectivity audit."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_underdetermined_topology.py"
spec = importlib.util.spec_from_file_location("c3d05_cell_faces", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def foam_list(name: str, values: list[int]) -> str:
    return (
        "FoamFile\n{\n    version 2.0;\n    format ascii;\n"
        f"    class labelList;\n    object {name};\n}}\n"
        f"{len(values)}\n(\n" + "".join(f"{i}\n" for i in values) + ")\n"
    )


class CellTopologyTest(unittest.TestCase):
    def test_boundary_face_counts_and_region_patch_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mesh = root / "constant" / "metal" / "polyMesh"
            (mesh / "sets").mkdir(parents=True)
            (mesh / "sets" / "underdeterminedCells").write_text(
                foam_list("underdeterminedCells", [0, 1])
            )
            (mesh / "owner").write_text(foam_list("owner", [0, 0, 0, 1, 1]))
            (mesh / "neighbour").write_text(foam_list("neighbour", [1]))
            (mesh / "boundary").write_text(
                "FoamFile\n{\nclass polyBoundaryMesh;\n}\n"
                "2\n(\nmetalTop\n{\ntype patch;\nnFaces 2;\nstartFace 1;\n}\n"
                "metal_to_mold\n{\ntype mappedWall;\nnFaces 2;\nstartFace 3;\n}\n)\n"
            )
            result = mod.audit_region(root, "metal")
            self.assertEqual(result["underdetermined_count"], 2)
            self.assertEqual(result["boundary_face_count_distribution"], {2: 2})
            self.assertEqual(result["internal_face_count_distribution"], {1: 2})
            self.assertEqual(result["cells_touching_each_patch"], {"metalTop": 1, "metal_to_mold": 1})
            self.assertEqual(result["cells_with_two_or_more_boundary_faces"], 2)

    def test_missing_bad_cellset_is_non_destructive_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                mod.audit_region(Path(tmp), "mold")


if __name__ == "__main__":
    unittest.main()
