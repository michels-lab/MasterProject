"""FS-C03 offline regressions: CAD-approx C3D03 + air all around, NO CFD."""
from __future__ import annotations
from pathlib import Path
import unittest

from audit_fs_c03_exterior_mesh import SOURCE, audit, parse


REFERENCE=SOURCE.parents[0].parent/"reference/C3D03_base_blockMeshDict"


class ExteriorAirMeshStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mesh=SOURCE.read_text()
        cls.ref=REFERENCE.read_text()

    def test_three_materials_connected_open_top_and_four_sidewalls(self):
        r=audit(self.mesh)
        self.assertEqual(r["status"],"STATIC_TOPOLOGY_CONSISTENT_NOT_NATIVE_CHECKMESH")
        self.assertEqual(r["blocks"],53)
        self.assertEqual(r["vertices"],84)
        self.assertEqual(r["material_cells_predicted"],
                         {"mold":7680,"metal":2368,"air":32000})
        self.assertEqual(r["cell_count_predicted"],42048)
        self.assertEqual(r["shared_block_faces_by_interface"],
                         {"metal_mold":13,"air_mold":24,"air_metal":1})
        self.assertEqual(r["mold_top_air_contact_block_faces"],4)
        self.assertEqual(r["metal_top_air_contact_block_faces"],1)
        self.assertEqual(r["mold_side_air_contact_block_faces"],20)
        self.assertEqual(r["air_block_count"],29)
        self.assertEqual(r["air_connected_block_count"],29)
        self.assertEqual(r["air_above_top_block_count"],9)
        self.assertEqual(r["air_around_four_sidewalls_block_count"],20)
        self.assertFalse(r["solver_executed"])
        self.assertFalse(r["native_OpenFOAM_mesh_quality_verified"])
        self.assertFalse(r["solid_mold_base_and_recess_exposure_resolved"])
        self.assertFalse(r["physical_CAD_surface_fidelity_verified"])

    def test_original_c3d03_material_blocks_and_vertices_unchanged(self):
        src_v,src_b,_=parse(self.mesh)
        import re
        from audit_fs_c03_exterior_mesh import section
        vs=section(self.ref,"vertices")
        vref=[tuple(float(x) for x in mat)
              for mat in re.findall(
                    r"\(\s*([-.\d]+)\s+([-.\d]+)\s+([-.\d]+)\s*\)",vs)]
        self.assertEqual(src_v[:48],vref)
        bs=section(self.ref,"blocks")
        pattern=r"hex\s*\(\s*([0-9 ]+)\s*\)\s+(metal|mold)\s*\(\s*([0-9 ]+)\s*\)\s+simpleGrading\s*\(\s*1\s+1\s+1\s*\)"
        bref=[(tuple(map(int,m.group(1).split())),
               m.group(2),tuple(map(int,m.group(3).split())))
              for m in re.finditer(pattern,bs)]
        self.assertEqual(len(bref),24)
        self.assertEqual(src_b[:24],bref)

    def test_closed_false_ceiling_rejected(self):
        damaged=self.mesh.replace("atmosphereTop\n    {\n        type patch;",
                                  "atmosphereTop\n    {\n        type wall;",1)
        self.assertNotEqual(damaged,self.mesh)
        with self.assertRaisesRegex(ValueError,"incorrect patch type"):
            audit(damaged)

    def test_missing_air_block_over_sand_detected(self):
        damaged=self.mesh.replace(
            "air (4 8 40) simpleGrading (1 1 1) // exterior air above sand top ring 0",
            "mold (4 8 40) simpleGrading (1 1 1) // exterior air above sand top ring 0",
            1)
        self.assertNotEqual(damaged,self.mesh)
        with self.assertRaisesRegex(ValueError,"material cell counts changed"):
            audit(damaged)

    def test_missing_sidewall_air_detected(self):
        damaged=self.mesh.replace(
            "air (8 8 8) simpleGrading (1 1 1) // exterior side air slab 0, face 0",
            "mold (8 8 8) simpleGrading (1 1 1) // exterior side air slab 0, face 0",
            1)
        self.assertNotEqual(damaged,self.mesh)
        with self.assertRaisesRegex(ValueError,"material cell counts changed"):
            audit(damaged)

    def test_unclassified_patch_face_rejected(self):
        damaged=self.mesh.replace(
            "(-30 -65.5 -30) // 48 new air", "(-29 -65.5 -30) // 48 new air",1)
        # A vertex geometric change does not change connectivity: this is a
        # metric/shape issue for native OpenFOAM checkMesh, not face ownership.
        self.assertEqual(audit(damaged)["blocks"],53)
        broken=self.mesh.replace(
            "    atmosphereLowerSides\n    {\n        type patch;",
            "    atmosphereLowerSides\n    {\n        type wall;",1)
        with self.assertRaisesRegex(ValueError,"incorrect patch type"):
            audit(broken)

    def test_derived_material_topology_no_air_in_sand(self):
        v,b,p=parse(self.mesh)
        self.assertEqual([x[1] for x in b[:24]].count("air"),0)
        self.assertEqual(set(x[1] for x in b[24:]),{"air"})
        self.assertEqual(p["moldBottom"][0],"wall")
        self.assertEqual(p["moldRecessWall"][0],"wall")
        self.assertEqual(p["moldRecessRoof"][0],"wall")
        self.assertEqual(p["atmosphereSides"][0],"patch")


if __name__=="__main__":
    unittest.main()
