#!/usr/bin/env python3
"""Fake runtime tests only. F14 actual native test is separate GitHub CI smoke."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import probe_c14_native_f14_single_vs_multi_time as probe


class Foundation14ThreeTimeProbeTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root=Path(d.name)
        self.source=self.root/"actual_C14_fluid_solid_2step"
        (self.source/"system").mkdir(parents=True)
        (self.source/"system/controlDict").write_text("SYNTHETIC F14\n")
        (self.source/"log.foamMultiRun").write_text("2-step synthetic solver End\n")
        mesh=self.source/"constant/metal/polyMesh"
        mesh.mkdir(parents=True)
        (mesh/"cellZones").write_text(probe.stage.whole_region_zone(27))
        for field in probe.stage.MESH:
            (mesh/field).write_text("polyMesh fixture "+field+"\n")
        for name in ("0","0.001","0.002"):
            (self.source/name/"metal").mkdir(parents=True)
            (self.source/name/"metal/T").write_text(name+" T saved\n")
            (self.source/name/"metal/U").write_text(name+" U saved\n")
        self.times=["0","0.001","0.002"]
        self.out=self.root/"NATIVE_NEW_THREE_TIME_PROBE"
        self.before={str(f):probe.sha(f) for f in self.source.rglob("*")
                     if f.is_file()}

    def fake_native(self, multi_has_fatal: bool):
        def runner(folder: Path, label: str, args: list[str]) -> dict:
            selector=args[-1]
            tlist=selector.split(",")
            log=folder/("log.C14_3D_postprocess_"+label)
            content="Time = "+tlist[0]+"\n"
            if multi_has_fatal and len(tlist)>1:
                content+="--> FOAM FATAL IO ERROR:\nCannot find cellZone metal\n"
                tlist=tlist[:1]
            content+="End\n"
            log.write_text(content)
            p=folder/"postProcessing/metal/metalSensibleEnthalpy/0"
            p.mkdir(parents=True)
            (p/"volFieldValue.dat").write_text(
                "# Time volIntegrate(rho*h)\n"+
                "".join(f"{t} 12.4\n" for t in tlist))
            return {
                "name":label,"command_without_bootstrap":args,
                "exit_code":0,"passed":True,"log":log.name
            }
        return runner

    def run_it(self, multi_has_fatal: bool):
        with mock.patch.object(probe.stage,"region_cells",
                               return_value={"nCells":27}), \
             mock.patch.object(probe.old,"run_native",
                               side_effect=self.fake_native(multi_has_fatal)):
            return probe.execute(self.source,self.out,self.times,27)

    def test_multi_fails_with_2_fatal_free_independent_ones(self):
        report=self.run_it(True)
        self.assertEqual(report["status"],
                         "THREE_TIME_ISOLATED_NATIVE_F14_PROBE_COMPLETED")
        self.assertEqual(report["verdict"],
            "REPRODUCED_NATIVE_MULTITIME_REGISTRY_FAILURE_IN_SAME_SAVED_C14_FIELDS")
        self.assertTrue(all(x["pass"] for x in report["individual_results"]))
        self.assertFalse(report["combined_three_time"]["pass"])
        self.assertEqual(report["combined_three_time"]["FATAL"],1)
        self.assertFalse(report["original_solver_rerun"])
        self.assertEqual(self.before,
                         {str(f):probe.sha(f) for f in self.source.rglob("*")
                          if f.is_file()})
        saved=json.loads((self.out/probe.REPORT).read_text())
        self.assertTrue(saved["source_SHA256_unchanged"])
        self.assertEqual(len(saved["trial_results"]),4)
        self.assertFalse(saved["native_energy_conservation_verified"])

    def test_all_four_pass_does_not_overclaim_failure_root_cause(self):
        report=self.run_it(False)
        self.assertEqual(report["verdict"],
            "SINGLE_AND_MULTITIME_NATIVE_PASS_NO_REGISTRY_FAILURE_REPRODUCED")
        self.assertTrue(report["combined_three_time"]["pass"])
        self.assertEqual(report["combined_three_time"]["FATAL"],0)

    def test_existing_destination_refused_before_any_copy(self):
        self.out.mkdir()
        with self.assertRaisesRegex(probe.ProbeBlocked,"output already exists"):
            probe.snapshots(self.source,self.times,27,self.out)
        self.assertEqual(self.before,
                         {str(f):probe.sha(f) for f in self.source.rglob("*")
                          if f.is_file()})

    def test_source_bad_full_metal_zone_fails_closed(self):
        (self.source/"constant/metal/polyMesh/cellZones").unlink()
        with mock.patch.object(probe.stage,"region_cells",
                               return_value={"nCells":27}):
            with self.assertRaisesRegex(probe.ProbeBlocked,"full-metal cellZone"):
                probe.snapshots(self.source,self.times,27,self.out)
        self.assertFalse(self.out.exists())

    def test_source_symlink_is_rejected(self):
        (self.source/"constant/metal/polyMesh/external").symlink_to(
            self.source/"system/controlDict")
        with mock.patch.object(probe.stage,"region_cells",
                               return_value={"nCells":27}):
            with self.assertRaisesRegex(probe.ProbeBlocked,"external symlink"):
                probe.execute(self.source,self.out,self.times,27)
        self.assertFalse(self.out.exists())

    def test_wrong_order_time_selectors_blocked(self):
        with self.assertRaisesRegex(probe.ProbeBlocked,"ordered snapshots"):
            probe.snapshots(self.source,["0","0.002","0.001"],27,self.out)


if __name__=="__main__":
    unittest.main()
