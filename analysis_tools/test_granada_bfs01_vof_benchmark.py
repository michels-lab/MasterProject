"""Synthetic regression suite for B-FS-01 water-air VOF analogue; never runs CFD."""
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from granada_bfs01_vof_benchmark import (
    ALPHA, BLOCK_MESH, END_TIME, REFERENCE_VOLUME, SOURCE_FILES,
    audit, check_upstream, main, parse_volume, stage,
)


class BFS01Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.src = self.root / "tutorials/compressibleVoF/damBreak"
        for filename in SOURCE_FILES:
            f = self.src / filename
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("FoamFile { format ascii; }\n")
        (self.src / "system/controlDict").write_text(
            "solver compressibleVoF;\nendTime 1;\ndeltaT 0.001;\n"
            "writeInterval 0.05;\nmaxCo 1;\nmaxAlphaCo 1;\nmaxDeltaT 1;\n"
        )
        (self.src / "constant/phaseProperties").write_text(
            "phases (water air);\nsigma { type liquidProperties; phase water; }\n"
        )
        (self.src / "constant/g").write_text(
            "dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);\n"
        )
        (self.src / "0/U").write_text("boundaryField { wall {type noSlip;} atmosphere {type pressureInletOutletVelocity;} }\n")
        self.dest = self.root / "staged"
        self.volume_data = (
            "# Selection : all\n"
            "# Volume : 2.400000e-05\n"
            "# Time volIntegrate(alpha.water)\n"
            f"0 {REFERENCE_VOLUME}\n"
            f"0.05 {REFERENCE_VOLUME}\n"
            f"0.1 {REFERENCE_VOLUME}\n"
        )

    def staged(self):
        return stage(self.src, self.dest)

    def write_volume(self, content=None):
        f = self.dest / "postProcessing/waterVolume/0/volFieldValue.dat"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(self.volume_data if content is None else content)
        return f

    def test_source_checkout_is_never_modified_and_stage_is_not_CFD(self):
        original = {name: hashlib.sha256((self.src/name).read_bytes()).hexdigest()
                    for name in SOURCE_FILES}
        result = self.staged()
        self.assertEqual(result["status"],"PREPARED_NOT_MESHED_OR_RUN")
        self.assertEqual(result["physics"]["shrinkage"],False)
        self.assertFalse(result["physics"]["metal"])
        self.assertEqual(len(result["upstream_sha256"]),len(SOURCE_FILES))
        self.assertEqual(original, {name: hashlib.sha256((self.src/name).read_bytes()).hexdigest()
                                    for name in SOURCE_FILES})
        self.assertIn("foamRun", (self.dest/"HOW_TO_RUN.md").read_text())
        self.assertFalse((self.dest/"postProcessing").exists())

    def test_geometry_and_initial_field_both_match_analytical_volume(self):
        self.staged()
        block=(self.dest/"system/blockMeshDict").read_text()
        alpha=(self.dest/"0/alpha.water").read_text()
        self.assertIn("(80 120 1)",block)
        self.assertIn("frontAndBack { type empty",block)
        self.assertIn("atmosphere { type patch",block)
        self.assertIn("box (0 0 -1) (0.04 0.04 1)",alpha)
        self.assertAlmostEqual(REFERENCE_VOLUME,1.6e-5)

    def test_source_solver_and_phase_identity_fail_closed(self):
        (self.src/"system/controlDict").write_text(
            (self.src/"system/controlDict").read_text().replace("compressibleVoF","isothermalFluid"))
        with self.assertRaisesRegex(ValueError,"official compressibleVoF"):
            self.staged()
        self.assertFalse(self.dest.exists())

    def test_missing_official_data_and_wrong_gravity_fail_closed(self):
        (self.src/"constant/g").write_text("value (0 9.81 0);")
        with self.assertRaisesRegex(ValueError,"gravity"):
            check_upstream(self.src)
        (self.src/"constant/g").unlink()
        with self.assertRaisesRegex(ValueError,"missing required"):
            check_upstream(self.src)

    def test_source_symlink_refused(self):
        f=self.src/"0/p_rgh"
        f.unlink()
        try:
            f.symlink_to(self.src/"0/U")
        except OSError:
            self.skipTest("symlink unavailable on this platform")
        with self.assertRaisesRegex(ValueError,"symlink"):
            check_upstream(self.src)

    def test_no_overwrite_or_original_case_tree_mutation(self):
        self.staged()
        with self.assertRaisesRegex(ValueError,"existing path"):
            stage(self.src,self.dest)
        with self.assertRaisesRegex(ValueError,"original research-case"):
            stage(self.src,self.root/"cases_controlled_buoyancy"/"B14"/"stage")
        with self.assertRaisesRegex(ValueError,"independent"):
            stage(self.src,self.src/"duplicate")

    def test_stage_preserves_thermo_and_writes_volume_instrumentation(self):
        self.staged()
        self.assertIn("waterVolume",(self.dest/"system/controlDict").read_text())
        self.assertIn("volIntegrate",(self.dest/"system/controlDict").read_text())
        self.assertIn("writeInterval 0.01;",(self.dest/"system/controlDict").read_text())
        self.assertIn("maxAlphaCo 0.25;",(self.dest/"system/controlDict").read_text())
        self.assertEqual((self.dest/"constant/phaseProperties").read_text(),
                         (self.src/"constant/phaseProperties").read_text())

    def test_audit_real_file_format_with_provenance(self):
        self.staged()
        f=self.write_volume()
        rec=audit(self.dest,self.root/"report")
        self.assertEqual(rec["status"],"VOLUME_SCREEN_PASSED")
        self.assertEqual(rec["observed_points"],3)
        self.assertEqual(rec["source_sha256"],hashlib.sha256(f.read_bytes()).hexdigest())
        self.assertTrue(rec["not_mass_or_shrinkage_validation"])
        self.assertAlmostEqual(rec["equivalent_height_last_m"],.04)
        self.assertTrue((self.root/"report/volume_times.csv").exists())
        with self.assertRaisesRegex(ValueError,"overwrite"):
            audit(self.dest,self.root/"report")

    def test_false_volume_conservation_fails(self):
        self.staged()
        modified=self.volume_data.replace(f"0.1 {REFERENCE_VOLUME}",
                                          f"0.1 {REFERENCE_VOLUME*.95}")
        self.write_volume(modified)
        result=audit(self.dest,self.root/"audit")
        self.assertEqual(result["status"],"REVIEW")
        self.assertGreater(result["max_abs_volume_drift_fraction"],0.04)

    def test_time_gap_and_wrong_initial_water_fraction_block_acceptance(self):
        self.staged()
        f=self.write_volume(self.volume_data.replace("0.1 ", "0.06 "))
        self.assertEqual(audit(self.dest,self.root/"audit1")["status"],"REVIEW")
        f.write_text(self.volume_data.replace(f"0 {REFERENCE_VOLUME}",f"0 {REFERENCE_VOLUME*0.9}"))
        self.assertEqual(audit(self.dest,self.root/"audit2")["status"],"REVIEW")

    def test_bad_column_and_time_provenance_rejected(self):
        self.staged()
        f=self.write_volume()
        f.write_text(self.volume_data.replace("volIntegrate(alpha.water)","volAverage(alpha.water)"))
        with self.assertRaisesRegex(ValueError,"water volume field header"):
            parse_volume(f)
        f.write_text("# Time volIntegrate(alpha.water)\n0 0.1\n0 0.2\n")
        with self.assertRaisesRegex(ValueError,"strictly increasing"):
            parse_volume(f)
        f.write_text("# Time volIntegrate(alpha.water)\n0 NaN\n0.1 0.2\n")
        with self.assertRaisesRegex(ValueError,"invalid time/volume"):
            parse_volume(f)

    def test_cli_stage_and_report_have_real_exit_codes(self):
        self.assertEqual(main(["stage","--tutorial",str(self.src),"--out",str(self.dest)]),0)
        self.write_volume()
        self.assertEqual(main(["audit","--case",str(self.dest),
                               "--out",str(self.root/"report")]),0)
        with self.assertRaises(SystemExit):
            main(["audit","--case",str(self.dest),
                  "--out",str(self.dest/"report-in-case")])

    def test_wrong_manifest_prevents_claims_for_arbitrary_data(self):
        self.staged()
        self.write_volume()
        p=self.dest/"BFS01_MANIFEST.json"
        obj=json.loads(p.read_text())
        obj["fluid_identity"]="MOLTEN_IRON"
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError,"wrong benchmark identity"):
            audit(self.dest,self.root/"audit")


if __name__ == "__main__":
    unittest.main()
