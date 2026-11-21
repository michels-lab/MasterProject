"""No-CFD regression tests: FS-C02 laminar vs RAS/damping input ablation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from run_fs_c02_laminar_control import (
    BASE_PROFILE, LAMINAR_PROFILE, main, postrun_snapshot, prepare,
)
from run_fs_c02_local import stage, SOURCE, B14_MATERIAL, INITIAL_VOLUME
from audit_fs_c02_local import EXPECTED_CELLS


def scalar_file(name: str, values: list[float]) -> str:
    return ("FoamFile { class volScalarField; object "+name+"; }\n"
            "internalField nonuniform List<scalar>\n"
            +str(len(values))+"\n(\n"
            +"\n".join(str(x) for x in values)+"\n);\n"
            "boundaryField {}\n")


class LaminarControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fs-c02-laminar-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ref_dir = self.root/"FS-C02_EXTENDED_reference"
        self.lam_dir = self.root/"FS-C02_LAMINAR_control"

    def test_only_RAS_and_dependent_damping_inputs_change(self):
        baseline,_ = stage(self.ref_dir, extended_probe=True)
        laminar,record = prepare(self.lam_dir)
        a=json.loads((baseline/"FS-C02_MANIFEST.json").read_text())
        b=json.loads((laminar/"FS-C02_MANIFEST.json").read_text())
        self.assertEqual(a["execution_profile"], BASE_PROFILE)
        self.assertEqual(b["execution_profile"], LAMINAR_PROFILE)
        self.assertEqual(record["profile"], LAMINAR_PROFILE)
        self.assertTrue(record["extended_probe"])
        self.assertTrue(record["laminar_control"])
        self.assertFalse(record["solver_tested_on_real_openfoam"])
        self.assertEqual(record["status"],"STAGED_NO_CFD_YET")
        self.assertEqual(a["time_controls"], b["time_controls"])
        self.assertEqual(len(b["generated_input_sha256"]), 20)
        changed={key for key in a["generated_input_sha256"]
                 if a["generated_input_sha256"][key]!=b["generated_input_sha256"][key]}
        self.assertEqual(changed,{
            "constant/momentumTransport","constant/fvModels"
        })
        self.assertIn("simulationType  laminar;",
                      (laminar/"constant/momentumTransport").read_text())
        self.assertNotIn("turbulenceDamping",
                         (laminar/"constant/fvModels").read_text())
        self.assertEqual((baseline/"constant/momentumTransport").read_bytes(),
                         (SOURCE/"constant/momentumTransport").read_bytes())
        self.assertFalse((laminar/"constant/polyMesh").exists())
        self.assertFalse((laminar/"postProcessing").exists())

    def test_reference_and_b14_immutable(self):
        ref_before=hashlib.sha256((SOURCE/"constant/momentumTransport").read_bytes()).hexdigest()
        b14_before=hashlib.sha256(B14_MATERIAL.read_bytes()).hexdigest()
        prepare(self.lam_dir)
        ref_after=hashlib.sha256((SOURCE/"constant/momentumTransport").read_bytes()).hexdigest()
        b14_after=hashlib.sha256(B14_MATERIAL.read_bytes()).hexdigest()
        self.assertEqual(ref_before, ref_after)
        self.assertEqual(b14_before,b14_after)

    def test_repeating_same_output_refuses_overwrite(self):
        prepare(self.lam_dir)
        with self.assertRaisesRegex(ValueError,"pre-existing run directory"):
            prepare(self.lam_dir)
        self.assertTrue((self.lam_dir/"FS-C02"/"FS-C02_MANIFEST.json").is_file())

    def test_stage_only_cli_never_executes_foamRun(self):
        self.assertEqual(main(["--stage-only","--out",str(self.lam_dir)]),0)
        self.assertTrue((self.lam_dir/"FS-C02"/"FS-C02_MANIFEST.json").is_file())
        self.assertFalse((self.lam_dir/"logs"/"FS-C02_foamRun.log").exists())

    def test_summary_only_reads_saved_alpha_T_and_integrated_volume(self):
        case,_=prepare(self.lam_dir)
        folder=case/"0.01"
        folder.mkdir()
        a=[1.0]*6400+[0.0]*(EXPECTED_CELLS-6400)
        T=[1500.0]*6400+[300.0]*(EXPECTED_CELLS-6400)
        (folder/"alpha.metal").write_text(scalar_file("alpha.metal",a))
        (folder/"T").write_text(scalar_file("T",T))
        data=case/"postProcessing/metalVolume/0/volFieldValue.dat"
        data.parent.mkdir(parents=True)
        data.write_text("# Time volIntegrate(alpha.metal)\n"
                        f"0 {INITIAL_VOLUME}\n0.005 {INITIAL_VOLUME}\n"
                        f"0.01 {INITIAL_VOLUME}\n")
        result=postrun_snapshot(case)
        self.assertEqual(result["near_pure_air_cell_count"],3200)
        self.assertEqual(result["near_pure_air_mean_T_K"],300.0)
        self.assertEqual(result["max_vol_drift_fraction"],0)
        self.assertTrue(result["fluid_energy_balance_unverified"])
        self.assertTrue(result["solidification_and_shrinkage_not_modelled"])


if __name__=="__main__":
    unittest.main()
