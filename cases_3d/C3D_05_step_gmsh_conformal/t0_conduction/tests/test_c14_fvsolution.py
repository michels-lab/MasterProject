#!/usr/bin/env python3
"""C14 -> C3D05 T0 fvSolution provenance and regression. No OpenFOAM or CFD."""
import importlib.util
import json
from pathlib import Path
import re
import unittest
from unittest import mock

T0 = Path(__file__).resolve().parents[1]
REPO = T0.parents[2]
SPEC = importlib.util.spec_from_file_location("c14_b_t0", T0 / "scripts/prepare_t0.py")
PREP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREP)

def strip_comments(text):
    return re.sub(r"//[^\n]*", "", re.sub(r"/\*[\s\S]*?\*/", "", text))

def block(text, key):
    src = strip_comments(text)
    start = re.search((r"\b" if key[0].isalnum() or key[0] == "_" else "") + re.escape(key) + r"\s*\{", src)
    if not start:
        raise ValueError("Missing dictionary: " + key)
    count = 1
    idx = start.end()
    while idx < len(src) and count:
        if src[idx] == "{": count += 1
        elif src[idx] == "}": count -= 1
        idx += 1
    if count:
        raise ValueError("Unclosed dictionary " + key)
    return src[start.end():idx-1]

def scalar(text, name):
    m = re.search(r"(?m)^\s*" + re.escape(name) + r"\s+([A-Za-z0-9_.+-]+)\s*;", text)
    if not m:
        raise ValueError("Missing scalar: " + name)
    return m.group(1)

class C14FVSolution(unittest.TestCase):
    def source(self, rel):
        return (REPO / "cases_controlled_buoyancy/C14_topFixedFlux_explicitRef" / rel).read_text(encoding="utf-8")

    def test_versioned_sha_all_three(self):
        PREP.verify_c14_fvsolution_source()
        doc = json.loads((T0 / "C14_FVSOLUTION_PROVENANCE.json").read_text())
        self.assertEqual(len(doc["sources"]), 3)

    def test_global_from_c14(self):
        parent = block(self.source("system/fvSolution"), "PIMPLE")
        current = block((T0 / "templates/system/fvSolution.tpl").read_text(), "PIMPLE")
        for name in ("nOuterCorrectors", "nCorrectors", "nNonOrthogonalCorrectors"):
            self.assertEqual(scalar(parent, name), scalar(current, name))
        origin = block(block(self.source("system/fvSolution"), "relaxationFactors"), "equations")
        now = block(block((T0 / "templates/system/fvSolution.tpl").read_text(), "relaxationFactors"), "equations")
        for name in ("e", "eFinal"):
            self.assertEqual(float(scalar(origin, name)), float(scalar(now, name)))

    def test_solid_thermal_solver_both_from_mold_c14(self):
        original = self.source("system/mold/fvSolution")
        solver = block(block(original, "solvers"), '"(h|e)"')
        source_pimple = block(original, "PIMPLE")
        for region in ("metal", "mold"):
            current = (T0 / f"templates/system/{region}/fvSolution.tpl").read_text()
            thermal = block(block(current, "solvers"), "e")
            for field in ("solver", "preconditioner", "tolerance", "relTol"):
                self.assertEqual(scalar(solver, field), scalar(thermal, field))
            self.assertIn("$e;", block(block(current, "solvers"), "eFinal"))
            pimple = block(current, "PIMPLE")
            for field in ("nOuterCorrectors", "nCorrectors", "nNonOrthogonalCorrectors"):
                self.assertEqual(scalar(source_pimple, field), scalar(pimple, field))
            self.assertNotIn("p_rgh", strip_comments(current))
            self.assertNotIn("momentumPredictor", current)

    def test_two_energy_correctors_trace_to_c14_metal(self):
        metal = block(self.source("system/metal/fvSolution"), "PIMPLE")
        current = block((T0 / "templates/system/fvSolution.tpl").read_text(), "PIMPLE")
        self.assertEqual(scalar(metal, "nEnergyCorrectors"), scalar(current, "nEnergyCorrectors"))

    def test_source_change_rejected_even_when_comments_only(self):
        original = Path.read_bytes
        def fake_read(path):
            result = original(path)
            if str(path).endswith("C14_topFixedFlux_explicitRef/system/mold/fvSolution"):
                return result + b"// altered\n"
            return result
        with mock.patch.object(Path, "read_bytes", fake_read):
            with self.assertRaisesRegex(ValueError, "changed"):
                PREP.verify_c14_fvsolution_source()

    def test_generator_contains_correct_solid_fields(self):
        cfg = json.loads((T0 / "T0_INPUTS.json").read_text())
        for region, temp in (("metal", 1500), ("mold", 300)):
            cfg[region].update({
                "rho_kg_m3": 6820, "Cv_J_kg_K": 827,
                "kappa_W_m_K": 20, "molWeight_g_mol": 56, "T_initial_K": temp,
                "source_rho": "SYNTHETIC_UNIT_TEST", "source_Cv": "SYNTHETIC_UNIT_TEST",
                "source_kappa": "SYNTHETIC_UNIT_TEST", "source_molWeight": "SYNTHETIC_UNIT_TEST",
                "source_T_initial": "SYNTHETIC_UNIT_TEST",
            })
        cfg["simulation"].update({
            "deltaT_s": 0.01, "endTime_s": 0.1, "writeEverySteps": 2,
            "source_time_choices": "SYNTHETIC_UNIT_TEST",
        })
        files = PREP.file_map(cfg)
        self.assertEqual(len(files), 10)
        for region in ("metal", "mold"):
            field = files[f"system/{region}/fvSolution"]
            self.assertIn("solver PCG;", field)
            self.assertNotIn("p_rgh", strip_comments(field))

if __name__ == "__main__":
    unittest.main()
