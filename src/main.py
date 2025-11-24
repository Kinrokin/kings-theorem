"""
AID: /src/main.py
Proof ID: PRF-ARB-008A
Purpose: Master Controller Entrypoint.
"""

import os
import sys

from src.logging_config import setup_logging

# KT Path Correction Axiom
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

setup_logging()

import logging

import src.config as config
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail
from src.kernels.arbiter_v47 import ArbiterKernelV47
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.primitives.dual_ledger import DualLedger

logger = logging.getLogger(__name__)


def run_system():
    logger.info("[BOOT] Initializing KT-v47 Engine...")
    ledger = DualLedger()
    guard = DeontologicalGuardrail(config.DEONTOLOGICAL_RULES)
    student = StudentKernelV42(guardrail=guard)
    teacher = TeacherKernelV45()
    arbiter = ArbiterKernelV47(guard, ledger, student, teacher)
    logger.info("[BOOT] System Sealed and Ready.")

    test_problem = {
        "task": "Whistleblower",
        "proposed_actions": [{"type": "SACRIFICE_MINORITY", "utility": 999}],
        "module3_planning": {"constraints": {"E_peak_threshold": 45}},
    }

    result = arbiter.adjudicate(test_problem)
    logger.info("\n[FINAL SYSTEM RULING] Outcome: %s", result["outcome"])


if __name__ == "__main__":
    run_system()
