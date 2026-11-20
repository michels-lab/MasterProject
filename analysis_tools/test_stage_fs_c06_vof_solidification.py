"""FS-C06 compatibility staging gates; synthetic only, NO OpenFOAM solver."""
import json
import math
from pathlib import Path
import tempfile
import unittest

from stage_fs_c06_vof_solidification import (
    C14_FVMODELS, FLUID_CELLS, PREFIX, TIMES, MODEL_FIELD,
    check_solid_fraction, model_text, read_c14_reference,
)


class FS_C06Test(unittest.TestCase):
    def test_c14_traceable_real_coefficients(self):
        project = Path(__file__).resolve().parents[1]
        data = read_c14_reference(project)
        v = data["values"]
        self.assertEqual(v["Tsol"], 1423)
        self.assertEqual(v["Tliq"], 1473)
        self.assertEqual(v["L"], 228600)
        self.assertEqual(v["relax"], 0.1)
        self.assertEqual(v["Cu"], 1e5)
        self.assertEqual(v["q"], 1e-3)
        self.assertFalse(data["alpha1e_transferred"])
        self.assertEqual(len(data["original_sha256"]), 64)

    def test_vof_native_model_format_and_limits(self):
        project = Path(__file__).resolve().parents[1]
        text = model_text(read_c14_reference(project))
        for x in ("type VoFSolidificationMelting;", "cellZone all;",
                  "(1423 1)", "(1473 0)", "L 228600;",
                  "relax 0.1;", "Cu 100000;", "q 0.001;",
                  "THIS MODEL DOES NOT CREATE SHRINKAGE OR FEEDING"):
            self.assertIn(x, text)
        self.assertNotIn("solidificationMeltingSource;", text)
        self.assertNotIn("alpha1e", text)

    def test_no_false_solid_mass(self):
        alpha = [0.0] * FLUID_CELLS
        solid = [0.0] * FLUID_CELLS
        alpha[0] = 1.0
        solid[0] = 0.3
        x = check_solid_fraction(alpha, solid)
        self.assertEqual(x["solid_fraction_max"], 0.3)
        self.assertFalse(x["mass_shrinkage_or_feeding_validated"])

    def test_solid_exceeds_vof_rejected(self):
        alpha = [0.0] * FLUID_CELLS
        solid = [0.0] * FLUID_CELLS
        alpha[0] = 0.1
        solid[0] = 0.5
        with self.assertRaises(ValueError):
            check_solid_fraction(alpha, solid)

    def test_negative_fraction_rejected(self):
        with self.assertRaises(ValueError):
            check_solid_fraction([0.0] * FLUID_CELLS, [-0.1] * FLUID_CELLS)

    def test_nonfinite_rejected(self):
        alpha = [0.0] * FLUID_CELLS
        solid = [0.0] * FLUID_CELLS
        solid[1] = math.nan
        with self.assertRaises(ValueError):
            check_solid_fraction(alpha, solid)

    def test_tampered_C14_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t) / C14_FVMODELS
            path.parent.mkdir(parents=True)
            path.write_text("type solidificationMeltingSource; Tsol 1423;")
            with self.assertRaises(ValueError):
                read_c14_reference(Path(t))

    def test_constants_and_outputs_distinct(self):
        self.assertEqual(TIMES, ("1e-07", "2e-07"))
        self.assertEqual(MODEL_FIELD, "alpha.metal.solid")
        self.assertTrue(PREFIX.startswith("FS_C06_"))


if __name__ == "__main__":
    unittest.main()
