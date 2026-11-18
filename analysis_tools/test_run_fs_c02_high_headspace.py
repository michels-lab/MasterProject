"""FS-C02 120mm high-air staging, top flux and field-size gates; NO OpenFOAM."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c02_open_top import verify
from audit_fs_c02_local import read_alpha, read_temperature
from run_fs_c02_high_headspace import (
    CELL_VOLUME, EXPECTED_CELLS, PROFILE, main, prepare, read_patch_flux,
    summarize,
)
from run_fs_c02_local import B14_MATERIAL, INITIAL_VOLUME, SOURCE, stage


def field(name: str, values: list[float]) -> str:
    return ("FoamFile { class volScalarField; object "+name+"; }\n"
            "internalField nonuniform List<scalar>\n"
            +str(len(values))+"\n(\n"+" ".join(str(v) for v in values)
            +"\n);\nboundaryField {}\n")


class HighAirTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c02-high-air-")
        self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.base=base/"FS-C02_EXTENDED_synthetic"
        self.new=base/"FS-C02_HIGH_AIR_synthetic"

    def test_air_extension_changes_only_mesh_and_flux_monitor(self):
        original,_=stage(self.base,extended_probe=True)
        high,status=prepare(self.new)
        a=json.loads((original/"FS-C02_MANIFEST.json").read_text())
        b=json.loads((high/"FS-C02_MANIFEST.json").read_text())
        self.assertEqual(b["execution_profile"],PROFILE)
        self.assertEqual(b["time_controls"],a["time_controls"])
        self.assertEqual(status["status"],"STAGED_NO_CFD_YET")
        self.assertTrue(status["high_headspace"])
        self.assertFalse(status["solver_tested_on_real_openfoam"])
        self.assertTrue(status["extended_probe"])
        self.assertEqual(len(b["generated_input_sha256"]),20)
        changed={key for key in a["generated_input_sha256"]
                 if a["generated_input_sha256"][key]!=b["generated_input_sha256"][key]}
        self.assertEqual(changed,{"system/blockMeshDict","system/controlDict"})
        for unchanged in ("0/alpha.metal","0/T","0/U","0/p_rgh",
                          "constant/momentumTransport","constant/fvModels",
                          "constant/physicalProperties.metal"):
            self.assertEqual((original/unchanged).read_bytes(),
                             (high/unchanged).read_bytes())
        r=verify(self.new)
        self.assertEqual(r["top_y_m"],.12)
        self.assertAlmostEqual(r["initial_air_headspace_m"],.08)
        self.assertTrue(r["top_is_open_patch"])
        mesh=(high/"system/blockMeshDict").read_text()
        self.assertIn("(80 240 1)",mesh)
        self.assertIn("(0.04 0.12 0)",mesh)
        self.assertNotIn("(80 120 1)",mesh)
        control=(high/"system/controlDict").read_text()
        self.assertIn("atmosphereFlux",control)
        self.assertIn("patch           atmosphere;",control)
        self.assertIn("fields          (phi);",control)
        self.assertIn("maxCo           0.15;",control)
        self.assertFalse((high/"constant/polyMesh").exists())
        self.assertFalse((high/"postProcessing").exists())
        self.assertEqual(b["geometry"]["dy_m"],.0005)
        self.assertEqual(b["geometry"]["extension_air_y_m"],[.06,.12])
        self.assertEqual(EXPECTED_CELLS,19200)
        self.assertAlmostEqual(CELL_VOLUME,2.5e-9)

    def test_old_reference_and_B14_are_read_only(self):
        h1=hashlib.sha256((SOURCE/"system/blockMeshDict").read_bytes()).hexdigest()
        h2=hashlib.sha256(B14_MATERIAL.read_bytes()).hexdigest()
        prepare(self.new)
        self.assertEqual(h1,hashlib.sha256((SOURCE/"system/blockMeshDict").read_bytes()).hexdigest())
        self.assertEqual(h2,hashlib.sha256(B14_MATERIAL.read_bytes()).hexdigest())

    def test_stage_only_no_solver_and_no_overwrite(self):
        self.assertEqual(main(["--stage-only","--out",str(self.new)]),0)
        self.assertFalse((self.new/"logs/FS-C02_foamRun.log").exists())
        with self.assertRaisesRegex(ValueError,"pre-existing run directory"):
            prepare(self.new)

    def test_no_CFD_for_vertical_only_air_over_missing_sand_geometry(self):
        # Must reject BEFORE making a case directory or checking OpenFOAM env.
        code=main(["--out",str(self.new)])
        self.assertEqual(code,2)
        self.assertFalse(self.new.exists())

    def test_19200_cell_fields_and_top_flux_summary(self):
        case,_=prepare(self.new)
        last=case/"0.01"
        last.mkdir()
        a=[1.0]*6400+[0.0]*(EXPECTED_CELLS-6400)
        T=[1500.]*6400+[300.]*(EXPECTED_CELLS-6400)
        (last/"alpha.metal").write_text(field("alpha.metal",a))
        (last/"T").write_text(field("T",T))
        vol=case/"postProcessing/metalVolume/0/volFieldValue.dat"
        vol.parent.mkdir(parents=True)
        vol.write_text("# Time volIntegrate(alpha.metal)\n"
                       f"0 {INITIAL_VOLUME}\n"
                       f"0.005 {INITIAL_VOLUME}\n"
                       f"0.01 {INITIAL_VOLUME}\n")
        flux=case/"postProcessing/atmosphereFlux/0/surfaceFieldValue.dat"
        flux.parent.mkdir(parents=True)
        flux.write_text("# Time sum(phi)\n"
                        "0.005 2e-7\n0.01 3e-7\n")
        r=summarize(case)
        self.assertEqual(r["cell_count"],19200)
        self.assertEqual(r["gas_near_pure_cells"],12800)
        self.assertEqual(r["gas_near_pure_mean_T_K"],300)
        self.assertAlmostEqual(r["volume_field_m3"],INITIAL_VOLUME)
        self.assertTrue(r["atmosphere_flux"]["measured"])
        self.assertEqual(r["atmosphere_flux"]["positive_flux_samples"],2)
        self.assertEqual(len(read_alpha(last/"alpha.metal",expected_cells=19200)),19200)
        self.assertEqual(len(read_temperature(last/"T",expected_cells=19200)),19200)
        with self.assertRaisesRegex(ValueError,"unexpected alpha cell count"):
            read_alpha(last/"alpha.metal")
        self.assertFalse(r["air_outflow_physically_verified"])

    def test_unmeasured_flux_not_claimed(self):
        case,_=prepare(self.new)
        r=read_patch_flux(case)
        self.assertFalse(r["measured"])

    def test_negative_signed_phi_is_not_outgoing_air_claim(self):
        case,_=prepare(self.new)
        flux=case/"postProcessing/atmosphereFlux/0/surfaceFieldValue.dat"
        flux.parent.mkdir(parents=True)
        flux.write_text("# Time sum(phi)\n"
                        "0.005 -4e-7\n0.01 -1e-7\n")
        r=read_patch_flux(case)
        self.assertEqual(r["positive_flux_samples"],0)
        self.assertEqual(r["negative_flux_samples"],2)
        self.assertFalse(r["outgoing_AIR_mass_or_heat_verified"])


if __name__=="__main__":
    unittest.main()
