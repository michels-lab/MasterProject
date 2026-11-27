"""Parser contract tests using synthetic log fragments, not CFD evidence."""
import csv
import io
import unittest
from audit_recovered_200s_log import parse_log

def parse(s):
    files={k:io.StringIO() for k in ("continuity","linear_solves","courant")}
    result=parse_log(io.StringIO(s),{k:csv.writer(v) for k,v in files.items()})
    return result,{k:list(csv.reader(io.StringIO(v.getvalue()))) for k,v in files.items()}

CONT="time step continuity errors : sum local = 2e-5, global = -1e-6, cumulative = -2e-6\n"
PRESS="GAMG: Solving for p_rgh, Initial residual = 0.2, Final residual = 1e-8, No Iterations 3\n"
EXEC="ExecutionTime = 1 s  ClockTime = 1 s\n"

class LogAudit(unittest.TestCase):
    def test_multiple_correctors_and_previous_time_marker(self):
        result,rows=parse("Courant Number mean: 0.01 max: 0.2\nTime = 0.001s\n"
            "Solving for fluid region metal\n"+PRESS+CONT+PRESS+CONT+EXEC+
            "Courant Number mean: 0.02 max: 0.26\nTime = 0.002s\n"
            "Solving for fluid region metal\n"+PRESS+CONT+EXEC+"End\n")
        self.assertEqual(result["time_markers"],2)
        self.assertEqual(result["steps_with_exactly_one_execution_time"],2)
        self.assertEqual(result["continuity_events"],3)
        self.assertEqual(result["steps_with_continuity"],2)
        self.assertEqual(result["pressure_events"],3)
        self.assertEqual(result["max_logged_courant"],.26)
        self.assertEqual(result["last_cumulative_continuity_as_printed"],-2e-6)
        self.assertEqual(rows["continuity"][0][3],"metal")
        self.assertEqual(rows["courant"][0][2],"")
        self.assertEqual(rows["courant"][1][2],"0.001")

    def test_missing_and_malformed_not_replaced_by_zero(self):
        r,_=parse("Time = 1\n"+PRESS+
            "time step continuity errors : sum local = nan, global = 0, cumulative = 0\n"+EXEC+"End\n")
        self.assertEqual(r["malformed_diagnostic_lines"],1)
        self.assertIsNone(r["last_cumulative_continuity_as_printed"])
        self.assertEqual(r["steps_with_continuity"],0)

    def test_non_increasing_time_rejected(self):
        with self.assertRaisesRegex(ValueError,"non-increasing"):
            parse("Time = 1\nTime = 1\n")

    def test_incomplete_fatal_step_not_counted(self):
        r,_=parse("Time = 1\n"+PRESS+CONT+"FOAM FATAL ERROR:\n")
        self.assertEqual(r["fatal_markers"],1)
        self.assertEqual(r["steps_with_exactly_one_execution_time"],0)
        self.assertEqual(r["end_markers"],0)

    def test_region_reset_and_repeated_execution(self):
        r,rows=parse("Time = 1\nSolving for fluid region metal\n"+PRESS+EXEC+
            "Time = 2\n"+PRESS+EXEC+EXEC+"End\n")
        self.assertEqual(r["steps_with_exactly_one_execution_time"],1)
        self.assertEqual(rows["linear_solves"][-1][3],"")

if __name__=="__main__":
    unittest.main()
