"""Synthetic-output contract tests; OpenFOAM native compilation remains WSL-only."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import verify_fs_c08_openfoam_inventory as v


def native_log(times=(0.2,0.4,1.0),*,bad_count=False,footer=True):
    data=json.loads(v.EVIDENCE.read_text(encoding="utf-8"))
    indexed={round(r["time_s"],8):r for r in data["time_series"]}
    lines=["OpenFOAM 14 test banner; NO solver launched"]
    for t in times:
        original=indexed[round(t,8)]
        Vm = v.LAST_METAL_M3 if t == 1.0 else 4.801e-5
        Vs = v.LAST_SOLID_M3 if t == 1.0 else 5e-7
        count=original["n_gt_1e8"]+(1 if bad_count else 0)
        lines.append("FS_C08_NATIVE_VOLUME_AUDIT "+ " ".join((
            f"time_s={t}",
            "cells=34368",
            f"V_metal_raw_m3={Vm:.17g}",
            f"V_solid_raw_m3={Vs:.17g}",
            f"V_liquid_difference_raw_m3={Vm-Vs:.17g}",
            f"V_solid_excess_m3={original['raw_positive_solid_over_metal_volume_m3']:.17g}",
            f"max_fraction_excess={original['max_solid_over_metal_fraction']:.17g}",
            f"n_significant_excess_gt_1e8={count}",
            "n_core_excess_gt_1e8=0",
        )))
    if footer:
        lines.append("FS_C08_NATIVE_BRIDGE_END read_only=1 solver_reexecuted=0 phase_fields_written=0 physical_shrinkage_validated=0")
    return "\n".join(lines)+"\n"


class TestNativeOpenFOAMBridgeContract(unittest.TestCase):
    def test_three_authentic_FS_C07_saved_state_evidence_records(self):
        output=v.verify_native_log(native_log(),(0.2,0.4,1.0))
        self.assertEqual(output["status"],"PASS")
        self.assertEqual(output["saved_times_verified"],[0.2,0.4,1.0])
        self.assertFalse(output["native_CFD_rerun"])
        self.assertFalse(output["physical_shrinkage_accepted"])

    def test_native_count_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"cell count mismatch"):
            v.verify_native_log(native_log(bad_count=True),(0.2,0.4,1.0))

    def test_missing_footer_or_fake_write_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"footer"):
            v.verify_native_log(native_log(footer=False),(0.2,0.4,1.0))
        bad=native_log().replace("phase_fields_written=0","phase_fields_written=1")
        with self.assertRaisesRegex(ValueError,"footer"):
            v.verify_native_log(bad,(0.2,0.4,1.0))

    def test_missing_or_duplicate_native_snapshots_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"time coverage"):
            v.verify_native_log(native_log((1.0,)),(0.2,0.4,1.0))
        with self.assertRaisesRegex(ValueError,"Duplicate native"):
            v.verify_native_log(native_log((1.0,1.0)),(1.0,))

    def test_invalid_final_real_metal_volume_rejected(self):
        bad=native_log((1.0,)).replace(
            f"V_metal_raw_m3={v.LAST_METAL_M3:.17g}",
            "V_metal_raw_m3=0.0048011038266835194"
        )
        with self.assertRaisesRegex(ValueError,"decomposition mismatch"):
            v.verify_native_log(bad,(1.0,))

    def test_no_openfoam_cpp_write_or_solver_run_statements(self):
        cpp=(v.ROOT/"freesurface/FS-C08_conservative_phase_mass/native_openfoam/fsC08NativeInventory.C").read_text()
        # Strip comments before scanning for executable writes.
        import re
        cpp_no_comments=re.sub(r"/\*.*?\*/|//[^\n]*","",cpp,flags=re.S)
        for forbidden in (
            "mesh.write(", "runTime.write(", "metal.write(",
            "solid.write(", "foamMultiRun(", "fvm::ddt(",
            "fvm::div(",
        ):
            self.assertNotIn(forbidden,cpp_no_comments)
        self.assertIn("IOobject::NO_WRITE",cpp_no_comments)
        self.assertIn("ConservativePhaseExchange.H",cpp_no_comments)

    def test_native_precision_manipulator_has_own_foundation14_header(self):
        cpp=(v.ROOT/"freesurface/FS-C08_conservative_phase_mass/native_openfoam/fsC08NativeInventory.C").read_text()
        self.assertIn('#include "IOmanip.H"',cpp)
        self.assertIn("Info<< setprecision(16);",cpp)
        self.assertNotIn("Info.precision(",cpp)

    def test_native_build_contract_is_wmake_and_explicit_CPP17(self):
        folder=(v.ROOT/"freesurface/FS-C08_conservative_phase_mass/native_openfoam/Make")
        files=(folder/"files").read_text()
        options=(folder/"options").read_text()
        self.assertIn("fsC08NativeInventory.C",files)
        self.assertIn("$(FOAM_USER_APPBIN)/fsC08NativeInventory",files)
        self.assertIn("-std=c++17",options)
        self.assertIn("$(LIB_SRC)/finiteVolume/lnInclude",options)
        self.assertIn("-lfiniteVolume",options)
        self.assertIn("-lOpenFOAM",options)


if __name__ == "__main__":
    unittest.main()
