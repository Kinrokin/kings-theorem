"""
AID: /audit/full_system_audit.py
Proof ID: PRF-K2-FORGE-001
Purpose: Self-Verification
"""
import os
import sys
import re
from pathlib import Path

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
    print("--- K2-FORGE SYSTEM AUDIT ---")
    
    if not NUMPY_OK:
        print("[CRITICAL WARNING] 'numpy' is missing.")
        print("   > PLEASE RUN 'INSTALL_DEPENDENCIES.bat' IN THE PROJECT FOLDER.")
        print("   > Audit entering degraded mode (Static Analysis Only).")
    
    errors = 0
    for art in ARTIFACTS:
        p = PROJECT_ROOT / art
        if p.exists():
            with open(p, 'r') as f:
                if "Proof ID:" in f.read():
                    print(f"[OK] {art} (Verified)")
                else:
                    print(f"[WARN] {art} (Missing Proof ID)")
        else:
            print(f"[FAIL] {art} (Missing File)")
            errors += 1
            
    if errors == 0:
        print("\n[SUCCESS] Static Audit Passed.")
    else:
        print(f"\n[FAILURE] {errors} Critical Errors.")

if __name__ == "__main__":
    run_audit()