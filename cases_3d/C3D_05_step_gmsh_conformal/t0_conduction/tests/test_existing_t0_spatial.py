#!/usr/bin/env python3
"""Synthetic ONLY: regression of Case B read-only native face q spatial analysis."""
from __future__ import annotations

from decimal import Decimal
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


T0 = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S = load("case_b_existing_spatial", T0/"scripts/analyze_existing_t0_spatial.py")
F = load("case_b_existing_spatial_flux", T0/"scripts/analyze_t0_patch_flux.py")


def fixture():
    def face(y, area, sign, q):
        return {"center":(0.,y,0.),"area":area,
                "normal":(float(sign),0.,0.),"q":q}
    m0 = {
        0:face(0.,1.,1,10.),
        1:face(0.02,2.,1,5.),
        2:face(0.04,1.,1,6.),
    }
    d0 = {
        0:face(0.04,1.,-1,-6.),
        1:face(0.,1.,-1,-10.),
        2:face(0.02,2.,-1,-5.),
    }
    metal={Decimal("0"):m0,Decimal("0.10000000000000001"):m0}
    mold={Decimal("0"):d0,Decimal("0.10000000000000001"):d0}
    energy={"history":[
        {"time_s":0.,"metal_sensible_energy_J":300.,"mold_sensible_energy_J":100.},
        {"time_s":0.1,"metal_sensible_energy_J":299.,"mold_sensible_energy_J":101.}
    ]}
    report=F.compare(metal,mold,energy,0.1,expected_faces=3)
    pairs=F.face_pairs(m0,d0)
    return metal,mold,report,pairs


class ExistingC14Spatial(unittest.TestCase):
    def test_no_solver_no_meshing_imports_or_execution(self):
        src=(T0/"scripts/analyze_existing_t0_spatial.py").read_text()
        self.assertNotIn("subprocess.",src)
        self.assertNotIn("foamMultiRun(",src)
        self.assertNotIn("gmsh.",src)
        self.assertIn("final.summarize(case, inputs, status)",src)
        self.assertIn("fx.face_pairs",src)
        self.assertIn("original_regional_energy_sha256",src)
        self.assertIn("NOT",S.__doc__.upper())

    def test_three_geometric_pairs_in_two_axial_bands_and_binary64_times(self):
        m,d,report,pairs=fixture()
        self.assertEqual(pairs,[(0,1),(1,2),(2,0)])
        summary,bands,points=S.spatialize(m,d,report,pairs,bands=2)
        self.assertEqual(summary["face_pairs_per_sample"],3)
        self.assertEqual(summary["temporal_samples"],2)
        self.assertFalse(summary["physically_accepted"])
        self.assertEqual(len(bands),4)
        self.assertEqual(sum(row[4] for row in bands if row[0]==0.1),3)
        self.assertEqual(len(points),3)
        self.assertEqual(sum(row[9] for row in points),0.0)
        self.assertAlmostEqual(summary["time_series"][-1]["metal_outward_W"],26.)
        self.assertAlmostEqual(summary["time_series"][-1]["mold_outward_W"],-26.)
        self.assertEqual(summary["time_series"][-1]["pairwise_abs_mismatch_W"],0.)

    def test_mismatched_original_powers_or_time_cannot_pass(self):
        m,d,report,pairs=fixture()
        bad=json.loads(json.dumps(report))
        bad["history"][-1]["metal_total_outward_W"]+=1
        with self.assertRaisesRegex(ValueError,"Spatial power sum"):
            S.spatialize(m,d,bad,pairs,bands=2)
        bad=json.loads(json.dumps(report))
        bad["history"][-1]["time_s"]=0.099
        with self.assertRaisesRegex(ValueError,"not time aligned"):
            S.spatialize(m,d,bad,pairs,bands=2)
        with self.assertRaisesRegex(ValueError,"Band count"):
            S.spatialize(m,d,report,pairs,bands=1)
        with self.assertRaisesRegex(ValueError,"coverage"):
            S.spatialize(m,d,report,pairs[:2],bands=2)

    def test_no_y_span_must_fail_and_keep_old_data(self):
        m,d,report,pairs=fixture()
        for snapshot in (m,d):
            for faces in snapshot.values():
                for f in faces.values():
                    f["center"]=(f["center"][0],0.,f["center"][2])
        with self.assertRaisesRegex(ValueError,"Y span"):
            S.spatialize(m,d,report,pairs,bands=2)

    def test_atomic_immutable_outputs_hash_and_reentry(self):
        m,d,report,pairs=fixture()
        summary,bands,points=S.spatialize(m,d,report,pairs,bands=2)
        summary["source_sha256"]={"dummy_evidence":"abc"}
        with TemporaryDirectory() as folder:
            out=Path(folder)/"report"
            self.assertIn("PUBLISHED",S.save_new(out,summary,bands,points))
            self.assertIn("SHA_VERIFIED",S.save_new(out,summary,bands,points))
            self.assertEqual(set(json.loads((out/"MANIFEST_SHA256.json").read_text())),
                             set(S.OUTPUT_FILES))
            self.assertEqual(json.loads((out/"T0_SPATIAL_INTERPRETATION.json").read_text()),
                             summary)
            with self.assertRaises(FileExistsError):
                S.save_new(out,{**summary,"axial_band_count":7},bands,points)
            (out/"FINAL_INTERFACE_FACE_CENTERS.csv").write_text("ALTERED!")
            with self.assertRaisesRegex(ValueError,"SHA manifest"):
                S.save_new(out,summary,bands,points)
            self.assertEqual((out/"FINAL_INTERFACE_FACE_CENTERS.csv").read_text(),"ALTERED!")


if __name__ == "__main__":
    unittest.main()
