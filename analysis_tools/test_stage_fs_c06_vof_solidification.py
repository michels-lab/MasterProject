"""FS-C06 compatibility staging gates; synthetic only, NO OpenFOAM solver."""
import json
import math
from pathlib import Path
import tempfile
import unittest

from stage_fs_c06_vof_solidification import (
    C14_FVMODELS, FLUID_CELLS, PREFIX, TIMES, MODEL_FIELD,
    check_solid_fraction, model_text, read_c14_reference, phase_volume_metrics,
    read_native_solid_fraction, read_native_metal_temperature,
    NATIVE_FVMODELS, NATIVE_CONTROL,
)


class FS_C06Test(unittest.TestCase):
    @staticmethod
    def _inherited_c05_models() -> str:
        # Exactly the FS-C01 fvModel installed by the FS-C05 native stager.
        project = Path(__file__).resolve().parents[1]
        return (project / "freesurface/FS-C01/constant/fvModels").read_text().replace(
            'location    "constant";', 'location    "constant/fluid";'
        )

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
        text = model_text(read_c14_reference(project), self._inherited_c05_models())
        for x in ("type VoFSolidificationMelting;", "cellZone all;",
                  "(1423 1)", "(1473 0)", "L 228600;",
                  "relax 0.1;", "Cu 100000;", "q 0.001;",
                  "THIS MODEL DOES NOT CREATE SHRINKAGE OR FEEDING"):
            self.assertIn(x, text)
        self.assertNotIn("solidificationMeltingSource;", text)
        self.assertNotIn("alpha1e", text)

    def test_native_openfoam_fvmodels_is_the_executable_source_of_truth(self):
        project = Path(__file__).resolve().parents[1]
        native = project / NATIVE_FVMODELS
        self.assertTrue(native.is_file())
        expected = model_text(read_c14_reference(project),
                              self._inherited_c05_models())
        self.assertEqual(native.read_text(), expected)
        self.assertIn("type VoFSolidificationMelting;", native.read_text())
        self.assertIn("compressible::VoFTurbulenceDamping", native.read_text())
        self.assertNotIn("solidificationMeltingSource;", native.read_text())

    def test_native_controlDict_runs_two_regions_and_writes_vof_volumes(self):
        project = Path(__file__).resolve().parents[1]
        src = (project / NATIVE_CONTROL).read_text()
        self.assertIn("fluid           compressibleVoF;", src)
        self.assertIn("mold            solid;", src)
        self.assertIn("deltaT          1e-07;", src)
        self.assertIn("endTime         2e-07;", src)
        self.assertEqual(src.count("type          volFieldValue;"), 3)
        self.assertEqual(src.count("type          surfaceFieldValue;"), 5)
        self.assertEqual(src.count("region        fluid;"), 8)
        self.assertEqual(src.count("writeFields   false;"), 8)
        self.assertIn("fields        (alpha.metal);", src)
        self.assertIn("fields        (alpha.metal.solid);", src)
        self.assertIn("fields        (rho);", src)
        for name in ("FS_C06_atmosphereMassFlux",
                     "FS_C06_atmosphereTopMassFlux",
                     "FS_C06_atmosphereSidesMassFlux",
                     "FS_C06_atmosphereLowerSidesMassFlux",
                     "FS_C06_fluidToMoldMassFlux"):
            self.assertEqual(src.count(name + "\n    {"), 1)
        self.assertEqual(src.count(
            "fields        (alphaRhoPhi.metal alphaRhoPhi.air rhoPhi);"), 5)
        self.assertIn("patches       (atmosphereTop atmosphereSides atmosphereLowerSides);", src)
        self.assertIn("patch         fluid_to_mold;", src)

    def test_native_fvmodels_composition_preserves_C05_turbulence_source(self):
        # Regression: old FS-C06 replaced the entire fvModels dictionary,
        # losing the C05 compressible VOF turbulence damping and its delta.
        project = Path(__file__).resolve().parents[1]
        old = self._inherited_c05_models()
        merged = model_text(read_c14_reference(project), old)
        self.assertTrue(merged.startswith(old.rstrip("\n")))
        self.assertEqual(merged.count("FoamFile"), 1)
        self.assertEqual(merged.count("type            compressible::VoFTurbulenceDamping;"), 1)
        self.assertEqual(merged.count("delta           1e-4;"), 1)
        self.assertEqual(merged.count("type VoFSolidificationMelting;"), 1)
        self.assertEqual(merged.count("FS_C06_vof_phase_change\n{"), 1)
        self.assertEqual(merged.count("cellZone all;"), 1)
        self.assertIn("(1423 1)\n", merged)
        self.assertIn("(1473 0)\n", merged)

    def test_native_fvmodels_rejects_missing_or_duplicate_C05_sources(self):
        project = Path(__file__).resolve().parents[1]
        reference = read_c14_reference(project)
        original = self._inherited_c05_models()
        invalid = [
            original.replace("compressible::VoFTurbulenceDamping", "unusedModel"),
            original.replace("turbulenceDamping", "renamedDamping"),
            original + "\nturbulenceDamping\n{ type compressible::VoFTurbulenceDamping; }\n",
            original.replace('"constant/fluid"', '"constant/other"'),
            original.replace("object      fvModels;", "object      somethingElse;"),
            original + "\nFS_C06_duplicate\n{ type VoFSolidificationMelting; }\n",
        ]
        for text in invalid:
            with self.subTest(source=text[-70:]):
                with self.assertRaises(ValueError):
                    model_text(reference, text)

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

    def test_volume_weighted_phase_inventory_not_fraction_sum(self):
        m = phase_volume_metrics(
            [2., 3.], [0.5, 1.0], [0.2, 0.8],
            [1440., 1410.], 1473.
        )
        self.assertAlmostEqual(m["metal_vof_volume_m3"], 4.)
        self.assertAlmostEqual(m["metal_solid_volume_m3"], 2.8)
        self.assertAlmostEqual(m["metal_liquid_volume_m3"], 1.2)
        self.assertAlmostEqual(
            m["metal_solid_fraction_conditional_volume_weighted"], .7
        )
        self.assertAlmostEqual(m["metal_T_mean_K_alpha_volume_weighted"], 1417.5)
        self.assertEqual(m["metal_vof_fraction_below_C14_liquidus"], 1.)
        self.assertFalse(m["metal_mass_conservation_verified"])
        self.assertFalse(m["volumetric_shrinkage_or_feeding_verified"])

    def test_all_liquid_above_liquidus_is_not_phase_change(self):
        m = phase_volume_metrics([1., 2.], [1., .5], [0., 0.],
                                 [1500., 1500.], 1473.)
        self.assertEqual(m["metal_solid_volume_m3"], 0.)
        self.assertEqual(m["metal_vof_fraction_below_C14_liquidus"], 0.)
        self.assertFalse(m["rho_liquid_and_rho_solid_verified"])

    def test_volume_metric_rejects_solid_larger_than_vof(self):
        with self.assertRaises(ValueError):
            phase_volume_metrics([1.], [.2], [.3], [1400.], 1473.)

    def test_volume_metric_rejects_nonpositive_or_nan_inputs(self):
        examples = [
            ([0.], [1.], [0.], [1400.], 1473.),
            ([1.], [1.], [0.], [math.nan], 1473.),
            ([1.], [1.], [-.01], [1400.], 1473.),
            ([1.], [0.], [0.], [1400.], 1473.),
            ([1.], [1.], [0.], [1400.], math.inf),
        ]
        for args in examples:
            with self.subTest(args=args), self.assertRaises(ValueError):
                phase_volume_metrics(*args)

    def test_volume_metric_rejects_numerically_negative_phase(self):
        with self.assertRaises(ValueError):
            phase_volume_metrics([1.], [.5], [.500000001],
                                 [1450.], 1473.)

    def _native_field(self, body, obj="alpha.metal.solid", fmt="ascii"):
        return (
            "FoamFile\n{\n"
            "    version 2.0;\n"
            f"    format {fmt};\n"
            "    class volScalarField;\n"
            f"    object {obj};\n"
            "}\n"
            f"internalField {body}\n"
            "boundaryField {}\n"
        )

    def test_native_auto_write_solid_uniform_is_read(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / MODEL_FIELD
            p.write_text(self._native_field("uniform 0.25;"))
            self.assertEqual(read_native_solid_fraction(p, 3), [.25]*3)

    def test_native_auto_write_solid_nonuniform_is_read(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / MODEL_FIELD
            p.write_text(self._native_field(
                "nonuniform List<scalar> 3\n(\n0.0\n0.125\n0.8\n);"))
            self.assertEqual(read_native_solid_fraction(p, 3),
                             [0., .125, .8])

    def test_native_reader_never_misidentifies_alpha_metal(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / MODEL_FIELD
            p.write_text(self._native_field("uniform 0.1;",
                                            obj="alpha.metal"))
            with self.assertRaises(ValueError):
                read_native_solid_fraction(p, 2)

    def test_native_reader_fail_closed_bad_output(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / MODEL_FIELD
            examples = [
                (self._native_field("nonuniform List<scalar> 2\n(0.1 0.2);"), 3),
                (self._native_field("nonuniform List<scalar> 3\n(0.1 0.2);"), 3),
                (self._native_field("uniform nan;"), 2),
                (self._native_field("uniform 0.1;", fmt="binary"), 2),
                (self._native_field("nonuniform List<vector> 2\n((0 0 0) (1 1 1));"), 2),
            ]
            for field, cells in examples:
                with self.subTest(field=field[:80]), self.assertRaises(ValueError):
                    p.write_text(field)
                    read_native_solid_fraction(p, cells)
            p.unlink()
            with self.assertRaises(ValueError):
                read_native_solid_fraction(p, 2)

    def test_metal_phase_temperature_not_mixture_temperature(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'T.metal'
            p.write_text(self._native_field('uniform 1462;', obj='T.metal'))
            self.assertEqual(read_native_metal_temperature(p, 3), [1462.]*3)
            p.write_text(self._native_field('uniform 1462;', obj='T'))
            with self.assertRaises(ValueError):
                read_native_metal_temperature(p, 3)
            p.write_text(self._native_field('uniform -1;', obj='T.metal'))
            with self.assertRaises(ValueError):
                read_native_metal_temperature(p, 3)

    def test_solid_and_metal_temperature_readers_are_not_interchangeable(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'T.metal'
            p.write_text(self._native_field('uniform 1500;', obj='T.metal'))
            with self.assertRaises(ValueError):
                read_native_solid_fraction(p, 2)
    def test_constants_and_outputs_distinct(self):
        self.assertEqual(TIMES, ("1e-07", "2e-07"))
        self.assertEqual(MODEL_FIELD, "alpha.metal.solid")
        self.assertTrue(PREFIX.startswith("FS_C06_"))


if __name__ == "__main__":
    unittest.main()
