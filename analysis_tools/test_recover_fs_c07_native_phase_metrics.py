"""FS-C07 archived-field recovery tests; synthetic data only. NO CFD."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recover_fs_c07_native_phase_metrics as r


class NativeRecoveryTests(unittest.TestCase):
    def test_nonclipped_raw_volumes_exact(self):
        # One valid cell, one with more solid than metal; keep native inputs.
        volumes = [2.0, 3.0]
        alpha = [1.0, 0.001]
        solid = [0.5, 0.001005]
        T = [1460.0, 1500.0]
        before = (alpha[:], solid[:], T[:])
        d = r.raw_phase_volume_diagnostics(volumes, alpha, solid, T)
        self.assertAlmostEqual(d["native_raw_volIntegrate_alpha_metal_m3"], 2.003)
        self.assertAlmostEqual(d["native_raw_volIntegrate_alpha_metal_solid_m3"],
                               1.003015)
        self.assertAlmostEqual(
            d["positive_violation_volume_integral_solid_exceeds_metal_m3"],
            0.000015)
        self.assertAlmostEqual(
            d["native_raw_liquid_difference_m3"],
            d["native_raw_volIntegrate_alpha_metal_m3"]
            - d["native_raw_volIntegrate_alpha_metal_solid_m3"])
        self.assertEqual(d["core_metal_cells_below_C14_screen_liquidus"], 1)
        self.assertEqual(d["core_metal_raw_solid_integral_m3"], 1.0)
        self.assertTrue(d["raw_solid_integral_is_not_accepted_solid_volume"])
        self.assertFalse(d["raw_fields_clipped_or_modified"])
        self.assertEqual(before, (alpha, solid, T))

    def test_negative_roundoff_integral_separately_reported(self):
        d = r.raw_phase_volume_diagnostics(
            [1.0, 4.0], [1.0, -1e-22], [0.5, -3e-21],
            [1450.0, 1500.0])
        self.assertAlmostEqual(d["negative_metal_volume_magnitude_m3"],
                               4e-22)
        self.assertAlmostEqual(d["negative_solid_volume_magnitude_m3"],
                               1.2e-20)
        self.assertAlmostEqual(
            d["positive_violation_volume_integral_solid_exceeds_metal_m3"],
            0)

    def test_below_liquidus_requires_metal_core(self):
        d = r.raw_phase_volume_diagnostics(
            [1.0, 1.0], [0.0001, 1.0], [0.0001, 0.2],
            [1200.0, 1500.0])
        self.assertEqual(d["core_metal_cells_below_C14_screen_liquidus"], 0)
        self.assertEqual(d["positive_solid_count_all_cells_including_traces"], 2)

    def test_mesh_or_data_corruption_blocks(self):
        for vols, a, s, T in [
            ([], [], [], []),
            ([0.0], [0.5], [0.1], [1450]),
            ([1], [0.5], [float("nan")], [1450]),
            ([1], [0.5], [0.1], [0]),
            ([1, 2], [0.5], [0.1], [1450]),
        ]:
            with self.subTest(volumes=vols), self.assertRaises(ValueError):
                r.raw_phase_volume_diagnostics(vols, a, s, T)

    def test_time_series_nearest_monitor_without_fabrication(self):
        rows = [(0.00001, 1.0), (0.05, 5.0), (0.1, 9.0)]
        self.assertEqual(r.nearest_monitor_value(rows, 0.05), 5.0)
        self.assertIsNone(r.nearest_monitor_value(rows, 0.2))
        self.assertIsNone(r.nearest_monitor_value([], 0.05))

    def test_realistic_native_monitor_file_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp) / "FS_C07_THERMAL_dummy"
            monitor = (case / "postProcessing/fluid"
                       / "FS_C06_solidMetalVolume/0/volFieldValue.dat")
            monitor.parent.mkdir(parents=True)
            monitor.write_text(
                "# Selection : all\n"
                "# Time  volIntegrate(alpha.metal.solid)\n"
                "0 0.0\n0.05 4.122e-8\n1 2.3e-6\n")
            self.assertEqual(
                r.load_native_vol_field_monitor(case, "FS_C06_solidMetalVolume"),
                [(0.0, 0.0), (0.05, 4.122e-8), (1.0, 2.3e-6)])
            self.assertIsNone(r.nearest_monitor_value(
                r.load_native_vol_field_monitor(case, "FS_C06_solidMetalVolume"),
                0.75))

    def test_read_only_evaluate_from_existing_native_fields_mocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp) / "FS_C07_THERMAL_dummy"
            case.mkdir()
            (case / "0/fluid").mkdir(parents=True)
            (case / "1/fluid").mkdir(parents=True)
            for field in ("alpha.metal", "alpha.metal.solid", "T.metal"):
                (case / "1/fluid" / field).write_text("native-placeholder")
            (case / "0/fluid/alpha.metal").write_text("native-initial")
            before = {str(p.relative_to(case)): p.read_bytes()
                      for p in case.rglob("*") if p.is_file()}
            with (
                patch.object(r, "inspect", return_value={
                    "case": str(case),
                    "solver_end_marker_in_recent_log_tail": True,
                    "latest_log_Time_s": 1.0,
                    "report_last_error": "allocation failed",
                }),
                patch.object(r, "read_mesh", return_value={}),
                patch.object(r, "cell_volume_m3", side_effect=[2.0, 3.0]),
                patch.object(r, "FLUID_CELLS", 2),
                patch.object(r, "read_alpha", side_effect=[
                    [1.0, 0.001], [1.0, 0.001]]),
                patch.object(r, "read_native_solid_fraction",
                             return_value=[0.5, 0.001005]),
                patch.object(r, "read_native_metal_temperature",
                             return_value=[1460.0, 1500.0]),
                patch.object(r, "native_time_dirs", return_value=[
                    (0.0, case / "0"), (1.0, case / "1")]),
                patch.object(r, "load_native_vol_field_monitor",
                             return_value=[]),
            ):
                report = r.evaluate(case)
            self.assertEqual(report["complete_saved_native_phase_snapshots"], 1)
            self.assertFalse(report["all_saved_snapshots_physically_bounded"])
            self.assertFalse(report["globally_conservative_shrinkage_or_feeding_validated"])
            self.assertAlmostEqual(
                report["time_series"][0]
                    ["positive_violation_volume_integral_solid_exceeds_metal_m3"],
                0.000015)
            after = {str(p.relative_to(case)): p.read_bytes()
                     for p in case.rglob("*") if p.is_file()}
            self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
