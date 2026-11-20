#!/usr/bin/env python3
"""Pure synthetic regressions for Foundation14 volFieldValue-based T0 energy diagnostics."""
import hashlib
import importlib.util
import json
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

T0 = Path(__file__).resolve().parents[1]
def load(name, file):
    spec = importlib.util.spec_from_file_location(name, T0 / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

N = load("c3d05_native_energy_post", "postprocess_t0_energy.py")
E = load("c3d05_energy_target_test", "t0_energy_reference.py")

def sample(time, volume, temp):
    return {"time_decimal": Decimal(time), "volume_m3": volume, "T_volume_average_K": temp}

class NativeEnergyTrace(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "metal": {"rho_kg_m3": 1, "Cv_J_kg_K": 2, "T_initial_K": 400},
            "mold": {"rho_kg_m3": 2, "Cv_J_kg_K": 2, "T_initial_K": 300},
            "simulation": {"endTime_s": 0.1},
        }
        self.ref = E.energy_target(self.cfg, {"metal": 1.0, "mold": 1.0})
        self.hot = [sample("0", 1, 400), sample("0.1", 1, 380)]
        self.cold = [sample("0.00", 1, 300), sample("0.10", 1, 310)]

    def test_dict_is_official_volFieldValue_all_cells_and_distinct_regions(self):
        for region in ("metal", "mold"):
            text=N.functions_dict(region)
            for fragment in ("type volFieldValue;", "cellZone all;", "operation volAverage;",
                             "writeVolume true;", "fields (T);", N.NAME[region]):
                self.assertIn(fragment, text)
        self.assertNotEqual(N.NAME["metal"],N.NAME["mold"])

    def test_realistic_volFieldValue_file_parses_with_header_and_comments(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"volFieldValue.dat"
            p.write_text("# Region metal\n# Time Volume volAverage(T)\n"
                         "0\t1\t400\n0.1\t1\t380\n",encoding="utf-8")
            data=N.read_volume_average(p)
            self.assertEqual(len(data),2)
            self.assertEqual(data[0]["time_decimal"], Decimal("0"))
            self.assertEqual(data[1]["T_volume_average_K"],380)

    def test_fail_closed_if_missing_header_duplicate_time_or_nan(self):
        for raw in (
            "0 1 400\n0.1 1 380\n",
            "# Time Volume volAverage(T)\n0 1 400\n0.0 1 380\n",
            "# Time Volume volAverage(T)\n0 1 400\n0.1 1 nan\n",
            "# Time Volume volAverage(T)\n0 1 400\n-0.1 1 380\n",
            "# Time Volume volAverage(T)\n0 1 400\n0.1 1 380 20\n",
        ):
            with self.subTest(raw=raw), TemporaryDirectory() as tmp:
                path=Path(tmp)/"values.dat"
                path.write_text(raw,encoding="utf-8")
                with self.assertRaises(ValueError):
                    N.read_volume_average(path)

    def test_exact_conservation_from_sampled_regional_temperature_fields(self):
        out=N.compute_energy_history(self.hot,self.cold,self.ref,self.cfg)
        self.assertEqual(out["samples"],2)
        self.assertAlmostEqual(out["max_abs_energy_closure_relative_to_initial_exchange"],0)
        self.assertFalse(out["direct_coupled_face_heat_flux_verified"])
        self.assertFalse(out["energy_closure_physically_or_numerically_accepted"])
        last=out["history"][-1]
        self.assertAlmostEqual(last["total_sensible_energy_J"],2000)
        self.assertAlmostEqual(last["effective_metal_energy_loss_rate_W"],400)
        self.assertAlmostEqual(last["effective_mold_energy_gain_rate_W"],400)
        self.assertAlmostEqual(last["pair_net_energy_rate_residual_W"],0)
        self.assertTrue(out["initial_time_native_observed"])

    def test_detect_drift_and_imbalanced_exchange_but_not_claim_validation(self):
        cold=[sample("0",1,300),sample("0.1",1,320)]
        out=N.compute_energy_history(self.hot,cold,self.ref,self.cfg)
        self.assertGreater(out["max_abs_energy_closure_relative_to_initial_exchange"],0)
        self.assertNotEqual(out["history"][-1]["pair_net_energy_rate_residual_W"],0)
        self.assertFalse(out["energy_closure_physically_or_numerically_accepted"])

    def test_mismatched_times_volumes_and_incomplete_end_are_blocked(self):
        with self.assertRaisesRegex(ValueError,"write-time"):
            N.compute_energy_history(self.hot,[sample("0",1,300),sample("0.05",1,310)],self.ref,self.cfg)
        with self.assertRaisesRegex(ValueError,"volume differs"):
            N.compute_energy_history([sample("0",1.02,400),sample("0.1",1.02,380)],
                                     self.cold,self.ref,self.cfg)
        with self.assertRaisesRegex(ValueError,"expected"):
            N.compute_energy_history(self.hot[:1],self.cold[:1],self.ref,self.cfg)

    def test_missing_time_zero_or_wrong_initial_field_never_masquerades_as_closure(self):
        with self.assertRaisesRegex(ValueError,"expected native time-zero"):
            N.compute_energy_history(self.hot[1:],self.cold[1:],self.ref,self.cfg)
        altered_hot=[sample("0",1,410),sample("0.1",1,380)]
        with self.assertRaisesRegex(ValueError,"time-zero native T"):
            N.compute_energy_history(altered_hot,self.cold,self.ref,self.cfg)
        altered_mold=[sample("0",1,290),sample("0.1",1,310)]
        with self.assertRaisesRegex(ValueError,"time-zero native T"):
            N.compute_energy_history(self.hot,altered_mold,self.ref,self.cfg)
        # Native writer may round the final displayed scalar; small
        # representational differences are allowed without ignoring drift.
        near=[sample("0",1,400.00001),sample("0.1",1,380)]
        self.assertEqual(N.compute_energy_history(near,self.cold,self.ref,self.cfg)["samples"],2)

    def test_actual_solver_run_report_is_sha_bound_and_not_a_fake_exit_zero(self):
        with TemporaryDirectory() as tmp:
            folder=Path(tmp)
            log=folder/"log.foamMultiRun"
            report=folder/"run.json"
            data=b'{"some":"input"}\n'
            log.write_text("Time = 0.1\nEnd\n",encoding="utf-8")
            payload={
                "scope":"C14_ARCHIVED_NUMERICAL_TWO_SOLID_T0_ONLY",
                "input_sha256":hashlib.sha256(data).hexdigest(),
                "log_sha256":hashlib.sha256(log.read_bytes()).hexdigest(),
                "numerical_run_completed":True,
            }
            report.write_text(json.dumps(payload),encoding="utf-8")
            self.assertTrue(N.verify_solver_attempt(log,report,data)["numerical_run_completed"])
            with self.assertRaisesRegex(ValueError,"input checksum"):
                N.verify_solver_attempt(log,report,b"other input")
            with self.assertRaisesRegex(ValueError,"log bytes"):
                log.write_text("Time=0.1\nModified\n")
                N.verify_solver_attempt(log,report,data)
            log.write_text("Time = 0.1\nEnd\n")
            payload["numerical_run_completed"]=False
            report.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,"not verified complete"):
                N.verify_solver_attempt(log,report,data)

    def test_exclusive_metrics_and_no_overwrite(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/"measure.json"
            metrics={"observed":False}
            self.assertEqual(N.save_exclusive(path,metrics),"NATIVE_ENERGY_OBSERVATIONS_WRITTEN_NO_PHYSICAL_VALIDATION")
            self.assertEqual(N.save_exclusive(path,metrics),"ALREADY_REPORTED_IDENTICAL")
            with self.assertRaises(FileExistsError):
                N.save_exclusive(path,{"observed":True})
            self.assertFalse(json.loads(path.read_text())["observed"])

if __name__ == "__main__":
    unittest.main()
