"""FS-C08 native bridge runner tests (mocked WSL executables, NO foamMultiRun)."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os

import run_fs_c08_native_bridge as r
from test_verify_fs_c08_openfoam_inventory import native_log


class NativeBridgeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(prefix="fs-c08-no-solver-")
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.case = self.root / "FS_C07_THERMAL_saved"
        self.case.mkdir()
        (self.case / "constant/fluid/polyMesh").mkdir(parents=True)
        (self.case / "constant/fluid/polyMesh/points").write_text("synthetic mesh")
        for time in r.SNAPSHOTS:
            folder = self.case / time / "fluid"
            folder.mkdir(parents=True)
            for field in r.FIELDS:
                (folder / field).write_text(
                    f"synthetic untouched {time} {field}\n")
        self.worktree = self.root / "fs_c08_worktree"
        self.worktree.mkdir()
        self.native = self.worktree / "native_openfoam"
        (self.native / "Make").mkdir(parents=True)
        (self.native / "Make/files").write_text("synthetic")
        (self.native / "Make/options").write_text("synthetic")
        self.foambin = self.root / "foamUserBin"
        self.foambin.mkdir()
        (self.foambin / "fsC08NativeInventory").write_text(
            "fake executable, mocked calls only\n"
        )

    def fake_run(self, argv, cwd, timeout_seconds, log):
        if argv[0] == "wmake":
            log.write_text("synthetic wmake stdout")
        else:
            log.write_text(native_log())

    def test_case_input_hashes_and_snapshot_count(self):
        with patch.object(r, "ROOT", self.worktree):
            sums = r.case_inputs(self.case)
        self.assertEqual(len(sums), 6)
        self.assertEqual(set(sums), {
            f"{t}/fluid/{field}" for t in r.SNAPSHOTS for field in r.FIELDS
        })
        self.assertTrue(all(len(x)==64 for x in sums.values()))

    def test_mocked_bridge_records_parity_and_untouched_case(self):
        before = r.case_inputs(self.case)
        with (
            patch.object(r, "ROOT", self.worktree),
            patch.object(r, "NATIVE", self.native),
            patch.object(r.shutil, "which", return_value="/mock/wmake"),
            patch.object(r, "execute_checked", side_effect=self.fake_run),
            patch.dict(os.environ, {
                "WM_PROJECT_VERSION": "14",
                "FOAM_USER_APPBIN": str(self.foambin)
            })
        ):
            result = r.run(self.case, self.root / "FS_C08_DIAGNOSTICS")
        self.assertEqual(
            result["status"], "FS_C08_NATIVE_FVMESH_READ_ONLY_BRIDGE_PASS__NO_CFD"
        )
        self.assertTrue(result["wmake_compiled"])
        self.assertTrue(result["independent_parity_gate_pass"])
        self.assertFalse(result["source_changed"])
        self.assertEqual(result["source_input_SHA256_before"], before)
        self.assertEqual(result["source_input_SHA256_after"], before)
        self.assertFalse(result["OpenFOAM_CFD_solver_executed"])
        self.assertFalse(result["physical_shrinkage_validated"])

    def test_fake_success_log_with_field_mutation_fails_source_integrity(self):
        def mutate(argv,cwd,timeout_seconds,log):
            self.fake_run(argv,cwd,timeout_seconds,log)
            if argv[0] != "wmake":
                (self.case / "0.4/fluid/alpha.metal").write_text(
                    "modified by mocked native bad actor")
        with (
            patch.object(r, "ROOT", self.worktree),
            patch.object(r, "NATIVE", self.native),
            patch.object(r.shutil, "which", return_value="/mock/wmake"),
            patch.object(r, "execute_checked", side_effect=mutate),
            patch.dict(os.environ, {
                "WM_PROJECT_VERSION": "14",
                "FOAM_USER_APPBIN": str(self.foambin)
            })
        ):
            result = r.run(self.case,self.root/"FS_C08_DIAGNOSTICS")
        self.assertEqual(result["status"],"FS_C08_SOURCE_HASH_CHANGED_CRITICAL_BLOCK")
        self.assertTrue(result["source_changed"])
        self.assertFalse(result["physical_shrinkage_validated"])

    def test_mocked_wmake_error_preserves_report_and_log(self):
        def fail(argv,cwd,timeout_seconds,log):
            log.write_text("mock wmake compilation error\n")
            raise ValueError("synthetic compiler error")
        with (
            patch.object(r, "ROOT", self.worktree),
            patch.object(r, "NATIVE", self.native),
            patch.object(r.shutil, "which", return_value="/mock/wmake"),
            patch.object(r, "execute_checked", side_effect=fail),
            patch.dict(os.environ, {
                "WM_PROJECT_VERSION": "14",
                "FOAM_USER_APPBIN": str(self.foambin)
            })
        ):
            result = r.run(self.case,self.root/"FS_C08_DIAGNOSTICS")
        self.assertEqual(
            result["status"],"FS_C08_NATIVE_BRIDGE_INCOMPLETE_EVIDENCE_PRESERVED")
        self.assertIn("synthetic compiler error",result["last_error"])
        self.assertTrue(Path(result["wmake_log_path"]).exists())
        self.assertFalse(result["source_changed"])
        self.assertFalse(result["wmake_compiled"])

    def test_requires_loaded_actual_Foundation14(self):
        with (
            patch.object(r, "ROOT", self.worktree),
            patch.object(r, "NATIVE", self.native),
            patch.dict(os.environ, {"WM_PROJECT_VERSION": "13"})
        ):
            with self.assertRaisesRegex(ValueError, "Foundation14"):
                r.run(self.case,self.root/"FS_C08_DIAGNOSTICS")


if __name__ == "__main__":
    unittest.main()
