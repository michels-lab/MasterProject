"""FS-C02 top must be open atmosphere, not artificial lid. No CFD tests."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c02_open_top import verify
from run_fs_c02_local import digest, stage


class OpenTopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c02-open-top-")
        self.addCleanup(self.tmp.cleanup)
        self.run=Path(self.tmp.name)/"FS-C02_EXTENDED_synthetic"
        self.case,_=stage(self.run,extended_probe=True)

    def _change_input(self, path, before, after):
        f=self.case/path
        content=f.read_text()
        self.assertIn(before,content)
        f.write_text(content.replace(before,after,1))
        mfile=self.case/"FS-C02_MANIFEST.json"
        m=json.loads(mfile.read_text())
        m["generated_input_sha256"][path]=digest(f)
        mfile.write_text(json.dumps(m))

    def test_staged_top_is_atmospheric_with_20mm_headspace(self):
        old=(self.case/"system/blockMeshDict").read_bytes()
        r=verify(self.run)
        self.assertEqual(r["status"],"OPEN_ATMOSPHERIC_BOUNDARY_TYPES_VERIFIED")
        self.assertEqual(r["top_y_m"],.06)
        self.assertEqual(r["initial_metal_surface_y_m"],.04)
        self.assertAlmostEqual(r["initial_air_headspace_m"],.02)
        self.assertFalse(r["top_is_wall"])
        self.assertTrue(r["open_boundary_allows_air_out_and_backflow"])
        self.assertFalse(r["outgoing_air_flux_actually_measured"])
        self.assertEqual(r["atmosphere_boundary_conditions"]["0/U"],
                         "pressureInletOutletVelocity")
        self.assertEqual(r["atmosphere_boundary_conditions"]["0/p_rgh"],
                         "prghTotalPressure")
        self.assertEqual(r["atmosphere_boundary_conditions"]["0/T"],
                         "inletOutlet")
        self.assertEqual((self.case/"system/blockMeshDict").read_bytes(),old)

    def test_geometry_wall_top_detected_even_if_manifest_rehashed(self):
        self._change_input(
            "system/blockMeshDict",
            "atmosphere { type patch; faces ((3 7 6 2)); }",
            "atmosphere { type wall; faces ((3 7 6 2)); }",
        )
        with self.assertRaisesRegex(ValueError,"not a generic open patch"):
            verify(self.run)

    def test_wrong_top_velocity_BC_rejected(self):
        self._change_input("0/U","pressureInletOutletVelocity","fixedValue")
        with self.assertRaisesRegex(ValueError,"top is not open atmospheric"):
            verify(self.run)

    def test_wrong_top_pressure_BC_rejected(self):
        self._change_input("0/p_rgh","prghTotalPressure","zeroGradient")
        with self.assertRaisesRegex(ValueError,"top is not open atmospheric"):
            verify(self.run)

    def test_wrong_gas_temperature_inflow_rejected(self):
        self._change_input("0/T","inletValue      uniform 300;",
                           "inletValue      uniform 1500;")
        with self.assertRaisesRegex(ValueError,"prescribed ambient backflow"):
            verify(self.run)

    def test_wrong_metal_inflow_rejected(self):
        self._change_input("0/alpha.metal","inletValue uniform 0;",
                           "inletValue uniform 1;")
        with self.assertRaisesRegex(ValueError,"prescribed ambient backflow"):
            verify(self.run)

    def test_mesh_generation_converts_top_to_wall_detected(self):
        p=self.case/"constant/polyMesh/boundary"
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(
            "FoamFile { class polyBoundaryMesh; object boundary; }\n"
            "1\n(\natmosphere\n{\ntype wall;\nnFaces 80;\nstartFace 1000;\n}\n);\n"
        )
        with self.assertRaisesRegex(ValueError,"ACTUAL mesh atmosphere is a wall"):
            verify(self.run)

    def test_input_provenance_tamper_rejected(self):
        (self.case/"constant/g").write_text("tampered")
        with self.assertRaisesRegex(ValueError,"solver input has changed"):
            verify(self.run)


if __name__=="__main__":
    unittest.main()
