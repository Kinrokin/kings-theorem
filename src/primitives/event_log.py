"""Append-Only Hash-Chained Event Log - Titanium X Protocol

AID: /src/primitives/event_log.py
Proof ID: PRF-PHOENIX-LEDGER-001
Adversarial Response: Section 2.2 "The Memory Lie"

Cryptographically chained, append-only event log that prevents:
- History rewriting by compromised Teacher
- Post-hoc deletion of embarrassing traces
- Silent truncation on crash
- Overwriting golden runs with test runs

Each log entry contains:
{
    "idx": int,           # Sequential index
    "timestamp": str,     # ISO 8601 timestamp
    "prev_hash": str,     # SHA-256 of previous entry (empty for genesis)
    "event": {...},       # Actual event data
    "hash": str           # SHA-256(idx || timestamp || prev_hash || canonical(event))
}

The head hash is stored in the proof file for external verification.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

logger = logging.getLogger(__name__)


# =============================================================================
# Entry Types
# =============================================================================


@dataclass
class LogEntry:
    """Single entry in the hash-chained log."""

    idx: int
    timestamp: str
    prev_hash: str
    event: Dict[str, Any]
    hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "idx": self.idx,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "event": self.event,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LogEntry":
        return cls(
            idx=d["idx"],
            timestamp=d["timestamp"],
            prev_hash=d["prev_hash"],
            event=d["event"],
            hash=d["hash"],
        )


@dataclass
class VerificationResult:
    """Result of log verification."""

    valid: bool
    entries_checked: int
    error_index: Optional[int] = None
    error_message: str = ""
    head_hash: str = ""


# =============================================================================
# Canonical Serialization
# =============================================================================


def canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization for hashing.

    - Sorted keys
    - No whitespace
    - ASCII-only (no Unicode escapes for reproducibility)
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_entry_hash(idx: int, timestamp: str, prev_hash: str, event: Dict[str, Any]) -> str:
    """Compute SHA-256 hash for a log entry.

    Hash = SHA256(idx || timestamp || prev_hash || canonical(event))
    """
    preimage = f"{idx}|{timestamp}|{prev_hash}|{canonical_json(event)}"
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


# =============================================================================
# Event Log Interface
# =============================================================================


class EventLog:
    """Append-only hash-chained event log.

    Provides:
    - Cryptographic integrity via hash chain
    - Append-only semantics (no delete, no update)
    - Verification of entire chain
    - Iterator access to entries

    Storage backends:
    - Memory (default, for testing)
    - JSONL file (persistent)
    - SQLite (optional, not implemented here)
    """

    def __init__(self, path: Optional[Union[str, Path]] = None, run_id: Optional[str] = None):
        """Initialize event log.

        Args:
            path: Path to JSONL log file (None = in-memory only)
            run_id: Unique identifier for this run (auto-generated if None)
        """
        self._entries: List[LogEntry] = []
        self._path = Path(path) if path else None
        self._run_id = run_id or self._generate_run_id()
        self._head_hash = ""

        # Load existing entries if file exists
        if self._path and self._path.exists():
            self._load_from_file()

    @staticmethod
    def _generate_run_id() -> str:
        """Generate unique run ID: run-<timestamp>-<random>."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        rand = secrets.token_hex(4)
        return f"run-{ts}-{rand}"

    @property
    def run_id(self) -> str:
        """Get run identifier."""
        return self._run_id

    @property
    def head_hash(self) -> str:
        """Get current head hash (hash of last entry)."""
        return self._head_hash

    def __len__(self) -> int:
        """Number of entries in log."""
        return len(self._entries)

    def append(self, event: Dict[str, Any]) -> int:
        """Append event to log.

        Args:
            event: Event data dictionary

        Returns:
            Index of the new entry
        """
        idx = len(self._entries)
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_hash = self._head_hash

        entry_hash = compute_entry_hash(idx, timestamp, prev_hash, event)

        entry = LogEntry(idx=idx, timestamp=timestamp, prev_hash=prev_hash, event=event, hash=entry_hash)

        self._entries.append(entry)
        self._head_hash = entry_hash

        # Persist if file-backed
        if self._path:
            self._append_to_file(entry)

        logger.debug(f"[EVENTLOG] Entry #{idx} hash={entry_hash[:16]}...")

        return idx

    def iterate(self, start: int = 0) -> Iterator[LogEntry]:
        """Iterate over entries from given index.

        Args:
            start: Starting index (0-based)

        Yields:
            LogEntry objects
        """
        for entry in self._entries[start:]:
            yield entry

    def get(self, idx: int) -> Optional[LogEntry]:
        """Get entry by index.

        Args:
            idx: Entry index

        Returns:
            LogEntry or None if index out of range
        """
        if 0 <= idx < len(self._entries):
            return self._entries[idx]
        return None

    def verify(self) -> VerificationResult:
        """Verify integrity of the entire hash chain.

        Returns:
            VerificationResult with validation status
        """
        if not self._entries:
            return VerificationResult(valid=True, entries_checked=0, head_hash="")

        expected_prev = ""

        for entry in self._entries:
            # Verify previous hash linkage
            if entry.prev_hash != expected_prev:
                return VerificationResult(
                    valid=False,
                    entries_checked=entry.idx,
                    error_index=entry.idx,
                    error_message=f"Chain break: expected prev_hash={expected_prev[:16]}..., got {entry.prev_hash[:16]}...",
                )

            # Recompute hash
            computed = compute_entry_hash(entry.idx, entry.timestamp, entry.prev_hash, entry.event)

            if computed != entry.hash:
                return VerificationResult(
                    valid=False,
                    entries_checked=entry.idx,
                    error_index=entry.idx,
                    error_message=f"Hash mismatch at idx={entry.idx}: computed={computed[:16]}..., stored={entry.hash[:16]}...",
                )

            expected_prev = entry.hash

        return VerificationResult(valid=True, entries_checked=len(self._entries), head_hash=self._head_hash)

    def export_proof(self, output_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Export proof metadata for verification.

        Args:
            output_path: Optional path to write proof JSON

        Returns:
            Proof metadata dict
        """
        proof = {
            "run_id": self._run_id,
            "entry_count": len(self._entries),
            "head_hash": self._head_hash,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "log_path": str(self._path) if self._path else None,
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(proof, f, indent=2)
            logger.info(f"[EVENTLOG] Exported proof to {output_path}")

        return proof

    def _append_to_file(self, entry: LogEntry) -> None:
        """Append single entry to JSONL file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a") as f:
            f.write(canonical_json(entry.to_dict()) + "\n")

    def _load_from_file(self) -> None:
        """Load entries from existing JSONL file."""
        with open(self._path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    entry = LogEntry.from_dict(data)
                    self._entries.append(entry)

        if self._entries:
            self._head_hash = self._entries[-1].hash
            self._run_id = self._entries[0].event.get("run_id", self._run_id)

        logger.info(f"[EVENTLOG] Loaded {len(self._entries)} entries from {self._path}")


# =============================================================================
# Proof File Management
# =============================================================================


def create_proof_file(
    log: EventLog, metrics: Optional[Dict[str, Any]] = None, output_dir: Union[str, Path] = "proofs"
) -> Path:
    """Create a proof file for a completed run.

    Args:
        log: Event log to seal
        metrics: Optional computed metrics to include
        output_dir: Directory for proof files

    Returns:
        Path to created proof file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    proof_path = output_dir / f"{log.run_id}.json"

    verification = log.verify()
    if not verification.valid:
        raise ValueError(f"Cannot create proof for invalid log: {verification.error_message}")

    proof = {
        "version": "1.0",
        "run_id": log.run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(log),
        "head_hash": log.head_hash,
        "log_path": str(log._path) if log._path else None,
        "verification": {
            "valid": verification.valid,
            "entries_checked": verification.entries_checked,
        },
        "metrics": metrics or {},
    }

    with open(proof_path, "w") as f:
        json.dump(proof, f, indent=2)

    logger.info(f"[EVENTLOG] Created proof file: {proof_path}")
    return proof_path


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "LogEntry",
    "VerificationResult",
    "EventLog",
    "canonical_json",
    "compute_entry_hash",
    "create_proof_file",
]
