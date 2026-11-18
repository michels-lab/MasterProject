"""No-CFD regression tests for actual-run FS-C02 RAS vs laminar pairing."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c02_local import EXPECTED_CELLS
from compare_fs_c02_ras_laminar import compare
from run_fs_c02_local import INITIAL_VOLUME, stage
from run_fs_c02_laminar_control import prepare


def field(name: str, values: list[float]) -> str:
    return (
        "FoamFile { class volScalarField; object "+name+"; }\n"
        "internalField nonuniform List<scalar>\n"
        f"{len(values)}\n(\n"
        +"\n".join(str(x) for x in values)
        +"\n);\nboundaryField {}\n"
    )


class PairedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="fs-c02-paired-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.ras=self.root/"FS-C02_EXTENDED_synthetic"
        self.lam=self.root/"FS-C02_LAMINAR_synthetic"
        self.reference_case,rs=stage(self.ras,extended_probe=True)
        self.laminar_case,ls=prepare(self.lam)
        self.times=(.001,.006,.01)
        alpha=[1.0]*6400+[0.0]*(EXPECTED_CELLS-6400)
        for root,case,status,gasT in (
            (self.ras,self.reference_case,rs,745.0),
            (self.lam,self.laminar_case,ls,390.0),
        ):
            status["solver_tested_on_real_openfoam"]=True
            status["status"]="PROBE_COURANT_SCREEN_PASSED"
            status["stages"]=[
                {"stage":s,"returncode":0,"gate_passed":True}
                for s in ("blockMesh","checkMesh","foamRun")
            ]
            (root/"FS-C02_RUN_STATUS.json").write_text(json.dumps(status))
            vol=case/"postProcessing/metalVolume/0/volFieldValue.dat"
            vol.parent.mkdir(parents=True)
            vol.write_text(
                "# Time volIntegrate(alpha.metal)\n"
                f"0 {INITIAL_VOLUME}\n"
                f"0.001 {INITIAL_VOLUME}\n"
                f"0.006 {INITIAL_VOLUME}\n"
                f"0.01 {INITIAL_VOLUME}\n"
            )
            log=root/"logs/FS-C02_foamRun.log"
            log.write_text(
                "Time = 0.001s\n"
                "Courant Number mean: 0.001 max: 0.163617\n"
                "Interface Courant Number mean: 0 max: 0.002\n"
                "Time = 0.01s\n"
                "Courant Number mean: 0.001 max: 0.01\n"
                "Interface Courant Number mean: 0 max: 0.001\nEnd\n"
            )
            for t in self.times:
                folder=case/str(t)
                folder.mkdir()
                (folder/"alpha.metal").write_text(field("alpha.metal",alpha))
                vals=[1500.0]*6400+[gasT]*(EXPECTED_CELLS-6400)
                (folder/"T").write_text(field("T",vals))

    def test_paired_compare_three_times_conservative_and_read_only(self):
        orig=(self.laminar_case/"0.01/T").read_bytes()
        report=compare(self.ras,self.lam)
        self.assertEqual(report["status"],
                         "PAIRED_NUMERICAL_COMPARISON_NO_THERMAL_VALIDATION")
        self.assertEqual(report["matched_time_samples"],3)
        self.assertEqual(report["final_time_s"],.01)
        self.assertEqual(report["unchanged_input_count"],18)
        self.assertEqual(report["changed_input_files"],
                         ["constant/fvModels","constant/momentumTransport"])
        self.assertAlmostEqual(report["final_gas_temperature_difference_RAS_minus_laminar_K"],355)
        self.assertAlmostEqual(report["final_near_pure_gas_mean_T_RAS_K"],745)
        self.assertAlmostEqual(report["final_near_pure_gas_mean_T_laminar_K"],390)
        self.assertAlmostEqual(report["final_relative_reduction_in_apparent_gas_heating"],
                               355/445)
        self.assertFalse(report["energy_balance_verified"])
        self.assertFalse(report["solidification_or_shrinkage_modelled"])
        self.assertTrue(report["model_effect_only_package_not_kEpsilon_or_damping_separately"])
        self.assertEqual(orig,(self.laminar_case/"0.01/T").read_bytes())
        self.assertEqual(set(self.root.iterdir()),{self.ras,self.lam})

    def test_extra_input_change_detected_even_if_manifest_rehashed(self):
        path=self.laminar_case/"system/fvSolution"
        path.write_text(path.read_text()+"\n// tampered\n")
        manifest_file=self.laminar_case/"FS-C02_MANIFEST.json"
        manifest=json.loads(manifest_file.read_text())
        import hashlib
        manifest["generated_input_sha256"]["system/fvSolution"] = \
            hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_file.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,"ablation MUST change only"):
            compare(self.ras,self.lam)

    def test_untracked_input_modification_blocked(self):
        (self.laminar_case/"constant/momentumTransport").write_text("tampered")
        with self.assertRaisesRegex(ValueError,"altered original input"):
            compare(self.ras,self.lam)

    def test_nonmatching_saved_times_never_interpolated(self):
        old=self.laminar_case/"0.006"
        old.rename(self.laminar_case/"0.005")
        with self.assertRaisesRegex(ValueError,"saved times not aligned"):
            compare(self.ras,self.lam)

    def test_out_of_spec_courant_log_rejected(self):
        (self.lam/"logs/FS-C02_foamRun.log").write_text(
            "Courant Number mean: 0.01 max: 0.2002\n"
            "Interface Courant Number mean: 0 max: 0.001\n"
        )
        with self.assertRaisesRegex(ValueError,"exceeds common Co acceptance"):
            compare(self.ras,self.lam)

    def test_incomplete_run_status_blocked(self):
        status_file=self.lam/"FS-C02_RUN_STATUS.json"
        s=json.loads(status_file.read_text())
        s["stages"][2]["gate_passed"]=False
        status_file.write_text(json.dumps(s))
        with self.assertRaisesRegex(ValueError,"success not recorded"):
            compare(self.ras,self.lam)

    def test_missing_temperature_field_blocks_comparison(self):
        (self.reference_case/"0.006/T").unlink()
        with self.assertRaisesRegex(ValueError,"final T field missing"):
            compare(self.ras,self.lam)


if __name__=="__main__":
    unittest.main()
