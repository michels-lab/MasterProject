#!/usr/bin/env python3
"""Contracts for the REAL CFD evidence gate; no CFD or synthetic solver run."""
from __future__ import annotations

import unittest

from run_fs_c08_real_cfd import inspect_real_cfd_budgets


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

    def test_empty_log_rejected(self):
        with self.assertRaisesRegex(ValueError, "no actual"):
            inspect_real_cfd_budgets("End\n", 0.05)


if __name__ == "__main__":
    unittest.main()
