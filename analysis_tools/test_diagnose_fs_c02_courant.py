"""Tests for the read-only FS-C02 Courant hotspot extractor; no CFD."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from diagnose_fs_c02_courant import diagnose, diagnose_lines


class FS_C02_CourantTests(unittest.TestCase):
    def test_peak_location_and_previous_following_times_are_only_brackets(self):
        lines = [
            "Create time",
            "Courant Number mean: 0 max: 0",
            "deltaT = 0.0001",
            "Time = 0.0001s",
            "Courant Number mean: 0.01 max: 9.41807",
            "Interface Courant Number mean: 0 max: 0",
            "deltaT = 5e-06",
            "Time = 0.000105s",
            "Courant Number mean: 0.01 max: 0.246551",
            "End",
        ]
        r = diagnose_lines(lines, .25, 2, 1)
        self.assertEqual(r["courant_observations"], 3)
        self.assertEqual(r["courant_global_max"], 9.41807)
        self.assertEqual(r["courant_last_max"], .246551)
        self.assertEqual(r["observations_above_threshold"], 1)
        self.assertEqual(r["observations_above_one"], 1)
        self.assertEqual(r["observations_above_five"], 1)
        peak = r["largest_spikes"][0]
        self.assertEqual(peak["line_number_1_based"], 5)
        self.assertEqual(peak["time_before_marker_s"], .0001)
        self.assertEqual(peak["time_after_marker_s"], .000105)
        self.assertEqual(peak["deltaT_before_marker_s"], .0001)
        self.assertEqual(peak["deltaT_after_marker_s"], 5e-06)
        self.assertTrue(peak["context_lines"])

    def test_no_valid_courant_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no Courant"):
            diagnose_lines(["Interface Courant Number mean: 0 max: 0"])
        with self.assertRaisesRegex(ValueError, "non-finite"):
            diagnose_lines(["Courant Number mean: 0 max: nan"])

    def test_negative_courant_max_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            diagnose_lines(["Courant Number mean: 0 max: -1"])

    def test_wrong_case_identity_is_blocked(self):
        with tempfile.TemporaryDirectory(prefix="fs-c02-hotspot-") as folder:
            run = Path(folder) / "FS-C02_synthetic"
            (run / "FS-C02").mkdir(parents=True)
            (run / "logs").mkdir()
            (run / "logs/FS-C02_foamRun.log").write_text(
                "Courant Number mean: 0 max: 9.41807\n"
            )
            (run / "FS-C02_RUN_STATUS.json").write_text(
                json.dumps({"case_id": "C3D-02"})
            )
            with self.assertRaisesRegex(ValueError, "wrong case"):
                diagnose(run)

    def test_original_run_not_modified_and_peak_reported(self):
        with tempfile.TemporaryDirectory(prefix="fs-c02-hotspot-") as folder:
            run = Path(folder) / "FS-C02_synthetic"
            (run / "FS-C02").mkdir(parents=True)
            (run / "logs").mkdir()
            contents = "Time = 0.001\nCourant Number mean: 0.1 max: 9.41807\n"
            log = run / "logs/FS-C02_foamRun.log"
            log.write_text(contents)
            status = run / "FS-C02_RUN_STATUS.json"
            status.write_text(json.dumps({"case_id": "FS-C02"}))
            r = diagnose(run, context=0)
            self.assertEqual(r["largest_spikes"][0]["courant_max"], 9.41807)
            self.assertEqual(log.read_text(), contents)
            self.assertEqual(status.read_text(), '{"case_id": "FS-C02"}')


if __name__ == "__main__":
    unittest.main()
