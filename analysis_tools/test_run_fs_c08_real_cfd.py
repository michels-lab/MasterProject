#!/usr/bin/env python3
"""Contracts for the REAL CFD evidence gate; no CFD or synthetic solver run."""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from run_fs_c08_real_cfd import (inspect_real_cfd_budgets, require_native_end_time,
                                 first_native_error, inspect_coupled_volume_closure)
from stage_fs_c08_coupled import add_phase_mass_solvers


def native_log(
    time: float = 0.05, metal_residual: float = 0.0,
    gas_residual: float = 0.0, include_last_mass_gate: bool = True,
    energy_residual: str = "0.005",
) -> str:
    # SOFTWARE-ONLY fabricated log lines. NEVER physical material or CFD data.
    budget = (
        f"FS_C08_REAL_CFD_MASS_BUDGET time_s={time} "
        "liquidSolidMetalMass_kg=0.042 previousMetalMass_kg=0.042 "
        f"metalMassResidual_kg={metal_residual} "
        "nativeGasInventory_kg=0.001 previousGasInventory_kg=0.001 "
        f"gasContinuityDefect_kg={gas_residual} "
        "gasMassBudgetTolerance_kg=1e-9 "
        f"totalInternalEnergyEquationBalance_J={energy_residual} "
        "pressureCorrectionEnergyGap_J=1e-5 "
        "phaseChangeVolumeSourceMean_s_1=-2e-8 "
        "combinedMaterialVolumeSourceMean_s_1=-3e-8"
    )
    lines = [f"FS_C08_NATIVE_PHASE_RESOLVED_INTERNAL_ENERGY time_s={time}",
             budget]
    if include_last_mass_gate:
        lines.append(
            "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED "
            f"time_s={time} gasResidual_kg={gas_residual} "
            f"metalResidual_kg={metal_residual}"
        )
    return "\n".join(lines)


class RealCFDBudgetEvidenceTests(unittest.TestCase):
    def test_real_log_numbers_accepted_but_energy_not_validated(self):
        got = inspect_real_cfd_budgets(native_log(), 0.05)
        self.assertEqual(got["numeric_budget_records"], 1)
        self.assertTrue(got["all_native_mass_budget_records_checked"])
        self.assertFalse(got["global_energy_verified"])
        self.assertFalse(got["physical_casting_shrinkage_validated"])
        self.assertAlmostEqual(
            got["final_native_mass_energy_budget"]["pressureCorrectionEnergyGap_J"],
            1e-5,
        )

    def test_missing_last_mass_gate_rejected(self):
        with self.assertRaisesRegex(ValueError, "last saved"):
            inspect_real_cfd_budgets(native_log(include_last_mass_gate=False), 0.05)

    def test_last_saved_snapshot_is_not_earlier_old_gate(self):
        with self.assertRaisesRegex(ValueError, "last saved"):
            inspect_real_cfd_budgets(native_log(time=0.02), 0.05)

    def test_metal_mass_defect_rejected(self):
        with self.assertRaisesRegex(ValueError, "metal mass balance"):
            inspect_real_cfd_budgets(native_log(metal_residual=0.0001), 0.05)

    def test_gas_mass_defect_rejected(self):
        with self.assertRaisesRegex(ValueError, "gas mass balance"):
            inspect_real_cfd_budgets(native_log(gas_residual=1e-5), 0.05)

    def test_nonfinite_energy_is_never_a_valid_numeric_report(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            inspect_real_cfd_budgets(native_log(energy_residual="nan"), 0.05)

    def test_requested_end_time_parsed_from_actual_control_dict(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "controlDict"
            path.write_text("startTime 0;\nendTime 1;\n")
            self.assertEqual(require_native_end_time(path), 1.0)

    def test_missing_or_duplicate_end_time_blocked(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "controlDict"
            for data in ("startTime 0;\n",
                         "endTime 0.5;\nendTime 1;\n"):
                path.write_text(data)
                with self.assertRaisesRegex(RuntimeError, "exactly one"):
                    require_native_end_time(path)

    def test_coupled_volume_gate_accepts_only_converged_local_step(self):
        iteration = ("FS_C08_COUPLED_VOLUME_ENERGY_ITER time_s=0.05 "
                     "maxVolumeResidual=1e-13 maxDeltaT_K=1e-7 "
                     "maxPhaseReplayRelative=1e-11 maxMetalOverfill=1e-13 "
                     "maxLocalMetalContinuity=1e-12 maxLocalGasContinuity=1e-12")
        pressure = ("FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY time_s=0.05 "
                    "gasEOSMismatch=1e-13 pressureVolumeEnergyIterationConverged=1")
        log = iteration + "\n" + pressure
        self.assertEqual(inspect_coupled_volume_closure(log, 0.05)
                         ["accepted_pressure_closure_records"], 1)
        for bad in (log.replace("maxVolumeResidual=1e-13", "maxVolumeResidual=1e-5"),
                    log.replace("maxLocalGasContinuity=1e-12", "maxLocalGasContinuity=1e-3"),
                    log.replace("gasEOSMismatch=1e-13", "gasEOSMismatch=nan"),
                    pressure, iteration):
            with self.assertRaises(ValueError):
                inspect_coupled_volume_closure(bad, 0.05)

    def test_empty_log_rejected(self):
        with self.assertRaisesRegex(ValueError, "no actual"):
            inspect_real_cfd_budgets("End\n", 0.05)


    def test_final_pimple_entries_generated_for_each_mass_field(self):
        import re
        original = "solvers\n{\n    p_rgh { solver PCG; }\n}\n"
        staged = add_phase_mass_solvers(original)
        for name in ("rhoAlpha.liquid", "rhoAlpha.solid"):
            for suffix, rel_tol in (("", "0.01"), ("Final", "0")):
                match = re.search(re.escape(name + suffix) + r"\s*\{([^}]+)\}", staged)
                self.assertIsNotNone(match)
                self.assertRegex(match[1], r"relTol\s+" + re.escape(rel_tol) + ";")
        self.assertIn("p_rgh { solver PCG; }", staged)

    def test_symmetric_temperature_solver_overrides_inherited_dilu(self):
        import re
        original = ('solvers\n{\n'
                    '    "T.*" { solver PBiCGStab; preconditioner DILU; }\n'
                    '    T { solver PBiCGStab; preconditioner DILU; }\n'
                    '    "TFinal" { $T; relTol 0; }\n'
                    '    U { solver PBiCGStab; preconditioner DILU; }\n}\n')
        staged = add_phase_mass_solvers(original)
        for key in ("T", "TFinal"):
            matches = re.findall(r"(?m)^\s*" + key + r"\s*\{([^}]+)\}", staged)
            self.assertEqual(len(matches), 1)
            self.assertRegex(matches[0], r"solver\s+PCG;")
            self.assertRegex(matches[0], r"preconditioner\s+DIC;")
            self.assertRegex(matches[0], r"relTol\s+0;")
        self.assertNotIn('"TFinal"', staged)
        self.assertIn('"T.*" { solver PBiCGStab; preconditioner DILU; }', staged)
        self.assertIn('U { solver PBiCGStab; preconditioner DILU; }', staged)
        self.assertRegex(staged, r"rhoAlpha\.liquidFinal\s*\{[^}]*preconditioner\s+diagonal;")

    def test_fatal_io_details_not_masked_by_sigfpe_startup(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "foamMultiRun.log"
            path.write_text("sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).\n"
                            "--> FOAM FATAL IO ERROR:\n"
                            "keyword rhoAlpha.liquidFinal is undefined in dictionary\n")
            self.assertIn("rhoAlpha.liquidFinal", first_native_error(path))
            path.write_text("sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).\n")
            self.assertIsNone(first_native_error(path))

    def test_actual_floating_point_exception_still_detected(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "foamMultiRun.log"
            path.write_text("sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).\n"
                            "Floating point exception (core dumped)\n")
            self.assertEqual(first_native_error(path), "Floating point exception (core dumped)")


if __name__ == "__main__":
    unittest.main()
