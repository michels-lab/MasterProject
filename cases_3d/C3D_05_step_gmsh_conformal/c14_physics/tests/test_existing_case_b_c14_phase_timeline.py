#!/usr/bin/env python3
"""Case B C14 original-native 101-state phase timeline: no-CFD negative QA."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "c3d05_b_existing_phase",HERE/"summarize_existing_case_b_c14_phase_timeline.py")
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def native_sample_rows():
    rows=[]
    for i in range(101):
        t=round(i/10,1)
        is_phase=i>=3
        row={
            "time_s":t,
            "metal_T_min_K":1500-t*13,
            "metal_T_mean_K":1500-t*6,
            "metal_T_max_K":1500-t*2,
            "mold_T_min_K":300+t,
            "mold_T_mean_K":300+2*t,
            "mold_T_max_K":300+3*t,
            "alpha1_min":0.0 if i>=50 else (.5 if is_phase else 1.0),
            "alpha1_mean":1-(.015*t if is_phase else 0),
            "alpha1_max":1,
            "alpha1_below_0_999_cells":100 if is_phase else 0,
            "metal_T_below_Tliq_cells":50 if is_phase else 0,
            "metal_T_below_Tsol_cells":5 if i>=60 else 0,
        }
        rows.append(row)
    return rows


class CaseBPhaseTimeline(unittest.TestCase):
    def setUp(self):
        self.rows=native_sample_rows()
        self.doc={
            "first_saved_alpha1_cell_below_0_999":{
                "first_observed_saved_time_s":0.3,
                "previous_saved_time_s":0.2,
                "cannot_infer_exact_onset_within_saved_interval":True},
            "original_C14_phase_parameters_reference":{
                "Tliq_K":1473,"Tsol_K":1423,"L_J_kg":270000},
            "max_saved_metal_Courant":0.267133,
            "saved_times_s":[r["time_s"] for r in self.rows],
            "initial_native_fields_unweighted":self.rows[0],
            "final_native_fields_unweighted":self.rows[-1],
            "status":S.base.STATUS,"saved_states":101,
            "native_CFD_solved_full_10s":True,
            "native_C14_solidificationMeltingSource_selected":True,
            "phase_field_mean_is_cell_based_unweighted":True,
            "JMatPro_QuickCup_physical_validation":False,
            "native_original_C14_metadata":{
                "metal_cells":92200,"mold_cells":178588}
        }

    def write_fixture(self,root):
        src=root/S.SOURCE.name
        src.mkdir()
        with (src/S.base.CSV).open("w",newline="",encoding="utf-8") as stream:
            writer=csv.DictWriter(stream,fieldnames=S.base.FIELDS)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({col:row.get(col,0) for col in S.base.FIELDS})
        (src/S.base.JSON).write_text(json.dumps(self.doc)+"\n",encoding="utf-8")
        (src/S.base.MANIFEST).write_text(json.dumps({
            "analysis_csv_sha256":S.sha(src/S.base.CSV),
            "analysis_json_sha256":S.sha(src/S.base.JSON)
        })+"\n",encoding="utf-8")
        return src

    def test_source_101_native_saved_times_and_hash_integrity(self):
        with TemporaryDirectory() as folder:
            src=self.write_fixture(Path(folder))
            rows,doc,hashes=S.load_native(src)
            self.assertEqual(len(rows),101)
            self.assertEqual(rows[-1]["time_s"],10)
            self.assertEqual(doc["status"],S.base.STATUS)
            self.assertEqual(hashes["csv_sha256"],S.sha(src/S.base.CSV))

    def test_original_saved_time_brackets_not_precise_solidification_instant(self):
        out,rates=S.describe(self.rows,self.doc)
        e=out["first_observed_events_only_bracketed_by_saved_states"]
        self.assertEqual(e["first_any_cell_alpha1_below_0_999"]["first_saved_s"],0.3)
        self.assertEqual(e["first_any_cell_alpha1_below_0_999"]["previous_saved_s"],0.2)
        self.assertTrue(e["first_any_cell_alpha1_below_0_999"]["exact_onset_unknown"])
        self.assertEqual(e["first_any_cell_alpha1_zero"]["first_saved_s"],5.0)
        self.assertEqual(len(rates),100)

    def test_solid_complement_is_not_reported_as_mass_volume_solid(self):
        out,rates=S.describe(self.rows,self.doc)
        self.assertAlmostEqual(out["one_minus_alpha1_final_unweighted_cell_mean"],0.15)
        self.assertTrue(out["saved_snapshots"]==101)
        for key in ("physical_volume_weighted_fraction_verified",
                    "latent_heat_energy_and_interface_flux_verified",
                    "QuickCup_JMatPro_validation","grid_time_convergence",
                    "contraction_feeding_verified"):
            self.assertIs(out[key],False,key)
        self.assertEqual(out["max_Courant_over_original_full_native_log"],0.267133)

    def test_checksum_tamper_is_rejected(self):
        with TemporaryDirectory() as folder:
            src=self.write_fixture(Path(folder))
            with (src/S.base.CSV).open("a",encoding="utf-8") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(ValueError,"SHA mismatch"):
                S.load_native(src)

    def test_uncompleted_native_case_is_rejected(self):
        with TemporaryDirectory() as folder:
            src=self.write_fixture(Path(folder))
            self.doc["native_CFD_solved_full_10s"]=False
            (src/S.base.JSON).write_text(json.dumps(self.doc)+"\n")
            manifest=json.loads((src/S.base.MANIFEST).read_text())
            manifest["analysis_json_sha256"]=S.sha(src/S.base.JSON)
            (src/S.base.MANIFEST).write_text(json.dumps(manifest)+"\n")
            with self.assertRaisesRegex(ValueError,"not completed C14"):
                S.load_native(src)

    def test_wrong_time_grid_is_rejected(self):
        rows=native_sample_rows()
        rows[-1]["time_s"]=9.9
        with self.assertRaisesRegex(ValueError,"invalid real native 101"):
            S.describe(rows,self.doc)

    def test_altered_source_onset_cannot_silently_pass(self):
        changed=dict(self.doc)
        changed["first_saved_alpha1_cell_below_0_999"]={
            "first_observed_saved_time_s":0.5,"previous_saved_time_s":0.4}
        with self.assertRaisesRegex(ValueError,"disagrees"):
            S.describe(self.rows,changed)

    def test_new_separate_output_only_and_source_preserved(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            src=self.write_fixture(root)
            source_before=S.sha(src/S.base.CSV)
            out=root/"timeline"
            result=S.execute(src,out)
            self.assertEqual(result["saved_snapshots"],101)
            self.assertTrue((out/S.NAME).is_file())
            self.assertTrue((out/S.RATES).is_file())
            self.assertEqual(S.sha(src/S.base.CSV),source_before)
            with self.assertRaisesRegex(ValueError,"existing analysis preserved"):
                S.execute(src,out)
            with self.assertRaisesRegex(ValueError,"do not write within"):
                S.execute(src,src/"nested")

    def test_no_solver_execution_or_mesh_changes(self):
        code=(HERE/"summarize_existing_case_b_c14_phase_timeline.py").read_text()
        self.assertNotIn("subprocess.",code)
        self.assertNotIn("foamMultiRun(",code)
        self.assertNotIn("blockMesh",code)
        self.assertNotIn("gmshToFoam",code)
        self.assertIn("analysis_csv_sha256",code)
        self.assertIn("first_any_cell_alpha1_zero",code)


if __name__=="__main__":
    unittest.main()
