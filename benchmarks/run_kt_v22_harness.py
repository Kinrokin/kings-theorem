# ruff: noqa: E402
import os
import sys

import numpy as np

# Path Correction
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.primitives.risk_math import calculate_cvar, calculate_intracluster_correlation


def run_benchmarks():
    import logging

    logger = logging.getLogger(__name__)
    logger.info("--- KT-v22 AXIOM HARNESS (Primitives Certified) ---")
    cvar = calculate_cvar(np.array([10, 100, 100]), alpha=0.99)
    rho = calculate_intracluster_correlation(np.array([1, 1, 1]))
    logger.info("[TEST] Axiom 1 (CVaR): %s", "PASS" if cvar == 100.0 else "FAIL")
    logger.info("[TEST] Axiom 4 (Rho/Fatigue): %s", "PASS" if rho == 1.0 else "FAIL")


if __name__ == "__main__":
    run_benchmarks()
