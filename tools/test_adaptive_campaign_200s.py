"""Regression for unordered cadence entries, using compact campaign fixtures."""
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import compact_campaign_200s as compact
import run_adaptive_campaign_200s as adaptive
from test_compact_campaign_200s import TestCompact

class AdaptiveCadence(unittest.TestCase):
    def test_inverted_and_nonadjacent(self):
        old="topFlow\n{\n    writeInterval 100;\n    executeInterval 100;\n    log true;\n    writeControl timeStep;\n    executeControl timeStep;\n}\n"
        new,n=adaptive.convert_cadence(old,"functions")
        self.assertEqual(n,2)
        self.assertIn("writeInterval 0.1;",new)
        self.assertIn("executeControl adjustableRunTime;",new)
    def fixture(self,family,three=False):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            TestCompact().fixture(root,family,three)
            compact.config(root,"3DA" if three else "2D")
            f=root/"system/functions"
            probe=compact.blocks(f.read_text())["temperatureProbe"][2]
            m=root/"system/researchDiagnostics"
            momentum=compact.blocks(m.read_text())[compact.MOMENTUM][2]
            adaptive.adapt_dicts(root)
            self.assertEqual(probe,compact.blocks(f.read_text())["temperatureProbe"][2])
            self.assertEqual(momentum,compact.blocks(m.read_text())[compact.MOMENTUM][2])
            self.assertRegex(f.read_text(),r"writeControl\s+adjustableRunTime;")
            control=(root/"system/controlDict").read_text()
            self.assertNotRegex(control,r"(?m)^\s*maxDeltaT\s")
            self.assertRegex(control,r"adjustTimeStep\s+yes;")
            self.assertRegex(control,r"maxCo\s+0\.25;")
            for p in ("functions","researchDiagnostics","lineProfiles","compactNearTop")+ (("additional3DProfiles",) if three else ()):
                self.assertNotRegex((root/"system"/p).read_text(),r"(?m)^\s*(?:execute|write)Interval\s+100\s*;")
    def test_b14(self):self.fixture("B14")
    def test_c14(self):self.fixture("C14")
    def test_3da(self):self.fixture("C14",True)
class AdaptiveIntegrity(unittest.TestCase):
    def test_linked_case_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);outside=root/"outside";outside.mkdir()
            case=root/adaptive.ORDER[0];case.symlink_to(outside,target_is_directory=True)
            with patch.object(adaptive,"ROOT",root):
                with self.assertRaises(RuntimeError):adaptive.case_guard(case)
    def test_linked_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);case=root/adaptive.ORDER[0];case.mkdir()
            outside=root/"outside";outside.write_text("original")
            (case/adaptive.REPORT).symlink_to(outside)
            with patch.object(adaptive,"ROOT",root):
                with self.assertRaises(RuntimeError):adaptive.case_guard(case)
            self.assertEqual(outside.read_text(),"original")
    def test_canonical_profile_retry_preserves_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/"raw.xy";dst=root/"canonical.xy"
            src.write_text("# x T\n0 1500\n1 1490\n")
            adaptive.profile(src,["T"],dst)
            original=dst.read_bytes()
            self.assertEqual(adaptive.profile(src,["T"],dst),2)
            self.assertEqual(dst.read_bytes(),original)
            src.write_text("# x T\n0 1500\n1 1480\n")
            with self.assertRaises(RuntimeError):adaptive.profile(src,["T"],dst)
            self.assertEqual(dst.read_bytes(),original)
    def test_numeric_symlink_and_nonfinite_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"outside").mkdir()
            (root/"0.1").symlink_to(root/"outside",target_is_directory=True)
            with self.assertRaises(RuntimeError):adaptive.directories(root)
            (root/"0.1").unlink();(root/"nan").mkdir()
            with self.assertRaises(RuntimeError):adaptive.directories(root)
    def test_report_write_does_not_follow_legacy_tmp_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/"report.json";outside=root/"outside"
            outside.write_text("original");p.with_suffix(".tmp").symlink_to(outside)
            adaptive.dump(p,{"status":"ok"})
            self.assertEqual(adaptive.read(p),{"status":"ok"})
            self.assertEqual(outside.read_text(),"original")
    def test_remote_manifest_identity_not_just_log_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            case=Path(tmp)/adaptive.ORDER[0];case.mkdir()
            (case/"log.foamMultiRun").write_text("End\n")
            r={"solver_steps":12};adaptive.dump(case/adaptive.REPORT,r)
            m={"complete":True,"kind":"adaptive_scientific_results","case":case.name,
               "time_mode":"adaptive_uncapped","solver_steps":12,"final_time_s":200,
               "solver_log_sha256":adaptive.transfer.sha(case/"log.foamMultiRun"),
               "report_sha256":adaptive.transfer.sha(case/adaptive.REPORT),
               "native_runtime_coverage_complete":False,"volume_fields_included":False}
            adaptive.manifest_matches(m,case,r)
            for key,value in (("case","wrong"),("solver_steps",13),("report_sha256","wrong"),("time_mode","fixed")):
                with self.subTest(key=key),self.assertRaises(RuntimeError):
                    adaptive.manifest_matches({**m,key:value},case,r)

if __name__=="__main__":unittest.main()
