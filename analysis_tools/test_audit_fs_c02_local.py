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
        self.assertIn("Courant max exceeds acceptance Co 0.25", r["alerts"])

    def make_extended_case(self, status_name="PROBE_COURANT_SCREEN_PASSED"):
        """New isolated synthetic 0.01 s run: never mutate original test run."""
        root = self.root / "FS-C02_EXTENDED_synthetic"
        case, record = stage(root, extended_probe=True)
        record["status"] = status_name
        record["solver_tested_on_real_openfoam"] = True
        record["stages"] = [
            {"stage": s, "returncode": 0, "gate_passed": True}
            for s in ("blockMesh", "checkMesh", "foamRun")
        ]
        (root / "FS-C02_RUN_STATUS.json").write_text(json.dumps(record) + "\n")
        volume = case / "postProcessing/metalVolume/0/volFieldValue.dat"
        volume.parent.mkdir(parents=True)
        volume.write_text(
            "# Time volIntegrate(alpha.metal)\n"
            f"0 {INITIAL_VOLUME}\n"
            f"0.001 {INITIAL_VOLUME}\n"
            f"0.01 {INITIAL_VOLUME}\n"
        )
        tdir = case / "0.01"
        tdir.mkdir()
        alpha_values = ["1"]*6400 + ["0"]*(EXPECTED_CELLS-6400)
        (tdir / "alpha.metal").write_text(
            "FoamFile { class volScalarField; object alpha.metal; }\n"
            "internalField nonuniform List<scalar>\n"
            f"{EXPECTED_CELLS}\n(\n" + "\n".join(alpha_values)
            + "\n);\nboundaryField {}\n"
        )
        temperature_values = ["1500"]*6400 + ["300"]*(EXPECTED_CELLS-6400)
        (tdir / "T").write_text(
            "FoamFile { class volScalarField; object T; }\n"
            "internalField nonuniform List<scalar>\n"
            f"{EXPECTED_CELLS}\n(\n" + "\n".join(temperature_values)
            + "\n);\nboundaryField {}\n"
        )
        log = root / "logs/FS-C02_foamRun.log"
        log.write_text(
            "Time = 0.001s\n"
            "Courant Number mean: 0.01 max: 0.163617\n"
            "Interface Courant Number mean: 0.0 max: 0.009\n"
            "Time = 0.01s\n"
            "Courant Number mean: 0.01 max: 0.10\n"
            "Interface Courant Number mean: 0.0 max: 0.009\nEnd\n"
        )
        return root, case, log

    def test_extended_001s_profile_is_validated_separately(self):
        root, _, _ = self.make_extended_case()
        r = audit(root, self.root / "extended_report")
        self.assertEqual(r["status"], "NUMERICAL_SCREEN_PASSED")
        self.assertEqual(r["execution_profile"],
                         "EXTENDED_PROBE_0_01S_TIGHTER_CO")
        self.assertEqual(r["expected_end_time_s"], .01)
        self.assertEqual(r["controller_target_maxCo"], .15)
        self.assertEqual(r["acceptance_maxCo"], .20)
        self.assertEqual(r["last_time_s"], .01)
        self.assertEqual(r["max_courant_over_log"], .163617)
        self.assertAlmostEqual(
            r["temperature_screen"]["metal_weighted_mean_T_K"], 1500
        )
        self.assertAlmostEqual(
            r["temperature_screen"]["air_weighted_mean_T_K"], 300
        )
        self.assertTrue(r["physical_mass_balance_not_verified"])
        self.assertTrue(r["temperature_screen"]["thermal_energy_balance_verified"] is False)
        self.assertTrue(r["shrinkage_not_modelled"])

    def test_extended_courant_over_02_fails_even_with_lower_target(self):
        root, _, log = self.make_extended_case()
        log.write_text(
            "Courant Number mean: 0.01 max: 0.21\n"
            "Interface Courant Number mean: 0 max: 0.009\nEnd\n"
        )
        r = audit(root, self.root / "extended_high_co")
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("Courant max exceeds acceptance Co 0.2", r["alerts"])

    def test_extended_profile_requires_temperature_field(self):
        root, case, _ = self.make_extended_case()
        (case / "0.01/T").unlink()
        r = audit(root, self.root / "extended_no_t")
        self.assertEqual(r["status"], "REVIEW")
        self.assertIn("final T field missing in extended probe", r["alerts"])

    def test_extended_status_profile_tampering_rejected(self):
        root, _, _ = self.make_extended_case()
        path = root / "FS-C02_RUN_STATUS.json"
        r = json.loads(path.read_text())
        r["extended_probe"] = False
        path.write_text(json.dumps(r) + "\n")
        with self.assertRaisesRegex(ValueError, "probe status"):
            audit(root, self.root / "tampered_status")

    def test_extended_profile_end_time_is_enforced(self):
        root, case, _ = self.make_extended_case()
        volume = case / "postProcessing/metalVolume/0/volFieldValue.dat"
        volume.write_text(
            "# Time volIntegrate(alpha.metal)\n"
            f"0 {INITIAL_VOLUME}\n"
            f"0.005 {INITIAL_VOLUME}\n"
        )
        # Disagreeing saved field time is a hard failure, not a fabricated match.
        with self.assertRaisesRegex(ValueError, "last saved alpha time"):
            audit(root, self.root / "inconsistent_end_time")

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
