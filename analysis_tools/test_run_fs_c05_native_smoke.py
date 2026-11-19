"""FS-C05 two-step real CFD startup runner, all tests SYNTHETIC/no OpenFOAM."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import test_stage_fs_c05_vof_cht as synthetic_fixture
from run_fs_c05_native_smoke import (
    OUTPUT_PREFIX,STOP_TIME,preflight,short_control,validate_run_log,run,
)


def success_output()->str:
    return (
        "Create time\n"
        "Starting time loop\n"
        "Time = 1e-07\n"
        "fluid: Courant Number mean: 0.01 max: 0.05\n"
        "mold: Solving for e\n"
        "Time = 2e-07\n"
        "fluid: Courant Number mean: 0.02 max: 0.06\n"
        "mold: Solving for e\n"
        "End\n"
    )


class CHTNativeSmokeTests(unittest.TestCase):
    def setUp(self):
        fixture=synthetic_fixture.CHTTemplateTests(
            "test_case_manifest_enforces_no_native_or_physics_validation_claim")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.source=fixture.out
        fixture.staged()
        self.output=self.source.parent/(OUTPUT_PREFIX+"synthetic")

    def test_native_input_provenance_is_checked_before_clone(self):
        p=preflight(self.source)
        self.assertEqual(p["input_file_count"],
                         len(json.loads((self.source/"FS_C05_PHYSICS_CANDIDATE.json").
                                        read_text())["written_files_sha256"]))
        self.assertEqual(p["mesh_contact_faces"],3136)
        self.assertFalse(p["physical_validation"])

    def test_tampered_ras_settings_cannot_be_launched(self):
        p=self.source/"constant/fluid/momentumTransport"
        p.write_text(p.read_text().replace("kEpsilon","kOmega"))
        with self.assertRaisesRegex(ValueError,"differs from manifest"):
            preflight(self.source)
        self.assertFalse(self.output.exists())

    def test_short_control_guards_exact_two_times_and_writes_each_step(self):
        src=(self.source/"system/controlDict").read_text()
        result=short_control(src)
        self.assertIn("endTime         2e-07;",result)
        self.assertIn("writeControl    timeStep;",result)
        self.assertIn("writeInterval   1;",result)
        self.assertIn("runTimeModifiable false;",result)
        self.assertIn("deltaT          1e-07;",result)
        self.assertIn("maxAlphaCo      0.1;",result)
        self.assertEqual((self.source/"system/controlDict").read_text(),src)

    def test_stage_only_copies_case_without_running_a_solver(self):
        initial=(self.source/"system/controlDict").read_bytes()
        with patch("run_fs_c05_native_smoke.subprocess.run") as process:
            status=run(self.source,self.output,native=False)
        process.assert_not_called()
        self.assertEqual(status["status"],"NATIVE_TWO_STEP_CH_T_STAGED_NO_SOLVER")
        self.assertFalse(status["solver_ran"])
        self.assertFalse(status["heat_flux_balance_verified"])
        self.assertFalse(status["energy_balance_verified"])
        self.assertFalse(status["physically_validated"])
        self.assertEqual((self.source/"system/controlDict").read_bytes(),initial)
        self.assertTrue((self.output/"FS_C05_NATIVE_SMOKE_REPORT.json").exists())
        self.assertFalse((self.source/"FS_C05_NATIVE_SMOKE_REPORT.json").exists())

    def test_native_two_steps_success_only_marks_startup_not_cht_validation(self):
        def run_foam(args,**kwargs):
            self.assertEqual(args,["foamMultiRun","-case",str(self.output)])
            self.assertLessEqual(kwargs.get("timeout"),480)
            return subprocess.CompletedProcess(args,0,success_output(),"")
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("run_fs_c05_native_smoke.shutil.which",
                   return_value="/opt/openfoam14/bin/foamMultiRun"),\
             patch("run_fs_c05_native_smoke.subprocess.run",
                   side_effect=run_foam):
            result=run(self.source,self.output,native=True)
        self.assertEqual(result["status"],
                         "NATIVE_TWO_STEP_VOF_CHT_STARTUP_COMPLETED_NOT_VALIDATED")
        self.assertTrue(result["solver_ran"])
        self.assertEqual(result["startup_log"]["completed_time_steps"],2)
        self.assertAlmostEqual(result["startup_log"]["last_time_s"],STOP_TIME)
        self.assertFalse(result["energy_balance_verified"])
        self.assertFalse(result["alpha_field_verified_after_run"])
        self.assertFalse(result["physically_validated"])
        self.assertIn("Starting time loop",
                      (self.output/"log.FS_C05_foamMultiRun").read_text())

    def test_fatal_log_rejected_even_when_exit_code_zero(self):
        contents=success_output().replace("End\n","FOAM FATAL IO ERROR\n")
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("run_fs_c05_native_smoke.shutil.which",
                   return_value="foamMultiRun"),\
             patch("run_fs_c05_native_smoke.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamMultiRun"],0,contents,"")):
            with self.assertRaisesRegex(ValueError,"fatal error"):
                run(self.source,self.output,native=True)
        r=json.loads((self.output/"FS_C05_NATIVE_SMOKE_REPORT.json").read_text())
        self.assertEqual(r["status"],"NATIVE_SMOKE_REJECTED")
        self.assertTrue(r["solver_ran"])
        self.assertFalse(r["energy_balance_verified"])

    def test_nonzero_solver_exit_stores_logs_and_rejects(self):
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("run_fs_c05_native_smoke.shutil.which",
                   return_value="foamMultiRun"),\
             patch("run_fs_c05_native_smoke.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamMultiRun"],1,"","FOAM FATAL ERROR: missing thermo")):
            with self.assertRaisesRegex(ValueError,"nonzero exit"):
                run(self.source,self.output,native=True)
        self.assertIn("missing thermo",
                      (self.output/"log.FS_C05_foamMultiRun").read_text())
        self.assertEqual(json.loads(
            (self.output/"FS_C05_NATIVE_SMOKE_REPORT.json").read_text()
        )["status"],"NATIVE_SMOKE_REJECTED")

    def test_solver_timeout_marks_failed_and_preserves_evidence(self):
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("run_fs_c05_native_smoke.shutil.which",
                   return_value="foamMultiRun"),\
             patch("run_fs_c05_native_smoke.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(
                       ["foamMultiRun"],480,output=b"old log")):
            with self.assertRaisesRegex(ValueError,"timed out"):
                run(self.source,self.output,native=True)
        status=json.loads((self.output/"FS_C05_NATIVE_SMOKE_REPORT.json").read_text())
        self.assertEqual(status["status"],"NATIVE_SMOKE_REJECTED")
        self.assertEqual(status["failure_reason"],"time limit reached")

    def test_missing_OpenFOAM_Foundation14_refused_before_copy(self):
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"13"}):
            with self.assertRaisesRegex(ValueError,"Foundation 14"):
                run(self.source,self.output,native=True)
        self.assertFalse(self.output.exists())

    def test_never_overwrite_an_existing_output(self):
        self.output.mkdir()
        sentinel=self.output/"valuable"
        sentinel.write_text("preserve")
        with self.assertRaisesRegex(ValueError,"destination required"):
            run(self.source,self.output,native=False)
        self.assertEqual(sentinel.read_text(),"preserve")

    def test_invalid_native_log_missing_end_or_two_steps_rejected(self):
        with self.assertRaisesRegex(ValueError,"lacks End"):
            validate_run_log("Time = 1e-07\n")
        with self.assertRaisesRegex(ValueError,"no two positive"):
            validate_run_log("Time = 2e-07\nEnd\n")
        with self.assertRaisesRegex(ValueError,"did not finish"):
            validate_run_log("Time = 1e-07\nTime = 1.5e-07\nEnd\n")


if __name__=="__main__":
    unittest.main()
