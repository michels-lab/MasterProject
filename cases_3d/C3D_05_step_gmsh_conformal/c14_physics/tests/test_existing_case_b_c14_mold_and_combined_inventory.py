#!/usr/bin/env python3
"""No-solver tests for genuine HEX8 mold + metal/mold reference-energy inventory."""
from __future__ import annotations

from array import array
import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SOURCE=Path(__file__).resolve().parents[1]/"quantify_existing_case_b_c14_mold_and_combined_inventory.py"
spec=importlib.util.spec_from_file_location("case_b_mold_native_reference",SOURCE)
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)
from test_volume_weighted_existing_case_b_c14 import two_cube_poly


class CaseBOriginalC14MoldReference(unittest.TestCase):
    def test_reconstruct_two_native_hex8_cells_from_face_orientation(self):
        with TemporaryDirectory() as folder:
            poly=Path(folder)/"polyMesh"
            two_cube_poly(poly)
            vols,info=M.native_mold_cell_volumes(
                poly,expected_cells=2,native_volume_m3=2.)
            self.assertEqual(len(vols),2)
            self.assertAlmostEqual(vols[0],1.0)
            self.assertAlmostEqual(vols[1],1.0)
            self.assertEqual(info["faces"],11)
            self.assertEqual(info["internal_faces"],1)
            self.assertEqual(info["relative_total_volume_discrepancy"],0)

    def test_wrong_checkmesh_mold_volume_blocks_report(self):
        with TemporaryDirectory() as folder:
            poly=Path(folder)/"polyMesh"
            two_cube_poly(poly)
            with self.assertRaisesRegex(ValueError,"checkMesh"):
                M.native_mold_cell_volumes(
                    poly,expected_cells=2,native_volume_m3=3.)

    def test_different_cell_size_mold_temperature_volume_weighted(self):
        r=M.mold_storage(
            [300,300],[400,320],array("d",[1.,3.]),1500,700)
        self.assertAlmostEqual(r["mold_volume_weighted_mean_T_K"],340.0)
        self.assertAlmostEqual(r["mold_sensible_change_from_t0_J"],
                               1500*700*(100*1+20*3))

    def test_correct_liquid_energy_sign_with_positive_solid_equivalent(self):
        r=M.combined_storage(5000,-13576.397936155232,8100.198210984614)
        self.assertAlmostEqual(
            r["metal_liquid_latent_content_change_from_t0_J"],
            -8100.198210984614)
        self.assertAlmostEqual(
            r["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],
            5000-13576.397936155232-8100.198210984614)

    def test_initial_zero_combined_reference_delta(self):
        r=M.combined_storage(0,0,0)
        self.assertEqual(
            r["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],0)

    def test_negative_latent_solid_equivalent_for_remelt_sign_preserved(self):
        r=M.combined_storage(0,-100,-25)
        self.assertEqual(r["metal_liquid_latent_content_change_from_t0_J"],25)
        self.assertEqual(
            r["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],-75)

    def test_nonphysical_mold_temperature_and_bad_cell_size_rejected(self):
        for T in ((math.nan,300),(-2,300),(0,300)):
            with self.assertRaisesRegex(ValueError,"absolute T"):
                M.mold_storage([300,300],list(T),
                               array("d",[1,1]),1500,700)
        with self.assertRaisesRegex(ValueError,"cell volume"):
            M.mold_storage([300],[301],array("d",[-1]),1500,700)
        with self.assertRaisesRegex(ValueError,"length mismatch"):
            M.mold_storage([300],[302,301],array("d",[1.]),1500,700)

    def test_no_rerun_no_mutation_prior_result_protected(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            case=root/M.CASE.name
            post=root/M.POST.name
            metal=root/M.METAL.name
            existing=root/"existing"
            existing.mkdir()
            with self.assertRaisesRegex(ValueError,"refuse replacement"):
                M.run(case,post,metal,existing)
            with self.assertRaisesRegex(ValueError,"cannot overlap"):
                M.run(case,post,metal,case/"within")
        code=SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run",code)
        self.assertNotIn("foamMultiRun(",code)
        self.assertNotIn("blockMesh(",code)
        self.assertIn("original_metal_inventory_CSV_SHA256",code)
        self.assertIn("native_fvModel_latent_heat_source_integral_verified",code)
        self.assertIn('"overall_sensible_latent_energy_conservation_verified":False',code)


if __name__=="__main__":
    unittest.main()
