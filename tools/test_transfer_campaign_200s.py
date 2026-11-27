"""Transfer snapshots: no CFD, no remote writes."""
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
import transfer_campaign_200s as t

class Snapshots(unittest.TestCase):
    def test_authorized_scope(self):
        self.assertEqual(t.RUN_ORDER,("C14-3DA-200s","C14-2D-200s","B14-2D-200s","C14-3DB-200s"))
        self.assertEqual(set(t.ORDER)-set(t.RUN_ORDER),set(t.EXCLUDED))
        self.assertEqual(len(t.ORDER),6)
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
    def test_linked_input_root_refused(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);case=base/"case";self.fixture(case)
            linked=base/"linked";linked.symlink_to(case,target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"unsafe root"):
                t.input_hashes(linked)
            (case/"system").rename(case/"original_system")
            (case/"system").symlink_to(case/"original_system",target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"symlink path"):
                t.input_hashes(case)
    def test_linked_nested_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);case=base/"case";self.fixture(case)
            (case/"0/metal").rename(case/"metal_saved")
            (case/"0/metal").symlink_to(case/"metal_saved",target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"symlink path"):
                t.checked_relative(case,"0/metal/T")
    def test_archive_rejects_internal_parent_link(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);dst=base/"out";dst.mkdir();(dst/"real").mkdir()
            (dst/"link").symlink_to(dst/"real",target_is_directory=True)
            archive=base/"archive.tar.gz"
            with tarfile.open(archive,"w:gz") as f:
                entry=tarfile.TarInfo("link/value");entry.size=1
                f.addfile(entry,io.BytesIO(b"x"))
            with self.assertRaisesRegex(RuntimeError,"symlink path"):
                t.extract(archive,dst)
            self.assertFalse((dst/"real/value").exists())
    def test_archive_accepts_regular_entries(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);dst=base/"out";dst.mkdir();archive=base/"archive.tar.gz"
            with tarfile.open(archive,"w:gz") as f:
                entry=tarfile.TarInfo("case/value");entry.size=1
                f.addfile(entry,io.BytesIO(b"x"))
            t.extract(archive,dst)
            self.assertEqual((dst/"case/value").read_bytes(),b"x")
    def test_existing_publication_requires_both_hashes_and_identity(self):
        with tempfile.TemporaryDirectory() as d:
            case=Path(d)/"C14-3DA-200s";self.fixture(case)
            log=case/"log.foamMultiRun";log.write_bytes(b"solver")
            m=dict(complete=True,kind="scientific_results",case=case.name,
                   final_time_s=200,solver_steps=200000,solver_log_sha256=t.sha(log),
                   report_sha256=t.sha(case/t.REPORT))
            t.verify_existing_result(m,case)
            with self.assertRaisesRegex(RuntimeError,"identity differs"):
                t.verify_existing_result(dict(m,case="wrong"),case)
            with self.assertRaisesRegex(RuntimeError,"report_sha256"):
                t.verify_existing_result(dict(m,report_sha256="wrong"),case)
    def test_preview_rejects_nonfinite_time(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);case=base/"case";self.fixture(case)
            probe=case/"postProcessing/metal/temperatureProbe/0/T"
            probe.parent.mkdir(parents=True);probe.write_text("nan 123\n")
            work=base/"work";work.mkdir()
            with self.assertRaisesRegex(RuntimeError,"nonfinite probe time"):
                t.preview(case,work)
if __name__=="__main__":unittest.main()
