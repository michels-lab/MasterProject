#!/usr/bin/env python3
"""Regression tests for indented OpenFOAM Foundation 14 solver-log markers."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from audit_pushed_results import audit_case


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


if __name__ == "__main__":
    unittest.main()
