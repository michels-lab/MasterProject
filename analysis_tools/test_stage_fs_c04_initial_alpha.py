"""FS-C04 isolated alpha.metal stage-only proof. NO OpenFOAM or CFD."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from audit_fs_c02_local import read_alpha
from stage_fs_c04_initial_alpha import (
    ATMOSPHERE_PATCHES, FLUID_CELLS, GAS_CELLS, METAL_CELLS,
    MOLD_CONTACT_FACES, MOLD_CONTACT_NAME, SOURCE_FILES,
    boundary_patches, make_alpha, stage, verify_alpha_file,
)

METAL_IDS=list(range(METAL_CELLS))
ALL_ALPHA=[1.0]*METAL_CELLS + [0.0]*GAS_CELLS
BCS={name:{"type":"patch","nFaces":str(count)}
     for name,count in ATMOSPHERE_PATCHES.items()}
BCS[MOLD_CONTACT_NAME]={
    "type":"mappedWall","nFaces":str(MOLD_CONTACT_FACES),
    "neighbourRegion":"mold","neighbourPatch":"mold_to_fluid",
}


def boundary_file()->str:
    lines=[
        "FoamFile { version 2.0; format ascii; object boundary; }",
        "4", "("
    ]
    for name,props in BCS.items():
        lines.extend([name,"{"])
        for key,v in props.items():
            lines.append("  "+key+" "+v+";")
        lines.append("}")
    return "\n".join(lines+[" )"])


class StageFieldTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="fs-c04-alpha-test-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.parent=self.root/"FS_C03_AIR_TOPOLOGY_synthetic"
        self.src=self.root/"FS_C04_FLUID_MOLD_TOPOLOGY_synthetic"
        self.out=self.root/"FS_C04_ALPHA_STAGE_synthetic"
        self.parent.mkdir()
        for s in ("parent","fluid","mold"):
            folder=(self.src/"constant"/("polyMesh" if s=="parent"
                                         else s+"/polyMesh"))
            folder.mkdir(parents=True)
            for name in SOURCE_FILES:
                (folder/name).write_text(
                    boundary_file() if name=="boundary" and s=="fluid"
                    else f"FoamFile {{ format ascii; }}\n{s} {name}\n")
        (self.src/"FS_C04_NATIVE_STATUS.json").write_text('{"status":"PASSED"}')
        (self.parent/"FS_C03_NATIVE_STATUS.json").write_text('{"status":"PASSED"}')
        self.proof={
            "status":"SPLIT_FLUID_METAL_MAPPING_VERIFIED_NO_FIELD_WRITTEN",
            "metal_volume_from_split_fluid_polyhedron_m3":2.368e-6,
        }

    def test_boundary_recognizes_atmospheres_and_solid_interface(self):
        p=self.src/"constant/fluid/polyMesh/boundary"
        self.assertEqual(boundary_patches(p),BCS)
        bad=p.read_text().replace("type patch;","type wall;",1)
        p.write_text(bad)
        with self.assertRaisesRegex(ValueError,"not an OPEN patch"):
            boundary_patches(p)

    def test_make_alpha_exact_phase_values_and_inlet_outlet_BCs(self):
        s=make_alpha(ALL_ALPHA,BCS)
        f=self.root/"alpha.metal"
        f.write_text(s)
        vals=read_alpha(f,expected_cells=FLUID_CELLS)
        self.assertEqual(vals[:METAL_CELLS],[1.0]*METAL_CELLS)
        self.assertEqual(vals[METAL_CELLS:],[0.0]*GAS_CELLS)
        self.assertEqual(s.count("type       inletOutlet;"),3)
        self.assertEqual(s.count("inletValue uniform 0;"),3)
        self.assertEqual(s.count("type       zeroGradient;"),1)
        self.assertIn('location    "0/fluid";',s)

    def test_alpha_rejects_short_or_wrong_metal_mask(self):
        with self.assertRaisesRegex(ValueError,"wrong fluid field cell count"):
            make_alpha(ALL_ALPHA[:-1],BCS)
        x=ALL_ALPHA.copy()
        x[0]=0.0
        with self.assertRaisesRegex(ValueError,"exactly 2368"):
            make_alpha(x,BCS)
        x[0]=.5
        with self.assertRaisesRegex(ValueError,"exactly 2368"):
            make_alpha(x,BCS)

    def test_alpha_readback_matches_id_list_and_geometry(self):
        file=self.root/"alpha.metal"
        file.write_text(make_alpha(ALL_ALPHA,BCS))
        with patch("stage_fs_c04_initial_alpha.cell_volume_m3",
                   return_value=1e-9):
            proof=verify_alpha_file(
                file,METAL_IDS,{},METAL_CELLS*1e-9
            )
        self.assertEqual(proof["metal_cell_count"],2368)
        self.assertEqual(proof["air_cell_count"],32000)
        self.assertEqual(proof["sum_alpha"],2368)
        self.assertAlmostEqual(proof["geometric_sum_alphaV_m3"],2.368e-6)
        self.assertFalse(proof["native_OpenFOAM_field_read_verified"])
        self.assertFalse(proof["physical_thermophysical_models_or_solver_executed"])

    def test_bad_alpha_inlet_backflow_cannot_pass(self):
        file=self.root/"alpha.metal"
        file.write_text(make_alpha(ALL_ALPHA,BCS).replace(
            "inletValue uniform 0;", "inletValue uniform 1;", 1
        ))
        with patch("stage_fs_c04_initial_alpha.cell_volume_m3",
                   return_value=1e-9):
            with self.assertRaisesRegex(ValueError,"backflow"):
                verify_alpha_file(file,METAL_IDS,{},2.368e-6)

    def test_nonmatching_cell_order_is_rejected_even_same_metal_count(self):
        file=self.root/"alpha.metal"
        values=ALL_ALPHA.copy()
        values[0]=0.0
        values[-1]=1.0
        file.write_text(make_alpha(values,BCS))
        with patch("stage_fs_c04_initial_alpha.cell_volume_m3",
                   return_value=1e-9):
            with self.assertRaisesRegex(ValueError,"incorrectly maps metal"):
                verify_alpha_file(file,METAL_IDS,{},2.368e-6)

    def test_copies_only_to_fresh_folder_and_writes_alpha_in_fluid(self):
        src_before={p.relative_to(self.src):hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.src.rglob("*") if p.is_file()}
        with patch("stage_fs_c04_initial_alpha.audit_split",
                   return_value=self.proof), \
             patch("stage_fs_c04_initial_alpha.metal_cell_ids",
                   return_value=METAL_IDS), \
             patch("stage_fs_c04_initial_alpha.read_mesh",return_value={}), \
             patch("stage_fs_c04_initial_alpha.cell_volume_m3",
                   return_value=1e-9):
            output=stage(self.parent,self.src,self.out)
        self.assertEqual(output["status"],
                         "INITIAL_ALPHA_STAGED_GEOMETRY_ONLY_NO_CFD")
        self.assertEqual(output["field_check"]["metal_cell_count"],2368)
        self.assertTrue((self.out/"0/fluid/alpha.metal").is_file())
        self.assertFalse((self.out/"0/mold/alpha.metal").exists())
        self.assertFalse((self.src/"0/fluid/alpha.metal").exists())
        self.assertTrue((self.out/"FS_C04_ALPHA_INITIALIZATION.json").exists())
        src_after={p.relative_to(self.src):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in self.src.rglob("*") if p.is_file()}
        self.assertEqual(src_before,src_after)

    def test_no_overwrite_of_existing_stage(self):
        self.out.mkdir()
        (self.out/"important.txt").write_text("preserve")
        with self.assertRaisesRegex(ValueError,"existing destination"):
            stage(self.parent,self.src,self.out)
        self.assertEqual((self.out/"important.txt").read_text(),"preserve")

    def test_reject_source_symlink_before_creating_stage(self):
        (self.src/"trap").symlink_to(self.root/"missing")
        with patch("stage_fs_c04_initial_alpha.audit_split",
                   return_value=self.proof), \
             patch("stage_fs_c04_initial_alpha.metal_cell_ids",
                   return_value=METAL_IDS):
            with self.assertRaisesRegex(ValueError,"source contains symlink"):
                stage(self.parent,self.src,self.out)
        self.assertFalse(self.out.exists())

    def test_refuses_output_nested_inside_native_source(self):
        with self.assertRaisesRegex(ValueError,"may not overlap"):
            stage(self.parent,self.src,self.src/"nested")


if __name__=="__main__":
    unittest.main()
