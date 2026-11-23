#!/usr/bin/env python3
"""Synthetic, deterministic tests only; NEVER uses investigator WSL data."""
from __future__ import annotations
from pathlib import Path
import tempfile
import json
import sys
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import c14_3d_postprocess_parity as parity


def poly_header(cls):
    return ("FoamFile\n{\n format ascii;\n class "+cls+";\n}\n")


def write_single_hex(root:Path, reverse:bool=False)->None:
    root.mkdir(parents=True,exist_ok=True)
    pts=[
        (0,0,0),(1,0,0),(1,1,0),(0,1,0),
        (0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    faces=[
        (0,3,2,1),(4,5,6,7),
        (0,4,7,3),(1,2,6,5),
        (0,1,5,4),(3,7,6,2)]
    if reverse:
        faces=[tuple(reversed(f)) for f in faces]
    (root/"points").write_text(
        poly_header("vectorField")+"8\n(\n"+
        "\n".join("(%d %d %d)"%x for x in pts)+"\n)\n"
    )
    (root/"faces").write_text(
        poly_header("faceList")+"6\n(\n"+
        "\n".join("4("+ " ".join(map(str,f))+")" for f in faces)+"\n)\n"
    )
    (root/"owner").write_text(poly_header("labelList")+"6{0}\n")
    (root/"neighbour").write_text(poly_header("labelList")+"0\n(\n)\n")
    (root/"boundary").write_text(
        poly_header("polyBoundaryMesh")+"1\n(\nouter\n{ type wall; nFaces 6; startFace 0; }\n)\n"
    )


def Ufield(body:str)->str:
    return ("FoamFile\n{ format ascii; class volVectorField; }\n"
            "internalField "+body+";\n"
            "boundaryField\n{outer {type fixedValue; value uniform (0 0 0);}}\n")


class C14VolumeParityTests(unittest.TestCase):
    def test_one_cubic_meter_owner_and_accepted_native_mesh(self):
        with tempfile.TemporaryDirectory() as d:
            case=Path(d)/"actual_fixture"
            write_single_hex(case/"constant/metal/polyMesh")
            vol=parity.cell_volumes(case,"metal",1)
            self.assertAlmostEqual(vol[0],1.0,places=12)
            self.assertEqual(parity.label_values(case/"constant/metal/polyMesh/owner"),[0]*6)
            self.assertEqual(parity.label_values(case/"constant/metal/polyMesh/neighbour"),[])

    def test_reversed_faces_must_fail(self):
        with tempfile.TemporaryDirectory() as d:
            case=Path(d)
            write_single_hex(case/"constant/metal/polyMesh",reverse=True)
            with self.assertRaisesRegex(ValueError,"nonpositive|positive"):
                parity.cell_volumes(case,"metal",1)

    def test_uniform_and_nonuniform_saved_vector_field(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"U"
            p.write_text(Ufield("uniform (1 2 3)"))
            self.assertEqual(parity.vector_field(p,2),[(1.0,2.0,3.0)]*2)
            p.write_text(Ufield("nonuniform List<vector> 2\n(\n(1 0 0)\n(0 2 0)\n)"))
            self.assertEqual(parity.vector_field(p,2),[(1.0,0.0,0.0),(0.0,2.0,0.0)])
            p.write_text(Ufield("nonuniform List<vector> 3\n(\n(1 0 0)\n(0 2 0)\n(0 0 1)\n)"))
            with self.assertRaisesRegex(ValueError,"count differs"):
                parity.vector_field(p,2)

    def test_mass_volume_weighted_not_cell_count(self):
        self.assertAlmostEqual(parity.weighted([100,200],[1,3]),175)
        with self.assertRaisesRegex(ValueError,"count mismatch"):
            parity.weighted([1,2],[1])
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/"log.foamMultiRun"
            log.write_text(
                "Time = 0.001s\n"
                "Solving for h, Initial residual = 0.1, Final residual = 0.0001\n"
                "Solving for e, Initial residual = 0.1, Final residual = 0.0002\n"
                "Solving for p_rgh, Initial residual = 0.1, Final residual = 0.007\n"
                "Time = 0.002s\n"
                "Solving for h, Initial residual = 0.1, Final residual = 0.00001\n"
                "Solving for e, Initial residual = 0.1, Final residual = 0.00002\n"
                "Solving for p_rgh, Initial residual = 0.1, Final residual = 0.00001\n")
            result=parity.scan_log_extrema(log)
            self.assertEqual(result["p_rgh"]["time_s"],0.001)
            self.assertEqual(result["p_rgh"]["final_residual_max"],0.007)
            self.assertEqual(result["h"]["occurrences"],2)

    def test_c14_exact_diagnostic_inventory_not_substituted(self):
        inventory=parity.original_inventory()
        self.assertIn("solidificationMeltingMomentumDiagnostics",
                      inventory["researchDiagnostics"]["function_objects"])
        self.assertIn("metalMoldEnergyPower",
                      inventory["researchDiagnostics"]["function_objects"])
        self.assertIn("horizontalProfiles",
                      inventory["lineProfiles"]["function_objects"])
        self.assertIn("verticalProfiles",
                      inventory["lineProfiles"]["function_objects"])
        self.assertIn("topFlow",
                      inventory["functions"]["function_objects"])
        self.assertIn("momentumMean",
                      inventory["momentumPostProcessing"]["function_objects"])


if __name__=="__main__":
    unittest.main()
