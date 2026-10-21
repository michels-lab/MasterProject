"""Synthetic scientific guards for PLAN D case3d-01. No CFD or original STL."""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from granada_plan_d_case3d01_mesh_gate import (
    CANONICAL_CASE_ID, LEGACY_SOURCE, EXPECTED_BASE_CELLS, inspect, main
)

BOX = """FoamFile { format ascii; }
units [mm];
vertices (
 (-3 -69 -3) (55 -69 -3) (55 3 -3) (-3 3 -3)
 (-3 -69 55) (55 -69 55) (55 3 55) (-3 3 55)
);
blocks ( hex (0 1 2 3 4 5 6 7) (29 36 29) simpleGrading (1 1 1) );
boundary ( outerBox { type patch; faces ((0 1 5 4)); } );
"""
LOG_BLOCK = """Create time
Creating block mesh
Mesh bounding box (-0.003 -0.069 -0.003) (0.055 0.003 0.055)
End
"""
LOG_CHECK = """Mesh stats
    cells: 30276
Checking geometry...
    Overall domain bounding box (-0.003 -0.069 -0.003) (0.055 0.003 0.055)
Mesh OK.
"""


def setup_case(root):
    c = root/LEGACY_SOURCE
    (c/"system").mkdir(parents=True)
    (c/"system/blockMeshDict").write_text(BOX)
    ref = {
        "stl_original_units": "mm",
        "background_mesh": {
            "bounds_min_m": [-.003, -.069, -.003],
            "bounds_max_m": [.055, .003, .055],
            "cells_nxyz": [29,36,29],
        },
        "sampled_seed_points_m": {
            "metal": [.0259,-.02,.0259],
            "mold": [.003,-.02,.0259],
        },
        "metal": {"original_filename":"metal.STL",
                  "original_sha256":hashlib.sha256(b"metal fixture").hexdigest(),
                  "triangle_count":3896,"stl_volume_m3":.00004798749039244212,
                  "bounds_m":[[.00765,-.04,.00765],[.04415,0,.04415]]},
        "mold": {"original_filename":"QuickCup.STL",
                 "original_sha256":hashlib.sha256(b"mold fixture").hexdigest(),
                 "triangle_count":3084,"stl_volume_m3":.00010284316521098784,
                 "bounds_m":[[0,-.0655,0],[.0518,0,.0518]]},
    }
    (c/"geometry_reference.json").write_text(json.dumps(ref))
    return c


class PlanDCase3D01Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/"repo"
        self.case = setup_case(self.root)

    def logs(self, block=LOG_BLOCK, check=LOG_CHECK):
        folder = Path(self.temp.name)/"logs"
        folder.mkdir(exist_ok=True)
        a, b = folder/"log.blockMesh", folder/"log.checkMesh.background"
        a.write_text(block); b.write_text(check)
        return a,b

    def test_canonical_case_name_and_legacy_source_are_distinct(self):
        r=inspect(self.root)
        self.assertEqual(r["case_id"],"case3d-01")
        self.assertEqual(CANONICAL_CASE_ID,"case3d-01")
        self.assertIn("C3D_01_metal_mold",r["source_directory_legacy_until_open_PRs_resolved"])
        self.assertTrue(r["no_OpenFOAM_commands_executed"])

    def test_background_source_strict_dimensions_and_cell_count(self):
        r=inspect(self.root)["background_input"]
        self.assertEqual(r["total_background_cells"],EXPECTED_BASE_CELLS)
        self.assertEqual(r["spacing_mm"],[2.,2.,2.])
        self.assertIn("NOT_CHECKMESH",r["status"])

    def test_stl_absence_is_explicit_not_zero_flux_or_validation(self):
        a=inspect(self.root)
        self.assertTrue(all(v["status"]=="PRIVATE_STL_NOT_PROVIDED"
                            for v in a["private_stl_provenance"].values()))
        self.assertEqual(a["mesh_log_screen"]["status"],"NOT_RUN_LOGS_NOT_SUPPLIED")
        self.assertEqual(a["global_CFD_validation"],"NOT_VALIDATED")

    def test_verify_actual_bytes_of_both_private_stls(self):
        d=Path(self.temp.name)/"STL"
        d.mkdir()
        (d/"metal.STL").write_bytes(b"metal fixture")
        (d/"QuickCup.STL").write_bytes(b"mold fixture")
        a=inspect(self.root,stl_dir=d)
        self.assertTrue(all("SOURCE_BYTES_MATCH" in v["status"] for v in
                            a["private_stl_provenance"].values()))
        self.assertEqual(len(a["source_manifest"]),4)
        self.assertEqual(a["scientific_gates"]["JMatPro_J0"],"OPEN")

    def test_reject_changed_private_stl_bytes(self):
        d=Path(self.temp.name)/"STL"
        d.mkdir()
        (d/"metal.STL").write_bytes(b"metal fixture")
        (d/"QuickCup.STL").write_bytes(b"wrong mold")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            inspect(self.root,stl_dir=d)

    def test_reject_double_scale_or_missing_mm_units(self):
        p=self.case/"system/blockMeshDict"
        p.write_text(p.read_text().replace("units [mm];","scale 0.001;"))
        with self.assertRaisesRegex(ValueError,"units"):
            inspect(self.root)
        p.write_text(BOX+"scale 0.001;")
        with self.assertRaisesRegex(ValueError,"double"):
            inspect(self.root)

    def test_reject_wrong_block_cell_shape(self):
        p=self.case/"system/blockMeshDict"
        p.write_text(BOX.replace("(29 36 29)","(30 36 29)"))
        with self.assertRaisesRegex(ValueError,"subdivision"):
            inspect(self.root)

    def test_reject_geometry_outside_box(self):
        p=self.case/"geometry_reference.json"
        ref=json.loads(p.read_text())
        ref["metal"]["bounds_m"][1][0]=1.0
        p.write_text(json.dumps(ref))
        with self.assertRaisesRegex(ValueError,"not inside background mesh"):
            inspect(self.root)

    def test_reject_seed_point_collision(self):
        p=self.case/"geometry_reference.json"
        ref=json.loads(p.read_text())
        ref["sampled_seed_points_m"]["mold"]=ref["sampled_seed_points_m"]["metal"]
        p.write_text(json.dumps(ref))
        with self.assertRaisesRegex(ValueError,"cannot be identical"):
            inspect(self.root)

    def test_present_pass_marked_as_log_screen_only(self):
        logs=self.logs()
        r=inspect(self.root,log_blockmesh=logs[0],log_checkmesh=logs[1])
        a=r["mesh_log_screen"]
        self.assertEqual(a["status"],"SUPPLIED_LOG_SCREEN_PASSED_NOT_INDEPENDENT_MESH_CHECK")
        self.assertFalse(a["errors"])
        self.assertEqual(len(a["log_sha256"]),2)
        self.assertEqual(r["scientific_gates"]["snappyHexMesh"],"NOT_EXECUTED_BY_THIS_TOOL")

    def test_missing_mesh_ok_does_not_pass(self):
        logs=self.logs(check=LOG_CHECK.replace("Mesh OK.","Mesh FAILED."))
        a=inspect(self.root,log_blockmesh=logs[0],log_checkmesh=logs[1])
        self.assertEqual(a["mesh_log_screen"]["status"],"SUPPLIED_LOG_REVIEW")
        self.assertIn("Mesh OK", str(a["mesh_log_screen"]["errors"]))

    def test_wrong_mesh_cells_and_bounds_not_accepted(self):
        logs=self.logs(check=LOG_CHECK.replace("30276","123").replace("0.055","0.5"))
        a=inspect(self.root,log_blockmesh=logs[0],log_checkmesh=logs[1])
        self.assertEqual(len(a["mesh_log_screen"]["errors"]),2)

    def test_fatal_errors_overrule_success_markers(self):
        logs=self.logs(block=LOG_BLOCK+"FOAM FATAL ERROR\n")
        a=inspect(self.root,log_blockmesh=logs[0],log_checkmesh=logs[1])
        self.assertIn("fatal error",str(a["mesh_log_screen"]["errors"]))

    def test_only_one_log_refused(self):
        logs=self.logs()
        with self.assertRaisesRegex(ValueError,"both blockMesh and checkMesh"):
            inspect(self.root,log_blockmesh=logs[0])

    def test_nominal_resolution_cost_is_estimate_not_claimed_result(self):
        a=inspect(self.root)
        options=a["nominal_resolution_options"]
        self.assertEqual([x["nominal_cell_edge_mm"] for x in options],[2.,1.,.5,.25])
        self.assertGreater(options[2]["combined_ideal_uniform_cells"],1_200_000)
        self.assertEqual(a["mesh_resolution_decision"],"OPEN_0.5MM_NOT_AUTOMATICALLY_APPROVED")

    def test_cli_readonly_outputs_and_required_evidence_gate(self):
        out=Path(self.temp.name)/"out"
        self.assertEqual(main(["--root",str(self.root),"--out",str(out)]),0)
        self.assertTrue((out/"case3d-01-mesh-readiness.json").is_file())
        self.assertTrue((out/"case3d-01-nominal-resolution.csv").is_file())
        with self.assertRaisesRegex(ValueError,"overwrite"):
            main(["--root",str(self.root),"--out",str(out)])
        self.assertEqual(main(["--root",str(self.root),"--out",str(Path(self.temp.name)/"out2"),
                               "--require-mesh-logs"]),1)
        self.assertEqual(main(["--root",str(self.root),"--out",str(Path(self.temp.name)/"out3"),
                               "--require-stls"]),1)

    def test_output_inside_repo_is_blocked(self):
        with self.assertRaisesRegex(ValueError,"independent"):
            main(["--root",str(self.root),"--out",str(self.case/"evidence")])

    def test_valid_source_manifest_all_sha(self):
        a=inspect(self.root)
        self.assertEqual(len(a["source_manifest"]),2)
        for src in a["source_manifest"]:
            f=self.root/src["path"]
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),src["sha256"])

    def test_canonical_case_staging_shell_is_parseable(self):
        path=Path(__file__).resolve().parents[1]/"cases_3d/case3d-01/scripts/stage_mesh_only.sh"
        r=subprocess.run(["bash","-n",str(path)],capture_output=True,text=True,check=False)
        self.assertEqual(r.returncode,0,r.stderr)
        script=path.read_text()
        self.assertNotIn("rm -rf",script)
        self.assertNotIn("foamMultiRun >",script)
        self.assertIn("sha256sum --check --status",script)

    def test_staging_missing_STLs_fails_without_output(self):
        path=Path(__file__).resolve().parents[1]/"cases_3d/case3d-01/scripts/stage_mesh_only.sh"
        out=Path(self.temp.name)/"safe-case3d-01"
        missing=Path(self.temp.name)/"missing-stl-source"
        r=subprocess.run(["bash",str(path),str(out),str(missing)],
                         capture_output=True,text=True,check=False)
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
