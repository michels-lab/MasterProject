#!/usr/bin/env python3
"""End-to-end SYNTHETIC shell transaction test: no CFD or native C++ executed.

A fake binary produces 12636 interface pairs per side over 2 timesteps. The
real run_native_t0_patch_flux.sh must publish ONLY complete, checked evidence,
then reuse it without rewriting the binary, solver, or original CSV. A failing
fake binary must leave the canonical output directory ABSENT.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

T0 = Path(__file__).resolve().parents[1]
SCRIPT = T0 / "scripts/run_native_t0_patch_flux.sh"

FAKE_BIN = r"""#!/usr/bin/env python3
# A simulator of the OUTPUT FILE FORMAT only, NOT Foundation14 or CFD.
import csv
import os
from pathlib import Path
import sys
args=sys.argv
def value(flag):
    return Path(args[args.index(flag)+1])
metal=value("-outMetal")
mold=value("-outMold")
header=("time_s","face_local","center_x_m","center_y_m","center_z_m",
        "area_m2","normal_x","normal_y","normal_z","q_out_W_m2")
for path,side in ((metal,1),(mold,-1)):
    with path.open("x",newline="",encoding="utf-8") as f:
        wr=csv.writer(f)
        wr.writerow(header)
        # Deliberately different ordering across the two regions!
        for time in (0,0.1):
            for i in range(12636):
                xyz_id=i if side==1 else 12635-i
                wr.writerow([format(float(time), ".17g"),i,0.,xyz_id*0.0001,0.,1e-5,
                             side,0.,0.,10*side])
    if os.getenv("C3D05_SYNTHETIC_BROKEN") == "1":
        sys.exit(8)  # Simulate a native binary crashing after one CSV.
"""


class NativeFluxAtomicShell(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.case=self.root/"isolated_case"
        self.case.mkdir()
        self.inp=self.root/"input.json"
        self.inp.write_text(json.dumps({"simulation":{"endTime_s":0.1}})+"\n")
        self.log=self.case/"log.foamMultiRun"
        self.log.write_text("Time = 0.0\nTime = 0.1\nEnd\n")
        self.status=self.case/"T0_NUMERICAL_RUN_STATUS.json"
        self.status.write_text(json.dumps({
            "numerical_run_completed":True,
            "scope":"C14_ARCHIVED_NUMERICAL_TWO_SOLID_T0_ONLY",
            "input_sha256":hashlib.sha256(self.inp.read_bytes()).hexdigest(),
            "log_sha256":hashlib.sha256(self.log.read_bytes()).hexdigest()
        })+"\n")
        self.energy=self.case/"T0_NATIVE_ENERGY_HISTORY.json"
        self.energy.write_text(json.dumps({
            "status":"OBSERVED_NATIVE_VOLUMETRIC_ENERGY_METRICS_NOT_PHYSICAL_VALIDATION",
            "input_sha256":hashlib.sha256(self.inp.read_bytes()).hexdigest(),
            "history":[
                {"time_s":0.,"metal_sensible_energy_J":1000.,"mold_sensible_energy_J":1000.},
                {"time_s":0.1,"metal_sensible_energy_J":999.987364,"mold_sensible_energy_J":1000.012636}
            ]
        })+"\n")
        self.bindir=self.case/"T0_NATIVE_FLUX_BIN"
        self.bindir.mkdir()
        self.bin=self.bindir/"c3d05PatchFlux"
        self.bin.write_text(FAKE_BIN)
        self.bin.chmod(0o755)
        (self.bindir/"c3d05PatchFlux.sha256").write_text(
            hashlib.sha256(self.bin.read_bytes()).hexdigest()+"  "+str(self.bin)+"\n")
        tools=self.root/"tools"
        tools.mkdir()
        wmake=tools/"wmake"
        wmake.write_text("#!/bin/sh\nexit 77\n")
        wmake.chmod(0o755)
        self.env=dict(os.environ,WM_PROJECT_VERSION="14",
                      PATH=str(tools)+os.pathsep+os.environ.get("PATH",""))

    def tearDown(self):
        self.tmp.cleanup()

    def run_shell(self, broken=False):
        env=dict(self.env)
        if broken:
            env["C3D05_SYNTHETIC_BROKEN"]="1"
        return subprocess.run(
            ["bash",str(SCRIPT),str(self.case),str(self.inp),str(self.log),str(self.status)],
            env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
            timeout=90,check=False)

    def test_complete_synthetic_flux_transaction_published_and_reused(self):
        first=self.run_shell()
        self.assertEqual(first.returncode,0,first.stdout[-3500:])
        dest=self.case/"T0_NATIVE_FACE_FLUX"
        self.assertTrue(dest.is_dir())
        self.assertTrue((dest/"manifest.sha256").is_file())
        result=json.loads((dest/"bilateral_diagnostics.json").read_text())
        self.assertEqual(result["faces_paired_per_side"],12636)
        self.assertFalse(result["patch_flux_continuity_numerically_accepted"])
        first_csv_hash=hashlib.sha256((dest/"metal.csv").read_bytes()).hexdigest()
        first_json_hash=hashlib.sha256((dest/"bilateral_diagnostics.json").read_bytes()).hexdigest()
        second=self.run_shell()
        self.assertEqual(second.returncode,0,second.stdout[-3500:])
        self.assertIn("NATIVE_FACE_FLUX_VERIFIED_REUSED",second.stdout)
        self.assertEqual(first_csv_hash,hashlib.sha256((dest/"metal.csv").read_bytes()).hexdigest())
        self.assertEqual(first_json_hash,hashlib.sha256((dest/"bilateral_diagnostics.json").read_bytes()).hexdigest())

    def test_reuse_complete_native_stage_without_rerunning_cpp_extractor(self):
        # Model real WSL situation: genuine two-sided extraction finished,
        # older Python analyzer failed before publishing diagnostics.
        stage=self.case/".T0_NATIVE_FACE_FLUX_STAGING.preserved"
        stage.mkdir()
        native=subprocess.run(
            [str(self.bin),"-case",str(self.case),
             "-outMetal",str(stage/"metal.csv"),
             "-outMold",str(stage/"mold.csv"),"-time","0:"],
            capture_output=True,text=True,check=False,timeout=90
        )
        self.assertEqual(native.returncode,0,native.stdout+native.stderr)
        (stage/"log.c3d05PatchFlux").write_text(
            "NATIVE_BILATERAL_PATCH_FLUX_EXTRACTED_NOT_VALIDATED\n"
        )
        # If shell calls the extractor again, deliberately fail the new run.
        result=self.run_shell(broken=True)
        self.assertEqual(result.returncode,0,result.stdout[-3500:])
        self.assertIn("REUSE_COMPLETE_NATIVE_PATCH_EXTRACTION_STAGE_UNVERIFIED",result.stdout)
        self.assertFalse(stage.exists())
        final=self.case/"T0_NATIVE_FACE_FLUX"
        self.assertTrue((final/"manifest.sha256").is_file())
        self.assertEqual(json.loads((final/"bilateral_diagnostics.json").read_text())
                         ["faces_paired_per_side"],12636)
        replay=self.run_shell(broken=True)
        self.assertEqual(replay.returncode,0,replay.stdout[-3500:])
        self.assertIn("NATIVE_FACE_FLUX_VERIFIED_REUSED",replay.stdout)

    def test_synthetic_partial_native_extraction_never_published(self):
        result=self.run_shell(broken=True)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.case/"T0_NATIVE_FACE_FLUX").exists())
        staging=list(self.case.glob(".T0_NATIVE_FACE_FLUX_STAGING.*"))
        self.assertEqual(len(staging),1)
        self.assertTrue((staging[0]/"metal.csv").exists())
        self.assertFalse((staging[0]/"bilateral_diagnostics.json").exists())

    def test_preexisting_untrusted_output_preserved(self):
        published=self.case/"T0_NATIVE_FACE_FLUX"
        published.mkdir()
        (published/"KEEP_USER_DATA").write_text("DO NOT DELETE\n")
        result=self.run_shell()
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((published/"KEEP_USER_DATA").read_text(),"DO NOT DELETE\n")


if __name__=="__main__":
    unittest.main()
