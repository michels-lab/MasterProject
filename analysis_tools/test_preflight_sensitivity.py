#!/usr/bin/env python3
"""Synthetic regression tests: no CFD execution, no real case mutation."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from preflight_sensitivity_cases import VARIANTS, audit_all


BASE_CONTROL = """
application foamMultiRun;
endTime 10;
deltaT 0.001;
adjustTimeStep no;
writeControl timeStep;
writeInterval 100;
maxCo 0.25;
maxDeltaT 0.1;
// Appendices may mention adjustTimeStep yes but are comments.
"""
BASE_PHASE = """
phaseChangeSource
{
    type solidificationMeltingSource;
    relax 0.1; // documented value may differ in comments
    Tsol 1423;
    Tliq 1473;
    L 2.286e5;
}
"""


class ControlledVariantPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for parent, child, target, rules in VARIANTS:
            for name in (parent, child):
                path = self.root / name
                (path / "0/metal").mkdir(parents=True, exist_ok=True)
                (path / "system").mkdir(exist_ok=True)
                (path / "constant/metal").mkdir(parents=True, exist_ok=True)
                (path / "0/metal/T").write_text("internalField uniform 1500;\n")
                (path / "Allrun").write_text("#!/bin/sh\nexit 0\n")
                (path / "Allclean").write_text("#!/bin/sh\nexit 0\n")
            (self.root / parent / "system/controlDict").write_text(BASE_CONTROL)
            (self.root / child / "system/controlDict").write_text(
                BASE_CONTROL.replace("adjustTimeStep no;", "adjustTimeStep yes;")
                .replace("writeControl timeStep;", "writeControl adjustableRunTime;")
                .replace("writeInterval 100;", "writeInterval 0.1;")
                if "15_" in child else BASE_CONTROL)
            (self.root / parent / "constant/metal/fvModels").write_text(BASE_PHASE)
            (self.root / child / "constant/metal/fvModels").write_text(
                BASE_PHASE.replace("relax 0.1;", "relax 0.25;")
                if "16_" in child else BASE_PHASE)

    def test_four_pairs_pass_with_only_declared_changes(self):
        self.assertTrue(all(not issues for issues in audit_all(self.root).values()))

    def test_detect_undeclared_physics_change(self):
        f = self.root / "C16_phaseRelax025_fromC14/constant/metal/fvModels"
        f.write_text(f.read_text().replace("L 2.286e5;", "L 2.99e5;"))
        self.assertTrue(audit_all(self.root)["C16_phaseRelax025_fromC14"])

    def test_detect_inherited_evidence(self):
        path = self.root / "B15_adaptiveDt_fromB14/log.foamMultiRun"
        path.write_text("End\n")
        self.assertIn("simulation output",
                      " ".join(audit_all(self.root)["B15_adaptiveDt_fromB14"]))

    def test_detect_time_directory(self):
        (self.root / "C15_adaptiveDt_fromC14/0.1").mkdir()
        self.assertIn("0.1", " ".join(audit_all(self.root)["C15_adaptiveDt_fromC14"]))

    def test_detect_altered_run_script(self):
        path = self.root / "B16_phaseRelax025_fromB14/Allrun"
        path.write_text("#!/bin/sh\nunsafe command\n")
        self.assertIn("sole changed input",
                      " ".join(audit_all(self.root)["B16_phaseRelax025_fromB14"]))

    def test_comments_do_not_count_as_physics_changes(self):
        path = self.root / "C16_phaseRelax025_fromC14/constant/metal/fvModels"
        path.write_text(path.read_text() + "\n// Additional explanatory comment.\n")
        self.assertEqual(audit_all(self.root)["C16_phaseRelax025_fromC14"], [])

    def test_postrun_auto_accepts_runtime_outputs_without_weakening_core_inputs(self):
        variant = self.root / "B15_adaptiveDt_fromB14"
        (variant / "logs").mkdir()
        (variant / "log.foamMultiRun").write_text("End\n")
        (variant / "0/metal/coolingRate").write_text("generated runtime diagnostic\n")
        self.assertEqual(audit_all(self.root, mode="auto")["B15_adaptiveDt_fromB14"], [])
        f = variant / "system/controlDict"
        f.write_text(f.read_text().replace("maxCo 0.25;", "maxCo 0.99;"))
        self.assertTrue(audit_all(self.root, mode="auto")["B15_adaptiveDt_fromB14"])

    def test_missing_input_is_a_failure(self):
        (self.root / "C15_adaptiveDt_fromC14/0/metal/T").unlink()
        self.assertIn("Missing inputs",
                      " ".join(audit_all(self.root)["C15_adaptiveDt_fromC14"]))


if __name__ == "__main__":
    unittest.main()
