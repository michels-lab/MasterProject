"""FS-C05 one-shot GRANADA integration tests, all synthetic; NO CFD in CI."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from run_fs_c05_granada import (
    assemble,report_text,run_granada,thermal_storage_proxies,
    RUN_PREFIX,
)

def data(source:str,warning=False):
    def snap(t,metal,air,sand,vol):
        return {
            "time_s":t,
            "metal_phase_volume_raw_m3":vol,
            "air_phase_volume_clamped_m3":0.0016,
            "mold_region_volume_m3":0.000103169142748,
            "metal_alpha_volume_weighted_T_K":metal,
            "air_alpha_volume_weighted_T_K":air,
            "mold_region_volume_weighted_T_K":sand,
            "fluid_T_min_K":299.,
            "fluid_T_max_K":1501.,
            "mold_T_max_K":sand,
            "alpha_within_tolerance":True,
        }
    return {
        "schema":"masterproject-fs-c05-postrun-two-step-observables-v1",
        "status":"NATIVE_TWO_STEP_FIELDS_MEASURED_NO_CHT_VALIDATION",
        "case":source,
        "snapshots":[
            snap(0.,1500.,300.,300.,4.801191628e-5),
            snap(1e-7,1499.99,301.5,300.00002,4.801191628e-5),
            snap(2e-7,1499.996564,301.68343,300.00003,4.801191628e-5),
        ],
        "metal_volume_relative_change":0.,
        "metal_volume_drift_below_alert":True,
        "metal_alpha_weighted_T_change_K":-0.003436,
        "air_alpha_weighted_T_change_K":1.68343,
        "mold_volume_weighted_T_change_K":.00003,
    }

def probe(case:str,bad_q=False):
    powers=[
        {
            "time_s":t,
            "Q_fluid_wall_W":100.,
            "Q_mold_wall_W":(-50. if bad_q else -100.),
            "Q_sum_W":50. if bad_q else 0.,
            "absolute_relative_reciprocity_mismatch":.5 if bad_q else 0.,
            "reciprocity_under_5pct_DIAGNOSTIC_ONLY":not bad_q,
        } for t in (1e-7,2e-7)]
    return {
        "status":"TWO_STEP_FLUID_MOLD_WALL_Q_MEASURED_NO_ENERGY_VALIDATION",
        "wall_heat_flux_measured":True,
        "native_solver_executed":True,
        "output":case,
        "native_flux_records":{"fluid":{"measurements":[]},"mold":{"measurements":[]}},
        "reciprocal_contact_power":{
            "snapshot_power_comparison":powers,
            "alert_mismatch_over_5pct":bad_q,
        },
    }


class GranadaOneShotTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="fs-c05-granada-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.src=self.root/"FS_C05_VOF_CHT_SCREEN_source"
        self.src.mkdir()
        self.original=self.src/"original.txt"
        self.original.write_text("DO NOT TOUCH")
        self.dest=self.root/(RUN_PREFIX+"synthetic")

    def test_complete_one_shot_with_real_paths_but_synthetic_results(self):
        def stub_run(src,out,native):
            self.assertEqual(src,self.src)
            self.assertEqual(out,self.dest)
            self.assertTrue(native)
            out.mkdir()
            return probe(str(out))
        with patch("run_fs_c05_granada.run_wall_probe",
                   side_effect=stub_run) as runner,\
             patch("run_fs_c05_granada.measure_saved_fields",
                   return_value=data(str(self.dest))) as field_audit:
            r=run_granada(self.src,self.dest,native=True)
        runner.assert_called_once()
        field_audit.assert_called_once_with(self.dest)
        self.assertEqual(r["status"],
                         "FS_C05_GRANADA_INTEGRATED_MEASUREMENTS_WITH_WARNINGS")
        self.assertTrue(r["actual_native_CFD_completed"])
        self.assertFalse(r["scope"]["global_energy_conservation_verified"])
        self.assertFalse(r["scope"]["mass_conservation_verified"])
        self.assertFalse(r["scope"]["solidification_or_shrinkage_present"])
        self.assertEqual(self.original.read_text(),"DO NOT TOUCH")
        report=json.loads((self.dest/"FS_C05_GRANADA_REPORT.json").read_text())
        self.assertEqual(report["case"],str(self.dest))
        text=(self.dest/"FS_C05_GRANADA_REPORT.md").read_text()
        for phrase in ("Hierro", "Aire", "Arena", "Q fluido", "NO VALIDADOS"):
            self.assertIn(phrase,text)
        self.assertFalse((self.src/"FS_C05_GRANADA_REPORT.json").exists())

    def test_stage_only_does_not_claim_openfoam_was_run(self):
        with patch("run_fs_c05_granada.run_wall_probe",
                   return_value={"output":str(self.dest)}) as runner,\
             patch("run_fs_c05_granada.measure_saved_fields") as measure:
            r=run_granada(self.src,self.dest,native=False)
        runner.assert_called_once_with(self.src,self.dest,False)
        measure.assert_not_called()
        self.assertEqual(r["status"],"GRANADA_PREPARED_NO_CFD")
        self.assertFalse(r["native_solver_executed"])

    def test_identical_run_required_for_flux_and_temperature_measurements(self):
        with self.assertRaisesRegex(ValueError,"different cases"):
            assemble(probe(str(self.dest)),data(str(self.root/"other")))

    def test_no_false_success_without_real_wall_Q(self):
        r=probe(str(self.dest))
        r["wall_heat_flux_measured"]=False
        with self.assertRaisesRegex(ValueError,"wall flux measurements required"):
            assemble(r,data(str(self.dest)))

    def test_diagnostic_missing_saved_field_persists_failure_for_review(self):
        def fake_run(src,out,native):
            out.mkdir()
            return probe(str(out))
        with patch("run_fs_c05_granada.run_wall_probe",
                   side_effect=fake_run),\
             patch("run_fs_c05_granada.measure_saved_fields",
                   side_effect=ValueError("missing native fluid/T at 2e-7")):
            with self.assertRaisesRegex(ValueError,"missing native"):
                run_granada(self.src,self.dest,native=True)
        r=json.loads((self.dest/"FS_C05_GRANADA_REPORT.json").read_text())
        self.assertEqual(r["status"],"GRANADA_POSTRUN_INCOMPLETE")
        self.assertFalse(r["no_physical_validation"] is False)
        self.assertTrue(r["original_cases_untouched"])

    def test_warning_for_mismatched_Q_is_clear_not_energy_certification(self):
        r=assemble(probe(str(self.dest),bad_q=True),data(str(self.dest)))
        self.assertIn("FLUID_SAND_CONTACT_Q_MISMATCH_GT_5PCT",
                      r["attention_items"])
        self.assertFalse(r["scope"]["global_energy_conservation_verified"])
        self.assertFalse(r["constant_property_thermal_storage_PROXIES_ONLY"]
                         ["thermodynamic_energy_conservation_validated"])

    def test_proxies_are_not_thermophysical_energy_balance(self):
        sample=data(str(self.dest))["snapshots"]
        x=thermal_storage_proxies(sample[0],sample[2])
        self.assertLess(x["metal_delta_sensible_J_PROVISIONAL"],0.)
        self.assertGreater(x["air_delta_sensible_J_FIXED_REFERENCE_RHO_ONLY"],0.)
        self.assertGreater(x["sand_delta_sensible_J_PROVISIONAL"],0.)
        self.assertIn("open",x["reason_NOT_energy_balance"])
        self.assertFalse(x["thermodynamic_energy_conservation_validated"])

    def test_output_already_exists_is_never_overwritten(self):
        self.dest.mkdir()
        mark=self.dest/"valuable"
        mark.write_text("keep me")
        with patch("run_fs_c05_granada.run_wall_probe") as runner:
            with self.assertRaisesRegex(ValueError,"unique fresh"):
                run_granada(self.src,self.dest,native=True)
            runner.assert_not_called()
        self.assertEqual(mark.read_text(),"keep me")

    def test_temperature_proxy_requires_complete_actual_three_times(self):
        d=data(str(self.dest))
        d["snapshots"]=d["snapshots"][:2]
        with self.assertRaisesRegex(ValueError,"exactly 0"):
            assemble(probe(str(self.dest)),d)


if __name__=="__main__":
    unittest.main()
