"""Synthetic Git repositories, no external services, no simulation."""
import datetime as dt
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

tool=Path(__file__).with_name("file_governance_audit_proof.py")
spec=importlib.util.spec_from_file_location("proof",tool)
proof=importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)

class ProofTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        subprocess.run(["git","init","-q",str(self.root)],check=True)
        (self.root/"README.md").write_text("fixture\n")
        subprocess.run(["git","-C",str(self.root),"add","README.md"],check=True)
        subprocess.run(["git","-C",str(self.root),"-c","user.name=QA",
                        "-c","user.email=qa@example.invalid","commit","-qm","fixture"],check=True)
        self.head=proof.head_sha(self.root)
        out=self.root/"reports/file-governance"
        out.mkdir(parents=True)
        (out/"SUMMARY.json").write_text(json.dumps({
            "audit_kind":"deterministic_full_tracked_tree",
            "inventory_fingerprint":"a"*64,"finding_total":0
        }),encoding="utf-8")
        self.now=dt.datetime(2026,10,21,12,0,tzinfo=dt.timezone.utc)
        self.actions={"GITHUB_REPOSITORY":"michels-lab/MasterProject",
                      "GITHUB_SHA":self.head,"GITHUB_REF":"refs/heads/main",
                      "GITHUB_EVENT_NAME":"push","GITHUB_RUN_ID":"123",
                      "GITHUB_RUN_ATTEMPT":"1"}
    def test_exact_actions_run_bound_to_scanned_head(self):
        x=proof.produce(self.root,self.actions,self.now,require_actions=True)
        self.assertEqual(x["audited_head_sha"],self.head)
        self.assertEqual(x["workflow_run_id"],123)
        self.assertEqual(x["inventory_fingerprint"],"a"*64)
        self.assertEqual(x["evidence_state"],"ACTIONS_CLAIM_PENDING_EXTERNAL_VERIFICATION")
        self.assertNotIn("workflow_success",x)
    def test_missing_or_mismatched_actions_cannot_claim_verified(self):
        for change in ({"GITHUB_SHA":"b"*40},{"GITHUB_REF":"refs/heads/feature"},
                       {"GITHUB_RUN_ID":"0"},{"GITHUB_REPOSITORY":"other/private"},
                       {"GITHUB_EVENT_NAME":"pull_request"}):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    proof.produce(self.root,{**self.actions,**change},self.now,require_actions=True)
    def test_local_run_explicitly_unverified(self):
        x=proof.produce(self.root,{},self.now,require_actions=False)
        self.assertEqual(x["evidence_state"],"UNVERIFIED_LOCAL")
        self.assertIsNone(x["workflow_run_id"])
        self.assertNotIn("success",x)
    def test_invalid_or_missing_summary_fails(self):
        file=self.root/proof.SUMMARY
        file.write_text(json.dumps({"audit_kind":"deterministic_full_tracked_tree",
                                    "inventory_fingerprint":"malformed"}))
        with self.assertRaises(ValueError):
            proof.produce(self.root,self.actions,self.now,True)
        file.unlink()
        with self.assertRaises(FileNotFoundError):
            proof.produce(self.root,self.actions,self.now,True)
    def test_nonaaware_clock_fails(self):
        with self.assertRaises(ValueError):
            proof.produce(self.root,self.actions,dt.datetime(2026,10,21,12,0),True)
    def test_report_only_changes_cannot_change_claimed_source_head(self):
        (self.root/"README.md").write_text("new source\n")
        subprocess.run(["git","-C",str(self.root),"add","README.md"],check=True)
        subprocess.run(["git","-C",str(self.root),"-c","user.name=QA",
                        "-c","user.email=qa@example.invalid","commit","-qm","changed source"],check=True)
        with self.assertRaises(ValueError):
            proof.produce(self.root,self.actions,self.now,True)

if __name__=="__main__":
    unittest.main()
