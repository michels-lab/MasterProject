"""Queue control regression tests; no OpenFOAM or network execution."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run_adaptive_mpi_campaign as mpi

class TestSequence(unittest.TestCase):
    def test_branch_identity(self):
        self.assertNotEqual(mpi.result_branch("C14-3DB-200s",8,.025),
                            mpi.result_branch("C14-3DB-200s",8,None))
        self.assertEqual(mpi.cap_tag(.025),"0p025")
        self.assertEqual(mpi.cap_tag(None),"uncapped")
        self.assertEqual(len(set(mpi.CASES)),4)

    def test_sequence_order_and_failure_preservation(self):
        calls=[]
        def fake(name,url,ranks,max_dt):
            calls.append((name,ranks,max_dt))
            if name=="C14-3DA-200s" and max_dt is not None:
                raise RuntimeError("simulated failed pilot")
            return {"status":"PUBLISHED"}
        with tempfile.TemporaryDirectory() as root:
            with patch.object(mpi,"ROOT",Path(root)), patch.object(mpi,"run_queued_case",side_effect=fake):
                with self.assertRaises(RuntimeError):
                    mpi.sequence("unused",8)
                summary=mpi.read(Path(root)/"MPI_SEQUENCE_R8.json")
                self.assertEqual(summary["0p025"]["C14-3DA-200s"]["status"],"BLOCKED_OR_FAILED_PRESERVED")
                self.assertTrue(all(x["status"]=="PUBLISHED" for x in summary["uncapped"].values()))
        self.assertEqual(calls,[(name,8,dt) for dt in (.025,None) for name in mpi.CASES])

    def test_no_rerun_of_incomplete_full(self):
        with patch.object(mpi,"reports_for",return_value=[(Path("/preserved"),{"status":"MPI_ATTEMPT_PRESERVED"})]), \
             patch.object(mpi.transfer,"complete_manifest",return_value=None), \
             patch.object(mpi,"new_attempt") as run:
            result=mpi.run_queued_case("C14-3DA-200s","unused",8,None)
            self.assertEqual(result["status"],"FULL_ATTEMPT_PRESERVED")
            run.assert_not_called()

if __name__=="__main__":
    unittest.main()
