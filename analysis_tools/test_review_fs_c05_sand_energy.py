"""FS-C05 sand Euler energy audit with REAL user values, no OpenFOAM in CI."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from review_fs_c05_sand_energy import (
    audit, main, report_md, sand_energy_steps, sand_model,
)


class SandEulerAuditTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="fs-c05-sand-review-")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.case=self.root/"FS_C05_WALL_Q_PROBE_synthetic"
        self.case.mkdir()

    @staticmethod
    def native_user_data():
        # Three original native T snapshots reported by user's 2026-11-19
        # field audit, plus 2026-11-20 real wallHeatFlux readings.
        volume=0.030950742856/300.
        snaps=[
            {"time_s":0., "mold_region_volume_m3":volume,
             "mold_region_volume_weighted_T_K":300.},
            {"time_s":1e-7, "mold_region_volume_m3":volume,
             "mold_region_volume_weighted_T_K":300.0000149843143},
            {"time_s":2e-7,"mold_region_volume_m3":volume,
             "mold_region_volume_weighted_T_K":300.0000299686341},
        ]
        q=[
            {"time_s":1e-7,"Q_mold_wall_W":16232.15236226,
             "Q_fluid_wall_W":-16232.10986685},
            {"time_s":2e-7,"Q_mold_wall_W":16232.15056037,
             "Q_fluid_wall_W":-16232.10729669},
        ]
        return snaps,q

    def test_actual_reported_sand_energy_closes_both_euler_steps(self):
        snaps,q=self.native_user_data()
        x=sand_energy_steps(snaps,q,1500.,700.)
        self.assertEqual(x["status"],
                         "SAND_EULER_ENERGY_CLOSES_WITHIN_1PCT_DIAGNOSTIC")
        self.assertAlmostEqual(x["steps"][0]["delta_internal_energy_J"],
                               0.00162321480623675,places=11)
        self.assertAlmostEqual(x["steps"][0]["incoming_wall_Q_times_dt_J"],
                               0.001623215236226,places=11)
        self.assertLess(x["steps"][0]["relative_discrete_error"],3e-7)
        self.assertLess(x["steps"][1]["relative_discrete_error"],3e-7)
        self.assertFalse(x["global_energy_balance_validated"])
        self.assertFalse(x["experimentally_validated"])

    def test_sand_local_energy_gap_is_flagged_and_not_hidden(self):
        snaps,q=self.native_user_data()
        q[1]["Q_mold_wall_W"]=100.
        x=sand_energy_steps(snaps,q,1500.,700.)
        self.assertEqual(x["status"],"SAND_EULER_ENERGY_RESIDUAL_WARNING")
        self.assertFalse(x["steps"][1]["under_1pct_DIAGNOSTIC"])
        self.assertFalse(x["global_energy_balance_validated"])

    def test_wrong_heat_flux_sign_is_not_falsely_balanced(self):
        snaps,q=self.native_user_data()
        q[0]["Q_mold_wall_W"]=-q[0]["Q_mold_wall_W"]
        x=sand_energy_steps(snaps,q,1500.,700.)
        self.assertEqual(x["status"],"SAND_EULER_ENERGY_RESIDUAL_WARNING")

    def test_wrong_time_alignment_and_mesh_change_refused(self):
        snaps,q=self.native_user_data()
        q[1]["time_s"]=3e-7
        with self.assertRaisesRegex(ValueError,"invalid chronology"):
            sand_energy_steps(snaps,q,1500.,700.)
        snaps,q=self.native_user_data()
        snaps[-1]["mold_region_volume_m3"]*=1.1
        with self.assertRaisesRegex(ValueError,"volumes do not match"):
            sand_energy_steps(snaps,q,1500.,700.)

    def test_model_is_read_from_actual_screening_dictionary(self):
        from test_run_fs_c05_native_smoke import CHTNativeSmokeTests
        fixture=CHTNativeSmokeTests(
            "test_native_input_provenance_is_checked_before_clone")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        model=sand_model(fixture.source)
        self.assertEqual(model["rho_kg_m3"],1500.)
        self.assertEqual(model["Cv_J_kgK"],700.)
        self.assertEqual(model["Euler_dt_expected_s"],1e-7)
        self.assertTrue(model["constant_property_screening_ONLY"])

    def test_model_refuses_nonadiabatic_sand_boundary(self):
        from test_run_fs_c05_native_smoke import CHTNativeSmokeTests
        fixture=CHTNativeSmokeTests(
            "test_native_input_provenance_is_checked_before_clone")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        field=fixture.source/"0/mold/T"
        field.write_text(field.read_text().replace(
            "moldBottom\n    {\n        type zeroGradient;",
            "moldBottom\n    {\n        type fixedValue; value uniform 300;"))
        with self.assertRaisesRegex(ValueError,"nonadiabatic"):
            sand_model(fixture.source)

    def test_result_consolidation_never_calls_native_solver(self):
        snaps,q=self.native_user_data()
        fields={
            "snapshots":snaps,
            "metal_volume_relative_change":0.,
        }
        comparison={"snapshot_power_comparison":q,
                    "alert_mismatch_over_5pct":False}
        native={
            "native_log_sha256":"synthetic",
            "old_granada_sha256":"synthetic",
            "rho_inventory":{"status":"SYNTHETIC_MASS_NO_CLOSURE",
                             "native_density_inventory_observed":True},
            "fields":fields,
            "wall":comparison,
        }
        with patch("review_fs_c05_sand_energy.verify_native",
                   return_value=native),\
             patch("review_fs_c05_sand_energy.sand_model",
                   return_value={"rho_kg_m3":1500.,"Cv_J_kgK":700.}),\
             patch("review_fs_c05_sand_energy.subprocess.run",
                   create=True) as forbidden:
            x=audit(self.case)
        forbidden.assert_not_called()
        self.assertTrue(x["no_new_CFD_executed"])
        self.assertFalse(x["global_mass_conservation_validated"])
        self.assertFalse(x["global_energy_conservation_validated"])
        self.assertEqual(x["status"],
                         "SAND_EULER_ENERGY_CLOSES_WITHIN_1PCT_DIAGNOSTIC")
        self.assertIn("Euler",report_md(x))
        self.assertIn("SAND",report_md(x).upper())

    def test_reports_are_written_outside_original_case(self):
        snaps,q=self.native_user_data()
        fake={
            "status":"SAND_EULER_ENERGY_CLOSES_WITHIN_1PCT_DIAGNOSTIC",
            "discrete_sand_energy":sand_energy_steps(snaps,q,1500.,700.),
            "real_density_inventory":{"status":"REAL_MASS_INVENTORY_NO_CLOSURE"},
        }
        target=self.root/"new_sibling_analysis"
        with patch("review_fs_c05_sand_energy.audit",return_value=fake):
            ret=main(["--case",str(self.case),"--out",str(target)])
        self.assertEqual(ret,0)
        self.assertTrue((target/"FS_C05_SAND_ENERGY_REVIEW.json").exists())
        self.assertTrue((target/"FS_C05_SAND_ENERGY_REVIEW.md").exists())
        self.assertFalse((self.case/"FS_C05_SAND_ENERGY_REVIEW.json").exists())
        with patch("review_fs_c05_sand_energy.audit") as read:
            ret=main(["--case",str(self.case),"--out",str(target)])
            read.assert_not_called()
        self.assertEqual(ret,2)


if __name__=="__main__":
    unittest.main()
