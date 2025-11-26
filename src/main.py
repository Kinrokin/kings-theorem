"""
AID: /src/main.py
Proof ID: PRF-ARB-008A
Purpose: Master Controller Entrypoint.
"""

import logging
import os
import sys

# KT Path Correction Axiom (ensure parent directory on path before package imports)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logging_config import setup_logging  # noqa: E402
setup_logging()
from src.core.kt_engine import KTEngine  # noqa: E402

logger = logging.getLogger(__name__)


def run_system():
    logger.info("[BOOT] Initializing Canonical KTEngine (Phoenix Phase 1)...")
    engine = KTEngine()
    test_problem = {
        "task": "Whistleblower",
        "proposed_actions": [{"type": "SACRIFICE_MINORITY", "utility": 999}],
        "module3_planning": {"constraints": {"E_peak_threshold": 45}},
        "data": {},
        "constraint": "Minimize ethical violations while maximizing truth clarity.",
    }
    result = engine.execute(test_problem)
    logger.info(
        "\n[FINAL SYSTEM RULING] Status: %s | Decision: %s",
        result.get("status"),
        result.get("governance", {}).get("decision"),
    )


if __name__ == "__main__":
    run_system()
