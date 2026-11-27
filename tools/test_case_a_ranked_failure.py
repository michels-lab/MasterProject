import tempfile
import unittest
from pathlib import Path

from run_case_a_200s_granada import failure


class CaseAFailureTests(unittest.TestCase):
    def test_rank_interleaving_preserves_negative_temperature_context(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory)
            (case / "log.foamMultiRun").write_text(
                "[0] Time = 0.68s\n[0] deltaT = 0.02\n"
                "[1] Time = 0.70s\n[1] deltaT = 0.01\n"
                "[0] Negative initial temperature T0: -1.5\n"
            )
            event, = failure(case)["negative_thermo_initial_temperature"]
            self.assertEqual(event["time_s"], 0.68)
            self.assertEqual(event["deltaT_s"], 0.02)
            self.assertEqual(event["T0_K"], -1.5)
