"""Software-only regression tests; no CFD or fabricated research results."""
import unittest
import tempfile
import subprocess
from pathlib import Path
from compare_c14_three_models import (
    station_map, match_stations, metrics, differences, check_nominal, pinned_inventory, pinned_sha)

def row(x,t=1500.,alpha=1.,uy=0.):
    return {"x":x,"T":t,"phaseChangeSource:alpha1":alpha,
            "U_x":0.,"U_y":uy,"U_z":0.}

class CommonStationsTests(unittest.TestCase):
    def test_translation_and_intersection_no_interpolation(self):
        a=station_map([row(.00865),row(.00915),row(.00965)],"x")
        b=station_map([row(.00865),row(.00965)],"x")
        c=station_map([row(.00275),row(.00325),row(.00375)],"x",.0059)
        matched,keys=match_stations({"A":a,"B":b,"2D":c})
        self.assertEqual(len(keys),2)
        self.assertEqual([r["x"] for r in matched["2D"]],[.00275,.00375])

    def test_duplicate_quantized_coordinates_rejected(self):
        with self.assertRaisesRegex(ValueError,"ambiguous"):
            station_map([row(.01),row(.010000001)],"x")

    def test_no_common_support_rejected(self):
        with self.assertRaisesRegex(ValueError,"insufficient"):
            match_stations({"A":station_map([row(.01),row(.02)],"x"),
                            "B":station_map([row(.03),row(.04)],"x")})

    def test_nonphysical_values_rejected(self):
        for r in (row(.01,alpha=1.1),row(.01,t=0)):
            with self.assertRaises(ValueError):
                station_map([r],"x")

    def test_metrics_and_signed_difference(self):
        a=[row(.01,1490,.9,-.001),row(.02,1500,1,.0001)]
        b=[row(.01,1500,1,.001),row(.02,1500,1,0)]
        m=metrics(a)
        self.assertEqual((m["down_points"],m["up_points"],m["deadband_points"]),(1,0,1))
        d=differences(a,b)
        self.assertAlmostEqual(d["bias_T"],-5)
        self.assertAlmostEqual(d["rmse_T"],50**.5)
        self.assertEqual(d["opposite_Uy_sign_points"],1)

    def test_pinned_nested_case_rejects_dirty_and_untracked_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def git(*args):
                subprocess.run(["git","-C",tmp,*args],check=True,
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            git("init")
            case=root/"nested"/"case"
            case.mkdir(parents=True)
            p=case/"profile.xy"
            p.write_text("original")
            git("add",".")
            git("-c","user.name=Test","-c","user.email=test@example.invalid","commit","-m","fixture")
            inv=pinned_inventory(case)
            self.assertEqual(len(pinned_sha(case,p,inv)),64)
            p.write_text("modified")
            with self.assertRaisesRegex(ValueError,"pinned Git blob"):
                pinned_sha(case,p,inv)
            q=case/"untracked.xy"
            q.write_text("original")
            with self.assertRaises(ValueError):
                pinned_sha(case,q,inv)

    def test_wrong_nominal_inventory_rejected(self):
        with self.assertRaisesRegex(ValueError,"inventory"):
            check_nominal({}, {}, {})

if __name__=="__main__":
    unittest.main()
