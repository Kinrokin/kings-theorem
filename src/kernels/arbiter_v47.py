"""
AID: /src/kernels/arbiter_v47.py
Proof ID: PRF-ARB-008A-LIVE
"""

from src.governance.guardrail_dg_v1 import DeontologicalGuardrail
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.primitives.dual_ledger import DualLedger
from src.ethics.manifold import EthicalManifold, ManifoldProjector
import logging

logger = logging.getLogger("kt.arbiter")


class ArbiterKernelV47:
    def __init__(
        self,
        guardrail: DeontologicalGuardrail,
        ledger: DualLedger,
        student: StudentKernelV42,
        teacher: TeacherKernelV45,
        ethical_manifold: EthicalManifold | None = None,
    ):
        self.guardrail = guardrail
        self.ledger = ledger
        self.student = student
        self.teacher = teacher
        self.manifold_projector = ManifoldProjector(ethical_manifold) if ethical_manifold else None

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

        # 3. Ethical manifold projection (if configured)
        if self.manifold_projector:
            # Derive a naive ethical vector from outcome contents (placeholder heuristic)
            text = student_out.get("solution", "") if isinstance(student_out, dict) else ""
            # Simple proxy counts (could be replaced by classifier outputs)
            vector = {
                "fairness": 0.8 if "fair" in text.lower() else 0.5,
                "non_maleficence": 0.9 if "harm" not in text.lower() else 0.4,
                "autonomy": 0.7,
                "truth": 0.6 if "verify" in text.lower() else 0.5,
            }
            projected, inside = self.manifold_projector.project(vector)
            delta = {k: projected[k] - vector.get(k, 0.0) for k in projected}
            final["ethical_vector"] = vector
            final["ethical_projected"] = projected
            final["ethical_in_manifold"] = inside
            final["ethical_delta"] = delta
            self.ledger.log(
                "Arbiter",
                "Manifold",
                {
                    "inside": inside,
                    "delta": delta,
                },
            )
            logger.info("[Arbiter] Ethical manifold applied (inside=%s)", inside)

        self.ledger.log("Arbiter", "Ruling", final["outcome"])
        return final
