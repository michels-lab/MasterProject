"""Unit/regression tests; synthetic fixtures only. No OpenFOAM or CFD."""
import json
from pathlib import Path
import tempfile
import unittest

from granada_boundary_spatial_gate import (
    CASES, PROFILE_FILES, all_face_evidence, inspect, keyed_times, main,
    phase_profiles, powers, table, time_dirs,
)


def source(case, path, data):
    fp=case/"postProcessing"/"metal"/path
    fp.parent.mkdir(parents=True,exist_ok=True)
    fp.write_text(data,encoding="utf8")
    return fp


def fixture(case):
    face_header="# face_x face_y face_z U_x U_y U_z phi\n"
    patch_header="# face_x face_y face_z phi U_x U_y U_z T p_rgh rho\n"
    for t in ("0","0.1"):
        source(case,f"topFlow/{t}/patch(metalTop).xy",
               face_header+"0 0.04 0.005 0.001 0 0 0\n0.001 0.04 0.005 0.002 0 0 0\n")
        source(case,f"topPatchFaceFields/{t}/patch(metalTop).xy",
               patch_header+"0 0.04 0.005 0 0.001 0 0 1500 100000 6820\n0.001 0.04 0.005 0 0.002 0 0 1500 100000 6820\n")
    source(case,"metalTopPhiSum/0/surfaceFieldValue.dat","# Time sum(phi)\n0 0\n0.1 0\n")
    power_header="# Time sum(energyAdvectiveFlux) sum(heatFlux) sum(energyFlux)\n"
    for name,power in (("metalMoldEnergyPower",80),("metalTopEnergyPower",20),("metalBoundaryEnergyPower",100)):
        source(case,f"{name}/0/surfaceFieldValue.dat",power_header+f"0 0 0 0\n0.1 0 {power} {power}\n")
    header="# x U_x U_y U_z T p_rgh rho alphaL v_x v_y v_z flowType mag gradT_x gradT_y gradT_z magGradT dTdt coolingRate gradRho_x gradRho_y gradRho_z magGradRho dAlphaLdt solidRate latentRate CoCell\n"
    vals=lambda alpha:" ".join(str(v) for v in [0.002,0,0,0,1490,100000,6820,alpha]+[0]*19)
    for folder, name in PROFILE_FILES:
        for t in ("0.1","0.2"):
            source(case,f"{folder}/{t}/{name}",header+vals(0.7)+"\n"+vals(0.95)+"\n")


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for case in CASES:
            fixture(self.root/"cases_controlled_buoyancy"/case)
        self.case=self.root/"cases_controlled_buoyancy"/CASES[0]

    def test_all_six_cases_three_sections_and_provenance(self):
        a=inspect(self.root)
        self.assertEqual(len(a["cases"]),6)
        self.assertTrue(all(c["status"]=="NUMERIC_SCREEN_PASSED" for c in a["cases"]))
        self.assertTrue(all(c["source_file_count"]>=15 for c in a["cases"]))
        self.assertTrue(all(len(c["source_manifest"])==c["source_file_count"] for c in a["cases"]))
        self.assertTrue(all(len(s["sha256"])==64 and not s["path"].startswith("/") for c in a["cases"] for s in c["source_manifest"]))
        b=a["cases"][0]["sections"]
        self.assertEqual(b["top_boundary"]["face_count"],2)
        self.assertEqual(b["top_boundary"]["checked_patch_times"],2)
        self.assertEqual(b["spatial_phase"]["source_profile_count"],8)
        self.assertEqual(b["metal_interface"]["mold_side_status"],"NOT_OBSERVED_NO_MOLD_POSTPROCESSING")
        self.assertFalse(b["metal_interface"]["bilateral_reciprocity_verified"])

    def test_original_faces_vs_sum_cancellation_caught(self):
        p=self.case/"postProcessing/metal/topFlow/0.1/patch(metalTop).xy"
        p.write_text(p.read_text().replace("0 0 0\n0.001", "0 0 0.001\n0.001").replace("0.002 0 0 0\n", "0.002 0 0 -0.001\n"))
        a=all_face_evidence(self.case,[])
        at=a["snapshots"][-1]
        self.assertAlmostEqual(at["net_phi_kg_s"],0)
        self.assertAlmostEqual(at["sum_abs_face_phi_kg_s"],0.002)
        self.assertIn("nonzero facewise", " ".join(a["alerts"]))

    def test_incorrect_face_order_and_velocity_flagged(self):
        p=self.case/"postProcessing/metal/topPatchFaceFields/0.1/patch(metalTop).xy"
        p.write_text(p.read_text().replace("0 0.04 0.005 0 0.001", "0.4 0.04 0.005 0 0.001"))
        self.assertIn("centroid", " ".join(all_face_evidence(self.case,[])["alerts"]))

    def test_partition_energy_no_double_count(self):
        a=powers(self.case,[])
        self.assertEqual(len(a["metal_side"]),2)
        self.assertEqual(a["max_partition_abs_difference_W"],0)
        self.assertFalse(a["bilateral_reciprocity_verified"])
        p=self.case/"postProcessing/metal/metalBoundaryEnergyPower/0/surfaceFieldValue.dat"
        p.write_text(p.read_text().replace("0.1 0 100 100","0.1 0 100 200"))
        self.assertIn("energyFlux arithmetic mismatch"," ".join(powers(self.case,[])["alerts"]))

    def test_phase_sample_classification_not_volume(self):
        a=phase_profiles(self.case,[])
        self.assertEqual(a["profiles"][0]["solid_sample_fraction"],0)
        self.assertEqual(a["profiles"][0]["liquid_sample_fraction"],0.5)
        self.assertEqual(a["profiles"][0]["mushy_sample_fraction"],0.5)
        self.assertIn("not cell-volume fractions",a["interpretation"])

    def test_invalid_alpha_fails_screen(self):
        p=self.case/"postProcessing/metal/horizontalProfiles/0.1/line_y10mm.xy"
        p.write_text(p.read_text().replace(" 0.7 ", " 1.6 "))
        a=phase_profiles(self.case,[])
        self.assertIn("invalid liquid fraction"," ".join(a["alerts"]))

    def test_duplicate_times_and_bad_measurement(self):
        p=self.case/"postProcessing/metal/metalTopPhiSum/0/surfaceFieldValue.dat"
        p.write_text("# Time sum(phi)\n0.1 0\n0.1 0\n")
        with self.assertRaisesRegex(ValueError,"repeated/out-of-order"):
            keyed_times(p,("sum(phi)",))
        p=self.case/"postProcessing/metal/topFlow/0/patch(metalTop).xy"
        p.write_text(p.read_text().replace("0.001 0 0 0", "0.001 NaN 0 0"))
        with self.assertRaisesRegex(ValueError,"NaN/Infinity"):
            table(p,("face_x","face_y","face_z","U_x","U_y","U_z","phi"))

    def test_missing_original_is_not_measured_zero(self):
        p=self.case/"postProcessing/metal/topFlow/0.1/patch(metalTop).xy"
        p.unlink()
        self.assertIsNone(inspect(self.root)["cases"][0]["sections"]["top_boundary"])
        self.assertEqual(inspect(self.root)["cases"][0]["status"],"REVIEW")

    def test_export_and_safe_no_overwrite(self):
        out=self.root/"newreport"
        self.assertEqual(main(["--root",str(self.root),"--out",str(out),"--strict"]),0)
        report=json.loads((out/"evidence.json").read_text())
        self.assertFalse(report["cfd_executed"])
        self.assertTrue((out/"summary.csv").exists())
        with self.assertRaises(SystemExit):
            main(["--root",str(self.root),"--out",str(out)])
        with self.assertRaises(SystemExit):
            main(["--root",str(self.root),"--out",str(self.case/"newreport")])


if __name__=="__main__":
    unittest.main()
