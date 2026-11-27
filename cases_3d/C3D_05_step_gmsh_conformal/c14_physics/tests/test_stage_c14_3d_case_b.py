#!/usr/bin/env python3
"""Case B/3D C14 research source staging: integration-level source regressions.

No generated mesh, fake CFD or Foundation14 run is used to claim research
results. All source-derived fields are tested against the preserved C14 model.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest


CODE=Path(__file__).resolve().parents[1]/"stage_c14_3d_case_b.py"
spec=importlib.util.spec_from_file_location("c3d05_case_b_c14", CODE)
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


class CaseBOriginalC14Physics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=S.original.assemble_unmaterialized_source_exact_fileset()
        cls.bcase=S.files_for_real_mesh(92200,has_zone=False)

    def test_22_original_source_files_preserved_except_two_documented_changes(self):
        self.assertEqual(len(self.original),22)
        self.assertEqual(set(self.bcase),set(self.original)|{
            "constant/metal/polyMesh/cellZones"})
        changed={p for p in self.original if self.original[p]!=self.bcase[p]}
        self.assertEqual(changed,{"0/mold/T","system/metal/fvSolution"})
        self.assertEqual(self.original["system/controlDict"],self.bcase["system/controlDict"])
        self.assertEqual(self.original["constant/metal/fvModels"],
                         self.bcase["constant/metal/fvModels"])
        self.assertIn("solidificationMeltingSource",self.bcase["constant/metal/fvModels"])
        self.assertIn("phaseChangeSource:alpha1",self.bcase["0/metal/phaseChangeSource:alpha1"])
        self.assertIn("heRhoThermo",self.bcase["constant/metal/materials/castIron"])
        self.assertIn("heSolidThermo",self.bcase["constant/mold/materials/silica"])
        self.assertIn("metal       fluid",self.bcase["system/controlDict"])
        self.assertIn("mold        solid",self.bcase["system/controlDict"])
        self.assertEqual(self.original["0/metal/T"],self.bcase["0/metal/T"])
        self.assertEqual(self.original["0/metal/U"],self.bcase["0/metal/U"])
        self.assertIn("pRefCell          0;",self.bcase["system/metal/fvSolution"])
        self.assertNotIn("pRefPoint",self.bcase["system/metal/fvSolution"])

    def test_case_b_real_mold_uses_exact_source_h_ta_emissivity_contact(self):
        mold=self.bcase["0/mold/T"]
        self.assertIn("moldOuterUnclassified",mold)
        self.assertEqual(mold.count("externalTemperature"),1)
        self.assertIn("mold_to_metal",mold)
        self.assertIn("coupledTemperature",mold)
        for patch in S.ORIGINAL_MOLD_EXTERIORS:
            self.assertIsNone(re.search(r"(?m)^\s*"+patch+r"\s*$",mold))
        original_bodies=[
            m.group(2) for m in re.finditer(
                r"(?m)^    ([A-Za-z][\w]*)\n    \{\n(.*?)\n    \}\n",
                self.original["0/mold/T"],re.S)
            if m.group(1) in S.ORIGINAL_MOLD_EXTERIORS
        ]
        self.assertEqual(len(original_bodies),5)
        self.assertEqual(len(set(original_bodies)),1)
        self.assertIn(original_bodies[0],mold)

    def test_metal_cell_zone_exact_92200_labels_and_reject_wrong_number(self):
        cells=self.bcase["constant/metal/polyMesh/cellZones"]
        self.assertIn("cellLabels List<label> 92200",cells)
        self.assertIn("\n92199\n",cells)
        self.assertIn("metal",cells)
        label_payload=cells.split("cellLabels List<label> 92200",1)[1].split(");",1)[0]
        self.assertEqual(len(re.findall(r"(?m)^\d{1,5}$",label_payload)),92200)
        with self.assertRaisesRegex(ValueError,"wrong Case B metal cell count"):
            S.files_for_real_mesh(8960,has_zone=False)
        without=S.files_for_real_mesh(92200,has_zone=True)
        self.assertNotIn("constant/metal/polyMesh/cellZones",without)

    def test_source_perturbation_does_not_silently_merge_different_exterior_bc(self):
        bad=dict(self.original)
        mold=bad["0/mold/T"]
        self.assertIn("emissivity",mold)
        # Force one source patch to differ without changing the original C14 files.
        first=next(iter(sorted(S.ORIGINAL_MOLD_EXTERIORS)))
        pattern=r"(?m)(^    "+re.escape(first)+r"\n    \{\n)(.*?)(\n    \}\n)"
        def change(match):
            self.assertIn("emissivity",match.group(2))
            return match.group(1)+match.group(2).replace("emissivity","emissivity_DRIFT",1)+match.group(3)
        mold,count=re.subn(pattern,change,mold,count=1,flags=re.S)
        self.assertEqual(count,1)
        bad["0/mold/T"]=mold
        with self.assertRaisesRegex(ValueError,"exterior values differ"):
            S.map_mold_exterior(bad)

    def test_patch_names_from_openfoam_boundary_header_and_extra_patch(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"boundary"
            p.write_text("""FoamFile
{
 version 2.0;
 format ascii;
 class polyBoundaryMesh;
 object boundary;
}
2
(
 metalTop
 {
    type patch;
    nFaces 12;
    startFace 100;
 }
 metal_to_mold
 {
    type mappedWall;
    nFaces 12636;
    startFace 112;
 }
)
""")
            self.assertEqual(S.patch_names(p),{"metalTop","metal_to_mold"})
            p.write_text(p.read_text().replace("metalTop\n", "badUnexpected\n"))
            self.assertNotEqual(S.patch_names(p),S.PATCHES["metal"])

    def test_empty_zone_only_accepted_with_native_header_and_no_other_zones(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/"constant/metal/polyMesh"
            p.mkdir(parents=True)
            c=p/"cellZones"
            self.assertEqual(S.native_cell_zone_state(Path(folder)),"ABSENT")
            c.write_text("""/* Official header banner */\nFoamFile
{
version 2.0;
format ascii;
class regIOobject;
object cellZones;
}
0
(
)
// ************************************************************************* //
""")
            self.assertEqual(S.native_cell_zone_state(Path(folder)),"EMPTY")
            c.write_text(c.read_text().replace("0\n(","1\n("))
            with self.assertRaises(ValueError):
                S.native_cell_zone_state(Path(folder))
            c.write_text("no native dictionary")
            with self.assertRaisesRegex(ValueError,"metadata"):
                S.native_cell_zone_state(Path(folder))

    def test_source_is_read_only_and_existing_output_is_protected(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/"source"
            source.mkdir()
            dest=root/"output"
            S.protect(source,dest)
            with self.assertRaisesRegex(ValueError,"overlap"):
                S.protect(source,source)
            dest.mkdir()
            with self.assertRaisesRegex(ValueError,"already exists"):
                S.protect(source,dest)
            with self.assertRaisesRegex(ValueError,"overlap"):
                S.protect(source,source/"nested")

    def test_ancestor_symlink_and_dotdot_cannot_bypass_source_guard(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            source=root/"source"
            source.mkdir()
            alias=root/"alias"
            alias.symlink_to(source, target_is_directory=True)
            with self.assertRaisesRegex(ValueError,"overlap"):
                S.protect(source,alias/"new_parent"/"new_case")
            with self.assertRaisesRegex(ValueError,"overlap"):
                S.protect(source,root/"other"/".."/"source"/"new_case")

    def test_original_C14_only_full_timing_and_no_shrinkage_claim(self):
        inputdict=self.bcase["system/controlDict"]
        self.assertRegex(inputdict,r"\bendTime\s+10\s*;")
        self.assertRegex(inputdict,r"\bdeltaT\s+0\.001\s*;")
        self.assertRegex(inputdict,r"\bwriteInterval\s+100\s*;")
        text=CODE.read_text()
        self.assertIn("contraction_model_activated",text)
        self.assertIn('"Cp_to_Cv_substitution":False',text)
        self.assertIn('"experimentally_validated":False',text)
        self.assertIn("refuse rerun",text)
        self.assertNotIn("subprocess.run([\"gmsh\"",text)
        self.assertNotIn("blockMesh",text)
        self.assertNotIn("C3D05_T0_C14_SHK_01",text)


if __name__=="__main__":
    unittest.main()
