"""FS-C04 Foundation14 native T field integration: synthetic NO-CFD tests."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from verify_fs_c04_native_temperature import (
    REGIONS,OPERATIONS,SCHEMA,guard_paths,parse_native_data,
    check_value, execute,
)

EXPECTED={
    "fluid":{
        "region_cells":34368,
        "expected_volume_m3":0.002,
        "expected_volume_weighted_T_K":420.,
        "expected_volIntegrate_T_K_m3":0.84,
    },
    "mold":{
        "region_cells":7680,
        "expected_volume_m3":0.001,
        "expected_volume_weighted_T_K":300.,
        "expected_volIntegrate_T_K_m3":0.3,
    },
}


class TemperatureNativeRegressions(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory(prefix="fs-c04-native-T-")
        self.addCleanup(self.t.cleanup)
        root=Path(self.t.name)
        self.source=root/"FS_C04_T_INITIAL_STAGE_test"
        self.out=root/"FS_C04_T_NATIVE_CHECK_test"
        for region in REGIONS:
            d=self.source/"0"/region
            d.mkdir(parents=True)
            (d/"T").write_text("screening T "+region+"\n")
        (self.source/"important").write_text("preserve")
        (self.source/"FS_C04_INITIAL_T_SCREEN.json").write_text(
            '{"status":"INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT"}')
        self.source_proof={"status":"INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT"}

    def create_result(self,case:Path,op:str,value:float,*,time=0.,header=True):
        f=case/"postProcessing"/(op+"(T)")/"0"/"volFieldValue.dat"
        f.parent.mkdir(parents=True,exist_ok=True)
        first="# Time\t"+op+"(T)\n" if header else "# Time\twrong(T)\n"
        f.write_text(first+str(time)+"\t"+str(value)+"\n")
        return f

    def test_native_average_and_integral_template_parser(self):
        case=self.out
        f=self.create_result(case,"volAverage",420.)
        out=parse_native_data(case,"volAverage")
        self.assertEqual(out["value"],420.)
        self.assertEqual(out["native_function"],"volAverage(T)")
        self.assertIn("volFieldValue.dat",out["path"])
        self.assertEqual(out["time_s"],0.)

    def test_parser_needs_correct_header(self):
        self.create_result(self.out,"volAverage",420.,header=False)
        with self.assertRaisesRegex(ValueError,"output missing/ambiguous"):
            parse_native_data(self.out,"volAverage")

    def test_parser_rejects_duplicate_volAverage_results(self):
        self.create_result(self.out,"volAverage",420.)
        f=self.out/"postProcessing/duplicate/0/volFieldValue.dat"
        f.parent.mkdir(parents=True)
        f.write_text("# Time\tvolAverage(T)\n0\t420\n")
        with self.assertRaisesRegex(ValueError,"output missing/ambiguous"):
            parse_native_data(self.out,"volAverage")

    def test_parser_rejects_wrong_time(self):
        self.create_result(self.out,"volAverage",420.,time=.001)
        with self.assertRaisesRegex(ValueError,"exactly one"):
            parse_native_data(self.out,"volAverage")

    def test_parser_requires_volume_integral_not_mean_header(self):
        self.create_result(self.out,"volAverage",420.)
        with self.assertRaisesRegex(ValueError,"output missing/ambiguous"):
            parse_native_data(self.out,"volIntegrate")

    def test_parser_rejects_nan_or_infinity(self):
        self.create_result(self.out,"volIntegrate",float("nan"))
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            parse_native_data(self.out,"volIntegrate")

    def test_numeric_native_value_outside_tolerance_is_blocked(self):
        with self.assertRaisesRegex(ValueError,"differs"):
            check_value(420.1,420.,"volAverage","fluid")
        with self.assertRaisesRegex(ValueError,"disagrees"):
            check_value(.7,.84,"volIntegrate","fluid")
        check_value(420.,420.,"volAverage","fluid")
        check_value(.84,.84,"volIntegrate","fluid")

    def test_no_overwrite_stage_or_nested_case(self):
        self.out.mkdir()
        (self.out/"precious").write_text("untouched")
        with self.assertRaisesRegex(ValueError,"already exists"):
            guard_paths(self.source,self.out)
        self.assertEqual((self.out/"precious").read_text(),"untouched")
        with self.assertRaisesRegex(ValueError,"cannot overlap"):
            guard_paths(self.source,self.source/"FS_C04_T_NATIVE_CHECK_nested")

    def test_refuse_wrong_source_namespace(self):
        other=self.source.parent/"original_masterproject"
        other.mkdir()
        with self.assertRaisesRegex(ValueError,"not an isolated"):
            guard_paths(other,self.out)

    def test_copy_only_never_calls_openfoam(self):
        with patch("verify_fs_c04_native_temperature.read_stage",
                   return_value=self.source_proof),\
             patch("verify_fs_c04_native_temperature.calculate_expected",
                   return_value=EXPECTED),\
             patch("verify_fs_c04_native_temperature.subprocess.run") as run:
            result=execute(self.source,self.out,False)
        run.assert_not_called()
        self.assertEqual(result["status"],"T_NATIVE_CHECK_STAGED_NO_OPENFOAM")
        self.assertFalse(result["native_volume_integrals_verified"])
        self.assertFalse(result["CFD_or_CHT_executed"])
        self.assertEqual((self.source/"important").read_text(),"preserve")
        self.assertFalse((self.source/"FS_C04_NATIVE_T_ACCEPTANCE.json").exists())

    def test_non_foundation14_rejected_before_copy(self):
        with patch("verify_fs_c04_native_temperature.read_stage",
                   return_value=self.source_proof),\
             patch("verify_fs_c04_native_temperature.calculate_expected",
                   return_value=EXPECTED),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"13"}):
            with self.assertRaisesRegex(ValueError,"Foundation 14"):
                execute(self.source,self.out,True)
        self.assertFalse(self.out.exists())

    def test_end_to_end_four_native_postprocess_ops_without_foamrun(self):
        calls=[]
        def fake_run(cmd,**kwargs):
            self.assertEqual(cmd[0],"foamPostProcess")
            self.assertNotIn("foamRun",cmd)
            self.assertEqual(cmd[cmd.index("-time")+1],"0")
            region=cmd[cmd.index("-region")+1]
            operation=cmd[cmd.index("-func")+1].split("(",1)[0]
            calls.append((region,operation))
            case=Path(cmd[cmd.index("-case")+1])
            expected=EXPECTED[region][
                "expected_volume_weighted_T_K" if operation=="volAverage"
                else "expected_volIntegrate_T_K_m3"
            ]
            self.create_result(case,operation,expected)
            return subprocess.CompletedProcess(cmd,0,"fake test only","")
        with patch("verify_fs_c04_native_temperature.read_stage",
                   return_value=self.source_proof),\
             patch("verify_fs_c04_native_temperature.calculate_expected",
                   return_value=EXPECTED),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("verify_fs_c04_native_temperature.shutil.which",
                   return_value="/opt/openfoam14/bin/foamPostProcess"),\
             patch("verify_fs_c04_native_temperature.subprocess.run",
                   side_effect=fake_run):
            result=execute(self.source,self.out,True)
        self.assertEqual(len(calls),4)
        self.assertEqual(set(calls),{
            ("fluid","volAverage"),("fluid","volIntegrate"),
            ("mold","volAverage"),("mold","volIntegrate")
        })
        self.assertEqual(result["status"],
                         "NATIVE_2_REGION_T_INTEGRALS_VERIFIED_NO_CHT")
        self.assertTrue(result["T_field_read_natively"])
        self.assertTrue(result["native_volume_integrals_verified"])
        self.assertFalse(result["CFD_or_CHT_executed"])
        self.assertFalse(result["solver_thermal_BCs_implemented"])
        self.assertEqual((self.source/"important").read_text(),"preserve")
        self.assertEqual(json.loads((self.out/"FS_C04_NATIVE_T_ACCEPTANCE.json").
                                    read_text())["status"],result["status"])

    def test_nonzero_native_command_is_not_false_success(self):
        with patch("verify_fs_c04_native_temperature.read_stage",
                   return_value=self.source_proof),\
             patch("verify_fs_c04_native_temperature.calculate_expected",
                   return_value=EXPECTED),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("verify_fs_c04_native_temperature.shutil.which",
                   return_value="/opt/openfoam14/bin/foamPostProcess"),\
             patch("verify_fs_c04_native_temperature.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamPostProcess"],1,"","missing temperature field")):
            with self.assertRaisesRegex(ValueError,"foamPostProcess failed"):
                execute(self.source,self.out,True)
        result=json.loads((self.out/"FS_C04_NATIVE_T_ACCEPTANCE.json").read_text())
        self.assertEqual(result["status"],
                         "NATIVE_T_READ_OR_INTEGRAL_REJECTED_NO_CHT")
        self.assertFalse(result["T_field_read_natively"])
        self.assertIn("missing temperature field",
                      (self.out/"log.fluid.volAverage").read_text())

    def test_empty_native_data_not_sufficient_even_if_exit_zero(self):
        with patch("verify_fs_c04_native_temperature.read_stage",
                   return_value=self.source_proof),\
             patch("verify_fs_c04_native_temperature.calculate_expected",
                   return_value=EXPECTED),\
             patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}),\
             patch("verify_fs_c04_native_temperature.shutil.which",
                   return_value="/opt/openfoam14/bin/foamPostProcess"),\
             patch("verify_fs_c04_native_temperature.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamPostProcess"],0,"End","")):
            with self.assertRaisesRegex(ValueError,"no postProcessing output"):
                execute(self.source,self.out,True)
        record=json.loads((self.out/"FS_C04_NATIVE_T_ACCEPTANCE.json").read_text())
        self.assertEqual(record["status"],
                         "NATIVE_T_READ_OR_INTEGRAL_REJECTED_NO_CHT")


if __name__=="__main__":
    unittest.main()
