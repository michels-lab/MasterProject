"""Synthetic software contracts; no CFD evidence."""
import tempfile
import unittest
from pathlib import Path
from compare_fs_c08_momentum import compare_variant, unique_ticks
from run_fs_c08_real_cfd import REQUIRED_FINAL_FIELDS
from test_fs_c08_transient_ledger import log_at
from test_fs_c08_momentum_diagnostics import FORCE

def fixture(t=1e-6, extreme_cell=3):
    # Existing ledger fixture uses native dt=1 microsecond and maxU=1.
    time=str(t)
    force=FORCE.replace("time_s=1e-6","time_s="+time).replace("speed_m_s=5","speed_m_s=1")
    consistency=("FS_C08_MOMENTUM_CONSISTENCY time_s="+time+
        " maxVelocityGap_m_s=0 maxDirectPressureSpeed_m_s=1 maxPureGasVelocityGap_m_s=0"
        " maxPureGasSpeed_m_s=1 maxInternalFaceNormalGap_m_s=0 cell=3")
    extreme=("FS_C08_ACCEPTED_EXTREME_CELL time_s="+time+
        " reason=maximumSpeed cell="+str(extreme_cell)+" center_m=(0 0 0) alphaGas=1"
        " speed_m_s=1 p_Pa=100000 pOld_Pa=100000 T_K=300 Told_K=300"
        " storage_J_m3=0 advectionOut_J_m3=0 conductionOut_J_m3=0 mechanicalWork_J_m3=0")
    mass="FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED time_s="+time
    # log_at emits pressure convergence as 1.0; actual native marker is integer 1.
    ledger=log_at(t).replace("pressureVolumeEnergyIterationConverged=1.0",
                             "pressureVolumeEnergyIterationConverged=1")
    return "\n".join((ledger,force,consistency,extreme,mass))

class CommonMomentumTest(unittest.TestCase):
    def run_case(self, log, strict=False, saved=True):
        with tempfile.TemporaryDirectory() as d:
            case=Path(d)/"1e-6"
            (case/"fluid").mkdir(parents=True)
            if saved:
                for field in REQUIRED_FINAL_FIELDS:
                    (case/"fluid"/field).touch()
            return compare_variant(log,[(1e-6,case)],1e-6,1,1.25e-7,strict)

    def test_join_complete_native_state(self):
        rows,meta=self.run_case(fixture())
        self.assertEqual(list(rows),[8])
        self.assertEqual(rows[8]["state"]["maxU_m_s"],1)
        self.assertEqual(rows[8]["maximum_speed_cell"]["center_m"],[0,0,0])
        self.assertIsNone(rows[8]["fresh_matrix_defect_domain_maxima"])
        self.assertEqual(meta["joined_steps"],1)

    def test_mismatched_cells_excluded(self):
        rows,meta=self.run_case(fixture(extreme_cell=4))
        self.assertFalse(rows)
        self.assertIn("cell identity",meta["excluded"]["1"])

    def test_missing_strict_energy_or_fields_excluded(self):
        self.assertFalse(self.run_case(fixture(),strict=True)[0])
        self.assertFalse(self.run_case(fixture(),saved=False)[0])

    def test_duplicate_tick_excluded(self):
        self.assertFalse(unique_ticks([{"time_s":1e-6},{"time_s":1e-6+1e-14}],1e-6))

    def test_missing_momentum_or_duplicate_marker_excluded(self):
        log=fixture()
        incomplete="\n".join(x for x in log.splitlines() if "MOMENTUM_CONSISTENCY" not in x)
        self.assertFalse(self.run_case(incomplete)[0])
        self.assertFalse(self.run_case(log+"\n"+FORCE)[0])

if __name__=="__main__":
    unittest.main()
