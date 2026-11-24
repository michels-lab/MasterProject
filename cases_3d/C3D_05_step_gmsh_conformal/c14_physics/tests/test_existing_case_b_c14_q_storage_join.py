#!/usr/bin/env python3
"""Synthetic 101-state C14 q/storage join tests, no CFD or actual q fabrication."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"compare_existing_case_b_c14_native_q_and_storage.py"
spec=importlib.util.spec_from_file_location("c3d05_B_q_storage_join",SCRIPT)
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def rows(n:int=101)->tuple[list[dict],list[dict]]:
    """UNIT TEST input only; no claim that it is the original native CFD."""
    q=[]
    storage=[]
    for i in range(n):
        t=round(i*.1,1)
        q.append({
            "time_s":str(t),
            "metal_to_mold_q_out_W":10.,
            "mold_to_metal_q_out_W":-10.,
            "interface_sum_outward_W":0.,
            "metalTop_q_out_W":2.,
            "moldOuterUnclassified_q_out_W":3.,
            "external_total_q_out_W":5.,
            "interface_relative_instantaneous_mismatch_over_gross":0.
        })
        storage.append({
            "time_s":str(t),
            "mold_sensible_change_from_t0_J":5*t,
            "metal_sensible_change_from_t0_J":-8*t,
            "metal_liquid_latent_content_change_from_t0_J":-2*t,
            "metal_latent_solid_equivalent_increase_from_t0_J":2*t,
            "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY":-5*t,
        })
    return q,storage


def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path:Path,items:list[dict])->None:
    with path.open("w",encoding="utf-8",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=list(items[0]))
        writer.writeheader()
        writer.writerows(items)


def write_fixture(root:Path)->tuple[Path,Path]:
    """Minimal SHA internally consistent original-style source archives.

    Source values are artificial and belong to unit tests ONLY.
    """
    qdir=root/M.QDIR.name
    storage=root/M.STORAGE.name
    qdir.mkdir()
    storage.mkdir()
    qq,ss=rows()
    write_csv(qdir/M.qr.TIMELINE,qq)
    write_csv(storage/M.s.CSV,ss)
    (qdir/M.qr.INTEGRALS).write_text("original-patch-fixture\n")
    (qdir/M.qr.LAST_FACES).write_text("original-face-fixture\n")
    original=root/"C3D05_B_C14_FLUID_SOLID_FULL_10S_01"
    original.mkdir()
    qreport={
        "status":M.qmod.STATUS,"stored_time_count":101,
        "native_patch_count":4,"native_interface_faces_each":12636,
        "real_fluid_and_solid_heat_conduction_q_computed":True,
        "overall_energy_conservation_verified":False,
        "native_latent_fvModel_source_integral":False,
        "per_face_geometry":{
            "interface_geometry_and_orientation_complete":True,
            "matched_rounded_centres_at_1e_8_m":12636,
            "matched_face_abs_power_sum_W":0.0,
        },
        "q_only_shadow_fvSchemes_provenance":{
            "explicit_shadow_only_scheme":"interpolate(kappa) harmonic;"
        },
        "signed_interface_sum_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL":0.,
        "signed_external_total_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL":50.,
        "first":qq[0],"final":qq[-1],
        "original_CFD_source_read_only":str(original)
    }
    sreport={
        "status":M.s.STATUS,"saved_states":101,
        "overall_sensible_latent_energy_conservation_verified":False,
        "metal_latent_liquid_content_delta_is_negative_solid_equivalent":True,
        "original_native_C14_run_readonly":str(original),
        "initial":ss[0],"final":ss[-1]
    }
    (qdir/M.qr.REPORT).write_text(json.dumps(qreport))
    (storage/M.s.JSON).write_text(json.dumps(sreport))
    (qdir/M.qr.MANIFEST).write_text(json.dumps({
        "original_CFD_stage_SHA256":"f"*64,
        "original_CFD_log_SHA256":"e"*64,
        "audited_report_SHA256":sha(qdir/M.qr.REPORT),
        "native_q_timeline_101_CSV_SHA256":sha(qdir/M.qr.TIMELINE),
        "native_integrated_101times_CSV_SHA256":sha(qdir/M.qr.INTEGRALS),
        "native_all_faces_t10_CSV_SHA256":sha(qdir/M.qr.LAST_FACES),
        "q_only_overlay_mold_fvSchemes_SHA256":"d"*64
    }))
    (storage/M.s.MANIFEST).write_text(json.dumps({
        "original_CFD_native_solver_report_SHA256":"f"*64,
        "original_CFD_native_solver_log_SHA256":"e"*64,
        "result_JSON_SHA256":sha(storage/M.s.JSON),
        "result_CSV_SHA256":sha(storage/M.s.CSV)
    }))
    return qdir,storage


class CaseBNativeQStorageJoinQA(unittest.TestCase):
    def test_synthetic_101_saved_time_integrals_and_signs_are_consistent(self):
        qq,ss=rows()
        result=M.analysis_rows(qq,ss)
        self.assertEqual(len(result),101)
        self.assertEqual(result[0][
            M.CUM_COLS["external_total_q_out_W"]],0)
        self.assertAlmostEqual(result[-1][
            M.CUM_COLS["external_total_q_out_W"]],50)
        self.assertAlmostEqual(result[-1][
            M.CUM_COLS["metal_to_mold_q_out_W"]],100)
        self.assertAlmostEqual(result[-1][
            M.CUM_COLS["mold_to_metal_q_out_W"]],-100)
        self.assertAlmostEqual(result[-1][
            M.CUM_COLS["interface_sum_outward_W"]],0)
        self.assertEqual(result[-1][
            "combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"],-50)
        self.assertAlmostEqual(result[-1][
            "reference_storage_change_plus_external_conduction_trapezoid_J_NOT_ENERGY_RESIDUAL"],0,places=10)

    def test_missing_time_rejected(self):
        qq,ss=rows()
        with self.assertRaisesRegex(ValueError,"101"):
            M.analysis_rows(qq[:-1],ss)

    def test_misaligned_times_rejected(self):
        qq,ss=rows()
        ss[50]["time_s"]="5.8"
        with self.assertRaisesRegex(ValueError,"time axis"):
            M.analysis_rows(qq,ss)

    def test_nan_conduction_rejected(self):
        qq,ss=rows()
        qq[9]["metalTop_q_out_W"]=math.nan
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            M.analysis_rows(qq,ss)

    def test_interface_outward_sign_gate_rejects_inconsistent_source(self):
        qq,ss=rows()
        qq[15]["interface_sum_outward_W"]=25
        with self.assertRaisesRegex(ValueError,"interface q sign"):
            M.analysis_rows(qq,ss)

    def test_external_q_gate_rejects_bad_source_aggregate(self):
        qq,ss=rows()
        qq[15]["external_total_q_out_W"]=14
        with self.assertRaisesRegex(ValueError,"exterior q"):
            M.analysis_rows(qq,ss)

    def test_latent_solid_plus_liquid_same_sign_is_rejected(self):
        qq,ss=rows()
        ss[88]["metal_liquid_latent_content_change_from_t0_J"]=18.
        ss[88]["combined_model_thermal_storage_change_from_t0_J_NOT_CLOSED_ENERGY"]=(
            ss[88]["mold_sensible_change_from_t0_J"]+
            ss[88]["metal_sensible_change_from_t0_J"]+18)
        with self.assertRaisesRegex(ValueError,"cannot be counted twice"):
            M.analysis_rows(qq,ss)

    def test_manifest_SHA_and_original_CFD_provenance_verified(self):
        with TemporaryDirectory() as path:
            q,st=write_fixture(Path(path))
            qr,sr,prov=M.verify_sources(q,st)
            self.assertEqual(len(qr),101)
            self.assertEqual(len(sr),101)
            self.assertEqual(prov["original_CFD_log_SHA256"],"e"*64)
            self.assertEqual(prov["native_q_10s_all_faces_SHA256"],
                             sha(q/M.qr.LAST_FACES))

    def test_tampered_native_q_CSV_is_refused(self):
        with TemporaryDirectory() as path:
            q,st=write_fixture(Path(path))
            with (q/M.qr.TIMELINE).open("a") as stream:
                stream.write("tampered\n")
            with self.assertRaisesRegex(ValueError,"SHA manifests mismatch"):
                M.verify_sources(q,st)

    def test_mismatched_original_CFD_hashes_are_refused(self):
        with TemporaryDirectory() as path:
            q,st=write_fixture(Path(path))
            m=st/M.s.MANIFEST
            data=json.loads(m.read_text())
            data["original_CFD_native_solver_log_SHA256"]="0"*64
            m.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"identical original"):
                M.verify_sources(q,st)

    def test_join_creates_new_SHA_audited_archives_without_touching_inputs(self):
        with TemporaryDirectory() as dirname:
            root=Path(dirname)
            q,st=write_fixture(root)
            original_sha=sha(q/M.qr.TIMELINE)
            st_sha=sha(st/M.s.CSV)
            result=root/M.OUTPUT.name
            report=M.run(q,st,result)
            self.assertEqual(report["status"],M.STATUS)
            self.assertEqual(report["original_saved_time_count"],101)
            self.assertFalse(report["valid_for_physically_calibrated_energy_conservation"])
            self.assertFalse(report["CFD_rerun"])
            self.assertAlmostEqual(
                report["outward_exterior_conduction_saved_trapezoid_J_NOT_SOLVER_DT"],
                50.)
            self.assertEqual(sha(q/M.qr.TIMELINE),original_sha)
            self.assertEqual(sha(st/M.s.CSV),st_sha)
            self.assertTrue((result/M.MANIFEST).is_file())
            self.assertTrue((result/M.JSON).is_file())
            self.assertTrue((result/M.CSV).is_file())
            with self.assertRaisesRegex(ValueError,"output exists"):
                M.run(q,st,result)

    def test_static_no_solver_and_no_unqualified_heat_loss_claim(self):
        source=SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run(",source)
        self.assertNotIn("foamMultiRun(",source)
        self.assertIn("NOT_ENERGY_RESIDUAL",source)
        self.assertIn('"fvModels_source_integral_native_0_001s_verified":False',source)
        self.assertIn('"external_radiation_convection_boundary_flux_terms_separately_verified":False',source)
        self.assertIn("all_original_archives_preserved",source)


if __name__=="__main__":
    unittest.main()
