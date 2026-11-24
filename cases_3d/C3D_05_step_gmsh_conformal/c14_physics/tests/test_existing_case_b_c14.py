#!/usr/bin/env python3
"""Regression/negative QA for real B 10s native postrun; NO solver runs."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

SRC=Path(__file__).resolve().parents[1]/"analyze_existing_case_b_c14.py"
spec=importlib.util.spec_from_file_location("c3d05_case_b_c14_postrun",SRC)
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class CaseBRealC14Postrun(unittest.TestCase):
    def test_label_times_must_contain_native_zero_to_ten_and_no_duplicate(self):
        with TemporaryDirectory() as folder:
            case=Path(folder)
            for p in ("0","0.1","1","10"):
                (case/p).mkdir()
            self.assertEqual(S.saved_times(case),[(0.0,"0"),(.1,"0.1"),(1.0,"1"),(10.0,"10")])
            (case/"1.0").mkdir()
            with self.assertRaisesRegex(ValueError,"duplicate physical times"):
                S.saved_times(case)
            (case/"1.0").rmdir()
            (case/"10").rmdir()
            with self.assertRaisesRegex(ValueError,"final 10s"):
                S.saved_times(case)

    def test_C14_original_thresholds_come_from_source_contract(self):
        tsol,tliq,L=S.thresholds()
        self.assertEqual(tsol,1423.0)
        self.assertEqual(tliq,1473.0)
        self.assertGreater(L,0)
        self.assertNotIn("T0_CONDUCTION",SRC.read_text())

    def test_native_scalar_row_includes_92200_real_metal_and_178588_mold(self):
        metal=[1500.0]*S.EXPECTED["metal"]
        metal[-1]=1472.0
        sand=[300.0]*S.EXPECTED["mold"]
        alpha=[1.0]*S.EXPECTED["metal"]
        alpha[-1]=0.5
        p_rgh=[100000.0]*S.EXPECTED["metal"]
        def fake(path,n):
            if path.name=="phaseChangeSource:alpha1":return alpha
            if path.name=="p_rgh":return p_rgh
            if path.name=="T" and path.parent.name=="metal":return metal
            if path.name=="T" and path.parent.name=="mold":return sand
            raise AssertionError(path)
        with patch.object(S.source_reader,"scalar_field_values",side_effect=fake):
            row=S.native_snapshot_row(Path("/unused"),1.2,"1.2",1423,1473)
        self.assertEqual(set(row),set(S.FIELDS))
        self.assertEqual(row["metal_T_below_Tliq_cells"],1)
        self.assertEqual(row["metal_T_below_Tsol_cells"],0)
        self.assertEqual(row["alpha1_below_0_999_cells"],1)
        self.assertEqual(row["alpha1_min"],0.5)
        self.assertEqual(row["mold_T_mean_K"],300)
        self.assertEqual(row["p_rgh_mean_Pa"],100000)

    def test_negative_fraction_and_nonpositive_absolute_T_rejected(self):
        with patch.object(S.source_reader,"scalar_field_values",
                          side_effect=lambda p,n:(
                              [1.01]*n if p.name=="phaseChangeSource:alpha1"
                              else [300]*n)):
            with self.assertRaisesRegex(ValueError,"physical fraction"):
                S.native_snapshot_row(Path("/unused"),0,"0",1423,1473)
        with patch.object(S.source_reader,"scalar_field_values",
                          side_effect=lambda p,n:(
                              [1.0]*n if p.name=="phaseChangeSource:alpha1"
                              else [0.0]*n)):
            with self.assertRaisesRegex(ValueError,"absolute T"):
                S.native_snapshot_row(Path("/unused"),0,"0",1423,1473)

    def test_phase_onset_is_saved_time_interval_not_exact_instant(self):
        rows=[{"time_s":0.0,"alpha1_below_0_999_cells":0},
              {"time_s":0.1,"alpha1_below_0_999_cells":0},
              {"time_s":0.2,"alpha1_below_0_999_cells":4}]
        detected=S.event_bracket(rows,lambda r:r["alpha1_below_0_999_cells"]>0)
        self.assertEqual(detected["first_observed_saved_time_s"],0.2)
        self.assertEqual(detected["previous_saved_time_s"],0.1)
        self.assertTrue(detected["cannot_infer_exact_onset_within_saved_interval"])
        self.assertIsNone(S.event_bracket(rows,lambda r:r["alpha1_below_0_999_cells"]>4))

    def test_summary_does_not_claim_latent_energy_balance_or_QuickCup_validation(self):
        fake={
            "time_s":0,"metal_T_mean_K":1500,"metal_T_min_K":1499,
            "metal_T_below_Tliq_cells":0,"metal_T_below_Tsol_cells":0,
            "alpha1_min":1.0,"alpha1_mean":1.0,
            "alpha1_below_0_999_cells":0
        }
        last={**fake,"time_s":10,"metal_T_mean_K":1450,"metal_T_min_K":1410,
              "metal_T_below_Tliq_cells":38,"metal_T_below_Tsol_cells":10,
              "alpha1_min":0.5,"alpha1_mean":0.87,"alpha1_below_0_999_cells":60}
        report=S.build_summary([fake,last],
            {"courant_max_over_all_logged_steps":0.55}, {},
            Path("/read-only"),Path("/separate"),1423,1473,270000)
        self.assertTrue(report["any_native_alpha1_cell_below_0_999_at_saved_times"])
        self.assertEqual(report["first_saved_alpha1_cell_below_0_999"]["previous_saved_time_s"],0)
        for k in (
            "volume_weighted_solid_fraction_computed","latent_heat_energy_balance_computed",
            "boundary_heat_flux_and_energy_conservation_verified",
            "pressure_momentum_flux_balance_verified","grid_time_step_convergence_verified",
            "JMatPro_QuickCup_physical_validation","recalescence_proven",
            "contraction_feeding_physics_enabled",
        ):
            self.assertIs(report[k],False,k)
        self.assertTrue(report["native_C14_solidificationMeltingSource_selected"])

    def test_inprogress_metadata_rejected_before_native_field_read(self):
        with TemporaryDirectory() as folder:
            case=Path(folder)/"C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
            case.mkdir()
            (case/S.REPORT).write_text(json.dumps({
                "schema":"C3D05_B_C14_EXACT_SOURCE_3D_V1",
                "status":"C3D05_B_C14_FLUID_SOLID_STAGED_F14_NOT_EXECUTED",
                "native_solver_run":False
            }))
            with patch.object(S.physics,"verify"):
                with self.assertRaisesRegex(ValueError,"has NOT completed"):
                    S.validated_mesh_and_stage(case)

    def test_immutable_original_and_existing_analysis_destination_rejected(self):
        with TemporaryDirectory() as folder:
            case=Path(folder)/"C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
            case.mkdir()
            out=case/"analysis"
            with self.assertRaisesRegex(ValueError,"separate"):
                S.audit(case,out)
            dest=Path(folder)/"separate_existing"
            dest.mkdir()
            with self.assertRaisesRegex(ValueError,"no overwrite"):
                S.audit(case,dest)

    def test_no_solver_no_mesh_change_no_fake_CFD(self):
        script=SRC.read_text(encoding="utf-8")
        self.assertNotIn("foamMultiRun(",script)
        self.assertNotIn("subprocess.",script)
        self.assertNotIn("blockMesh",script)
        self.assertNotIn("gmshToFoam",script)
        self.assertIn("selected_C14_fluid_solid_phase_model",script)
        self.assertIn("solver_log_sha256",script)
        self.assertIn("native 10s field changed",script)
        self.assertIn("phaseChangeSource:alpha1",script)


if __name__=="__main__":
    unittest.main()
