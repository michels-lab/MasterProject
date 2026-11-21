"""FS-C06 density screen numerical/provenance tests: synthetic, NO CFD."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from screen_fs_c06_density_contraction import (
    DENSITY_SCHEMA, NATIVE_STATUS, audit, check_native_report,
    read_density_law, screen_inventories
)


SHA = "a" * 64


def native_report(solid=0.2):
    def snap(t):
        return {
            "time_s": t,
            "cell_volume_weighted_not_cell_sum": True,
            "solid_fraction_within_metal_vof": True,
            "temperature_field_for_solidification": "T.metal",
            "alpha_metal_sha256": SHA,
            "alpha_metal_solid_sha256": SHA,
            "temperature_sha256": SHA,
            "metal_vof_volume_m3": 1.0,
            "metal_solid_volume_m3": solid,
            "metal_liquid_volume_m3": 1.0-solid,
            "metal_T_mean_K_alpha_volume_weighted": 1450.0,
        }
    return {
        "status": NATIVE_STATUS,
        "native_cfd_executed": True,
        "model_loaded_native": True,
        "solid_fraction_fields_measured": True,
        "model_field_expected": "alpha.metal.solid",
        "native_fraction_diagnostics": {
            "native_solid_fraction_observed": True,
            "volumes_from_native_fluid_mesh": True,
            "initial_metal_vof_volume_m3": 1.0,
            "snapshots": [snap(1e-7), snap(2e-7)],
        }
    }


class DensityScreenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.report = base / "FS_C06_REPORT.json"
        self.spec = base / "density.json"
        self.source = base / "original-jmatpro-export.txt"
        self.output = base / "separate-screen.json"
        self.source.write_text("SYNTHETIC ONLY: no material properties measured\n")
        self.report.write_text(json.dumps(native_report()))
        self.law = {
            "schema": DENSITY_SCHEMA,
            "material_id": "test-cast-iron-not-calibrated",
            "source_kind": "jmatpro_export",
            "source_reference": "Synthetic test fixture ONLY",
            "source_file_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "rho_liquid_kg_m3": 6900,
            "rho_solid_kg_m3": 7200,
            "density_reference_temperature_K": 1450,
            "graphitization_handling": "not_modelled",
        }
        self.spec.write_text(json.dumps(self.law))

    def test_density_increases_contracts_only_under_fixed_mass_hypothesis(self):
        result = audit(self.report, self.spec, self.source, self.output)
        x = result["snapshots"][0]
        self.assertGreater(x["closed_fixed_mass_signed_contraction_relative_initial"], 0)
        self.assertLess(x["closed_fixed_mass_hypothesis_volume_m3"], 1)
        self.assertGreater(x["inferred_metal_mass_proxy_change_from_initial_kg"], 0)
        self.assertFalse(x["metal_mass_conservation_verified"])
        self.assertFalse(x["physical_volumetric_shrinkage_verified"])
        self.assertFalse(result["density_coupled_into_solver"])
        self.assertTrue(self.output.is_file())

    def test_equal_density_is_zero_signed_volume_effect(self):
        _, snaps = check_native_report(native_report())
        d = {"rho_liquid_kg_m3": 7000, "rho_solid_kg_m3": 7000}
        x = screen_inventories(1.0, snaps, d)[0]
        self.assertAlmostEqual(x["closed_fixed_mass_hypothesis_volume_m3"], 1.0)
        self.assertAlmostEqual(x["closed_fixed_mass_signed_contraction_relative_initial"], 0)
        self.assertAlmostEqual(x["inferred_metal_mass_proxy_change_from_initial_kg"], 0)

    def test_graphite_like_effective_lower_solid_density_expands_hypothesis(self):
        _, snaps = check_native_report(native_report())
        d = {"rho_liquid_kg_m3": 7000, "rho_solid_kg_m3": 6750}
        x = screen_inventories(1.0, snaps, d)[0]
        self.assertLess(x["closed_fixed_mass_signed_contraction_relative_initial"], 0)
        self.assertFalse(x["physical_volumetric_shrinkage_verified"])

    def test_no_solid_two_steps_cannot_claim_contraction(self):
        _, snaps = check_native_report(native_report(solid=0))
        d = {"rho_liquid_kg_m3": 6900, "rho_solid_kg_m3": 7300}
        x = screen_inventories(1.0, snaps, d)[0]
        self.assertEqual(x["closed_fixed_mass_signed_contraction_relative_initial"], 0)
        self.assertFalse(x["feeding_verified"])

    def test_reject_false_native_and_wrong_temperature(self):
        for key, value in (("native_cfd_executed", False),
                           ("model_loaded_native", False),
                           ("solid_fraction_fields_measured", False)):
            x = native_report()
            x[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                check_native_report(x)
        x = native_report()
        x["native_fraction_diagnostics"]["snapshots"][0][
            "temperature_field_for_solidification"] = "T"
        with self.assertRaises(ValueError):
            check_native_report(x)

    def test_reject_phase_volume_fraud_and_missing_native_hash(self):
        x = native_report()
        snap = x["native_fraction_diagnostics"]["snapshots"][1]
        snap["metal_liquid_volume_m3"] = 0.7
        with self.assertRaises(ValueError):
            check_native_report(x)
        x = native_report()
        x["native_fraction_diagnostics"]["snapshots"][0][
            "alpha_metal_solid_sha256"] = "missing"
        with self.assertRaises(ValueError):
            check_native_report(x)

    def test_original_density_export_hash_cannot_be_faked(self):
        x = read_density_law(self.spec, self.source)
        self.assertEqual(x["rho_liquid_kg_m3"], 6900)
        self.source.write_text("changed physical provenance")
        with self.assertRaises(ValueError):
            read_density_law(self.spec, self.source)

    def test_missing_or_untraceable_density_rejected(self):
        for key, bad in (("rho_solid_kg_m3", 0),
                         ("rho_liquid_kg_m3", float("nan")),
                         ("source_file_sha256", "fake"),
                         ("graphitization_handling", None),
                         ("source_reference", ""),
                         ("source_kind", "unknown")):
            spec = dict(self.law)
            spec[key] = bad
            self.spec.write_text(json.dumps(spec))
            with self.subTest(key=key), self.assertRaises(ValueError):
                read_density_law(self.spec, self.source)

    def test_no_overwrite_and_no_cfd_invoked(self):
        self.output.write_text("sentinel")
        with self.assertRaises(ValueError):
            audit(self.report, self.spec, self.source, self.output)
        self.assertEqual(self.output.read_text(), "sentinel")
        self.output.unlink()
        audit(self.report, self.spec, self.source, self.output)
        with self.assertRaises(ValueError):
            audit(self.report, self.spec, self.source, self.output)


if __name__ == "__main__":
    unittest.main()
