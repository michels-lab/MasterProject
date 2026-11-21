#!/usr/bin/env python3
"""Numerical T0 energy and solver-log forensics from real inputs/synthetic tests only."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

T0 = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    instance = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(instance)
    return instance

E = load("case_b_energy", T0 / "scripts/t0_energy_reference.py")
A = load("case_b_solver_audit", T0 / "scripts/audit_t0_numerical_run.py")
REF = load("case_b_c14_reference", T0 / "scripts/c14_numerical_reference.py")
R = load("case_b_preserved_run_review", T0 / "scripts/review_preserved_t0_run.py")


class NumericalEnergy(unittest.TestCase):
    def test_formula_equilibrium_exact_capacity_weights(self):
        materials = {
            "metal": {"rho_kg_m3": 1, "Cv_J_kg_K": 2, "T_initial_K": 400},
            "mold": {"rho_kg_m3": 2, "Cv_J_kg_K": 2, "T_initial_K": 300}
        }
        expected = E.energy_target(materials, {"metal": 1, "mold": 1})
        self.assertAlmostEqual(expected["ideal_closed_system_equilibrium_temperature_K"], (2*400+4*300)/6)
        self.assertAlmostEqual(expected["total_initial_sensible_energy_relative_to_zero_K_J"], 2000)
        self.assertAlmostEqual(expected["total_thermal_capacity_J_per_K"], 6)
        self.assertFalse(expected["energy_closure_observed"])

    def test_native_log_requires_positive_volume_and_mesh_ok(self):
        self.assertEqual(E.native_volume("Total volume = 4.797e-05. Cell volumes OK.\nMesh OK.\n"), 4.797e-5)
        with self.assertRaises(ValueError):
            E.native_volume("Total volume = -1.\nMesh OK.\n")
        with self.assertRaises(ValueError):
            E.native_volume("Total volume = 1.5.\nFailed 3 mesh checks.\n")

    def test_energy_report_reads_actual_log_bytes_not_literature_volume(self):
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            params = folder / "input.json"
            params.write_text(json.dumps(REF.build()), encoding="utf-8")
            for reg, volume in (("metal", "4.7987697e-5"), ("mold", "1.02843333e-4")):
                (folder / f"log.checkMesh.{reg}").write_text(
                    f"Total volume = {volume}. Cell volumes OK.\nMesh OK.\n", encoding="utf-8")
            result = E.make_report(params, folder)
            self.assertEqual(len(result["native_logs"]), 2)
            self.assertEqual(len(result["input_file_sha256"]), 64)
            self.assertGreater(result["ideal_closed_system_equilibrium_temperature_K"], 300)
            self.assertLess(result["ideal_closed_system_equilibrium_temperature_K"], 1500)
            target = folder / "energy.json"
            self.assertEqual(E.write_exclusive(target, result), "REFERENCE_ENERGY_TARGET_WRITTEN_NO_SOLVER")
            self.assertEqual(E.write_exclusive(target, result), "ALREADY_PRESENT_IDENTICAL")
            target.write_text("KEEP EXISTING")
            with self.assertRaises(FileExistsError):
                E.write_exclusive(target, result)
            self.assertEqual(target.read_text(), "KEEP EXISTING")

    def test_solver_log_completed_is_numerical_only(self):
        cfg=REF.build()
        log=("Time = 0.001\nSolving for e, Initial residual = 0.02, Final residual = 1e-7\n"
             "Time = 0.05\nTime = 0.1\nExecutionTime = 12 s\nEnd\n")
        result=A.audit(log,0,cfg)
        self.assertTrue(result["numerical_run_completed"])
        self.assertEqual(result["native_energy_equation_linear_solves_observed"], 1)
        self.assertTrue(result["native_energy_residuals_all_finite"])
        self.assertAlmostEqual(result["maximum_initial_energy_residual"], 0.02)
        self.assertAlmostEqual(result["last_final_energy_residual"], 1e-7)
        self.assertFalse(result["energy_conservation_verified"])
        self.assertFalse(result["physical_properties_jmatpro_verified"])
        self.assertIn("NUMERICAL_ONLY",result["status"])

    def test_solver_failure_and_missing_end_are_not_success(self):
        cfg=REF.build()
        self.assertFalse(A.audit("Time = 0.001\nTime = 0.1\n",0,cfg)["numerical_run_completed"])
        self.assertFalse(A.audit("Time = 0.001\nTime = 0.1\nEnd\n",1,cfg)["numerical_run_completed"])
        self.assertFalse(A.audit("Time = 0.001\nTime = 0.1\nFOAM FATAL ERROR\nEnd\n",0,cfg)["numerical_run_completed"])
        self.assertFalse(A.audit("Time = 0.001\nTime = 0.1\nSolving for e, Initial residual = nan\nEnd\n",0,cfg)["numerical_run_completed"])
        self.assertFalse(A.audit("Time = 0.05\nTime = 0.01\nEnd\n",0,cfg)["numerical_run_completed"])
        self.assertFalse(A.audit("End\n",0,cfg)["numerical_run_completed"])
        # A log which only claims time progress and End is not evidence that
        # the 270788-cell solid energy equations were actually solved.
        faked = "Time = 0.001\nTime = 0.1\nEnd\n"
        self.assertFalse(A.audit(faked, 0, cfg)["numerical_run_completed"])
        self.assertEqual(A.audit(faked, 0, cfg)["native_energy_equation_linear_solves_observed"], 0)

    def test_native_f14_seconds_and_sigfpe_banner_are_not_fatal(self):
        cfg = REF.build()
        log = (
            "Enabling floating point exception trapping (FOAM_SIGFPE)\n"
            "Time = 0.001s\n"
            "metal DICPCG: Solving for e, Initial residual = 0.01, Final residual = 1e-7, No Iterations 1\n"
            "mold  DICPCG: Solving for e, Initial residual = 0.003, Final residual = 1e-8, No Iterations 1\n"
            "Time = 0.1s\n"
            "metal DICPCG: Solving for e, Initial residual = 0.001, Final residual = 1e-8, No Iterations 1\n"
            "End\n"
        )
        accepted = A.audit(log, 0, cfg)
        self.assertTrue(accepted["numerical_run_completed"])
        self.assertEqual(accepted["times_observed"], 2)
        self.assertFalse(accepted["fatal_openfoam_pattern"])
        self.assertEqual(accepted["final_time_observed_s"], 0.1)
        self.assertFalse(A.audit(log + "Floating point exception (core dumped)\n", 0, cfg)["numerical_run_completed"])
        self.assertFalse(A.audit(log + "FOAM FATAL IO ERROR\n", 0, cfg)["numerical_run_completed"])
        self.assertFalse(A.audit(log.replace("Time = 0.1s", "Time = 0.09s"), 0, cfg)["numerical_run_completed"])
        self.assertFalse(A.audit(log, 1, cfg)["numerical_run_completed"])

    def test_recover_old_false_negative_with_original_hashes_unchanged(self):
        import hashlib
        cfg = REF.build()
        input_bytes = json.dumps(cfg).encode()
        log_bytes = (
            "Enabling floating point exception trapping (FOAM_SIGFPE)\n"
            "Time = 0.001s\n"
            "metal DICPCG: Solving for e, Initial residual = 0.01, Final residual = 1e-7\n"
            "Time = 0.1s\n"
            "mold DICPCG: Solving for e, Initial residual = 0.001, Final residual = 1e-8\n"
            "End\n"
        ).encode()
        legacy = A.audit(log_bytes.decode(), 0, cfg)
        legacy.update({
            "numerical_run_completed": False,
            "status": "NUMERICAL_ONLY_SOLVER_NOT_VERIFIED_COMPLETE",
            "fatal_openfoam_pattern": True,
            "times_observed": 0,
            "exit_code": 0,
            "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
            "log_sha256": hashlib.sha256(log_bytes).hexdigest(),
        })
        old_bytes = json.dumps(legacy).encode()
        recovered = R.recover(old_bytes, log_bytes, input_bytes)
        self.assertTrue(recovered["numerical_run_completed"])
        self.assertEqual(recovered["original_legacy_status_sha256"], hashlib.sha256(old_bytes).hexdigest())
        self.assertTrue(recovered["recovered_without_solver_rerun"])
        self.assertFalse(recovered["energy_conservation_verified"])
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            R.recover(old_bytes, log_bytes + b"CHANGED", input_bytes)
        with self.assertRaisesRegex(ValueError, "STILL fails"):
            corrupted_log = log_bytes + b"FOAM FATAL ERROR\n"
            corrupted_legacy = {**legacy, "log_sha256": hashlib.sha256(corrupted_log).hexdigest()}
            R.recover(json.dumps(corrupted_legacy).encode(), corrupted_log, input_bytes)
        bad = dict(legacy, exit_code=1)
        with self.assertRaisesRegex(ValueError, "zero-exit"):
            R.recover(json.dumps(bad).encode(), log_bytes, input_bytes)

    def test_run_log_report_preservation(self):
        with TemporaryDirectory() as folder:
            output = Path(folder) / "run.json"
            result={"status":"NUMERICAL_ONLY_SOLVER_NOT_VERIFIED_COMPLETE"}
            self.assertEqual(A.save(output,result),"RUN_ATTEMPT_CLASSIFIED")
            self.assertEqual(A.save(output,result),"RUN_REPORT_EXISTS_IDENTICAL")
            with self.assertRaises(FileExistsError):
                A.save(output,{"status":"INVALID_UNVERIFIED_DATA"})

if __name__=="__main__":
    unittest.main()
