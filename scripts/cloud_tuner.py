#!/usr/bin/env python3
"""
Cloud Tuner - Colab/Cloud Job Management

Prepares job descriptors for cloud-based teacher generation and QLoRA training.
Does NOT automatically run Colab - humans will open notebooks manually.

Modes:
- prepare-job: Create job descriptor JSON from purified harvest
- merge-teacher: Log arrival of teacher (silver medal) data
- sync-from-drive: (stub) Future automation hook
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

REPO_ROOT = Path(__file__).parent.parent
DATA_DIR = REPO_ROOT / "data"
TEACHER_DIR = DATA_DIR / "teacher"
TEACHER_DIR.mkdir(parents=True, exist_ok=True)

JOBS_DIR = TEACHER_DIR / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# PREPARE JOB
# ═══════════════════════════════════════════════════════════════════════════


def prepare_job(purified_path: Path, verbose: bool = True) -> str:
    """
    Create a job descriptor for teacher generation in Colab.
    
    Args:
        purified_path: Path to purified_harvest.jsonl
        verbose: Enable logging
        
    Returns:
        Job ID string
    """
    if not purified_path.exists():
        raise FileNotFoundError(f"Purified harvest not found: {purified_path}")
    
    # Generate job ID
    job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # Count samples in purified file
    sample_count = 0
    with purified_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                sample_count += 1
    
    # Create job descriptor
    job = {
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat(),
        "input_path": str(purified_path.absolute()),
        "sample_count": sample_count,
        "suggested_teacher_model": "gpt-4o-mini",  # or gemini-1.5-flash
        "suggested_qwen_target": "qwen3-8b-instruct",
        "status": "pending",
        "notes": "Open Colab teacher notebook and point it to this job descriptor",
    }
    
    # Write job descriptor
    job_file = JOBS_DIR / f"{job_id}.json"
    with job_file.open("w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"☁️  JOB DESCRIPTOR CREATED")
        print(f"{'='*70}")
        print(f"Job ID: {job_id}")
        print(f"Samples: {sample_count}")
        print(f"Descriptor: {job_file}")
        print(f"\n📝 Next steps:")
        print(f"   1. Open your Colab teacher notebook")
        print(f"   2. Point it to: {job_file}")
        print(f"   3. Run teacher generation")
        print(f"   4. Save output to data/teacher/silver_medal_{job_id}.jsonl")
        print(f"{'='*70}\n")
    
    return job_id


# ═══════════════════════════════════════════════════════════════════════════
# MERGE TEACHER
# ═══════════════════════════════════════════════════════════════════════════


def merge_teacher(teacher_path: Path, verbose: bool = True) -> None:
    """
    Log arrival of teacher (silver medal) data.
    
    Args:
        teacher_path: Path to silver_medal.jsonl
        verbose: Enable logging
    """
    if not teacher_path.exists():
        raise FileNotFoundError(f"Teacher data not found: {teacher_path}")
    
    # Count samples
    sample_count = 0
    with teacher_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                sample_count += 1
    
    # Log merge
    merge_log = TEACHER_DIR / "merge_log.jsonl"
    entry = {
        "event": "teacher_merge",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "teacher_path": str(teacher_path.absolute()),
        "sample_count": sample_count,
    }
    
    with merge_log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"✨ TEACHER DATA LOGGED")
        print(f"{'='*70}")
        print(f"Teacher file: {teacher_path}")
        print(f"Samples: {sample_count}")
        print(f"Log updated: {merge_log}")
        print(f"\n📝 Next steps:")
        print(f"   1. Open your Colab QLoRA notebook")
        print(f"   2. Point it to: {teacher_path}")
        print(f"   3. Run fine-tuning")
        print(f"   4. Download trained model/adapter")
        print(f"{'='*70}\n")


# ═══════════════════════════════════════════════════════════════════════════
# SYNC FROM DRIVE (STUB)
# ═══════════════════════════════════════════════════════════════════════════


def sync_from_drive(verbose: bool = True) -> None:
    """
    Stub for future automation: sync teacher data from Google Drive.
    
    Args:
        verbose: Enable logging
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"☁️  SYNC FROM DRIVE")
        print(f"{'='*70}")
        print(f"⚠️  This feature is not yet implemented.")
        print(f"   For now, manually download silver_medal.jsonl from Drive")
        print(f"   and place it in: {TEACHER_DIR}")
        print(f"{'='*70}\n")


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Cloud tuner CLI."""
    parser = argparse.ArgumentParser(
        description="Cloud Tuner - Manage Colab teacher/training jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prepare a job descriptor for Colab teacher
  python scripts/cloud_tuner.py prepare-job --purified data/purified/purified_harvest.jsonl

  # Log teacher data arrival
  python scripts/cloud_tuner.py merge-teacher --teacher data/teacher/silver_medal_job123.jsonl

  # Sync from Drive (stub)
  python scripts/cloud_tuner.py sync-from-drive

Modes:
  prepare-job: Create job descriptor JSON for Colab
  merge-teacher: Log arrival of teacher (silver medal) data
  sync-from-drive: (stub) Future automation
        """
    )
    
    subparsers = parser.add_subparsers(dest="mode", required=True)
    
    # prepare-job mode
    prepare_parser = subparsers.add_parser("prepare-job", help="Create job descriptor")
    prepare_parser.add_argument(
        "--purified",
        type=str,
        required=True,
        help="Path to purified_harvest.jsonl",
    )
    
    # merge-teacher mode
    merge_parser = subparsers.add_parser("merge-teacher", help="Log teacher data")
    merge_parser.add_argument(
        "--teacher",
        type=str,
        required=True,
        help="Path to silver_medal.jsonl",
    )
    
    # sync-from-drive mode
    subparsers.add_parser("sync-from-drive", help="Sync from Google Drive (stub)")
    
    args = parser.parse_args()
    
    try:
        if args.mode == "prepare-job":
            prepare_job(Path(args.purified), verbose=True)
        
        elif args.mode == "merge-teacher":
            merge_teacher(Path(args.teacher), verbose=True)
        
        elif args.mode == "sync-from-drive":
            sync_from_drive(verbose=True)
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
