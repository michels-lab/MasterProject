#!/usr/bin/env python3
"""No WSL requirement: deterministic geometry/dictionary transformation tests."""
from __future__ import annotations
from pathlib import Path
import json
import sys
import tempfile
import unittest

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import run_c14_3d_complete_postprocess as runner
import c14_3d_postprocess_parity as parity


class OriginalC14NativePostprocessingPreparationTests(unittest.TestCase):
    def test_real_3d_compatible_geometry_plan_from_synthetic_cells(self):
        # 16 x 28 x 20 = 8960 synthetic cells in 3D; never native WSL.
        centres=[(0.0005+i*0.002,0.0005+j*0.0013,0.0005+k*0.0008)
                 for i in range(16) for j in range(28) for k in range(20)]
        self.assertEqual(len(centres),8960)
        plan=runner.sample_geometry(centres)
        self.assertEqual(len(plan["profiles"]),5)
        self.assertAlmostEqual(plan["profiles"]["line_y10mm"]["actual_y_m"],0.01)
        self.assertAlmostEqual(plan["profiles"]["line_y20mm"]["actual_y_m"],0.02)
        self.assertAlmostEqual(plan["profiles"]["line_y30mm"]["actual_y_m"],0.03)
        self.assertEqual(plan["profiles"]["line_y30mm"]["sampling_method"],
                         "PRESERVED_C14_METRIC_Y_WITHIN_3D_BBOX_NEEDS_NATIVE_INSIDE_CHECK")
        probe=plan["probe_actual_m"]
        self.assertIn(probe,centres)
        for name,p in plan["profiles"].items():
            self.assertEqual(p["nPoints"],80)
            self.assertNotEqual(p["start"],p["end"])
            self.assertIn(p["axis"],("x","y"))
            self.assertGreater(max(p["start"][0],p["end"][0]),0)

    def test_C14_dict_geometry_only_preserves_diagnostic_fields(self):
        points=[(0.0005+i*0.002,0.0005+j*0.0013,0.0005+k*0.0008)
                for i in range(16) for j in range(28) for k in range(20)]
        plan=runner.sample_geometry(points)
        with tempfile.TemporaryDirectory() as d:
            case=Path(d)/"disposable_workcopy"
            (case/"system").mkdir(parents=True)
            c14_control=runner.C14/"system/controlDict"
            (case/"system/controlDict").write_bytes(c14_control.read_bytes())
            digests=runner.adapt_diagnostic_files(case,plan)
            self.assertEqual(len(digests),6)
            self.assertEqual((case/"system/controlDict").read_bytes(),
                             c14_control.read_bytes())
            f=(case/"system/functions").read_text()
            self.assertIn("temperatureProbe",f)
            self.assertIn(runner.vector(plan["probe_actual_m"]),f)
            self.assertIn("#include \"researchDiagnostics\"",f)
            a=(case/"system/lineProfiles").read_text()
            for name in ("horizontalProfiles","verticalProfiles",
                         "line_y10mm","line_y20mm","line_y30mm","line_x20mm"):
                self.assertIn(name,a)
            for field in ("vorticity","flowType","latentHeatRateVol","CoCell"):
                self.assertIn(field,a)
            b=(case/"system/momentumPostProcessing").read_text()
            for field in ("phaseChangeDarcyAcceleration","phaseChangeBuoyancyAcceleration",
                          "phaseChangeDragToPressure","phaseChangeDragToBuoyancy"):
                self.assertIn(field,b)
            top=(case/"system/topSurfaceFlowPostProcessing").read_text()
            self.assertIn("topPhiAbsolute",top)
            self.assertIn("nearTopInternalLine",top)
            self.assertIn("line_topNear",top)
            # No patch/model/material/time replacements in copied diagnostics.
            self.assertEqual((case/"system/researchDiagnostics").read_bytes(),
                             (runner.C14/"system/researchDiagnostics").read_bytes())

    def test_corrupted_function_object_is_blocked(self):
        with self.assertRaisesRegex(ValueError,"missing C14 functionObject"):
            runner.replace_sets("hello","nonexistent",[])
        source="profile\n{\n fields (T);\n sets\n {\n old {x 1;}\n }\n}\n"
        changed=runner.replace_sets(source,"profile",[("new",{
            "axis":"x","start":(0,1,2),"end":(1,1,2),"nPoints":80})])
        self.assertIn("fields (T);",changed)
        self.assertIn("new",changed)
        self.assertNotIn("old {",changed)

    def test_native_3d_profiles_require_all_80_finite_points(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            expected=runner.profile_coverage(root)
            self.assertEqual(len(expected),9)
            self.assertTrue(all(v["status"]=="MISSING" for v in expected.values()))
            path=root/"postProcessing/metal/horizontalProfiles/10/line_y20mm.xy"
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text("# x T\n"+"".join(f"{i} 1500\n" for i in range(80)))
            result=runner.profile_coverage(root)
            self.assertEqual(result["horizontalProfiles/line_y20mm"]["status"],"PASS")
            path.write_text("# x T\n"+"".join(f"{i} nan\n" for i in range(80)))
            result=runner.profile_coverage(root)
            self.assertEqual(result["horizontalProfiles/line_y20mm"]["status"],"INCOMPLETE")

    def test_all_original_output_families_exist_in_reference(self):
        root=runner.C14/"postProcessing/metal"
        self.assertTrue(root.is_dir())
        recorded={p.name for p in root.iterdir() if p.is_dir()}
        for name in ("horizontalProfiles","verticalProfiles",
                     "metalTopEnergyPower","metalMoldEnergyPower",
                     "metalSensibleEnthalpy","metalLatentHeatPower",
                     "momentumMean","momentumMax","topPhiAbsolute",
                     "temperatureProbe"):
            self.assertIn(name,recorded)


if __name__=="__main__":
    unittest.main()
