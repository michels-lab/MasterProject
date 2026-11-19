#!/usr/bin/env python3
"""Static and synthetic integrated tests only: never run OpenFOAM or claim material validity."""
import importlib.util
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock

T0 = Path(__file__).resolve().parents[1]
SCRIPT = T0 / "scripts/run_t0_granada.py"
spec = importlib.util.spec_from_file_location("t0_granada_runner", SCRIPT)
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)


def synthetic_inputs():
    cfg = json.loads((T0 / "T0_INPUTS.json").read_text(encoding="utf-8"))
    for region, temperature in (("metal", 900), ("mold", 300)):
        cfg[region].update({
            "rho_kg_m3": 6500, "Cv_J_kg_K": 600, "kappa_W_m_K": 20,
            "molWeight_g_mol": 50, "T_initial_K": temperature,
            "source_rho": "UNIT TEST LAB FIXTURE",
            "source_Cv": "UNIT TEST LAB FIXTURE",
            "source_kappa": "UNIT TEST LAB FIXTURE",
            "source_molWeight": "UNIT TEST LAB FIXTURE",
            "source_T_initial": "UNIT TEST LAB FIXTURE",
        })
    cfg["simulation"].update({
        "deltaT_s": 0.01, "endTime_s": 0.1, "writeEverySteps": 2,
        "source_time_choices": "UNIT TEST LAB FIXTURE",
    })
    return cfg


class T0GranadaIntegration(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.inputs = self.work / "inputs.json"
        self.source = self.work / "C3D05_STEP_GMSH_HEX_SUBDIV_COARSE_02"
        self.output = self.work / "C3D05_T0_CONDUCTION_01"

    def write_inputs(self, values):
        self.inputs.write_text(json.dumps(values), encoding="utf-8")

    def fake_source(self):
        for region in ("metal", "mold"):
            poly = self.source / "constant" / region / "polyMesh"
            poly.mkdir(parents=True)
            for file in ("points", "faces", "owner", "neighbour", "boundary"):
                (poly / file).write_text("FAKE ONLY FOR TEST", encoding="utf-8")
        for file in ("STEP_CAD_AUDIT.json", "CONTACT_AREA_REPORT.json", "NATIVE_BUILD_STATUS.txt"):
            (self.source / file).write_text("TEST ONLY", encoding="utf-8")
        for file in ("log.checkMesh.parent", "log.checkMesh.metal", "log.checkMesh.mold"):
            (self.source / file).write_text("SYNTHETIC LOG ONLY", encoding="utf-8")

    def test_missing_physical_inputs_fail_before_mesh_or_wsl(self):
        self.write_inputs(json.loads((T0 / "T0_INPUTS.json").read_text()))
        with mock.patch.object(target, "source_review", side_effect=AssertionError("must not assess mesh")):
            self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 3)
        self.assertFalse(self.output.exists())

    def test_bad_provenance_cannot_materialize(self):
        data = synthetic_inputs()
        data["metal"]["source_Cv"] = "SYNTHETIC_UNIT_TEST"
        self.write_inputs(data)
        self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 3)

    def test_valid_inputs_missing_foundation14_preserve_source_and_output(self):
        self.write_inputs(synthetic_inputs())
        with mock.patch.dict(os.environ, {"WM_PROJECT_VERSION": "13"}):
            self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 4)
        self.assertFalse(self.output.exists())

    def test_unknown_existing_output_is_never_overwritten(self):
        self.write_inputs(synthetic_inputs())
        self.output.mkdir()
        (self.output / "user-data.txt").write_text("KEEP ME")
        self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 2)
        self.assertEqual((self.output / "user-data.txt").read_text(), "KEEP ME")

    def test_integrated_synthetic_materialize_and_idempotence(self):
        self.fake_source()
        self.write_inputs(synthetic_inputs())
        binary_dir = self.work / "bin"
        binary_dir.mkdir()
        for binary in ("foamDictionary", "foamMultiRun"):
            path = binary_dir / binary
            path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            path.chmod(0o755)
        env = {"WM_PROJECT_VERSION": "14", "PATH": str(binary_dir) + os.pathsep + os.environ.get("PATH", "")}
        evidence = {"geometry_topology_gate_passed": True, "source": "SYNTHETIC_FIXTURE_ONLY",
                    "high_nonorthogonality_warning": True}
        with mock.patch.dict(os.environ, env), mock.patch.object(target, "source_review", return_value=evidence) as review:
            self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 0)
            self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 0)
            self.assertEqual(review.call_count, 1)
        report = json.loads((self.output / "T0_GRANADA_REPORT.json").read_text())
        self.assertEqual(report["status"], target.STAGE)
        self.assertEqual(len(report["parsed_dictionaries"]), 10)
        self.assertFalse(report["cfd_executed"])
        self.assertEqual(len(report["source_fingerprint_sha256"]), 64)
        prep = json.loads((self.output / "T0_PREPARATION_REPORT.json").read_text())
        self.assertEqual(prep["output"], str(self.output))
        self.assertTrue(prep["staging_finalized_into_output"])
        self.assertTrue((self.output / "constant/metal/polyMesh/points").is_file())
        self.assertFalse((self.output / "constant/metal/polyMesh").is_symlink())
        self.assertFalse((self.output.with_name(self.output.name + ".granada.lock")).exists())
        self.assertFalse(list(self.work.glob("*.granada-staging-*")))
        (self.source / "constant/metal/polyMesh/points").write_text("SOURCE MODIFIED AFTER ACCEPTED RUN")
        self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 2)
        self.assertTrue((self.output / "T0_GRANADA_REPORT.json").is_file())

    def test_changed_inputs_cannot_reuse_prepared_output(self):
        self.fake_source()
        self.write_inputs(synthetic_inputs())
        binary_dir = self.work / "bin"
        binary_dir.mkdir()
        for binary in ("foamDictionary", "foamMultiRun"):
            path = binary_dir / binary
            path.write_text("#!/bin/sh\nexit 0\n")
            path.chmod(0o755)
        with mock.patch.dict(os.environ, {"WM_PROJECT_VERSION":"14","PATH":str(binary_dir)+os.pathsep+os.environ.get("PATH","")}), mock.patch.object(target, "source_review", return_value={"geometry_topology_gate_passed":True}):
            self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 0)
            c=synthetic_inputs()
            c["metal"]["Cv_J_kg_K"]=700
            self.write_inputs(c)
            self.assertEqual(target.pipeline(self.inputs, self.source, self.output), 2)
            self.assertEqual(json.loads((self.output/"T0_PREPARATION_REPORT.json").read_text())["temperature_and_material_sources"]["metal"]["Cv_J_kg_K"],600)


if __name__ == "__main__":
    main()
