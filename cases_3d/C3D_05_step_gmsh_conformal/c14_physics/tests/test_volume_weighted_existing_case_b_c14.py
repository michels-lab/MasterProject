#!/usr/bin/env python3
"""Native HEX8 face-geometry weighted phase QA. NO solver, real mesh or remesh."""
from __future__ import annotations

from array import array
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

CODE=Path(__file__).resolve().parents[1]/"volume_weighted_existing_case_b_c14.py"
spec=importlib.util.spec_from_file_location("c3d05_b_native_cellvol",CODE)
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def foamfile(classname: str, body: str) -> str:
    return (
        "/* native FoamFile ASCII fixture; only geometry not CFD */\n"
        "FoamFile\n{\n version 2.0;\n format ascii;\n"
        f" class {classname};\n object test;\n}}\n{body}\n"
    )


def two_cube_poly(poly: Path) -> None:
    """2 adjacent unit HEX8 with one owner 0 -> neighbour 1 internal quad."""
    poly.mkdir(parents=True)
    points=[
        (0,0,0),(1,0,0),(1,1,0),(0,1,0),
        (0,0,1),(1,0,1),(1,1,1),(0,1,1),
        (2,0,0),(2,1,0),(2,1,1),(2,0,1),
    ]
    # Internal face first, owner 0, neighbour 1. Exterior faces owner-outward.
    faces=[
        (1,2,6,5),
        (0,3,2,1),(4,5,6,7),(0,4,7,3),(0,1,5,4),(3,7,6,2),
        (8,9,10,11),(1,2,9,8),(5,11,10,6),(1,8,11,5),(2,6,10,9),
    ]
    owner=[0]*6+[1]*5
    neighbour=[1]
    (poly/"points").write_text(foamfile("vectorField",str(len(points))+"\n(\n"+
        "\n".join("("+ " ".join(map(str,v))+")" for v in points)+"\n)"))
    (poly/"faces").write_text(foamfile("faceList",str(len(faces))+"\n(\n"+
        "\n".join("4("+ " ".join(map(str,v))+")" for v in faces)+"\n)"))
    (poly/"owner").write_text(foamfile("labelList",str(len(owner))+"\n(\n"+
        "\n".join(map(str,owner))+"\n)"))
    (poly/"neighbour").write_text(foamfile("labelList",str(len(neighbour))+"\n(\n"+
        "\n".join(map(str,neighbour))+"\n)"))


class VolumeWeightedNativeB(unittest.TestCase):
    def test_two_real_native_style_hex8_cubes_have_unit_cell_volume(self):
        with TemporaryDirectory() as folder:
            poly=Path(folder)/"polyMesh"
            two_cube_poly(poly)
            with patch.object(S,"EXPECTED_CELLS",2),\
                 patch.object(S,"CHECKMESH_METAL_VOLUME_M3",2.0):
                vols,meta=S.calculate_native_metal_cell_volumes(poly)
            self.assertAlmostEqual(vols[0],1.0,places=12)
            self.assertAlmostEqual(vols[1],1.0,places=12)
            self.assertEqual(meta["nFaces"],11)
            self.assertEqual(meta["nInternalFaces"],1)
            self.assertEqual(meta["nPoints"],12)
            self.assertEqual(meta["relative_discrepancy_vs_checkMesh"],0)

    def test_weighted_liquid_differs_from_unweighted_for_unequal_hex_volumes(self):
        with patch.object(S,"EXPECTED_CELLS",2):
            r=S.weighted_phase([1.0,0.0],array("d",[1.0,3.0]))
        self.assertEqual(r["mean_liquid_fraction_volume_weighted"],0.25)
        self.assertEqual(r["mean_solid_complement_volume_weighted"],0.75)
        self.assertEqual(r["volume_with_alpha1_below_0_999_m3"],3.0)
        self.assertEqual(r["volume_fully_solid_alpha1_zero_m3"],3.0)

    def test_face_orientation_or_wrong_mesh_volume_rejected(self):
        with TemporaryDirectory() as folder:
            poly=Path(folder)/"polyMesh"
            two_cube_poly(poly)
            with patch.object(S,"EXPECTED_CELLS",2),\
                 patch.object(S,"CHECKMESH_METAL_VOLUME_M3",100.0):
                with self.assertRaisesRegex(ValueError,"checkMesh total"):
                    S.calculate_native_metal_cell_volumes(poly)
            # Flip every first cube exterior face -> nonpositive cell volume
            source=(poly/"faces").read_text()
            (poly/"faces").write_text(source.replace("4(0 3 2 1)","4(0 1 2 3)"))
            with patch.object(S,"EXPECTED_CELLS",2),\
                 patch.object(S,"CHECKMESH_METAL_VOLUME_M3",2.0):
                with self.assertRaisesRegex(ValueError,"nonpositive|checkMesh total"):
                    S.calculate_native_metal_cell_volumes(poly)

    def test_not_quad_hex8_native_face_rejected(self):
        with TemporaryDirectory() as folder:
            poly=Path(folder)/"polyMesh"
            two_cube_poly(poly)
            raw=(poly/"faces").read_text().replace("4(1 2 6 5)","3(1 2 6)")
            (poly/"faces").write_text(raw)
            with patch.object(S,"EXPECTED_CELLS",2):
                with self.assertRaisesRegex(ValueError,"non-quad"):
                    S.calculate_native_metal_cell_volumes(poly)

    def test_ascii_and_header_class_mandatory(self):
        with TemporaryDirectory() as folder:
            poly=Path(folder)/"polyMesh"
            two_cube_poly(poly)
            f=poly/"points"
            f.write_text(f.read_text().replace("format ascii;","format binary;"))
            with self.assertRaisesRegex(ValueError,"binary mesh forbidden"):
                S.parse_points(f)
            f.write_text(f.read_text().replace("format binary;","format ascii;")
                         .replace("class vectorField;","class scalarField;"))
            with self.assertRaisesRegex(ValueError,"unexpected native mesh class"):
                S.parse_points(f)

    def test_wrong_source_status_cannot_become_volume_weighted_science(self):
        with TemporaryDirectory() as folder:
            inp=Path(folder)/S.DEFAULT_ANALYSIS.name
            inp.mkdir()
            (inp/S.base.MANIFEST).write_text("{}")
            with self.assertRaisesRegex(ValueError,"missing/linked archived input"):
                S.verified_existing_analysis(inp)

    def test_nonfinite_or_out_of_range_native_alpha_rejected(self):
        with patch.object(S,"EXPECTED_CELLS",2):
            for alpha in ((float("nan"),1.0),(-0.1,1.0),(1.0001,1.0)):
                with self.assertRaisesRegex(ValueError,"physical liquid fraction"):
                    S.weighted_phase(alpha,array("d",[1.,2.]))

    def test_never_reexecute_solver_or_alter_old_output(self):
        source=CODE.read_text(encoding="utf-8")
        self.assertNotIn("subprocess.run",source)
        self.assertNotIn("foamMultiRun(",source)
        self.assertNotIn("foamToVTK(",source)
        self.assertNotIn("gmshToFoam(",source)
        self.assertIn("poly/\"faces\"",source)
        self.assertIn("original native accepted polyMesh altered",source)
        self.assertIn("output already exists; preserve data",source)


if __name__=="__main__":
    unittest.main()
