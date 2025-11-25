"""
AID: /src/kernels/arbiter_v47.py
Proof ID: PRF-ARB-008A-LIVE
"""

import logging
from pathlib import Path

from src.arbitration.pce_bundle import PCEBundle, StepResult, hash_blob
from src.ethics.manifold import EthicalManifold, ManifoldProjector
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.ledger.emotion_drift_ledger import append_drift
from src.ledger.pceb_ledger import append_pceb
from src.primitives.dual_ledger import DualLedger
from src.proofs.dsl import parse as parse_dsl
from src.risk.guard import finalize_decision
from src.ux.emotion_drift import EmotionDriftMonitor, classify_tone

logger = logging.getLogger("kt.arbiter")


class ArbiterKernelV47:
    def __init__(
        self,
        guardrail: DeontologicalGuardrail,
        ledger: DualLedger,
        student: StudentKernelV42,
        teacher: TeacherKernelV45,
        ethical_manifold: EthicalManifold | None = None,
        proof_dsl_path: str | None = None,
        emotion_monitor: EmotionDriftMonitor | None = None,
    ):
        self.guardrail = guardrail
        self.ledger = ledger
        self.student = student
        self.teacher = teacher
        self.manifold_projector = ManifoldProjector(ethical_manifold) if ethical_manifold else None
        self.proof_program = None
        if proof_dsl_path and Path(proof_dsl_path).exists():
            try:
                self.proof_program = parse_dsl(Path(proof_dsl_path).read_text(encoding="utf-8"))
                logger.info("[Arbiter] Loaded proof DSL program from %s", proof_dsl_path)
            except Exception as e:
                logger.warning("[Arbiter] Failed to load DSL program: %s", e)
        self.emotion_monitor = emotion_monitor or EmotionDriftMonitor()

    def adjudicate(self, problem):
        self.ledger.log("Arbiter", "Start", f"Adjudicating: {problem.get('task', 'Unknown')}")

        # Build initial PCEB structure
        bundle_steps = []

        # 1. Run the Student (Real LLM Call via StudentKernelV42)
        student_out = self.student.staged_solve_pipeline(problem)
        bundle_steps.append(
            StepResult(
                step_id="student",
                verdict="PASS" if student_out.get("status", "FAIL").startswith("PASS") else "CONTINUE",
                output_artifact={
                    "solution": student_out.get("solution"),
                    "status": student_out.get("status"),
                },
            )
        )

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
            final = {
                "outcome": "SOLVED",
                "source": "Teacher (Heuristic)",
                "data": teacher_out,
            }
            bundle_steps.append(
                StepResult(
                    step_id="teacher",
                    verdict="CONTINUE",
                    output_artifact={
                        "solution": teacher_out.get("solution"),
                        "status": teacher_out.get("status"),
                    },
                )
            )

        else:
            final = {"outcome": "FAILED", "source": "System Exhaustion", "data": None}

        # 3. Compose PCE Bundle & optional DSL proof evaluation
        pceb = PCEBundle(
            bundle_id="pceb-" + hash_blob(problem)[:8],
            initial_input_hash=hash_blob(problem),
            steps=bundle_steps,
            final_output_hash=hash_blob(final),
        )
        final["pceb_id"] = pceb.bundle_id
        final["pceb_vetoed_locally"] = pceb.is_vetoed_locally()
        self.ledger.log("Arbiter", "PCEB", {"id": pceb.bundle_id, "veto": pceb.is_vetoed_locally()})
        try:
            append_pceb(
                pceb.bundle_id,
                len(pceb.steps),
                pceb.is_vetoed_locally(),
                pceb.final_output_hash,
            )
        except Exception as e:
            logger.warning("[Arbiter] Failed to append PCEB ledger record: %s", e)

        if self.proof_program:
            # Build evidence for DSL evaluation
            text = student_out.get("solution", "") if isinstance(student_out, dict) else ""
            evidence = {
                "fairness": 0.75 if "fair" in text.lower() else 0.6,
                "traditions": sum(1 for t in ["christian", "islamic", "hindu", "secular"] if t in text.lower()),
            }
            try:
                theorem_results = self.proof_program.evaluate(evidence)
                final["dsl_theorems"] = theorem_results
                self.ledger.log("Arbiter", "DSL", theorem_results)
            except Exception as e:
                final["dsl_error"] = str(e)
                self.ledger.log("Arbiter", "DSL_ERROR", str(e))

        # 4. Ethical manifold projection (if configured)
        # PRE-GATE: Project before risk analysis to enforce ethical bounds
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
            
            # PRE-GATE ENFORCEMENT: If outside manifold, veto before risk analysis
            if not inside:
                veto_reason = f"Output violates ethical manifold bounds (delta: {delta})"
                self.ledger.log("Arbiter", "MANIFOLD_VETO", {"reason": veto_reason, "delta": delta})
                logger.warning("[Arbiter] Manifold pre-gate veto: %s", veto_reason)
                return {
                    "outcome": "VETOED",
                    "reason": veto_reason,
                    "ethical_vector": vector,
                    "ethical_projected": projected,
                    "ethical_delta": delta,
                    "pceb_id": final.get("pceb_id"),
                }
            
            self.ledger.log(
                "Arbiter",
                "Manifold",
                {
                    "inside": inside,
                    "delta": delta,
                },
            )
            logger.info("[Arbiter] Ethical manifold applied (inside=%s)", inside)

        # 5. Emotion drift monitoring
        solution_text = student_out.get("solution", "") if isinstance(student_out, dict) else ""
        tone = classify_tone(solution_text)
        drift = self.emotion_monitor.record(tone)
        final["emotion_tone"] = tone
        final["emotion_drift"] = drift
        if drift.get("drift_alert"):
            self.ledger.log("Arbiter", "EmotionDrift", drift)
            logger.warning("[Arbiter] Emotion drift alert: %s", drift)
        try:
            append_drift(tone, drift.get("dominance_ratio", 0.0), drift.get("drift_alert", False))
        except Exception as e:
            logger.warning("[Arbiter] Failed to append emotion drift record: %s", e)

        # Risk gating: convert to KTDecision and enforce budget if configured
        try:
            trace_id = pceb.bundle_id
            decision = finalize_decision(final, trace_id)
            if decision.risk:
                self.ledger.log(
                    "Risk",
                    "Profile",
                    {
                        "trace_id": trace_id,
                        "catastrophic_prob": decision.risk.catastrophic_prob,
                        "samples": decision.risk.samples,
                    },
                )
            if decision.answer.get("outcome") == "REFUSED":
                self.ledger.log(
                    "Risk",
                    "Violation",
                    {"trace_id": trace_id, "reason": decision.answer.get("reason")},
                )
                logger.warning("[Arbiter] Risk budget exceeded for %s; fallback engaged", trace_id)
            final = decision.answer
        except Exception as e:
            logger.warning("[Arbiter] Risk gating skipped due to error: %s", e)

        self.ledger.log("Arbiter", "Ruling", final.get("outcome"))
        return final
