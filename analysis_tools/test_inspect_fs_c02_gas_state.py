"""Synthetic tests for FS-C02 postrun p-rho-U gas proxy, zero CFD."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

from inspect_fs_c02_gas_state import (
    R_AIR, evaluate_cells, read_scalar, read_vector_magnitude, run_analysis,
)
from audit_fs_c02_local import EXPECTED_CELLS
from run_fs_c02_local import stage


def scalar_file(name, values):
    data = " ".join(str(v) for v in values)
    return (
        "FoamFile { class volScalarField; object " + name + "; }\n"
        "internalField nonuniform List<scalar>\n"
        + str(len(values)) + "\n(\n" + data + "\n);\nboundaryField {}\n"
    )


class GasStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fs-c02-gas-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / "FS-C02_EXTENDED_synthetic"
        self.case, status = stage(self.run, extended_probe=True)
        status["status"] = "PROBE_COURANT_SCREEN_PASSED"
        status["solver_tested_on_real_openfoam"] = True
        (self.run / "FS-C02_RUN_STATUS.json").write_text(json.dumps(status))
        self.alpha = [1.0]*6400 + [0.0]*(EXPECTED_CELLS-6400)
        self.T = [1500.0]*6400 + [700.0]*(EXPECTED_CELLS-6400)
        self.p = [100000.0]*EXPECTED_CELLS
        self.rho = [6820.0]*6400 + [100000/(R_AIR*700)]*(EXPECTED_CELLS-6400)
        for t in (.001, .006, .01):
            folder = self.case / str(t)
            folder.mkdir()
            for name,vals in (("alpha.metal",self.alpha),("T",self.T),
                              ("p",self.p),("rho",self.rho)):
                (folder/name).write_text(scalar_file(name,vals))
            (folder/"U").write_text(
                "FoamFile { class volVectorField; object U; }\n"
                "internalField uniform (0 0 0.5);\n"
                "boundaryField {}\n"
            )

    def test_gas_pressure_density_speed_and_ideal_relation(self):
        report = run_analysis(self.run)
        self.assertEqual(report["status"],
                         "GAS_STATE_DESCRIPTIVE_NOT_PHYSICALLY_VALIDATED")
        self.assertEqual(report["archived_times_checked"], 3)
        self.assertEqual(report["sampled_times"], [.001,.006,.01])
        self.assertTrue(report["not_energy_or_phase_mass_balance"])
        r = report["records"][-1]
        self.assertEqual(r["near_pure_air_cells_alpha_le_1e_minus_6"],3200)
        self.assertEqual(r["near_pure_air_T_K"]["mean"],700.0)
        self.assertEqual(r["near_pure_air_speed_m_s"]["mean"],0.5)
        self.assertAlmostEqual(r["ideal_gas_p_over_rhoRT_near_pure_air"]["mean"],1)
        self.assertEqual(r["near_pure_air_hot_gt1000K_cells"],0)

    def test_missing_archived_rho_fails_closed(self):
        (self.case/"0.01"/"rho").unlink()
        with self.assertRaisesRegex(ValueError,"saved field missing: rho"):
            run_analysis(self.run)

    def test_negative_pressure_is_blocked(self):
        bad=self.p.copy()
        bad[7000]=-1
        (self.case/"0.01"/"p").write_text(scalar_file("p",bad))
        with self.assertRaisesRegex(ValueError,"nonpositive absolute p"):
            run_analysis(self.run)

    def test_missing_U_fails_closed(self):
        (self.case/"0.01"/"U").unlink()
        with self.assertRaisesRegex(ValueError,"saved field missing: U"):
            run_analysis(self.run)

    def test_imported_volVector_and_volScalar_uniform(self):
        folder=self.case/"0.01"
        self.assertEqual(read_vector_magnitude(folder/"U")[-1],0.5)
        (folder/"p").write_text(
            "FoamFile { class volScalarField; object p; }\n"
            "internalField uniform 100000;\nboundaryField {}\n"
        )
        self.assertEqual(read_scalar(folder/"p","p")[10],100000)

    def test_high_temperature_near_pure_gas_is_explicit(self):
        a=[0.0]*EXPECTED_CELLS
        T=[300.0]*(EXPECTED_CELLS-577)+[1200.0]*577
        rho=[1e5/(R_AIR*t) for t in T]
        stats=evaluate_cells(a,T,[1e5]*EXPECTED_CELLS,rho,[1]*EXPECTED_CELLS)
        self.assertEqual(stats["near_pure_air_hot_gt1000K_cells"],577)
        self.assertAlmostEqual(stats["ideal_gas_p_over_rhoRT_near_pure_air"]["mean"],1)

    def test_input_tamper_blocks_before_gas_diagnostics(self):
        (self.case/"system/controlDict").write_text("modified")
        with self.assertRaisesRegex(ValueError,"modified original solver input"):
            run_analysis(self.run)


if __name__=="__main__":
    unittest.main()
