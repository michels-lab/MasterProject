#!/usr/bin/env python3
"""3D registry resolution regression; source directories never imply CFD success."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reg_checker", HERE / "check_run_registry.py")
reg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg)


class ThreeDimensionalCaseFolders(unittest.TestCase):
    def test_all_explicit_3d_categories_count_when_real_directory_exists(self):
        rows = [
            {"case":"C3D_02_metal_sand_clean", "group":"THREE_D_CLEAN_RESTART", "run_status":"PREPARED_NOT_RUN"},
            {"case":"C3D_03_doctor_multiblock_pilot", "group":"THREE_D_TOPOLOGY_PILOT", "run_status":"PREPARED_NOT_RUN"},
            {"case":"C3D_04_rounded_multiblock_pilot", "group":"THREE_D_CURVILINEAR_BLOCKMESH_PILOT", "run_status":"PREPARED_NOT_RUN"},
            {"case":"C3D_05_step_gmsh_conformal", "group":"THREE_D_STEP_GMSH_PARALLEL_PILOT", "run_status":"PREPARED_NOT_RUN"},
        ]
        with TemporaryDirectory() as temp:
            root=Path(temp)
            controlled=root/"cases_controlled_buoyancy"
            three=root/"cases_3d"
            controlled.mkdir()
            three.mkdir()
            (controlled/"B3_reference").mkdir()
            for row in rows:
                (three/row["case"]).mkdir()
            # Unregistered geometry must NOT automatically count as a verified case.
            (three/"C3D_01_geometry_experiment").mkdir()
            got=reg.existing_registry_case_dirs(rows, controlled, three)
            self.assertEqual(len(got), 5)
            self.assertIn("B3_reference", got)
            for row in rows:
                self.assertIn(row["case"],got)
                self.assertEqual(row["run_status"],"PREPARED_NOT_RUN")
            self.assertNotIn("C3D_01_geometry_experiment",got)

    def test_missing_registered_3d_directory_is_not_silently_accepted(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            controlled=root/"controlled"
            three=root/"three_d"
            controlled.mkdir()
            three.mkdir()
            rows=[{"case":"C3D_05_step_gmsh_conformal","group":"THREE_D_STEP_GMSH_PARALLEL_PILOT"}]
            got=reg.existing_registry_case_dirs(rows,controlled,three)
            self.assertNotIn(rows[0]["case"],got)

    def test_2d_extra_directory_remains_visible_for_unregistered_check(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            a=root/"controlled"
            b=root/"three_d"
            a.mkdir()
            b.mkdir()
            (a/"UNREGISTERED_2D_DIR").mkdir()
            got=reg.existing_registry_case_dirs([],a,b)
            self.assertIn("UNREGISTERED_2D_DIR",got)

if __name__ == "__main__":
    unittest.main()
