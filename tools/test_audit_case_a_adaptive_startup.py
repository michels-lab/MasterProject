import tempfile
import unittest
from pathlib import Path
from audit_case_a_adaptive_startup import audit, compare

class StartupAudit(unittest.TestCase):
    def test_native_suffix_and_negative_temperature(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"log.foamMultiRun"
            p.write_text("sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).\nCourant Number mean: 0.1 max: 0.2\ndeltaT = 0.02\nTime = 0.68s\nSolving for fluid region metal\nPBiCGStab: Solving for h, Initial residual = 0.4, Final residual = 1e-8, No Iterations 7\nFOAM FATAL ERROR:\nNegative initial temperature T0: -139.17\n")
            r=audit(p)
            self.assertEqual(r["startup_steps"][0]["deltaT_s"],.02)
            self.assertEqual(r["startup_steps"][0]["solves"]["metal/h"]["max_iterations"],7)
            self.assertEqual(len(r["fatal_events"]),2)
            self.assertEqual(r["fatal_events"][-1]["negative_T0_K"],-139.17)
            self.assertFalse(r["end_marker"])
            self.assertEqual(compare(r,r)["different_inputs"],[])
    def test_horizon_and_no_end_false_positive(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"log.foamMultiRun"
            p.write_text("Time = 0.001s\nTime = 1s\nEnd\n")
            r=audit(p)
            self.assertEqual(len(r["startup_steps"]),1)
            self.assertEqual(r["last_logged_time_s"],1)
            self.assertTrue(r["end_marker"])
    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"log.foamMultiRun"
            p.write_text("startup only\n")
            with self.assertRaises(ValueError): audit(p)

if __name__=="__main__":
    unittest.main()
