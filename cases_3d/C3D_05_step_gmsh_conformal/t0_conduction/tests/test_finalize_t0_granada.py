#!/usr/bin/env python3
"""Synthetic SHA-chain/summary tests; NO solver, no C3D05 CAD, no physical data."""
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

T0 = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("c3d05_granada_final", T0/"scripts/finalize_t0_granada.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


def put(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+"\n", encoding="utf-8")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_run(root: Path):
    case = root/"num_case"
    case.mkdir()
    inp = root/"numeric_inputs.json"
    put(inp, {
        "reference_profile":"C14_ARCHIVED_NUMERICAL_REFERENCE_NOT_JMATPRO_NOT_PHYSICAL_VALIDATION",
        "simulation":{"endTime_s":0.1}
    })
    ih=sha(inp)
    put(case/"T0_GRANADA_REPORT.json",{
        "case":"C3D_05_step_gmsh_conformal",
        "status":"T0_PREPARED_DICTIONARIES_PARSED_NO_CFD",
        "input_sha256":ih,
    })
    put(case/"T0_CLOSED_ENERGY_REFERENCE.json",{"input_file_sha256":ih})
    log=case/"log.foamMultiRun.C14_NUMERICAL_T0"
    log.write_text("Time = 0\nTime = 0.1\nEnd\n")
    put(case/"T0_NUMERICAL_RUN_STATUS.json",{
        "numerical_run_completed":True, "input_sha256":ih,
        "log_sha256":sha(log),
        "scope":"C14_ARCHIVED_NUMERICAL_TWO_SOLID_T0_ONLY",
    })
    energy=case/"T0_NATIVE_ENERGY_HISTORY.json"
    put(energy,{
        "status":"OBSERVED_NATIVE_VOLUMETRIC_ENERGY_METRICS_NOT_PHYSICAL_VALIDATION",
        "input_sha256":ih,
        "max_abs_energy_closure_relative_to_initial_exchange":0.002,
        "history":[{"time_s":0.},{"time_s":0.1}]
    })
    fluxdir=case/"T0_NATIVE_FACE_FLUX"
    fluxdir.mkdir()
    metal=fluxdir/"metal.csv"
    mold=fluxdir/"mold.csv"
    metal.write_text("synthetic metal CSV bytes\n")
    mold.write_text("synthetic mold CSV bytes\n")
    native_log=fluxdir/"log.c3d05PatchFlux"
    native_log.write_text("synthetic extraction\n")
    face=fluxdir/"bilateral_diagnostics.json"
    put(face,{
        "status":"NATIVE_PATCH_Q_FACE_PAIR_DIAGNOSTICS_NO_ACCEPTANCE_THRESHOLD",
        "faces_paired_per_side":12636,
        "history":[
            {"time_s":0., "relative_pairwise_mismatch_over_gross_flux":0.01},
            {"time_s":0.1, "relative_pairwise_mismatch_over_gross_flux":0.015},
        ],
        "source_sha256":{
            "metal_face_csv":sha(metal), "mold_face_csv":sha(mold),
            "regional_energy_json":sha(energy), "inputs_json":ih,
            "solver_log":sha(log)
        }
    })
    with (fluxdir/"manifest.sha256").open("w",encoding="utf-8") as manifest:
        for file in F.EXPECTED_FILES:
            manifest.write(sha(fluxdir/file)+"  "+file+"\n")
    return case,inp


class EvidenceSummary(unittest.TestCase):
    def test_exact_complete_chain_outputs_metrics_without_scientific_acceptance(self):
        with TemporaryDirectory() as tmp:
            case,inp=synthetic_run(Path(tmp))
            out=F.summarize(case,inp)
            self.assertEqual(out["case_stage"],"3/7")
            self.assertEqual(out["technical_milestones_closed"],2)
            self.assertEqual(out["total_flux_pairs_per_time"],12636)
            self.assertEqual(out["temporal_samples"],2)
            self.assertEqual(out["max_relative_energy_discrepancy_over_initial_exchange"],.002)
            self.assertEqual(out["max_relative_pairwise_flux_mismatch_over_gross"],.015)
            self.assertFalse(out["numerical_energy_accepted"])
            self.assertFalse(out["numerical_flux_continuity_accepted"])
            self.assertFalse(out["experimental_JMatPro_or_QuickCup_validation"])
            self.assertFalse(out["user_WSL_host_origin_independently_attested"])
            filename=case/"T0_GRANADA_EVIDENCE_SUMMARY.json"
            self.assertIn("GENERATED",F.exclusive(filename,out))
            self.assertIn("IDENTICAL",F.exclusive(filename,out))
            with self.assertRaises(FileExistsError):
                F.exclusive(filename,{"status":"tampered"})

    def test_corrupted_native_region_or_manifest_blocks_all_claims(self):
        with TemporaryDirectory() as tmp:
            case,inp=synthetic_run(Path(tmp))
            (case/"T0_NATIVE_FACE_FLUX/metal.csv").write_text("corrupted")
            with self.assertRaisesRegex(ValueError,"modified"):
                F.summarize(case,inp)
        with TemporaryDirectory() as tmp:
            case,inp=synthetic_run(Path(tmp))
            (case/"T0_NATIVE_FACE_FLUX/manifest.sha256").write_text("WRONG\n")
            with self.assertRaisesRegex(ValueError,"manifest"):
                F.summarize(case,inp)

    def test_wrong_run_source_or_timestep_cannot_be_a_single_run(self):
        with TemporaryDirectory() as tmp:
            case,inp=synthetic_run(Path(tmp))
            result=case/"T0_NUMERICAL_RUN_STATUS.json"
            data=json.loads(result.read_text())
            data["log_sha256"]="0"*64
            put(result,data)
            with self.assertRaisesRegex(ValueError,"solver"):
                F.summarize(case,inp)
        with TemporaryDirectory() as tmp:
            case,inp=synthetic_run(Path(tmp))
            report=case/"T0_NATIVE_ENERGY_HISTORY.json"
            e=json.loads(report.read_text())
            e["history"][-1]["time_s"]=.09
            put(report,e)
            with self.assertRaises(ValueError):
                F.summarize(case,inp)

    def test_no_numerical_acceptance_from_zero_flux_or_wrong_face_count(self):
        with TemporaryDirectory() as tmp:
            case,inp=synthetic_run(Path(tmp))
            face=case/"T0_NATIVE_FACE_FLUX/bilateral_diagnostics.json"
            f=json.loads(face.read_text())
            f["faces_paired_per_side"]=10
            put(face,f)
            # Rebuild hash so the substantive gate is what rejects it.
            manifest=case/"T0_NATIVE_FACE_FLUX/manifest.sha256"
            rows=manifest.read_text().splitlines()
            manifest.write_text("\n".join(
                sha(face)+"  bilateral_diagnostics.json" if x.endswith("bilateral_diagnostics.json") else x
                for x in rows)+"\n")
            with self.assertRaisesRegex(ValueError,"12636"):
                F.summarize(case,inp)

if __name__=="__main__":
    unittest.main()
