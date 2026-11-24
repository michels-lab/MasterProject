#!/usr/bin/env python3
"""All tests are disposable data; NEVER operate user's WSL native CFD."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import run_c14_stage07_solver_backed_recovery as sut


class NativeSolverBackedStage07Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.newcopy=self.root/"C3D04_NEW_COPY"
        (self.newcopy/"system").mkdir(parents=True)
        self.reference=sut.C14
        for name in ("functions","researchDiagnostics","lineProfiles",
                     "momentumPostProcessing"):
            shutil.copy2(self.reference/"system"/name,
                         self.newcopy/"system"/name)
        self.sample_geometry={"profiles":{
            "line_y10mm":{"start":(0.001,0.01,0.005),
                           "end":(0.03,0.01,0.005),"axis":"x","nPoints":80},
            "line_y20mm":{"start":(0.001,0.02,0.005),
                           "end":(0.03,0.02,0.005),"axis":"x","nPoints":80},
            "line_y30mm":{"start":(0.001,0.03,0.005),
                           "end":(0.03,0.03,0.005),"axis":"x","nPoints":80},
            "line_x20mm":{"start":(0.02,0.001,0.005),
                           "end":(0.02,0.03,0.005),"axis":"y","nPoints":80},
        },"probe_actual_m":(0.02,0.02,0.005)}

    def test_original_c14_group_objects_preserved_and_offline_ddt_stripped(self):
        paths={}
        for name in sut.TASK_ORDER:
            path,objects=sut.assembled_dict(self.newcopy,name)
            paths[name]=path
            self.assertEqual(len(objects),len(sut.PAIRS[name]))
            self.assertTrue(path.is_file())
            text=path.read_text()
            for item in sut.PAIRS[name]:
                self.assertIn(item[1]+"\n",text)
            self.assertNotIn("temperatureTimeDerivative\n",text)
            self.assertNotIn("liquidFractionTimeDerivative\n",text)
        energy=paths["energy"].read_text()
        self.assertIn("type            energyFlux;",energy)
        self.assertIn("patch           metal_to_mold;",energy)
        self.assertIn("operation       sum;",energy)
        core=paths["core"].read_text()
        self.assertIn("volIntegrate;",core)
        self.assertIn("weightField     rho;",core)
        phase=paths["phase"].read_text()
        self.assertIn("phaseChangeSource:alpha1",phase)
        profiles=paths["profiles"].read_text()
        for name in ("horizontalProfiles","verticalProfiles"):
            self.assertIn(name,profiles)
        self.assertNotIn("latentHeatRateVol",profiles)
        self.assertNotIn("coolingRate",profiles)
        self.assertIn("phaseChangeSource:alpha1",profiles)
        self.assertIn("magPhaseChangeDarcyAcceleration",paths["momentum"].read_text())
        with self.assertRaisesRegex(sut.Blocked,"unexpectedly already contains"):
            sut.assembled_dict(self.newcopy,"energy")

    def test_native_offline_arguments_never_launch_solver(self):
        args_seen=[]
        def fake_native(copy,name,arguments):
            args_seen.append((name,arguments))
            out=copy/("log.C14_3D_postprocess_"+name)
            out.write_text("Enabling floating point exception trapping\nEnd\n")
            return {"name":name,"command_without_bootstrap":arguments,
                    "exit_code":0,"passed":True,"log":out.name}
        with mock.patch.object(sut.old,"run_native",side_effect=fake_native):
            for group in sut.TASK_ORDER:
                d=self.newcopy/"system"/("stage07Offline_"+group)
                d.write_text("valid")
                result=sut.native_group(self.newcopy,group,d)
                self.assertTrue(result["passed"])
                self.assertFalse(result["log_signatures"])
        self.assertEqual(len(args_seen),6)
        for name,args in args_seen:
            self.assertEqual(args[0],"foamPostProcess")
            self.assertIn("-region",args)
            self.assertIn("metal",args)
            self.assertEqual(args[-2:],["-time","0:"])
            if name.endswith(("core","energy","flow","momentum")):
                self.assertEqual(args[args.index("-solver")+1],"fluid")
                self.assertNotIn("-fields",args)
            else:
                self.assertIn("-fields",args)
                self.assertNotIn("-solver",args)

    def test_existing_CFD_failed_copy_and_forensics_are_SHA_bound(self):
        # Synthetic log/controlDict-only fixture omits native 8960-cell mesh.
        # Mesh topology is tested independently by fresh-zone regression.
        mocked_mesh=mock.patch.object(
            sut.stage,"region_cells",return_value={
                "nCells":sut.stage.EXPECTED["metal"]})
        mocked_mesh.start()
        self.addCleanup(mocked_mesh.stop)
        ca=self.root/"CANONICAL_C14"
        (ca/"system").mkdir(parents=True)
        (ca/"system/controlDict").write_text("AUTHENTIC C14\n")
        case=self.root/"C3D04_A_RUN"
        (case/"10/metal").mkdir(parents=True)
        (case/"system").mkdir()
        (case/"system/controlDict").write_text("AUTHENTIC C14\n")
        (case/"log.foamMultiRun").write_text("10000 steps; End\n")
        (case/"10/metal/T").write_text("T")
        (case/"10/metal/U").write_text("U")
        (case/"10/metal/phaseChangeSource:alpha1").write_text("alpha")
        failed=self.root/"C3D04_PREVIOUS_FAILED_COPY"
        (failed/"system").mkdir(parents=True)
        (failed/"system/controlDict").write_text("AUTHENTIC C14\n")
        (failed/"log.foamMultiRun").write_text("10000 steps; End\n")
        recovery=self.root/"Kinetics"
        recovery.mkdir()
        (recovery/"C3D04_A_STAGE07_RECOVERY_REPORT.json").write_text(
            json.dumps({
                "schema":"C3D04_A_C14_3D_STAGE07_EXISTING_EVIDENCE_V1",
                "case_A_source_run_read_only":str(case),
                "source_sha256":{
                    "source_CFD_log_sha256":sut.sha(case/"log.foamMultiRun")
                }
            }))
        forensic=self.root/"Forensic"
        forensic.mkdir()
        (forensic/"C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json").write_text(
            json.dumps({
                "schema":"C3D04_A_STAGE07_NATIVE_FAILURE_FORENSICS_V1",
                "original_10s_case_read_only":str(case),
                "existing_native_workcopy_read_only":str(failed),
                "native_commands_verified":False,
                "native_failed_commands":["c14_functions"],
                "evidence_sha256":{"source_model_sha":{
                    "authentic_10s_solver_log_sha256":
                        sut.sha(case/"log.foamMultiRun")
                }}
            }))
        old_c14=sut.C14
        sut.C14=ca
        self.addCleanup(lambda:setattr(sut,"C14",old_c14))
        target=self.root/"NEW_SAFE_RECOVERY"
        evidence=sut.original_case_gate(case,failed,recovery,forensic,target)
        self.assertEqual(evidence["original_10s_solver_log_sha256"],
                         sut.sha(case/"log.foamMultiRun"))
        self.assertFalse(target.exists())
        with self.assertRaisesRegex(sut.Blocked,"overlaps"):
            sut.original_case_gate(case,failed,recovery,forensic,
                                   failed/"DANGEROUS_NEW")
        target.mkdir()
        with self.assertRaisesRegex(sut.Blocked,"occupied"):
            sut.original_case_gate(case,failed,recovery,forensic,target)

    def test_forged_failure_or_new_original_CFD_log_blocks(self):
        # Use fixture above but modify the source before invoking a new copy.
        # The previous test validates identity and occupied folder checks.
        self.assertTrue(sut.selected_source_block(
            (self.reference/"system/researchDiagnostics").read_text(),
            "metalSensibleEnthalpy").startswith("metalSensibleEnthalpy"))

    def test_surface_energy_101_states_from_new_native_tables_is_not_global_closure(self):
        base=self.newcopy/"postProcessing/metal"
        for dirname,multiplier in (
            ("metalTopEnergyPower",2.0),
            ("metalMoldEnergyPower",3.0),
            ("metalBoundaryEnergyPower",5.0),
        ):
            d=base/dirname/"0"
            d.mkdir(parents=True)
            rows=["# Time sum(energyFlux)"]
            rows += [f"{i/10:g} {i*multiplier:g}" for i in range(101)]
            (d/"surfaceFieldValue.dat").write_text("\n".join(rows)+"\n")
        result=sut.surface_energy_summary(self.newcopy)
        self.assertEqual(result["status"],
                         "NATIVE_METAL_SURFACE_POWER_SAVED_STATES_DIAGNOSTIC")
        self.assertEqual(result["final_energy_power_out_W"],
                         {"top":200.0,"contact":300.0,"total":500.0})
        self.assertTrue(result["nominal_metal_surface_power_reconciled"])
        self.assertFalse(result["global_energy_conservation_verified"])
        # Inconsistency must never be misreported as a successful balance.
        bad=base/"metalBoundaryEnergyPower"/"0/surfaceFieldValue.dat"
        bad.write_text(bad.read_text().replace("10 500", "10 550"))
        changed=sut.surface_energy_summary(self.newcopy)
        self.assertFalse(changed["nominal_metal_surface_power_reconciled"])
        self.assertFalse(changed["global_energy_conservation_verified"])

    def test_native_power_100_complete_saved_states_excluding_t0_not_fabricated(self):
        base=self.newcopy/"postProcessing/metal"
        for name,fac in (("metalTopEnergyPower",2),
                         ("metalMoldEnergyPower",3),
                         ("metalBoundaryEnergyPower",5)):
            folder=base/name/"0"
            folder.mkdir(parents=True)
            with (folder/"surfaceFieldValue.dat").open("w") as stream:
                stream.write("# Time sum(energyFlux)\n")
                for i in range(1,101):
                    stream.write(f"{i/10:g} {i*fac:g}\n")
        out=sut.surface_energy_summary(self.newcopy)
        self.assertTrue(out["nominal_metal_surface_power_reconciled"])
        self.assertEqual(out["saved_times_count"],100)
        self.assertAlmostEqual(out["first_saved_time_s"],0.1)
        self.assertFalse(out["t0_native_power_available"])
        self.assertFalse(out["t0_native_flux_fabricated"])
        self.assertFalse(out["global_energy_conservation_verified"])
        self.assertEqual(out["native_time_series"][
            "metalBoundaryEnergyPower"]["numeric_data_row_count"],100)

    def test_native_power_only_99_states_is_blocked_without_guessing(self):
        base=self.newcopy/"postProcessing/metal"
        for name in ("metalTopEnergyPower","metalMoldEnergyPower",
                     "metalBoundaryEnergyPower"):
            path=base/name/"0"
            path.mkdir(parents=True)
            (path/"surfaceFieldValue.dat").write_text(
                "# Time sum(energyFlux)\n"+
                "\n".join(f"{i/10:g} {i:g}" for i in range(2,101))+"\n")
        out=sut.surface_energy_summary(self.newcopy)
        self.assertEqual(out["status"],
                         "NATIVE_SURFACE_POWER_TABLES_MISSING_OR_INCOMPATIBLE")
        self.assertIn("99 rows",out["reason"])
        self.assertFalse(out["nominal_metal_surface_power_reconciled"])

    def test_missing_energy_table_is_reported_without_fabrication(self):
        result=sut.surface_energy_summary(self.newcopy)
        self.assertEqual(result["status"],
                         "NATIVE_SURFACE_POWER_TABLES_MISSING_OR_INCOMPATIBLE")
        self.assertFalse(result["global_energy_conservation_verified"])


class ExistingNewCopyNonDestructiveInspectionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.c14=self.root/"ORIGINAL_C14"
        self.case=self.root/"C14_10S_REAL"
        self.copy=self.root/"C14_NATIVE_NEW_COPY_02"
        self.recovery=self.root/"C14_STAGE07_KINETICS"
        self.forensic=self.root/"C14_STAGE07_FAILED_COPY_FORENSICS"
        (self.c14/"system").mkdir(parents=True)
        (self.case/"system").mkdir(parents=True)
        (self.copy/"system").mkdir(parents=True)
        self.recovery.mkdir()
        self.forensic.mkdir()
        for base in (self.c14,self.case,self.copy):
            (base/"system/controlDict").write_text("ORIGINAL C14 controlDict\n")
        for base in (self.case,self.copy):
            (base/"log.foamMultiRun").write_text("Time = 10s\nEnd\n")
        (self.recovery/"C3D04_A_STAGE07_RECOVERY_REPORT.json").write_text("{}\n")
        (self.forensic/"C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json").write_text("{}\n")
        prev=sut.C14
        sut.C14=self.c14
        self.addCleanup(lambda:setattr(sut,"C14",prev))
        self.groups=[]
        for i,g in enumerate(sut.TASK_ORDER):
            f=self.copy/("log.C14_3D_postprocess_solverBacked_"+g)
            f.write_text("start\nEnd\n" if i != 5 else
                         "--> FOAM FATAL ERROR:\nfield missing\n")
            self.groups.append({
                "group":g,"name":"solverBacked_"+g,
                "exit_code":0 if i != 5 else 2,
                "passed":i != 5,
                "log":f.name,
                "log_sha256":sut.sha(f),
            })
        self.report=self.copy/sut.REPORT
        self.report.write_text(json.dumps({
            "schema":"C3D04_A_C14_F14_SOLVER_BACKED_OFFLINE_RECOVERY_V1",
            "isolated_new_workcopy":str(self.copy),
            "source_authentication":{
                "case":str(self.case),
                "original_10s_solver_log_sha256":
                    sut.sha(self.case/"log.foamMultiRun"),
                "original_C14_controlDict_sha256":
                    sut.sha(self.c14/"system/controlDict"),
                "recovery_report_sha256":sut.sha(
                    self.recovery/"C3D04_A_STAGE07_RECOVERY_REPORT.json"),
                "forensic_report_sha256":sut.sha(
                    self.forensic/"C3D04_A_C14_NATIVE_STAGE07_FORENSIC_REPORT.json"),
            },
            "native_groups":self.groups,
            "native_groups_passed":[x["group"] for x in self.groups if x["passed"]],
            "native_groups_failed":[x["group"] for x in self.groups if not x["passed"]],
            "surface_energy":{"status":"NATIVE_METAL_SURFACE_POWER_SAVED_STATES_DIAGNOSTIC",
                              "global_energy_conservation_verified":False},
        }))

    def inspect(self):
        return sut.inspect_occupied_copy(
            self.case,self.copy,self.recovery,self.forensic)

    def test_completed_earlier_run_is_identified_no_new_commands_or_writes(self):
        data=[(p,sut.sha(p)) for p in [
            self.report,self.case/"log.foamMultiRun",
            self.copy/"log.C14_3D_postprocess_solverBacked_core"]]
        with mock.patch.object(sut.old,"run_native",
                               side_effect=AssertionError("must never call native")):
            state=self.inspect()
        self.assertEqual(state["status"],
                         "EXISTING_COMPLETE_NATIVE_POSTPROCESS_REPORT_REUSED_NO_NEW_RUN")
        self.assertEqual(state["native_groups_failed"],["momentum"])
        self.assertEqual(len(state["native_groups_passed"]),5)
        self.assertFalse(state["native_validation_verified"])
        self.assertFalse(state["global_energy_conservation_verified"])
        self.assertEqual(data,[(p,sut.sha(p)) for p,_ in data])

    def test_real_wsl_exit_zero_four_fatal_groups_reclassified_in_place(self):
        """All OS passes in prior report; native FATAL for four groups overrides."""
        record=json.loads(self.report.read_text())
        for item in record["native_groups"]:
            group=item["group"]
            # Simulate the actual _02 report with zero OS exit codes for all.
            item["exit_code"]=0
            item["passed"]=True
            p=self.copy/("log.C14_3D_postprocess_solverBacked_"+group)
            if group in ("core","energy","flow","momentum"):
                p.write_text(
                    "Time = 10s\n--> FOAM FATAL IO ERROR:\n"
                    "Cannot find cellZone metal\nAvailable cellZones: 0()\nEnd\n")
            else:
                p.write_text("Time = 10s\nNative field processing\nEnd\n")
            item["log_sha256"]=sut.sha(p)
        record["native_groups_passed"]=list(sut.TASK_ORDER)
        record["native_groups_failed"]=[]
        self.report.write_text(json.dumps(record))
        before=sut.sha(self.report)
        with mock.patch.object(sut.old,"run_native",
                               side_effect=AssertionError("NO native rerun")):
            observed=self.inspect()
        self.assertEqual(observed["status"],
                         "EXISTING_COMPLETE_REPORT_WITH_NATIVE_FATALS_PRESERVED")
        self.assertEqual(observed["native_groups_passed"],["phase","profiles"])
        self.assertEqual(observed["native_groups_failed"],
                         ["core","energy","flow","momentum"])
        self.assertTrue(observed["prior_report_false_positive_success_detected"])
        self.assertEqual(observed["original_report_groups_passed_by_exit_code_only"],
                         list(sut.TASK_ORDER))
        self.assertEqual(sut.sha(self.report),before)

    def test_new_semantic_group_report_with_fatal_exit_zero_is_authenticated(self):
        """Future _03 must not fail authenticity checks on semantic FAIL/rc=0."""
        record=json.loads(self.report.read_text())
        for item in record["native_groups"]:
            log=self.copy/("log.C14_3D_postprocess_solverBacked_"+item["group"])
            log.write_text(
                "--> FOAM FATAL IO ERROR:\n"
                "Cannot find cellZone metal\nEnd\n"
                if item["group"]=="core" else "End\n")
            item["exit_code"]=0
            item["passed"]=item["group"]!="core"
            item["foam_fatal_present"]=item["group"]=="core"
            item["log_sha256"]=sut.sha(log)
        record["native_groups_passed"]=[x["group"] for x in record["native_groups"]
                                        if x["passed"]]
        record["native_groups_failed"]=["core"]
        self.report.write_text(json.dumps(record))
        observed=self.inspect()
        self.assertEqual(observed["status"],
                         "EXISTING_COMPLETE_NATIVE_POSTPROCESS_REPORT_REUSED_NO_NEW_RUN")
        self.assertEqual(observed["native_groups_failed"],["core"])
        self.assertFalse(observed["prior_report_false_positive_success_detected"])

    def test_partial_workcopy_no_final_report_preserved_and_not_marked_pass(self):
        self.report.unlink()
        state=self.inspect()
        self.assertEqual(state["status"],
                         "EXISTING_COPY_PARTIAL_OR_POSSIBLY_ACTIVE_PRESERVED")
        self.assertFalse(state["final_report_present"])
        self.assertTrue(state["per_group_logs"]["energy"]["present"])
        self.assertTrue(state["copy_10s_solver_log_SHA_matches"])
        self.assertTrue(state["can_prove_other_process_not_running"] is False)
        self.assertFalse(self.report.exists())

    def test_changed_native_group_log_invalidates_completed_report(self):
        original=sut.sha(self.report)
        logfile=self.copy/"log.C14_3D_postprocess_solverBacked_core"
        logfile.write_text(logfile.read_text()+"New divergent log evidence\n")
        state=self.inspect()
        self.assertEqual(state["status"],
                         "EXISTING_COPY_PARTIAL_OR_POSSIBLY_ACTIVE_PRESERVED")
        self.assertIn("provenance",state["reason"])
        self.assertEqual(sut.sha(self.report),original)

    def test_mismatched_source_authentication_is_not_accepted_as_complete(self):
        (self.case/"log.foamMultiRun").write_text("modified forbidden source\n")
        state=self.inspect()
        self.assertIn("authenticated original source",state["reason"])
        self.assertFalse(state.get("final_report_sha_verified",False))

    def test_symlink_or_directory_instead_of_regular_copy_blocks(self):
        alias=self.root/"unsafe_alias"
        alias.symlink_to(self.copy,target_is_directory=True)
        with self.assertRaisesRegex(sut.Blocked,"symlink"):
            sut.inspect_occupied_copy(self.case,alias,self.recovery,self.forensic)


class RealWSLFatalAndFullMetalZoneRegression(unittest.TestCase):
    """Disposable files reproduce the REAL C14 _02 F14 exit-zero fatal IO."""

    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.copy=self.root/"NEW_COPY_NOT_ORIGINAL_CFD"
        (self.copy/"system").mkdir(parents=True)

    def test_native_zero_exit_with_foam_fatal_io_never_counted_pass(self):
        dic=self.copy/"system/stage07Offline_core"
        dic.write_text("FoamFile {}")
        log=self.copy/"log.C14_3D_postprocess_solverBacked_core"
        def fake_native(case,name,args):
            log.write_text(
                "Time = 10s\n"
                "--> FOAM FATAL IO ERROR:\n"
                "Cannot find cellZone metal\n"
                "Available cellZones: 0()\n"
                "End\n")
            return {"name":name,"command_without_bootstrap":args,
                    "exit_code":0,"passed":True,"log":log.name}
        with mock.patch.object(sut.old,"run_native",side_effect=fake_native):
            result=sut.native_group(self.copy,"core",dic)
        self.assertEqual(result["exit_code"],0)
        self.assertTrue(result["os_exit_code_zero"])
        self.assertFalse(result["passed"])
        self.assertTrue(result["foam_fatal_present"])
        self.assertEqual(result["foam_fatal_occurrence_count"],1)
        self.assertTrue(sut.fatal_openfoam_log(log)["foam_fatal_present"])

    def test_full_metal_zone_materialized_only_in_separate_copy(self):
        source=self.root/"C14_ORIGINAL_IMMUTABLE_CFD"
        clone=self.copy
        for region in (source,clone):
            root=region/"constant/metal/polyMesh"
            root.mkdir(parents=True)
            for name in sut.stage.MESH:
                (root/name).write_text("Native source mesh element "+name+"\n")
        source_checksums={
            x:sut.sha(source/"constant/metal/polyMesh"/x)
            for x in sut.stage.MESH}
        # Use real Foundation14 cellZones formatter + exhaustive audit, but
        # replace only the mesh cell-count reader (not included in the fixture).
        with mock.patch.object(sut.stage,"region_cells",
                               return_value={"nCells":3}):
            item=sut.verify_or_add_metal_zone_in_new_copy(source,clone)
        self.assertTrue(item["added_to_copy_only"])
        self.assertTrue(item["geometry_connectivity_unchanged"])
        self.assertEqual(item["metal_cells"],3)
        self.assertFalse((source/"constant/metal/polyMesh/cellZones").exists())
        self.assertTrue(sut.stage.audit_existing_zone(
            clone/"constant/metal/polyMesh/cellZones",3))
        self.assertEqual(source_checksums,{
            x:sut.sha(source/"constant/metal/polyMesh"/x)
            for x in sut.stage.MESH})
        with mock.patch.object(sut.stage,"region_cells",
                               return_value={"nCells":3}):
            with self.assertRaisesRegex(sut.Blocked,"unexpected zone"):
                sut.verify_or_add_metal_zone_in_new_copy(source,clone)

    def test_existing_metal_zone_is_exactly_cloned_not_rewritten(self):
        source=self.root/"C14_ORIGINAL"
        for folder in (source,self.copy):
            root=folder/"constant/metal/polyMesh"
            root.mkdir(parents=True)
            for name in sut.stage.MESH:
                (root/name).write_text("fixture mesh "+name+"\n")
            (root/"cellZones").write_text(sut.stage.whole_region_zone(4))
        saved=sut.sha(self.copy/"constant/metal/polyMesh/cellZones")
        with mock.patch.object(sut.stage,"region_cells",
                               return_value={"nCells":4}):
            result=sut.verify_or_add_metal_zone_in_new_copy(source,self.copy)
        self.assertFalse(result["added_to_copy_only"])
        self.assertEqual(sut.sha(self.copy/"constant/metal/polyMesh/cellZones"),saved)


if __name__=="__main__":
    unittest.main()
