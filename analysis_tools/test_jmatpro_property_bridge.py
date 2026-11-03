"""Synthetic regression suite for J0 numeric CSV provenance gate. NO OpenFOAM/CFD."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from jmatpro_property_bridge import (
    interp, linear_fit, main, of_equilibrium_branch, read_csv, report,
)

VALID = """T_K,rho_kg_m3,Cp_J_kgK,k_W_mK,fL
1400,6878.52,800,31,0
1473.15,6820,827,32,0.8
1573.15,6740,840,33,0.9
1773.15,6580,870,35,1
"""


class JMatProAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.csv"
        self.source.write_text(VALID, encoding="utf-8")
        self.out = self.root / "reports"

    def test_valid_export_preserves_source_and_emits_hash(self):
        before = self.source.read_bytes()
        self.assertEqual(main([str(self.source), "--out", str(self.out),
                               "--require-density", "--require-phase"]), 0)
        self.assertEqual(self.source.read_bytes(), before)
        report_path = self.out / "source_audit.json"
        data = json.loads(report_path.read_text())
        self.assertEqual(data["source_sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(data["row_count"], 4)
        self.assertEqual(data["density"]["status"], "NUMERIC_DIAGNOSTIC_ONLY")
        self.assertAlmostEqual(data["density"]["beta_1_K"], .8/6820, places=12)
        self.assertEqual(data["phase"]["status"], "EQUILIBRIUM_BRANCH_DIAGNOSTIC_ONLY")
        self.assertEqual(data["J0_status"], "OPEN_NEEDS_RAW_PROVENANCE_AND_COMPOSITION")
        self.assertFalse(data["CFD_executed"])
        self.assertFalse(data["experimental_validation"])
        self.assertTrue((self.out / "source_fL_comparison.csv").is_file())

    def test_source_hash_changes_with_source_bytes(self):
        first = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.source.write_text(VALID.replace("870,35,1", "870,36,1"))
        self.assertEqual(main([str(self.source), "--out", str(self.out)]), 0)
        audit = json.loads((self.out/"source_audit.json").read_text())
        self.assertNotEqual(first, audit["source_sha256"])

    def test_no_density_extrapolation(self):
        rows = read_csv(self.source)
        self.assertIsNone(interp(rows, "rho_kg_m3", 1800))
        self.assertIsNone(interp(rows, "rho_kg_m3", 1300))
        self.assertAlmostEqual(interp(rows, "rho_kg_m3", 1523.15), 6780)

    def test_fitted_reference_outside_data_is_unavailable(self):
        # Fit samples exist but the requested reference is outside data.
        with self.assertRaises(SystemExit) as outcome:
            main([str(self.source), "--out", str(self.out),
                  "--rho-ref-T", "1900", "--require-density"])
        self.assertEqual(outcome.exception.code, 2)
        self.assertFalse(self.out.exists())

    def test_solidus_eutectic_branch_is_diagnostic_only(self):
        self.assertEqual(of_equilibrium_branch(1423, 1423, 1473, .8), .8)
        self.assertEqual(of_equilibrium_branch(1400, 1423, 1473, .8), 0)
        self.assertEqual(of_equilibrium_branch(1473, 1423, 1473, .8), 1)
        with self.assertRaises(ValueError):
            of_equilibrium_branch(1440, 1473, 1423, .8)

    def test_density_linear_fit_consistency(self):
        slope, intercept, r2 = linear_fit([1473.15, 1573.15, 1773.15],
                                          [6820, 6740, 6580])
        self.assertAlmostEqual(slope, -.8)
        self.assertAlmostEqual(r2, 1)
        self.assertTrue(math.isfinite(intercept))

    def test_numeric_hard_fail_cases(self):
        invalid = [
            VALID.replace("T_K,", "Temp_C,"),
            VALID.replace("1400,6878.52", "1400,NaN"),
            VALID.replace("1400,6878.52", "1400,INF"),
            VALID.replace("1400,6878.52", "1400,foo"),
            VALID.replace("1400,6878.52", "1400,-20"),
            VALID.replace("1400,6878.52", "1400,0"),
            VALID.replace("1400,6878.52", ",6878.52"),
            VALID.replace("1400,6878.52", "1473.15,6878.52"),
            VALID.replace("1400,6878.52", "1400,6878.52,EXTRA"),
            VALID.replace("1400,6878.52", "-1,6878.52"),
            VALID.replace("1400,6878.52", "1400,6878.52").replace("800,31,0", "-800,31,0"),
            VALID.replace("800,31,0", "800,31,1.1"),
            VALID.replace("T_K,", "T_K,T_K,"),
        ]
        for content in invalid:
            with self.subTest(content=content[:70]):
                self.source.write_text(content)
                with self.assertRaises(ValueError):
                    read_csv(self.source)
                with self.assertRaises(SystemExit) as caught:
                    main([str(self.source), "--out", str(self.out)])
                self.assertEqual(caught.exception.code, 2)
                self.assertFalse(self.out.exists())

    def test_missing_density_and_phase_require_explicit_gates(self):
        self.source.write_text("T_K,Cp_J_kgK\\n1400,800\\n1500,820\\n".replace("\\n", "\n"))
        self.assertEqual(main([str(self.source), "--out", str(self.out)]), 0)
        data = json.loads((self.out/"source_audit.json").read_text())
        self.assertEqual(data["density"]["status"], "NOT_EVALUATED_INSUFFICIENT_RANGE_OR_REFERENCE")
        self.assertEqual(data["phase"]["status"], "NOT_EVALUATED_NO_FRACTION_SAMPLES")
        with self.assertRaises(SystemExit) as caught:
            main([str(self.source), "--out", str(self.root/"strict"),
                  "--require-density", "--require-phase"])
        self.assertEqual(caught.exception.code, 2)
        self.assertFalse((self.root/"strict").exists())

    def test_invalid_model_parameter_prevents_output(self):
        for extra in (["--Tliq", "1400"], ["--alpha1e", "1.2"],
                      ["--beta-min-T", "1773.15", "--beta-max-T", "1400"],
                      ["--Tliq", "NaN"]):
            with self.subTest(extra=extra):
                with self.assertRaises(SystemExit) as outcome:
                    main([str(self.source), "--out", str(self.out), *extra])
                self.assertEqual(outcome.exception.code, 2)
                self.assertFalse(self.out.exists())

    def test_rejects_output_containing_original_source(self):
        with self.assertRaises(SystemExit) as caught:
            main([str(self.source), "--out", str(self.root)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(self.source.read_text(), VALID)

    def test_no_new_solver_case_or_cad_mutation(self):
        case = self.root / "cases_controlled_buoyancy" / "C14_original"
        case.mkdir(parents=True)
        sentinel = case / "constant"
        sentinel.write_bytes(b"UNCHANGED")
        self.assertEqual(main([str(self.source), "--out", str(self.out)]), 0)
        self.assertEqual(sentinel.read_bytes(), b"UNCHANGED")
        self.assertEqual(sorted(x.name for x in case.iterdir()), ["constant"])

    def test_empty_csv_and_duplicate_headers(self):
        for value in ("", "T_K,fL\\n".replace("\\n", "\n"),
                      "T_K,T_K\\n1400,1500\\n".replace("\\n", "\n")):
            with self.subTest(value=value):
                self.source.write_text(value)
                with self.assertRaises(ValueError):
                    read_csv(self.source)


if __name__ == "__main__":
    unittest.main()
