#!/usr/bin/env python3
"""One integrated static regression suite for CASE A T0; never calls OpenFOAM."""
import copy
import importlib.util
import json
import pathlib
import shutil
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
import native_f14_dictionary_smoke as native_f14
import native_f14_coupled_runtime_smoke as native_runtime
sys.path.insert(0, str(CASE_A / "c14_physics"))
import c14_source_fidelity as c14_exact
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

    def test_03_all_ten_thermal_dictionaries_generated_from_synthetic_fixture(self):
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
        self.assertIn("nOuterCorrectors 3;", items["system/fvSolution"])
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
            self.assertEqual(
                field.count("type externalTemperature;"),
                len(engine.EXTERIOR[region])
            )
            for patch in engine.EXTERIOR[region] + (engine.COUPLED[region],):
                self.assertIn(patch + "\n", field)
        for region in ("metal", "mold"):
            field = items[f"0/{region}/T"]
            self.assertNotIn("externalWallHeatFluxTemperature", field)
            self.assertNotIn("kappaMethod solidThermo", field)
            self.assertNotIn("mode coefficient", field)
            self.assertIn("h uniform 10;", field)
            # Native Foundation14 reads h as a patch field, Ta as a Function1.
            self.assertNotIn("h constant ", field)
            self.assertIn("Ta constant 300;", field)
        self.assertIn("thicknessLayers (0.0002);", items["0/metal/T"])
        self.assertIn("kappaLayers (0.1);", items["0/metal/T"])
        self.assertIn("emissivity 0.3;", items["0/metal/T"])
        self.assertIn("emissivity 0.5;", items["0/mold/T"])
        self.assertNotIn("moldOuterUnclassified", items["0/mold/T"])
        self.assertNotIn("type patch;", items["0/metal/T"])

    def test_044_real_original_C14_source_parity_and_negative_regression(self):
        raw = json.loads(engine.INPUTS.read_text(encoding="utf-8"))
        evidence = engine.c14_source_gate(raw)
        self.assertEqual(evidence["verified_scalar_comparisons"], 27)
        self.assertTrue(
            evidence["Cp_as_Cv_surrogate_explicit_not_original_C14_thermo"]
        )
        changed = copy.deepcopy(raw)
        changed["metal"]["Cp_C14_J_kg_K"] = 828
        with self.assertRaises(ValueError):
            engine.c14_source_gate(changed)
        changed = copy.deepcopy(raw)
        changed["c14_boundary_reference"]["metal_to_mold"]["layer_thickness_m"] = .001
        with self.assertRaises(ValueError):
            engine.c14_source_gate(changed)
        changed = copy.deepcopy(raw)
        changed["simulation"]["deltaT_s"] = .005
        with self.assertRaises(ValueError):
            engine.c14_source_gate(changed)
        # Independent drift in the archived C14 executable file must also
        # fail, even when all input numbers remain unmodified.
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)/"archived_C14"
            baseline = json.loads(
                (engine.T0/"C14_PARAMETER_BASELINE.json").read_text()
            )
            for row in baseline["source_details"]:
                dest = root/row["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(engine.C14_ROOT/row["path"], dest)
            changed_source = root/"constant/metal/materials/castIron"
            changed_source.write_bytes(changed_source.read_bytes() + b"\n")
            with patch.object(engine, "C14_ROOT", root):
                with self.assertRaisesRegex(ValueError, "Original C14 source changed"):
                    engine.c14_source_gate(raw)

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
                             "COUNTERFACTUAL_INSULATED_LIMIT_NOT_T0_WITH_C14_CONVECTIVE_BOUNDARIES")
            report.write_text(report.read_text().replace("YES", "NO", 1))
            with self.assertRaises(ValueError):
                engine.read_preserved_mesh_volumes(root)

    def test_046b_native_volume_without_optional_tsv_and_orientation_rejection(self):
        # Closed cube, all faces oriented outward as FOAM boundary owner faces.
        vertices = [
            (0,0,0), (1,0,0), (1,1,0), (0,1,0),
            (0,0,1), (1,0,1), (1,1,1), (0,1,1),
        ]
        polygons = [
            [0,3,2,1], [4,5,6,7],
            [0,4,7,3], [1,2,6,5],
            [0,1,5,4], [3,7,6,2],
        ]
        self.assertAlmostEqual(
            engine.oriented_boundary_volume(vertices, polygons, 0), 1.0
        )
        with self.assertRaisesRegex(ValueError, "positive"):
            engine.oriented_boundary_volume(
                vertices, [list(reversed(f)) for f in polygons], 0
            )
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            # No PILOT_MESH_REPORT.tsv anywhere: exercise actual fallback.
            for region, edge in (("metal", 1), ("mold", 2)):
                mesh = root/"constant"/region/"polyMesh"
                mesh.mkdir(parents=True)
                coords = "\n".join(
                    f"({edge*x} {edge*y} {edge*z})"
                    for x,y,z in vertices
                )
                fs = "\n".join(
                    str(len(face))+"("+" ".join(map(str, face))+")"
                    for face in polygons
                )
                (mesh/"points").write_text(
                    "FoamFile { class vectorField; }\n8\n(\n"+coords+"\n)\n"
                )
                (mesh/"faces").write_text(
                    "FoamFile { class faceList; }\n6\n(\n"+fs+"\n)\n"
                )
                (mesh/"neighbour").write_text(
                    "FoamFile { class labelList; }\n0\n(\n)\n"
                )
            found = engine.read_preserved_mesh_volumes(root)
            self.assertAlmostEqual(found["metal"], 1.0)
            self.assertAlmostEqual(found["mold"], 8.0)

    def test_047_C14_convection_and_contact_budget_on_native_area_fixture(self):
        cfg = json.loads(engine.INPUTS.read_text(encoding="utf-8"))
        self.assertEqual(engine.validate(cfg), [])
        areas = {
            ("metal", "metalTop"): (0.001326, 256),
            ("metal", "metal_to_mold"): (0.006343771874, 2496),
            ("mold", "mold_to_metal"): (0.006343771874, 2496),
            ("mold", "moldTop"): (0.001, 128),
            ("mold", "moldExterior"): (0.005, 512),
            ("mold", "moldBottom"): (0.001, 128),
            ("mold", "moldRecessWall"): (0.002, 128),
            ("mold", "moldRecessRoof"): (0.001, 128),
        }
        volumes = {"metal": 4.798e-5, "mold": 1.0284e-4}
        with patch.object(engine, "patch_area",
                          side_effect=lambda _case, region, name:
                          areas[(region, name)]):
            budget = engine.thermal_network_budget(
                pathlib.Path("/not-a-real-mesh"), cfg, volumes
            )
        self.assertEqual(budget["status"],
                         "INITIAL_C14_BC_GEOMETRIC_POWER_SCALE_NOT_CFD")
        self.assertEqual(budget["native_contact_faces_each_side"], 2496)
        powers = budget["initial_uniform_temperature_power_W_positive_outward"]
        self.assertAlmostEqual(
            powers["metal_to_mold_contact"],
            500 * 0.006343771874 * (1500-300), places=7
        )
        self.assertAlmostEqual(
            powers["metal_to_ambient_convection"],
            10 * 0.001326 * (1500-300), places=7
        )
        self.assertEqual(powers["mold_to_ambient_convection"], 0.0)
        self.assertGreater(powers["metal_to_ambient_radiation_estimate"], 0)
        self.assertTrue(all(x > 0 for x in
                            budget["contact_only_lumped_time_scale_s"].values()))
        altered = dict(areas)
        altered[("mold", "mold_to_metal")] = (0.00634, 2496)
        with patch.object(engine, "patch_area",
                          side_effect=lambda _case, region, name:
                          altered[(region, name)]):
            with self.assertRaises(ValueError):
                engine.thermal_network_budget(
                    pathlib.Path("/not-a-real-mesh"), cfg, volumes
                )

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
                     {"metal": 1.0, "mold": 1.0},
                     "initial_C14_BC_thermal_budget": {
                         "status": "INITIAL_C14_BC_GEOMETRIC_POWER_SCALE_NOT_CFD",
                         "native_contact_faces_each_side": 2496,
                         "verified_fixture_only": True,
                     }}
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
                     {"metal": 1.0, "mold": 1.0},
                     "initial_C14_BC_thermal_budget": {
                         "status": "INITIAL_C14_BC_GEOMETRIC_POWER_SCALE_NOT_CFD",
                         "native_contact_faces_each_side": 2496,
                         "verified_fixture_only": True,
                     }}
                )
                self.assertEqual(call.call_count, 10)
            self.assertEqual((output/"system/fvSolution").is_file(), True)
            report = json.loads((output/"T0_PREPARATION_REPORT.json").read_text())
            self.assertEqual(report["status"],
                             "T0_FILESET_MATERIALIZED_NATIVE_DICTIONARIES_PARSED_NOT_SOLVED")
            self.assertTrue(report["no_solver_executed"])
            self.assertEqual(
                report["initial_C14_BC_thermal_budget"]
                ["native_contact_faces_each_side"], 2496
            )
            self.assertEqual(len(report["native_foundation14_parsed_files"]), 10)
            for region in ("metal", "mold"):
                src_mesh = src/"constant"/region/"polyMesh"
                dst_mesh = output/"constant"/region/"polyMesh"
                for filename in ("points", "faces", "owner", "neighbour", "boundary"):
                    self.assertEqual((src_mesh/filename).read_bytes(),
                                     (dst_mesh/filename).read_bytes())
            with self.assertRaises(FileExistsError):
                engine.isolated_output(src, output)

    def test_055b_reject_missing_verified_thermal_budget_before_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            source = root/"accepted"
            source.mkdir()
            destination = root/"refused_output"
            with self.assertRaisesRegex(ValueError, "prior, successful integrated"):
                engine.materialize(
                    source, destination, engine.synthetic_fixture(),
                    engine.INPUTS, {}, {"native_volumes_m3_from_preserved_tsv":
                                       {"metal": 1.0, "mold": 1.0}}
                )
            self.assertFalse(destination.exists())

    def test_056_integrated_preflight_never_reports_success_on_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = pathlib.Path(folder)
            config = json.loads(engine.INPUTS.read_text(encoding="utf-8"))
            config["metal"]["rho_kg_m3"] = None
            config_path = directory/"invalid_inputs.json"
            config_path.write_text(json.dumps(config))
            source = directory/"accepted_V4_T02"
            source.mkdir()
            out = directory/"never_created"
            args = [
                "prepare_case_a_t0.py", "--inputs", str(config_path),
                "--source", str(source), "--out", str(out),
            ]
            with patch.object(engine.sys, "argv", args), \
                 patch.object(engine, "native_case_gate", side_effect=AssertionError(
                     "Invalid configuration must be rejected before touching native mesh"
                 )), \
                 patch.object(engine, "materialize", side_effect=AssertionError(
                     "A failed preflight must never materialize a case"
                 )):
                self.assertEqual(engine.main(), 3)
            self.assertFalse(out.exists())

    def test_057_integrated_valid_C14_preflight_no_writes_or_CFD(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = pathlib.Path(folder)
            source = directory/"accepted_V4_T02"
            source.mkdir()
            out = directory/"never_created"
            args = [
                "prepare_case_a_t0.py",
                "--inputs", str(engine.INPUTS),
                "--source", str(source),
                "--out", str(out),
            ]
            native = {
                "native_volumes_m3_from_preserved_tsv": {
                    "metal": 4.79e-5, "mold": 1.028e-4,
                }
            }
            budget = {
                "initial_uniform_temperature_power_W_positive_outward": {
                    "metal_to_mold_contact": 3806.0,
                    "metal_to_ambient_convection": 15.9,
                }
            }
            with patch.object(engine.sys, "argv", args), \
                 patch.object(engine, "native_case_gate", return_value=native), \
                 patch.object(engine, "thermal_network_budget", return_value=budget), \
                 patch.object(engine, "materialize", side_effect=AssertionError(
                     "Preflight must never materialize a case"
                 )):
                self.assertEqual(engine.main(), 0)
            self.assertFalse(out.exists())

    def test_058_F14_native_smoke_orchestration_all_ten_and_bad_version(self):
        import types
        good = types.SimpleNamespace(returncode=0, stdout="", stderr="")
        called = []
        def fake_run(cmd, **kwargs):
            called.append(cmd)
            return good
        with patch.dict(native_f14.os.environ, {"WM_PROJECT_VERSION": "14"}), \
             patch.object(native_f14.shutil, "which", side_effect=lambda x: "/mock/"+x), \
             patch.object(native_f14.subprocess, "run", side_effect=fake_run):
            report = native_f14.inspect()
        self.assertEqual(report["status"],
                         "NATIVE_F14_DICTIONARY_SYNTAX_PASS_NOT_CFD")
        self.assertFalse(report["CFD_executed"])
        self.assertFalse(report["native_C3D04_V4_T02_mesh_present_in_CI"])
        self.assertEqual(len(report["dictionary_results"]), 10)
        self.assertEqual(len(called), 10)
        self.assertTrue(all(row["parsed_with_Foundation14_foamDictionary"]
                            for row in report["dictionary_results"]))
        with patch.dict(native_f14.os.environ, {"WM_PROJECT_VERSION": "13"}):
            with self.assertRaisesRegex(RuntimeError, "Expected sourced Foundation14"):
                native_f14.inspect()
        with patch.dict(native_f14.os.environ, {"WM_PROJECT_VERSION": "14"}), \
             patch.object(native_f14.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "missing foamDictionary"):
                native_f14.inspect()

    def test_059_builtin_selftest_is_exercised_by_integrated_CI(self):
        # Prevent legacy F13 temperature BC assertions from silently
        # drifting after edits to the Foundation14 T0 dictionary generator.
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as output:
            engine.self_test()
        self.assertIn("STATIC_INTEGRATED_T0_PASS", output.getvalue())
        cfg = engine.synthetic_fixture()
        files = engine.generate(cfg)
        for region in ("metal", "mold"):
            field = files[f"0/{region}/T"]
            self.assertEqual(field.count("type externalTemperature;"),
                             len(engine.EXTERIOR[region]))
            self.assertNotIn("externalWallHeatFluxTemperature", field)

    def test_059b_native_f14_two_cube_case_a_runtime_contract(self):
        # This is the only synthetic mesh; production V4/T02 remains untouched.
        metal = native_runtime.block_mesh_dict("metal")
        mold = native_runtime.block_mesh_dict("mold")
        self.assertIn("type mappedWall;", metal)
        self.assertIn("type mappedWall;", mold)
        self.assertIn("neighbourRegion mold;", metal)
        self.assertIn("neighbourRegion metal;", mold)
        self.assertIn("neighbourPatch mold_to_metal;", metal)
        self.assertIn("neighbourPatch metal_to_mold;", mold)
        self.assertIn("method matching;", metal)
        self.assertIn("method matching;", mold)
        self.assertNotIn("sampleMode nearestPatchFace;", metal + mold)
        self.assertNotIn("sampleRegion", metal + mold)
        self.assertEqual(metal.count("type mappedWall;"), 1)
        self.assertEqual(mold.count("type mappedWall;"), 1)
        self.assertEqual(metal.count("type wall;"), 1)
        self.assertEqual(mold.count("type wall;"), 5)
        self.assertIn("scale 0.01;", metal)
        self.assertIn("scale 0.01;", mold)
        # All six faces per region, and a single mirrored interface.
        self.assertEqual(sum(metal.count(face) for face in native_runtime.FACES.values()), 6)
        self.assertEqual(sum(mold.count(face) for face in native_runtime.FACES.values()), 6)
        for patch in engine.EXTERIOR["mold"]:
            self.assertIn(patch + "\n", mold)
        with self.assertRaises(ValueError):
            native_runtime.block_mesh_dict("Case_B")

        real = json.loads(engine.INPUTS.read_text(encoding="utf-8"))
        source = engine.generate(real)["system/controlDict"]
        short = native_runtime.shorten_for_runtime(source)
        self.assertIn("endTime 0.002;", short)
        self.assertIn("writeInterval 1;", short)
        self.assertIn("deltaT 0.001;", short)
        self.assertIn("regionSolvers", short)
        self.assertIn("endTime 10;", source)
        with self.assertRaises(ValueError):
            native_runtime.shorten_for_runtime(short)

    def test_059c_synthetic_native_smoke_fail_closed_without_f14(self):
        with patch.dict(native_runtime.os.environ, {"WM_PROJECT_VERSION": "13"}), \
             patch.object(native_runtime.shutil, "which", return_value=None):
            with tempfile.TemporaryDirectory() as directory:
                out = pathlib.Path(directory)/"never_created"
                with self.assertRaises(RuntimeError):
                    native_runtime.run(out)
                self.assertFalse(out.exists())
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory)/"already_present"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                native_runtime.run(target)

    def test_060_case_a_C14_metal_fluid_enthalpy_all_original_values(self):
        # Critical regression: a two-solid T0 is NOT the C14 research model.
        report = c14_exact.verify()
        self.assertEqual(report["regionSolvers"], {"metal": "fluid", "mold": "solid"})
        self.assertTrue(report["C14_momentum_and_energy_retained"])
        self.assertFalse(report["3D_solver_executed"])
        fileset = c14_exact.assemble_unmaterialized_source_exact_fileset()
        manifest = c14_exact.sources_manifest()
        self.assertEqual(len(fileset), 22)
        self.assertEqual(manifest["files_total"], 22)
        self.assertFalse(manifest["native_solver_run"])
        self.assertFalse(manifest["native_pressure_reference_point_mapped"])
        self.assertFalse(manifest["native_phaseChange_metal_cellZone_mapped"])
        self.assertIn("metal       fluid;", fileset["system/controlDict"])
        self.assertIn("mold        solid;", fileset["system/controlDict"])
        self.assertIn("solidificationMeltingSource;",
                      fileset["constant/metal/fvModels"])
        self.assertIn("alpha1e         0.8;",
                      fileset["constant/metal/fvModels"])
        self.assertIn("heRhoThermo;",
                      fileset["constant/metal/materials/castIron"])
        self.assertIn("sensibleEnthalpy;",
                      fileset["constant/metal/materials/castIron"])
        fields = c14_exact.generate_3d_initial_fields()
        self.assertEqual(len(fields), 8)
        self.assertIn("type externalTemperature;", fields["0/metal/T"])
        self.assertIn("h uniform 10;", fields["0/metal/T"])
        self.assertIn("Ta constant 300;", fields["0/metal/T"])
        self.assertIn("type coupledTemperature;", fields["0/mold/T"])
        self.assertIn("type slip;", fields["0/metal/U"])
        self.assertIn("type noSlip;", fields["0/metal/U"])
        self.assertIn("type fixedFluxPressure;", fields["0/metal/p_rgh"])
        self.assertIn("internalField uniform 228600;", fields["0/metal/latentHeat"])
        self.assertTrue(all("frontAndBack" not in body for body in fields.values()))
        for value in ("alpha1e", "beta", "Tsol", "Tliq", "rhoRef", "Cu", "relax"):
            self.assertIn(value, c14_exact.read_original("constant/metal/fvModels"))
        contract = json.loads(c14_exact.CONTRACT.read_text())
        self.assertEqual(contract["non_negotiable"]["metal_energy"],
                         "sensibleEnthalpy")
        self.assertTrue(contract["non_negotiable"]["forbid_metal_Cp_as_Cv"])
        self.assertEqual(contract["C14_exact_values"]["numerics"]
                         ["metal_region_nEnergyCorrectors_effective"], 1)

    def test_061_case_a_C14_source_parity_rejects_silent_material_mutations(self):
        original = c14_exact.read_original
        variants = (
            ("constant/metal/materials/castIron", "Cp          827;", "Cp          900;"),
            ("constant/mold/materials/silica", "Cv      700;", "Cv      900;"),
            ("constant/metal/fvModels", "alpha1e         0.8;", "alpha1e         0.9;"),
            ("constant/metal/momentumTransport", "simulationType laminar;", "simulationType RAS;"),
            ("constant/metal/g", "value           (0 -9.81 0);", "value           (0 0 -9.81);"),
            ("system/controlDict", "metal       fluid;", "metal       solid;"),
        )
        for relative, old, replacement in variants:
            with self.subTest(relative=relative):
                raw = original(relative)
                self.assertIn(old, raw)
                def contaminated(path, relative=relative, old=old, replacement=replacement):
                    text = original(path)
                    return text.replace(old, replacement) if path == relative else text
                with patch.object(c14_exact, "read_original", side_effect=contaminated):
                    with self.assertRaisesRegex(ValueError, "C14_SOURCE_FIDELITY_BLOCKED"):
                        c14_exact.verify()

    def test_06_no_CFD_or_remeshing_launched_by_integrated_runner(self):
        runner = (T0/"run_integrated_milestone.sh").read_text()
        self.assertIn("report_case_a_progress.py", runner)
        self.assertIn("prepare_case_a_t0.py", runner)
        self.assertNotIn("blockMesh -case", runner)
        self.assertNotIn("checkMesh -case", runner)
        self.assertNotIn("foamMultiRun -case", runner)
        self.assertNotIn("rm -rf", runner)
        self.assertIn("--preflight", runner)
        self.assertIn('HWLOC_COMPONENTS=-gl', runner)
        self.assertIn('ubuntu_version" == "26.04"', runner)
        self.assertEqual(runner.count("source /opt/openfoam14/etc/bashrc"), 1)
        self.assertIn("load_openfoam14_once", runner)


if __name__ == "__main__":
    unittest.main()
