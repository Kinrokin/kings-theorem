#!/usr/bin/env python3
"""
The Tribunal - Real Metrics Pipeline
Verification system that computes actual metrics for synthetic data quality.

Takes a generated JSONL harvest file and produces:
- data/purified_harvest.jsonl (clean samples only)
- data/audit_log.json (aggregate metrics)

Metrics computed per sample:
- compression_ratio: len(compressed) / len(verbose)
- new_token_count: tokens in compressed not in verbose (lexical drift proxy)
- drift_score: normalized drift in [0, 1]
- contamination_level: 0 (clean), 1 (suspect), 2 (bad)
- struct_flags: boolean structural validation checks
- is_valid: included in purified file if True
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Use consistent paths with new data layout
REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
PURIFIED_DIR = DATA_DIR / "purified"
PURIFIED_DIR.mkdir(parents=True, exist_ok=True)

PURIFIED_PATH = PURIFIED_DIR / "purified_harvest.jsonl"
AUDIT_LOG_PATH = DATA_DIR / "audit_log.json"

MIN_VERBOSE_LENGTH = 256  # Minimum verbose response length
DRIFT_CAP = 64           # Soft cap for normalizing drift score
MIN_SCORE_THRESHOLD = 0.90  # Minimum final_score for validity


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class StructFlags:
    """Structural validation flags for a sample."""
    has_id: bool
    has_instruction: bool
    has_verbose: bool
    has_compressed: bool
    verbose_long_enough: bool
    compressed_nonempty: bool


@dataclass
class SampleMetrics:
    """Complete metrics for a single sample."""
    id: str
    final_score: float
    compression_ratio: float
    new_token_count: int
    drift_score: float
    contamination_level: int
    struct_flags: StructFlags
    is_valid: bool


# ═══════════════════════════════════════════════════════════════════════════
# TOKENIZATION & METRIC COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════


def tokenize(text: str) -> List[str]:
    """
    Simple whitespace + punctuation tokenization.
    
    Lowercases text and extracts word tokens and punctuation separately.
    Can be replaced with a proper tokenizer (tiktoken, etc.) for production.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of token strings
    """
    text = text.lower()
    return re.findall(r"\w+|\S", text)


def compute_metrics(entry: Dict[str, Any]) -> SampleMetrics:
    """
    Compute comprehensive quality metrics for a sample.
    
    Args:
        entry: JSONL entry containing sample data
        
    Returns:
        SampleMetrics with all computed values
    """
    # Extract fields with safe defaults
    sample_id = str(entry.get("id", ""))
    instruction = str(entry.get("instruction", "") or "")
    verbose = str(entry.get("response_verbose", "") or "")
    compressed = str(entry.get("response_compressed", "") or "")
    final_score = float(entry.get("final_score", 0.0))

    # Structural validation flags
    flags = StructFlags(
        has_id=bool(sample_id),
        has_instruction=bool(instruction.strip()),
        has_verbose=bool(verbose.strip()),
        has_compressed=bool(compressed.strip()),
        verbose_long_enough=len(verbose) >= MIN_VERBOSE_LENGTH,
        compressed_nonempty=len(compressed) > 0,
    )

    # Compression ratio: compressed length / verbose length
    v_len = max(len(verbose), 1)
    compression_ratio = len(compressed) / v_len

    # Ontological drift via lexical difference
    # Count tokens in compressed that don't appear in verbose
    verbose_tokens = set(tokenize(verbose))
    compressed_tokens = tokenize(compressed)
    new_tokens = [t for t in compressed_tokens if t not in verbose_tokens]
    new_token_count = len(new_tokens)

    # Normalize drift_score to [0, 1] using soft cap
    drift_score = min(1.0, new_token_count / DRIFT_CAP)

    # Contamination level determination:
    # Level 0 = clean, Level 1 = suspicious, Level 2 = bad
    contamination_level = 0

    # Missing critical fields → Level 2 (bad)
    if not (flags.has_id and flags.has_instruction and flags.has_verbose and flags.has_compressed):
        contamination_level = 2
    # Poor compression or short verbose → Level 1 (suspicious)
    elif not flags.verbose_long_enough or compression_ratio > 0.75:
        contamination_level = max(contamination_level, 1)

    # High drift → Level 2 or 1
    if drift_score > 0.75:
        contamination_level = 2
    elif drift_score > 0.5:
        contamination_level = max(contamination_level, 1)

    # Validity check: must pass all critical criteria
    is_valid = (
        final_score >= MIN_SCORE_THRESHOLD
        and contamination_level < 2
        and flags.has_id
        and flags.has_instruction
        and flags.has_verbose
        and flags.has_compressed
    )

    return SampleMetrics(
        id=sample_id,
        final_score=final_score,
        compression_ratio=compression_ratio,
        new_token_count=new_token_count,
        drift_score=drift_score,
        contamination_level=contamination_level,
        struct_flags=flags,
        is_valid=is_valid,
    )


# ═══════════════════════════════════════════════════════════════════════════
# VERIFICATION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════


def verify_harvest(input_path: Path, verbose_output: bool = True) -> None:
    """
    Main verification pipeline.
    
    Reads raw harvest JSONL, computes metrics for each sample,
    writes purified samples to purified_harvest.jsonl and
    aggregate statistics to audit_log.json.
    
    Args:
        input_path: Path to raw harvest JSONL file
        verbose_output: If True, print progress messages
        
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input harvest not found: {input_path}")

    if verbose_output:
        print(f"📥 Reading harvest from {input_path}")

    total = 0
    kept = 0
    metrics_list: List[SampleMetrics] = []

    # Process harvest file line by line
    with input_path.open("r", encoding="utf-8") as fin, \
            PURIFIED_PATH.open("w", encoding="utf-8") as fout:
        
        for line in fin:
            line = line.strip()
            if not line:
                continue
            
            total += 1
            
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                if verbose_output:
                    print(f"⚠️  Skipping malformed JSON on line {total}")
                continue

            # Compute metrics for this sample
            metrics = compute_metrics(entry)
            metrics_list.append(metrics)

            # Attach computed metrics to entry
            entry["compression_ratio"] = metrics.compression_ratio
            entry["new_token_count"] = metrics.new_token_count
            entry["drift_score"] = metrics.drift_score
            entry["contamination_level"] = metrics.contamination_level
            entry["struct_flags"] = asdict(metrics.struct_flags)

            # Write to purified file if valid
            if metrics.is_valid:
                kept += 1
                fout.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Compute aggregate statistics
    if metrics_list:
        avg_score = sum(m.final_score for m in metrics_list) / len(metrics_list)
        avg_compression = sum(m.compression_ratio for m in metrics_list) / len(metrics_list)
        avg_drift = sum(m.drift_score for m in metrics_list) / len(metrics_list)
        
        contamination_counts = {0: 0, 1: 0, 2: 0}
        for m in metrics_list:
            contamination_counts[m.contamination_level] += 1
    else:
        avg_score = avg_compression = avg_drift = 0.0
        contamination_counts = {0: 0, 1: 0, 2: 0}

    # Build audit log
    audit = {
        "input_file": str(input_path),
        "purified_file": str(PURIFIED_PATH),
        "total_samples": total,
        "kept_samples": kept,
        "dropped_samples": total - kept,
        "retention_rate": kept / total if total > 0 else 0.0,
        "avg_final_score": avg_score,
        "avg_compression_ratio": avg_compression,
        "avg_drift_score": avg_drift,
        "contamination_counts": contamination_counts,
    }

    # Write audit log
    with AUDIT_LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    if verbose_output:
        print(f"✅ Verification complete.")
        print(f"   Total: {total}, Kept: {kept}, Dropped: {total - kept}")
        print(f"   Retention Rate: {audit['retention_rate']:.1%}")
        print(f"   Avg Score: {avg_score:.3f}")
        print(f"   Avg Compression: {avg_compression:.3f}")
        print(f"   Avg Drift: {avg_drift:.3f}")
        print(f"   Contamination: Clean={contamination_counts[0]}, "
              f"Suspect={contamination_counts[1]}, Bad={contamination_counts[2]}")
        print(f"   Purified → {PURIFIED_PATH}")
        print(f"   Audit log → {AUDIT_LOG_PATH}")


# ═══════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Command-line interface for harvest verification."""
    parser = argparse.ArgumentParser(
        description="Verify and purify a harvest JSONL file with real metrics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Verify a curved curriculum harvest
  python scripts/verify_harvest.py --input data/harvests/curriculum_20251128.jsonl
  
  # Verify an Ouroboros iteration
  python scripts/verify_harvest.py --input data/harvests/ouroboros_iter_003.jsonl
  
  # Quiet mode (minimal output)
  python scripts/verify_harvest.py --input data/my_harvest.jsonl --quiet

Output:
  - data/purified_harvest.jsonl (clean samples with metrics attached)
  - data/audit_log.json (aggregate statistics)
        """
    )
    
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the raw harvest JSONL file to verify",
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )
    
    args = parser.parse_args()
    
    try:
        verify_harvest(Path(args.input), verbose_output=not args.quiet)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
