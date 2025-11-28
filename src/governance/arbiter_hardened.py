"""
Titanium X Hardened Arbiter - Uniform Ethics Enforcement
=========================================================

Adversarial improvements:
- Vet BOTH Student and Teacher outputs with identical policy pack
- Return FAILED state with full provenance when both vetoed
- Structured ExecResult integration for timeout handling
- Decision ledger with cryptographic sealing
- No bypasses: every path goes through guardrails

Constitutional compliance: Axiom 6 (ethics ≥ 0.7), Axiom 4 (recursive self-interrogation)
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from ..engine.executor import run_with_timeout

# Import hardened primitives
from ..governance.guardrail_v2 import (
    PolicyPack,
    PrefilterCache,
    RiskLevel,
    VetResult,
    get_baseline_policy_pack,
    vet_text,
)
from ..governance.sigma_text import to_sigma_text
from ..ledger.append_only import AppendOnlyLedger
from ..metrics.trinity import compute_trinity
from .semantic_guard import get_semantic_guard

logger = logging.getLogger(__name__)


class ArbiterDecision(Enum):
    """Final arbiter verdict."""

    APPROVED = "approved"  # At least one path passed
    FAILED = "failed"  # Both paths vetoed
    ERROR = "error"  # Execution error before decision
    TIMEOUT = "timeout"  # Deadline exceeded


@dataclass
class BlindedOutput:
    """
    Doubly-blind output wrapper preventing role leakage.

    Attributes:
        job_id: Pseudorandom job identifier (prevents order correlation)
        content: The actual output text
        true_role: Actual role (student/teacher) - NOT revealed to vetting
        vetting_role: Masked role tag for ledger provenance
    """

    job_id: str
    content: str
    true_role: str
    vetting_role: str

    @classmethod
    def create_pair(cls, student_output: str, teacher_output: str) -> Tuple["BlindedOutput", "BlindedOutput"]:
        """
        Create pseudorandomly ordered blinded pair.

        Args:
            student_output: Student kernel output
            teacher_output: Teacher kernel output

        Returns:
            Tuple of (output_a, output_b) in randomized order
        """
        # Generate cryptographically random job IDs
        job_a = secrets.token_hex(16)
        job_b = secrets.token_hex(16)

        # Pseudorandom ordering (prevents positional bias)
        order_seed = secrets.randbelow(2)

        if order_seed == 0:
            # Student first
            output_a = cls(job_a, student_output, "student", f"agent_{job_a[:8]}")
            output_b = cls(job_b, teacher_output, "teacher", f"agent_{job_b[:8]}")
        else:
            # Teacher first
            output_a = cls(job_a, teacher_output, "teacher", f"agent_{job_a[:8]}")
            output_b = cls(job_b, student_output, "student", f"agent_{job_b[:8]}")

        return output_a, output_b


@dataclass
class ArbiterResult:
    """
    Complete arbiter decision with provenance.

    Attributes:
        decision: Final verdict (ArbiterDecision enum)
        student_vet: VetResult from student path
        teacher_vet: Optional VetResult from teacher path (None if not run)
        chosen_output: Selected output (student or teacher), None if FAILED
        provenance: Full decision audit trail
        ledger_hash: Hash of sealed ledger entry
        timestamp: ISO 8601 timestamp
    """

    decision: ArbiterDecision
    student_vet: VetResult
    teacher_vet: Optional[VetResult]
    chosen_output: Optional[str]
    provenance: Dict[str, Any]
    ledger_hash: Optional[str]
    timestamp: str

    def to_dict(self) -> Dict:
        """Serialize for ledger storage."""
        return {
            "decision": self.decision.value,
            "student_vet": self.student_vet.to_dict(),
            "teacher_vet": self.teacher_vet.to_dict() if self.teacher_vet else None,
            "chosen_output": self.chosen_output,
            "provenance": self.provenance,
            "ledger_hash": self.ledger_hash,
            "timestamp": self.timestamp,
        }


class HardenedArbiter:
    """
    Uniform ethics arbiter with no bypass paths.

    Flow:
    1. Execute Student with timeout
    2. Vet Student output with policy pack
    3. If Student vetoed, execute Teacher
    4. Vet Teacher output with SAME policy pack
    5. If both vetoed, return FAILED with full provenance
    6. Seal decision in append-only ledger
    """

    def __init__(
        self,
        ledger: AppendOnlyLedger,
        policy_pack: Optional[PolicyPack] = None,
        student_timeout: float = 10.0,
        teacher_timeout: float = 30.0,
        locale: str = "en",
    ):
        """
        Initialize hardened arbiter.

        Args:
            ledger: AppendOnlyLedger for decision sealing
            policy_pack: Optional PolicyPack (uses baseline if None)
            student_timeout: Student execution timeout (seconds)
            teacher_timeout: Teacher execution timeout (seconds)
            locale: Locale for guardrail checking
        """
        self.ledger = ledger
        self.policy_pack = policy_pack or get_baseline_policy_pack()
        self.prefilter = PrefilterCache()
        self.student_timeout = student_timeout
        self.teacher_timeout = teacher_timeout
        self.locale = locale

        logger.info(
            f"HardenedArbiter initialized: policy={self.policy_pack.id}, "
            f"student_timeout={student_timeout}s, teacher_timeout={teacher_timeout}s"
        )

    async def arbitrate(
        self, student_fn: Any, teacher_fn: Any, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> ArbiterResult:
        """
        Execute full arbitration pipeline with uniform vetting.

        Args:
            student_fn: Async callable for student generation
            teacher_fn: Async callable for teacher generation
            prompt: Original user prompt
            context: Optional context dictionary

        Returns:
            ArbiterResult with decision and provenance
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        provenance: Dict[str, Any] = {
            "prompt_hash": hash(prompt),
            "policy_version": self.policy_pack.version,
            "locale": self.locale,
            "context": context or {},
        }

        # Phase 1: Execute and vet Student
        logger.info("Phase 1: Executing Student kernel")
        student_exec = await run_with_timeout(student_fn, timeout_sec=self.student_timeout, task_name="Student")

        if not student_exec.is_success():
            # Student execution failed
            logger.error(f"Student execution failed: {student_exec.error_code.value}")
            provenance["student_error"] = student_exec.to_dict()

            # Try Teacher as fallback
            return await self._handle_student_failure(teacher_fn, prompt, provenance, timestamp)

        student_output = student_exec.data
        logger.info(f"Student generated {len(student_output)} chars")

        # Pre-veto via Semantic Guard (Dense Symbolic Mesh) before regex pack
        sg = get_semantic_guard()
        sg_result = sg.assess(student_output)
        if sg_result.is_blocked:
            # Log risk event with specific synonym trigger
            try:
                self.ledger.log_risk_event(sg_result.to_dict(), provenance["prompt_hash"])
            except Exception as e:
                logger.warning("Ledger risk log (student) failed: %s", e)
            # Map to VetResult for uniform handling
            student_vet = VetResult(
                decision="veto",
                risk_level=RiskLevel.CRITICAL,
                score=1.0,
                hits=["symbolic_block"],
                role="student",
                policy_version=self.policy_pack.version,
                timestamp=timestamp,
                decoded_variants=1,
                locale=self.locale,
            )
            provenance["semantic_guard_student"] = sg_result.to_dict()
        else:
            # Vet Student output with policy pack
            student_vet = vet_text(
                text=student_output, pack=self.policy_pack, role="student", locale=self.locale, prefilter=self.prefilter
            )
        provenance["student_vet"] = student_vet.to_dict()

        if student_vet.decision == "allow":
            # Student passed - compute σ-text + Trinity (metadata only)
            try:
                sigma_s = to_sigma_text(student_output)
                provenance["sigma_student_sha256"] = sigma_s.text_sha256
                provenance["sigma_student_len"] = sigma_s.length
                provenance["sigma_path"] = "student_only"
            except Exception as e:
                logger.warning("Sigma computation (student) failed: %s", e)
            try:
                tri = compute_trinity(student_output, student_output)
                provenance["trinity"] = {
                    "divergence": tri.divergence,
                    "epistemic": tri.epistemic,
                    "risk": tri.risk,
                    "composite": tri.composite,
                }
            except Exception as e:
                logger.warning("Trinity computation failed: %s", e)

            # Student passed - seal and return
            logger.info("Student APPROVED by guardrails")
            ledger_hash = self.ledger.append(
                {
                    "decision": ArbiterDecision.APPROVED.value,
                    "chosen": "student",
                    "provenance": provenance,
                    "timestamp": timestamp,
                }
            )

            return ArbiterResult(
                decision=ArbiterDecision.APPROVED,
                student_vet=student_vet,
                teacher_vet=None,
                chosen_output=student_output,
                provenance=provenance,
                ledger_hash=ledger_hash,
                timestamp=timestamp,
            )

        # Phase 2: Student vetoed - execute Teacher with SAME policy pack
        logger.warning("Student VETOED - executing Teacher for review")
        return await self._handle_student_veto(teacher_fn, student_vet, student_output, prompt, provenance, timestamp)

    async def _handle_student_failure(
        self, teacher_fn: Any, prompt: str, provenance: Dict, timestamp: str
    ) -> ArbiterResult:
        """Handle Student execution failure by trying Teacher."""
        logger.info("Phase 2: Student failed - executing Teacher")

        teacher_exec = await run_with_timeout(teacher_fn, timeout_sec=self.teacher_timeout, task_name="Teacher")

        if not teacher_exec.is_success():
            # Both failed
            logger.error(f"Teacher execution also failed: {teacher_exec.error_code.value}")
            provenance["teacher_error"] = teacher_exec.to_dict()

            ledger_hash = self.ledger.append(
                {"decision": ArbiterDecision.ERROR.value, "provenance": provenance, "timestamp": timestamp}
            )

            # Create placeholder vet results for error case
            from ..governance.guardrail_v2 import RiskLevel, VetResult

            error_vet = VetResult(
                decision="veto",
                risk_level=RiskLevel.CRITICAL,
                score=1.0,
                hits=["execution_error"],
                role="student",
                policy_version=self.policy_pack.version,
                timestamp=timestamp,
            )

            return ArbiterResult(
                decision=ArbiterDecision.ERROR,
                student_vet=error_vet,
                teacher_vet=None,
                chosen_output=None,
                provenance=provenance,
                ledger_hash=ledger_hash,
                timestamp=timestamp,
            )

        teacher_output = teacher_exec.data
        logger.info(f"Teacher generated {len(teacher_output)} chars")

        # Pre-veto teacher via Semantic Guard (Dense Symbolic Mesh)
        sg_t = get_semantic_guard()
        sg_t_result = sg_t.assess(teacher_output)
        if sg_t_result.is_blocked:
            try:
                self.ledger.log_risk_event(sg_t_result.to_dict(), provenance["prompt_hash"])
            except Exception as e:
                logger.warning("Ledger risk log (teacher) failed: %s", e)
            teacher_vet = VetResult(
                decision="veto",
                risk_level=RiskLevel.CRITICAL,
                score=1.0,
                hits=["symbolic_block"],
                role="teacher",
                policy_version=self.policy_pack.version,
                timestamp=timestamp,
                decoded_variants=1,
                locale=self.locale,
            )
            provenance["semantic_guard_teacher"] = sg_t_result.to_dict()
        else:
            # Vet Teacher with SAME policy pack
            teacher_vet = vet_text(
                text=teacher_output, pack=self.policy_pack, role="teacher", locale=self.locale, prefilter=self.prefilter
            )
        provenance["teacher_vet"] = teacher_vet.to_dict()

        if teacher_vet.decision == "allow":
            logger.info("Teacher APPROVED by guardrails (Student failed)")
            ledger_hash = self.ledger.append(
                {
                    "decision": ArbiterDecision.APPROVED.value,
                    "chosen": "teacher",
                    "provenance": provenance,
                    "timestamp": timestamp,
                }
            )

            # Create placeholder student vet for this case
            from ..governance.guardrail_v2 import RiskLevel, VetResult

            error_vet = VetResult(
                decision="veto",
                risk_level=RiskLevel.CRITICAL,
                score=1.0,
                hits=["execution_error"],
                role="student",
                policy_version=self.policy_pack.version,
                timestamp=timestamp,
            )

            return ArbiterResult(
                decision=ArbiterDecision.APPROVED,
                student_vet=error_vet,
                teacher_vet=teacher_vet,
                chosen_output=teacher_output,
                provenance=provenance,
                ledger_hash=ledger_hash,
                timestamp=timestamp,
            )

        # Both failed
        logger.error("Both Student and Teacher failed execution")
        ledger_hash = self.ledger.append(
            {
                "decision": ArbiterDecision.FAILED.value,
                "reason": "both_execution_failed",
                "provenance": provenance,
                "timestamp": timestamp,
            }
        )

        from ..governance.guardrail_v2 import RiskLevel, VetResult

        error_vet = VetResult(
            decision="veto",
            risk_level=RiskLevel.CRITICAL,
            score=1.0,
            hits=["execution_error"],
            role="student",
            policy_version=self.policy_pack.version,
            timestamp=timestamp,
        )

        return ArbiterResult(
            decision=ArbiterDecision.FAILED,
            student_vet=error_vet,
            teacher_vet=teacher_vet,
            chosen_output=None,
            provenance=provenance,
            ledger_hash=ledger_hash,
            timestamp=timestamp,
        )

    async def _handle_student_veto(
        self,
        teacher_fn: Any,
        student_vet: VetResult,
        student_output: str,
        prompt: str,
        provenance: Dict,
        timestamp: str,
    ) -> ArbiterResult:
        """Handle Student veto with doubly-blind Teacher evaluation."""
        teacher_exec = await run_with_timeout(teacher_fn, timeout_sec=self.teacher_timeout, task_name="Teacher")

        if not teacher_exec.is_success():
            # Teacher execution failed after Student veto
            logger.error(f"Teacher execution failed: {teacher_exec.error_code.value}")
            provenance["teacher_error"] = teacher_exec.to_dict()

            ledger_hash = self.ledger.append(
                {
                    "decision": ArbiterDecision.FAILED.value,
                    "reason": "student_vetoed_teacher_failed",
                    "provenance": provenance,
                    "timestamp": timestamp,
                }
            )

            return ArbiterResult(
                decision=ArbiterDecision.FAILED,
                student_vet=student_vet,
                teacher_vet=None,
                chosen_output=None,
                provenance=provenance,
                ledger_hash=ledger_hash,
                timestamp=timestamp,
            )

        teacher_output = teacher_exec.data
        logger.info(f"Teacher generated {len(teacher_output)} chars")

        # Add σ-text and Trinity metadata (does not change decision semantics)
        try:
            sigma_s = to_sigma_text(student_output)
            sigma_t = to_sigma_text(teacher_output)
            provenance["sigma_student_sha256"] = sigma_s.text_sha256
            provenance["sigma_teacher_sha256"] = sigma_t.text_sha256
            provenance["sigma_student_len"] = sigma_s.length
            provenance["sigma_teacher_len"] = sigma_t.length
        except Exception as e:
            logger.warning("Sigma computation failed: %s", e)
        try:
            tri = compute_trinity(student_output, teacher_output)
            provenance["trinity"] = {
                "divergence": tri.divergence,
                "epistemic": tri.epistemic,
                "risk": tri.risk,
                "composite": tri.composite,
            }
        except Exception as e:
            logger.warning("Trinity computation failed: %s", e)

        # CRITICAL: Doubly-blind evaluation
        # Arbiter must NOT know which output is Student vs Teacher
        blinded_a, blinded_b = BlindedOutput.create_pair(student_output, teacher_output)

        # Vet both with masked role tags
        vet_a = vet_text(
            text=blinded_a.content,
            pack=self.policy_pack,
            role=blinded_a.vetting_role,  # Masked role
            locale=self.locale,
            prefilter=self.prefilter,
        )

        vet_b = vet_text(
            text=blinded_b.content,
            pack=self.policy_pack,
            role=blinded_b.vetting_role,  # Masked role
            locale=self.locale,
            prefilter=self.prefilter,
        )

        # Unmask and assign to true roles
        if blinded_a.true_role == "teacher":
            teacher_vet = vet_a
            # Student already vetted earlier
        else:
            teacher_vet = vet_b

        # Restore true role tags for ledger provenance
        teacher_vet.role = "teacher"

        provenance["teacher_vet"] = teacher_vet.to_dict()
        provenance["doubly_blind"] = True  # Mark as blinded evaluation

        if teacher_vet.decision == "allow":
            # Teacher passed where Student failed
            logger.info("Teacher APPROVED by guardrails (Student vetoed, doubly-blind)")
            ledger_hash = self.ledger.append(
                {
                    "decision": ArbiterDecision.APPROVED.value,
                    "chosen": "teacher",
                    "student_vetoed": True,
                    "doubly_blind": True,
                    "provenance": provenance,
                    "timestamp": timestamp,
                }
            )

            return ArbiterResult(
                decision=ArbiterDecision.APPROVED,
                student_vet=student_vet,
                teacher_vet=teacher_vet,
                chosen_output=teacher_output,
                provenance=provenance,
                ledger_hash=ledger_hash,
                timestamp=timestamp,
            )

        # Both Student and Teacher vetoed - FAILED state
        logger.error(f"BOTH VETOED (doubly-blind) - Student: {student_vet.score:.3f}, Teacher: {teacher_vet.score:.3f}")
        ledger_hash = self.ledger.append(
            {
                "decision": ArbiterDecision.FAILED.value,
                "reason": "both_vetoed_doubly_blind",
                "student_score": student_vet.score,
                "teacher_score": teacher_vet.score,
                "combined_hits": list(set(student_vet.hits + teacher_vet.hits)),
                "doubly_blind": True,
                "provenance": provenance,
                "timestamp": timestamp,
            }
        )

        return ArbiterResult(
            decision=ArbiterDecision.FAILED,
            student_vet=student_vet,
            teacher_vet=teacher_vet,
            chosen_output=None,
            provenance=provenance,
            ledger_hash=ledger_hash,
            timestamp=timestamp,
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get arbiter statistics from ledger.

        Returns:
            Dictionary with decision counts and policy info
        """
        blocks = self.ledger.get_blocks()

        decisions = {"approved": 0, "failed": 0, "error": 0, "timeout": 0}

        for block in blocks:
            decision = block.entry.get("decision", "unknown")
            if decision in decisions:
                decisions[decision] += 1

        return {
            "total_decisions": len(blocks),
            "decisions": decisions,
            "policy_version": self.policy_pack.version,
            "ledger_stats": self.ledger.get_stats(),
        }
