"""Synthetic tests of QuickCup bilateral readiness and guard rails. No CFD."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from granada_mold_bilateral_readiness import (
    CASES, METAL_DAT, audit, coupling, geometry, metal_flux,
    read_optional_mold, main
)


def fixture(folder):
    (folder/"0/metal").mkdir(parents=True,exist_ok=True)
    (folder/"0/mold").mkdir(parents=True,exist_ok=True)
    metal = """boundaryField
    {
        metal_to_mold
        {
            type coupledTemperature;
            h
            {
                type wallLayersHeatTransferCoefficient;
                thicknessLayers (2e-4);
                kappaLayers (1e-1);
            }
        }
    }
    """
    mold = "boundaryField { mold_to_metal { type coupledTemperature; } }"
    (folder/"0/metal/T").write_text(metal)
    (folder/"0/mold/T").write_text(mold)
    (folder/"system").mkdir(exist_ok=True)
    (folder/"system/blockMeshDict").write_text("""convertToMeters 0.001;
    vertices (
    (0 0 0) (40 0 0) (40 40 0) (0 40 0)
    (0 0 10) (40 0 10) (40 40 10) (0 40 10)
    );
    blocks ( hex (0 1 2 3 4 5 6 7) metal (80 80 1) simpleGrading (1 1 1) );
    """)
    file=folder/METAL_DAT
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("""# Selection : patch(metal_to_mold)
# Faces : 240
# Area : 1.200000e-03
# Time sum(energyAdvectiveFlux) sum(heatFlux) sum(energyFlux)
0 0 0 0
0.1 0 100 100
""")


def prepare_mold(root, name, *, mutate=False):
    case=root/name
    case.mkdir(parents=True,exist_ok=True)
    path=case/"mold_interface_W.csv"
    path.write_text("time_s,outward_power_W\n0,0\n0.1,-100\n")
    spec={"case":name, "patch":"mold_to_metal", "units":"W",
          "orientation":"outward_from_mold",
          "quantity":"integrated_interface_power",
          "source_method":"OpenFOAM_Foundation14",
          "measured_area_m2":.0012,
          "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (case/"provenance.json").write_text(json.dumps(spec))
    if mutate:
        path.write_text(path.read_text()+"0.2,-100\n")
    return path


class BilateralTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for name in CASES:
            fixture(self.root/"cases_controlled_buoyancy"/name)
        self.case=self.root/"cases_controlled_buoyancy"/CASES[0]

    def test_six_cases_and_missing_mold_explicit(self):
        a=audit(self.root)
        self.assertEqual(len(a["cases"]),6)
        self.assertTrue(a["no_mold_measurement_fabricated"])
        self.assertTrue(all(c["status"]=="METAL_SIDE_READINESS_PASSED_MOLD_UNVERIFIED" for c in a["cases"]))
        self.assertTrue(all(c["sections"]["mold_side"]["status"]=="NOT_OBSERVED_NO_MOLD_OUTPUT" for c in a["cases"]))
        self.assertTrue(all(len(c["source_manifest"])==4 for c in a["cases"]))

    def test_nominal_geometry_and_explicit_limit(self):
        a=geometry(self.case,[])
        self.assertAlmostEqual(a["nominal_three_contact_sides_area_m2"],.0012)
        self.assertEqual(a["nominal_contact_face_count"],240)
        self.assertIn("NOT_CHECKMESH",a["status"])

    def test_nominal_contact_resistance_and_BCs(self):
        a=coupling(self.case,[])
        self.assertAlmostEqual(a["nominal_layer_R_m2K_W"],.002)
        self.assertAlmostEqual(a["nominal_layer_h_W_m2K"],500)

    def test_mismatched_boundary_type_is_blocked(self):
        file=self.case/"0/mold/T"
        file.write_text(file.read_text().replace("coupledTemperature","fixedValue"))
        a=audit(self.root)["cases"][0]
        self.assertEqual(a["status"],"SOURCE_REVIEW")
        self.assertIn("not coupledTemperature"," ".join(a["alerts"]))

    def test_mismatched_area_is_flagged(self):
        p=self.case/METAL_DAT
        p.write_text(p.read_text().replace("1.200000e-03","2.200000e-03"))
        self.assertIn("area differs"," ".join(audit(self.root)["cases"][0]["alerts"]))

    def test_mold_csv_normalized_pair_is_only_provisional(self):
        root=self.root/"optional"
        prepare_mold(root,CASES[0])
        a=audit(self.root,root)["cases"][0]
        self.assertEqual(a["sections"]["mold_side"]["status"],
                         "PROVISIONAL_SOURCE_PAIR_NEEDS_MESH_NORMAL_VALIDATION")
        self.assertAlmostEqual(a["sections"]["mold_side"]["numerical_metrics"]["max_abs_power_imbalance_W"],0)
        self.assertNotEqual(a["sections"]["mold_side"]["status"],"PHYSICALLY_VALIDATED")

    def test_mold_checksum_mismatch_rejected(self):
        root=self.root/"optional"
        prepare_mold(root,CASES[0],mutate=True)
        a=audit(self.root,root)["cases"][0]
        self.assertEqual(a["sections"]["mold_side"]["status"],"INVALID_MOLD_EVIDENCE")
        self.assertIn("checksum", " ".join(a["alerts"]))

    def test_mold_missing_provenance_is_not_passed(self):
        root=self.root/"optional"
        (root/CASES[0]).mkdir(parents=True)
        (root/CASES[0]/"mold_interface_W.csv").write_text("time_s,outward_power_W\n0,0\n")
        a=audit(self.root,root)["cases"][0]
        self.assertIn("provenance", " ".join(a["alerts"]))

    def test_mold_time_mismatch_blocks_pairing(self):
        root=self.root/"optional"
        file=prepare_mold(root,CASES[0])
        file.write_text("time_s,outward_power_W\n0,0\n0.15,-100\n")
        spec=root/CASES[0]/"provenance.json"
        js=json.loads(spec.read_text())
        js["source_sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
        spec.write_text(json.dumps(js))
        a=audit(self.root,root)["cases"][0]
        self.assertIn("time grids", " ".join(a["alerts"]))

    def test_missing_original_source_does_not_make_zero(self):
        (self.case/METAL_DAT).unlink()
        a=audit(self.root)["cases"][0]
        self.assertIsNone(a["sections"]["metal_side_power"])
        self.assertEqual(a["status"],"SOURCE_REVIEW")

    def test_export_and_no_original_mutation(self):
        out=self.root/"reports"
        self.assertEqual(main(["--root",str(self.root),"--out",str(out),"--strict"]),0)
        report=json.loads((out/"bilateral_readiness.json").read_text())
        self.assertTrue((out/"mold_wall_heat_flux_CANDIDATE.foam").exists())
        self.assertIn("NOT_VALIDATED",report["global_physics_verdict"])
        with self.assertRaises(SystemExit):
            main(["--root",str(self.root),"--out",str(out)])
        with self.assertRaises(SystemExit):
            main(["--root",str(self.root),"--out",str(self.case/"inside")])

    def test_bilateral_strict_gate_fails_without_measurements(self):
        out=self.root/"newreport"
        self.assertEqual(main(["--root",str(self.root),"--out",str(out),
                               "--require-bilateral"]),1)


if __name__=="__main__":
    unittest.main()
