#!/usr/bin/env python3
"""Case B synthetic test ONLY; no C++ compile, OpenFOAM, CFD or physical validation."""
import csv
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

T0=Path(__file__).resolve().parents[1]
script=T0/"scripts/analyze_t0_patch_flux.py"
spec=importlib.util.spec_from_file_location("case_b_patch_flux",script)
F=importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)

def frow(x,area,normal,q):
    return {"center":x,"area":area,"normal":normal,"q":q}

def fixture(shift=0.):
    coords=[(0.,0.,0.),(0.,0.01,0.),(0.,0.02,0.)]
    m={i:frow(coords[i],1.,(1.,0.,0.),[10.,5.,5.][i]) for i in range(3)}
    # Real mappedWall faces can have a DIFFERENT patch-list order.
    d={0:frow((coords[1][0]+shift,*coords[1][1:]),1.,(-1.,0.,0.),-5.),
       1:frow((coords[2][0]+shift,*coords[2][1:]),1.,(-1.,0.,0.),-5.),
       2:frow((coords[0][0]+shift,*coords[0][1:]),1.,(-1.,0.,0.),-10.)}
    metal={Decimal("0"):m,Decimal("0.1"):m}
    mold={Decimal("0"):d,Decimal("0.10"):d}
    energy={"history":[
      {"time_s":0.,"metal_sensible_energy_J":800.,"mold_sensible_energy_J":1200.},
      {"time_s":0.1,"metal_sensible_energy_J":798.,"mold_sensible_energy_J":1202.}
    ]}
    return metal,mold,energy

class FaceFluxQA(unittest.TestCase):
    def test_native_foundation14_solid_transport_used_not_wallHeatFlux_guess(self):
        c=(T0/"native_flux/c3d05PatchFlux.C").read_text(encoding="utf-8")
        for check in ("solidThermo::New(metal)", "solidThermo::New(mold)",
                      "solidThermophysicalTransportModel::New(tm())",
                      "solidThermophysicalTransportModel::New(td())",
                      "transport.q()", "mesh.Cf()", "mesh.Sf()", "12636",
                      "metal_to_mold", "mold_to_metal", '"wx"', "writeFaceFlux(fm", "writeFaceFlux(fd"):
            self.assertIn(check,c)
        self.assertNotIn("wallHeatFlux::",c)
        # Foundation14 upstream polyBoundaryMesh API; CI wmake enforces it.
        self.assertIn("mesh.poly().boundary().findIndex(patchName)",c)
        self.assertNotIn("findPatchID(",c)
        self.assertNotIn('#include "fvCFD.H"',c)
        self.assertIn("fvMesh::UNCHANGED",c)
        opt=(T0/"native_flux/Make/options").read_text()
        self.assertIn("-lsolidThermophysicalTransportModels",opt)

    def test_geometric_face_mapping_permutation_and_exact_balance(self):
        m,d,e=fixture()
        matches=F.face_pairs(m[Decimal("0")],d[Decimal("0")])
        self.assertEqual(dict(matches),{0:2,1:0,2:1})
        output=F.compare(m,d,e,0.1,expected_faces=3)
        self.assertEqual(output["faces_paired_per_side"],3)
        self.assertTrue(output["direct_patch_normal_heat_flux_observed"])
        self.assertFalse(output["patch_flux_continuity_numerically_accepted"])
        self.assertAlmostEqual(output["history"][0]["net_outward_interface_W"],0.)
        self.assertAlmostEqual(output["history"][1]["metal_energy_change_plus_patch_flux_trapezoid_J"],0.)
        self.assertAlmostEqual(output["history"][1]["mold_energy_change_plus_patch_flux_trapezoid_J"],0.)

    def test_local_mismatch_detected_without_false_global_pass(self):
        m,d,e=fixture()
        d[Decimal("0.1")][0]["q"]=-3.
        out=F.compare(m,d,e,0.1,expected_faces=3)
        last=out["history"][-1]
        self.assertGreater(last["pairwise_abs_flux_mismatch_W"],0)
        self.assertGreater(last["max_abs_single_pair_mismatch_W"],0)
        self.assertFalse(out["patch_flux_continuity_numerically_accepted"])

    def test_geometric_pair_tolerance_and_fail_closed(self):
        m,d,e=fixture(shift=2e-8)
        self.assertEqual(len(F.face_pairs(m[Decimal("0")],d[Decimal("0")])),3)
        m,d,e=fixture(shift=2e-6)
        with self.assertRaisesRegex(ValueError,"missing"):
            F.face_pairs(m[Decimal("0")],d[Decimal("0")])
        m,d,e=fixture()
        d[Decimal("0")][0]["area"]=1.1
        with self.assertRaisesRegex(ValueError,"area"):
            F.face_pairs(m[Decimal("0")],d[Decimal("0")])
        m,d,e=fixture()
        d[Decimal("0")][0]["normal"]=(1.,0.,0.)
        with self.assertRaisesRegex(ValueError,"normals"):
            F.face_pairs(m[Decimal("0")],d[Decimal("0")])

    def test_nonmatching_time_grid_and_energy_times_blocked(self):
        m,d,e=fixture()
        del d[Decimal("0.10")]
        d[Decimal("0.09")]=d[Decimal("0")]
        with self.assertRaisesRegex(ValueError,"time sets"):
            F.compare(m,d,e,0.1,expected_faces=3)
        m,d,e=fixture()
        e["history"][-1]["time_s"]=0.09
        with self.assertRaisesRegex(ValueError,"do not match"):
            F.compare(m,d,e,0.1,expected_faces=3)

    def test_foundation14_17digit_times_align_bijectively_without_resampling(self):
        # Native C++ writes runTime.value() using "%.17g", e.g. 0.04
        # becomes 0.040000000000000001; JSON energy uses short decimals.
        times=(0.,0.02,0.04,0.06,0.08,0.1)
        metal0,mold0,_=fixture()
        metal={Decimal(format(t, ".17g")):metal0[Decimal("0")] for t in times}
        mold={Decimal(format(t, ".17g")):mold0[Decimal("0")] for t in times}
        energy={"history":[
            {"time_s":t, "metal_sensible_energy_J":800.-20.*t,
             "mold_sensible_energy_J":1200.+20.*t}
            for t in times
        ]}
        native, max_delta, allowed = F.align_native_energy_times(set(metal), energy["history"])
        self.assertEqual(len(native), 6)
        self.assertGreater(max_delta, Decimal("0"))
        self.assertLess(max_delta, allowed)
        out=F.compare(metal,mold,energy,0.1,expected_faces=3)
        self.assertEqual(len(out["history"]),6)
        self.assertGreater(out["max_time_roundtrip_difference_s"],0.)
        self.assertLess(out["max_time_roundtrip_difference_s"],1e-12)
        self.assertIn("NO interpolation",out["time_alignment_method"])
        self.assertEqual(out["history"][-1]["time_s"],0.1)

    def test_time_alignment_rejects_missing_extra_shifted_or_ambiguous_samples(self):
        m,d,e=fixture()
        # A deleted energy time must never be silently interpolated.
        with self.assertRaisesRegex(ValueError, "times do not match"):
            F.align_native_energy_times(set(m),e["history"][:1])
        # An extra time value is likewise not permitted.
        with self.assertRaisesRegex(ValueError, "times do not match"):
            F.align_native_energy_times(set(m),e["history"]+[dict(e["history"][1],time_s=0.05)])
        # A meaningful physical time mismatch (not binary64 formatting) fails.
        with self.assertRaisesRegex(ValueError, "no interpolation or time substitution"):
            F.align_native_energy_times(set(m),[
                e["history"][0],dict(e["history"][1],time_s=0.099)
            ])
        # Duplicated nominal time, including JSON repeats, is rejected.
        with self.assertRaisesRegex(ValueError, "Duplicate energy time"):
            F.align_native_energy_times(set(m),e["history"]+[dict(e["history"][1])])
        # Closely spaced times cannot be collapsed by the numerical tolerance.
        close={Decimal("0"),Decimal("0.000000000000001"),Decimal("0.1")}
        close_e=[{"time_s":0.}, {"time_s":1.6e-15}, {"time_s":0.1}]
        with self.assertRaisesRegex(ValueError, "times do not match"):
            F.align_native_energy_times(close,close_e)

    def test_native_csv_count_duplicates_nan_missing_header_and_time_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"flux.csv"
            def write(times,rows,header=True):
                with path.open("w",newline="",encoding="utf-8") as stream:
                    w=csv.writer(stream)
                    if header:w.writerow(F.HEADER)
                    for t in times:
                        for i,q in enumerate(rows):
                            w.writerow([t,i,0.,0.01*i,0.,1.,1.,0.,0.,q])
            write([0,0.1],[10.,5.,5.])
            d=F.parse_csv(path,expected_faces=3)
            self.assertEqual(len(d),2)
            write([0,0.1],[10.,float("nan"),5.])
            with self.assertRaisesRegex(ValueError,"Nonfinite"):
                F.parse_csv(path,expected_faces=3)
            write([0.1],[10.,5.,5.])
            with self.assertRaises(ValueError):
                F.parse_csv(path,expected_faces=3)
            write([0,0.1],[10.,5.,5.],header=False)
            with self.assertRaisesRegex(ValueError,"header"):
                F.parse_csv(path,expected_faces=3)
            write([0.,0.1],[10.,5.,5.])
            with path.open("a",encoding="utf-8") as stream:
                stream.write("0.1,0,0,0,0,1,1,0,0,10\n")
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                F.parse_csv(path,expected_faces=3)

    def test_report_exclusive_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"report.json"
            self.assertIn("WRITTEN",F.exclusive(path,{"x":1}))
            self.assertIn("ALREADY",F.exclusive(path,{"x":1}))
            with self.assertRaises(FileExistsError):
                F.exclusive(path,{"x":2})
            self.assertEqual(json.loads(path.read_text()),{"x":1})

if __name__=="__main__":
    unittest.main()
