"""Synthetic scientific diagnostic guards; no native CFD or field data."""
import math
from pathlib import Path
import tempfile
import unittest
import audit_existing_case_b_c14_energy_closure_readiness as energy
import analyze_existing_case_b_c14_metal_mass_phi as mass


def row(t, rho=1., phi=0.):
    return {"time_s":t,"rho_mass_kg":rho,
            "phi_metalTop_kg_s_if_readable":phi,
            "phi_metal_to_mold_kg_s_if_readable":0.}


class DiagnosticGuards(unittest.TestCase):
    def test_axis(self):
        times=[(i/10,format(i/10,"g")) for i in range(101)]
        energy.validate_saved_axis(times)
        times[5]=times[4]
        with self.assertRaises(ValueError):
            energy.validate_saved_axis(times)

    def test_output_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"source"
            source.mkdir()
            alias=root/"alias"
            alias.symlink_to(source,target_is_directory=True)
            with self.assertRaises(ValueError):
                energy.independent_output(alias/"child",[source])
            self.assertEqual(energy.independent_output(root/"new",[source]),
                             root/"new")

    def test_full_saved_mass_coverage(self):
        report=mass.temporal_mass_screening([row(i/10) for i in range(1,101)])
        self.assertEqual(report["integrated_contiguous_intervals"],99)
        self.assertTrue(report["complete_uninterrupted_joint_coverage_to_10s"])
        self.assertFalse(report["mass_conservation_verified"])

    def test_suffix_not_complete(self):
        report=mass.temporal_mass_screening([row(i/10) for i in range(50,101)])
        self.assertFalse(report["complete_uninterrupted_joint_coverage_to_10s"])
        self.assertTrue(report["contiguous_suffix_reaches_10s_NOT_FULL_COVERAGE"])

    def test_gap_not_bridged(self):
        rows=[row(i/10,phi=None if i==5 else 0.) for i in range(1,101)]
        report=mass.temporal_mass_screening(rows)
        self.assertEqual(report["integrated_contiguous_intervals"],3)
        self.assertFalse(report["complete_uninterrupted_joint_coverage_to_10s"])

    def test_nonfinite_and_duplicate(self):
        for rows in ([row(.1),row(.1)],[row(.1),row(.2,phi=math.nan)]):
            with self.assertRaises(ValueError):
                mass.temporal_mass_screening(rows)


if __name__=="__main__":
    unittest.main()
