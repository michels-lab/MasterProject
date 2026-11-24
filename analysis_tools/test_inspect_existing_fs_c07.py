"""Read-only, synthetic FS-C07 native termination diagnostics (NO CFD)."""
import json
from pathlib import Path
import tempfile
import unittest

from inspect_existing_fs_c07 import inspect, parse_times, native_time_dirs


class TestExistingFS_C07(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fs-c07-read-only-")
        self.addCleanup(self.temp.cleanup)
        self.case = Path(self.temp.name) / "FS_C07_THERMAL_saved"
        self.case.mkdir()
        (self.case / "FS_C07_REPORT.json").write_text(json.dumps({
            "status": "FS_C07_INCOMPLETE_PRESERVE_EVIDENCE",
            "last_error": "1 s native thermal horizon not reached",
            "native_cfd_executed": False,
        }))
        (self.case / "log.FS_C07_foamMultiRun").write_text(
            "OpenFOAM Foundation14\nTime = 1e-07s\n"
            "ExecutionTime = 0.01 s\nTime = 0.1142694919s\n"
            "fluid Courant Number mean: 0.02 max: 0.1\n"
        )
        for t in ("0", "0.05", "0.1", "0.1142694919"):
            (self.case / t).mkdir()
        (self.case / "0.05/fluid").mkdir()
        for name in ("alpha.metal", "alpha.metal.solid", "T.metal"):
            (self.case / "0.05/fluid" / name).write_text("native\n")

    def test_report_error_is_distinct_from_solver_termination(self):
        d = inspect(self.case)
        self.assertEqual(d["report_status"],
                         "FS_C07_INCOMPLETE_PRESERVE_EVIDENCE")
        self.assertEqual(d["report_last_error"],
                         "1 s native thermal horizon not reached")
        self.assertEqual(d["latest_log_Time_s"], 0.1142694919)
        self.assertEqual(d["max_time_directory_s"], 0.1142694919)
        self.assertEqual(d["last_saved_complete_phase_fields_s"], 0.05)
        self.assertEqual(d["complete_phase_field_directories_count"], 1)
        self.assertFalse(d["solver_end_marker_in_recent_log_tail"])
        self.assertFalse(d["this_diagnostic_executed_solver"])
        self.assertFalse(d["this_diagnostic_modified_case"])

    def test_existing_files_unchanged(self):
        before = {str(p.relative_to(self.case)): p.read_bytes()
                  for p in self.case.rglob("*") if p.is_file()}
        inspect(self.case)
        after = {str(p.relative_to(self.case)): p.read_bytes()
                 for p in self.case.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_float_time_sorted_arithmetically_not_lexically(self):
        self.assertEqual([t for t, _ in native_time_dirs(self.case)],
                         [0.0, 0.05, 0.1, 0.1142694919])

    def test_supports_time_seconds_suffix(self):
        self.assertEqual(
            parse_times("Time = 0.5s\nTime = 1e-4\nTime = 0.7 s\n"),
            [0.5, 0.0001, 0.7])

    def test_no_last_error_does_not_claim_success(self):
        (self.case / "FS_C07_REPORT.json").write_text(json.dumps({
            "status": "FS_C07_STAGED_NO_CFD",
        }))
        d = inspect(self.case)
        self.assertIsNone(d["report_last_error"])
        self.assertIn("process state", d["interpretation"])

    def test_refuses_unrelated_source(self):
        with self.assertRaisesRegex(ValueError, "FS_C07_THERMAL"):
            inspect(Path(self.temp.name))


if __name__ == "__main__":
    unittest.main()
