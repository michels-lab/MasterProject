from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_c14_stage07_bilateral_native_flux as q

class BilateralTests(unittest.TestCase):
    def test_harmonic_overlay(self):
        original="interpolationSchemes { interpolate((kappa|Cv)) harmonic; }"
        actual=q.overlay(original)
        self.assertIn("interpolate(kappa) harmonic;",actual)
        self.assertEqual(q.overlay(actual),actual)
        self.assertIn("interpolate((kappa|Cv)) harmonic;",actual)
    def test_no_invented_scheme(self):
        for text in ("interpolationSchemes { default linear; }",
                     "interpolationSchemes { interpolate(kappa) linear; }",
                     "interpolationSchemes { } interpolationSchemes { }"):
            with self.assertRaises(ValueError): q.overlay(text)
    def test_patch_contract(self):
        self.assertEqual(len(q.PATCHES),8)
        self.assertEqual(len(q.INTERFACE),2)
        self.assertEqual(len([x for x in q.PATCHES if x[0]=="mold"]),6)
    def test_native_source_scope(self):
        text=(q.HERE/"native_bilateral_flux/c3d04C14FluidSolidFlux.C").read_text()
        for item in ("8960","12352","2496","fluidTransport->q()","solidTransport->q()"):
            self.assertIn(item,text)
        for _,patch in q.PATCHES:
            self.assertIn('"'+patch+'"',text)
if __name__=="__main__":unittest.main()
