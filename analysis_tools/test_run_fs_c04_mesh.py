"""FS-C04 native mesh-only staging tests. No OpenFOAM or CFD required."""
from __future__ import annotations
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from audit_fs_c04_fluid_mold import SOURCE, audit
from run_fs_c04_mesh import stage, main, EXPECTED, CONTACTS, AIR_PATCHES


class FS04NativePreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c04-mesh-")
        self.addCleanup(self.tmp.cleanup)
        self.dest=Path(self.tmp.name)/"FS_C04_FLUID_MOLD_TOPOLOGY_synthetic"

    def test_stage_has_exact_two_regions_no_fields_and_no_solver(self):
        source_before=SOURCE.read_bytes()
        r=stage(self.dest)
        self.assertEqual(r["status"],"STAGED_NO_OPENFOAM")
        self.assertEqual(r["schema"],"masterproject-fs-c04-2region-native-mesh-only-v1")
        self.assertFalse(r["solver_executed"])
        self.assertTrue(r["alpha_metal_not_initialized"])
        self.assertTrue(r["two_geometric_regions_only_not_cht_or_vof"])
        self.assertEqual((self.dest/"system/blockMeshDict").read_bytes(),source_before)
        self.assertEqual(SOURCE.read_bytes(),source_before)
        self.assertFalse((self.dest/"constant/polyMesh").exists())
        self.assertFalse((self.dest/"log.blockMesh").exists())
        self.assertEqual(EXPECTED,{"fluid":34368,"mold":7680})
        self.assertEqual(CONTACTS,{("fluid","mold"):3136})
        self.assertEqual(AIR_PATCHES,{"atmosphereTop":448,
                                      "atmosphereSides":3040,
                                      "atmosphereLowerSides":256})

    def test_runner_refuses_preexisting_destination(self):
        self.dest.mkdir()
        (self.dest/"important").write_text("DO NOT DELETE")
        with self.assertRaisesRegex(ValueError,"pre-existing pilot directory"):
            stage(self.dest)
        self.assertEqual((self.dest/"important").read_text(),"DO NOT DELETE")

    def test_main_stage_only_does_not_require_openfoam(self):
        with patch.dict("os.environ",{"WM_PROJECT_VERSION":"13"}):
            status=main(["--out",str(self.dest)])
        self.assertEqual(status,0)
        self.assertFalse((self.dest/"constant/polyMesh").exists())
        self.assertEqual(json.loads(
            (self.dest/"FS_C04_NATIVE_STATUS.json").read_text())["status"],
            "STAGED_NO_OPENFOAM")

    def test_native_requires_foundation14_without_creating_folder(self):
        with patch.dict("os.environ",{"WM_PROJECT_VERSION":"13"}):
            status=main(["--native","--out",str(self.dest)])
        self.assertEqual(status,2)
        self.assertFalse(self.dest.exists())

    def test_static_mesh_remains_unvalidated_by_native(self):
        r=audit(SOURCE.read_text())
        self.assertEqual(r["fluid_connected_blocks"],32)
        self.assertFalse(r["native_openfoam_2_region_checkmesh_verified"])
        self.assertFalse(r["fluid_mold_cht_coupling_verified"])
        self.assertFalse(r["alpha_metal_initial_field_defined"])


if __name__=="__main__":
    unittest.main()
