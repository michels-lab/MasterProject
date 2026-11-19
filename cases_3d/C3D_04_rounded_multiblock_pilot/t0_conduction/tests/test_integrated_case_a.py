#!/usr/bin/env python3
"""One integrated static regression suite for CASE A T0; never calls OpenFOAM."""
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

CASE_A = pathlib.Path(__file__).resolve().parents[2]
T0 = CASE_A / "t0_conduction"
SCRIPTS = T0 / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(CASE_A / "scripts"))

import prepare_case_a_t0 as engine
import report_case_a_progress as progress


class IntegratedCaseAT0(unittest.TestCase):
    def test_01_progress_is_consistent_and_canonical(self):
        status = progress.report(progress.STATUS_FILE)
        self.assertEqual(status["scope"], "CASE_A_C3D_04_V4_T02_ONLY")
        self.assertEqual(status["progress_count_total"], 10)
        self.assertEqual(status["progress_count_done"],
                         sum(e["status"] == "DONE" for e in status["milestones"]))
        self.assertEqual(status["progress_percent"],
                         10*status["progress_count_done"])
        self.assertEqual(
            status["current_stage"],
            next(e["id"] for e in status["milestones"] if e["status"] == "IN_PROGRESS")
        )
        if status["current_stage"] == "05_THERMAL_T0_DESIGN":
            self.assertFalse(status["CFD_run"])
        for field in ("CFD_run", "grid_independence", "physical_validation"):
            self.assertIs(type(status[field]), bool)
        with tempfile.TemporaryDirectory() as folder:
            p = pathlib.Path(folder) / "status.json"
            bad = copy.deepcopy(status)
            bad["progress_percent"] = 90
            p.write_text(json.dumps(bad))
            with self.assertRaises(AssertionError):
                progress.report(p)

    def test_02_real_inputs_are_strictly_blocked_until_sourced(self):
        cfg = engine.synthetic_fixture()
        # Synthetic deliberately unfilled fixture, independent of whether
        # the user later enters correctly sourced real data into T0_INPUTS.
        for region in ("metal", "mold"):
            for field, source in engine.FIELDS.items():
                cfg[region][field] = None
                cfg[region][source] = None
        for field in ("deltaT_s", "endTime_s", "writeEverySteps",
                      "nNonOrthogonalCorrectors", "source_time_choices",
                      "source_nonorth_choice"):
            cfg["simulation"][field] = None
        self.assertGreaterEqual(len(engine.validate(cfg)), 15)
        self.assertFalse(engine.positive(None))
        self.assertFalse(engine.positive(float("nan")))
        self.assertFalse(engine.positive(True))
        self.assertFalse(engine.positive(0))
        with self.assertRaises(ValueError):
            engine.generate(cfg)

    def test_03_all_nine_thermal_dictionaries_generated_from_synthetic_fixture(self):
        cfg = engine.synthetic_fixture()
        self.assertEqual(engine.validate(cfg, allow_synthetic_test=True), [])
        self.assertNotEqual(engine.validate(cfg), [])
        items = engine.generate(cfg)
        self.assertEqual(len(items), 10)
        self.assertEqual(set(items), {
            "0/metal/T", "0/mold/T",
            "constant/metal/physicalProperties", "constant/mold/physicalProperties",
            "system/controlDict", "system/fvSolution",
            "system/metal/fvSchemes", "system/metal/fvSolution",
            "system/mold/fvSchemes", "system/mold/fvSolution",
        })
        for name, content in items.items():
            self.assertNotIn("{{", content, name)
            self.assertNotIn("C3D-05", content, name)
            self.assertEqual(content.count("{"), content.count("}"), name)
        self.assertIn("application foamMultiRun;", items["system/controlDict"])
        self.assertIn("nEnergyCorrectors 2;", items["system/fvSolution"])
        self.assertIn("metal solid;", items["system/controlDict"])
        self.assertIn("mold solid;", items["system/controlDict"])
        self.assertIn("nNonOrthogonalCorrectors 2;", items["system/metal/fvSolution"])
        self.assertIn("constIsoSolid", items["constant/metal/physicalProperties"])

    def test_04_validate_actual_C3D04_patch_contract_without_a_mesh(self):
        cfg = engine.synthetic_fixture()
        items = engine.generate(cfg)
        self.assertEqual(set(engine.EXTERIOR["metal"]), {"metalTop"})
        self.assertEqual(set(engine.EXTERIOR["mold"]), {
            "moldTop", "moldExterior", "moldBottom",
            "moldRecessWall", "moldRecessRoof"
        })
        for region in ("metal", "mold"):
            field = items[f"0/{region}/T"]
            self.assertEqual(field.count("type coupledTemperature;"), 1)
            self.assertEqual(field.count("type zeroGradient;"), len(engine.EXTERIOR[region]))
            for patch in engine.EXTERIOR[region] + (engine.COUPLED[region],):
                self.assertIn(patch + "\n", field)
        self.assertNotIn("moldOuterUnclassified", items["0/mold/T"])
        self.assertNotIn("type patch;", items["0/metal/T"])

    def test_045_real_boundary_coverage_detects_extra_patches(self):
        with tempfile.TemporaryDirectory() as folder:
            f = pathlib.Path(folder)/"boundary"
            f.write_text(
                "FoamFile { version 2.0; }\n"
                "metalTop\n{ type wall; nFaces 256; startFace 123; }\n"
                "metal_to_mold\n{ type mappedWall; nFaces 2496; startFace 456; }\n"
                "unexpectedFaces\n{ type wall; nFaces 0; startFace 0; }\n"
            )
            self.assertEqual(
                engine.physical_patch_names(f), {"metalTop", "metal_to_mold"}
            )
            f.write_text(f.read_text().replace("nFaces 0;", "nFaces 7;"))
            self.assertEqual(
                engine.physical_patch_names(f),
                {"metalTop", "metal_to_mold", "unexpectedFaces"}
            )

    def test_046_native_volume_source_and_adiabatic_energy_target(self):
        cfg = engine.synthetic_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            report = root/"PILOT_MESH_REPORT.tsv"
            report.write_text(
                "region\tcells\tvolume_m3\tCAD_m3\tmesh_ok\n"
                "metal\t8960\t4.79e-5\t4.80e-5\tYES\n"
                "mold\t12352\t1.028e-4\t1.028e-4\tYES\n"
            )
            measured = engine.read_preserved_mesh_volumes(root)
            self.assertEqual(measured["metal"], 4.79e-5)
            self.assertEqual(measured["mold"], 1.028e-4)
            target = engine.closed_t0_energy_target(cfg, measured)
            self.assertTrue(6 < target["ideal_equilibrium_K_no_heat_loss"] < 7)
            self.assertEqual(target["validation_status"],
                             "ANALYTICAL_TARGET_ONLY_NOT_CFD_OUTPUT")
            report.write_text(report.read_text().replace("YES", "NO", 1))
            with self.assertRaises(ValueError):
                engine.read_preserved_mesh_volumes(root)

    def test_05_negative_cases_and_isolation(self):
        cfg = engine.synthetic_fixture()
        cfg["metal"]["source_rho"] = None
        self.assertTrue(any("source_rho" in e for e in engine.validate(cfg)))
        cfg["metal"]["source_rho"] = "SYNTHETIC_UNIT_TEST"
        cfg["simulation"]["nNonOrthogonalCorrectors"] = -1
        self.assertTrue(any("nNonOrthogonalCorrectors" in e for e in engine.validate(cfg)))
        cfg["simulation"]["nNonOrthogonalCorrectors"] = 2
        cfg["mold"]["T_initial_K"] = cfg["metal"]["T_initial_K"]
        self.assertTrue(any("T_initial_K" in e for e in engine.validate(cfg)))
        with tempfile.TemporaryDirectory() as folder:
            source = pathlib.Path(folder)/"reference"
            source.mkdir()
            with self.assertRaises(ValueError):
                engine.isolated_output(source, source)
            with self.assertRaises(ValueError):
                engine.isolated_output(source, source/"nested")
            with self.assertRaises(ValueError):
                engine.isolated_output(source, source.parent)
            existing = pathlib.Path(folder)/"present"
            existing.mkdir()
            with self.assertRaises(FileExistsError):
                engine.isolated_output(source, existing)

    def test_055_atomic_materialization_and_native_dictionary_failure(self):
        cfg = engine.synthetic_fixture()
        items = engine.generate(cfg)
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            src = root/"accepted_T02"
            for region in ("metal", "mold"):
                mesh = src/"constant"/region/"polyMesh"
                mesh.mkdir(parents=True)
                for name in ("points", "faces", "owner", "neighbour", "boundary"):
                    (mesh/name).write_bytes(f"REGION={region} FILE={name}".encode())
            cfg_path = root/"synthetic_test_only.json"
            cfg_path.write_text(json.dumps(cfg))
            output = root/"prepared_T0"
            environment = {"WM_PROJECT_VERSION": "14"}
            with patch.dict(engine.os.environ, environment), \
                 patch.object(engine.shutil, "which", return_value="/mock/foamDictionary"), \
                 patch.object(engine.subprocess, "run",
                              return_value=types.SimpleNamespace(
                                  returncode=2, stdout="", stderr="bad dictionary")):
                with self.assertRaises(RuntimeError):
                    engine.materialize(
                    src, output, cfg, cfg_path, items,
                    {"native_volumes_m3_from_preserved_tsv":
                     {"metal": 1.0, "mold": 1.0}}
                )
                self.assertFalse(output.exists())
            self.assertFalse(list(root.glob(".prepared_T0.staging.*")))
            with patch.dict(engine.os.environ, environment), \
                 patch.object(engine.shutil, "which", return_value="/mock/foamDictionary"), \
                 patch.object(engine.subprocess, "run",
                              return_value=types.SimpleNamespace(
                                  returncode=0, stdout="", stderr="")) as call:
                engine.materialize(
                    src, output, cfg, cfg_path, items,
                    {"native_volumes_m3_from_preserved_tsv":
                     {"metal": 1.0, "mold": 1.0}}
                )
                self.assertEqual(call.call_count, 10)
            self.assertEqual((output/"system/fvSolution").is_file(), True)
            report = json.loads((output/"T0_PREPARATION_REPORT.json").read_text())
            self.assertEqual(report["status"],
                             "T0_FILESET_MATERIALIZED_NATIVE_DICTIONARIES_PARSED_NOT_SOLVED")
            self.assertTrue(report["no_solver_executed"])
            self.assertEqual(len(report["native_foundation14_parsed_files"]), 10)
            for region in ("metal", "mold"):
                src_mesh = src/"constant"/region/"polyMesh"
                dst_mesh = output/"constant"/region/"polyMesh"
                for filename in ("points", "faces", "owner", "neighbour", "boundary"):
                    self.assertEqual((src_mesh/filename).read_bytes(),
                                     (dst_mesh/filename).read_bytes())
            with self.assertRaises(FileExistsError):
                engine.isolated_output(src, output)

    def test_06_no_CFD_or_remeshing_launched_by_integrated_runner(self):
        runner = (T0/"run_integrated_milestone.sh").read_text()
        self.assertIn("report_case_a_progress.py", runner)
        self.assertIn("prepare_case_a_t0.py", runner)
        self.assertNotIn("blockMesh -case", runner)
        self.assertNotIn("checkMesh -case", runner)
        self.assertNotIn("foamMultiRun -case", runner)
        self.assertNotIn("rm -rf", runner)
        self.assertIn("--preflight", runner)


if __name__ == "__main__":
    unittest.main()
