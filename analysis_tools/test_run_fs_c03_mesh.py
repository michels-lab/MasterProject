"""FS-C03 native pilot staging tests: no OpenFOAM, CAD or CFD needed."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c03_exterior_mesh import SOURCE, audit
from run_fs_c03_mesh import main, patch_info, stage


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c03-native-test-")
        self.addCleanup(self.tmp.cleanup)
        self.dst=Path(self.tmp.name)/"FS_C03_AIR_TOPOLOGY_synthetic"

    def test_stages_outside_source_without_native_or_CFD(self):
        original=SOURCE.read_bytes()
        record=stage(self.dst)
        self.assertEqual(record["status"],"STAGED_NO_OPENFOAM")
        self.assertEqual(record["topology"]["cell_count_predicted"],42048)
        self.assertFalse(record["solver_executed"])
        self.assertFalse((self.dst/"constant/polyMesh").exists())
        self.assertFalse((self.dst/"log.blockMesh").exists())
        self.assertEqual((self.dst/"system/blockMeshDict").read_bytes(),original)
        self.assertEqual(SOURCE.read_bytes(),original)
        self.assertEqual(
            json.loads((self.dst/"FS_C03_NATIVE_STATUS.json").read_text())["status"],
            "STAGED_NO_OPENFOAM"
        )

    def test_refuses_any_existing_output_without_mutation(self):
        self.dst.mkdir()
        (self.dst/"important.txt").write_text("untouched")
        with self.assertRaisesRegex(ValueError,"pre-existing pilot directory"):
            stage(self.dst)
        self.assertEqual((self.dst/"important.txt").read_text(),"untouched")

    def test_non_native_cli_does_not_invoke_openfoam(self):
        self.assertEqual(main(["--out",str(self.dst)]),0)
        self.assertTrue((self.dst/"FS_C03_NATIVE_STATUS.json").is_file())
        self.assertFalse((self.dst/"constant/polyMesh").exists())

    def test_native_cli_requires_foundation14_before_creating_destination(self):
        from unittest.mock import patch
        with patch.dict("os.environ",{"WM_PROJECT_VERSION":"13"}):
            code=main(["--native","--out",str(self.dst)])
        self.assertEqual(code,2)
        self.assertFalse(self.dst.exists())

    def test_native_patch_reader_requires_expected_patch(self):
        f=Path(self.tmp.name)/"boundary"
        f.write_text("""
        2
        (
        atmosphereTop
        {
            type patch;
            nFaces 448;
            startFace 20;
        }
        mold_to_air
        {
            type mappedWall;
            nFaces 1888;
            neighbourRegion air;
            neighbourPatch air_to_mold;
        }
        )
        """)
        self.assertEqual(patch_info(f,"atmosphereTop")["type"],"patch")
        self.assertEqual(patch_info(f,"mold_to_air")["neighbourRegion"],"air")
        with self.assertRaisesRegex(ValueError,"not uniquely present"):
            patch_info(f,"nonexistent")

    def test_source_still_has_mold_top_and_four_side_contacts(self):
        report=audit(SOURCE.read_text())
        self.assertEqual(report["mold_top_air_contact_block_faces"],4)
        self.assertEqual(report["mold_side_air_contact_block_faces"],20)
        self.assertEqual(report["metal_top_air_contact_block_faces"],1)


if __name__=="__main__":
    unittest.main()
