"""Audit expected schedule independently of native CFD."""
import tempfile
from pathlib import Path
import unittest
from run_fs_c08_real_cfd import inspect_fixed_probe_schedule, REQUIRED_FINAL_FIELDS

class ProbeScheduleTest(unittest.TestCase):
    def test_all_steps_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            snaps=[]
            lines=[]
            for i in (1,2):
                t=i*1e-6
                d=Path(tmp)/str(t)
                (d/"fluid").mkdir(parents=True)
                for field in REQUIRED_FINAL_FIELDS:
                    (d/"fluid"/(field+".gz")).touch()
                snaps.append((t,d))
                for marker in ("FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY",
                    "FS_C08_REAL_CFD_MASS_BUDGET",
                    "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED",
                    "FS_C08_NATIVE_PHASE_RESOLVED_INTERNAL_ENERGY"):
                    lines.append(f"{marker} time_s={t}")
            log="\n".join(lines)
            self.assertEqual(inspect_fixed_probe_schedule(log,snaps,1e-6,2)["verified_steps"],2)
            with self.assertRaises(ValueError):
                inspect_fixed_probe_schedule(log,snaps[1:],1e-6,2)
            with self.assertRaises(ValueError):
                inspect_fixed_probe_schedule("\n".join(lines[1:]),snaps,1e-6,2)
            (snaps[0][1]/"fluid"/(REQUIRED_FINAL_FIELDS[0]+".gz")).unlink()
            with self.assertRaises(ValueError):
                inspect_fixed_probe_schedule(log,snaps,1e-6,2)

if __name__ == "__main__":
    unittest.main()
