"""Regression tests for the verbatim-reported 20-state FS-C07 native evidence.

These tests check *documented* WSL observations and arithmetic consistency.
They neither execute CFD nor re-read native case fields from researcher's WSL.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT / "freesurface/FS-C07_thermal_transition/evidence"
    / "FS_C07_PHASE_ALLOCATION_20_NATIVE_STATES_20261123.json"
)


class TestFS_C07NativeEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.rows = cls.report["time_series"]

    def test_exactly_20_native_saved_states_at_0p05_intervals(self):
        self.assertEqual(len(self.rows), 20)
        self.assertEqual([round(row["time_s"], 6) for row in self.rows],
                         [round(i*0.05, 6) for i in range(1, 21)])
        self.assertEqual(self.report["tested_native_times_count"], 20)

    def test_all_native_fluid_bins_partition_significant_violations(self):
        for row in self.rows:
            counted = sum(row[name] for name in (
                "n_metal_alpha_0_to_1e6",
                "n_metal_alpha_1e6_to_1e3",
                "n_metal_alpha_1e3_to_0p5",
                "n_core_metal_alpha_ge_0p5",
            ))
            self.assertEqual(counted, row["n_gt_1e8"])
            self.assertEqual(row["n_core_metal_alpha_ge_0p5"], 0)

    def test_total_is_7692_cell_time_incidents_not_unique_cells(self):
        summed = sum(row["n_gt_1e8"] for row in self.rows)
        self.assertEqual(summed, 7692)
        self.assertEqual(
            self.report["aggregate"]["total_cell_time_incidences_gt_1e8"],
            summed
        )
        self.assertIn("cell-time incidences", self.report["metric"])

    def test_99p258970_percent_incidents_at_alpha_below_1e3(self):
        bins = (
            sum(r["n_metal_alpha_0_to_1e6"] for r in self.rows),
            sum(r["n_metal_alpha_1e6_to_1e3"] for r in self.rows),
            sum(r["n_metal_alpha_1e3_to_0p5"] for r in self.rows),
        )
        self.assertEqual(bins, (2938, 4697, 57))
        self.assertEqual(sum(bins), 7692)
        self.assertAlmostEqual(
            self.report["aggregate"]["fraction_of_incidences_below_alpha_metal_1e3"],
            (2938+4697)/7692, places=15,
        )

    def test_three_distinct_peak_times_are_preserved(self):
        a = self.report["aggregate"]
        self.assertEqual(a["peak_count_time_s"], 0.35)
        self.assertEqual(a["peak_count"], 641)
        self.assertEqual(a["peak_integrated_excess_time_s"], 0.4)
        self.assertAlmostEqual(a["peak_integrated_excess_m3"],
                               6.1272893715684775e-12)
        self.assertEqual(a["peak_fraction_violation_time_s"], 0.2)
        self.assertAlmostEqual(a["peak_fraction_violation"],
                               6.181342900000129e-6)

    def test_raw_phase_inconsistency_not_declared_physical_pass(self):
        r = self.report
        self.assertFalse(r["source_reported_flags"]["case_modified"])
        self.assertFalse(r["source_reported_flags"]["solver_rerun"])
        self.assertTrue(
            r["source_reported_flags"]["no_global_phase_boundedness_claim"])
        self.assertTrue(
            r["source_reported_flags"]["not_a_geometric_interface_classification"])
        self.assertIn("global phase-allocation gate FAIL",
                      r["scientific_conclusion"])


if __name__ == "__main__":
    unittest.main()
