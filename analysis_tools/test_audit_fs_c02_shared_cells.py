"""No-CFD FS-C02 exact common-cell temperature and alpha-motion audit tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c02_local import EXPECTED_CELLS
from audit_fs_c02_shared_cells import analyze, evaluate_same_cells
from run_fs_c02_local import INITIAL_VOLUME, stage
from run_fs_c02_laminar_control import prepare


def scalar_file(name: str, values: list[float]) -> str:
    return (
        "FoamFile { class volScalarField; object "+name+"; }\n"
        "internalField nonuniform List<scalar>\n"
        +str(len(values))+"\n(\n"
        +"\n".join(str(x) for x in values)
        +"\n);\nboundaryField {}\n"
    )


class SharedCellsTests(unittest.TestCase):
    def test_shared_cells_excludes_unmatched_phase_masks(self):
        a=[1.0]*6400 + [0.0]*(EXPECTED_CELLS-6400)
        b=a.copy()
        a[6400]=.5
        b[6401]=.5
        t_a=[1500.0]*6400 + [745.0]*(EXPECTED_CELLS-6400)
        t_b=[1500.0]*6400 + [390.0]*(EXPECTED_CELLS-6400)
        r=evaluate_same_cells(a,t_a,b,t_b,b,b)
        self.assertEqual(r["same_near_pure_gas_cells_both_models"],3198)
        self.assertEqual(r["near_pure_gas_cells_only_RAS"],1)
        self.assertEqual(r["near_pure_gas_cells_only_laminar"],1)
        self.assertEqual(r["common_cells_RAS_minus_laminar_T_K"],355.)
        self.assertEqual(r["RAS_alpha_motion_since_first_saved_time"]
                         ["alpha_cells_changed_above_1e_minus_6"],2)
        self.assertEqual(r["laminar_alpha_motion_since_first_saved_time"]
                         ["alpha_cells_changed_above_1e_minus_6"],0)
        self.assertEqual(r["RAS_alpha_motion_since_first_saved_time"]
                         ["meaningful_interface_cells_0_01_to_0_99"],1)

    def test_exact_same_pure_gas_set_must_be_nonempty(self):
        a=[1.0]*EXPECTED_CELLS
        b=[0.0]*EXPECTED_CELLS
        t=[400.0]*EXPECTED_CELLS
        with self.assertRaisesRegex(ValueError,"no common"):
            evaluate_same_cells(a,t,b,t,a,b)

    def test_invalid_temperature_or_alpha_blocked(self):
        a=[0.0]*EXPECTED_CELLS
        t=[300.0]*EXPECTED_CELLS
        a[0]=1.25
        with self.assertRaisesRegex(ValueError,"invalid alpha"):
            evaluate_same_cells(a,t,a,t,a,a)
        a[0]=0
        t[0]=-1
        with self.assertRaisesRegex(ValueError,"invalid temperature"):
            evaluate_same_cells(a,t,a,t,a,a)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c02-shared-")
        self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.ras=base/"FS-C02_EXTENDED_synthetic"
        self.lam=base/"FS-C02_LAMINAR_synthetic"
        self.ref_case,ra=stage(self.ras,extended_probe=True)
        self.lam_case,la=prepare(self.lam)
        for root,case,status,Tgas in (
            (self.ras,self.ref_case,ra,745.),
            (self.lam,self.lam_case,la,390.),
        ):
            status["solver_tested_on_real_openfoam"]=True
            status["status"]="PROBE_COURANT_SCREEN_PASSED"
            status["stages"]=[
                {"stage":s,"returncode":0,"gate_passed":True}
                for s in ("blockMesh","checkMesh","foamRun")]
            (root/"FS-C02_RUN_STATUS.json").write_text(json.dumps(status))
            v=case/"postProcessing/metalVolume/0/volFieldValue.dat"
            v.parent.mkdir(parents=True)
            v.write_text(
                "# Time volIntegrate(alpha.metal)\n"
                f"0 {INITIAL_VOLUME}\n"
                f"0.001 {INITIAL_VOLUME}\n"
                f"0.006 {INITIAL_VOLUME}\n"
                f"0.01 {INITIAL_VOLUME}\n")
            (root/"logs/FS-C02_foamRun.log").write_text(
                "Courant Number mean: 0.01 max: 0.16\n"
                "Interface Courant Number mean: 0 max: 0.002\n"
                "Courant Number mean: 0.01 max: 0.01\n"
                "Interface Courant Number mean: 0 max: 0.001\nEnd\n"
            )
            for t in (0.001,0.006,0.01):
                folder=case/str(t)
                folder.mkdir()
                alpha=[1.0]*6400+[0.0]*(EXPECTED_CELLS-6400)
                if root==self.ras and t!=0.001:
                    alpha[6399]=.5
                    alpha[6400]=.5
                T=[1500.0]*6400+[Tgas]*(EXPECTED_CELLS-6400)
                (folder/"alpha.metal").write_text(scalar_file("alpha.metal",alpha))
                (folder/"T").write_text(scalar_file("T",T))

    def test_pair_reports_shared_mask_and_movement_vs_first_saved(self):
        orig=(self.lam_case/"0.01/T").read_bytes()
        r=analyze(self.ras,self.lam)
        self.assertEqual(r["snapshots_compared"],3)
        self.assertEqual(r["unchanged_solver_inputs"],18)
        self.assertEqual(r["changed_solver_inputs"],
                         ["constant/fvModels","constant/momentumTransport"])
        self.assertEqual(r["first_time_s"],.001)
        self.assertEqual(r["final_time_s"],.01)
        self.assertEqual(r["final_common_near_pure_gas_cell_count"],3199)
        self.assertAlmostEqual(r["final_common_cells_temperature_gap_K"],355)
        self.assertEqual(r["final_RAS_interface_cell_count"],2)
        self.assertEqual(r["final_laminar_interface_cell_count"],0)
        self.assertTrue(r["laminar_alpha_unchanged_since_first_saved_step"])
        self.assertGreater(r["records"][-1]
                          ["RAS_alpha_motion_since_first_saved_time"]
                          ["alpha_L1_changed_volume_equivalent_m3"],0)
        self.assertEqual(
            r["records"][-1]["laminar_alpha_motion_since_first_saved_time"]
            ["alpha_L1_changed_volume_equivalent_m3"],0
        )
        self.assertFalse(r["records"][-1]["energy_conservation_physically_verified"])
        self.assertFalse(r["records"][-1]
                         ["free_surface_height_or_interface_velocity_measured"])
        self.assertEqual((self.lam_case/"0.01/T").read_bytes(),orig)

    def test_modified_first_snapshot_changes_alpha_motion_reference(self):
        a=self.ref_case/"0.001/alpha.metal"
        vals=[1.0]*6400+[0.0]*(EXPECTED_CELLS-6400)
        vals[6399]=.5
        vals[6400]=.5
        a.write_text(scalar_file("alpha.metal",vals))
        r=analyze(self.ras,self.lam)
        self.assertEqual(
            r["records"][-1]["RAS_alpha_motion_since_first_saved_time"]
            ["alpha_cells_changed_above_1e_minus_6"],0
        )

    def test_nonmatching_mesh_or_stale_saved_field_fails(self):
        (self.lam_case/"system/blockMeshDict").write_text("bad")
        with self.assertRaisesRegex(ValueError,"altered original input"):
            analyze(self.ras,self.lam)


if __name__=="__main__":
    unittest.main()
