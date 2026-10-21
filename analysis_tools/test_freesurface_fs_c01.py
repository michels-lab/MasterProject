"""Static integrity tests for the committed FS-C01 case; no OpenFOAM run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "freesurface" / "FS-C01"


class FreeSurfaceFS_C01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((CASE / "BFS01_MANIFEST.json").read_text(encoding="utf8"))

    def test_case_directory_and_research_name(self):
        self.assertTrue(CASE.is_dir())
        self.assertIn("FS-C01", (CASE / "CASE_NOTES.md").read_text())
        self.assertEqual(self.manifest["status"], "PREPARED_NOT_MESHED_OR_RUN")
        self.assertEqual(self.manifest["schema"], "quickcup-bfs01-hydro-analogue-v1")

    def test_every_input_sha256_matches_staged_artifact(self):
        hashes = self.manifest["generated_sha256"]
        self.assertEqual(len(hashes), 20)
        for name, expected in hashes.items():
            with self.subTest(file=name):
                f = CASE / name
                self.assertTrue(f.is_file())
                self.assertFalse(f.is_symlink())
                self.assertNotIn("..", Path(name).parts)
                self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), expected)

    def test_no_untracked_solver_inputs_or_results(self):
        observed = {p.relative_to(CASE).as_posix() for p in CASE.rglob("*") if p.is_file()
                    and p.parts[len(CASE.parts)] in ("0", "constant", "system")}
        self.assertEqual(observed, set(self.manifest["generated_sha256"]))
        self.assertFalse((CASE / "postProcessing").exists())
        self.assertFalse((CASE / "processor0").exists())
        self.assertFalse((CASE / "constant/polyMesh").exists())

    def test_official_solver_and_analogue_phase_identity(self):
        cfg = (CASE / "system/controlDict").read_text()
        phases = (CASE / "constant/phaseProperties").read_text()
        self.assertRegex(cfg, r"(?m)^solver\s+compressibleVoF\s*;")
        self.assertRegex(phases, r"phases\s*\(water\s+air\)\s*;")
        self.assertEqual(self.manifest["fluid_identity"], "WATER_AIR_ANALOGUE_NOT_MOLTEN_IRON")
        self.assertFalse(self.manifest["physics"]["shrinkage"])
        self.assertFalse(self.manifest["physics"]["solidification"])

    def test_geometry_initial_fill_and_volume_diagnostic(self):
        mesh = (CASE / "system/blockMeshDict").read_text()
        alpha = (CASE / "0/alpha.water").read_text()
        control = (CASE / "system/controlDict").read_text()
        self.assertIn("(80 120 1)", mesh)
        self.assertIn("atmosphere { type patch;", mesh)
        self.assertIn("frontAndBack { type empty;", mesh)
        self.assertIn("box (0 0 -1) (0.04 0.04 1);", alpha)
        self.assertIn("fields (alpha.water);", control)
        self.assertAlmostEqual(self.manifest["analytical_initial_water_volume_m3"], 1.6e-5)
        self.assertAlmostEqual(self.manifest["end_time_s"], 0.1)

    def test_operation_is_not_marked_as_completed_cfd(self):
        instructions = (CASE / "HOW_TO_RUN.md").read_text()
        self.assertIn("foamRun", instructions)
        self.assertIn("not", instructions.lower())
        self.assertNotIn("RUN_VERIFIED", (CASE / "CASE_NOTES.md").read_text())


if __name__ == "__main__":
    unittest.main()
