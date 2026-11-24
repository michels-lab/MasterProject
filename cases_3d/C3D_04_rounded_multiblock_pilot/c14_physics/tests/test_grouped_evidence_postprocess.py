import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import continue_c14_stage07_grouped_evidence as c

class GroupedEvidenceTests(unittest.TestCase):
    def test_integral_starts_at_first_noninitial_saved_time(self):
        result=c.integrate([0.,.1,.2,.3],[999.,10.,10.,10.])
        self.assertIsNone(result[0])
        for actual,expected in zip(result[1:],[0.,1.,2.]):
            self.assertAlmostEqual(actual,expected)
    def test_integral_rejects_bad_times(self):
        for t,v in (([0.,.1,.1],[1.,1.,1.]),([0.,.1],[1.,math.nan])):
            with self.assertRaises(ValueError):
                c.integrate(t,v)
    def test_native_chord_does_not_bridge_gap(self):
        result=c.longest_sample_interval([0.,1.,2.,5.,6.,7.,8.],0.,10.,11)
        self.assertEqual(result["start_y_m"],5.5)
        self.assertEqual(result["end_y_m"],7.5)
        self.assertEqual(len(result["contiguous_runs"]),2)
    def test_invalid_coordinates_rejected(self):
        with self.assertRaises(ValueError):
            c.longest_sample_interval([0.,1.2,2.],0.,10.,11)
    def test_profile_rejects_nonfinite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"line.xy"
            p.write_text("0 1\n1 nan\n")
            with self.assertRaises(ValueError):
                c.profile_rows(p)

if __name__=="__main__":
    unittest.main()
