#!/usr/bin/env python3
"""Offline synthetic native report/log + 101-state recovery forensics.

Exercises real evidence-shape checks, without touching WSL C14 CFD fields.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import audit_existing_native_c14_stage07 as sut


def fixture(temp: Path) -> tuple[Path,Path,Path,Path]:
    c14=temp/"ORIGINAL_C14"
    (c14/"system").mkdir(parents=True)
    (c14/"system/controlDict").write_text("C14 ORIGINAL UNCHANGED")
    (c14/"system/researchDiagnostics").write_text("""
temperatureTimeDerivative
{
  type ddt;
  field T;
}
liquidFractionTimeDerivative
{
  type ddt;
  field phaseChangeSource:alpha1;
}
""")
    case=temp/"C3D04_A_ORIGINAL_10S"
    (case/"system").mkdir(parents=True)
    (case/"system/controlDict").write_text("C14 ORIGINAL UNCHANGED")
    (case/"log.foamMultiRun").write_text("Time = 10s\nEnd\n")
    copy=temp/"ISOLATED_NATIVE_WORKCOPY"
    (copy/"system").mkdir(parents=True)
    (copy/"system/controlDict").write_text("C14 ORIGINAL UNCHANGED")
    (copy/"log.foamMultiRun").write_text("Time = 10s\nEnd\n")
    recovery=temp/"STAGE07_RECOVERED_KINETICS"
    recovery.mkdir()
    (recovery/sut.RECOVERY_NAME).write_text(json.dumps({
        "schema":"C3D04_A_C14_3D_STAGE07_EXISTING_EVIDENCE_V1",
        "case_A_source_run_read_only":str(case),
        "source_sha256":{
            "source_CFD_log_sha256":sut.sha(case/"log.foamMultiRun")
        }
    }))
    tasks=[]
    for name,exit_code in [
        ("c14_functions",1),("momentum",2),
        ("top_surface",0),("foamLog",0),
    ]:
        (copy/("log.C14_3D_postprocess_"+name)).write_text(
            "Enabling floating point exception trapping (FOAM_SIGFPE)\n"
            + ("--> FOAM FATAL ERROR:\nCannot find field U in metal\n" if exit_code else
               "End\n"))
        tasks.append({"name":name,"exit_code":exit_code,
                      "passed":exit_code==0,
                      "log":"log.C14_3D_postprocess_"+name})
    original_meta={
        "schema":"C3D04_A_C14_3D_NATIVE_FUNCTION_OBJECT_PARITY_V1",
        "original_CFD_read_only":str(case),
        "source_log_sha256":sut.sha(case/"log.foamMultiRun"),
        "isolated_copy":str(copy),
        "all_native_processing_commands_passed":False,
        "steps":tasks,
        "missing_expected_C14_object_dirs":[
            "metalSensibleEnthalpy","metalLatentHeatPower"],
        "missing_derived_C14_fields_at_final_time":[
            "dAlphaLdt","solidificationRate","phaseChangeDarcyCoeff"],
        "incomplete_profiles_at_t10":[
            "horizontalProfiles/line_y20mm"],
        "full_80_point_profiles_at_t10":{
            "horizontalProfiles/line_y20mm":{
                "status":"INCOMPLETE","saved_data_points":50},
            "verticalProfiles/line_x20mm":{
                "status":"PASS","saved_data_points":80}
        },
        "native_energy_closure_audit":{
            "attempted":True,"passed":False,
            "physically_validated":False,
            "error":"missing native table"},
    }
    (copy/sut.NATIVE_NAME).write_text(json.dumps(original_meta))
    return c14,case,copy,recovery


class NativeEvidenceForensicsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.c14,self.case,self.copy,self.recovery=fixture(self.root)
        original=sut.C14
        sut.C14=self.c14
        self.addCleanup(lambda: setattr(sut,"C14",original))

    def test_integrated_native_failure_summary_and_log_signatures(self):
        before={str(p):sut.sha(p) for p in [
            self.case/"log.foamMultiRun",
            self.copy/sut.NATIVE_NAME,
            self.copy/"log.C14_3D_postprocess_c14_functions",
            self.recovery/sut.RECOVERY_NAME]}
        with mock.patch.object(sut.energy,"calculate",
                               side_effect=ValueError("no native 101-state power tables")):
            r=sut.analyze(self.case,self.copy,self.recovery)
        self.assertEqual(r["native_failed_commands"],["c14_functions","momentum"])
        self.assertFalse(r["native_commands_verified"])
        self.assertEqual(r["missing_C14_postProcessing_object_families"],
                         ["metalSensibleEnthalpy","metalLatentHeatPower"])
        self.assertEqual(len(r["missing_derived_C14_fields_at_10s"]),3)
        self.assertEqual(len(r["missing_or_partial_80_point_profiles"]),1)
        self.assertEqual(
            r["native_command_runs"]["c14_functions"]["error_signatures"][0]["kind"],
            "FATAL_OPENFOAM")
        self.assertIn("Cannot find field U in metal",
                      r["native_command_runs"]["c14_functions"]["tail_last_24_lines"])
        self.assertIn("Cannot find field U in metal",
                      sut.brief(r)["failed_command_last_24_log_lines"]["c14_functions"])
        self.assertEqual(
            [x["object"] for x in
             r["known_original_C14_functionObjects_unavailable_in_offline_replay"]],
            ["temperatureTimeDerivative","liquidFractionTimeDerivative"])
        self.assertFalse(r["energy_conservation_verified"])
        self.assertFalse(r["new_CFD_run"])
        self.assertEqual(r["energy_table_read_only_audit"]["status"],
                         "MISSING_OR_INCOMPATIBLE_NATIVE_ENERGY_TABLES")
        self.assertEqual(before,{k:sut.sha(Path(k)) for k in before})
        out=self.root/"BRAND_NEW_NATIVE_AUDIT"
        self.assertEqual(sut.publish(r,out),
                         "FORENSIC_NATIVE_EVIDENCE_PUBLISHED_READONLY_INPUTS")
        self.assertEqual(sut.publish(r,out),
                         "PREVIOUS_EVIDENCE_MATCHED_REPORT_PRESERVED")
        self.assertEqual(before,{k:sut.sha(Path(k)) for k in before})
        brief=sut.brief(r)
        self.assertEqual(brief["native_commands_verified"],False)
        self.assertEqual(brief["missing_C14_object_families_count"],2)

    def test_native_energy_tables_read_only_reconciliation_is_not_physical(self):
        native_result={
            "final_relative_nominal_closure_residual":0.135,
            "final_integrated_terms":{"time_s":10,"metal_energy_J":100}}
        with mock.patch.object(sut.energy,"calculate",return_value=native_result):
            out=sut.analyze(self.case,self.copy,self.recovery)
        self.assertTrue(out["energy_table_read_only_audit"][
                        "read_only_101_native_energy_tables_reconciled"])
        self.assertAlmostEqual(out["energy_table_read_only_audit"][
                               "final_relative_nominal_residual"],0.135)
        self.assertFalse(out["energy_table_read_only_audit"]["energy_balance_verified"])

    def test_fpe_banner_is_not_runtime_exception(self):
        p=self.copy/"log.C14_3D_postprocess_top_surface"
        result=sut.error_excerpt(p)
        self.assertTrue(result["exists"])
        self.assertEqual(result["error_signatures"],[])

    def test_native_log_replacements_force_new_immutable_output(self):
        with mock.patch.object(sut.energy,"calculate",
                               side_effect=ValueError("unavailable")):
            first=sut.analyze(self.case,self.copy,self.recovery)
            out=self.root/"INDEPENDENT_AUDIT"
            sut.publish(first,out)
            original=sut.sha(out/sut.FORENSIC_NAME)
            p=self.copy/"log.C14_3D_postprocess_momentum"
            p.write_text("changed new native diagnostic evidence\n")
            second=sut.analyze(self.case,self.copy,self.recovery)
            with self.assertRaisesRegex(sut.NativeEvidenceBlocked,"different input"):
                sut.publish(second,out)
            self.assertEqual(sut.sha(out/sut.FORENSIC_NAME),original)

    def test_native_report_exit_mismatch_is_blocked(self):
        p=self.copy/sut.NATIVE_NAME
        obj=json.loads(p.read_text())
        obj["steps"][0]["passed"]=True
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(sut.NativeEvidenceBlocked,
                                     "exit code/passed contradiction"):
            sut.analyze(self.case,self.copy,self.recovery)

    def test_inconsistent_solver_log_or_controlDict_is_blocked(self):
        (self.copy/"log.foamMultiRun").write_text("unrelated solver log!")
        with self.assertRaisesRegex(sut.NativeEvidenceBlocked,
                                     "solver log SHA differs"):
            sut.analyze(self.case,self.copy,self.recovery)

    def test_native_report_different_CFD_case_is_blocked(self):
        p=self.copy/sut.NATIVE_NAME
        obj=json.loads(p.read_text())
        obj["original_CFD_read_only"]="/tmp/other_cfd_case"
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(sut.NativeEvidenceBlocked,
                                     "different source/workcopy"):
            sut.analyze(self.case,self.copy,self.recovery)

    def test_no_writes_inside_source_or_C14_or_native_copy(self):
        with mock.patch.object(sut.energy,"calculate",
                               side_effect=ValueError("not ready")):
            result=sut.analyze(self.case,self.copy,self.recovery)
        for inside in (
            self.case/"FORENSIC",
            self.copy/"FORENSIC",
            self.recovery/"FORENSIC",
            self.c14/"FORENSIC",
            sut.native_runner.BASE.parents[2]/"FORENSIC",
        ):
            with self.subTest(target=str(inside)):
                with self.assertRaisesRegex(sut.NativeEvidenceBlocked,"overlaps"):
                    sut.publish(result,inside)
                self.assertFalse(inside.exists())


if __name__ == "__main__":
    unittest.main()
