"""Transfer snapshots: no CFD, no remote writes."""
import hashlib
import tempfile
import unittest
from pathlib import Path
import transfer_campaign_200s as t

class Snapshots(unittest.TestCase):
    def fixture(self,p,compact=False):
        p.mkdir(parents=True)
        for rel,body in (("0/metal/T",b"initial"),("constant/metal/polyMesh/points",b"mesh"),("system/controlDict",b"compact" if compact else b"dense")):
            q=p/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(body)
        report={"case":"C14-3DA-200s","status":"PREPARED_COMPACT_NOT_RUN" if compact else "PREPARED_NOT_RUN",
                "solver_completed":False,"input_sha256":t.input_hashes(p),"geometry":"3DA","formulation":"C14"}
        if compact:report.update(source_input_sha256=t.read(p.parent.parent/"CAMPAIGN_200S_01"/p.name/t.REPORT)["input_sha256"],implementation_sha256="solver")
        t.dump(p/t.REPORT,report)
    def test_attempted_source_recovered_exactly(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);name="C14-3DA-200s"
            dense=base/t.DENSE.name/name;compact=base/t.COMPACT.name/name
            self.fixture(dense);self.fixture(compact,True)
            r=t.read(dense/t.REPORT);r.update(status="RUN_INCOMPLETE_PRESERVED",solver_completed=False);t.dump(dense/t.REPORT,r)
            (dense/"0/metal/T").write_bytes(b"changed")
            (dense/"0/metal/rho").write_bytes(b"generated")
            (dense/"log.foamMultiRun").write_bytes(b"runtime")
            (dense/"1").mkdir()
            old=t.sha(dense/t.REPORT)
            dst=base/"export"/t.DENSE.name/name
            a=t.snapshot_inputs(dense,dst,compact,name,False,"solver")
            self.assertEqual(a["status"],"PREPARED_NOT_RUN")
            self.assertEqual(a["transfer_snapshot"]["original_status"],"RUN_INCOMPLETE_PRESERVED")
            self.assertEqual(a["transfer_snapshot"]["recovered_exact_sha_inputs"],["0/metal/T"])
            self.assertEqual(t.input_hashes(dst),r["input_sha256"])
            self.assertFalse((dst/"1").exists())
            self.assertFalse((dst/"log.foamMultiRun").exists())
            self.assertEqual(t.sha(dense/t.REPORT),old)
            self.assertEqual((dense/"0/metal/T").read_bytes(),b"changed")
            c=t.snapshot_inputs(compact,base/"export"/t.COMPACT.name/name,dense,name,True,"solver")
            self.assertEqual(c["status"],"PREPARED_COMPACT_NOT_RUN")
            self.assertEqual(c["source_dense_report_sha256"],t.sha(dst/t.REPORT))
    def test_missing_exact_bytes_refused(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);name="C14-3DA-200s"
            a=base/t.DENSE.name/name;b=base/t.COMPACT.name/name
            self.fixture(a);self.fixture(b,True)
            (a/"0/metal/T").write_bytes(b"changed");(b/"0/metal/T").write_bytes(b"also changed")
            with self.assertRaisesRegex(RuntimeError,"original input SHA unavailable"):
                t.snapshot_inputs(a,base/"out",b,name,False,"solver")
if __name__=="__main__":unittest.main()
