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
            fields.update(liquidMass_kg=2.0,solidMass_kg=1.0,
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

if __name__ == "__main__":
    unittest.main()
