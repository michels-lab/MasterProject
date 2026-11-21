"""Synthetic read-only FS-C02 thermal/alpha trace tests; zero CFD runs."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from inspect_fs_c02_thermal import classify, inspect
from audit_fs_c02_local import EXPECTED_CELLS
from run_fs_c02_local import stage


def scalar_file(name: str, values: list[float]) -> str:
    return (
        "FoamFile { class volScalarField; object " + name + "; }\n"
        "dimensions [];\n"
        "internalField nonuniform List<scalar>\n"
        + str(len(values)) + "\n(\n"
        + "\n".join(str(x) for x in values) + "\n);\n"
        + "boundaryField {}\n"
    )


class ThermalTraceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fs-c02-thermal-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "FS-C02_EXTENDED_synthetic"
        self.case, s = stage(self.run, extended_probe=True)
        s["status"] = "PROBE_COURANT_SCREEN_PASSED"
        s["solver_tested_on_real_openfoam"] = True
        (self.run / "FS-C02_RUN_STATUS.json").write_text(json.dumps(s))
        self.alpha = [1.0]*6400 + [0.5]*200 + [0.0]*(EXPECTED_CELLS-6600)
        self.temp_values = [1500.0]*6400 + [900.0]*200 + [300.0]*(EXPECTED_CELLS-6600)
        self.times = (0.001, 0.005, 0.01)
        for t in self.times:
            folder = self.case / str(t)
            folder.mkdir()
            (folder/"alpha.metal").write_text(scalar_file("alpha.metal", self.alpha))
            (folder/"T").write_text(scalar_file("T", self.temp_values))

    def test_classifies_only_significant_mixed_cells(self):
        r = classify(self.alpha, self.temp_values)
        self.assertEqual(r["gas_like_alpha_le_0_01"]["cell_count"], EXPECTED_CELLS-6600)
        self.assertEqual(r["interface_like_alpha_0_01_to_0_99"]["cell_count"], 200)
        self.assertEqual(r["metal_like_alpha_ge_0_99"]["cell_count"], 6400)
        self.assertEqual(r["gas_like_alpha_le_0_01"]["temperature_mean_K"], 300)
        self.assertEqual(r["interface_like_alpha_0_01_to_0_99"]["temperature_mean_K"], 900)
        self.assertEqual(r["metal_like_alpha_ge_0_99"]["temperature_mean_K"], 1500)
        self.assertGreater(r["T_gas_weighted_mean_K"], 300)
        self.assertFalse(r["interface_cell_T_represents_both_phase_temperatures"])
        self.assertFalse(r["bulk_gas_mean_is_physical_gas_temperature"])

    def test_three_snapshots_trace_does_not_write_report_or_modify_fields(self):
        field = self.case/"0.01"/"T"
        original = field.read_bytes()
        r = inspect(self.run)
        self.assertEqual(r["status"], "DIAGNOSTIC_RECORDED_PHYSICS_UNVERIFIED")
        self.assertEqual(r["snapshots_analyzed"], 3)
        self.assertEqual(r["first_saved_time_s"], .001)
        self.assertEqual(r["last_saved_time_s"], .01)
        self.assertEqual(r["final_gas_like_mean_T_K"], 300)
        self.assertEqual(r["final_interface_like_mean_T_K"], 900)
        self.assertEqual(r["final_metal_like_mean_T_K"], 1500)
        self.assertEqual(len(r["records"]), 3)
        self.assertEqual(field.read_bytes(), original)
        self.assertEqual(list(self.root.iterdir()), [self.run])

    def test_final_missing_T_fails_instead_of_faking_temperature(self):
        (self.case/"0.01"/"T").unlink()
        with self.assertRaisesRegex(ValueError, "final T field missing"):
            inspect(self.run)

    def test_nonphysical_temperature_rejected(self):
        temp = self.temp_values.copy()
        temp[1] = -5
        (self.case/"0.01"/"T").write_text(scalar_file("T", temp))
        with self.assertRaisesRegex(ValueError, "invalid temperature"):
            inspect(self.run)

    def test_changed_original_input_rejected(self):
        (self.case/"system"/"controlDict").write_text("changed")
        with self.assertRaisesRegex(ValueError, "modified original solver input"):
            inspect(self.run)

    def test_wrong_case_status_rejected(self):
        sfile = self.run/"FS-C02_RUN_STATUS.json"
        s = json.loads(sfile.read_text())
        s["status"] = "PROBE_REVIEW_COURANT"
        sfile.write_text(json.dumps(s))
        with self.assertRaisesRegex(ValueError, "extended solver gate"):
            inspect(self.run)

    def test_roundoff_tails_not_counted_as_interfacial_cells(self):
        a = self.alpha.copy()
        a[7000] = 1e-26
        a[3000] = 1-1e-12
        r = classify(a, self.temp_values)
        self.assertEqual(r["interface_like_alpha_0_01_to_0_99"]["cell_count"], 200)
        self.assertEqual(r["alpha_strictly_between_zero_one_count"], 202)

    def test_missing_positive_times_rejected(self):
        for t in self.times[:2]:
            folder = self.case/str(t)
            (folder/"alpha.metal").unlink()
            (folder/"T").unlink()
            folder.rmdir()
        with self.assertRaisesRegex(ValueError, "need >=3"):
            inspect(self.run)


if __name__ == "__main__":
    unittest.main()
