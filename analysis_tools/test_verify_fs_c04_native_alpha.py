"""FS-C04 native volume integration copy-only, parsing, fail-closed tests.

All tests synthetic. They neither execute foamPostProcess nor certify a
real native OpenFOAM result; the actual result requires the user's Ubuntu.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from verify_fs_c04_native_alpha import (
    FUNCTION_NAME,TARGET_VOLUME_M3,RELATIVE_TOLERANCE,
    guard_paths,read_native_integral,execute
)


class NativeAlphaAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c04-native-alpha-")
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.staged=root/"FS_C04_ALPHA_STAGE_synthetic"
        self.output=root/"FS_C04_ALPHA_NATIVE_CHECK_synthetic"
        self.staged.mkdir()
        (self.staged/"important.txt").write_text("source immutable")
        self.post=self.output/"postProcessing/volIntegrate(alpha.metal)/0"
        self.mock_proof={
            "stage":str(self.staged),
            "manifest_sha256":"synthetic",
            "alpha_sha256":"synthetic",
            "geometric_volume_m3":TARGET_VOLUME_M3,
            "alpha_metal_cells":2368,
            "alpha_air_cells":32000,
        }

    def fake_native_result(self,volume=TARGET_VOLUME_M3,rows=None,
                           header=True):
        self.post.mkdir(parents=True,exist_ok=True)
        content="# Time\tvolIntegrate(alpha.metal)\n" if header else "# Time value\n"
        for t,v in (rows or [(0,volume)]):
            content+=f"{t}\t{v:.16g}\n"
        (self.post/"volFieldValue.dat").write_text(content)

    def test_genuine_numeric_integral_file_parses(self):
        self.fake_native_result()
        report=read_native_integral(self.output)
        self.assertAlmostEqual(report["native_integral_m3"],TARGET_VOLUME_M3)
        self.assertTrue(report["within_0_2_percent_tolerance"])
        self.assertIn("volFieldValue.dat",report["native_result_file"])

    def test_out_of_tolerance_native_integral_rejected(self):
        self.fake_native_result(TARGET_VOLUME_M3*1.01)
        with self.assertRaisesRegex(ValueError,"disagrees with pilot"):
            read_native_integral(self.output)

    def test_native_output_missing_header_rejected(self):
        self.fake_native_result(header=False)
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):
            read_native_integral(self.output)

    def test_native_output_multiple_times_rejected(self):
        self.fake_native_result(rows=[(0,TARGET_VOLUME_M3),
                                      (.001,TARGET_VOLUME_M3)])
        with self.assertRaisesRegex(ValueError,"exactly one t=0"):
            read_native_integral(self.output)

    def test_native_output_wrong_time_rejected(self):
        self.fake_native_result(rows=[(.01,TARGET_VOLUME_M3)])
        with self.assertRaisesRegex(ValueError,"exactly one t=0"):
            read_native_integral(self.output)

    def test_duplicate_native_integrals_rejected(self):
        self.fake_native_result()
        another=self.output/"postProcessing/another/0"
        another.mkdir(parents=True)
        (another/"volFieldValue.dat").write_text(
            (self.post/"volFieldValue.dat").read_text()
        )
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):
            read_native_integral(self.output)

    def test_output_existing_forbidden_and_preserved(self):
        self.output.mkdir()
        (self.output/"preserve").write_text("untouched")
        with self.assertRaisesRegex(ValueError,"destination already exists"):
            guard_paths(self.staged,self.output)
        self.assertEqual((self.output/"preserve").read_text(),"untouched")

    def test_source_nested_destination_forbidden(self):
        with self.assertRaisesRegex(ValueError,"may not overlap"):
            guard_paths(self.staged,self.staged/"FS_C04_ALPHA_NATIVE_CHECK_bad")

    def test_source_wrong_namespace_rejected(self):
        wrong=self.staged.parent/"other"
        wrong.mkdir()
        with self.assertRaisesRegex(ValueError,"not an isolated"):
            guard_paths(wrong,self.output)

    def test_copy_only_never_invokes_native_or_mutates_stage(self):
        with patch("verify_fs_c04_native_alpha.check_source",
                   return_value=self.mock_proof), \
             patch("verify_fs_c04_native_alpha.subprocess.run") as native:
            r=execute(self.staged,self.output,False)
        native.assert_not_called()
        self.assertEqual(r["status"],"CLONED_NOT_NATIVE_VALIDATED")
        self.assertFalse(r["native_field_read_verified"])
        self.assertFalse(r["native_integral_verified"])
        self.assertFalse(r["CFD_or_CHT_executed"])
        self.assertEqual((self.staged/"important.txt").read_text(),"source immutable")
        self.assertEqual((self.output/"important.txt").read_text(),"source immutable")
        self.assertTrue((self.output/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json").is_file())
        self.assertFalse((self.staged/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json").exists())

    def test_nonzero_native_tool_blocks_green_status(self):
        with patch("verify_fs_c04_native_alpha.check_source",
                   return_value=self.mock_proof),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("verify_fs_c04_native_alpha.shutil.which",
                   return_value="/opt/openfoam14/bin/foamPostProcess"),\
             patch("verify_fs_c04_native_alpha.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       args=["foamPostProcess"],returncode=1,
                       stdout="bad",stderr="missing field")):
            with self.assertRaisesRegex(ValueError,"nonzero status"):
                execute(self.staged,self.output,True)
        r=json.loads((self.output/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json").read_text())
        self.assertEqual(r["status"],"NATIVE_ALPHA_INTEGRAL_REJECTED_NO_CFD")
        self.assertFalse(r["native_integral_verified"])
        self.assertFalse(r["native_field_read_verified"])
        self.assertIn("missing field",
                      (self.output/"FS_C04_NATIVE_ALPHA_POSTPROCESS.log").read_text())

    def test_missing_native_integral_rejected_even_if_command_exit_zero(self):
        with patch("verify_fs_c04_native_alpha.check_source",
                   return_value=self.mock_proof),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("verify_fs_c04_native_alpha.shutil.which",
                   return_value="/opt/openfoam14/bin/foamPostProcess"),\
             patch("verify_fs_c04_native_alpha.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       args=["foamPostProcess"],returncode=0,
                       stdout="End",stderr="")):
            with self.assertRaisesRegex(ValueError,"no postProcessing folder"):
                execute(self.staged,self.output,True)
        r=json.loads((self.output/"FS_C04_NATIVE_ALPHA_ACCEPTANCE.json").read_text())
        self.assertEqual(r["status"],"NATIVE_ALPHA_INTEGRAL_REJECTED_NO_CFD")

    def test_refuse_native_if_wrong_openfoam_version_before_copy(self):
        with patch("verify_fs_c04_native_alpha.check_source",
                   return_value=self.mock_proof),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"13"}):
            with self.assertRaisesRegex(ValueError,"Foundation14"):
                execute(self.staged,self.output,True)
        self.assertFalse(self.output.exists())

    def test_native_command_arguments_never_include_foamrun(self):
        def fake_command(args,**kwargs):
            self.assertEqual(args[0],"foamPostProcess")
            self.assertEqual(args[args.index("-region")+1],"fluid")
            self.assertEqual(args[args.index("-time")+1],"0")
            self.assertEqual(args[args.index("-func")+1],FUNCTION_NAME)
            self.assertNotIn("foamRun",args)
            self.fake_native_result()
            return subprocess.CompletedProcess(args,0,"synthetic native","")
        with patch("verify_fs_c04_native_alpha.check_source",
                   return_value=self.mock_proof),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("verify_fs_c04_native_alpha.shutil.which",
                   return_value="/opt/openfoam14/bin/foamPostProcess"),\
             patch("verify_fs_c04_native_alpha.subprocess.run",
                   side_effect=fake_command):
            r=execute(self.staged,self.output,True)
        self.assertEqual(r["status"],"NATIVE_ALPHA_INTEGRAL_VERIFIED_NO_CFD")
        self.assertTrue(r["native_integral_verified"])
        self.assertFalse(r["CFD_or_CHT_executed"])
        self.assertEqual((self.staged/"important.txt").read_text(),"source immutable")


if __name__=="__main__":
    unittest.main()
