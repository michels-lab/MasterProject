#!/usr/bin/env python3
"""Regression of archived C14 material reference, NO CFD, NO JMatPro measurements."""
import copy
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

T0 = Path(__file__).resolve().parents[1]
module_path = T0 / "scripts/c14_numerical_reference.py"
spec = importlib.util.spec_from_file_location("case_b_reference", module_path)
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)

prep_spec = importlib.util.spec_from_file_location("case_b_prepare_reference_check", T0 / "scripts/prepare_t0.py")
prep = importlib.util.module_from_spec(prep_spec)
prep_spec.loader.exec_module(prep)


class C14NumericalReference(unittest.TestCase):
    def test_original_archived_values_are_exact_and_explicitly_hypothetical(self):
        cfg = reference.build()
        self.assertEqual(cfg["metal"]["rho_kg_m3"], 6820)
        self.assertEqual(cfg["metal"]["Cv_J_kg_K"], 827)
        self.assertAlmostEqual(cfg["metal"]["kappa_W_m_K"], 827 * 0.0055 / 0.14)
        self.assertEqual(cfg["metal"]["T_initial_K"], 1500)
        self.assertEqual(cfg["mold"]["rho_kg_m3"], 1500)
        self.assertEqual(cfg["mold"]["Cv_J_kg_K"], 700)
        self.assertEqual(cfg["mold"]["kappa_W_m_K"], 2)
        self.assertEqual(cfg["mold"]["molWeight_g_mol"], 28)
        self.assertEqual(cfg["mold"]["T_initial_K"], 300)
        self.assertEqual(cfg["simulation"]["deltaT_s"], 0.001)
        self.assertEqual(cfg["simulation"]["endTime_s"], 0.1)
        self.assertEqual(cfg["simulation"]["writeEverySteps"], 20)
        self.assertIn("NOT_JMATPRO", cfg["reference_profile"])
        self.assertIn("Cp approximated as Cv", cfg["metal"]["source_Cv"])
        self.assertIn("100", cfg["simulation"]["source_time_choices"])
        self.assertEqual(len(cfg["reference_source_sha256"]), 5)
        self.assertEqual(reference.validate_reference(cfg), [])
        self.assertEqual(prep.validate(cfg), [])
        self.assertEqual(len(prep.file_map(cfg)), 10)

    def test_tampered_numerical_input_cannot_be_materialized(self):
        data = reference.build()
        data["metal"]["Cv_J_kg_K"] = 900
        self.assertTrue(reference.validate_reference(data))
        with self.assertRaisesRegex(ValueError, "Invalid archived C14 numerical"):
            prep.file_map(data)

    def test_fake_source_sha_rejected(self):
        data = reference.build()
        first = next(iter(data["reference_source_sha256"]))
        data["reference_source_sha256"][first] = "0" * 64
        self.assertTrue(reference.validate_reference(data))
        with self.assertRaisesRegex(ValueError, "Invalid archived C14 numerical"):
            prep.file_map(data)

    def test_unknown_profile_rejected(self):
        data = reference.build()
        data["reference_profile"] = "LAB_MEASUREMENTS_CONFIRMED"
        with self.assertRaisesRegex(ValueError, "Invalid archived C14 numerical"):
            prep.file_map(data)

    def test_missing_source_fails_closed(self):
        data = reference.build()
        with TemporaryDirectory() as tmp:
            self.assertTrue(reference.validate_reference(data, Path(tmp)))

    def test_exclusive_output_is_idempotent_and_never_overwrites(self):
        cfg = reference.build()
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "reference.json"
            self.assertEqual(reference.write_exclusive(out, cfg), "CREATED_NUMERICAL_REFERENCE_NOT_PHYSICAL_VALIDATION")
            self.assertEqual(reference.write_exclusive(out, cfg), "ALREADY_GENERATED_IDENTICAL")
            out.write_text("PRESERVE USER DATA", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                reference.write_exclusive(out, cfg)
            self.assertEqual(out.read_text(), "PRESERVE USER DATA")

    def test_legacy_incomplete_physical_template_remains_unmodified(self):
        base = json.loads((T0 / "T0_INPUTS.json").read_text(encoding="utf-8"))
        self.assertIsNone(base["metal"]["rho_kg_m3"])
        self.assertIsNone(base["mold"]["Cv_J_kg_K"])
        self.assertNotIn("reference_profile", base)

if __name__ == "__main__":
    unittest.main()
