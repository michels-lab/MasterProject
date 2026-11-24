"""Regression for the grouped native offline gate; no native CFD fixture."""
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_c14_stage07_grouped_native_recovery as grouped

class GroupedRecoveryTests(unittest.TestCase):
    def test_exact_byte_delta(self):
        src=b"phaseChangeSource\n{\n    cellZone        metal;\n    Tsol 1423;\n}\n"
        self.assertEqual(grouped.replace_selection(src),
                         src.replace(b"metal;",b"all;"))
    def test_reject_missing_or_duplicate_zone(self):
        for src in (b"cellZone other;",b"cellZone metal;\ncellZone metal;"):
            with self.assertRaises(ValueError):
                grouped.replace_selection(src)
    def test_compare_numeric(self):
        result=grouped.compare([0.,1.,10.],[0.,1.,10.])
        self.assertEqual(result["absolute_differences_J"],[0.,0.,0.])
        for got in ([0.,2.,10.],[math.nan,1.,10.],[0.,1.]):
            with self.assertRaises(ValueError):
                grouped.compare(got,[0.,1.,10.])
    def test_strict_time_axis_and_finite_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"volFieldValue.dat"
            p.write_text("# Time volIntegrate(rho,h)\n0 1\n0.1 2\n10 3\n")
            self.assertEqual(grouped.scalar_table(p,grouped.H,[0,.1,10]),[1,2,3])
            for rows in ("0 1\n0.1 2\n","0 1\n0.1 2\n0.1 3\n",
                         "0 1\n0.1 nan\n10 3\n","0 1\n0.1 2\n10 3\n10 4\n"):
                p.write_text("# Time volIntegrate(rho,h)\n"+rows)
                with self.assertRaises(ValueError):
                    grouped.scalar_table(p,grouped.H,[0,.1,10])
    def test_full_time_axis(self):
        self.assertEqual(len(grouped.TIMES),101)
        self.assertEqual(grouped.TIMES[1],.1)
        self.assertEqual(grouped.TIMES[-1],10.)

if __name__=="__main__":
    unittest.main()
