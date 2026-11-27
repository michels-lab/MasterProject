"""Synthetic lab guard regressions; no native commands, no process termination."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import finalize_lab_fixed_mpi8 as f
import run_lab_fixed_mpi8 as q
import run_lab_mpi8_fresh_timing as fresh
import resume_lab_mpi8_deadline as resume
import recover_lab_mpi_reference as ref

class LabIntegrity(unittest.TestCase):
    def test_takeover_requires_explicit_authorization(self):
        with patch.object(q,"old_processes",return_value=([99],[],[])),patch.object(q.os,"kill") as kill:
            with self.assertRaisesRegex(RuntimeError,"explicit"):q.terminate_old()
            kill.assert_not_called()
        active=[(99,["python","run_lab_serial_deadline.py"])]
        with patch.object(q,"procs",return_value=active),patch.object(fresh,"signal_stop") as kill:
            with self.assertRaisesRegex(RuntimeError,"explicit"):fresh.stop_previous()
            kill.assert_not_called()
        with patch.object(resume,"processes",return_value=active),patch.object(resume,"terminate") as kill:
            with self.assertRaisesRegex(RuntimeError,"explicit"):resume.stop_serial()
            kill.assert_not_called()
    def test_finalization_blocked_is_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/"out";out.mkdir();src=root/"src";src.mkdir()
            with patch.object(f,"OUT",out),patch.object(f,"SERIAL",src):
                with self.assertRaisesRegex(RuntimeError,"finalization incomplete"):
                    f.finish("unused",f.NAMES[:1],True)
                self.assertEqual(f.read(out/"FINALIZATION_STATUS.json")[f.NAMES[0]]["status"],"BLOCKED_PRESERVED")
    def test_report_temp_link_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);victim=root/"victim";victim.write_text("preserve")
            (root/".r.json.tmp").symlink_to(victim)
            q.save(root/"r.json",{"ok":True})
            self.assertEqual(victim.read_text(),"preserve")
            self.assertEqual(q.read(root/"r.json"),{"ok":True})
    def test_reference_failure_does_not_accept_linked_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);victim=root/"victim";victim.write_text("Unable to set reference cell for field p")
            (root/"log.foamMultiRun").symlink_to(victim)
            with self.assertRaises(RuntimeError):ref.ref_failure(root)
    def test_reference_coordinate_nonfinite_refused(self):
        with self.assertRaisesRegex(RuntimeError,"invalid reference"):
            ref.nearest_cell(Path("/unused"),(0,float("nan"),0),Path("/unused"))
    def test_fixed_time_grid_rejects_duplicate(self):
        self.assertTrue(f.complete_steps([.001,.002],0,.002))
        self.assertFalse(f.complete_steps([.001,.001],0,.002))

if __name__=="__main__":
    unittest.main()
