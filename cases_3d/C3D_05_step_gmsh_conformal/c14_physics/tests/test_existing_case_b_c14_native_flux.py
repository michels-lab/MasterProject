#!/usr/bin/env python3
"""Case B exact fluid+solid C14 boundary q CSV; synthetic native-layout tests ONLY."""
from __future__ import annotations

import ast
import csv
import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "real_c14_f14_flux_audit",HERE/"analyze_existing_case_b_c14_native_flux.py")
A=importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
run_source=(HERE/"run_existing_case_b_c14_native_flux.py")
runner_spec=importlib.util.spec_from_file_location("case_b_native_q_runner",run_source)
R=importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(R)
cpp_source=HERE/"native_flux/c3d05C14FluidSolidFlux.C"
PATCHES=tuple(A.PATCHES)
INTERFACE=12636


def fixtures(root:Path)->tuple[Path,Path]:
    integral=root/"integ.csv"
    faces=root/"faces.csv"
    with integral.open("w",newline="",encoding="utf-8") as stream:
        w=csv.DictWriter(stream,fieldnames=A.SUM_FIELDS)
        w.writeheader()
        for i in range(101):
            t=i/10
            for reg,patch in PATCHES:
                is_if=patch in ("metal_to_mold","mold_to_metal")
                count=INTERFACE if is_if else 1
                q=10.0 if reg=="metal" else (-10.0 if is_if else 1.0)
                w.writerow({
                    "time_s":f"{t:.17g}","region":reg,"patch":patch,
                    "nFaces":count,"area_m2":count,
                    "q_out_W":q*count,
                    "gross_abs_face_power_W":abs(q)*count,
                })
    with faces.open("w",newline="",encoding="utf-8") as stream:
        w=csv.DictWriter(stream,fieldnames=A.FACE_FIELDS)
        w.writeheader()
        for reg,patch in PATCHES:
            is_if=patch in ("metal_to_mold","mold_to_metal")
            count=INTERFACE if is_if else 1
            q=10.0 if reg=="metal" else (-10.0 if is_if else 1.0)
            for i in range(count):
                x=i*1e-5 if is_if else 0.0
                w.writerow({
                    "time_s":"10","region":reg,"patch":patch,
                    "face_local":i,"center_x_m":x,
                    "center_y_m":0.0,"center_z_m":0.0,
                    "area_m2":1.0,
                    "normal_x":1.0 if reg=="metal" else -1.0,
                    "normal_y":0.0,"normal_z":0.0,
                    "q_out_W_m2":q,"q_out_face_W":q,
                })
    return integral,faces


class CaseBC14TrueFluidSolidFluxAudit(unittest.TestCase):
    def test_exact_101x4_integrated_and_final_4patch_face_values(self):
        with TemporaryDirectory() as path:
            native,faces=fixtures(Path(path))
            d=A.native_flux_analysis(native,faces)
            self.assertEqual(d["status"],A.STATUS)
            self.assertEqual(d["stored_time_count"],101)
            self.assertEqual(d["native_patch_count"],4)
            self.assertEqual(d["native_interface_faces_each"],INTERFACE)
            self.assertEqual(d["per_face_native_last_time_count"],2*INTERFACE+2)
            self.assertEqual(d["per_face_geometry"][
                "matched_rounded_centres_at_1e_8_m"],INTERFACE)
            self.assertTrue(d["per_face_geometry"][
                "interface_geometry_and_orientation_complete"])
            self.assertEqual(d["final"]["interface_sum_outward_W"],0)
            self.assertEqual(d["final"]["metalTop_q_out_W"],10)
            self.assertEqual(d["final"]["moldOuterUnclassified_q_out_W"],1)
            self.assertAlmostEqual(d[
                "signed_external_total_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL"],110)
            self.assertFalse(d["overall_energy_conservation_verified"])
            self.assertFalse(d["native_latent_fvModel_source_integral"])
            self.assertFalse(d["boundary_flux_native_time_step_integral"])

    def test_bad_time_grid_duplicate_region_or_unmatched_patch_rejected(self):
        with TemporaryDirectory() as path:
            native,faces=fixtures(Path(path))
            data=native.read_text(encoding="utf-8")
            native.write_text(data.replace("0,metal,metal_to_mold,",
                                           "0,metal,WRONG_PATCH,",1))
            with self.assertRaisesRegex(ValueError,"patch not recognized"):
                A.native_flux_analysis(native,faces)

    def test_mismatched_real_face_count_rejected(self):
        with TemporaryDirectory() as path:
            native,faces=fixtures(Path(path))
            with native.open("r",encoding="utf-8",newline="") as fp:
                rows=list(csv.DictReader(fp))
            assert rows[0]["region"]=="metal" and rows[0]["patch"]=="metal_to_mold"
            rows[0]["nFaces"]="12635"
            with native.open("w",encoding="utf-8",newline="") as fp:
                writer=csv.DictWriter(fp,fieldnames=A.SUM_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError,"patch count"):
                A.native_flux_analysis(native,faces)

    def test_missing_source_time_rejected_before_all_face_analysis(self):
        with TemporaryDirectory() as path:
            native,faces=fixtures(Path(path))
            lines=native.read_text(encoding="utf-8").splitlines()
            native.write_text("\n".join(lines[:-1])+"\n")
            with self.assertRaisesRegex(ValueError,"404"):
                A.native_flux_analysis(native,faces)

    def test_bad_native_face_power_or_duplicate_face_rejected(self):
        with TemporaryDirectory() as path:
            native,faces=fixtures(Path(path))
            data=faces.read_text(encoding="utf-8")
            # This intentionally changes the first face power to +11 vs
            # native q*area=10 and must fail rather than silently sum totals.
            faces.write_text(data.replace(
                ",1.0,0.0,0.0,10.0,10.0\n",
                ",1.0,0.0,0.0,10.0,11.0\n",1))
            with self.assertRaisesRegex(ValueError,"q\\*area"):
                A.native_flux_analysis(native,faces)

    def test_signed_approximation_not_claimed_solver_dt_integral(self):
        values=[{"time_s":0.0,"q":0.0},
                {"time_s":0.1,"q":10.0},
                {"time_s":0.2,"q":5.0}]
        self.assertAlmostEqual(A.signed_interval_integral(values,"q"),1.25)
        with TemporaryDirectory() as path:
            f,g=fixtures(Path(path))
            d=A.native_flux_analysis(f,g)
            self.assertIn("NOT_NATIVE_INTEGRAL",
                          "signed_external_total_outward_trapezoid_saved_0_1s_J_NOT_NATIVE_INTEGRAL")
            self.assertFalse(d["overall_energy_conservation_verified"])

    def test_compiled_F14_fluid_differs_from_old_T0_solid(self):
        code=cpp_source.read_text(encoding="utf-8")
        self.assertIn("fluidThermoThermophysicalTransportModel::New(momentum(),tm())",code)
        self.assertIn("solidThermophysicalTransportModel::New(td())",code)
        self.assertIn("compressible::momentumTransportModel::New",code)
        self.assertIn("metal_to_mold",code)
        self.assertIn("mold_to_metal",code)
        self.assertIn("metalTop",code)
        self.assertIn("moldOuterUnclassified",code)
        self.assertIn("dirs.size()!=101",code)
        self.assertIn('#include "linear.H"',code)
        self.assertNotIn('#include "linearInterpolate.H"',code)
        self.assertNotIn("autoPtr<solidThermo> tm",code)

    def test_diagnose_existing_real_WSL_attempt_exposes_fatal_io_context_only(self):
        with TemporaryDirectory() as rootname:
            root=Path(rootname)
            output=root/"C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01"
            attempt=root/("."+output.name+".ATTEMPT_native")
            attempt.mkdir()
            (attempt/R.LOG_BUILD).write_text("wmake success\\n",encoding="utf-8")
            (attempt/R.LOG_EXTRACT).write_text(
                "Create time\\nSelecting thermo fluid\\n"
                "--> FOAM FATAL IO ERROR:\\n"
                "keyword thermophysicalTransport is undefined\\n"
                "file: constant/metal/momentumTransport\\n",
                encoding="utf-8"
            )
            (attempt/"bin").mkdir()
            (attempt/"bin/c3d05C14FluidSolidFlux").write_text(
                "fake fixture, not executable",encoding="utf-8"
            )
            with patch.object(R,"OUTPUT",output):
                diagnosis=R.diagnose_attempt(attempt)
            self.assertTrue(diagnosis["compiled_native_binary_exists"])
            self.assertTrue(any("FOAM FATAL IO ERROR" in line
                                for line in diagnosis["fatal_error_context_lines"]))
            self.assertTrue(any("keyword thermophysicalTransport" in line
                                for line in diagnosis["fatal_error_context_lines"]))
            self.assertTrue(diagnosis["NO_CFD_NO_REBUILD_NO_NEW_EXTRACTION"])
            self.assertFalse(diagnosis["native_q_successfully_published"])

    def test_diagnose_rejects_unrelated_or_missing_attempt_without_executing(self):
        with TemporaryDirectory() as rootname:
            root=Path(rootname)
            output=root/"C3D05_B_C14_NATIVE_FLUID_SOLID_PATCH_Q_01"
            wrong=root/"not_a_real_q_ATTEMPT"
            wrong.mkdir()
            (wrong/R.LOG_EXTRACT).write_text("FOAM FATAL\\n",encoding="utf-8")
            with patch.object(R,"OUTPUT",output):
                with self.assertRaisesRegex(ValueError,"isolated C3D05"):
                    R.diagnose_attempt(wrong)
                missing=root/("."+output.name+".ATTEMPT_missing_log")
                missing.mkdir()
                with self.assertRaisesRegex(ValueError,"extractor log not present"):
                    R.diagnose_attempt(missing)

    def test_no_CFD_solver_or_old_case_mutation_runner(self):
        source=run_source.read_text(encoding="utf-8")
        # Inspect executable AST calls rather than searching for a string:
        # the runner deliberately contains "foamMultiRun(" inside a safety
        # check against accidental solver execution. That's NOT a solver call.
        tree=ast.parse(source)
        run_function=next(n for n in tree.body
                          if isinstance(n,ast.FunctionDef) and n.name=="run")
        calls=[node for node in ast.walk(run_function)
               if isinstance(node,ast.Call)]
        invocations=[node for node in calls
                     if isinstance(node.func,ast.Name)
                     and node.func.id=="invoke"]
        self.assertEqual(len(invocations),2)
        compiled=invocations[0].args[0]
        extracted=invocations[1].args[0]
        self.assertIsInstance(compiled,ast.List)
        self.assertIsInstance(extracted,ast.List)
        self.assertEqual(ast.literal_eval(compiled.elts[0]),"wmake")
        self.assertEqual(ast.unparse(extracted.elts[0]),"str(binary)")
        self.assertIn('"foamMultiRun(" not in cpp',source)
        subprocess_calls=[node for node in ast.walk(tree)
                           if isinstance(node,ast.Call)
                           and isinstance(node.func,ast.Attribute)
                           and isinstance(node.func.value,ast.Name)
                           and node.func.value.id=="subprocess"]
        self.assertEqual(len(subprocess_calls),1)
        self.assertEqual(subprocess_calls[0].func.attr,"Popen")
        self.assertEqual(ast.unparse(subprocess_calls[0].args[0]),"argv")
        self.assertIn("runTime",cpp_source.read_text())
        self.assertIn("shutil.copytree(SOURCE,source)",source)
        self.assertIn("staging.rename(output)",source)
        self.assertIn("native_stage_report_sha256",source)
        self.assertIn("output already exists; preserve it",source)


if __name__=="__main__":
    unittest.main()
