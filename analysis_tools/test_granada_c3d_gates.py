"""Static checks for C3D Granada science provenance. NEVER execute OpenFOAM or change cases."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "granada"
GATES = json.loads((DOCS / "C3D_01_EVIDENCE_GATES.json").read_text(encoding="utf-8"))


class GranadaC3DScienceGateTests(unittest.TestCase):
    def test_provenance_is_never_passed_without_measured_chemistry(self):
        self.assertEqual(GATES["science_gates"]["MAT-01"]["status"], "OPEN")
        self.assertEqual(GATES["science_gates"]["J0"]["status"], "OPEN")
        self.assertEqual(GATES["observed_from_user"]["gray_cast_iron"], "USER_EXPECTATION_UNCONFIRMED")
        self.assertEqual(GATES["observed_from_user"]["host2_windows_physical_ram"], "NOT_MEASURED")

    def test_no_simulation_accepted_on_static_metadata(self):
        for key in ("background_mesh", "snappy_hex_mesh", "multiregion_mesh",
                    "three_dimensional_cfd", "mpi_benchmark"):
            self.assertEqual(GATES["run_evidence"][key], "NOT_RUN_EVIDENCED", key)
        for key in ("MESH-01", "MESH-02"):
            self.assertEqual(GATES["science_gates"][key]["status"], "NOT_RUN")

    def test_open_draft_pr_is_isolated(self):
        self.assertEqual(GATES["active_draft_pr"]["number"], 18)
        self.assertEqual(GATES["active_draft_pr"]["disposition"], "LEAVE_OPEN_UNTOUCHED")
        self.assertIn("DO_NOT_FORCE_0P5MM_AS_ACCEPTED_CRITERION",
                      GATES["prohibitions"])

    def test_all_mentioned_source_files_exist(self):
        for path in GATES["sources"]:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_gates_have_documentation_and_explanations(self):
        files = (
            "C3D_01_MALLA_Y_FISICA_ES.md",
            "COMPOSICION_Y_PROCEDENCIA_ES.md",
            "EQUIPOS_MPI_Y_EJECUCION_ES.md",
            "GRANADA_C3D_HANDOFF_ES.md",
        )
        for path in files:
            with self.subTest(path=path):
                self.assertGreater((DOCS / path).stat().st_size, 500)
        material = (DOCS / "COMPOSICION_Y_PROCEDENCIA_ES.md").read_text(encoding="utf-8")
        self.assertIn("NO SON LA TESIS", material)
        physics = (DOCS / "C3D_01_MALLA_Y_FISICA_ES.md").read_text(encoding="utf-8")
        self.assertIn("mushy zone", physics)
        self.assertIn("0.5 mm", physics)
        self.assertIn("recalescencia", physics.lower())


if __name__ == "__main__":
    unittest.main()
