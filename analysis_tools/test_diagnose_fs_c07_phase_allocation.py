"""FS-C07 native VOF/solid forensic regression; synthetic-only, NO CFD."""
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import diagnose_fs_c07_phase_allocation as m


class AllocationTests(unittest.TestCase):
    def test_zero_solid_is_valid(self):
        d = m.classify_allocation([0.0, 0.1, 1.0], [0.0, 0.0, 0.0])
        self.assertTrue(d["strict_0_le_s_le_a_le_1_pass"])
        self.assertEqual(d["max_physical_constraint_violation"], 0)
        self.assertEqual(d["positive_solid_cell_count_exact"], 0)

    def test_machine_roundoff_is_reported_but_not_clipped(self):
        tiny = 9.7663980137e-46
        d = m.classify_allocation([-tiny, 1.0], [0, 0])
        self.assertEqual(d["strict_invalid_cells"], 1)
        self.assertTrue(d["validation_pass_with_original_tolerance_1e-8"])
        self.assertFalse(d["strict_0_le_s_le_a_le_1_pass"])
        self.assertEqual(d["alpha_metal_min"], -tiny)
        self.assertEqual(d["worst_by_constraint"]["metal_negative"]["cell"], 0)
        self.assertEqual(d["worst_by_constraint"]["solid_above_metal"]["cell"], 0)
        self.assertFalse(d["native_fields_were_modified_or_clipped"])

    def test_significant_solid_above_metal_is_not_silently_accepted(self):
        d = m.classify_allocation([0.2, 0.8], [0.2001, 0.5])
        self.assertFalse(d["validation_pass_with_original_tolerance_1e-8"])
        self.assertEqual(d["violating_cells_above_tolerance"][str(1e-8)], 1)
        self.assertAlmostEqual(
            d["worst_by_constraint"]["solid_above_metal"]["overshoot"],
            0.0001, places=8)

    def test_slight_outside_01_is_classified(self):
        d = m.classify_allocation([1+1e-9, 0.2], [0.2, -1e-9])
        self.assertEqual(d["count_by_constraint"]["metal_above_1"], 1)
        self.assertEqual(d["count_by_constraint"]["solid_negative"], 1)
        self.assertTrue(d["validation_pass_with_original_tolerance_1e-8"])
        self.assertEqual(d["violating_cells_above_tolerance"][str(1e-12)], 2)

    def test_nonfinite_values_are_blocked(self):
        for v in (math.nan, math.inf, -math.inf):
            with self.subTest(v=v), self.assertRaisesRegex(ValueError, "NaN"):
                m.classify_allocation([0.2, v], [0.0, 0.0])

    def test_mismatched_fields_blocked(self):
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            m.classify_allocation([0.5], [0.0, 0.0])

    def test_examples_capped_without_losing_error_count(self):
        d = m.classify_allocation([-0.1]*10, [0.0]*10, limit_examples=2)
        self.assertEqual(d["count_by_constraint"]["metal_negative"], 10)
        self.assertEqual(len(d["first_examples_by_constraint"]["metal_negative"]), 2)

    def test_read_only_native_snapshot_decision(self):
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp) / "FS_C07_THERMAL_synthetic"
            first = case / "0.05/fluid"
            last = case / "1/fluid"
            for p in (first, last):
                p.mkdir(parents=True)
                for field in ("alpha.metal", "alpha.metal.solid", "T.metal"):
                    (p / field).write_text("NATIVE FAKE FOR MOCK ONLY")
            status = {
                "case": str(case),
                "latest_log_Time_s": 1.0,
                "solver_end_marker_in_recent_log_tail": True,
                "report_status": "FS_C07_INCOMPLETE_PRESERVE_EVIDENCE",
                "report_last_error":
                    "FS-C03 STATIC GATE: invalid VOF / absolute-solid phase allocation",
            }
            with (
                patch.object(m, "inspect", return_value=status),
                patch.object(m, "native_time_dirs",
                             return_value=[(0.05, first.parent), (1.0, last.parent)]),
                patch.object(m, "read_alpha", side_effect=[
                    [-1e-45, 1.0, 0.1], [0.1, 1.0, 0.5]]),
                patch.object(m, "read_native_solid_fraction", side_effect=[
                    [0, 0, 0], [0, 0.5, 0.1]]),
                patch.object(m, "read_native_metal_temperature", side_effect=[
                    [1500, 1490, 1500], [1500, 1400, 1500]]),
                patch.object(m, "sha256", return_value="test-not-real"),
                patch.object(m, "FLUID_CELLS", 3),
            ):
                result = m.inspect_saved_phases(case)
            self.assertEqual(result["complete_native_phase_snapshots_inspected"], 2)
            self.assertTrue(result["all_snapshots_pass_original_tolerance"])
            self.assertFalse(result["all_snapshots_pass_strict_allocation"])
            self.assertIsNone(result["first_snapshot_failing_original_tolerance"])
            self.assertTrue(result["any_core_metal_below_screen_liquidus"])
            self.assertTrue(result["any_positive_solid_cells_in_saved_fields"])
            self.assertTrue(result["read_only"])
            self.assertTrue(result["postprocess_only"])
            self.assertTrue(result["no_solver_or_mesh_change"])


if __name__ == "__main__":
    unittest.main()
