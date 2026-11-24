#!/usr/bin/env python3
"""Real C3D05 B source-only 100 saved rho/phi, mass and modeled phase QA."""
from __future__ import annotations

from array import array
import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"analyze_existing_case_b_c14_metal_mass_phi.py"
spec=importlib.util.spec_from_file_location("case_b_real_metal_mass_phi",SCRIPT)
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def foam_phi(path:Path,patch1:str,patch2:str,
             units:str="1 0 -1 0 0 0 0")->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(
        "FoamFile { format ascii; class surfaceScalarField; object phi; }\n"
        "dimensions ["+units+"];\n"
        "internalField uniform 0;\n"
        "boundaryField\n{\n"
        " metalTop {\n  type calculated;\n"+patch1+"\n }\n"
        " metal_to_mold {\n type calculated;\n"+patch2+"\n }\n"
        "}\n",encoding="utf-8"
    )


class CaseBRealSavedRhoPhiMassQA(unittest.TestCase):
    def test_source_contract_exact_reference_keys_present(self):
        contract=M.inventory.source_C14_constants()
        self.assertAlmostEqual(contract["rho_metal_kg_m3"],6820)
        self.assertAlmostEqual(contract["L_metal_J_kg"],228600)
        code=SCRIPT.read_text(encoding="utf-8")
        self.assertIn('C14["rho_metal_kg_m3"]',code)
        self.assertIn('C14["L_metal_J_kg"]',code)

    def test_true_rho_mass_and_model_solid_complement_unequal_volumes(self):
        d=M.rho_mass_snapshot(
            [1000.,2000.],[.5,0.],[1.,3.],200.)
        self.assertAlmostEqual(d["rho_mass_kg"],7000.)
        self.assertAlmostEqual(d["rho_mean_volume_weighted_kg_m3"],1750.)
        self.assertAlmostEqual(d["modeled_solid_complement_mass_kg"],6500.)
        self.assertAlmostEqual(d[
            "rho_weighted_solid_complement_mass_fraction_MODELED"],6500/7000)
        self.assertAlmostEqual(d[
            "model_rhoL_solid_equivalent_inventory_J_NOT_NATIVE_FVMODEL"],1300000.)

    def test_reject_nonphysical_original_rho_and_phase(self):
        with self.assertRaisesRegex(ValueError,"nonphysical"):
            M.rho_mass_snapshot([-2,1000],[.5,.6],array("d",[1,1]),228600)
        with self.assertRaisesRegex(ValueError,"alpha1"):
            M.rho_mass_snapshot([1000,1000],[.5,1.1],array("d",[1,1]),228600)
        with self.assertRaisesRegex(ValueError,"lengths"):
            M.rho_mass_snapshot([1000],[.5,.8],array("d",[1,1]),228600)
        with self.assertRaisesRegex(ValueError,"cell volume"):
            M.rho_mass_snapshot([1000],[.5],array("d",[-1]),228600)

    def test_phi_reads_units_and_true_patch_values_uniform_and_nonuniform(self):
        with TemporaryDirectory() as d:
            f=Path(d)/"1/metal/phi"
            foam_phi(f,"value uniform 0.5;",
                     "value nonuniform List<scalar> 3 ( 1 -2 3 );")
            x=M.phi_patch_mass_flux(f,{"metalTop":2,"metal_to_mold":3})
            self.assertAlmostEqual(x["metalTop"],1.)
            self.assertAlmostEqual(x["metal_to_mold"],2.)

    def test_phi_compact_native_face_values_and_comments(self):
        with TemporaryDirectory() as d:
            f=Path(d)/"1/metal/phi"
            foam_phi(f,
                     "value nonuniform List<scalar> 2 { -0.25 };",
                     "// thermo names\nvalue uniform 0;")
            x=M.phi_patch_mass_flux(f,{"metalTop":2,"metal_to_mold":3})
            self.assertEqual(x["metalTop"],-.5)
            self.assertEqual(x["metal_to_mold"],0)

    def test_phi_rejects_not_kg_per_s_and_invalid_patch_counts(self):
        with TemporaryDirectory() as d:
            f=Path(d)/"1/metal/phi"
            foam_phi(f,"value uniform 0;",
                     "value nonuniform List<scalar> 3 ( 1 2 3 );",
                     units="0 3 -1 0 0 0 0")
            with self.assertRaisesRegex(ValueError,"not kg/s"):
                M.phi_patch_mass_flux(f,{"metalTop":2,"metal_to_mold":3})
            foam_phi(f,"value uniform 0;",
                     "value nonuniform List<scalar> 2 (1 2);")
            with self.assertRaisesRegex(ValueError,"face count"):
                M.phi_patch_mass_flux(f,{"metalTop":2,"metal_to_mold":3})
            foam_phi(f,"type zeroGradient;",
                     "value uniform 0;")
            with self.assertRaisesRegex(ValueError,"one readable"):
                M.phi_patch_mass_flux(f,{"metalTop":2,"metal_to_mold":3})

    def test_phi_native_mesh_boundary_source_patch_counts(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"boundary"
            p.write_text(
                "FoamFile { format ascii; class polyBoundaryMesh; object boundary; }\n"
                "2\n(\n"
                " metalTop { type patch; nFaces 5; startFace 9; }\n"
                " metal_to_mold { type mappedWall; nFaces 12636; startFace 14; }\n"
                ")\n",encoding="utf-8"
            )
            x=M.mesh_patch_counts(p)
            self.assertEqual(x["metalTop"],5)
            self.assertEqual(x["metal_to_mold"],12636)

    def test_mass_screen_100_readable_times_but_no_t0_never_fabricated(self):
        records=[]
        for i in range(101):
            row={name:None for name in M.HEADER}
            row["time_s"]=round(i*.1,1)
            row["rho_mass_kg"]=None if i==0 else 5.0
            row["phi_metalTop_kg_s_if_readable"]=None if i==0 else .01
            row["phi_metal_to_mold_kg_s_if_readable"]=None if i==0 else 0.0
            records.append(row)
        v=M.temporal_mass_screening(records)
        self.assertEqual(v["rho_states"],100)
        self.assertEqual(v["phi_and_rho_joint_readable_states"],100)
        self.assertEqual(v["first_rho_time_s"],.1)
        self.assertEqual(v["last_contiguous_joint_time_s"],10)
        self.assertFalse(v["first_time_t0_rho_assumed_or_fabricated"])
        self.assertIsNone(records[0]["rho_mass_kg"])
        self.assertIsNone(records[0][
            "sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"])
        self.assertAlmostEqual(v["sampled_cumulative_exterior_phi_kg"],.099)
        self.assertAlmostEqual(v[
            "partial_mass_delta_plus_sampled_q_kg_NOT_CONTINUITY_RESIDUAL"],.099)
        self.assertFalse(v["mass_conservation_verified"])

    def test_mass_screen_missing_phi_does_not_substitute_zero(self):
        records=[]
        for i in range(101):
            row={name:None for name in M.HEADER}
            row["time_s"]=round(i*.1,1)
            row["rho_mass_kg"]=5.0
            row["phi_metalTop_kg_s_if_readable"]=None
            row["phi_metal_to_mold_kg_s_if_readable"]=None
            records.append(row)
        x=M.temporal_mass_screening(records)
        self.assertEqual(x["phi_and_rho_joint_readable_states"],0)
        self.assertFalse(x["saved_time_screening_available"])
        self.assertIsNone(records[-1][
            "mass_delta_plus_sampled_exterior_phi_kg_NOT_CONTINUITY_RESIDUAL"])

    def test_mass_screen_time_gap_stops_integration_instead_of_bridging(self):
        records=[]
        for i in range(101):
            row={name:None for name in M.HEADER}
            row["time_s"]=round(i*.1,1)
            row["rho_mass_kg"]=5.0
            row["phi_metalTop_kg_s_if_readable"]=0.0
            row["phi_metal_to_mold_kg_s_if_readable"]=0.0
            records.append(row)
        records[20]["rho_mass_kg"]=None
        x=M.temporal_mass_screening(records)
        self.assertEqual(x["last_contiguous_joint_time_s"],1.9)
        self.assertFalse(x["complete_uninterrupted_joint_coverage_to_10s"])
        self.assertIsNone(records[21][
            "sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"])

    def test_read_only_source_no_new_solver_and_new_immutable_archive(self):
        code=SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run(",code)
        self.assertNotIn("foamMultiRun(",code)
        self.assertNotIn("wmake(",code)
        self.assertIn("pending.rename(out)",code)
        self.assertIn('"actual_native_fvModel_latent_source_integrated":False',code)
        self.assertIn('"no_original_t0_rho_or_phi_fabricated":True',code)
        self.assertIn('"native_solver_mass_conservation_verified":False',code)
        self.assertIn("phi_patch_mass_flux",code)
        self.assertIn("C3D05_B_C14_ORIGINAL_RHO_PHI_ALPHA1_INPUT_SHA256.json",code)


if __name__=="__main__":
    unittest.main()
