"""Native FS-C07 spatial allocation diagnostic tests, synthetic, NO CFD."""
import math
import unittest

import locate_fs_c07_phase_violation as d


class PhaseAllocationSpatialTests(unittest.TestCase):
    def setUp(self):
        # Three disjoint 8-vertex cubes, quantized like native C04 mesh.
        scale = d.METRE_COORD_SCALE
        self.mesh = {"points": [], "cell_nodes": []}
        for cell in range(3):
            vertices = []
            for x, y, z in (
                (0,0,0), (1,0,0), (1,1,0), (0,1,0),
                (0,0,1), (1,0,1), (1,1,1), (0,1,1),
            ):
                vertices.append(len(self.mesh["points"]))
                self.mesh["points"].append(
                    tuple(int(scale * val) for val in (
                        cell * 2+x, y, z
                    )))
            self.mesh["cell_nodes"].append(set(vertices))

    def test_alpha_bins_independent_of_fraction_solid(self):
        cases = [
            (-1e-22, "alpha_metal_negative"),
            (0, "alpha_metal_exactly_zero"),
            (1e-7, "alpha_metal_0_to_1e-6"),
            (1e-4, "alpha_metal_1e-6_to_1e-3"),
            (0.1, "alpha_metal_1e-3_to_0p5"),
            (0.5, "alpha_metal_ge_0p5"),
            (1, "alpha_metal_ge_0p5"),
            (1.01, "alpha_metal_above_one"),
        ]
        for actual, name in cases:
            with self.subTest(alpha=actual):
                self.assertEqual(d.metal_bin(actual), name)

    def test_native_geometry_uses_real_eight_vertices(self):
        self.assertEqual(d.cell_vertex_average_m(self.mesh, 0),
                         (0.5, 0.5, 0.5))
        self.assertEqual(d.cell_vertex_average_m(self.mesh, 2),
                         (4.5, 0.5, 0.5))

    def test_violations_preserve_actual_values_and_original_indices(self):
        alpha = [1e-5, 0.1, 1.0]
        solid = [1.8e-5, 0.100002, 0.9]
        raw = (alpha[:], solid[:])
        out = d.locate([2.0, 3.0, 4.0], alpha, solid,
                       [1500.0, 1400.0, 1600.0], self.mesh)
        self.assertEqual(out["cells_above_tolerance"], 2)
        self.assertAlmostEqual(
            out["positive_excess_integral_m3_all_cells"],
            2.0*8e-6 + 3.0*2e-6)
        self.assertEqual(
            out["bin_by_actual_native_alpha_metal"]
               ["alpha_metal_1e-6_to_1e-3"]["count_gt_tolerance"],
            1)
        self.assertEqual(out["top_8_by_local_excess"][0]["native_fluid_cell"], 0)
        self.assertEqual(
            out["top_8_by_local_excess"][0]["8_vertex_average_xyz_m"],
            [0.5, 0.5, 0.5])
        self.assertTrue(out["all_significant_solid_excess_outside_metal_core_alpha_ge_0p5"])
        self.assertFalse(out["native_field_edited"])
        self.assertEqual(raw, (alpha, solid))

    def test_solid_above_metal_in_core_detected(self):
        out = d.locate(
            [1, 1, 1], [0.1, 0.2, 1.0], [0, 0.1, 1.00001],
            [1400, 1400, 1400], self.mesh)
        self.assertEqual(out["cells_above_tolerance"], 1)
        self.assertFalse(out["all_significant_solid_excess_outside_metal_core_alpha_ge_0p5"])
        self.assertEqual(
            out["bin_by_actual_native_alpha_metal"]
                ["alpha_metal_ge_0p5"]["count_gt_tolerance"], 1)

    def test_small_roundoff_not_counted_as_significant(self):
        out = d.locate(
            [1, 1, 1], [-1e-30, 1e-10, 1.0],
            [0, 1.0001e-10, 1.0],
            [1400, 1400, 1400], self.mesh)
        self.assertEqual(out["cells_above_tolerance"], 0)
        self.assertGreater(out["positive_excess_integral_m3_all_cells"], 0)

    def test_nonfinite_input_or_bad_native_geometry_blocks(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            d.locate([1,1,1], [math.nan,0.1,0.2], [0,0,0],
                     [1500,1500,1500], self.mesh)
        with self.assertRaisesRegex(ValueError, "matching cell counts"):
            d.locate([1], [0.1], [0.1], [1500], self.mesh)


if __name__ == "__main__":
    unittest.main()
