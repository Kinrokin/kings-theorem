"""
AID: /src/kernels/arbiter_v47.py
Proof ID: PRF-ARB-008A-LIVE
"""
from src.governance.nemo_guard import DeontologicalGuardrail
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.primitives.merkle_ledger import MerkleLedger


class ArbiterKernelV47:
    def __init__(
        self,
        guardrail: DeontologicalGuardrail,
        ledger: MerkleLedger,
        student: StudentKernelV42,
        teacher: TeacherKernelV45,
    ):
        self.guardrail = guardrail
        self.ledger = ledger
        self.student = student
        self.teacher = teacher

    def adjudicate(self, problem):
        self.ledger.log("Arbiter", "Start", f"Adjudicating: {problem.get('task', 'Unknown')}")

        # 1. Run the Student (Real LLM Call via StudentKernelV42)
        student_out = self.student.staged_solve_pipeline(problem)

        # 2. Evaluate Result
        final = {}
        if student_out["status"] == "PASS (Student)":
            # Check the TEXT of the solution for ethical violations
            solution_text = student_out.get("solution", "")

            # Ask the Guardrail to check the content text
            passed, reason = self.guardrail.validate_content(solution_text)

            if not passed:
                # Log veto reason to ledger
                self.ledger.log("Arbiter", "VETO", reason)
                final = {"outcome": "VETOED", "reason": reason, "data": student_out}
            else:
                final = {"outcome": "SOLVED", "source": "Student", "data": student_out}

        elif student_out["status"] == "SIT":
            # Failover to Teacher if Student fails/timeouts
            teacher_out = self.teacher.mopfo_pipeline(problem)
            final = {"outcome": "SOLVED", "source": "Teacher (Heuristic)", "data": teacher_out}

        else:
            final = {"outcome": "FAILED", "source": "System Exhaustion", "data": None}

        self.ledger.log("Arbiter", "Ruling", final["outcome"])
        return final
