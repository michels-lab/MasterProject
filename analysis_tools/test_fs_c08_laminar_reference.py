"""Regression for controlled transport staging, no CFD validation."""
import unittest
from stage_fs_c08_coupled import laminar_reference_models

class LaminarReferenceTest(unittest.TestCase):
    def test_explicit_reference_changes_only_transport_and_damping(self):
        momentum = "FoamFile { object momentumTransport; }\nsimulationType RAS;\nRAS { model kEpsilon; }\n"
        models = ("FoamFile { object fvModels; }\n"
                  "turbulenceDamping\n{\n type compressible::VoFTurbulenceDamping;\n delta 1e-4;\n}\n"
                  "otherModel\n{ type anotherModel; }\n")
        new_momentum, new_models = laminar_reference_models(momentum, models)
        self.assertIn("simulationType laminar;", new_momentum)
        self.assertIn("RAS { model kEpsilon; }", new_momentum)
        self.assertNotIn("type compressible::VoFTurbulenceDamping", new_models)
        self.assertIn("otherModel", new_models)
        self.assertIn("simulationType RAS;", momentum)

    def test_refuse_unknown_transport(self):
        with self.assertRaises(ValueError):
            laminar_reference_models("simulationType twoPhaseTransport;", "")

    def test_refuse_unknown_damping_layout(self):
        with self.assertRaises(ValueError):
            laminar_reference_models("simulationType RAS;", "FoamFile {}")

if __name__ == "__main__":
    unittest.main()
