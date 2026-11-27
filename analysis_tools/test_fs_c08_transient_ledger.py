"""Synthetic parser regression only; not a CFD or material validation."""
import tempfile
import unittest
from pathlib import Path
from fs_c08_transient_ledger import extract, write_transient_ledger, MARKERS, REQUIRED

def log_at(t, skip=None):
    lines=[]
    for marker,kind in MARKERS.items():
        if kind==skip:
            continue
        fields={key: 1.0 for key in REQUIRED[kind]}
        if kind=="state":
            fields.update(dt_s=1e-6,liquidMass_kg=2.0,solidMass_kg=1.0,
                          liquidVolume_m3=2e-4,solidVolume_m3=1e-4,
                          gasVolume_m3=7e-4,domainVolume_m3=1e-3)
        if kind=="budget":
            fields.update(liquidSolidMetalMass_kg=3.0,previousMetalMass_kg=3.0)
        lines.append(marker+" time_s="+str(t)+" "+
                     " ".join(f"{k}={v}" for k,v in fields.items()))
    return "\n".join(lines)

class LedgerTest(unittest.TestCase):
    def test_complete(self):
        rows,issues=extract(log_at(1e-6)+"\n"+log_at(2e-6))
        self.assertFalse(issues)
        self.assertEqual(len(rows),2)
        self.assertAlmostEqual(rows[0]["volumeClosure_m3"],0)
        self.assertAlmostEqual(rows[0]["solidMassFraction"],1/3)
        self.assertEqual(rows[1]["metalHistoryMismatch_kg"],0)
    def test_partial_and_nonfinite(self):
        rows,issues=extract(log_at(1e-6,skip="energy"))
        self.assertFalse(rows[0]["all_native_ledgers_present"])
        self.assertTrue(issues)
        _,issues=extract(log_at(1e-6).replace("Tmin_K=1.0","Tmin_K=nan"))
        self.assertTrue(issues)
    def test_csv_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            report=write_transient_ledger(log_at(1e-6),Path(tmp))
            self.assertEqual(report["complete_native_ledger_times"],1)
            self.assertFalse(report["global_energy_verified"])
            self.assertTrue((Path(tmp)/"FS_C08_TRANSIENT_LEDGER.csv").is_file())

    def test_duplicate_marker_is_not_complete(self):
        log = log_at(1e-6)
        rows, issues = extract(log + "\n" + log.splitlines()[0])
        self.assertFalse(rows[0]["all_native_ledgers_present"])
        self.assertTrue(any("duplicate state" in x for x in issues))

    def test_unconverged_pressure_is_not_complete(self):
        rows, issues = extract(log_at(1e-6).replace(
            "pressureVolumeEnergyIterationConverged=1.0",
            "pressureVolumeEnergyIterationConverged=0.0"))
        self.assertFalse(rows[0]["all_native_ledgers_present"])
        self.assertTrue(any("pressure closure not converged" in x for x in issues))

    def test_history_not_compared_across_incomplete_time(self):
        rows, issues = extract("\n".join((
            log_at(1e-6), log_at(2e-6, skip="energy"), log_at(3e-6))))
        self.assertFalse(rows[1]["all_native_ledgers_present"])
        self.assertTrue(rows[2]["all_native_ledgers_present"])
        self.assertNotIn("metalHistoryMismatch_kg", rows[2])

    def test_history_not_compared_across_missing_time(self):
        rows,issues=extract(log_at(1e-6)+"\n"+log_at(3e-6))
        self.assertTrue(rows[1]["all_native_ledgers_present"])
        self.assertNotIn("metalHistoryMismatch_kg",rows[1])
        self.assertTrue(any("noncontiguous native history" in x for x in issues))

    def test_invalid_only_time_retained(self):
        bad="FS_C08_ACCEPTED_STATE_LEDGER time_s=2e-6 dt_s=nan"
        rows,issues=extract("\n".join((log_at(1e-6),bad,log_at(3e-6))))
        self.assertEqual(len(rows),3)
        self.assertFalse(rows[1]["all_native_ledgers_present"])
        self.assertNotIn("metalHistoryMismatch_kg",rows[2])

    def test_duplicate_key_and_nonpositive_dt(self):
        for log in (log_at(1e-6).replace("dt_s=1e-06","dt_s=0"),
                    log_at(1e-6).replace("dt_s=1e-06","dt_s=1e-06 dt_s=1e-06")):
            rows,issues=extract(log)
            self.assertFalse(rows[0]["all_native_ledgers_present"])
            self.assertTrue(issues)

if __name__ == "__main__":
    unittest.main()
