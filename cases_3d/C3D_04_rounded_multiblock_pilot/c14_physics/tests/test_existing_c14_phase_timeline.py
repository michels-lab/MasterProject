#!/usr/bin/env python3
"""No-CFD regression tests for time-series derived C14 phase evolution."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import summarize_existing_c14_phase_timeline as phase


def fixtures(directory:Path)->tuple[Path,Path]:
    csv_file=directory/phase.CSV
    json_file=directory/phase.JSON
    headers=[
        "time_s","metal_T_min_K","metal_T_mean_K","metal_T_max_K",
        "mold_T_min_K","mold_T_mean_K","mold_T_max_K",
        "metal_below_Tliq_cells","metal_below_Tsol_cells",
        "metal_alpha1_min","metal_alpha1_mean","metal_alpha1_max",
        "metal_alpha1_below_0_999_cells",
        "metal_p_rgh_min_Pa","metal_p_rgh_mean_Pa","metal_p_rgh_max_Pa",
    ]
    records=[
        [0,1500,1500,1500,300,300,300,0,0,1,1,1,0,100000,100000,100000],
        [0.1,1460,1470,1490,300,305,310,100,0,0.8,0.97,1,100,99999,100000,100001],
        [10,1401.91,1444.7184787946428,1471.07,300.006,
         531.3307448186529,918.764,8960,1158,0,
         0.8367355017427456,0.992311,8960,99999.8,99999.91190848213,100000],
    ]
    with csv_file.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(records)
    json_file.write_text(json.dumps({
        "status":phase.AUDITED_STATUS,
        "source_mesh_cells":{"metal":8960,"mold":12352},
        "F14_native_log":{"time_last_s":10,
                          "courant_max_over_all_logged_steps":0.0240415},
        "NOT_A_NEW_CFD":True,"energy_balance_verified":False,
        "time_states_count":len(records),
        "source_case_read_only":"/read-only/existing/C14/V4T02",
        "output_analysis_separate":str(directory),
    }),encoding="utf-8")
    return csv_file,json_file


class PhaseTimelineFromExistingPostrunTests(unittest.TestCase):
    def test_saved_event_ranges_and_unweighted_fraction(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path,meta=fixtures(Path(d))
            rows,source=phase.parse_existing(csv_path,meta)
            out=phase.summarize(rows,source)
            self.assertEqual(len(out["interval_rates"]),2)
            self.assertEqual(out["first_saved_metal_below_liquidus"],
                             {"first_saved_time_s":0.1,
                              "previous_saved_time_s":0.0,
                              "interpretation":"FIRST_SAVED_SNAPSHOT_ONLY_NOT_EXACT_PHYSICAL_ONSET"})
            self.assertEqual(out["first_saved_metal_below_solidus"]["first_saved_time_s"],10)
            self.assertEqual(out["last_metal_below_Tsol_cells"],1158)
            self.assertEqual(out["last_metal_below_Tliq_cells"],8960)
            self.assertAlmostEqual(out["last_mean_one_minus_alpha1_unweighted"],
                                   0.1632644982572544)
            self.assertEqual(out["native_log_Courant_max_all_steps"],0.0240415)
            self.assertFalse(out["energy_balance_verified"])
            self.assertFalse(out["volume_weighting"])
            self.assertFalse(out["physical_validation"])

    def test_bad_native_data_and_wrong_science_source_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path,meta=fixtures(Path(d))
            records=csv_path.read_text()
            meta_obj=json.loads(meta.read_text())
            meta_obj["source_mesh_cells"]["metal"]=27
            meta.write_text(json.dumps(meta_obj))
            with self.assertRaisesRegex(ValueError,"wrong source mesh"):
                phase.parse_existing(csv_path,meta)
            meta_obj["source_mesh_cells"]["metal"]=8960
            meta.write_text(json.dumps(meta_obj))
            csv_path.write_text(records.replace("0.8367355017427456","1.25"))
            with self.assertRaisesRegex(ValueError,"fraction outside"):
                phase.parse_existing(csv_path,meta)
            csv_path.write_text(records.replace("8960,1158","500,1158"))
            with self.assertRaisesRegex(ValueError,"solidus"):
                phase.parse_existing(csv_path,meta)
            csv_path.write_text(records)
            rows,source=phase.parse_existing(csv_path,meta)
            rows[0]["metal_T_min_K"]=1000
            with self.assertRaisesRegex(ValueError,"initial metal"):
                phase.summarize(rows,source)


if __name__=="__main__":
    unittest.main()
