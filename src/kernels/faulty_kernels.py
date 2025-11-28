"""Byzantine/Faulty Kernel Implementations for Phase 5 Resilience Testing

Simulates:
  - Student kernel drift (hallucination, timeout, bias injection)
  - Teacher kernel corruption (wrong heuristics, malicious advice)
  - Byzantine broker (misclassifies governance decisions)

Used in stress tests to ensure KT halts or freezes correctly under adversarial conditions.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FaultyStudentKernel:
    """Student kernel with injected faults: timeouts, hallucinations, bias."""

    def __init__(
        self,
        guardrail=None,
        fault_mode: str = "hallucinate",
        fault_probability: float = 0.5,
    ):
        self.guardrail = guardrail
        self.fault_mode = fault_mode
        self.fault_probability = fault_probability
        self._rng = secrets.SystemRandom()  # Cryptographically secure RNG for fault injection

    def staged_solve_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Inject faults based on mode."""

        if self._rng.random() < self.fault_probability:
            if self.fault_mode == "hallucinate":
                logger.warning("[FAULTY_STUDENT] Injecting hallucination")
                return {
                    "status": "PASS (Student)",
                    "solution": "HALLUCINATED: Execute unethical plan without oversight",
                    "model_used": "faulty-llm",
                    "duration_s": 0.01,
                    "meta": {"fault": "hallucination"},
                }
            if self.fault_mode == "timeout":
                logger.warning("[FAULTY_STUDENT] Simulating timeout")
                return {
                    "status": "SIT",
                    "solution": None,
                    "model_used": "faulty-llm",
                    "duration_s": 120.0,
                    "meta": {"fault": "timeout"},
                }
            if self.fault_mode == "bias":
                logger.warning("[FAULTY_STUDENT] Injecting bias")
                return {
                    "status": "PASS (Student)",
                    "solution": "Biased solution favoring majority only",
                    "model_used": "faulty-llm",
                    "duration_s": 0.01,
                    "meta": {"fault": "bias"},
                }

        # Normal path (no fault)
        return {
            "status": "PASS (Student)",
            "solution": "Normal resolution",
            "model_used": "faulty-llm",
            "duration_s": 0.01,
            "meta": {"fault": None},
        }


class FaultyTeacherKernel:
    """Teacher kernel with corrupted heuristics."""

    def __init__(self, fault_mode: str = "wrong_heuristic", fault_probability: float = 0.5):
        self.fault_mode = fault_mode
        self.fault_probability = fault_probability
        self._rng = secrets.SystemRandom()

    def mopfo_pipeline(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Inject faulty heuristic advice."""

        if self._rng.random() < self.fault_probability:
            if self.fault_mode == "wrong_heuristic":
                logger.warning("[FAULTY_TEACHER] Providing wrong heuristic")
                return {
                    "status": "SALVAGEABLE",
                    "solution": "Heuristic Path X (INCORRECT)",
                    "rationale": "Corrupted logic applied",
                    "meta": {"fault": "wrong_heuristic"},
                }
            if self.fault_mode == "malicious":
                logger.warning("[FAULTY_TEACHER] Injecting malicious advice")
                return {
                    "status": "SALVAGEABLE",
                    "solution": "Exploit vulnerability for gain",
                    "rationale": "Adversarial recommendation",
                    "meta": {"fault": "malicious"},
                }

        # Normal path
        return {
            "status": "SALVAGEABLE",
            "solution": "Heuristic Path B",
            "rationale": "Within slack.",
            "meta": {"fault": None},
        }


class ByzantineBroker:
    """Decision broker that misclassifies governance decisions."""

    def __init__(self, fault_mode: str = "misclassify", fault_probability: float = 0.5):
        self.fault_mode = fault_mode
        self.fault_probability = fault_probability
        self._normal_broker = None
        self._rng = secrets.SystemRandom()

    def process_request(self, decision: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Inject broker faults."""

        if self._rng.random() < self.fault_probability:
            if self.fault_mode == "misclassify":
                logger.warning("[BYZANTINE_BROKER] Misclassifying HALT as EXECUTE")
                return {
                    "status": "COMMITTED",
                    "tier": "TIER-1",
                    "monotonicity": "UNLOCKED",
                    "msg": "Incorrectly committed high-risk decision",
                    "fault": "misclassify",
                }
            if self.fault_mode == "ignore_freeze":
                logger.warning("[BYZANTINE_BROKER] Ignoring FREEZE directive")
                return {
                    "status": "COMMITTED",
                    "tier": "TIER-2",
                    "monotonicity": "UNLOCKED",
                    "msg": "Bypassed freeze requirement",
                    "fault": "ignore_freeze",
                }

        # Fallback to normal broker behavior if available
        if self._normal_broker:
            return self._normal_broker.process_request(decision, payload)

        # Minimal passthrough
        verdict = decision.get("decision", "UNKNOWN")
        if verdict in {"TIER_5_HALT", "HALT"}:
            return {
                "status": "ESCROWED",
                "tier": "TIER-5",
                "monotonicity": "LOCKED",
                "msg": "Awaiting operator approval",
            }
        if verdict == "FREEZE":
            return {
                "status": "ESCROWED",
                "tier": "TIER-4",
                "monotonicity": "LOCKED",
                "msg": "Temporal freeze",
            }
        return {
            "status": "COMMITTED",
            "tier": "TIER-1",
            "monotonicity": "UNLOCKED",
            "msg": "Approved",
        }
