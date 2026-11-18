#!/usr/bin/env python3
"""Offline regression for C3D-05 read-only native log postmortem."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagnose_existing_mesh.py"
spec = importlib.util.spec_from_file_location("c3d05_diagnostic", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class NativeLogDiagnosis(unittest.TestCase):
    def test_reject_mesh_quality_without_blame_on_volume(self):
        sample = """Mesh stats
    cells: 190365
    Total volume = 4.79675605036e-05
    Number of regions: 1
    *** Concave cells (using face planes) found: 172
    Failed 1 mesh checks.
End
"""
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.checkMesh.metal"
            log.write_text(sample)
            item = mod.check_one(log, "metal")
            self.assertEqual(item["cells"], 190365)
            self.assertEqual(item["connected_regions_reported"], 1)
            self.assertEqual(item["failed_checks_reported"], 1)
            self.assertEqual(item["status"], "GATE_REJECTED")
            self.assertTrue(item["checks"]["volume_within_CAD_2percent"])
            self.assertFalse(item["checks"]["native_mesh_OK_marker"])
            self.assertFalse(item["checks"]["native_failed_checks_not_positive"])
            self.assertTrue(any("Concave" in row["message"] for row in item["evidence_lines"]))

    def test_mesh_ok_with_material_volume_and_one_region(self):
        sample = """Mesh stats
    cells: 335341
    Total volume = 0.000102843547305
    Number of regions: 1
    Mesh OK.
End
"""
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.checkMesh.mold"
            log.write_text(sample)
            item = mod.check_one(log, "mold")
            self.assertEqual(item["status"], "GATE_PASSED")
            self.assertTrue(all(item["checks"].values()))

    def test_no_region_line_is_distinct_from_failed_native_quality(self):
        sample = """Mesh stats
    cells: 190365
    Total volume = 4.79675605036e-05
    Mesh OK.
End
"""
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log.checkMesh.metal"
            log.write_text(sample)
            item = mod.check_one(log, "metal")
            self.assertFalse(item["checks"]["one_connected_region_reported"])
            self.assertTrue(item["checks"]["native_mesh_OK_marker"])

    def test_missing_log_is_reported_not_fabricated(self):
        with tempfile.TemporaryDirectory() as tmp:
            item = mod.check_one(Path(tmp) / "missing.log", "metal")
            self.assertEqual(item["status"], "LOG_MISSING")
            self.assertFalse(item["exists"])


if __name__ == "__main__":
    unittest.main()
