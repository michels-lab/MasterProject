#!/usr/bin/env python3
"""Negative and positive source-faithful 3D-A phase-change staging regressions."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import stage_c14_3d_case_a as stage
import c14_source_fidelity as c14


def fake_list(values: list[int]) -> str:
    return (
        "FoamFile\n{\n format ascii;\n class labelList;\n object owner;\n}\n"
        + str(len(values))+"\n(\n"
        + "\n".join(map(str,values))+"\n)\n"
    )


class CaseAOriginalC14PhysicsTest(unittest.TestCase):
    def test_exact_C14_material_fluid_and_phase_change_preserved(self):
        evidence=c14.verify()
        self.assertEqual(evidence["regionSolvers"],{"metal":"fluid","mold":"solid"})
        files=stage.input_files(2,smoke=False)
        self.assertEqual(len(files),23)
        for rel in ("constant/metal/materials/castIron",
                    "constant/mold/materials/silica",
                    "constant/metal/fvModels",
                    "constant/metal/momentumTransport",
                    "system/metal/fvSchemes",
                    "system/mold/fvSchemes",
                    "system/fvSolution",
                    "system/controlDict"):
            self.assertEqual(files[rel].encode("utf-8"),
                             (c14.C14/rel).read_bytes())
        self.assertIn("heRhoThermo;",files["constant/metal/materials/castIron"])
        self.assertIn("sensibleEnthalpy;",files["constant/metal/materials/castIron"])
        self.assertIn("heSolidThermo;",files["constant/mold/materials/silica"])
        self.assertIn("alpha1e         0.8;",files["constant/metal/fvModels"])
        self.assertIn("cellZone        metal;",files["constant/metal/fvModels"])
        self.assertIn("pRefCell          0;",files["system/metal/fvSolution"])
        self.assertIn("pRefValue          1e5;",files["system/metal/fvSolution"])
        self.assertNotIn("pRefPoint",c14.strip_comments(
            files["system/metal/fvSolution"]))
        self.assertIn("endTime         10;",files["system/controlDict"])
        self.assertIn("deltaT          0.001;",files["system/controlDict"])

    def test_C14_3D_only_physical_invariant_and_fail_closed(self):
        original=c14.assemble_unmaterialized_source_exact_fileset()
        full=stage.input_files(8960,smoke=False)
        self.assertEqual(full["system/controlDict"],original["system/controlDict"])
        self.assertEqual(full["constant/metal/fvModels"],
                         original["constant/metal/fvModels"])
        self.assertEqual(full["constant/metal/materials/castIron"],
                         original["constant/metal/materials/castIron"])
        self.assertEqual(full["constant/mold/materials/silica"],
                         original["constant/mold/materials/silica"])
        self.assertEqual(set(full)-set(original),
                         {"constant/metal/polyMesh/cellZones"})
        self.assertEqual(
            {key for key in original if full[key]!=original[key]},
            {"system/metal/fvSolution"})
        for relative, alteration in (
            ("constant/metal/materials/castIron", ("827","900")),
            ("constant/metal/fvModels", ("alpha1e         0.8;","alpha1e 0.9;")),
            ("system/controlDict", ("deltaT          0.001;","deltaT 0.002;")),
            ("0/metal/T", ("h uniform 10;","h uniform 25;")),
            ("system/mold/fvSchemes", ("FoamFile","WrongFoamFile")),
        ):
            with self.subTest(relative=relative):
                bad=dict(full)
                previous,new=alteration
                self.assertIn(previous,bad[relative])
                bad[relative]=bad[relative].replace(previous,new,1)
                with self.assertRaisesRegex(ValueError,
                                            "C3D04_A_C14_NATIVE_GATE_BLOCKED"):
                    stage.enforce_C14_3D_only_delta(
                        bad,original,8960,smoke=False,existing_zone=False)
        bad=dict(full)
        bad["constant/metal/polyMesh/cellZones"]=stage.whole_region_zone(8959)
        with self.assertRaisesRegex(ValueError,"metal zone"):
            stage.enforce_C14_3D_only_delta(
                bad,original,8960,smoke=False,existing_zone=False)
        bad=dict(full)
        bad["constant/metal/fvModels.newArbitraryPhysics"]="true"
        with self.assertRaisesRegex(ValueError,"unexpected file"):
            stage.enforce_C14_3D_only_delta(
                bad,original,8960,smoke=False,existing_zone=False)

    def test_all_zone_labels_without_duplicates_or_omissions(self):
        for n in (1,4,8960):
            zone=stage.whole_region_zone(n)
            self.assertIn("type cellZone;",zone)
            self.assertIn("object cellZones;",zone)
            self.assertIn("cellLabels List<label> "+str(n),zone)
            with tempfile.TemporaryDirectory() as d:
                file=Path(d)/"cellZones"
                file.write_text(zone)
                self.assertTrue(stage.audit_existing_zone(file,n))
                with self.assertRaisesRegex(ValueError,"does not cover"):
                    stage.audit_existing_zone(file,n+1)
                file.write_text(zone.replace("metal\n{","wrong\n{"))
                with self.assertRaisesRegex(ValueError,"unique metal"):
                    stage.audit_existing_zone(file,n)
        with self.assertRaises(ValueError):
            stage.whole_region_zone(0)
        with self.assertRaises(ValueError):
            stage.whole_region_zone(-1)

    def test_pressure_gauge_adapts_index_only_and_rejects_wrong_2d_source(self):
        raw=c14.read_original("system/metal/fvSolution")
        update=stage.three_d_pressure_solution(raw,1)
        self.assertEqual(update.count("pRefCell          0;"),1)
        self.assertNotIn("pRefPoint",c14.strip_comments(update))
        self.assertIn("nEnergyCorrectors  2;",update)
        with self.assertRaisesRegex(ValueError,"pRefPoint"):
            stage.three_d_pressure_solution(update,1)
        with self.assertRaises(ValueError):
            stage.three_d_pressure_solution(raw,0)
        with self.assertRaisesRegex(ValueError,"reference pressure"):
            stage.three_d_pressure_solution(raw.replace("pRefValue          1e5;",
                                                          "pRefValue 90000;"),1)

    def test_smoke_changes_time_only_no_C14_transport_or_phase_parameters(self):
        candidate=stage.input_files(1,smoke=True)
        self.assertEqual(len(candidate),23)
        c=candidate["system/controlDict"]
        self.assertIn("endTime 0.002;",c)
        self.assertIn("writeInterval 1;",c)
        self.assertIn("deltaT          0.001;",c)
        self.assertIn("metal       fluid;",c)
        self.assertIn("mold        solid;",c)
        self.assertEqual(candidate["constant/metal/fvModels"],
                         c14.read_original("constant/metal/fvModels"))
        self.assertEqual(candidate["constant/metal/materials/castIron"],
                         c14.read_original("constant/metal/materials/castIron"))
        with self.assertRaisesRegex(ValueError,"endTime"):
            stage.smoke_control(c)

    def test_F14_native_compact_owner_and_empty_neighbour_real_blockMesh_format(self):
        # Native Foundation14 artifact 14688837569 writes 6{0} and 0(),
        # NOT the multi-line numeric list accepted by the legacy T0 helper.
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for region in ("metal","mold"):
                mesh=root/"constant"/region/"polyMesh"
                mesh.mkdir(parents=True)
                h=('FoamFile\n{\n    format ascii;\n    class labelList;\n'
                   '    note "nCells: 1 nFaces: 6 nInternalFaces: 0";\n'
                   '    object owner;\n}\n')
                (mesh/"owner").write_text(h+"\n6{0}\n")
                (mesh/"neighbour").write_text(h+"\n0()\n")
                for name in ("points","faces","boundary"):
                    (mesh/name).write_text("STATIC_F14_NATIVE_FIXTURE")
                self.assertEqual(stage.read_labels(mesh/"owner"),(6,0))
                self.assertEqual(stage.read_labels(mesh/"neighbour"),(0,-1))
                self.assertEqual(stage.region_cells(root,region,1)["nCells"],1)
                (mesh/"owner").write_text(h+"\n6(0 0 0 0 0)\n")
                with self.assertRaisesRegex(ValueError,"length"):
                    stage.region_cells(root,region,1)

    def test_real_polyMesh_owner_neighbour_count_read_and_nondestructive_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for region in ("metal","mold"):
                mesh=root/"constant"/region/"polyMesh"
                mesh.mkdir(parents=True)
                (mesh/"owner").write_text(fake_list([0]*6))
                (mesh/"neighbour").write_text(fake_list([]))
                for name in ("points","faces","boundary"):
                    (mesh/name).write_text("ORIGINAL_3D_MESH_BYTES_"+region+name)
            self.assertEqual(stage.region_cells(root,"metal",1)["nCells"],1)
            self.assertEqual(stage.region_cells(root,"mold",1)["nCells"],1)
            with self.assertRaisesRegex(ValueError,"expected 8960"):
                stage.region_cells(root,"metal",8960)
            dst=root.parent/(root.name+"-stage-not-inside-source")
            # output outside ephemeral source but non-overwrite; harmless fake
            with patch.object(stage,"environment",return_value={
                  "foamDictionary":"/mock/foamDictionary",
                  "foamMultiRun":"/mock/foamMultiRun",
                  "checkMesh":"/mock/checkMesh",
            }), patch.object(stage,"native",return_value={"rc":0}):
                report=stage.stage(root,dst,smoke=False,
                                   expected={"metal":None,"mold":None})
            try:
                self.assertFalse(report["native_solver_run"])
                self.assertFalse(report["Cp_to_Cv_metal_substitution"])
                self.assertEqual(report["files_count"],23)
                self.assertEqual(len(report["parsed_dicts"]),22)
                self.assertEqual(report["native_geometry_gate"]["counts"]
                                 ["metal"]["nCells"],1)
                self.assertIn("cellLabels List<label> 1",
                              (dst/"constant/metal/polyMesh/cellZones").read_text())
                self.assertEqual((root/"constant/metal/polyMesh/owner").read_bytes(),
                                 (dst/"constant/metal/polyMesh/owner").read_bytes())
                with self.assertRaisesRegex(ValueError,"overwrit"):
                    stage.protect_source(root,dst)
                with self.assertRaisesRegex(ValueError,"overlaps"):
                    stage.protect_source(root,root/"inside")
            finally:
                import shutil
                shutil.rmtree(dst)

    def test_existing_real_zone_reject_if_not_all_cells(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"cellZones"
            self.assertFalse(stage.audit_existing_zone(path,3))
            path.write_text(stage.whole_region_zone(3))
            self.assertTrue(stage.audit_existing_zone(path,3))
            path.write_text(path.read_text().replace("0\n1\n2","0\n1\n1"))
            with self.assertRaisesRegex(ValueError,"does not cover"):
                stage.audit_existing_zone(path,3)


if __name__=="__main__":
    unittest.main()
