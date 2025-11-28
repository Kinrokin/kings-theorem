"""KT Data Refinery: Trace to Training Data Pipeline

Converts raw execution traces from the KT runtime into structured training data
for Supervised Fine-Tuning (SFT) and Direct Preference Optimization (DPO).

The refinery extracts:
- Student proposals (creative hypotheses)
- Teacher critiques (rigorous analysis)
- Arbiter judgments (governance decisions)
- Harmonizer verdicts (constitutional compliance)

Output formats:
- sft_d7_ready.jsonl: Chat-format training pairs
- dpo_pairs.jsonl: Preference pairs (chosen vs rejected)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_cot(trace: List[Dict[str, Any]]) -> str:
    """Reconstruct internal reasoning chain from trace events.

    Args:
        trace: List of trace event dictionaries

    Returns:
        Formatted chain-of-thought string with XML-style tags
    """
    cot_parts = []

    for event in trace:
        etype = event.get("type", "")
        phase = event.get("phase", "")
        status = event.get("status", "")
        meta = event.get("meta", {})

        # 1. Student Phase: Capture creative proposals
        if phase == "STUDENT" or etype == "STUDENT_PROPOSAL":
            solution = meta.get("solution", "") or event.get("student_raw", "")
            if solution:
                cot_parts.append(f"<student_proposal>\n{solution}\n</student_proposal>")

        # 2. Teacher Phase: Capture rigorous critique
        elif phase == "TEACHER" or etype == "TEACHER_CRITIQUE":
            evaluation = meta.get("evaluation", "") or event.get("teacher_raw", "")
            if evaluation:
                cot_parts.append(f"<teacher_critique>\n{evaluation}\n</teacher_critique>")

        # 3. Guardrail Phase: Capture safety checks
        elif phase == "GUARDRAIL" or etype == "GUARDRAIL_CHECK":
            reason = meta.get("reason", "") or event.get("reason", "")
            if status == "VETO" or event.get("vetoed"):
                cot_parts.append(f"<safety_veto>\nReason: {reason}\n</safety_veto>")
            else:
                cot_parts.append("<safety_check>\nStatus: PASS\n</safety_check>")

        # 4. Runtime Review: Capture governance and harmonizer
        elif etype == "RUNTIME_REVIEW":
            # Arbiter decisions
            arbiter_view = event.get("arbiter_view", {})
            if arbiter_view.get("vetoed"):
                reasons = arbiter_view.get("reasons", ["Constitutional veto"])
                cot_parts.append(f"<arbiter_veto>\n{', '.join(reasons)}\n</arbiter_veto>")

            # Guard results
            guard_result = event.get("guard_result", {})
            if guard_result.get("is_blocked"):
                cot_parts.append(
                    f"<guard_block>\nReason: {guard_result.get('reason', 'Safety violation')}\n</guard_block>"
                )

            # Harmonizer verdict
            harmonized = event.get("harmonized", {})
            decision = harmonized.get("decision", "UNKNOWN")
            score = harmonized.get("total_score", 0.0)
            cot_parts.append(
                f"<constitution_check>\nDecision: {decision}\nConstitutional Score: {score}\n</constitution_check>"
            )

        # 5. TriGovernor Phase: Capture governance decision (legacy)
        elif phase == "TRIGOVERNOR":
            risk_score = meta.get("risk_score", 0.0)
            cot_parts.append(
                f"<governance_review>\nDecision: {status}\nRisk Score: {risk_score:.3f}\n</governance_review>"
            )

    return "\n\n".join(cot_parts) if cot_parts else "<no_reasoning_trace>"


def extract_preference_pair(trace: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract DPO preference pair from trace with student/teacher divergence.

    Args:
        trace: List of trace event dictionaries

    Returns:
        Dict with 'chosen' and 'rejected' keys, or None if no divergence
    """
    student_proposal = None
    teacher_critique = None
    governance_vetoed = False

    for event in trace:
        etype = event.get("type", "")
        phase = event.get("phase", "")

        # Extract student proposal
        if phase == "STUDENT" or etype == "STUDENT_PROPOSAL":
            student_proposal = event.get("meta", {}).get("solution", "") or event.get("student_raw", "")

        # Extract teacher critique
        elif phase == "TEACHER" or etype == "TEACHER_CRITIQUE":
            teacher_critique = event.get("meta", {}).get("evaluation", "") or event.get("teacher_raw", "")

        # Check for governance veto
        elif phase == "TRIGOVERNOR":
            if event.get("status") in ["VETO", "TIER_5_HALT"]:
                governance_vetoed = True

        # Check runtime review veto
        elif etype == "RUNTIME_REVIEW":
            arbiter = event.get("arbiter_view", {})
            harmonized = event.get("harmonized", {})
            if arbiter.get("vetoed") or harmonized.get("decision") == "VETO":
                governance_vetoed = True

    # DPO requires divergence: student proposed something, but governance vetoed
    if student_proposal and governance_vetoed:
        return {
            "prompt": "Evaluate the following proposal for safety and constitutional compliance.",
            "chosen": teacher_critique or "Proposal rejected due to governance constraints.",
            "rejected": student_proposal,
        }

    return None


def process_sft_refinery(input_file: Path, output_dir: Path) -> int:
    """Process raw traces into SFT training data.

    Args:
        input_file: Path to golden_traces.jsonl or similar
        output_dir: Directory to write sft_d7_ready.jsonl

    Returns:
        Number of training examples created
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sft_path = output_dir / "sft_d7_ready.jsonl"

    count = 0
    with open(input_file, "r", encoding="utf-8") as fin, open(sft_path, "w", encoding="utf-8") as f_sft:
        for line_num, line in enumerate(fin, 1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

            # Quality filter: Only train on successful executions
            quality = entry.get("quality_check", "UNKNOWN")
            if quality not in ["PASS", "SALVAGEABLE"]:
                logger.debug(f"Skipping entry {line_num} with quality: {quality}")
                continue

            prompt = entry.get("input", "")
            final_output = entry.get("final_output", "")
            full_trace = entry.get("full_trace", [])

            if not prompt or not final_output:
                logger.warning(f"Skipping entry {line_num}: missing prompt or output")
                continue

            # Extract reasoning chain
            cot_chain = extract_cot(full_trace)

            # SFT Format: Multi-turn chat with reasoning trace
            sft_entry = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": f"{cot_chain}\n\nFINAL ANSWER:\n{final_output}"},
                ],
                "metadata": {
                    "source": "kt_refinery",
                    "difficulty": entry.get("difficulty", "unknown"),
                    "quality": quality,
                },
            }

            f_sft.write(json.dumps(sft_entry, ensure_ascii=False) + "\n")
            count += 1

            if count % 100 == 0:
                logger.info(f"Processed {count} SFT examples...")

    logger.info(f"✅ SFT Refinery Complete: {count} examples -> {sft_path}")
    return count


def process_dpo_refinery(input_file: Path, output_dir: Path) -> int:
    """Process raw traces into DPO preference pairs.

    Args:
        input_file: Path to golden_traces.jsonl
        output_dir: Directory to write dpo_pairs.jsonl

    Returns:
        Number of preference pairs created
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    dpo_path = output_dir / "dpo_pairs.jsonl"

    count = 0
    with open(input_file, "r", encoding="utf-8") as fin, open(dpo_path, "w", encoding="utf-8") as f_dpo:
        for line_num, line in enumerate(fin, 1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

            full_trace = entry.get("full_trace", [])
            pair = extract_preference_pair(full_trace)

            if pair:
                dpo_entry = {
                    **pair,
                    "metadata": {"source": "kt_refinery", "difficulty": entry.get("difficulty", "unknown")},
                }
                f_dpo.write(json.dumps(dpo_entry, ensure_ascii=False) + "\n")
                count += 1

                if count % 50 == 0:
                    logger.info(f"Processed {count} DPO pairs...")

    logger.info(f"✅ DPO Refinery Complete: {count} pairs -> {dpo_path}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="KT Data Refinery: Convert execution traces to training data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create SFT dataset from golden traces
  python scripts/refine_data.py --input logs/golden_traces.jsonl --output-dir data/training --format sft

  # Create DPO preference pairs
  python scripts/refine_data.py --input logs/golden_traces.jsonl --output-dir data/training --format dpo

  # Create both formats
  python scripts/refine_data.py --input logs/golden_traces.jsonl --output-dir data/training --format both
        """,
    )
    parser.add_argument("--input", required=True, help="Path to golden_traces.jsonl")
    parser.add_argument("--output-dir", required=True, help="Directory for training files")
    parser.add_argument("--format", choices=["sft", "dpo", "both"], default="sft", help="Output format (default: sft)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1

    output_dir = Path(args.output_dir)

    if args.format in ["sft", "both"]:
        sft_count = process_sft_refinery(input_path, output_dir)
        logger.info(f"✅ SFT: {sft_count} training examples")

    if args.format in ["dpo", "both"]:
        dpo_count = process_dpo_refinery(input_path, output_dir)
        logger.info(f"✅ DPO: {dpo_count} preference pairs")

    logger.info("\n🏭 Refinery complete. Training data ready for curriculum.")
    return 0


if __name__ == "__main__":
    exit(main())
