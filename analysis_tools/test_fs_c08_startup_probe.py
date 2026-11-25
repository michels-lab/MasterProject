"""Numerical startup-probe staging checks; not a CFD validation."""
import unittest
from stage_fs_c08_coupled import startup_probe_controls

CONTROL = """startFrom startTime;
startTime 0;
stopAt endTime;
endTime 1;
deltaT 1e-7;
adjustTimeStep yes;
maxDeltaT 1e-4;
maxCo 0.1;
writeControl adjustableRunTime;
writeInterval 0.05;
"""

class StartupProbeTest(unittest.TestCase):
    def test_one_fixed_step(self):
        staged = startup_probe_controls(CONTROL, 1e-6)
        self.assertIn("endTime 1e-06;", staged)
        self.assertIn("deltaT 1e-06;", staged)
        self.assertIn("adjustTimeStep no;", staged)
        self.assertIn("writeControl timeStep;", staged)
        self.assertIn("writeInterval 1;", staged)
        self.assertIn("maxDeltaT 1e-4;", staged)
        self.assertIn("maxCo 0.1;", staged)
        self.assertIn("endTime 1;", CONTROL)

    def test_reject_invalid_dt(self):
        for dt in (0, -1, float("nan"), float("inf"), 2e-4):
            with self.subTest(dt=dt), self.assertRaises(ValueError):
                startup_probe_controls(CONTROL, dt)

    def test_reject_nonzero_start_or_ambiguous_controls(self):
        for ctrl in (CONTROL.replace("startTime 0;", "startTime 1;"),
                     CONTROL + "\ndeltaT 2e-7;\n"):
            with self.assertRaises(ValueError):
                startup_probe_controls(ctrl, 1e-6)

if __name__ == "__main__":
    unittest.main()
