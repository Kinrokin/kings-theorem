import random
import math
"""
AID: /src/kernels/arbiter_v47.py
Proof ID: PRF-ARB-008A-LIVE
"""
from src.primitives.dual_ledger import DualLedger
from collections import defaultdict
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45





class ArbiterKernelV47:
    def __init__(self, guardrail: DeontologicalGuardrail, ledger: DualLedger, student: StudentKernelV42, teacher: TeacherKernelV45):
        self.guardrail = guardrail
        self.ledger = ledger
        self.student = student
        self.teacher = teacher
        self.kernels = {'student': self.student, 'teacher': self.teacher}
        self.ucb_router = UCBRouter(list(self.kernels.keys())) # Initialize UCBRouter with kernel names

    def adjudicate(self, problem: dict) -> dict:
        self.ledger.log("ADJUDICATION_START", problem)

        selected_kernel_name = self.ucb_router.select_kernel()
        selected_kernel_instance = self.kernels[selected_kernel_name]
        self.ledger.log("UCB_SELECTED_KERNEL", selected_kernel_name)

        final_outcome = "UNRESOLVED"
        final_source = "None"
        final_solution_data = {}
        reward_for_ucb_selection = 0.0 # Reward for the kernel selected by UCB

        # --- Handle initial UCB selection ---
        if selected_kernel_name == 'student':
            self.ledger.log("STUDENT_PIPELINE_START", problem)
            student_result = selected_kernel_instance.staged_solve_pipeline(problem)
            self.ledger.log("STUDENT_PIPELINE_END", student_result)
            student_status = student_result.get("status")
            student_solution = student_result.get("solution")

            if student_status == "PASS (Student)":
                guardrail_passed, guardrail_reason = self.guardrail.validate_content(student_solution)
                self.ledger.log("GUARDRAIL_VALIDATION_STUDENT", guardrail_passed, guardrail_reason)
                if guardrail_passed:
                    final_outcome = "SOLVED"
                    final_source = "Student"
                    final_solution_data = student_result
                    reward_for_ucb_selection = 1.0 # Student successfully solved
                else:
                    final_outcome = "VETOED"
                    final_source = "Guardrail (Student)"
                    final_solution_data = {"outcome": final_outcome, "source": final_source, "reason": guardrail_reason}
                    reward_for_ucb_selection = -1.0 # Student's solution was vetoed
            elif student_status == "SIT":
                self.ledger.log("STUDENT_DEFERS_TO_TEACHER")
                # Student defers, so its direct performance reward is neutral/low
                reward_for_ucb_selection = 0.0 # No direct positive outcome from student itself for this action
            else: # Student failed
                reward_for_ucb_selection = -0.5 # Student failed to solve

            # Update UCB for 'student' based on its direct performance
            self.ucb_router.update('student', reward_for_ucb_selection)

        elif selected_kernel_name == 'teacher':
            self.ledger.log("TEACHER_PIPELINE_START", problem)
            teacher_result = selected_kernel_instance.mopfo_pipeline(problem)
            self.ledger.log("TEACHER_PIPELINE_END", teacher_result)
            teacher_status = teacher_result.get("status")
            teacher_solution = teacher_result.get("solution")

            if teacher_status == "SALVAGEABLE":
                guardrail_passed, guardrail_reason = self.guardrail.validate_content(teacher_solution)
                self.ledger.log("GUARDRAIL_VALIDATION_TEACHER", guardrail_passed, guardrail_reason)
                if guardrail_passed:
                    final_outcome = "SOLVED"
                    final_source = "Teacher (Heuristic)"
                    final_solution_data = teacher_result
                    reward_for_ucb_selection = 1.0 # Teacher successfully solved
                else:
                    final_outcome = "VETOED"
                    final_source = "Guardrail (Teacher)"
                    final_solution_data = {"outcome": final_outcome, "source": final_source, "reason": guardrail_reason}
                    reward_for_ucb_selection = -1.0 # Teacher's solution was vetoed
            else: # Teacher failed
                reward_for_ucb_selection = -0.5 # Teacher failed to solve

            # Update UCB for 'teacher' based on its direct performance
            self.ucb_router.update('teacher', reward_for_ucb_selection)

        # --- Handle fallback logic if initial selection didn't resolve or student SIT ---
        # This part should only set final_outcome/source if it's currently UNRESOLVED
        # due to a student SIT or failure. If teacher was selected, its outcome is already final_outcome.
        if final_outcome == "UNRESOLVED": # Means student failed or SIT, and no direct solution yet
            # If student was selected and SIT/failed, we now try teacher as fallback.
            self.ledger.log("FALLBACK_TO_TEACHER_AFTER_STUDENT_FAILURE_OR_SIT")
            teacher_result = self.teacher.mopfo_pipeline(problem) # Use self.teacher here as it's the fallback
            teacher_status = teacher_result.get("status")
            teacher_solution = teacher_result.get("solution")

            if teacher_status == "SALVAGEABLE":
                guardrail_passed, guardrail_reason = self.guardrail.validate_content(teacher_solution)
                if guardrail_passed:
                    final_outcome = "SOLVED"
                    final_source = "Teacher (Heuristic)"
                    final_solution_data = teacher_result
                else:
                    final_outcome = "VETOED"
                    final_source = "Guardrail (Teacher)"
                    final_solution_data = {"outcome": final_outcome, "source": final_source, "reason": guardrail_reason}
            # If teacher also fails, final_outcome remains UNRESOLVED

        # No UCB update for fallback actions, as UCB didn't directly choose this path.
        # This keeps the UCB clean for its explicit choices.

        self.ledger.log("ADJUDICATION_END", final_outcome, final_source)
        return {"outcome": final_outcome, "source": final_source, "solution": final_solution_data.get("solution"), **final_solution_data}
class UCBRouter:
    def __init__(self, kernels):
        self.kernels = kernels # List of available kernel identifiers
        self.rewards = defaultdict(float) # Wi: Total rewards for each kernel
        self.plays = defaultdict(int)     # Ni: Total times each kernel has been selected
        self.total_plays = 0              # t: Total number of rounds/decisions made

    def select_kernel(self):
        self.total_plays += 1

        # Initialize unplayed kernels with an optimistic high value
        # to ensure they are explored at least once
        for kernel in self.kernels:
            if self.plays[kernel] == 0:
                return kernel

        best_kernel = None
        max_ucb_value = -1.0

        for kernel in self.kernels:
            # Calculate the average reward (exploitation term)
            avg_reward = self.rewards[kernel] / self.plays[kernel]

            # Calculate the exploration term (square root part of UCB formula)
            exploration_term = math.sqrt((2 * math.log(self.total_plays)) / self.plays[kernel])

            # Calculate UCB value
            ucb_value = avg_reward + exploration_term

            if ucb_value > max_ucb_value:
                max_ucb_value = ucb_value
                best_kernel = kernel

        return best_kernel

    def update(self, kernel, reward):
        # Update rewards and plays for the selected kernel
        self.rewards[kernel] += reward
        self.plays[kernel] += 1