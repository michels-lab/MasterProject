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
                         "METAL_SURFACE_POWER_101_STATES_DIAGNOSTIC")
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

    def test_missing_energy_table_is_reported_without_fabrication(self):
        result=sut.surface_energy_summary(self.newcopy)
        self.assertEqual(result["status"],
                         "NATIVE_SURFACE_POWER_TABLES_MISSING_OR_INCOMPATIBLE")
        self.assertFalse(result["global_energy_conservation_verified"])


if __name__=="__main__":
    unittest.main()
