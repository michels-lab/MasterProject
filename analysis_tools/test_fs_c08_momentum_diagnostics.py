"""Synthetic parser tests, not new CFD evidence."""
import unittest
from fs_c08_momentum_diagnostics import parse

FORCE=("FS_C08_MOMENTUM_FORCE_SPLIT time_s=1e-6 cell=3 alphaMetal=0 "
       "speed_m_s=5 HbyA_m_s=(3 0 0) pressureContribution_m_s=(-3 4 0) "
       "gravitySurfaceContribution_m_s=(0 0 0) maxTemporalFaceCorrection_m_s=1 diagnosticOnly=1")

class MomentumDiagnosticsTest(unittest.TestCase):
    def test_vector_sum_not_sum_of_norms(self):
        result=parse(FORCE)
        self.assertFalse(result["issues"])
        row=result["diagnostic_records"][0]
        self.assertEqual(row["frozen_direct_velocity_norm_m_s"],4)
        self.assertEqual(row["direct_minus_accepted_speed_m_s"],-1)

    def test_duplicate_and_invalid_vector(self):
        self.assertFalse(parse(FORCE+"\n"+FORCE)["diagnostic_records"])
        self.assertTrue(parse(FORCE.replace("(3 0 0)","(nan 0 0)"))["issues"])

    def test_startup_has_no_invented_time(self):
        r=parse("FS_C08_STARTUP_PRESSURE_COMPONENT dt_s=1e-6 source=phase "
                "minDpCell=3 dpAtMinCell_Pa=-20 minDp_Pa=-25 maxDp_Pa=4 localResidual=.01")
        self.assertFalse(r["issues"])
        self.assertNotIn("time_s",r["startup_records"][0])
        self.assertFalse(r["force_or_acceleration_validated"])

if __name__=="__main__":
    unittest.main()
