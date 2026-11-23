#!/usr/bin/env python3
"""Regression tests: postrun inspector must never alter/rerun authentic CFD."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import analyze_existing_c14_3d_results as inspector


def field(value: float | list[float], n: int=3, compressed: bool=False)->str:
    header="FoamFile\n{\n    format ascii;\n    class volScalarField;\n    object T;\n}\n"
    if type(value) is list:
        if compressed:
            internal=f"nonuniform List<scalar> {n}{{{value[0]}}}"
        else:
            internal=("nonuniform List<scalar> "+str(n)+"\n(\n"
                      +"\n".join(map(str,value))+"\n)")
    else:
        internal=f"uniform {value}"
    return header+f"dimensions [0 0 0 1 0 0 0];\ninternalField {internal};\n"+(
        "boundaryField\n{\n a\n { type zeroGradient; value uniform 999999; }\n}\n"
    )


# Equivalent to selected authentic log fragments, shortened for tests only.
NATIVE_LOG="""Selecting solver fluid
Selecting solver solid
Selecting solidificationMeltingSource with name phaseChangeSource
metal Courant Number mean: 0.11 max: 0.21
Time = 0.001s
metal DILUPBiCGStab: Solving for h, Initial residual = 0.02, Final residual = 1e-5, No Iterations 1
mold DICPCG: Solving for e, Initial residual = 0.02, Final residual = 2e-6, No Iterations 1
metal GAMG: Solving for p_rgh, Initial residual = 0.1, Final residual = 3e-7, No Iterations 2
metal time step continuity errors : sum local = 1e-10, global = -1e-11, cumulative = -1e-12
metal Courant Number mean: 0.00157478 max: 0.00450431
Time = 10s
metal DILUPBiCGStab: Solving for h, Initial residual = 0.1, Final residual = 1e-5, No Iterations 1
mold DICPCG: Solving for e, Initial residual = 0.02, Final residual = 1e-7, No Iterations 1
metal GAMG: Solving for p_rgh, Initial residual = 0.05, Final residual = 1e-6, No Iterations 3
metal time step continuity errors : sum local = 4.19755e-14, global = -1.65749e-19, cumulative = -6.5319e-14
ExecutionTime = 838.394 s ClockTime = 839 s
End
"""


class ReadOnlyRealC14AnalysisTests(unittest.TestCase):
    def test_scalar_uniform_values_exclude_boundary_values(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"T"
            p.write_text(field(1500,n=3))
            self.assertEqual(inspector.scalar_field_values(p,3),[1500]*3)

    def test_scalar_nonuniform_expanded_and_compact(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"T"
            p.write_text(field([1470,1490,1500],n=3))
            self.assertEqual(inspector.scalar_field_values(p,3),[1470,1490,1500])
            p.write_text(field([1470,1470,1470],n=3,compressed=True))
            self.assertEqual(inspector.scalar_field_values(p,3),[1470]*3)

    def test_scalar_parser_rejects_wrong_length_non_finite_or_binary(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"T"
            p.write_text(field([1400,1500],n=3))
            with self.assertRaisesRegex(ValueError,"length"):
                inspector.scalar_field_values(p,3)
            p.write_text(field(1400,n=3).replace("format ascii","format binary"))
            with self.assertRaisesRegex(ValueError,"ASCII"):
                inspector.scalar_field_values(p,3)
            p.write_text(field([1400,1450,1500],n=3))
            with self.assertRaisesRegex(ValueError,"field cell count"):
                inspector.scalar_field_values(p,4)

    def test_all_run_log_uses_actual_max_not_only_last_Courant(self):
        stats=inspector.parse_full_log(NATIVE_LOG)
        self.assertTrue(stats["native_end_found"])
        self.assertEqual(stats["time_last_s"],10)
        self.assertEqual(stats["courant_samples"],2)
        self.assertEqual(stats["courant_max_over_all_logged_steps"],0.21)
        self.assertAlmostEqual(stats["courant_max_last"],0.00450431)
        self.assertAlmostEqual(stats["continuity_cumulative_last"],-6.5319e-14)
        self.assertEqual(stats["residuals_over_entire_log"]["h"]["count"],2)
        with self.assertRaisesRegex(ValueError,"10 s"):
            inspector.parse_full_log(NATIVE_LOG.replace("Time = 10s","Time = 9.9s"))
        with self.assertRaisesRegex(ValueError,"End"):
            inspector.parse_full_log(NATIVE_LOG.replace("\nEnd\n","\n"))
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            inspector.parse_full_log(NATIVE_LOG.replace(
                "Final residual = 1e-6","Final residual = nan"))

    def test_from_existing_complete_case_only_never_rerun_or_modify(self):
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td)
            case=folder/"real_C14"
            destination=folder/"separate_analysis"
            (case/"system").mkdir(parents=True)
            (case/"system/controlDict").write_bytes(
                (inspector.original.physics.C14/"system/controlDict").read_bytes()
            )
            (case/inspector.original.REPORT).write_text(json.dumps({
                "status":inspector.ORIGINAL_META_STATUS,
                "native_solver_run":True,
                "full_10s_original_controlDict_unchanged":True,
            }))
            (case/"log.foamMultiRun").write_text(NATIVE_LOG)
            for time,metal,mold,alpha in (
                ("0",1500,300,1.0),("10",1450,340,0.6)):
                (case/time/"metal").mkdir(parents=True)
                (case/time/"mold").mkdir(parents=True)
                for name,value in (
                    ("T",metal),("p_rgh",100000),("phaseChangeSource:alpha1",alpha)):
                    (case/time/"metal"/name).write_text(field(value))
                (case/time/"mold/T").write_text(field(mold))
            before={
                p.relative_to(case).as_posix():inspector.file_digest(p)
                for p in case.rglob("*") if p.is_file()
            }
            with patch.object(inspector.original,"region_cells",
                              side_effect=[
                                  {"nCells":3},{"nCells":3}
                              ]):
                result=inspector.analyze(case,destination)
            self.assertFalse(result["energy_balance_verified"])
            self.assertFalse(result["mesh_time_independence_verified"])
            self.assertTrue(result["any_saved_cell_below_Tliq_C14"])
            self.assertTrue(result["any_saved_cell_alpha1_below_0_999"])
            self.assertEqual(result["time_states_count"],2)
            with (destination/"C3D04_A_C14_10S_TIME_SERIES.csv").open() as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),2)
            self.assertEqual(float(rows[-1]["metal_T_mean_K"]),1450)
            after={
                p.relative_to(case).as_posix():inspector.file_digest(p)
                for p in case.rglob("*") if p.is_file()
            }
            self.assertEqual(before,after)
            with self.assertRaisesRegex(ValueError,"exists"):
                inspector.analyze(case,destination)
            with self.assertRaisesRegex(ValueError,"overlap"):
                inspector.safe_new_output(case,case/"analysis")

if __name__=="__main__":
    unittest.main()
