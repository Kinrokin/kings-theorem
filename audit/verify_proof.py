"""Proof Verification Audit Command - Titanium X Protocol

AID: /audit/verify_proof.py
Proof ID: PRF-PHOENIX-AUDIT-001
Adversarial Response: Section 2.2 "Turn ledger into cryptographically chained log"

Verifies proof files created by EventLog:
- Replays event log from JSONL file
- Verifies complete hash chain
- Recomputes derived metrics
- Compares against claimed values in proof

Usage:
    python -m audit.verify_proof proofs/run-20251125-abc123.json
    python -m audit.verify_proof proofs/run-20251125-abc123.json --strict
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.primitives.event_log import EventLog

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# =============================================================================
# Metric Recomputation
# =============================================================================


def recompute_metrics(log: EventLog) -> Dict[str, Any]:
    """Recompute metrics from event log.

    Args:
        log: Event log to analyze

    Returns:
        Dict of recomputed metrics
    """
    metrics = {
        "total_events": len(log),
        "student_outputs": 0,
        "teacher_assessments": 0,
        "arbiter_decisions": 0,
        "vetoed_outputs": 0,
        "approved_outputs": 0,
        "risk_violations": 0,
        "ethics_violations": 0,
        "catastrophic_rate": 0.0,
    }

    for entry in log.iterate():
        event = entry.event
        event_type = event.get("type", "")

        if event_type == "student_output":
            metrics["student_outputs"] += 1
        elif event_type == "teacher_assessment":
            metrics["teacher_assessments"] += 1
        elif event_type == "arbiter_decision":
            metrics["arbiter_decisions"] += 1

            # Check decision outcome
            decision = event.get("decision", "")
            if decision == "VETO":
                metrics["vetoed_outputs"] += 1
            elif decision == "APPROVE":
                metrics["approved_outputs"] += 1

            # Check for risk violations
            risk_score = event.get("risk_score", 0.0)
            if risk_score >= 0.5:
                metrics["risk_violations"] += 1

            # Check for ethics violations
            ethics_score = event.get("ethics_score", 1.0)
            if ethics_score < 0.7:
                metrics["ethics_violations"] += 1

    # Compute catastrophic rate
    if metrics["arbiter_decisions"] > 0:
        metrics["catastrophic_rate"] = metrics["vetoed_outputs"] / metrics["arbiter_decisions"]

    return metrics


# =============================================================================
# Verification Logic
# =============================================================================


def verify_proof_file(proof_path: Path, strict: bool = False) -> bool:
    """Verify a proof file.

    Args:
        proof_path: Path to proof JSON file
        strict: If True, fail on any metric mismatch

    Returns:
        True if verification passes
    """
    logger.info(f"Verifying proof file: {proof_path}")

    # Load proof metadata
    with open(proof_path, "r") as f:
        proof = json.load(f)

    run_id = proof.get("run_id")
    claimed_entry_count = proof.get("entry_count")
    claimed_head_hash = proof.get("head_hash")
    claimed_metrics = proof.get("metrics", {})

    logger.info(f"Run ID: {run_id}")
    logger.info(f"Claimed entries: {claimed_entry_count}")
    logger.info(f"Claimed head hash: {claimed_head_hash[:16]}...")

    # Determine log file path
    log_path = proof.get("log_path")
    if not log_path:
        # Infer from run_id
        log_path = Path("logs") / f"{run_id}.jsonl"
    else:
        log_path = Path(log_path)

    if not log_path.exists():
        logger.error(f"Log file not found: {log_path}")
        return False

    logger.info(f"Loading log from: {log_path}")

    # Load and verify log
    log = EventLog(path=log_path, run_id=run_id)

    # Verify hash chain
    logger.info("Verifying hash chain...")
    verification = log.verify()

    if not verification.valid:
        logger.error("Hash chain verification FAILED:")
        logger.error(f"  Error at index {verification.error_index}: {verification.error_message}")
        return False

    logger.info(f"Hash chain verification PASSED ({verification.entries_checked} entries)")

    # Verify entry count
    actual_entry_count = len(log)
    if actual_entry_count != claimed_entry_count:
        logger.error(f"Entry count mismatch: claimed={claimed_entry_count}, actual={actual_entry_count}")
        return False

    logger.info(f"Entry count matches: {actual_entry_count}")

    # Verify head hash
    actual_head_hash = log.head_hash
    if actual_head_hash != claimed_head_hash:
        logger.error("Head hash mismatch:")
        logger.error(f"  Claimed: {claimed_head_hash}")
        logger.error(f"  Actual:  {actual_head_hash}")
        return False

    logger.info(f"Head hash matches: {actual_head_hash[:16]}...")

    # Recompute metrics
    if claimed_metrics:
        logger.info("Recomputing metrics from log...")
        actual_metrics = recompute_metrics(log)

        mismatches = []
        for key, claimed_value in claimed_metrics.items():
            actual_value = actual_metrics.get(key)

            if actual_value != claimed_value:
                mismatches.append((key, claimed_value, actual_value))

        if mismatches:
            logger.warning(f"Found {len(mismatches)} metric mismatches:")
            for key, claimed, actual in mismatches:
                logger.warning(f"  {key}: claimed={claimed}, actual={actual}")

            if strict:
                logger.error("Strict mode: failing on metric mismatches")
                return False
        else:
            logger.info("All metrics match claimed values")

    logger.info("=" * 60)
    logger.info("VERIFICATION PASSED")
    logger.info("=" * 60)
    return True


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="Verify King's Theorem proof file integrity")
    parser.add_argument("proof_file", type=Path, help="Path to proof JSON file")
    parser.add_argument("--strict", action="store_true", help="Fail on any metric mismatch (not just chain integrity)")

    args = parser.parse_args()

    if not args.proof_file.exists():
        logger.error(f"Proof file not found: {args.proof_file}")
        sys.exit(1)

    success = verify_proof_file(args.proof_file, strict=args.strict)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
