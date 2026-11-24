"""FS-C04 thermal contact geometry regression. Synthetic, NO CFD/OpenFOAM."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from audit_fs_c04_thermal_interfaces import (
    compare_interface, polygon_area_vector, normalized_area,
    patch_window, EXPECTED_GROUP_FACES,
)

SCALE=1_000_000_000

def mesh_on_quad(quad, face=(0,1,2,3)):
    return {
        "points":[tuple(int(x*SCALE) for x in p) for p in quad],
        "faces":[tuple(face)],
        "count":1,
    }


def pair(quad, *, reversed_solid=True):
    fluid=mesh_on_quad(quad)
    solid=mesh_on_quad(quad,(3,2,1,0) if reversed_solid else (0,1,2,3))
    return fluid,solid


SIDE_QUAD=((1,0,0),(1,1,0),(1,1,1),(1,0,1))
TOP_QUAD=((0,0,0),(0,0,1),(1,0,1),(1,0,0))


class ContactRegressionTests(unittest.TestCase):
    def _check(self,quad,initial_alpha,*,mold_reversed=True,strict=False):
        fluid,mold=pair(quad,reversed_solid=mold_reversed)
        return compare_interface(fluid,mold,[0],[0],0,0,1,[initial_alpha],
                                 enforce_pilot_counts=strict)

    def test_one_to_one_opposite_wall_areas_initial_metal(self):
        r=self._check(SIDE_QUAD,1.)
        self.assertEqual(r["interface_face_count"],1)
        self.assertEqual(r["matched_faces"],1)
        self.assertEqual(r["areas_by_initial_contact"]["metal_sand"]["faces"],1)
        self.assertEqual(r["areas_by_initial_contact"]["air_sand_top"]["faces"],0)
        self.assertEqual(r["areas_by_initial_contact"]["air_sand_lateral"]["faces"],0)
        self.assertAlmostEqual(r["total_area_m2"],1.,places=13)
        self.assertLess(r["max_opposite_unit_normal_error"],1e-9)

    def test_air_above_sand_top_is_real_interface_not_atmosphere(self):
        r=self._check(TOP_QUAD,0.)
        self.assertEqual(r["areas_by_initial_contact"]["air_sand_top"]["faces"],1)
        self.assertEqual(r["areas_by_initial_contact"]["metal_sand"]["faces"],0)
        self.assertAlmostEqual(r["total_area_cm2"],10000.,places=8)

    def test_air_on_sand_side_is_real_interface(self):
        r=self._check(SIDE_QUAD,0.)
        self.assertEqual(r["areas_by_initial_contact"]["air_sand_lateral"]["faces"],1)
        self.assertEqual(r["areas_by_initial_contact"]["air_sand_top"]["faces"],0)

    def test_same_direction_normals_are_forbidden(self):
        with self.assertRaisesRegex(ValueError,"not opposite"):
            self._check(SIDE_QUAD,1.,mold_reversed=False)

    def test_different_wall_coordinates_are_forbidden(self):
        fluid,mold=pair(SIDE_QUAD)
        mold["points"][2]=(SCALE,2*SCALE,SCALE)
        with self.assertRaisesRegex(ValueError,"face mismatch"):
            compare_interface(fluid,mold,[0],[0],0,0,1,[1.],
                              enforce_pilot_counts=False)

    def test_alpha_metal_cannot_be_fractional_in_initial_phase_audit(self):
        with self.assertRaisesRegex(ValueError,"not exact 0/1"):
            self._check(SIDE_QUAD,0.5)

    def test_duplicate_sand_faces_are_rejected(self):
        fluid,mold=pair(SIDE_QUAD)
        fluid["faces"]=fluid["faces"]*2
        mold["faces"]=mold["faces"]*2
        with self.assertRaisesRegex(ValueError,"duplicated sand contact"):
            compare_interface(fluid,mold,[0,0],[0,0],0,0,2,[1.],
                              enforce_pilot_counts=False)

    def test_pilot_face_counts_are_required_in_production(self):
        with self.assertRaisesRegex(ValueError,"contact counts changed"):
            self._check(SIDE_QUAD,1.,strict=True)
        self.assertEqual(sum(EXPECTED_GROUP_FACES.values()),3136)

    def test_degenerate_polygon_is_rejected(self):
        same=((1,0,0),(1,0,0),(1,1,0),(1,0,1))
        fluid,mold=pair(same)
        with self.assertRaisesRegex(ValueError,"degenerate"):
            compare_interface(fluid,mold,[0],[0],0,0,1,[1.],
                              enforce_pilot_counts=False)

    def test_native_patch_window_recognizes_reciprocal_mapped_wall(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            def write(typ="mappedWall",n=3136,other="mold",far="mold_to_fluid"):
                (p/"boundary").write_text(
                    "FoamFile { version 2.0; format ascii; }\n"
                    "1\n(\nfluid_to_mold\n{\n"
                    f"type {typ};\n"
                    f"nFaces {n};\n"
                    "startFace 4000;\n"
                    f"neighbourRegion {other};\n"
                    f"neighbourPatch {far};\n"
                    "}\n)\n"
                )
            write()
            self.assertEqual(patch_window(p,"fluid_to_mold",7200,3136,
                                          "mold","mold_to_fluid"),(4000,3136))
            write(typ="wall")
            with self.assertRaisesRegex(ValueError,"wrong mappedWall"):
                patch_window(p,"fluid_to_mold",7200,3136,
                             "mold","mold_to_fluid")
            write(n=3135)
            with self.assertRaisesRegex(ValueError,"wrong native face range"):
                patch_window(p,"fluid_to_mold",7200,3136,
                             "mold","mold_to_fluid")

    def test_polygon_area_vector_unit_square(self):
        f=mesh_on_quad(SIDE_QUAD)
        normal=polygon_area_vector(f["points"],f["faces"][0])
        self.assertAlmostEqual(normal[0],1.,places=12)
        self.assertAlmostEqual(normal[1],0.,places=12)
        self.assertAlmostEqual(normalized_area(normal),1.,places=12)


if __name__=="__main__":
    unittest.main()
