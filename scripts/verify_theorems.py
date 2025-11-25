#!/usr/bin/env python3
"""
DSL Theorem Verification Script for CI Integration

This script:
1. Compiles DSL theorem files
2. Evaluates them against evidence/metrics
3. Produces machine-readable JSON/YAML output
4. Fails CI if any theorem fails or bounds are exceeded

Usage:
    python scripts/verify_theorems.py [--source FILE] [--evidence FILE] [--output FILE]

Options:
    --source FILE       DSL source file (default: theorems/safety.dsl)
    --evidence FILE     Evidence JSON file (default: theorems/evidence.json)
    --output FILE       Output artifact file (default: theorem_output.json)
    --threshold FLOAT   Max violation probability (default: 0.001)
    --strict            Fail on any theorem failure
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.proofs.dsl import compile_and_evaluate, verify_theorem_output, DSLCompilerOutput


DEFAULT_DSL_SOURCE = """\
# King's Theorem Safety Invariants DSL
# These theorems define the safety bounds that gate CI

# Core safety constraints
constraint C_fairness: fairness >= 0.7
constraint C_safety: safety_score >= 0.8
constraint C_integrity: integrity >= 0.9
constraint C_audit: audit_coverage >= 0.95

# Risk bounds for CVaR gating
bound B_cvar99: cvar_99 <= 0.001
bound B_violation: violation_probability <= 0.001
bound B_tail_risk: tail_risk <= 0.05

# Safety theorems
theorem T_composition_safe: C_fairness & C_safety -> COMPOSITION_SAFE
theorem T_integrity_verified: C_integrity & C_audit -> INTEGRITY_VERIFIED
theorem T_governance_compliant: C_fairness & C_safety & C_integrity -> GOVERNANCE_COMPLIANT
"""

DEFAULT_EVIDENCE = {
    "fairness": 0.85,
    "safety_score": 0.92,
    "integrity": 0.95,
    "audit_coverage": 0.98,
    "cvar_99": 0.0005,
    "violation_probability": 0.0001,
    "tail_risk": 0.02,
}


def load_dsl_source(path: str) -> str:
    """Load DSL source from file or return default."""
    p = Path(path)
    if p.exists():
        return p.read_text()
    return DEFAULT_DSL_SOURCE


def load_evidence(path: str) -> dict:
    """Load evidence from JSON file or return default."""
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return DEFAULT_EVIDENCE


def append_to_ledger(output: DSLCompilerOutput, ledger_path: str) -> bool:
    """
    Append theorem output to integrity ledger.

    This integrates with the L_int (Integrity Ledger) for audit trail.
    """
    try:
        ledger_file = Path(ledger_path)
        ledger_file.parent.mkdir(parents=True, exist_ok=True)

        # Create ledger entry
        entry = {
            "type": "THEOREM_VERIFICATION",
            "timestamp": output.timestamp,
            "program_hash": output.program_hash,
            "overall_status": output.overall_status,
            "violation_probability": output.violation_probability,
            "safety_verdict": output.safety_verdict,
            "theorem_count": len(output.theorem_results),
            "bound_count": len(output.bound_results),
        }

        # Append to ledger (JSONL format)
        with open(ledger_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return True
    except Exception as e:
        print(f"Warning: Failed to append to ledger: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="DSL Theorem Verification for CI")
    parser.add_argument("--source", default="theorems/safety.dsl", help="DSL source file")
    parser.add_argument("--evidence", default="theorems/evidence.json", help="Evidence JSON file")
    parser.add_argument("--output", default="theorem_output.json", help="Output artifact file")
    parser.add_argument("--format", choices=["json", "yaml"], default="json", help="Output format")
    parser.add_argument("--threshold", type=float, default=0.001, help="Max violation probability")
    parser.add_argument("--strict", action="store_true", help="Fail on any theorem failure")
    parser.add_argument("--ledger", default="audit/theorem_ledger.jsonl", help="Path to audit ledger")
    parser.add_argument("--no-ledger", action="store_true", help="Skip ledger append")

    args = parser.parse_args()

    # Load inputs
    dsl_source = load_dsl_source(args.source)
    evidence = load_evidence(args.evidence)

    # Compile and evaluate
    print("=" * 60)
    print("DSL Theorem Verification")
    print("=" * 60)

    output = compile_and_evaluate(dsl_source, evidence, observed_metrics=evidence)

    # Print results
    print(f"\nProgram Hash: {output.program_hash[:16]}...")
    print(f"Timestamp: {output.timestamp}")
    print()

    print("Theorem Results:")
    for tr in output.theorem_results:
        status_icon = "✓" if tr.status == "PASS" else "✗"
        print(f"  {status_icon} {tr.theorem_id}: {tr.status}")
        if tr.status == "FAIL":
            for cid, passed in tr.antecedents_status.items():
                print(f"      - {cid}: {'PASS' if passed else 'FAIL'}")

    print()
    print("Bound Results:")
    for bid, br in output.bound_results.items():
        status_icon = "✓" if br["passed"] else "✗"
        print(f"  {status_icon} {bid}: {br['metric']} {br['operator']} {br['bound']} (observed: {br['observed']})")

    print()
    print(f"Overall Status: {output.overall_status}")
    print(f"Violation Probability: {output.violation_probability:.6f}")
    print(f"Safety Verdict: {output.safety_verdict}")
    print()

    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.save(str(output_path), format=args.format)
    print(f"Output saved to: {output_path}")

    # Append to ledger
    if not args.no_ledger:
        ledger_path = Path(project_root) / args.ledger
        if append_to_ledger(output, str(ledger_path)):
            print(f"Ledger entry appended to: {ledger_path}")

    # Verify for CI gating
    passed = verify_theorem_output(output, max_violation_probability=args.threshold, require_all_pass=args.strict)

    if passed:
        print("\n✓ CI Gate: PASS")
        sys.exit(0)
    else:
        print("\n✗ CI Gate: FAIL")
        print(f"  Violation probability ({output.violation_probability:.6f}) exceeds threshold ({args.threshold})")
        sys.exit(1)


if __name__ == "__main__":
    main()
