"""Synthetic FS-C01 runner tests. These tests NEVER execute OpenFOAM or CFD."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from run_fs_c01_local import (
    FSC01Error, REPO, SOURCE_CASE, CASE_ID, mesh_success, prepare_run,
    run_stage, solver_success, validate_source, verify_runtime,
)


class FSC01IsolatedRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fs-c01-test-")
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name) / "FS_C01_RUNS"

    def test_frozen_source_is_explicitly_fs_c01_only(self):
        manifest = validate_source()
        self.assertEqual(CASE_ID, "FS-C01")
        self.assertEqual(manifest["fluid_identity"], "WATER_AIR_ANALOGUE_NOT_MOLTEN_IRON")
        self.assertEqual(len(manifest["generated_sha256"]), 20)

    def test_isolated_stage_hashes_inputs_and_never_edits_3d_or_source(self):
        before = hashlib.sha256((SOURCE_CASE / "0/U").read_bytes()).hexdigest()
        run, case, status = prepare_run(self.out, run_id="FS-C01_test001")
        self.assertEqual(case.name, CASE_ID)
        self.assertEqual(case.parent, run)
        self.assertEqual(status["source_case"], "freesurface/FS-C01")
        self.assertEqual(status["status"], "STAGED_NO_CFD_YET")
        self.assertFalse(status["mass_balance_verified"])
        self.assertFalse(status["shrinkage_modelled"])
        self.assertFalse((case / "postProcessing").exists())
        self.assertFalse((case / "constant/polyMesh").exists())
        self.assertEqual(len(validate_source(case)["generated_sha256"]), 20)
        self.assertEqual(
            before, hashlib.sha256((SOURCE_CASE / "0/U").read_bytes()).hexdigest()
        )
        self.assertTrue((run / "FS-C01_RUN_STATUS.json").is_file())
        self.assertFalse(any(x.name == "C3D-02" for x in run.rglob("*")))

    def test_run_id_and_existing_outputs_fail_closed(self):
        prepare_run(self.out, run_id="FS-C01_unique")
        with self.assertRaises(FileExistsError):
            prepare_run(self.out, run_id="FS-C01_unique")
        with self.assertRaisesRegex(FSC01Error, "run identifier"):
            prepare_run(self.out, run_id="C3D_02_test")

    def test_source_inputs_tamper_detected_on_stage_copy(self):
        _, case, _ = prepare_run(self.out, run_id="FS-C01_modified")
        (case / "0/U").write_text("incorrect data")
        with self.assertRaisesRegex(FSC01Error, "checksum mismatch"):
            validate_source(case)

    def test_wrong_identity_rejected(self):
        _, case, _ = prepare_run(self.out, run_id="FS-C01_wrongID")
        p = case / "BFS01_MANIFEST.json"
        obj = json.loads(p.read_text())
        obj["fluid_identity"] = "IRON"
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(FSC01Error, "not the FS-C01"):
            validate_source(case)

    def test_repo_output_root_refused_even_for_fs_c01(self):
        with self.assertRaisesRegex(FSC01Error, "outside the entire"):
            prepare_run(REPO / "freesurface" / "FS-C01" / "runs")

    def test_mesh_quality_gate_rejects_zero_exit_failed_checks(self):
        self.assertTrue(mesh_success("Checking geometry...\nMesh OK.\n"))
        self.assertFalse(mesh_success("Failed 2 mesh checks.\n"))
        self.assertFalse(mesh_success("Mesh OK.\nFailed 1 mesh checks.\n"))
        self.assertFalse(mesh_success("FOAM FATAL ERROR\nMesh OK.\n"))

    def test_solver_gate_requires_actual_end_marker(self):
        self.assertTrue(solver_success("Time = 0.1\nEnd\n"))
        self.assertFalse(solver_success("Time = 0.04\n"))
        self.assertFalse(solver_success("FOAM FATAL ERROR\nEnd\n"))

    def test_synthetic_log_stage_detects_fail_even_with_zero_process_exit(self):
        run, case, status = prepare_run(self.out, run_id="FS-C01_synthetic")
        command = [sys.executable, "-c", "print('Failed 2 mesh checks.')"]
        with self.assertRaisesRegex(FSC01Error, "checkMesh failed"):
            run_stage(run, case, status, "checkMesh", command, mesh_success)
        saved = json.loads((run / "FS-C01_RUN_STATUS.json").read_text())
        self.assertEqual(saved["status"], "BLOCKED_CHECKMESH")
        self.assertEqual(saved["stages"][0]["returncode"], 0)
        self.assertFalse(saved["stages"][0]["gate_passed"])
        self.assertIn("FS-C01_checkMesh.log", saved["stages"][0]["log"])

    def test_runtime_version_fails_closed(self):
        with patch.dict("os.environ", {"WM_PROJECT_VERSION": "13"}):
            with self.assertRaisesRegex(FSC01Error, "Foundation 14"):
                verify_runtime()
        with patch.dict("os.environ", {"WM_PROJECT_VERSION": "14"}), \
             patch("run_fs_c01_local.shutil.which", return_value=None):
            with self.assertRaisesRegex(FSC01Error, "not found"):
                verify_runtime()


if __name__ == "__main__":
    unittest.main()
