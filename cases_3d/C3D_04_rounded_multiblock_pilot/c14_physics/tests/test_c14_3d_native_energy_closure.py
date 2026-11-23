#!/usr/bin/env python3
"""Reference regression: parse actual C14 2D native outputs, never fake powers."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import c14_3d_native_energy_closure as closure
import stage_c14_3d_case_a as stage


class ExistingOriginalC14EnergyReferenceTests(unittest.TestCase):
    def test_actual_native_C14_2d_output_read_and_power_decomposition(self):
        original=stage.physics.C14
        r=closure.calculate(original)
        self.assertEqual(r["final_time_s"],10)
        self.assertEqual(r["time_reference_s"],0.1)
        self.assertTrue(r["t0_flux_excluded_from_integral_due_to_uninitialized_function_object_risk"])
        self.assertFalse(r["energy_conservation_physically_validated"])
        self.assertIn("final_relative_nominal_closure_residual",r)
        final=r["final_integrated_terms"]
        self.assertAlmostEqual(final["time_s"],10)
        self.assertGreater(final["all_metal_boundary_energy_power_out_W"],0)
        self.assertGreater(final["native_latent_heat_release_power_W"],0)
        self.assertLess(abs(final["boundary_minus_top_contact_W"]),0.1)

    def test_native_C14_columns_not_guessed(self):
        p=stage.physics.C14/"postProcessing/metal/metalBoundaryEnergyPower/0/surfaceFieldValue.dat"
        keys,rows=closure.parse_table(p)
        self.assertEqual(len(rows),101)
        self.assertIn("sum(energyFlux)",keys)
        self.assertEqual(rows[0]["Time"],0)
        self.assertEqual(rows[-1]["Time"],10)
        self.assertGreater(rows[-1]["sum(energyFlux)"],0)


if __name__=="__main__":
    unittest.main()
