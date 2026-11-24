#!/usr/bin/env python3
"""Real C3D05 B C14 101-state q and source-field readiness audit: unit QA only."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

P=Path(__file__).resolve().parents[1]/"audit_existing_case_b_c14_energy_closure_readiness.py"
spec=importlib.util.spec_from_file_location("C3D05_B_energy_term_readiness",P)
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def base_time_records():
    rows=[]
    for i in range(101):
        t=i*.1
        rows.append({
            "time_s":t,
            "metal_to_mold_q_out_W":20.,
            "mold_to_metal_q_out_W":-20.,
            "interface_sum_outward_W":0.,
            "metalTop_q_out_W":2.,
            "moldOuterUnclassified_q_out_W":3.,
            "external_total_q_out_W":5.,
        })
    return rows


def final_actual_wsl_observation():
    """Numbers literally provided by real user WSL, not fixture CFD."""
    return {
        "metal_sensible_change_from_t0_J":-13576.397936155232,
        "metal_liquid_latent_content_change_from_t0_J":-8100.198210984614,
        "mold_sensible_change_from_t0_J":20323.651945808975,
        "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY":
            -1352.9442013308708,
        S.joined.CUM_COLS["metal_to_mold_q_out_W"]:20283.45236535595,
        S.joined.CUM_COLS["mold_to_metal_q_out_W"]:-20283.567648522097,
        S.joined.CUM_COLS["metalTop_q_out_W"]:1212.0952906419318,
        S.joined.CUM_COLS["moldOuterUnclassified_q_out_W"]:129.41261637931336,
        S.joined.CUM_COLS["interface_sum_outward_W"]:-0.11528316616279427,
        S.joined.CUM_COLS["external_total_q_out_W"]:1341.5079070212457,
    }


class CaseB101SourceEnergyReadinessQA(unittest.TestCase):
    def test_real_user_observed_values_per_region_are_consistent(self):
        r=S.per_region_reference_diagnostic(final_actual_wsl_observation())
        self.assertAlmostEqual(r["metal"]["reference_storage_change_J"],
                               -21676.596147139848,places=7)
        self.assertAlmostEqual(r["mold"]["reference_storage_change_J"],
                               20323.651945808975,places=7)
        self.assertAlmostEqual(r["metal"][
            "outward_conductive_q_saved_trapezoid_J"],21495.547655997885,places=6)
        self.assertAlmostEqual(r["mold"][
            "outward_conductive_q_saved_trapezoid_J"],-20154.155032142786,places=6)
        self.assertAlmostEqual(r["metal"][
            "sum_reference_storage_plus_outward_conduction_J_NOT_ENERGY_RESIDUAL"],
            -181.0484911419626,places=5)
        self.assertAlmostEqual(r["mold"][
            "sum_reference_storage_plus_outward_conduction_J_NOT_ENERGY_RESIDUAL"],
            169.49691366618936,places=5)
        self.assertAlmostEqual(r[
            "domain_exterior_only_reference_comparison_J_NOT_ENERGY_RESIDUAL"],
            -11.436294309625055,places=5)
        self.assertAlmostEqual(r["internal_interface_signed_q_saved_trapezoid_J"],
                               -0.11528316616279427,places=6)

    def test_saved_constant_flux_trapezoid_all_grids_same_10s_integral(self):
        data=S.quadrature_sensitivity(base_time_records())
        self.assertEqual([round(x["saved_time_step_s"],1) for x in data],
                         [.1,.2,.5,1.])
        self.assertEqual([x["count_saved_snapshots"] for x in data],
                         [101,51,21,11])
        for x in data:
            self.assertAlmostEqual(
                x["external_total_q_out_J_SAVED_TIME_TRAPEZOID"],50.)
            self.assertAlmostEqual(
                x["metal_to_mold_q_out_J_SAVED_TIME_TRAPEZOID"],200.)
            self.assertAlmostEqual(
                x["mold_to_metal_q_out_J_SAVED_TIME_TRAPEZOID"],-200.)
            self.assertTrue(x["not_original_solver_dt_integral"])

    def test_subsampling_shows_temporal_resolution_sensitivity_not_dt_error(self):
        data=base_time_records()
        # A narrow 100-ms pulse at one original snapshot is invisible to
        # saved 0.2s and coarser grids; this is a LIMITATION, not true error.
        data[1]["metalTop_q_out_W"]=102.
        data[1]["external_total_q_out_W"]=105.
        measures=S.quadrature_sensitivity(data)
        fine=measures[0]["external_total_q_out_J_SAVED_TIME_TRAPEZOID"]
        coarse=measures[1]["external_total_q_out_J_SAVED_TIME_TRAPEZOID"]
        self.assertAlmostEqual(fine,60.)
        self.assertAlmostEqual(coarse,50.)
        self.assertAlmostEqual(measures[1][
            "external_total_q_out_J_SAVED_TIME_TRAPEZOID_difference_vs_0_1s_J"],-10.)

    def test_partial_expressions_are_never_relabelled_conservation(self):
        r=S.per_region_reference_diagnostic(final_actual_wsl_observation())
        self.assertIn("NOT_ENERGY_RESIDUAL",list(r["metal"])[-1])
        self.assertIn("NOT_ENERGY_RESIDUAL",list(r["mold"])[-1])
        self.assertIn("NOT_ENERGY_RESIDUAL",
                      "domain_exterior_only_reference_comparison_J_NOT_ENERGY_RESIDUAL")
        source=P.read_text(encoding="utf-8")
        self.assertIn('"overall_F14_solver_energy_conservation_verified":False',source)
        self.assertIn('"no_native_fvModels_internal_time_integral":True',source)
        self.assertIn('"NO_SOLVER_NO_POSTRUN_Q_REEXECUTION":True',source)

    def test_missing_nonessential_h_e_fields_recorded_not_guessed(self):
        with TemporaryDirectory() as d:
            original=Path(d)/"native_archived_CFD"
            original.mkdir()
            saved=[]
            for i in range(101):
                t=round(i*.1,1)
                name=f"{t:g}"
                saved.append((t,name))
                (original/name/"metal").mkdir(parents=True)
                (original/name/"mold").mkdir()
                for path in ("metal/T","metal/phaseChangeSource:alpha1",
                             "mold/T"):
                    (original/name/path).write_text("immutable original test field")
            result=S.field_coverage(original,saved)
            self.assertEqual(result["metal_T"]["saved_states_with_field"],101)
            self.assertEqual(result["metal_alpha1"]["saved_states_with_field"],101)
            self.assertEqual(result["mold_T"]["saved_states_with_field"],101)
            self.assertEqual(result["metal_h"]["saved_states_with_field"],0)
            self.assertFalse(result["metal_h"]["all_101_states_available"])
            self.assertFalse(result["mold_e"]["all_101_states_available"])

    def test_essential_original_T_field_missing_rejected(self):
        with TemporaryDirectory() as d:
            original=Path(d)/"native_archived_CFD"
            original.mkdir()
            saved=[]
            for i in range(101):
                t=round(i*.1,1)
                name=f"{t:g}"
                saved.append((t,name))
                (original/name/"metal").mkdir(parents=True)
                (original/name/"mold").mkdir()
                for path in ("metal/T","metal/phaseChangeSource:alpha1",
                             "mold/T"):
                    (original/name/path).write_text("original archived test field")
            (original/"5"/"mold/T").unlink()
            with self.assertRaisesRegex(ValueError,"essential original C14"):
                S.field_coverage(original,saved)

    def test_corrupt_saved_Q_field_or_time_axis_rejected(self):
        x=base_time_records()
        x[10]["external_total_q_out_W"]=float("nan")
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            S.quadrature_sensitivity(x)
        x=base_time_records()
        x[10]["time_s"]=1.9
        with self.assertRaisesRegex(ValueError,"time axis"):
            S.quadrature_sensitivity(x)

    def test_mismatched_reference_inventory_rejected(self):
        x=final_actual_wsl_observation()
        x["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"]=7.
        with self.assertRaisesRegex(ValueError,"storage sum"):
            S.per_region_reference_diagnostic(x)

    def test_no_solver_runs_or_overwrites_in_readiness_source(self):
        source=P.read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run(",source)
        self.assertNotIn("foamMultiRun(",source)
        self.assertNotIn("wmake(",source)
        self.assertIn("pending.rename(out)",source)
        self.assertIn("out not in p.parents and p not in out.parents",source)
        self.assertIn("source_original_CFD_stage_SHA256",source)


if __name__=="__main__":
    unittest.main()
