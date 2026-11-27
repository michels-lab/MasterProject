#!/usr/bin/env python3
"""Offline consistency guard. No GitHub requests, solver or binary validation."""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
HEX40=re.compile(r"[0-9a-f]{40}")
HEX64=re.compile(r"[0-9a-f]{64}")

def read(name):
    return json.loads((ROOT/"docs"/name).read_text())

def validate(index, state, a, b):
    results=[x for x in index["branches"] if x.get("complete") is True and
             x.get("kind") in ("adaptive_scientific_results","fixed_lab_scientific_results")]
    assert all(HEX40.fullmatch(x.get("sha","")) and HEX40.fullmatch(x.get("manifest_blob_sha","")) for x in results), "missing immutable result pin"
    assert len({x["sha"] for x in results})==len(results), "duplicate pinned results"
    fixed=[x for x in results if x["kind"]=="fixed_lab_scientific_results"]
    lab=state["fixed_lab"]
    assert len(fixed)==lab["confirmed_manifest_count"], "fixed manifest count drift"
    assert set(x["case"].removesuffix("-200s") for x in fixed)==set(lab["published_cases"]), "fixed case set drift"
    assert sum(x["part_count"] for x in fixed)==lab["archive_part_count"], "part count drift"
    assert sum(x["archive_bytes"] for x in fixed)==lab["archive_bytes_total"], "archive byte count drift"
    assert sum(x["solver_steps"] for x in fixed)==lab["total_solver_steps"], "step count drift"
    for e in fixed:
        assert e["native_runtime_coverage_complete"] is True and e["physical_validation"] is False
        assert e["volume_fields_included"] is False and e["final_time_s"]==lab["final_time_s"]
        assert e["deltaT_s"]==lab["deltaT_s"] and HEX64.fullmatch(e["archive_sha256"])
    by_case={e["case"]:e for e in fixed}
    for key,case,owner in (("case_A","C14-3DA-200s",a["campaign_200s_update_20261127"]["fixed_lab"]),
                           ("case_B","C14-3DB-200s",b["current_campaign_state"]["fixed_lab"])):
        e=by_case[case]
        assert state[key]["fixed_lab_manifest_verified"] is True
        assert state[key]["fixed_lab_manifest_commit"]==owner["manifest_commit"]==e["sha"]
        assert owner["manifest_verified"] is True and owner["manifest_blob_sha"]==e["manifest_blob_sha"]
        assert owner["physical_validation"] is False

class Consistency(unittest.TestCase):
    def setUp(self):
        self.index=read("MAESTRIA_RESULT_MANIFEST_INDEX_20261127.json")
        self.state=read("MAESTRIA_STATUS.json")
        self.a=read("C3D04_CASE_A_STATUS.json")
        self.b=read("PROJECT_STAGE_STATUS.json")
    def check(self):
        validate(self.index,self.state,self.a,self.b)
    def test_current_records(self):
        self.check()
    def test_missing_pin_rejected(self):
        next(e for e in self.index["branches"] if e.get("kind")=="fixed_lab_scientific_results").pop("sha")
        with self.assertRaisesRegex(AssertionError,"missing immutable"):
            self.check()
    def test_case_state_drift_rejected(self):
        self.state["case_A"]["fixed_lab_manifest_verified"]=False
        with self.assertRaises(AssertionError):
            self.check()
    def test_archive_count_drift_rejected(self):
        self.state["fixed_lab"]["archive_part_count"]+=1
        with self.assertRaisesRegex(AssertionError,"part count"):
            self.check()

if __name__=="__main__":
    unittest.main()
