"""No-CFD FS-C02 audit tests, using only synthetic files with known values."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c02_local import (
    CELL_VOLUME, EXPECTED_CELLS, INITIAL_VOLUME,
    audit, log_courant, read_alpha, read_volume,
)
from run_fs_c02_local import stage


class FSC02AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fs-c02-audit-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "FS-C02_synthetic"
        self.case, self.status = stage(self.run)
        self.status["status"] = "SOLVER_FINISHED_PHYSICS_NOT_VALIDATED"
        self.status["solver_tested_on_real_openfoam"] = True
        self.status["stages"] = [
            {"stage": n, "returncode": 0, "gate_passed": True}
            for n in ("blockMesh", "checkMesh", "foamRun")
        ]
        (self.run / "FS-C02_RUN_STATUS.json").write_text(
            json.dumps(self.status) + "\n")
        self.volfile = self.case / "postProcessing/metalVolume/0/volFieldValue.dat"
        self.volfile.parent.mkdir(parents=True)
        self.volfile.write_text(
            "# Selection : all\n"
            "# Volume : 2.400000e-05\n"
            "# Time volIntegrate(alpha.metal)\n"
            f"0 {INITIAL_VOLUME}\n"
            f"0.05 {INITIAL_VOLUME}\n"
            f"0.1 {INITIAL_VOLUME}\n"
        )
        self.alpha_file = self.case / "0.1/alpha.metal"
        self.alpha_file.parent.mkdir()
        # Realistic mesh alpha array: 6400 metal, 3200 air cells.
        vals = ["1"] * 6400 + ["0"] * (EXPECTED_CELLS - 6400)
        self.alpha_file.write_text(
            "FoamFile { class volScalarField; object alpha.metal; }\n"
            "dimensions [];\n"
            "internalField nonuniform List<scalar>\n"
            + str(EXPECTED_CELLS) + "\n(\n"
            + "\n".join(vals) + "\n);\n"
            "boundaryField {}\n"
        )
        self.log = self.run / "logs/FS-C02_foamRun.log"
        self.log.write_text(
            "Time = 0.05\n"
            "Courant Number mean: 0.001 max: 0.009\n"
            "Interface Courant Number mean: 0.0 max: 0.004\n"
            "Time = 0.1\n"
            "Courant Number mean: 0.001 max: 0.009\n"
            "Interface Courant Number mean: 0.0 max: 0.004\n"
            "End\n"
        )

    def test_provisional_iron_smoke_screen_not_mass_validation(self):
        out = self.root / "report"
        r = audit(self.run, out)
        self.assertEqual(r["status"], "NUMERICAL_SCREEN_PASSED")
        self.assertEqual(r["case_id"], "FS-C02")
        self.assertEqual(r["time_points"], 3)
        self.assertEqual(r["max_relative_volume_drift"], 0)
        self.assertEqual(r["alpha_min"], 0)
        self.assertEqual(r["alpha_max"], 1)
        self.assertEqual(r["alpha_cells"], EXPECTED_CELLS)
        self.assertAlmostEqual(r["last_field_integrated_volume_m3"], INITIAL_VOLUME)
        self.assertAlmostEqual(r["last_mass_kg_DERIVED_NOT_MEASURED"], 0.10912)
        self.assertTrue(r["physical_mass_balance_not_verified"])
        self.assertTrue(r["solidification_not_modelled"])
        self.assertTrue(r["shrinkage_not_modelled"])
        self.assertFalse((self.case / "FS-C02_NUMERICAL_SCREEN.json").exists())
        self.assertTrue((out / "FS-C02_NUMERICAL_SCREEN.json").is_file())

    def test_alpha_overshoot_blocks_numerical_screen(self):
        self.alpha_file.write_text(
            "FoamFile { class volScalarField; object alpha.metal; }\n"
            "internalField uniform 1.02;\n"
            "boundaryField {}\n"
        )
        r = audit(self.run, self.root / "overshoot")
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("alpha.metal outside admissible bounds", r["alerts"])

    def test_volume_drift_blocks(self):
        self.volfile.write_text(
            "# Time volIntegrate(alpha.metal)\n"
            f"0 {INITIAL_VOLUME}\n"
            f"0.1 {INITIAL_VOLUME*0.98}\n"
        )
        r = audit(self.run, self.root / "drift")
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("max volume drift exceeds tolerance", r["alerts"])

    def test_wrong_phase_series_rejected(self):
        self.volfile.write_text(
            "# Time volIntegrate(alpha.water)\n"
            f"0 {INITIAL_VOLUME}\n"
            f"0.1 {INITIAL_VOLUME}\n"
        )
        with self.assertRaisesRegex(ValueError, "must be alpha.metal"):
            read_volume(self.volfile)

    def test_nan_alpha_rejected(self):
        self.alpha_file.write_text(
            "FoamFile { class volScalarField; object alpha.metal; }\n"
            "internalField uniform NaN;\nboundaryField {}\n"
        )
        with self.assertRaisesRegex(ValueError, "unsupported/non-ASCII"):
            read_alpha(self.alpha_file)

    def test_no_false_gate_when_stage_did_not_complete(self):
        s = json.loads((self.run / "FS-C02_RUN_STATUS.json").read_text())
        s["status"] = "BLOCKED_FOAMRUN"
        (self.run / "FS-C02_RUN_STATUS.json").write_text(json.dumps(s))
        with self.assertRaisesRegex(ValueError, "not a completed"):
            audit(self.run, self.root / "blocked")

    def test_manifest_input_tamper_rejected(self):
        (self.case / "system/controlDict").write_text("changed")
        with self.assertRaisesRegex(ValueError, "changed FS-C02 solver input"):
            audit(self.run, self.root / "tamper")

    def test_cannot_overwrite_or_put_report_inside_original_run(self):
        audit(self.run, self.root / "existing")
        with self.assertRaisesRegex(ValueError, "refusing overwrite"):
            audit(self.run, self.root / "existing")
        with self.assertRaisesRegex(ValueError, "separate"):
            audit(self.run, self.run / "FS-C02" / "audit")

    def test_full_run_max_courant_caught_even_if_last_low(self):
        c = log_courant(
            "Courant Number mean: 0.01 max: 0.31\n"
            "Courant Number mean: 0.001 max: 0.001\n"
            "Interface Courant Number mean: 0 max: 0.03\n"
        )
        self.assertEqual(c["max_courant_over_log"], 0.31)
        self.assertEqual(c["last_courant_max"], 0.001)
        self.log.write_text(
            "Courant Number mean: 0.01 max: 0.31\n"
            "Courant Number mean: 0.001 max: 0.001\n"
            "Interface Courant Number mean: 0 max: 0.03\nEnd\n"
        )
        r = audit(self.run, self.root / "highCourant")
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("Courant max exceeds configured maxCo .25", r["alerts"])

    def test_spatial_field_vs_function_disagreement_flagged(self):
        self.alpha_file.write_text(
            "FoamFile { class volScalarField; object alpha.metal; }\n"
            "internalField uniform 0.5;\nboundaryField {}\n"
        )
        r = audit(self.run, self.root / "mismatch")
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("final integrated alpha field does not match volFieldValue", r["alerts"])


if __name__ == "__main__":
    unittest.main()
