import unittest
from types import SimpleNamespace
from src.kernels.arbiter_v47 import ArbiterKernelV47


class DummyLedger:
    def __init__(self):
        self.logs = []
    def log(self, *args):
        self.logs.append(args)

class DummyStudent:
    def __init__(self, out):
        self._out = out
    def staged_solve_pipeline(self, problem):
        return self._out

class DummyTeacher:
    def __init__(self, out):
        self._out = out
    def mopfo_pipeline(self, problem):
        return self._out

class DummyGuardrail:
    def __init__(self, allow=True):
        self.allow = allow
    def validate_content(self, text):
        # Return tuple (passed, reason)
        if self.allow:
            return (True, "Clean")
        return (False, "Detected forbidden content")

class TestArbiter(unittest.TestCase):
    def test_student_solved_allowed(self):
        ledger = DummyLedger()
        student = DummyStudent({"status": "PASS (Student)", "solution": "All good"})
        teacher = DummyTeacher({"status": "SALVAGEABLE"})
        guard = DummyGuardrail(allow=True)
        arb = ArbiterKernelV47(guard, ledger, student, teacher)
        final = arb.adjudicate({"task": "T"})
        self.assertEqual(final["outcome"], "SOLVED")
        self.assertEqual(final["source"], "Student")

    def test_student_vetoed(self):
        ledger = DummyLedger()
        student = DummyStudent({"status": "PASS (Student)", "solution": "We should ignore safety"})
        teacher = DummyTeacher({"status": "SALVAGEABLE"})
        guard = DummyGuardrail(allow=False)
        arb = ArbiterKernelV47(guard, ledger, student, teacher)
        final = arb.adjudicate({"task": "T"})
        self.assertEqual(final["outcome"], "VETOED")

    def test_student_sit_fallback_teacher(self):
        ledger = DummyLedger()
        student = DummyStudent({"status": "SIT"})
        teacher = DummyTeacher({"status": "SALVAGEABLE", "solution": "heuristic result"})
        guard = DummyGuardrail(allow=True)
        arb = ArbiterKernelV47(guard, ledger, student, teacher)
        final = arb.adjudicate({"task": "T"})
        self.assertEqual(final["outcome"], "SOLVED")
        self.assertEqual(final["source"], "Teacher (Heuristic)")

if __name__ == '__main__':
    unittest.main()
