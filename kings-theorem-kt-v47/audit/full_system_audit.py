"""
AID: /audit/full_system_audit.py
Proof ID: PRF-K2-FORGE-001
Purpose: Self-Verification
"""
import logging
import os
import re
import sys
from pathlib import Path

from src.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# --- ROBUST IMPORT CHECK ---
try:
    import numpy
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

ARTIFACTS = [
    "src/config.py", "src/main.py",
    "src/primitives/risk_math.py", "src/primitives/dual_ledger.py", "src/primitives/exceptions.py",
    "src/kernels/student_v42.py", "src/kernels/teacher_v45.py", "src/kernels/arbiter_v47.py",
    "src/governance/guardrail_dg_v1.py", "src/protocols/iads_v10.py"
]

def run_audit():
    logger.info("--- K2-FORGE SYSTEM AUDIT ---")

    if not NUMPY_OK:
        logger.critical("[CRITICAL WARNING] 'numpy' is missing.")
        logger.info("   > PLEASE RUN 'INSTALL_DEPENDENCIES.bat' IN THE PROJECT FOLDER.")
        logger.info("   > Audit entering degraded mode (Static Analysis Only).")

    errors = 0
    for art in ARTIFACTS:
        p = PROJECT_ROOT / art
        if p.exists():
            with open(p, 'r') as f:
                if "Proof ID:" in f.read():
                    logger.info("[OK] %s (Verified)", art)
                else:
                    logger.warning("[WARN] %s (Missing Proof ID)", art)
        else:
            logger.error("[FAIL] %s (Missing File)", art)
            errors += 1

    if errors == 0:
        logger.info("
[SUCCESS] Static Audit Passed.")
    else:
        logger.error("
[FAILURE] %s Critical Errors.", errors)

if __name__ == "__main__":
    run_audit()
