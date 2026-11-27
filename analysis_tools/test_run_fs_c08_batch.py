"""Software-only regression contracts for FS-C08 comparison eligibility."""
import csv
import tempfile
import unittest
from pathlib import Path
from run_fs_c08_batch import common_time_comparison
from run_fs_c08_real_cfd import comparison_ready_times, REQUIRED_FINAL_FIELDS


class ComparisonTests(unittest.TestCase):
    def row(self, root, name, dt, steps, records, ready):
        path = root / (name + ".csv")
        with path.open("w", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=(
                "time_s", "all_native_ledgers_present", "maxU_m_s"))
            writer.writeheader()
            for t in records:
                writer.writerow(dict(time_s=t, all_native_ledgers_present=True,
                                     maxU_m_s=1))
        return dict(variant=name, fixed_dt_s=dt, scheduled_steps=steps,
                    comparison_ready_times_s=ready, ledger_csv=str(path))

    def test_common_physical_times_not_step_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = self.row(root, "a", 1e-6, 2, [1e-6, 2e-6], [1e-6, 2e-6])
            b = self.row(root, "b", 5e-7, 4, [5e-7, 1e-6], [5e-7, 1e-6])
            got = common_time_comparison([a, b], 5e-7)
            self.assertEqual(len(got), 1)
            self.assertEqual(got[0]["actual_steps"], {"a": 1, "b": 2})

    def test_missing_native_gate_and_duplicate_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = self.row(Path(tmp), "a", 1e-6, 3,
                           [1e-6, 1e-6, 2e-6, 3e-6], [1e-6, 3e-6])
            got = common_time_comparison([row], 1e-6)
            self.assertEqual([x["comparison_tick"] for x in got], [3])

    def test_off_schedule_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = self.row(Path(tmp), "a", 1e-6, 1,
                           [5e-7, 1e-6, 2e-6], [5e-7, 1e-6, 2e-6])
            self.assertEqual(len(common_time_comparison([row], 5e-7)), 1)

    def test_duplicate_variant_rejected(self):
        with self.assertRaises(ValueError):
            common_time_comparison([{"variant": "a"}, {"variant": "a"}], 1e-6)

    def test_native_markers_and_fields_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "1e-6"
            fluid = directory / "fluid"
            fluid.mkdir(parents=True)
            for field in REQUIRED_FINAL_FIELDS:
                (fluid / field).touch()
            mass = "FS_C08_NATIVE_METAL_AND_GAS_CONSERVATION_GATES_PASSED time_s=1e-6"
            pressure = ("FS_C08_NATIVE_PRESSURE_WITH_MASS_DENSITY time_s=1e-6 "
                        "pressureVolumeEnergyIterationConverged=1")
            energy = "FS_C08_FINAL_COUPLED_ENERGY_AUDIT_PASS time_s=1e-6"
            log = "\n".join((mass, pressure))
            snapshots = [(1e-6, directory)]
            self.assertEqual(comparison_ready_times(log, snapshots, 1e-6), [1e-6])
            self.assertEqual(comparison_ready_times(log, snapshots, 1e-6, True), [])
            self.assertEqual(comparison_ready_times(log+"\n"+energy, snapshots, 1e-6, True), [1e-6])
            self.assertEqual(comparison_ready_times(log+"\n"+mass, snapshots, 1e-6), [])
            rejected=pressure.replace("Converged=1","Converged=0")
            self.assertEqual(comparison_ready_times(log+"\n"+rejected, snapshots, 1e-6), [])
            self.assertEqual(comparison_ready_times(log+"\n"+mass.replace("time_s=1e-6",""), snapshots, 1e-6), [])
            self.assertEqual(comparison_ready_times(log, snapshots+snapshots, 1e-6), [])
            (fluid / REQUIRED_FINAL_FIELDS[0]).unlink()
            self.assertEqual(comparison_ready_times(log, snapshots, 1e-6), [])


if __name__ == "__main__":
    unittest.main()
