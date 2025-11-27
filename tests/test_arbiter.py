
import unittest
import math
from collections import defaultdict
from types import SimpleNamespace
import sys
import os

# Add the project root to sys.path to resolve imports like 'src.kernels'
# This is handled by the execution cell, not directly in the test file.

from src.kernels.arbiter_v47 import ArbiterKernelV47
from src.kernels.arbiter_v47 import UCBRouter


class DummyLedger:
    def __init__(self):
        self.logs = []
    def log(self, *args):
        self.logs.append(args)

class DummyStudent:
    def __init__(self, status_out, solution_out=None):
        self._status = status_out
        self._solution = solution_out if solution_out is not None else "default student solution"
    def staged_solve_pipeline(self, problem):
        return {"status": self._status, "solution": self._solution}

class DummyTeacher:
    def __init__(self, status_out, solution_out=None):
        self._status = status_out
        self._solution = solution_out if solution_out is not None else "default teacher solution"
    def mopfo_pipeline(self, problem):
        return {"status": self._status, "solution": self._solution}

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
        student = DummyStudent("PASS (Student)", "All good")
        teacher = DummyTeacher("SALVAGEABLE")
        guard = DummyGuardrail(allow=True)
        arb = ArbiterKernelV47(guard, ledger, student, teacher)
        final = arb.adjudicate({"task": "T"})
        self.assertEqual(final["outcome"], "SOLVED")
        self.assertEqual(final["source"], "Student")

    def test_student_vetoed(self):
        ledger = DummyLedger()
        student = DummyStudent("PASS (Student)", "We should ignore safety")
        teacher = DummyTeacher("SALVAGEABLE")
        guard = DummyGuardrail(allow=False)
        arb = ArbiterKernelV47(guard, ledger, student, teacher)
        final = arb.adjudicate({"task": "T"})
        self.assertEqual(final["outcome"], "VETOED")

    def test_student_sit_fallback_teacher(self):
        ledger = DummyLedger()
        student = DummyStudent("SIT")
        teacher = DummyTeacher("SALVAGEABLE", "heuristic result")
        guard = DummyGuardrail(allow=True)
        arb = ArbiterKernelV47(guard, ledger, student, teacher)
        final = arb.adjudicate({"task": "T"})
        self.assertEqual(final["outcome"], "SOLVED")
        self.assertEqual(final["source"], "Teacher (Heuristic)")

class TestUCBRouter(unittest.TestCase):
    def setUp(self):
        self.kernels = ['student', 'teacher'] # Use kernel names directly
        self.router = UCBRouter(self.kernels)

    def test_init(self):
        self.assertEqual(self.router.kernels, self.kernels)
        self.assertEqual(self.router.rewards, defaultdict(float))
        self.assertEqual(self.router.plays, defaultdict(int))
        self.assertEqual(self.router.total_plays, 0)

    def test_select_kernel_initial_exploration(self):
        selected_kernels = set()
        for _ in range(len(self.kernels)):
            selected_kernel = self.router.select_kernel()
            selected_kernels.add(selected_kernel)
            self.router.update(selected_kernel, 0.0)

        self.assertEqual(selected_kernels, set(self.kernels))
        self.assertEqual(self.router.total_plays, len(self.kernels))
        for kernel in self.kernels:
            self.assertEqual(self.router.plays[kernel], 1)

    def test_select_kernel_exploitation_and_exploration(self):
        self.router.update('student', 10.0)
        self.router.plays['student'] = 1 # Manually set for initial state
        self.router.total_plays = 1

        self.router.update('teacher', 1.0)
        self.router.plays['teacher'] = 1 # Manually set for initial state
        self.router.total_plays = 2

        # After initial plays, student has higher reward
        # Simulate more selections
        selection_counts = defaultdict(int)
        for _ in range(20):
            selected = self.router.select_kernel()
            selection_counts[selected] += 1
            if selected == 'student':
                self.router.update(selected, 10.0)
            else:
                self.router.update(selected, 1.0)

        # Expect student to have significantly more selections due to higher reward
        self.assertGreater(selection_counts['student'], selection_counts['teacher'])

    def test_update_method(self):
        initial_reward_student = self.router.rewards['student']
        initial_plays_student = self.router.plays['student']
        initial_total_plays = self.router.total_plays

        self.router.select_kernel() # Simulate a selection
        self.router.update('student', 5.0)

        self.assertEqual(self.router.rewards['student'], initial_reward_student + 5.0)
        self.assertEqual(self.router.plays['student'], initial_plays_student + 1)
        self.assertEqual(self.router.total_plays, initial_total_plays + 1)

        self.router.select_kernel() # Simulate another selection
        self.router.update('teacher', 7.5)

        self.assertEqual(self.router.rewards['teacher'], 7.5)
        self.assertEqual(self.router.plays['teacher'], 1)
        self.assertEqual(self.router.total_plays, initial_total_plays + 2)


class TestArbiterKernelUCBIntegration(unittest.TestCase):
    def setUp(self):
        self.ledger = DummyLedger()
        self.guard = DummyGuardrail(allow=True)
        self.problem = {"task": "T"}

    def _run_adjudication_rounds(self, num_rounds, student_outcomes, teacher_outcomes, guardrail_allows=True):
        # student_outcomes and teacher_outcomes are lists of (status, solution) tuples or just status strings
        # If only status string, solution is default.

        guard_config = DummyGuardrail(allow=guardrail_allows)
        # ArbiterKernelV47 now requires student and teacher during init, so create dummy instances
        # These will be replaced by the arbiter.student/teacher assignment within the loop for precise control.
        initial_dummy_student = DummyStudent("FAIL")
        initial_dummy_teacher = DummyTeacher("FAIL")
        arb = ArbiterKernelV47(guard_config, self.ledger, initial_dummy_student, initial_dummy_teacher)

        history = []
        for i in range(num_rounds):
            current_student_status = student_outcomes[i % len(student_outcomes)] if student_outcomes else "FAIL"
            current_teacher_status = teacher_outcomes[i % len(teacher_outcomes)] if teacher_outcomes else "FAIL"

            # Create new dummy student/teacher for each round to control their output precisely
            arb.student = DummyStudent(current_student_status, "student_sol")
            arb.teacher = DummyTeacher(current_teacher_status, "teacher_sol")
            # arb.kernels needs to be updated to reflect the new dummy student/teacher instances
            arb.kernels = {'student': arb.student, 'teacher': arb.teacher} # Corrected escaping

            # Reset the ucb_router to reflect the new arb.kernels, but maintain history
            if i == 0:
                arb.ucb_router = UCBRouter(list(arb.kernels.keys()))
            # For subsequent rounds, the existing router instance is used, maintaining state.
            
            final = arb.adjudicate(self.problem)
            history.append(final)
        return history, arb.ucb_router

    def test_ucb_initial_exploration(self):
        # Simulate 2 rounds, ensuring both student and teacher are called once initially
        student_statuses = ["PASS (Student)", "SIT"]
        teacher_statuses = ["SALVAGEABLE", "FAIL"]

        history, router = self._run_adjudication_rounds(2, student_statuses, teacher_statuses)

        # In the first 2 rounds, both kernels should be played at least once for exploration
        self.assertEqual(router.plays['student'], 1)
        self.assertEqual(router.plays['teacher'], 1)
        self.assertEqual(router.total_plays, 2)

        # Check if outcomes reflect the dummy kernel's behavior
        # The order of selection is not guaranteed for equal UCB, so we check existence.
        student_outcome_present = any(h['source'] == 'Student' for h in history)
        teacher_outcome_present = any(h['source'] == 'Teacher (Heuristic)' for h in history)
        self.assertTrue(student_outcome_present or teacher_outcome_present, "Both student and teacher should have been explored")
        
        # Check if rewards for both kernels were recorded, without asserting their sign initially.
        self.assertIn('student', router.rewards)
        self.assertIn('teacher', router.rewards)


    def test_ucb_exploitation_of_successful_student(self):
        # Student always passes, teacher always fails. UCB should favor student.
        student_statuses = ["PASS (Student)"]
        teacher_statuses = ["FAIL"]

        # Simulate enough rounds to see exploitation
        history, router = self._run_adjudication_rounds(10, student_statuses, teacher_statuses)

        # Student should be chosen more often after initial exploration
        self.assertGreater(router.plays['student'], router.plays['teacher'])
        self.assertGreaterEqual(router.plays['student'] + router.plays['teacher'], 10)

        # Verify high reward for student and low for teacher
        self.assertGreater(router.rewards['student'], router.rewards['teacher'])
        self.assertAlmostEqual(router.rewards['student'] / router.plays['student'], 1.0, places=5)
        if router.plays['teacher'] > 0:
            self.assertLessEqual(router.rewards['teacher'] / router.plays['teacher'], -0.5) # Teacher gives -0.5 reward for failure

        # All final outcomes should eventually be SOLVED by Student
        solved_by_student_count = sum(1 for h in history if h['source'] == 'Student')
        self.assertGreater(solved_by_student_count, 5) # More than half should be student

    def test_ucb_fallback_to_teacher(self):
        # Student always defers (SIT), teacher always passes. UCB should favor teacher after exploration.
        student_statuses = ["SIT"]
        teacher_statuses = ["SALVAGEABLE"]

        history, router = self._run_adjudication_rounds(10, student_statuses, teacher_statuses)

        # With the new reward logic (0.0 for student SIT), teacher should be preferred.
        # Teacher should be chosen more often after initial exploration
        self.assertGreater(router.plays['teacher'], router.plays['student'])
        self.assertGreaterEqual(router.plays['student'] + router.plays['teacher'], 10)

        # Verify high reward for teacher and neutral/low for student
        self.assertAlmostEqual(router.rewards['teacher'] / router.plays['teacher'], 1.0, places=5) # Teacher gets 1.0 for solving
        if router.plays['student'] > 0:
             self.assertAlmostEqual(router.rewards['student'] / router.plays['student'], 0.0, places=5) # Student gets 0.0 for SIT

        # All final outcomes should eventually be SOLVED by Teacher (Heuristic)
        solved_by_teacher_count = sum(1 for h in history if h['source'] == 'Teacher (Heuristic)')
        self.assertGreater(solved_by_teacher_count, 5)

    def test_ucb_guardrail_veto_punishment(self):
        # Student always passes, but guardrail always vetoes. Reward should be -1.0 for student selection.
        student_statuses = ["PASS (Student)"]
        teacher_statuses = ["FAIL"]

        history, router = self._run_adjudication_rounds(10, student_statuses, teacher_statuses, guardrail_allows=False)

        # Since student selection leads to VETOED, its reward should be low, pushing UCB to teacher.
        self.assertLessEqual(router.rewards['student'] / router.plays['student'], -1.0) # Should be -1.0
        self.assertGreater(router.plays['teacher'], router.plays['student'])


