#!/usr/bin/env python3
"""Disposable read-only evidence tests; never access research WSL case."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import audit_c14_stage07_active_cellzone as audit
import run_c14_stage07_solver_backed_recovery as recovery
import stage_c14_3d_case_a as stage


class ActiveMeshZoneReadOnlyTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.case=self.root/"ORIGINAL"
        self.copy=self.root/"WORKCOPY_03"
        for case in (self.case,self.copy):
            poly=case/"constant/metal/polyMesh"
            poly.mkdir(parents=True)
            for name in stage.MESH:
                (poly/name).write_text("SAME C14 mesh data: "+name+"\n")
            (case/"log.foamMultiRun").write_text("ORIGINAL 10-second C14 CFD log\n")
        (self.copy/"constant/metal/polyMesh/cellZones").write_text(
            stage.whole_region_zone(stage.EXPECTED["metal"]))
        self.groups=[]
        for name in recovery.TASK_ORDER:
            log=self.copy/("log.C14_3D_postprocess_solverBacked_"+name)
            if name in ("core","energy","flow","momentum"):
                log.write_text("Time = 0.1\n--> FOAM FATAL IO ERROR:\n"
                               "Cannot find cellZone metal\nEnd\n")
            else:
                log.write_text("Time = 10s\nNative postprocessing End\n")
            self.groups.append({"group":name,"exit_code":0,
                                "log_sha256":audit.hash_file(log)})
        self.report=self.copy/recovery.REPORT
        self.report.write_text(json.dumps({
            "schema":"C3D04_A_C14_F14_SOLVER_BACKED_OFFLINE_RECOVERY_V1",
            "source_authentication":{"case":str(self.case)},
            "isolated_new_workcopy":str(self.copy),
            "native_groups":self.groups,
            "metal_cellZone_copy_only_recovery":{
                "status":"FULL_METAL_CELLZONE_CREATED_ONLY_IN_FRESH_COPY",
                "metal_cells":stage.EXPECTED["metal"],
                "added_to_copy_only":True,
            }
        }))

    def snapshot(self):
        return {str(p):audit.hash_file(p)
                for root in (self.case,self.copy)
                for p in root.rglob("*") if p.is_file()}

    def test_c14_zone_present_but_four_native_fatals_detected(self):
        before=self.snapshot()
        result=audit.inspect(self.case,self.copy)
        self.assertEqual(result["schema"],
                         "C3D04_A_STAGE07_ACTIVE_MESH_ZONE_READONLY_WSL_V1")
        self.assertEqual(result["triage_classification"],
                         "CONSTANT_METAL_ZONE_VALID_BUT_F14_REGISTRY_EMPTY_ROOT_CAUSE_UNRESOLVED")
        self.assertTrue(result["copy_constant_metal_mesh"][
                        "full_metal_cellzone_verified"])
        self.assertEqual(result["native_group_semantic_status"]["core"][
                         "foam_fatal_occurrences"],1)
        self.assertEqual(result["native_group_semantic_status"]["phase"][
                         "foam_fatal_occurrences"],0)
        self.assertEqual(result["metal_native_surface_power_coverage"][
                         "metalBoundaryEnergyPower"]["present"],False)
        self.assertFalse(result["new_CFD_run"])
        self.assertFalse(result["native_zone_repair_verified_in_actual_F14_runtime"])
        self.assertEqual(before,self.snapshot())

    def test_time_local_mesh_instance_warns_not_asserts_runtime_cause(self):
        local=self.copy/"0.1/metal/polyMesh"
        local.mkdir(parents=True)
        (local/"points").write_text("alternate mesh time instance\n")
        result=audit.inspect(self.case,self.copy)
        self.assertEqual(result["triage_classification"],
                         "TIME_LOCAL_MESH_ZONE_OVERRIDE_POSSIBLE_NOT_PROVEN")
        self.assertEqual(result["saved_mesh_instance_evidence"][
                         "time_local_metal_mesh_missing_full_zone"],1)
        self.assertFalse(result[
            "can_conclude_selected_F14_mesh_instance_from_files_only"])

    def test_real_native_profile_and_power_deficits_are_counted(self):
        for name,fac in (("metalTopEnergyPower",1),
                         ("metalMoldEnergyPower",2),
                         ("metalBoundaryEnergyPower",3)):
            out=self.copy/"postProcessing/metal"/name/"0"
            out.mkdir(parents=True)
            (out/"surfaceFieldValue.dat").write_text(
                "# Time sum(energyFlux)\n0 "+str(fac)+"\n")
        for family, names in (("horizontalProfiles",
                               ("line_y10mm","line_y20mm","line_y30mm")),
                              ("verticalProfiles",("line_x20mm",))):
            out=self.copy/"postProcessing/metal"/family/"10"
            out.mkdir(parents=True)
            for name in names:
                n=27 if family=="verticalProfiles" else 80
                (out/(name+".xy")).write_text(
                    "\n".join(f"{i/1000:g} 1400 {0.9-i/10000:g}"
                              for i in range(n))+"\n")
        report=audit.inspect(self.case,self.copy)
        self.assertEqual(report["metal_native_surface_power_coverage"][
                         "metalBoundaryEnergyPower"]["numeric_data_row_count"],1)
        self.assertEqual(report["final_primitive_80_point_profile_coverage"][
                         "verticalProfiles/line_x20mm"]["saved_data_points"],27)
        self.assertEqual(report["final_primitive_80_point_profile_coverage"][
                         "horizontalProfiles/line_y20mm"]["status"],"PASS")
        self.assertFalse(report["energy_conservation_verified"])

    def test_changed_original_CFD_solver_log_blocks_and_does_not_modify_copy(self):
        before=audit.hash_file(self.report)
        (self.case/"log.foamMultiRun").write_text("tampered original\n")
        with self.assertRaisesRegex(ValueError,"not identical"):
            audit.inspect(self.case,self.copy)
        self.assertEqual(audit.hash_file(self.report),before)

    def test_missing_copy_zone_is_reported_not_repaired(self):
        zone=self.copy/"constant/metal/polyMesh/cellZones"
        zone.unlink()
        before=self.snapshot()
        result=audit.inspect(self.case,self.copy)
        self.assertEqual(result["triage_classification"],
                         "MISSING_CELLZONE_FILE_IN_PRESERVED_COPY")
        self.assertFalse(zone.exists())
        self.assertEqual(before,self.snapshot())


if __name__=="__main__":
    unittest.main()
