#!/usr/bin/env python3
"""Static provenance regression; never run CFD or claim energy solver validation."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cases_controlled_buoyancy"
REPORT = ROOT / "docs/granada/B11_C11_ENERGY2_DOCUMENTATION_AUDIT_20261021.md"


def active_energy_correctors(text):
    # Strip C++ block and // comments before finding real OpenFOAM entries.
    no_blocks = re.sub(r"/\*[\s\S]*?\*/", "", text)
    no_comments = re.sub(r"(?m)//.*$", "", no_blocks)
    return re.findall(r"\bnEnergyCorrectors\s+([0-9]+)\s*;", no_comments)


class Energy2Provenance(unittest.TestCase):
    def test_source_difference_is_explicit_and_historical_docs_are_contextualized(self):
        for family in ("B11", "C11"):
            with self.subTest(family=family):
                experimental = BASE / (family + "_energy2_test")
                reference = BASE / (family + "_topFixedFlux_airGapOF14")
                e_doc = (experimental / "CASE_VARIANT.md").read_text(encoding="utf-8")
                r_doc = (reference / "CASE_VARIANT.md").read_text(encoding="utf-8")
                e_conf = (experimental / "system/fvSolution").read_text(encoding="utf-8")
                r_conf = (reference / "system/fvSolution").read_text(encoding="utf-8")
                self.assertEqual(active_energy_correctors(e_conf), ["2"])
                self.assertEqual(active_energy_correctors(r_conf), [])
                self.assertNotEqual(e_doc, r_doc)
                self.assertIn("provenance clarification", e_doc)
                self.assertIn("not proof", e_doc)
                self.assertIn("Preserved baseline description", e_doc)
                self.assertIn("RUN-VERIFIED + ANALYSIS-VERIFIED", e_doc)
                self.assertIn("B11_C11_ENERGY2_DOCUMENTATION_AUDIT_20261021.md", e_doc)
    def test_research_audit_is_present_and_not_claiming_physical_validation(self):
        report=REPORT.read_text(encoding="utf-8")
        self.assertIn("NOT VERIFIED",report)
        self.assertIn("No modificar",report)
        self.assertIn("nEnergyCorrectors",report)

if __name__=="__main__":
    unittest.main()
