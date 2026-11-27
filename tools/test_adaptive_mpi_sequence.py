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

    def test_manifest_requires_mode_and_evidence(self):
        m={"complete":True,"kind":"adaptive_scientific_results","case":mpi.CASES[0],
           "mpi_ranks":8,"max_co":.25,"max_dt_s":None,"time_mode":"adaptive_uncapped",
           "validation_class":mpi.experiment(None),"physical_validation":False,"final_time_s":200,
           "native_runtime_coverage_complete":True,"volume_fields_included":False,
           "solver_steps":15012,"solver_log_sha256":"a"*64,"report_sha256":"b"*64}
        mpi.check_manifest(m,mpi.CASES[0],8,None)
        for k,v in (("solver_steps",0),("max_dt_s",.025),("physical_validation",True),
                    ("report_sha256","bad"),("kind","inputs")):
            with self.subTest(k=k),self.assertRaises(RuntimeError):
                mpi.check_manifest({**m,k:v},mpi.CASES[0],8,None)
    def test_timeline_requires_every_native_step(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"log"
            p.write_text("nProcs : 8\nTime = 0.1s\nTime = 0.2s\nTime = 200s\nEnd\n")
            mpi.check_native_timeline(p,[.1,.2,200],8)
            for steps in ([.1,.3,200],[.1,200]):
                with self.assertRaises(RuntimeError):mpi.check_native_timeline(p,steps,8)
            with self.assertRaises(RuntimeError):mpi.check_native_timeline(p,[.1,.2,200],1)
    def test_linked_attempt_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);outside=p/"outside";outside.mkdir()
            parent=p/"attempt";parent.mkdir();case=parent/mpi.CASES[0]
            case.symlink_to(outside,target_is_directory=True)
            with patch.object(mpi,"ROOT",p),self.assertRaises(RuntimeError):mpi.checked_case(case)
    def test_recovery_reserve_before_moving(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);parent=p/"attempt";parent.mkdir();case=parent/mpi.CASES[0];case.mkdir()
            (case/"200").mkdir()
            (case/mpi.adaptive.TIMELINE).write_text("step,time_s\n1,200\n")
            (case/"log.foamMultiRun").write_text("nProcs : 8\nTime = 200s\nEnd\n")
            r={"solver_completed":True,"final_time_s":200,"observed_mpi_ranks":8,
               "max_dt_s":None,"solver_steps":1}
            with patch.object(mpi,"ROOT",p),patch.object(mpi.shutil,"disk_usage",return_value=type("Disk",(),{"free":0})()):
                with self.assertRaisesRegex(RuntimeError,"free space"):
                    mpi.recover_completed(case,r,8,None)
            self.assertTrue((case/"200").is_dir())
            self.assertEqual(list(parent.iterdir()),[case])

if __name__=="__main__":
    unittest.main()
