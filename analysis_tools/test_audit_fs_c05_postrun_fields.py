"""FS-C05 read-only native 0/1e-7/2e-7 VOF/CHT observables. No CFD."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from audit_fs_c05_postrun_fields import (
    audit, discover_saved_times, summarize_fields, gate_successful_native_run,
    METAL_REFERENCE_VOLUME_M3, STOP_TIME,
)
from stage_fs_c04_initial_alpha import make_alpha
from stage_fs_c04_initial_temperature import (
    create_T, FLUID_PATCHES, MOLD_PATCHES,
)
from run_fs_c05_native_smoke import run
from test_run_fs_c05_native_smoke import (
    CHTNativeSmokeTests, success_output,
)
import subprocess
import os


class DiagnosticArithmeticTests(unittest.TestCase):
    def test_exact_vof_phase_weighted_temperature_and_region_volumes(self):
        r=summarize_fields(
            [2.,3.,5.],[7.,11.],
            [1.,.5,0.],[1000.,500.,300.],[300.,310.]
        )
        self.assertAlmostEqual(r["metal_phase_volume_raw_m3"],3.5)
        self.assertAlmostEqual(r["air_phase_volume_clamped_m3"],6.5)
        self.assertAlmostEqual(r["metal_alpha_volume_weighted_T_K"],
                               (2*1000+1.5*500)/3.5)
        self.assertAlmostEqual(r["air_alpha_volume_weighted_T_K"],
                               (1.5*500+5*300)/6.5)
        self.assertAlmostEqual(r["mold_region_volume_weighted_T_K"],
                               (7*300+11*310)/18)
        self.assertAlmostEqual(r["fluid_region_volume_weighted_T_K"],500)
        self.assertEqual(r["interfacial_alpha_0_to_1_cells"],1)
        self.assertEqual(r["alpha_out_of_unit_interval_cells"],0)
        self.assertFalse(r["energy_or_mass_conservation_validated"])
        self.assertFalse(r["heat_flux_integral_computed"])

    def test_small_alpha_overshoot_flagged_not_silently_discarded(self):
        r=summarize_fields(
            [1.,1.,1.],[1.],[1.00002,.5,-.00001],
            [1000.,500.,300.],[300.]
        )
        self.assertFalse(r["alpha_within_tolerance"])
        self.assertEqual(r["alpha_out_of_unit_interval_cells"],2)
        self.assertNotAlmostEqual(r["metal_phase_volume_raw_m3"],
                                  r["metal_phase_volume_clamped_m3"])

    def test_nonfinite_alpha_or_T_rejected(self):
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            summarize_fields([1.,1.],[1.],[float("nan"),0.],
                             [300.,300.],[300.])
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            summarize_fields([1.,1.],[1.],[1.,0.],
                             [300.,float("inf")],[300.])

    def test_temperature_below_absolute_zero_rejected(self):
        with self.assertRaisesRegex(ValueError,"nonpositive"):
            summarize_fields([1.,1.],[1.],[1.,0.],
                             [1500.,-1.],[300.])

    def test_zero_or_negative_cell_volume_rejected(self):
        with self.assertRaisesRegex(ValueError,"cell volumes"):
            summarize_fields([0.,1.],[1.],[1.,0.],
                             [1500.,300.],[300.])

    def test_empty_phase_or_malformed_arrays_rejected(self):
        with self.assertRaisesRegex(ValueError,"phase volume missing"):
            summarize_fields([1.,1.],[1.],[0.,0.],
                             [300.,300.],[300.])
        with self.assertRaisesRegex(ValueError,"lengths"):
            summarize_fields([1.,1.],[1.],[1.,0.],
                             [1500.],[300.])


class NativeSavedFieldTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="fs-c05-postrun-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.native_case=self.root/"FS_C05_NATIVE_SMOKE_example"
        self.native_case.mkdir()

    def test_all_three_native_times_detected_with_different_names(self):
        for p in ("0","0.0000001","2e-07"):
            (self.native_case/p).mkdir()
        x=discover_saved_times(self.native_case)
        self.assertEqual(set(x),{0.,1e-7,STOP_TIME})

    def test_missing_native_time_rejected(self):
        (self.native_case/"0").mkdir()
        (self.native_case/"2e-07").mkdir()
        with self.assertRaisesRegex(ValueError,"missing t=0"):
            discover_saved_times(self.native_case)

    def test_ambiguous_time_directory_rejected(self):
        for name in ("0","1e-07","0.0000001","2e-07"):
            (self.native_case/name).mkdir()
        with self.assertRaisesRegex(ValueError,"multiple time folders"):
            discover_saved_times(self.native_case)

    def test_non_numeric_directories_ignored(self):
        for name in ("0","1e-07","2e-07","system","constant","postProcessing"):
            (self.native_case/name).mkdir()
        self.assertEqual(len(discover_saved_times(self.native_case)),3)


class FullSmokeFieldsTests(unittest.TestCase):
    def setUp(self):
        self.fixture=CHTNativeSmokeTests(
            "test_native_two_steps_success_only_marks_startup_not_cht_validation")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.case=self.fixture.output
        with patch.dict(os.environ,{"WM_PROJECT_VERSION":"14"}), \
             patch("run_fs_c05_native_smoke.shutil.which",
                   return_value="/opt/openfoam14/bin/foamMultiRun"), \
             patch("run_fs_c05_native_smoke.subprocess.run",
                   return_value=subprocess.CompletedProcess(
                       ["foamMultiRun"],0,success_output(),"")):
            run(self.fixture.source,self.case,native=True)
        # Synthetic native times as ASCII fields. No CFD is run in tests.
        for t in ("1e-07","2e-07"):
            for r in ("fluid","mold"):
                folder=self.case/t/r
                folder.mkdir(parents=True)
                shutil.copy2(self.case/"0"/r/"T",folder/"T")
                if r=="fluid":
                    shutil.copy2(self.case/"0/fluid/alpha.metal",
                                 folder/"alpha.metal")

    def test_accepted_native_manifest_and_exact_log_provenance(self):
        proof=gate_successful_native_run(self.case)
        self.assertEqual(proof["run_steps"]["completed_time_steps"],2)
        self.assertEqual(proof["run_steps"]["last_time_s"],STOP_TIME)
        self.assertTrue(proof["native_log_sha256"])

    def test_unchanged_fields_generate_quantitative_not_cht_green_report(self):
        source=(self.fixture.source/"0/fluid/alpha.metal").read_bytes()
        with patch("audit_fs_c05_postrun_fields.read_mesh",
                   side_effect=lambda p,n:{"region":"fluid" if n==34368 else "mold"}), \
             patch("audit_fs_c05_postrun_fields.cell_volume_m3",
                   side_effect=lambda m,i: (
                       METAL_REFERENCE_VOLUME_M3/2368 if m["region"]=="fluid"
                       else .0001/7680)):
            report=audit(self.case)
        self.assertEqual(report["status"],
                         "NATIVE_TWO_STEP_FIELDS_MEASURED_NO_CHT_VALIDATION")
        self.assertAlmostEqual(report["initial_metal_volume_m3"],
                               METAL_REFERENCE_VOLUME_M3)
        self.assertEqual(report["metal_volume_relative_change"],0.)
        self.assertEqual(report["metal_alpha_weighted_T_change_K"],0.)
        self.assertEqual(report["mold_volume_weighted_T_change_K"],0.)
        self.assertFalse(report["native_foamPostProcess_integrals_at_final_time"])
        self.assertFalse(report["interface_heat_flux_balance_measured"])
        self.assertFalse(report["total_energy_balance_measured"])
        self.assertFalse(report["solidification_shrinkage_present"])
        self.assertEqual(
            (self.fixture.source/"0/fluid/alpha.metal").read_bytes(),source)
        self.assertFalse((self.case/"FS_C05_POSTRUN_DIAGNOSTIC.json").exists())

    def test_modified_native_log_fails_before_field_read(self):
        p=self.case/"log.FS_C05_foamMultiRun"
        p.write_text(p.read_text()+"\nTAMPER")
        with self.assertRaisesRegex(ValueError,"modified or missing"):
            gate_successful_native_run(self.case)

    def test_missing_saved_fluid_T_field_blocks_measurement(self):
        (self.case/"2e-07/fluid/T").unlink()
        with patch("audit_fs_c05_postrun_fields.read_mesh",
                   side_effect=lambda p,n:{"region":"fluid" if n==34368 else "mold"}), \
             patch("audit_fs_c05_postrun_fields.cell_volume_m3",
                   return_value=1.):
            with self.assertRaisesRegex(ValueError,"missing actual saved T_fluid"):
                audit(self.case)

    def test_no_synthetic_CFDrun_error_if_one_snap_missing(self):
        (self.case/"1e-07/fluid/alpha.metal").unlink()
        with patch("audit_fs_c05_postrun_fields.read_mesh",
                   side_effect=lambda p,n:{"region":"fluid" if n==34368 else "mold"}), \
             patch("audit_fs_c05_postrun_fields.cell_volume_m3",
                   return_value=1.):
            with self.assertRaisesRegex(ValueError,"missing actual saved alpha"):
                audit(self.case)


if __name__=="__main__":
    unittest.main()
