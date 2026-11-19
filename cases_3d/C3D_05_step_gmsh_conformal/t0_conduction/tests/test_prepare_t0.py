#!/usr/bin/env python3
"""T0 strict test-only Python: no OpenFOAM, no CFD, no material measurements."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "scripts" / "prepare_t0.py"
SPEC = importlib.util.spec_from_file_location("c3d05_t0_prepare", SRC)
T0 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(T0)


def example_config():
    # Pure synthetic *unit-test fixtures*, not physical cast-iron/sand inputs.
    cfg = json.loads((ROOT / "T0_INPUTS.json").read_text())
    for name in ("metal", "mold"):
        cfg[name].update({
            "rho_kg_m3": 1.0, "Cv_J_kg_K": 2.0,
            "kappa_W_m_K": 3.0, "molWeight_g_mol": 4.0,
            "T_initial_K": 5.0 if name == "metal" else 6.0,
            "source_rho": "SYNTHETIC_UNIT_TEST",
            "source_Cv": "SYNTHETIC_UNIT_TEST",
            "source_kappa": "SYNTHETIC_UNIT_TEST",
            "source_molWeight": "SYNTHETIC_UNIT_TEST",
            "source_T_initial": "SYNTHETIC_UNIT_TEST",
        })
    cfg["simulation"].update({
        "deltaT_s": 0.01, "endTime_s": 0.1, "writeEverySteps": 2,
        "source_time_choices": "SYNTHETIC_UNIT_TEST",
    })
    return cfg


class StrictT0(unittest.TestCase):
    def test_unfilled_defaults_are_intentionally_blocked(self):
        cfg = json.loads((ROOT / "T0_INPUTS.json").read_text())
        errors = T0.validate(cfg)
        self.assertGreater(len(errors), 10)
        self.assertTrue(any("metal.rho_kg_m3" in x for x in errors))
        self.assertTrue(any("mold.source_T_initial" in x for x in errors))
        self.assertTrue(any("simulation.deltaT_s" in x for x in errors))

    def test_synthetic_fixture_validates_without_fake_material_claim(self):
        cfg = example_config()
        self.assertEqual(T0.validate(cfg), [])
        items = T0.file_map(cfg)
        self.assertEqual(len(items), 10)
        self.assertIn("PIMPLE", items["system/fvSolution"])
        self.assertIn("metal           solid;", items["system/controlDict"])
        self.assertIn("mold            solid;", items["system/controlDict"])
        self.assertIn("application     foamMultiRun;", items["system/controlDict"])
        self.assertIn("deltaT          0.01;", items["system/controlDict"])
        self.assertIn("Cv          2;", items["constant/metal/physicalProperties"])
        self.assertIn("type            coupledTemperature;", items["0/metal/T"])
        self.assertIn("metalTop", items["0/metal/T"])
        self.assertIn("moldOuterUnclassified", items["0/mold/T"])
        self.assertFalse(any("{{" in text for text in items.values()))
        self.assertFalse(any("}}" in text for text in items.values()))

    def test_missing_single_source_provenance_stays_blocked(self):
        cfg = example_config()
        cfg["metal"]["source_T_initial"] = None
        self.assertTrue(any("metal.source_T_initial" in x for x in T0.validate(cfg)))
        cfg = example_config()
        cfg["mold"]["source_kappa"] = ""
        self.assertTrue(any("mold.source_kappa" in x for x in T0.validate(cfg)))

    def test_missing_boundary_ack_or_nonpositive_data_reject(self):
        cfg = example_config()
        cfg["thermal_BC_hypothesis"] = "unknown"
        cfg["metal"]["Cv_J_kg_K"] = -10
        cfg["mold"]["T_initial_K"] = cfg["metal"]["T_initial_K"]
        errs = T0.validate(cfg)
        self.assertTrue(any("thermal_BC_hypothesis" in x for x in errs))
        self.assertTrue(any("Cv_J_kg_K" in x for x in errs))
        self.assertTrue(any("T_initial_K must differ" in x for x in errs))

    def test_template_placeholders_are_exact_not_silently_skipped(self):
        with self.assertRaises(ValueError):
            T0.render("{{T_INITIAL}}", {})
        with self.assertRaises(ValueError):
            T0.render("no placeholders", {"T_INITIAL": "50"})


if __name__ == "__main__":
    unittest.main()
