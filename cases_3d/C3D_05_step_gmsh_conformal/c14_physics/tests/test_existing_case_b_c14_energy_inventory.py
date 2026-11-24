#!/usr/bin/env python3
"""Exact metal C14 sensible + LATENT EQUIVALENT postrun: zero-solver QA."""
from __future__ import annotations

from array import array
import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

CODE=Path(__file__).resolve().parents[1]/"quantify_existing_case_b_c14_energy_inventory.py"
spec=importlib.util.spec_from_file_location("c3d05_b_C14_energy_inventory",CODE)
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class C14OriginalMetalStorageInventory(unittest.TestCase):
    def test_material_constants_exact_original_source_contract(self):
        d=S.source_C14_constants()
        self.assertEqual(d["rho_metal_kg_m3"],6820)
        self.assertEqual(d["Cp_metal_J_kgK"],827)
        self.assertEqual(d["L_metal_J_kg"],228600)
        self.assertEqual(d["reference_initial_temperature_K"],1500)
        self.assertIn("NOT QuickCup/JMatPro",d["provenance"])

    def test_initial_zero_sensible_and_zero_phase_proxy(self):
        result=S.storage_at_time(array("d",[1,3]),[1500,1510],[1.0,.75],
                    [1500,1510],[1.0,.75],6820,827,228600)
        self.assertEqual(result["metal_sensible_change_from_t0_J"],0)
        self.assertEqual(result[
            "metal_latent_equivalent_solid_complement_change_from_t0_J"],0)
        self.assertEqual(result["mean_metal_temperature_volume_weighted_K"],1507.5)
        self.assertEqual(result["mean_liquid_fraction_volume_weighted"],.8125)

    def test_t_and_alpha_model_storage_formula_on_unequal_cells(self):
        volumes=array("d",[1.0,3.0])
        delta=S.storage_at_time(volumes,[1490,1480],[.5,.25],
                                [1500,1500],[1.,1.],6820,827,228600)
        expected_sensible=6820*827*(-10*1-20*3)
        expected_latent=6820*228600*(.5*1+.75*3)
        self.assertAlmostEqual(delta["metal_sensible_change_from_t0_J"],
                               expected_sensible)
        self.assertAlmostEqual(delta[
            "metal_latent_equivalent_solid_complement_change_from_t0_J"],
                               expected_latent)
        self.assertAlmostEqual(delta["mean_liquid_fraction_volume_weighted"],.3125)
        self.assertAlmostEqual(delta["mean_solid_complement_volume_weighted"],.6875)
        self.assertAlmostEqual(delta["latent_equivalent_instantaneous_inventory_J"],
                               expected_latent)

    def test_initial_partly_solid_does_not_count_as_latent_change(self):
        delta=S.storage_at_time(array("d",[1.0]),[1490],[.3],[1500],[.7],
                                1000,10,100)
        self.assertAlmostEqual(delta["metal_sensible_change_from_t0_J"],-100000)
        self.assertAlmostEqual(delta[
            "metal_latent_equivalent_solid_complement_change_from_t0_J"],40000)
        self.assertAlmostEqual(delta["latent_equivalent_instantaneous_inventory_J"],
                               70000)

    def test_model_remelting_negative_latent_equivalent_change_preserved(self):
        delta=S.storage_at_time(array("d",[2.0]),[1500],[.8],[1500],[.5],
                                1000,10,100)
        self.assertEqual(delta["metal_sensible_change_from_t0_J"],0)
        self.assertAlmostEqual(delta[
            "metal_latent_equivalent_solid_complement_change_from_t0_J"],-60000)

    def test_nonphysical_alpha_or_nonfinite_temperature_or_volumes_rejected(self):
        with self.assertRaisesRegex(ValueError,"liquid fraction"):
            S.storage_at_time(array("d",[1]),[1500],[1.2],[1500],[1.0],
                              6820,827,228600)
        with self.assertRaisesRegex(ValueError,"temperatures"):
            S.storage_at_time(array("d",[1]),[math.nan],[1.0],[1500],[1.0],
                              6820,827,228600)
        with self.assertRaisesRegex(ValueError,"volumes"):
            S.storage_at_time(array("d",[-1]),[1500],[1.0],[1500],[1.0],
                              6820,827,228600)
        with self.assertRaisesRegex(ValueError,"do not align"):
            S.storage_at_time(array("d",[1]),[1500,1490],[1.0],
                              [1500],[1.0],6820,827,228600)

    def test_existing_output_and_source_dir_refused_before_work(self):
        with TemporaryDirectory() as folder:
            case=Path(folder)/"C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
            post=Path(folder)/"C3D05_B_C14_FLUID_SOLID_10S_ANALYSIS_01"
            weighted=Path(folder)/"C3D05_B_C14_VOLUME_WEIGHTED_PHASE_01"
            out=Path(folder)/"result"
            out.mkdir()
            with self.assertRaisesRegex(ValueError,"refuse overwrite"):
                S.run(case,post,weighted,out)
            with self.assertRaisesRegex(ValueError,"separate"):
                S.run(case,post,weighted,case/"nested")

    def test_old_phase_and_CFD_integrity_required_not_optional(self):
        source=CODE.read_text(encoding="utf-8")
        for phrase in ("source_native_CFD_report_SHA256","source_native_CFD_log_SHA256",
                       "result_CSV_sha256","source_original_postrun_CSV_SHA256",
                       "weighted alpha from native geometry disagrees",
                       "original archived native postrun SHA changed"):
            if phrase=="source_native_CFD_report_SHA256":
                self.assertIn(phrase,source)
            else:
                self.assertIn(phrase,source)
        self.assertIn("source_C14_constants",source)
        self.assertIn("absolute_energy_stored_J_computed",source)

    def test_no_native_solver_no_q_balance_or_QuickCup_claim(self):
        source=CODE.read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run",source)
        self.assertNotIn("foamMultiRun(",source)
        self.assertNotIn("blockMesh(",source)
        self.assertIn('"metal_sand_exterior_energy_balance_verified":False',source)
        self.assertIn('"native_solver_latent_fvModels_integral_computed":False',source)
        self.assertIn('"material_properties_JMatPro_QuickCup_calibrated":False',source)


if __name__=="__main__":
    unittest.main()
