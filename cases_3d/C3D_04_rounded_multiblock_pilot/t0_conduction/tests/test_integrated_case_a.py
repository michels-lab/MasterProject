#!/usr/bin/env python3
"""One integrated static regression suite for CASE A T0; never calls OpenFOAM."""
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

CASE_A = pathlib.Path(__file__).resolve().parents[2]
T0 = CASE_A / "t0_conduction"
SCRIPTS = T0 / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(CASE_A / "scripts"))

import prepare_case_a_t0 as engine
import report_case_a_progress as progress


class IntegratedCaseAT0(unittest.TestCase):
    def test_01_progress_is_consistent_and_canonical(self):
        status = progress.report(progress.STATUS_FILE)
        self.assertEqual(status["current_stage"], "05_THERMAL_T0_DESIGN")
        self.assertEqual(status["progress_count_done"], 4)
        self.assertEqual(status["progress_count_total"], 10)
        self.assertEqual(status["progress_percent"], 40)
        self.assertFalse(status["CFD_run"])
        self.assertFalse(status["grid_independence"])
        self.assertFalse(status["physical_validation"])
        with tempfile.TemporaryDirectory() as folder:
            p = pathlib.Path(folder) / "status.json"
            bad = copy.deepcopy(status)
            bad["progress_percent"] = 90
            p.write_text(json.dumps(bad))
            with self.assertRaises(AssertionError):
                progress.report(p)

    def test_02_real_inputs_are_strictly_blocked_until_sourced(self):
        cfg = json.loads(engine.INPUTS.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(engine.validate(cfg)), 15)
        self.assertFalse(engine.positive(None))
        self.assertFalse(engine.positive(float("nan")))
        self.assertFalse(engine.positive(True))
        self.assertFalse(engine.positive(0))
        with self.assertRaises(ValueError):
            engine.generate(cfg)

    def test_03_all_nine_thermal_dictionaries_generated_from_synthetic_fixture(self):
        cfg = engine.synthetic_fixture()
        self.assertEqual(engine.validate(cfg, allow_synthetic_test=True), [])
        self.assertNotEqual(engine.validate(cfg), [])
        items = engine.generate(cfg)
        self.assertEqual(len(items), 9)
        self.assertEqual(set(items), {
            "0/metal/T", "0/mold/T",
            "constant/metal/physicalProperties", "constant/mold/physicalProperties",
            "system/controlDict",
            "system/metal/fvSchemes", "system/metal/fvSolution",
            "system/mold/fvSchemes", "system/mold/fvSolution",
        })
        for name, content in items.items():
            self.assertNotIn("{{", content, name)
            self.assertNotIn("C3D-05", content, name)
            self.assertEqual(content.count("{"), content.count("}"), name)
        self.assertIn("application foamMultiRun;", items["system/controlDict"])
        self.assertIn("metal solid;", items["system/controlDict"])
        self.assertIn("mold solid;", items["system/controlDict"])
        self.assertIn("nNonOrthogonalCorrectors 2;", items["system/metal/fvSolution"])
        self.assertIn("constIsoSolid", items["constant/metal/physicalProperties"])

    def test_04_validate_actual_C3D04_patch_contract_without_a_mesh(self):
        cfg = engine.synthetic_fixture()
        items = engine.generate(cfg)
        self.assertEqual(set(engine.EXTERIOR["metal"]), {"metalTop"})
        self.assertEqual(set(engine.EXTERIOR["mold"]), {
            "moldTop", "moldExterior", "moldBottom",
            "moldRecessWall", "moldRecessRoof"
        })
        for region in ("metal", "mold"):
            field = items[f"0/{region}/T"]
            self.assertEqual(field.count("type coupledTemperature;"), 1)
            self.assertEqual(field.count("type zeroGradient;"), len(engine.EXTERIOR[region]))
            for patch in engine.EXTERIOR[region] + (engine.COUPLED[region],):
                self.assertIn(patch + "\n", field)
        self.assertNotIn("moldOuterUnclassified", items["0/mold/T"])
        self.assertNotIn("type patch;", items["0/metal/T"])

    def test_05_negative_cases_and_isolation(self):
        cfg = engine.synthetic_fixture()
        cfg["metal"]["source_rho"] = None
        self.assertTrue(any("source_rho" in e for e in engine.validate(cfg)))
        cfg["metal"]["source_rho"] = "SYNTHETIC_UNIT_TEST"
        cfg["simulation"]["nNonOrthogonalCorrectors"] = -1
        self.assertTrue(any("nNonOrthogonalCorrectors" in e for e in engine.validate(cfg)))
        cfg["simulation"]["nNonOrthogonalCorrectors"] = 2
        cfg["mold"]["T_initial_K"] = cfg["metal"]["T_initial_K"]
        self.assertTrue(any("T_initial_K" in e for e in engine.validate(cfg)))
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder)/"reference"
            source.mkdir()
            with self.assertRaises(ValueError):
                engine.isolated_output(source, source)
            with self.assertRaises(ValueError):
                engine.isolated_output(source, source/"nested")
            with self.assertRaises(ValueError):
                engine.isolated_output(source, source.parent)
            existing = pathlib.Path(folder)/"present"
            existing.mkdir()
            with self.assertRaises(FileExistsError):
                engine.isolated_output(source, existing)

    def test_06_no_CFD_or_remeshing_launched_by_integrated_runner(self):
        runner = (T0/"run_integrated_milestone.sh").read_text()
        self.assertIn("report_case_a_progress.py", runner)
        self.assertIn("prepare_case_a_t0.py", runner)
        self.assertNotIn("blockMesh -case", runner)
        self.assertNotIn("checkMesh -case", runner)
        self.assertNotIn("foamMultiRun -case", runner)
        self.assertNotIn("rm -rf", runner)
        self.assertIn("--preflight", runner)


if __name__ == "__main__":
    unittest.main()
