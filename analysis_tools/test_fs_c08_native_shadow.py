"""Independent verifier + safe runner contract for nonzero-Gamma native FV shadow.

All logs/test fixtures are fabricated and labelled synthetic; this test does
NOT establish OpenFOAM14 wmake compilation or physical 3D shrinkage.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_fs_c08_native_shadow as run
import verify_fs_c08_native_shadow as v


def synthetic_stdout() -> str:
    rows = dict(
        cells=34368, internal_faces=124000, face_index=0,
        owner=12, neighbour=33, dt_s=0.05,
        GammaOwner_kg_m3_s=200, GammaNeighbour_kg_m3_s=-50,
        flowL_kg_s=1e-5, flowS_kg_s=5e-7, flowG_kg_s=1e-9,
        initial_metal_kg=0.042, final_metal_kg=0.042,
        initial_gas_kg=0.000001, final_gas_kg=0.000001,
        initial_enthalpy_J=38640.84, final_enthalpy_J=38640.84,
        gamma_transferred_kg=0.0000003,
        delta_metal_volume_m3=-3e-10,
        metal_mass_residual_kg=0,gas_mass_residual_kg=0,
        enthalpy_residual_J=0, owner_T_final_K=1501,
        neighbour_T_final_K=1459
    )
    flags = dict(
        synthetic_only=1,nonzero_gamma=1,
        native_fvmesh_owner_neighbour=1,three_phase_internal_flux=1,
        closed_domain_no_boundary_flux=1,original_fields_written=0,
        OpenFOAM_CFD_pressure_solved=0,OpenFOAM_CFD_velocity_solved=0,
        physical_3d_shrinkage_validated=0
    )
    return (
        "OpenFOAM Foundation14 synthetic fixture mocked test\n"
        + v.MARKER
        + " ".join(f"{key}={val}" for key,val in rows.items()) + "\n"
        + v.FOOTER
        + " ".join(f"{key}={val}" for key,val in flags.items()) + "\n"
    )


class ShadowNativeOutputTests(unittest.TestCase):
    def test_complete_nonzero_gamma_three_phase_and_energy_fixture(self):
        report=v.verify_shadow_stdout(synthetic_stdout())
        self.assertEqual(report["status"],"PASS")
        self.assertEqual(report["mesh_cells"],34368)
        self.assertEqual(report["nonzero_source_gamma_owner_kg_m3_s"],200)
        self.assertEqual(report["nonzero_source_gamma_neighbour_kg_m3_s"],-50)
        self.assertEqual(report["net_liquid_to_solid_kg"],3e-7)
        self.assertFalse(report["physical_shrinkage_validated"])
        self.assertFalse(report["pressure_velocity_free_surface_solved"])

    def test_rejects_conservation_residual_even_if_footer_says_pass(self):
        bad=synthetic_stdout().replace(
            "final_metal_kg=0.042", "final_metal_kg=0.05"
        )
        with self.assertRaisesRegex(ValueError,"metal global conservation"):
            v.verify_shadow_stdout(bad)

    def test_local_nonzero_gamma_can_have_zero_net_transfer(self):
        # Volume-weighted melting and solidification can cancel globally.
        text=synthetic_stdout().replace(
            "gamma_transferred_kg=3e-07",
            "gamma_transferred_kg=0"
        )
        self.assertEqual(v.verify_shadow_stdout(text)["status"],"PASS")

    def test_rejects_unphysical_missing_gamma(self):
        bad=synthetic_stdout().replace("GammaOwner_kg_m3_s=200",
                                       "GammaOwner_kg_m3_s=0")
        with self.assertRaisesRegex(ValueError,"opposite-sign"):
            v.verify_shadow_stdout(bad)

    def test_rejects_fake_cfd_or_field_write_and_missing_footer(self):
        with self.assertRaisesRegex(ValueError,"footer"):
            v.verify_shadow_stdout(synthetic_stdout().split(v.FOOTER)[0])
        bad=synthetic_stdout().replace("original_fields_written=0",
                                       "original_fields_written=1")
        with self.assertRaisesRegex(ValueError,"original_fields_written"):
            v.verify_shadow_stdout(bad)
        bad=synthetic_stdout().replace("OpenFOAM_CFD_pressure_solved=0",
                                       "OpenFOAM_CFD_pressure_solved=1")
        with self.assertRaisesRegex(ValueError,"pressure_solved"):
            v.verify_shadow_stdout(bad)

    def test_rejects_fake_mesh_and_duplicate_rows(self):
        with self.assertRaisesRegex(ValueError,"mesh cell count"):
            v.verify_shadow_stdout(
                synthetic_stdout().replace("cells=34368","cells=12000")
            )
        text=synthetic_stdout()
        first=[line for line in text.splitlines()
               if line.startswith(v.MARKER)][0]
        with self.assertRaisesRegex(ValueError,"Exactly one"):
            v.verify_shadow_stdout(text+first+"\n")

    def test_new_native_cpp_and_wmake_source_contract(self):
        native=run.NATIVE
        cpp=(native/"fsC08NativeShadowStep.C").read_text(encoding="utf-8")
        opts=(native/"Make/options").read_text(encoding="utf-8")
        mk=(native/"Make/files").read_text(encoding="utf-8")
        header=(run.ROOT/"freesurface/FS-C08_conservative_phase_mass/native_cpp/"
                "ConservativePhaseNetwork.H").read_text(encoding="utf-8")
        fixture=run.FIXTURE.read_text(encoding="utf-8")
        self.assertIn("mesh.owner()[facei]",cpp)
        self.assertIn("mesh.neighbour()[facei]",cpp)
        self.assertIn("mesh.V()",cpp)
        self.assertIn("advanceNetwork(cells,thermo,step)",cpp)
        self.assertIn('#include "IOmanip.H"',cpp)
        self.assertIn("GammaOwner_kg_m3_s",cpp)
        self.assertIn("IOobject::NO_WRITE",cpp)
        self.assertIn("-std=c++17",opts)
        self.assertIn("fsC08NativeShadowStep.C",mk)
        self.assertIn("phaseSpecificEnthalpy",header)
        self.assertIn("ConservativePhaseExchange.H",header)
        self.assertIn("materialProvenance SYNTHETIC_ONLY_NOT_JMATPRO",fixture)
        self.assertNotIn("foamMultiRun(",cpp)
        self.assertNotIn("runTime.write(",cpp)


class ShadowRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c08-shadow-tests-")
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.case=self.base/"FS_C07_THERMAL_fake_source"
        (self.case/"constant/fluid/polyMesh").mkdir(parents=True)
        (self.case/"constant/fluid/polyMesh/points").write_text("synthetic")
        for t in ("0.2","0.4","1"):
            folder=self.case/t/"fluid"
            folder.mkdir(parents=True)
            for field in ("alpha.metal","alpha.metal.solid"):
                (folder/field).write_text("native synthetic mock "+field+t)
        self.bin=self.base/"bin"
        self.bin.mkdir()
        (self.bin/"fsC08NativeShadowStep").write_text("mock binary")
        self.native=self.base/"shadow_source"
        (self.native/"Make").mkdir(parents=True)
        (self.native/"Make/files").write_text("mock make files")
        (self.native/"Make/options").write_text("mock options")
        self.fixture=self.native/"SYNTHETIC_ONLY_NOT_JMATPRO.dict"
        self.fixture.write_text(
            "materialProvenance SYNTHETIC_ONLY_NOT_JMATPRO;\n"
        )

    def fake_commands(self, argv, cwd, timeout_seconds, log):
        log.write_text(
            "simulated successful compiler\n" if argv==["wmake"]
            else synthetic_stdout()
        )

    def patches(self):
        return (
            patch.object(run,"NATIVE",self.native),
            patch.object(run,"FIXTURE",self.fixture),
            patch.object(run.shutil,"which",return_value="/mock/wmake"),
            patch.object(run,"execute_checked",side_effect=self.fake_commands),
            patch.dict(os.environ,{
                "WM_PROJECT_VERSION":"14","FOAM_USER_APPBIN":str(self.bin)
            })
        )

    def test_mocked_success_proves_sha_preservation_contract(self):
        from contextlib import ExitStack
        with ExitStack() as stack:
            for p in self.patches(): stack.enter_context(p)
            report=run.run(self.case,self.base/"diagnostics")
        self.assertEqual(report["status"],run.EXPECTED_STATUS)
        self.assertTrue(report["wmake_compiled"])
        self.assertTrue(report["conservation_and_native_mesh_gate_pass"])
        self.assertFalse(report["source_changed"])
        self.assertEqual(report["original_fields_SHA256_before"],
                         report["original_fields_SHA256_after"])
        self.assertFalse(report["pressure_CFD_solved"])
        self.assertFalse(report["physical_3d_shrinkage_validated"])
        self.assertEqual(len(report["original_fields_SHA256_before"]),6)

    def test_mutation_detection_takes_priority_over_fake_pass(self):
        from contextlib import ExitStack
        def fake_mutation(argv,cwd,timeout_seconds,log):
            self.fake_commands(argv,cwd,timeout_seconds,log)
            if argv!=["wmake"]:
                (self.case/"0.4/fluid/alpha.metal").write_text("altered")
        with ExitStack() as stack:
            for p in self.patches(): stack.enter_context(p)
            stack.enter_context(patch.object(
                run,"execute_checked",side_effect=fake_mutation
            ))
            report=run.run(self.case,self.base/"diagnostics")
        self.assertEqual(
            report["status"],"FS_C08_NATIVE_GAMMA_SHADOW_SOURCE_CHANGED_CRITICAL"
        )

    def test_reject_non_synthetic_provenance_without_build(self):
        from contextlib import ExitStack
        self.fixture.write_text("materialProvenance REAL_CAST_IRON;\n")
        with ExitStack() as stack:
            for p in self.patches(): stack.enter_context(p)
            with self.assertRaisesRegex(ValueError,"synthetic provenance"):
                run.run(self.case,self.base/"diagnostics")


if __name__=="__main__":
    unittest.main()
