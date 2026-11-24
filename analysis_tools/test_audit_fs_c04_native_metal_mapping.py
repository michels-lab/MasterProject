"""Synthetic exact FS-C03/FS-C04 native parent cell mapping gates. NO CFD."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audit_fs_c03_exterior_mesh import SOURCE as C03_SOURCE
from audit_fs_c04_fluid_mold import SOURCE as C04_SOURCE
from audit_fs_c04_native_metal_mapping import analyze, read_ascii_zones


TOTAL=42048
METAL=list(range(0,2368))
MOLD=list(range(2368,10048))
AIR=list(range(10048,TOTAL))


def zones_file(groups:dict[str,list[int]])->str:
    result="FoamFile { format ascii; class regIOobject; object cellZones; }\n"
    result+=str(len(groups))+"\n(\n"
    for name,vals in groups.items():
        result+=(name+"\n{\n"
                 "type cellZone;\ncellLabels List<label>\n"+
                 str(len(vals))+"\n(\n"
                 +" ".join(str(i) for i in vals)
                 +"\n);\n}\n")
    return result+")\n"


class NativeCellLabelsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="fs-c04-labels-")
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.old=self.base/"FS_C03_AIR_TOPOLOGY_synthetic"
        self.new=self.base/"FS_C04_FLUID_MOLD_TOPOLOGY_synthetic"
        for root,src,status_name,status,regions,groups in (
            (self.old,C03_SOURCE,"FS_C03_NATIVE_STATUS.json",
             "NATIVE_3_REGION_TOPOLOGY_PASSED_NO_CFD",
             {"metal":2368,"mold":7680,"air":32000},
             {"metal":METAL,"mold":MOLD,"air":AIR}),
            (self.new,C04_SOURCE,"FS_C04_NATIVE_STATUS.json",
             "NATIVE_2_REGION_FLUID_MOLD_TOPOLOGY_PASSED_NO_CFD",
             {"fluid":34368,"mold":7680},
             {"fluid":METAL+AIR,"mold":MOLD}),
        ):
            system=root/"system"
            poly=root/"constant/polyMesh"
            system.mkdir(parents=True)
            poly.mkdir(parents=True)
            (system/"blockMeshDict").write_bytes(src.read_bytes())
            (root/status_name).write_text(json.dumps({
                "status":status,"native_mesh_checks_passed":True,
                "solver_executed":False,"region_cells":regions
            }))
            for fname in ("points","faces","owner","neighbour"):
                (poly/fname).write_bytes(b"FoamFile { format ascii; }\nmesh topology example\n")
            (poly/"cellZones").write_text(zones_file(groups))

    def test_same_native_parent_mesh_cell_ids_proven_no_field_written(self):
        old=(self.old/"constant/polyMesh/cellZones").read_bytes()
        new=(self.new/"constant/polyMesh/cellZones").read_bytes()
        r=analyze(self.old,self.new)
        self.assertEqual(r["status"],"PARENT_MESH_METAL_CELL_LABELS_MATCH_NO_FIELD_WRITTEN")
        self.assertEqual(r["metal_parent_cell_label_count"],2368)
        self.assertEqual(r["air_parent_cell_label_count"],32000)
        self.assertEqual(r["mold_parent_cell_label_count"],7680)
        self.assertTrue(r["verified_metal_plus_air_equals_fluid"])
        self.assertTrue(r["verified_mold_labels_unchanged"])
        self.assertFalse(r["fluid_region_split_cell_addressing_verified"])
        self.assertFalse(r["initial_alpha_field_written"])
        self.assertFalse(r["native_metal_cell_volumes_summed"])
        self.assertFalse(r["CFD_or_CHT_executed"])
        self.assertEqual((self.old/"constant/polyMesh/cellZones").read_bytes(),old)
        self.assertEqual((self.new/"constant/polyMesh/cellZones").read_bytes(),new)
        self.assertFalse((self.new/"0/fluid/alpha.metal").exists())

    def test_changed_native_mesh_faces_blocks_mapping(self):
        f=self.new/"constant/polyMesh/faces"
        f.write_bytes(f.read_bytes()+b"modified")
        with self.assertRaisesRegex(ValueError,"parent mesh faces differs"):
            analyze(self.old,self.new)

    def test_wrong_zone_selection_cannot_pass(self):
        f=self.new/"constant/polyMesh/cellZones"
        fluid=METAL+AIR
        # Swap one solid cell and one metal cell; all counts remain correct.
        fluid[0]=2368
        mold=MOLD.copy()
        mold[0]=0
        f.write_text(zones_file({"fluid":fluid,"mold":mold}))
        with self.assertRaisesRegex(ValueError,"fluid zone != original metal"):
            analyze(self.old,self.new)

    def test_native_status_not_green_rejected(self):
        f=self.new/"FS_C04_NATIVE_STATUS.json"
        r=json.loads(f.read_text())
        r["status"]="STAGED_NO_OPENFOAM"
        f.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError,"did not pass expected"):
            analyze(self.old,self.new)

    def test_binary_zone_file_fail_closed(self):
        f=self.new/"constant/polyMesh/cellZones"
        f.write_text(f.read_text().replace("format ascii;","format binary;"))
        with self.assertRaisesRegex(ValueError,"binary cellZones unsupported"):
            analyze(self.old,self.new)

    def test_zone_overlap_detected(self):
        f=self.new/"constant/polyMesh/cellZones"
        fluid=METAL+AIR
        mold=MOLD.copy()
        mold[0]=fluid[0]
        f.write_text(zones_file({"fluid":fluid,"mold":mold}))
        with self.assertRaisesRegex(ValueError,"overlapping native material zones"):
            analyze(self.old,self.new)


if __name__=="__main__":
    unittest.main()
