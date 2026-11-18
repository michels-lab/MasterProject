"""FS-C02 provisional iron/air source and isolation regressions (NO CFD)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from run_fs_c02_local import (
    B14_MATERIAL, CASE_ID, DENSITY, INITIAL_VOLUME, REPO, SIGMA, SOURCE,
    THERMO_METAL, check_runtime, outside_repo, replace_once, stage,
    validate_b14_reference,
)


class FSC02Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fs-c02-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "FS-C02_once"

    def test_reads_only_B14_material_identity_and_frozen_fs_c01(self):
        self.assertEqual(CASE_ID, "FS-C02")
        self.assertEqual(B14_MATERIAL.name, "castIron")
        self.assertTrue(len(validate_b14_reference()) == 64)
        self.assertEqual(INITIAL_VOLUME, 1.6e-5)
        self.assertEqual(DENSITY, 6820.0)

    def test_new_case_creates_distinct_source_without_modifying_B14_or_FS_C01(self):
        source_digest = hashlib.sha256((SOURCE / "0/alpha.water").read_bytes()).hexdigest()
        b14_digest = hashlib.sha256(B14_MATERIAL.read_bytes()).hexdigest()
        case, status = stage(self.out)
        self.assertEqual(case.name, "FS-C02")
        self.assertEqual(status["status"], "STAGED_NO_CFD_YET")
        self.assertFalse(status["contraction_modelled"])
        self.assertFalse(status["mass_verified"])
        self.assertFalse((case / "constant/polyMesh").exists())
        self.assertFalse((case / "postProcessing").exists())
        self.assertFalse((case / "0/alpha.water").exists())
        self.assertFalse((case / "constant/physicalProperties.water").exists())
        self.assertTrue((case / "0/alpha.metal").is_file())
        self.assertTrue((case / "constant/physicalProperties.metal").is_file())
        self.assertEqual(
            source_digest, hashlib.sha256((SOURCE / "0/alpha.water").read_bytes()).hexdigest())
        self.assertEqual(b14_digest, hashlib.sha256(B14_MATERIAL.read_bytes()).hexdigest())

    def test_phase_thermo_field_B14_provenance_and_no_fake_shrinkage(self):
        case, _ = stage(self.out)
        p = (case / "constant/phaseProperties").read_text()
        self.assertIn("phases (metal air);", p)
        self.assertIn("type constant;", p)
        self.assertIn("sigma 1.0;", p)
        self.assertIn("rhoConst", (case / "constant/physicalProperties.metal").read_text())
        self.assertIn("Cv 827;", THERMO_METAL)
        self.assertIn("rho 6820;", THERMO_METAL)
        self.assertIn("alpha.metal.*", (case / "system/fvSolution").read_text())
        self.assertIn("object alpha.metal;", (case / "0/alpha.metal").read_text())
        t = (case / "0/T").read_text()
        self.assertIn("defaultValue 300;", t)
        self.assertIn("value 1500;", t)
        self.assertIn("inletValue      uniform 300;", t)
        control = (case / "system/controlDict").read_text()
        self.assertIn("fields (alpha.metal);", control)
        self.assertIn("metalVolume", control)
        self.assertIn("writeFields false;", control)
        manifest = json.loads((case / "FS-C02_MANIFEST.json").read_text())
        self.assertEqual(len(manifest["generated_input_sha256"]), 20)
        self.assertEqual(manifest["reference_metal_mass_kg"], DENSITY * INITIAL_VOLUME)
        self.assertEqual(manifest["physical_assumptions"]["surface_tension"],
                         "1.0 N/m PROVISIONAL UNSOURCED")
        for physics in ("solidification", "latent_heat", "mold", "contraction", "porosity"):
            self.assertIs(manifest["physical_assumptions"][physics], False)

    def test_manifest_sha256_checks_every_transformed_input(self):
        case, _ = stage(self.out)
        manifest = json.loads((case / "FS-C02_MANIFEST.json").read_text())
        for rel, expected in manifest["generated_input_sha256"].items():
            with self.subTest(file=rel):
                self.assertEqual(
                    hashlib.sha256((case / rel).read_bytes()).hexdigest(), expected)

    def test_restage_same_path_fails_without_overwriting(self):
        stage(self.out)
        with self.assertRaisesRegex(ValueError, "pre-existing"):
            stage(self.out)
        self.assertTrue((self.out / "FS-C02" / "FS-C02_MANIFEST.json").exists())

    def test_original_checkouts_and_wrong_run_namespaces_are_rejected(self):
        for output in (
            REPO / "freesurface" / "FS-C02",
            Path.home() / "OpenFOAM" / "MasterProject" / "cases_3d" / "C3D_02_metal_sand_clean",
            Path.home() / "OpenFOAM" / "FS_C01_RUNS" / "FS-C02_accidental",
        ):
            with self.subTest(path=output), self.assertRaisesRegex(ValueError, "FS-C02"):
                outside_repo(output)

    def test_unsupported_fs_c01_schema_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unexpected"):
            replace_once("alpha.water alpha.water", "alpha.water", "alpha.metal", "alpha")

    def test_only_foundation14_runtime_accepted(self):
        with patch.dict("os.environ", {"WM_PROJECT_VERSION": "13"}):
            with self.assertRaisesRegex(ValueError, "Foundation 14"):
                check_runtime()
        with patch.dict("os.environ", {"WM_PROJECT_VERSION": "14"}), \
             patch("run_fs_c02_local.shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, "not in PATH"):
                check_runtime()


if __name__ == "__main__":
    unittest.main()
