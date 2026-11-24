"""FS-C05 two-region native wallHeatFlux probe: synthetic tests ONLY."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from run_fs_c05_wall_heat_flux import (
    PREFIX,OBJECT_NAME,REGION_PATCH,functions_dict,read_wall_q,
    compare_power,prepare,run,
)
from test_run_fs_c05_native_smoke import (
    CHTNativeSmokeTests, success_output,
)


def synthetic_wall_q(case:Path,region:str,qs:list[tuple[float,float]]
                    )->Path:
    name=OBJECT_NAME[region]
    folder=case/"postProcessing"/name/"0"
    folder.mkdir(parents=True,exist_ok=True)
    p=folder/"wallHeatFlux.dat"
    lines=["# Wall heat-flux",
           "# Time    patch    min [W/m^2]    max [W/m^2]    Q [W]    q [W/m^2]"]
    for time,Q in qs:
        lines.append(f"{time:g} {REGION_PATCH[region]} -1 1 {Q:g} 0.001")
    p.write_text("\n".join(lines)+"\n")
    return p


class WallFluxDataTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="fs-c05-wallflux-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.case=self.root/"new_case"
        self.case.mkdir()

    def test_native_two_wall_Q_tables_are_parsed_with_real_times_and_units(self):
        synthetic_wall_q(self.case,"fluid",[(1e-7,12.),(2e-7,10.)])
        synthetic_wall_q(self.case,"mold",[(1e-7,-12.),(2e-7,-10.)])
        f=read_wall_q(self.case,"fluid")
        m=read_wall_q(self.case,"mold")
        report=compare_power(f,m)
        self.assertEqual(len(f["measurements"]),2)
        self.assertEqual(f["measurements"][0]["Q_W"],12.)
        self.assertEqual(m["measurements"][0]["Q_W"],-12.)
        self.assertFalse(report["alert_mismatch_over_5pct"])
        self.assertEqual(report["snapshot_power_comparison"][0]["Q_sum_W"],0.)
        self.assertFalse(report["full_energy_balance_verified"])

    def test_mismatch_alert_is_diagnostic_not_energy_validation(self):
        synthetic_wall_q(self.case,"fluid",[(1e-7,100.),(2e-7,100.)])
        synthetic_wall_q(self.case,"mold",[(1e-7,-90.),(2e-7,-110.)])
        r=compare_power(read_wall_q(self.case,"fluid"),
                        read_wall_q(self.case,"mold"))
        self.assertTrue(r["alert_mismatch_over_5pct"])
        self.assertFalse(r["energy_flux_physical_validation"])
        self.assertFalse(r["full_energy_balance_verified"])

    def test_missing_native_flux_in_either_region_is_rejected(self):
        synthetic_wall_q(self.case,"fluid",[(1e-7,1.),(2e-7,2.)])
        with self.assertRaisesRegex(ValueError,"missing or ambiguous"):
            read_wall_q(self.case,"mold")

    def test_missing_second_time_is_rejected(self):
        synthetic_wall_q(self.case,"fluid",[(1e-7,1.)])
        with self.assertRaisesRegex(ValueError,"missing native wallHeatFlux"):
            read_wall_q(self.case,"fluid")

    def test_mismatched_patch_rejected(self):
        path=synthetic_wall_q(self.case,"fluid",[(1e-7,1.),(2e-7,2.)])
        path.write_text(path.read_text().replace(
            "fluid_to_mold","atmosphereTop"))
        with self.assertRaisesRegex(ValueError,"wrong wall patch"):
            read_wall_q(self.case,"fluid")

    def test_bad_data_or_missing_Q_header_blocks_acceptance(self):
        path=synthetic_wall_q(self.case,"fluid",[(1e-7,1.),(2e-7,2.)])
        path.write_text(path.read_text().replace("Q [W]","W/m2",1))
        with self.assertRaisesRegex(ValueError,"Time or Q"):
            read_wall_q(self.case,"fluid")

    def test_nan_or_duplicate_native_measurements_rejected(self):
        path=synthetic_wall_q(self.case,"fluid",[(1e-7,1.),(2e-7,2.)])
        path.write_text(path.read_text().replace("1e-07", "nan",1))
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            read_wall_q(self.case,"fluid")
        synthetic_wall_q(self.case,"fluid",
                         [(1e-7,1.),(1e-7,1.),(2e-7,2.)])
        with self.assertRaisesRegex(ValueError,"duplicate"):
            read_wall_q(self.case,"fluid")

    def test_function_dictionary_has_both_real_coupled_walls(self):
        f=functions_dict()
        self.assertIn("wallHeatFluxFluid",f)
        self.assertIn("wallHeatFluxMold",f)
        self.assertIn("type wallHeatFlux;",f)
        self.assertIn("fluid_to_mold",f)
        self.assertIn("mold_to_fluid",f)
        self.assertIn('libs ("libfieldFunctionObjects.so");',f)
        self.assertEqual(f.count("executeControl timeStep;"),2)
        self.assertEqual(f.count("writeInterval 1;"),2)
        self.assertNotIn("wallHeatFluxAtmosphere",f)


class NativeProbeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.fixture=CHTNativeSmokeTests(
            "test_native_input_provenance_is_checked_before_clone")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.source=self.fixture.source
        self.out=self.source.parent/(PREFIX+"synthetic")

    def test_stage_only_copies_then_adds_function_objects_without_running(self):
        before=(self.source/"system/fluid/fvSchemes").read_bytes()
        with patch("run_fs_c05_wall_heat_flux.subprocess.run") as solver:
            data=run(self.source,self.out,native=False)
        solver.assert_not_called()
        self.assertFalse(data["native_solver_executed"])
        self.assertFalse(data["wall_heat_flux_measured"])
        self.assertFalse(data["global_energy_balance_validated"])
        self.assertEqual((self.source/"system/fluid/fvSchemes").read_bytes(),
                         before)
        self.assertTrue((self.out/"system/functions").is_file())
        self.assertTrue((self.out/"FS_C05_WALL_Q_REPORT.json").is_file())
        self.assertFalse((self.source/"system/functions").exists())

    def test_native_two_wall_Q_data_measured_but_energy_not_declared_valid(self):
        def fake_solver(cmd,**kwargs):
            self.assertEqual(cmd,["foamMultiRun","-case",str(self.out)])
            synthetic_wall_q(self.out,"fluid",
                             [(1e-7,10.),(2e-7,5.)])
            synthetic_wall_q(self.out,"mold",
                             [(1e-7,-10.),(2e-7,-5.)])
            return subprocess.CompletedProcess(cmd,0,success_output(),"")
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}), \
             patch("run_fs_c05_wall_heat_flux.shutil.which",
                   return_value="/opt/openfoam14/bin/foamMultiRun"), \
             patch("run_fs_c05_wall_heat_flux.subprocess.run",
                   side_effect=fake_solver):
            data=run(self.source,self.out,native=True)
        self.assertEqual(data["status"],
            "TWO_STEP_FLUID_MOLD_WALL_Q_MEASURED_NO_ENERGY_VALIDATION")
        self.assertTrue(data["wall_heat_flux_measured"])
        self.assertFalse(data["interface_energy_balance_validated"])
        self.assertFalse(data["global_energy_balance_validated"])
        self.assertEqual(data["reciprocal_contact_power"][
            "snapshot_power_comparison"][-1]["Q_sum_W"],0.)
        self.assertTrue((self.out/"log.FS_C05_wall_q_foamMultiRun").is_file())
        self.assertFalse((self.source/"postProcessing").exists())

    def test_solver_error_leaves_failure_report_and_log(self):
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}), \
             patch("run_fs_c05_wall_heat_flux.shutil.which",
                   return_value="/opt/openfoam14/bin/foamMultiRun"), \
             patch("run_fs_c05_wall_heat_flux.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamMultiRun"],1,"","FOAM FATAL IO ERROR")):
            with self.assertRaisesRegex(ValueError,"nonzero"):
                run(self.source,self.out,native=True)
        report=json.loads(
            (self.out/"FS_C05_WALL_Q_REPORT.json").read_text())
        self.assertEqual(report["status"],"WALL_Q_PROBE_REJECTED")
        self.assertFalse(report["wall_heat_flux_measured"])
        self.assertIn("FOAM FATAL",
                      (self.out/"log.FS_C05_wall_q_foamMultiRun").read_text())

    def test_zero_solver_exit_without_Q_files_still_rejected(self):
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}), \
             patch("run_fs_c05_wall_heat_flux.shutil.which",
                   return_value="/opt/openfoam14/bin/foamMultiRun"), \
             patch("run_fs_c05_wall_heat_flux.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamMultiRun"],0,success_output(),"")):
            with self.assertRaisesRegex(ValueError,"no native wallHeatFlux"):
                run(self.source,self.out,native=True)
        report=json.loads(
            (self.out/"FS_C05_WALL_Q_REPORT.json").read_text())
        self.assertEqual(report["status"],"WALL_Q_PROBE_REJECTED")
        self.assertFalse(report["wall_heat_flux_measured"])
        self.assertTrue(report["native_solver_executed"])

    def test_existing_probe_output_cannot_be_reused(self):
        self.out.mkdir()
        (self.out/"preserve").write_text("mine")
        with self.assertRaisesRegex(ValueError,"new isolated destination"):
            prepare(self.source,self.out)
        self.assertEqual((self.out/"preserve").read_text(),"mine")

    def test_wrong_OpenFOAM_14_environment_rejected_before_copy(self):
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"13"}):
            with self.assertRaisesRegex(ValueError,"Foundation OpenFOAM 14"):
                run(self.source,self.out,native=True)
        self.assertFalse(self.out.exists())


if __name__=="__main__":
    unittest.main()
