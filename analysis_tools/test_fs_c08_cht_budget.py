"""Synthetic software regression only, never a CHT simulation."""
import unittest
from fs_c08_cht_budget import audit
from test_fs_c08_transient_ledger import log_at

def fixture(t=1e-6,patch="wall",energy=True):
    lines=log_at(t).splitlines()
    for i,line in enumerate(lines):
        if "FS_C08_REAL_CFD_MASS_BUDGET" in line:
            # Synthetic E change balances 2 W conduction + 1 W advection.
            lines[i]=line.replace("totalInternalEnergyEquationBalance_J=1.0",
                                 "totalInternalEnergyEquationBalance_J=0")
            lines[i]+=(" deltaInternalEnergy_J=-3e-6 nativeEnergySolveAdvectionOut_W=1"
                       " nativeEnergySolveConductionOut_W=2 nativeMechanicalWork_W=0"
                       " mushyDarcyDissipation_W=0 pressureCorrectionEnergyGap_J=0"
                       " boundaryMetalOut_kg_s=0 gasBoundaryOut_kg_s=0")
    lines.append(f"FS_C08_REAL_CFD_PATCH_BUDGET time_s={t} patch={patch}"
                 " liquidMetalIn_kg_s=0 liquidMetalOut_kg_s=0 signedGasOut_kg_s=0"
                 " signedCHTHeatOut_W=2 energySolverAdvectedOut_W=1")
    lines.append(f"FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED time_s={t}")
    if energy:
        lines.append(f"FS_C08_FINAL_COUPLED_ENERGY_AUDIT_PASS time_s={t}")
    return "\n".join(lines)

class CHTBudgetTest(unittest.TestCase):
    def test_printed_balance_and_integrals(self):
        r=audit(fixture(),["wall"])
        self.assertEqual(len(r["eligible_records"]),1)
        self.assertAlmostEqual(r["eligible_records"][0]["reconstructed_printed_fluid_balance_J"],0)
        self.assertAlmostEqual(r["prefix_patch_integrals"]["wall"]["signedConductionOut_J"],2e-6)
        self.assertFalse(r["global_CHT_energy_verified"])

    def test_no_bridge_missing_step(self):
        r=audit(fixture()+"\n"+fixture(3e-6),["wall"])
        self.assertEqual(len(r["eligible_records"]),2)
        self.assertEqual(r["contiguous_prefix_end_s"],1e-6)
        self.assertFalse(r["prefix_reaches_last_observed_time"])

    def test_patch_inventory_and_duplicate(self):
        self.assertFalse(audit(fixture(),["wall","other"])["eligible_records"])
        log=fixture()
        patch=next(x for x in log.splitlines() if "PATCH_BUDGET" in x)
        self.assertFalse(audit(log+"\n"+patch,["wall"])["eligible_records"])

    def test_strict_gate(self):
        self.assertFalse(audit(fixture(energy=False),["wall"])["eligible_records"])
        self.assertEqual(len(audit(fixture(energy=False),["wall"],False)["eligible_records"]),1)

    def test_no_invented_initial_interval(self):
        r=audit(fixture(2e-6),["wall"])
        self.assertEqual(len(r["eligible_records"]),1)
        self.assertIsNone(r["prefix_patch_integrals"])
        self.assertFalse(r["prefix_reaches_last_observed_time"])

if __name__=="__main__":
    unittest.main()
