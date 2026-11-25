"""Regression for unordered cadence entries, using compact campaign fixtures."""
import tempfile
import unittest
from pathlib import Path
import compact_campaign_200s as compact
import run_adaptive_campaign_200s as adaptive
from test_compact_campaign_200s import TestCompact

class AdaptiveCadence(unittest.TestCase):
    def test_inverted_and_nonadjacent(self):
        old="topFlow\n{\n    writeInterval 100;\n    executeInterval 100;\n    log true;\n    writeControl timeStep;\n    executeControl timeStep;\n}\n"
        new,n=adaptive.convert_cadence(old,"functions")
        self.assertEqual(n,2)
        self.assertIn("writeInterval 0.1;",new)
        self.assertIn("executeControl adjustableRunTime;",new)
    def fixture(self,family,three=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            TestCompact().fixture(root,family,three)
            compact.config(root,"3DA" if three else "2D")
            f=root/"system/functions"
            probe=compact.blocks(f.read_text())["temperatureProbe"][2]
            m=root/"system/researchDiagnostics"
            momentum=compact.blocks(m.read_text())[compact.MOMENTUM][2]
            adaptive.adapt_dicts(root)
            self.assertEqual(probe,compact.blocks(f.read_text())["temperatureProbe"][2])
            self.assertEqual(momentum,compact.blocks(m.read_text())[compact.MOMENTUM][2])
            self.assertRegex(f.read_text(),r"writeControl\s+adjustableRunTime;")
            control=(root/"system/controlDict").read_text()
            self.assertNotRegex(control,r"(?m)^\s*maxDeltaT\s")
            self.assertRegex(control,r"adjustTimeStep\s+yes;")
            self.assertRegex(control,r"maxCo\s+0\.25;")
            for p in ("functions","researchDiagnostics","lineProfiles","compactNearTop")+ (("additional3DProfiles",) if three else ()):
                self.assertNotRegex((root/"system"/p).read_text(),r"(?m)^\s*(?:execute|write)Interval\s+100\s*;")
    def test_b14(self):self.fixture("B14")
    def test_c14(self):self.fixture("C14")
    def test_3da(self):self.fixture("C14",True)
if __name__=="__main__":unittest.main()
