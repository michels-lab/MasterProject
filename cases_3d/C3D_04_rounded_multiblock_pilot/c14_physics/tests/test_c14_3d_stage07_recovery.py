#!/usr/bin/env python3
"""No investigator WSL files: genuine temporary Python volume audit fixtures."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "recover_existing_c14_3d_stage07",ROOT/"recover_existing_c14_3d_stage07.py")
assert spec and spec.loader
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def evidence(root:Path):
    case=root/"ORIGINAL_10S_NEVER_MUTATED"
    (case/"system").mkdir(parents=True)
    (case/"system/controlDict").write_text("C14 controlDict exact fixture\n")
    (case/"log.foamMultiRun").write_text("Time = 10s\nEnd\n")
    c14=root/"CANONICAL_C14"
    (c14/"system").mkdir(parents=True)
    (c14/"system/controlDict").write_bytes((case/"system/controlDict").read_bytes())
    vol=root/"VOL_101_STATES"
    vol.mkdir()
    contract=root/"C14_contract.json"
    contract.write_text(json.dumps({"C14_exact_values":{
        "metal":{"rho_kg_m3":6820},
        "solidification":{"L_J_kg":228600},
        "numerics":{"deltaT_s":0.001},
    }}))
    metal_vol=0.000048
    mold_vol=0.0001
    fields=list(module.INPUTS)
    with (vol/module.CSV_IN).open("w",encoding="utf-8",newline="") as fd:
        writer=csv.DictWriter(fd,fieldnames=fields)
        writer.writeheader()
        for i in range(101):
            a=1.0-i*0.002 if i>=5 else 1.0
            latent=-(1-a)*metal_vol*6820*228600
            metalE=-100*i
            moldE=20*i
            liq=25.0 if i>=10 else 0.0
            sol=5.0 if i>=90 else 0.0
            row={
              "time_s":i*0.1,
              "metal_volume_m3":metal_vol,
              "mold_volume_m3":mold_vol,
              "metal_T_volMean_K":1500-i*0.5,
              "mold_T_volMean_K":300+i*0.1,
              "metal_alpha1_volMean":a,
              "metal_solid_fraction_volMean":1-a,
              "metal_below_Tliq_volume_percent":liq,
              "metal_below_Tsol_volume_percent":sol,
              "metal_mean_speed_m_s":0.01,
              "metal_max_speed_m_s":0.025,
              "metal_sensible_delta_J":metalE,
              "metal_latent_inventory_delta_J":latent,
              "mold_sensible_delta_J":moldE,
              "combined_estimated_stored_energy_delta_J":metalE+latent+moldE,
            }
            writer.writerow(row)
    (vol/module.JSON_IN).write_text(json.dumps({
        "schema":"C3D04_A_C14_3D_POSTPROCESS_VOLUME_PARITY_V1",
        "CFD_rerun":False,"energy_conservation_verified":False,
        "source_case_read_only":str(case),
        "native_log_sha256":sha(case/"log.foamMultiRun"),
        "metal_volume_m3":metal_vol,"mold_volume_m3":mold_vol,
        "metal_total_mass_kg":metal_vol*6820,
        "peak_solver_final_residual_with_time":{
            "h":{"final_residual_max":0.00001,"time_s":0.1},
            "e":{"final_residual_max":0.00002,"time_s":0.2},
            "p_rgh":{"final_residual_max":0.0077,"time_s":0.8},
        }
    }))
    copy=root/"EXISTING_NATIVE_WORKCOPY"
    (copy/"system").mkdir(parents=True)
    (copy/"system/controlDict").write_bytes((case/"system/controlDict").read_bytes())
    (copy/"log.foamMultiRun").write_bytes((case/"log.foamMultiRun").read_bytes())
    (copy/"log.C14_3D_postprocess_c14_functions").write_text(
        "FOAM FATAL ERROR: missing input field\n")
    return case,c14,vol,copy,contract


class GenuineSavedVolumeRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.case,self.c14,self.vol,self.copy,self.contract=evidence(self.root)
        self.orig_c14,self.orig_contract=module.C14,module.CONTRACT
        module.C14,module.CONTRACT=self.c14,self.contract
        self.addCleanup(self.restore)
    def restore(self):
        module.C14,module.CONTRACT=self.orig_c14,self.orig_contract

    def test_101_saved_states_derivatives_onset_bounds_and_original_input_immutability(self):
        sourcehashes=[sha(self.case/"log.foamMultiRun"),
                      sha(self.vol/module.CSV_IN),
                      sha(self.copy/"log.C14_3D_postprocess_c14_functions")]
        report,rows=module.evaluate(self.case,self.vol,self.copy)
        self.assertEqual(len(rows),101)
        self.assertEqual(report["stage"],"7/10")
        self.assertEqual(report["milestones_done"],"6/10")
        k=report["kinetics"]
        self.assertAlmostEqual(k["final"]["metal_T_volMean_K"],1450)
        self.assertAlmostEqual(k["final"]["metal_alpha1_volMean"],0.8)
        self.assertAlmostEqual(
            k["peak_saved_interval_metal_cooling_K_s"]["value"],5.0)
        self.assertEqual(k["first_saved_below_liquidus"]["first_saved_time_s"],1.0)
        self.assertAlmostEqual(
            k["first_saved_below_liquidus"]["last_saved_time_before_event_s"],0.9)
        self.assertEqual(k["first_saved_below_solidus"]["first_saved_time_s"],9.0)
        self.assertEqual(k["first_saved_alpha1_decrease"]["first_saved_time_s"],0.5)
        self.assertFalse(k["first_saved_alpha1_decrease"]["exact_physical_onset_known"])
        self.assertFalse(report["global_energy_conservation_verified"])
        self.assertFalse(report["native_postprocess_existing_inspection"]["verified_native_success"])
        self.assertEqual(report["native_postprocess_existing_inspection"]["status"],
                         "COPY_VALID_NATIVE_REPORT_NOT_YET_WRITTEN")
        self.assertEqual(sourcehashes,[
            sha(self.case/"log.foamMultiRun"),
            sha(self.vol/module.CSV_IN),
            sha(self.copy/"log.C14_3D_postprocess_c14_functions"),
        ])
        dest=self.root/"BRAND_NEW_OUTPUT"
        first=module.publish(report,rows,dest)
        self.assertEqual(first,"NEW_101_STATE_DIAGNOSTIC_PUBLISHED_NO_CFD")
        self.assertEqual(len(list(csv.DictReader((dest/module.CSV_OUT).open()))),101)
        exported=sha(dest/module.JSON_OUT)
        self.assertEqual(module.publish(report,rows,dest),
                         "EXISTING_SOURCE_MATCHED_DIAGNOSTIC_PRESERVED_NO_OVERWRITE")
        self.assertEqual(sha(dest/module.JSON_OUT),exported)
        self.assertEqual(sourcehashes,[
            sha(self.case/"log.foamMultiRun"),
            sha(self.vol/module.CSV_IN),
            sha(self.copy/"log.C14_3D_postprocess_c14_functions"),
        ])

    def test_existing_copy_missing_or_partial_is_explicit_not_native_pass(self):
        report,_=module.evaluate(self.case,self.vol,self.copy)
        self.assertTrue(report["native_postprocess_existing_inspection"][
            "log_inspection"]["c14_functions"]["present"])
        self.assertFalse(report["native_postprocess_existing_inspection"][
            "log_inspection"]["c14_functions"]["exit_code_recoverable_from_log"])
        # Even if a prior output contains a fabricated PASS, source hashes gate it.
        (self.copy/module.NATIVE).write_text(json.dumps({
            "source_log_sha256":"WRONG_HASH",
            "original_CFD_read_only":str(self.case),
            "all_native_processing_commands_passed":True,
            "missing_expected_C14_object_dirs":[],
            "missing_derived_C14_fields_at_final_time":[],
            "incomplete_profiles_at_t10":[],
        }))
        report,_=module.evaluate(self.case,self.vol,self.copy)
        self.assertFalse(report["native_postprocess_existing_inspection"][
            "verified_native_success"])
        self.assertEqual(report["native_postprocess_existing_inspection"]["status"],
                         "UNTRUSTED_NATIVE_REPORT")

    def test_corrupt_csv_or_divergent_log_fail_closed(self):
        data=(self.vol/module.CSV_IN).read_text()
        (self.vol/module.CSV_IN).write_text(data.replace("0.0,", "nan,", 1))
        with self.assertRaisesRegex(module.Blocked,"nonfinite|unexpected recorded time"):
            module.evaluate(self.case,self.vol,self.copy)
        (self.vol/module.CSV_IN).write_text(data)
        (self.case/"log.foamMultiRun").write_text("changed original CFD\n")
        with self.assertRaisesRegex(module.Blocked,"hashes disagree"):
            module.evaluate(self.case,self.vol,self.copy)
        self.assertFalse((self.root/"BRAND_NEW_OUTPUT").exists())

    def test_existing_output_blocks_overwrite_when_provenance_changes(self):
        report,rows=module.evaluate(self.case,self.vol,self.copy)
        dest=self.root/"SAVED_DIAGNOSTIC"
        module.publish(report,rows,dest)
        original=sha(dest/module.JSON_OUT)
        fake={**report,"source_sha256":{**report["source_sha256"],
                                      "source_CFD_log_sha256":"NEW"}}
        with self.assertRaisesRegex(module.Blocked,"incompatible"):
            module.publish(fake,rows,dest)
        self.assertEqual(sha(dest/module.JSON_OUT),original)

    def test_new_native_log_after_publication_requires_new_output(self):
        report,rows=module.evaluate(self.case,self.vol,self.copy)
        dest=self.root/"RECOVERY_ALREADY_PUBLISHED"
        module.publish(report,rows,dest)
        fingerprint=sha(dest/module.JSON_OUT)
        (self.copy/"log.C14_3D_postprocess_momentum").write_text(
            "new downstream native postprocessing evidence\\n".replace("\\n","\n"))
        updated,newrows=module.evaluate(self.case,self.vol,self.copy)
        with self.assertRaisesRegex(module.Blocked,"incompatible"):
            module.publish(updated,newrows,dest)
        self.assertEqual(sha(dest/module.JSON_OUT),fingerprint)
        newdir=self.root/"RECOVERY_NEXT_IMMUTABLE_VERSION"
        self.assertEqual(
            module.publish(updated,newrows,newdir),
            "NEW_101_STATE_DIAGNOSTIC_PUBLISHED_NO_CFD")

    def test_never_create_within_existing_cfd_or_workcopy(self):
        report,rows=module.evaluate(self.case,self.vol,self.copy)
        for target in (self.case/"newreport",self.vol/"newreport",
                       self.copy/"newreport"):
            with self.assertRaisesRegex(module.Blocked,"overlaps"):
                module.publish(report,rows,target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
