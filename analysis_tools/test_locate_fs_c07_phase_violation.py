"""Native FS-C07 spatial allocation diagnostic tests, synthetic, NO CFD."""
import math
from pathlib import Path
import tempfile
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


    def test_discover_20_real_saved_phase_states_not_function_object_folders(self):
        with tempfile.TemporaryDirectory() as td:
            case = Path(td) / "FS_C07_THERMAL_fixture"
            case.mkdir()
            for idx in range(1, 21):
                t = round(idx*0.05, 10)
                fluid = case / str(t) / "fluid"
                fluid.mkdir(parents=True)
                for name in ("alpha.metal", d.MODEL_FIELD, "T.metal"):
                    (fluid / name).write_text("synthetic mock")
            (case / "0.12745").mkdir()  # function-object-only time
            self.assertEqual(
                d.complete_saved_native_times(case),
                tuple(round(idx*0.05, 10) for idx in range(1, 21))
            )
            (case / "0.25/fluid/T.metal").unlink()
            with self.assertRaisesRegex(ValueError, "exactly 20"):
                d.complete_saved_native_times(case)

    def test_compact_all_states_requires_each_core_to_have_zero_significant_violation(self):
        results = []
        for idx in range(1, 21):
            b = {name: {"count_gt_tolerance": 0}
                 for name in d.BINS}
            b["alpha_metal_1e-6_to_1e-3"]["count_gt_tolerance"] = 2
            results.append({
                "time_s": round(idx*0.05, 10),
                "total_native_cells": 34368,
                "cells_above_tolerance": 2,
                "bin_by_actual_native_alpha_metal": b,
                "positive_excess_integral_m3_all_cells": idx*1e-13,
                "top_8_by_local_excess": [{"excess_fraction": idx*1e-7}],
            })
        report = {
            "results": results,
            "case_modified": False,
            "solver_rerun": False,
        }
        got = d.compact_result(report)
        self.assertTrue(got["all_20_states_have_zero_core_cell_excess_above_threshold"])
        self.assertEqual(got["max_core_cells_exceeding_threshold_any_state"], 0)
        self.assertEqual(got["total_cell_time_incidences_above_threshold"], 40)
        self.assertEqual(got["peak_integrated_excess_time_s"], 1.0)
        self.assertEqual(len(got["results"]), 20)
        self.assertFalse(got["case_modified"])
        self.assertTrue(got["no_new_native_solver_run"])
        results[3]["bin_by_actual_native_alpha_metal"]["alpha_metal_ge_0p5"][
            "count_gt_tolerance"
        ] = 1
        with self.assertRaisesRegex(ValueError, "do not reproduce"):
            d.compact_result(report)
        results[3]["cells_above_tolerance"] = 3
        got2 = d.compact_result(report)
        self.assertFalse(got2["all_20_states_have_zero_core_cell_excess_above_threshold"])
        self.assertEqual(got2["max_core_cells_exceeding_threshold_any_state"], 1)



if __name__ == "__main__":
    unittest.main()
