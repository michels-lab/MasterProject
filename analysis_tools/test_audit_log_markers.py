#!/usr/bin/env python3
"""Regression tests for indented OpenFOAM Foundation 14 solver-log markers."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from audit_pushed_results import audit_case, last_row, tail


class OpenFOAMLogMarkersTests(unittest.TestCase):
    def test_indented_end_not_missing(self):
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "C14_test"
            case.mkdir()
            (case / "log.foamMultiRun").write_text(
                "Time = 0.001s\n      Time = 10s\n"
                "      ExecutionTime = 550 s  ClockTime = 575 s\n"
                "      End\n", encoding="utf-8")
            (case / "system").mkdir()
            (case / "system/controlDict").write_text("endTime 10;\n", encoding="utf-8")
            result = audit_case(case, {"run_status": "RUN_VERIFIED",
                                       "analysis_status": "NOT_ANALYZED"})
            self.assertNotIn(
                "End marker not found near saved log tail", result["notes"])
            self.assertEqual(result["requested_end_s"], 10)

    def test_missing_end_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "C15_test"
            case.mkdir()
            (case / "log.foamMultiRun").write_text(
                "Time = 9.5s\n", encoding="utf-8")
            result = audit_case(case, {"run_status": "RUN_VERIFIED",
                                       "analysis_status": "NOT_ANALYZED"})
            self.assertIn(
                "End marker not found near saved log tail", result["notes"])


    def test_probe_invalid_last_row_not_hidden(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"T"
            for bad in ("10 nan", "10 corrupt"):
                p.write_text("9 1200\n"+bad+"\n")
                self.assertIsNone(last_row(p))

    def test_partial_tail_line_not_read_as_sample(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"T"
            p.write_text("123456789 1200\n10 1100\n")
            self.assertEqual(tail(p,13),"10 1100\n")

    def test_end_before_last_time_and_probe_overshoot(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"C14";p.mkdir()
            (p/"system").mkdir()
            (p/"system/controlDict").write_text("endTime 10;\n")
            (p/"log.foamMultiRun").write_text("Time = 9s\nEnd\nTime = 11s\n")
            probe=p/"postProcessing/metal/temperatureProbe/0/T"
            probe.parent.mkdir(parents=True)
            probe.write_text("11 1200\n")
            r=audit_case(p,{"run_status":"RUN_VERIFIED"})
            self.assertIn("End precedes last native Time marker",r["alerts"])
            self.assertIn("Last native Time differs from requested endTime",r["alerts"])
            self.assertIn("Temperature probe not at requested endTime",r["alerts"])

if __name__ == "__main__":
    unittest.main()
