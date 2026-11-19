"""FS-C05 provisional compressibleVoF+solid CHT generator: NO CFD in tests.

Uses minimal synthetic OF14-tutorial files; real runtime must load installed
$FOAM_TUTORIALS and actual natively accepted FS-C04 T stage.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from stage_fs_c04_initial_alpha import make_alpha, ATMOSPHERE_PATCHES, MOLD_CONTACT_FACES
from stage_fs_c04_initial_temperature import create_T, FLUID_PATCHES, MOLD_PATCHES
from stage_fs_c05_vof_cht import (
    stage, control_dict, scalar_field, vector_field, REGION_FIELDS,
    ATMOSPHERES, CASE_PREFIX, ensure_compressible_kepsilon_divergence,
)


class CHTTemplateTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="fs-c05-cht-")
        self.addCleanup(t.cleanup)
        p=Path(t.name)
        self.source=p/"FS_C04_T_INITIAL_STAGE_synthetic"
        self.accept=p/"FS_C04_T_NATIVE_CHECK_synthetic"
        self.tutorial=p/"of14"/"multiRegion/CHT/VoFcoolingCylinder2D"
        self.out=p/(CASE_PREFIX+"synthetic")
        self.source.mkdir()
        self.accept.mkdir()
        self.tutorial.mkdir(parents=True)
        for name in ("points","faces","owner","neighbour","boundary"):
            for region in ("fluid","mold"):
                poly=self.source/"constant"/region/"polyMesh"
                poly.mkdir(parents=True,exist_ok=True)
                (poly/name).write_text("FoamFile {format ascii;}\n")
        (self.source/"system").mkdir()
        (self.source/"system/controlDict").write_text(
            "FoamFile {object controlDict;}\n")
        (self.source/"0/fluid").mkdir(parents=True)
        (self.source/"0/mold").mkdir(parents=True)
        bc={
            "fluid_to_mold":{
                "type":"mappedWall","nFaces":str(MOLD_CONTACT_FACES),
                "neighbourRegion":"mold","neighbourPatch":"mold_to_fluid"},
            **{p:{"type":"patch","nFaces":str(n)}
               for p,n in ATMOSPHERE_PATCHES.items()}
        }
        (self.source/"constant/fluid/polyMesh/boundary").write_text(
            "\n".join(name+"\n{\n"+"\n".join(
                "    "+k+" "+v+";" for k,v in data.items())+"\n}"
                for name,data in bc.items()))
        (self.source/"0/fluid/alpha.metal").write_text(
            make_alpha([1.]*2368+[0.]*32000,bc))
        tvals=[1500.]*2368+[300.]*32000
        (self.source/"0/fluid/T").write_text(create_T(tvals,"fluid",FLUID_PATCHES))
        (self.source/"0/mold/T").write_text(create_T(
            [300.]*7680,"mold",MOLD_PATCHES))
        (self.source/"FS_C04_INITIAL_T_SCREEN.json").write_text(
            '{"status":"INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT"}')
        self.record={
            "status":"INITIAL_T_STAGED_READBACK_NO_NATIVE_OR_CHT",
            "source_accepted_alpha_case":str(self.source),
            "source_thermal_interface_audit":{"status":"SYNTHETIC"},
        }
        (self.accept/"FS_C04_NATIVE_T_ACCEPTANCE.json").write_text(json.dumps({
            "status":"NATIVE_2_REGION_T_INTEGRALS_VERIFIED_NO_CHT",
            "source":str(self.source),
            "T_field_read_natively":True,
            "native_volume_integrals_verified":True,
            "CFD_or_CHT_executed":False,
            "native_postprocess":{f"{region}.{op}":{"status":"TEST"}
                for region in ("fluid","mold")
                for op in ("volAverage","volIntegrate")},
        }))
        files={
            "system/controlDict":(
                "regionSolvers\n{\n"
                "    fluid           compressibleVoF;\n"
                "    solid           solid;\n}\n"
                "endTime         5;\n"
                "deltaT          1e-4;\n"
                "writeControl    adjustableRunTime;\n"
                "writeInterval   0.1;\n"
                "runTimeModifiable true;\n"
                "maxCo           2;\n"
                "maxAlphaCo      1;\n"
                "maxDeltaT       1;\n"
                "writePrecision  8;\n"),
            "system/fvSolution":"PIMPLE {nOuterCorrectors 1; nEnergyCorrectors 2;}",
            "system/fluid/fvSchemes":(
                "divSchemes\n{\n"
                "    turbulence Gauss limitedLinear 1;\n"
                "    div(phi,k)         $turbulence;\n"
                "}\n"),
            "system/fluid/fvSolution":(
                'solvers {\n"alpha.water.*" {nCorrectors 2;}\n'
                '"(T|k|B|nuTilda).*" {solver PBiCGStab;}\n}\n'),
            "system/solid/fvSchemes":"ddtSchemes {default Euler;}",
            "system/solid/fvSolution":"solvers {e {solver PCG;}}",
            "constant/solid/physicalProperties":"thermoType constSolidThermo;",
        }
        for path,c in files.items():
            fp=self.tutorial/path
            fp.parent.mkdir(parents=True,exist_ok=True)
            fp.write_text(c)

    def mock_real_provenance(self):
        return (
            patch("stage_fs_c05_vof_cht.read_stage",
                  return_value=self.record),
            patch("stage_fs_c05_vof_cht.audit_contacts",
                  return_value=self.record["source_thermal_interface_audit"]),
            patch("stage_fs_c05_vof_cht.check_T",
                  side_effect=lambda p,region,alpha=None:{
                      "cells":34368 if region=="fluid" else 7680,
                  }),
        )

    def staged(self):
        a,b,c=self.mock_real_provenance()
        with a,b,c:
            return stage(self.source,self.accept,self.tutorial,self.out)

    def test_2region_multiphase_cht_and_actual_coupled_wall_screen_inputs(self):
        record=self.staged()
        self.assertEqual(record["status"],
                         "VOF_CHT_SOLVER_INPUTS_STAGED_UNTESTED_NO_CFD")
        self.assertEqual(record["regionSolvers"],
                         {"fluid":"compressibleVoF","mold":"solid"})
        self.assertFalse(record["solver_executed"])
        self.assertFalse(record["VOF_CHT_energy_balance_validated"])
        self.assertFalse(record["native_dictionary_validation_done"])
        self.assertTrue(record["do_not_execute_without_native_review"])
        self.assertIn("mold            solid;",
                      (self.out/"system/controlDict").read_text())
        self.assertIn("fluid           compressibleVoF;",
                      (self.out/"system/controlDict").read_text())
        self.assertIn("nEnergyCorrectors 2;",
                      (self.out/"system/fvSolution").read_text())
        self.assertIn("alpha.metal.*",
                      (self.out/"system/fluid/fvSolution").read_text())
        schemes=(self.out/"system/fluid/fvSchemes").read_text()
        self.assertIn("div(rhoPhi,k)",schemes)
        self.assertIn("div(rhoPhi,epsilon)",schemes)
        self.assertNotIn("div(phi,epsilon)",schemes)
        self.assertIn("type coupledTemperature;",
                      (self.out/"0/fluid/T").read_text())
        self.assertIn("type coupledTemperature;",
                      (self.out/"0/mold/T").read_text())
        self.assertIn("type inletOutlet;",
                      (self.out/"0/fluid/T").read_text())
        self.assertNotIn("type calculated;",
                         (self.out/"0/fluid/T").read_text())
        self.assertNotIn("type calculated;",
                         (self.out/"0/mold/T").read_text())

    def test_compressible_ras_rhoPhi_schemes_are_idempotent_and_safe(self):
        official=(self.tutorial/"system/fluid/fvSchemes").read_text()
        fixed,added=ensure_compressible_kepsilon_divergence(official)
        self.assertEqual(added,["k","epsilon"])
        self.assertEqual(fixed.count("div(rhoPhi,k)"),1)
        self.assertEqual(fixed.count("div(rhoPhi,epsilon)"),1)
        again,added_again=ensure_compressible_kepsilon_divergence(fixed)
        self.assertEqual(again,fixed)
        self.assertEqual(added_again,[])
        self.assertEqual(
            (self.tutorial/"system/fluid/fvSchemes").read_text(),official)

    def test_wrong_rhoPhi_epsilon_discretization_fails_closed(self):
        base=(self.tutorial/"system/fluid/fvSchemes").read_text()
        bad=base.replace(
            "div(phi,k)         $turbulence;",
            "div(phi,k)         $turbulence;\n"
            "    div(rhoPhi,epsilon) Gauss upwind;")
        with self.assertRaisesRegex(ValueError,"unexpected compressible"):
            ensure_compressible_kepsilon_divergence(bad)

    def test_retains_exact_native_alpha_and_initial_temperature_mask(self):
        source_alpha=(self.source/"0/fluid/alpha.metal").read_bytes()
        old_fluid_T=(self.source/"0/fluid/T").read_bytes()
        self.staged()
        self.assertEqual((self.out/"0/fluid/alpha.metal").read_bytes(),
                         source_alpha)
        self.assertEqual((self.source/"0/fluid/T").read_bytes(),old_fluid_T)
        self.assertIn("nonuniform List<scalar>",
                      (self.out/"0/fluid/T").read_text())
        self.assertIn("1500\n", (self.out/"0/fluid/T").read_text())
        self.assertFalse((self.out/"0/mold/alpha.metal").exists())
        self.assertEqual(len([p for p in (self.out/"0/fluid").iterdir()
                              if p.is_file()]),len(REGION_FIELDS["fluid"]))

    def test_provisional_RAS_and_no_heat_sources_no_solidification(self):
        record=self.staged()
        self.assertIn("kEpsilon",
                      (self.out/"constant/fluid/momentumTransport").read_text())
        self.assertIn("VoFTurbulenceDamping",
                      (self.out/"constant/fluid/fvModels").read_text())
        self.assertNotIn("heatSource",
                         (self.out/"constant/mold/fvModels").read_text())
        self.assertTrue(record["pilot_reference"]["mold_support_and_lower_recess_unresolved"])
        self.assertFalse(record["latent_heat_solidification_graphitization_shrinkage"])
        self.assertIn("zeroGradient",(self.out/"0/mold/T").read_text())

    def test_output_cannot_overwrite_even_empty_folder(self):
        self.out.mkdir()
        before=self.source/"0/fluid/T"
        orig=before.read_bytes()
        a,b,c=self.mock_real_provenance()
        with a,b,c:
            with self.assertRaisesRegex(ValueError,"never overwrite"):
                stage(self.source,self.accept,self.tutorial,self.out)
        self.assertEqual(before.read_bytes(),orig)

    def test_unapproved_native_T_does_not_start_copy(self):
        a,b,c=self.mock_real_provenance()
        f=self.accept/"FS_C04_NATIVE_T_ACCEPTANCE.json"
        record=json.loads(f.read_text())
        record["status"]="STAGED_NO_OPENFOAM"
        f.write_text(json.dumps(record))
        with a,b,c:
            with self.assertRaisesRegex(ValueError,"not accepted"):
                stage(self.source,self.accept,self.tutorial,self.out)
        self.assertFalse(self.out.exists())

    def test_wrong_official_solver_pair_rejected_before_copy(self):
        f=self.tutorial/"system/controlDict"
        f.write_text(f.read_text().replace("compressibleVoF;","fluid;"))
        a,b,c=self.mock_real_provenance()
        with a,b,c:
            with self.assertRaisesRegex(ValueError,"compatible region solvers"):
                stage(self.source,self.accept,self.tutorial,self.out)
        self.assertFalse((self.out/"system/controlDict").exists())

    def test_correct_screening_thermodynamic_dimension_and_temperature_BC(self):
        self.staged()
        t=(self.out/"0/fluid/T").read_text()
        self.assertIn("dimensions [0 0 0 1 0 0 0];",t)
        self.assertIn("atmosphereTop",t)
        self.assertIn("atmosphereSides",t)
        self.assertIn("atmosphereLowerSides",t)
        self.assertIn("fluid_to_mold",t)
        self.assertIn("inletValue uniform 300;",t)
        thermal=(self.out/"constant/mold/physicalProperties").read_text()
        self.assertIn("kappa { type uniform; value 2; }",thermal)

    def test_case_manifest_enforces_no_native_or_physics_validation_claim(self):
        record=self.staged()
        m=json.loads((self.out/"FS_C05_PHYSICS_CANDIDATE.json").read_text())
        self.assertEqual(m,record)
        self.assertFalse(m["solver_executed"])
        self.assertFalse(m["native_dictionary_validation_done"])
        self.assertFalse(m["VOF_CHT_energy_balance_validated"])
        self.assertTrue(m["mesh_and_alpha_initial_integrity_preserved"])


if __name__=="__main__":
    unittest.main()
