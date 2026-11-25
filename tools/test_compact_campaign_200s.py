"""Static checks with real committed B14/C14 dictionaries, no CFD."""
import tempfile
from pathlib import Path
import shutil
import unittest
import compact_campaign_200s as c

ROOT=Path(__file__).resolve().parents[1]
class TestCompact(unittest.TestCase):
    def fixture(self,root,family,three=False):
        original=ROOT/"cases_controlled_buoyancy"/(family+"_topFixedFlux_explicitRef")
        source=ROOT/"cases_3d/C3D_04_rounded_multiblock_pilot/C14_3D_A_faithful" if three else original
        (root/"system").mkdir()
        for n in ("controlDict","functions","researchDiagnostics","lineProfiles"):
            shutil.copy2(source/"system"/n,root/"system"/n)
        if three:shutil.copy2(source/"system/additional3DProfiles",root/"system/additional3DProfiles")
        p=root/"system/controlDict";p.write_text(c.exact_replace(p.read_text(),r"^(endTime[ \t]+)10([ \t]*;)",r"\g<1>200\2"))
        shutil.copy2(ROOT/"analysis_tools/topSurfaceFlowPostProcessing",root/"system/topSurfaceFlowPostProcessing")
    def check(self,family,three):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.fixture(root,family,three)
            before=(root/"system/researchDiagnostics").read_text()
            changes=c.config(root,"3DA" if three else "2D")
            self.assertEqual(len(changes),6 if three else 5)
            s=(root/"system/controlDict").read_text()
            self.assertRegex(s,r"writeInterval\s+1000;")
            self.assertRegex(s,r"deltaT\s+0\.001;")
            b=c.blocks((root/"system/researchDiagnostics").read_text())
            self.assertEqual(b[c.MOMENTUM][2],c.blocks(before)[c.MOMENTUM][2])
            for n in c.PRODUCERS:
                self.assertRegex(b[n][2],r"executeInterval\s+100;")
                self.assertRegex(b[n][2],r"writeControl\s+writeTime;")
            for n in c.REDUCTIONS:
                self.assertRegex(b[n][2],r"writeControl\s+timeStep;")
                self.assertRegex(b[n][2],r"writeInterval\s+100;")
            f=(root/"system/functions").read_text()
            self.assertIn("FoamFile",f);self.assertIn('#include "compactNearTop"',f)
            self.assertRegex(c.blocks(f)["temperatureProbe"][2],r"writeInterval\s+1;")
    def test_b14(self):self.check("B14",False)
    def test_c14(self):self.check("C14",False)
    def test_3d_a_archive(self):self.check("C14",True)
    def test_estimate(self):
        x=c.estimate({"field_estimate_bytes":200100,"diagnostic_estimate_bytes":10000,"projected_bytes_with_50pct_margin":315150})
        self.assertEqual(x["field_estimate_bytes"],20100)
        self.assertEqual(x["diagnostic_estimate_bytes"],11000)
    def test_unknown_object_rejected(self):
        with self.assertRaises(ValueError):c.transform("unknown\n{\n type bad;\n}\n",(),())
if __name__=="__main__":unittest.main()
