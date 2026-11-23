"""FS-C07 stage regression tests; synthetic fixtures, NO native CFD."""
import json
from pathlib import Path
import tempfile
import unittest

from stage_fs_c07_native import (
    CONTROL, FUNCTIONS, FVMODELS, MONITORS,
    source_preflight, stage,
)


class FS_C07_Staging(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="fs-c07-static-")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.src = root / "FS_C06_VOF_SOLID_SMOKE_accepted"
        self.dest = root / "FS_C07_THERMAL_new"
        for n in ("0/fluid", "0/mold", "constant/fluid/polyMesh",
                  "constant/mold/polyMesh", "system",
                  "1e-07/fluid", "2e-07/fluid"):
            (self.src / n).mkdir(parents=True, exist_ok=True)
        for name in ("0/fluid/T.metal", "0/fluid/alpha.metal",
                     "0/mold/T", "constant/fluid/polyMesh/points",
                     "constant/mold/polyMesh/points"):
            (self.src / name).write_text("ORIGINAL PRESERVE\n")
        (self.src / "constant/fluid/fvModels").write_bytes(FVMODELS.read_bytes())
        (self.src / "system/functions").write_bytes(FUNCTIONS.read_bytes())
        (self.src / "system/controlDict").write_text("C06 ORIGINAL\n")
        (self.src / "FS_C06_REPORT.json").write_text(json.dumps({
            "status": "FS_C06_NATIVE_TWO_STEP_MODEL_FIELD_OBSERVED_NOT_SHRINKAGE",
            "native_cfd_executed": True,
            "solid_fraction_fields_measured": True,
        }))
        for name in MONITORS:
            folder = self.src / "postProcessing" / (
                "mold" if name.endswith("FluxMold") else "fluid") / name / "0"
            folder.mkdir(parents=True)
            (folder / "monitor.dat").write_text("0\t123\n")

    def test_source_preflight_accepts_both_nested_regions(self):
        result = source_preflight(self.src)
        self.assertEqual(set(result["source_monitor_sha256"]), set(MONITORS))
        self.assertEqual(len(result["native_FS_C06_report_sha256"]), 64)

    def test_native_source_new_case_preserves_original(self):
        original = (self.src / "0/fluid/T.metal").read_bytes()
        report = stage(self.src, self.dest)
        self.assertEqual(report["status"], "FS_C07_STAGED_NO_CFD")
        self.assertFalse(report["native_cfd_executed"])
        self.assertFalse(report["volumetric_shrinkage_implemented"])
        self.assertFalse(report["phase_density_coupling_implemented"])
        self.assertEqual((self.dest / "system/controlDict").read_bytes(),
                         CONTROL.read_bytes())
        self.assertEqual((self.dest / "system/functions").read_bytes(),
                         FUNCTIONS.read_bytes())
        self.assertEqual((self.src / "0/fluid/T.metal").read_bytes(), original)
        self.assertEqual((self.src / "system/controlDict").read_text(),
                         "C06 ORIGINAL\n")
        self.assertTrue((self.src / "postProcessing").is_dir())
        self.assertFalse((self.dest / "postProcessing").exists())
        self.assertFalse((self.dest / "1e-07").exists())
        self.assertFalse((self.dest / "2e-07").exists())
        self.assertTrue((self.dest / "0/fluid/T.metal").exists())
        self.assertTrue((self.dest / "FS_C06_PARENT_REPORT.json").is_file())
        self.assertFalse((self.dest / "FS_C06_REPORT.json").exists())

    def test_second_stage_same_output_is_rejected(self):
        stage(self.src, self.dest)
        with self.assertRaisesRegex(ValueError, "already exists"):
            stage(self.src, self.dest)

    def test_source_without_true_native_gate_rejected(self):
        path = self.src / "FS_C06_REPORT.json"
        data = json.loads(path.read_text())
        data["native_cfd_executed"] = False
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "provenance"):
            source_preflight(self.src)

    def test_missing_monitor_rejected(self):
        (self.src / "postProcessing/fluid/FS_C06_mixtureMass/0/monitor.dat").unlink()
        with self.assertRaisesRegex(ValueError, "monitor absent"):
            stage(self.src, self.dest)
        self.assertFalse(self.dest.exists())

    def test_unknown_newer_source_time_rejected(self):
        (self.src / "3e-07").mkdir()
        with self.assertRaisesRegex(ValueError, "unexpected.*time"):
            stage(self.src, self.dest)
        self.assertFalse(self.dest.exists())

    def test_mismatched_solver_physics_rejected(self):
        p = self.src / "constant/fluid/fvModels"
        p.write_bytes(p.read_bytes() + b"\nuncalibratedSource {}\n")
        with self.assertRaisesRegex(ValueError, "differs"):
            source_preflight(self.src)

    def test_symlink_in_source_rejected(self):
        (self.src / "symbolic").symlink_to(self.src / "0")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            source_preflight(self.src)

    def test_native_transition_controls_are_bounded_and_no_fabricated_rho(self):
        text = CONTROL.read_text()
        self.assertIn("regionSolvers", text)
        self.assertIn("fluid           compressibleVoF;", text)
        self.assertIn("mold            solid;", text)
        self.assertIn("endTime         1;", text)
        self.assertIn("maxDeltaT       1e-04;", text)
        self.assertIn("maxCo           0.1;", text)
        self.assertIn("maxAlphaCo      0.1;", text)
        self.assertIn("writeControl    adjustableRunTime;", text)
        self.assertNotIn("massSource", text)
        self.assertNotIn("rhoLiquid", text)
        self.assertNotIn("functions\n{", text)


if __name__ == "__main__":
    unittest.main()
