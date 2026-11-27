"""Software-only regressions for incomplete saved-time mass screening."""
import importlib.util
from pathlib import Path
import unittest

CODE=Path(__file__).resolve().parents[1]/"analyze_existing_case_b_c14_metal_mass_phi.py"
spec=importlib.util.spec_from_file_location("case_b_mass_screening", CODE)
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

def row(t, interface=0.0, top=0.0):
    return {"time_s":t, "rho_mass_kg":1.0,
            "phi_metalTop_kg_s_if_readable":top,
            "phi_metal_to_mold_kg_s_if_readable":interface}

class Screening(unittest.TestCase):
    def test_missing_interface_breaks_integration(self):
        records=[row(.1),row(.2,interface=None),row(.3)]
        result=M.temporal_mass_screening(records)
        self.assertFalse(result["saved_time_screening_available"])
        self.assertEqual(result["integrated_contiguous_intervals"],0)
        self.assertIsNone(records[2]["sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"])

    def test_preserves_valid_prefix_but_never_bridges_gap(self):
        records=[row(.1,interface=2.0),row(.2,interface=2.0),
                 row(.3,interface=None),row(.4,interface=2.0)]
        result=M.temporal_mass_screening(records)
        self.assertTrue(result["saved_time_screening_available"])
        self.assertEqual(result["integrated_contiguous_intervals"],1)
        self.assertAlmostEqual(result["sampled_cumulative_exterior_phi_kg"],.2)
        self.assertEqual(result["last_contiguous_joint_time_s"],.2)
        self.assertFalse(result["mass_conservation_verified"])
        self.assertIsNone(records[-1]["sampled_cumulative_exterior_phi_kg_NOT_SOLVER_DT_INTEGRAL"])

if __name__=="__main__":
    unittest.main()
