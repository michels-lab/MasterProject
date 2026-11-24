"""FS-C04 exact geometry 2-zone relabeling tests; Python only, NO CFD."""
from __future__ import annotations
import unittest

from audit_fs_c04_fluid_mold import SOURCE, THREE_ZONE, audit, read_new_blocks


class FS04TwoRegionStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target=SOURCE.read_text()
        cls.base=THREE_ZONE.read_text()

    def test_connected_fluid_and_solid_preserve_exterior_air_and_sand(self):
        result=audit(self.target)
        self.assertEqual(result["status"],
                         "STATIC_2_ZONE_TOPOLOGY_CONSISTENT_NOT_NATIVE_CHECKMESH")
        self.assertEqual(result["fluid_cell_count_predicted"],34368)
        self.assertEqual(result["mold_cell_count_predicted"],7680)
        self.assertEqual(result["total_cell_count_predicted"],42048)
        self.assertEqual(result["fluid_connected_blocks"],32)
        self.assertEqual(result["mold_connected_blocks"],21)
        self.assertEqual(result["fluid_mold_shared_block_faces"],37)
        self.assertEqual(result["original_metal_block_indices"],[9,14,19])
        self.assertEqual(result["original_air_block_count"],29)
        self.assertTrue(result["original_top_metal_air_block_face_now_internal_to_fluid"])
        self.assertFalse(result["alpha_metal_initial_field_defined"])
        self.assertFalse(result["CFD_solver_executed"])
        self.assertFalse(result["native_openfoam_2_region_checkmesh_verified"])

    def test_original_all_53_vertices_blocks_and_external_faces_unchanged(self):
        from audit_fs_c03_exterior_mesh import section, parse
        vertices_ref, old_blocks, _ = parse(self.base)
        new_blocks=read_new_blocks(self.target)
        self.assertEqual(len(old_blocks),len(new_blocks))
        for before,after in zip(old_blocks,new_blocks):
            self.assertEqual(before[0],after[0])
            self.assertEqual(before[2],after[2])
            self.assertEqual(after[1],
                             "mold" if before[1]=="mold" else "fluid")
        for sec in ("vertices","edges","boundary"):
            self.assertEqual(section(self.base,sec).strip(),
                             section(self.target,sec).strip())

    def test_false_roof_cannot_pass_zone_only_audit(self):
        before="atmosphereTop\n    {\n        type patch;"
        after="atmosphereTop\n    {\n        type wall;"
        self.assertIn(before,self.target)
        with self.assertRaisesRegex(ValueError,"changed boundary"):
            audit(self.target.replace(before,after,1))

    def test_misclassified_air_as_solid_rejected(self):
        from re import sub
        # First air block after 24 material blocks must remain fluid.
        before="fluid (8 8 8) simpleGrading (1 1 1) // exterior side air slab 0, face 0"
        after="mold (8 8 8) simpleGrading (1 1 1) // exterior side air slab 0, face 0"
        self.assertIn(before,self.target)
        with self.assertRaisesRegex(ValueError,"block 24 changed"):
            audit(self.target.replace(before,after,1))

    def test_geom_or_cell_refinement_change_not_allowed(self):
        orig="fluid (8 8 8) simpleGrading (1 1 1) // exterior side air slab 0, face 0"
        new="fluid (16 4 8) simpleGrading (1 1 1) // exterior side air slab 0, face 0"
        self.assertIn(orig,self.target)
        with self.assertRaisesRegex(ValueError,"block 24 changed"):
            audit(self.target.replace(orig,new,1))

    def test_metal_air_phase_interface_no_explicit_wall(self):
        r=audit(self.target)
        self.assertTrue(r["original_top_metal_air_block_face_now_internal_to_fluid"])
        # The physical interface will be transported by alpha.metal, not a wall.
        self.assertNotIn("metalTop\n    {",self.target)
        self.assertNotIn("metal_to_air\n    {",self.target)


if __name__=="__main__":
    unittest.main()
