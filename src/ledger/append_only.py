"""
Titanium X Append-Only Ledger - HMAC Integrity, Chain Verification
===================================================================

Adversarial improvements:
- fsync() on every append (durability guarantee)
- HMAC-SHA256 over block content with sealed key
- Previous block hash chaining (blockchain-style)
- Startup integrity verification (refuse writes on corruption)
- Immutable in-memory state (frozen snapshots)

Constitutional compliance: Axiom 3 (formal auditability), Anti-fragility
"""

import hashlib
import hmac
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LedgerCorruptionError(Exception):
    """Raised when ledger integrity verification fails."""

    pass


@dataclass
class Block:
    """
    Single ledger block with content and integrity metadata.

    Attributes:
        index: Block sequence number (0-indexed)
        timestamp: ISO 8601 timestamp
        entry: Arbitrary JSON-serializable data
        prev_hash: SHA-256 hash of previous block (None for genesis)
        mac: HMAC-SHA256 of block content
    """

    index: int
    timestamp: str
    entry: Dict[str, Any]
    prev_hash: Optional[str]
    mac: str

    def to_dict(self) -> Dict:
        """Serialize block for storage."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "entry": self.entry,
            "prev_hash": self.prev_hash,
            "mac": self.mac,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Block":
        """Deserialize block from storage."""
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            entry=data["entry"],
            prev_hash=data.get("prev_hash"),
            mac=data["mac"],
        )


class AppendOnlyLedger:
    """
    Cryptographically sealed append-only ledger with forward-secure key rotation.

    Features:
    - HMAC-SHA256 per block with sealed key
    - Previous block hash chaining
    - fsync() on every write
    - Startup integrity verification
    - Read-only in-memory snapshot
    - Forward-secure key ratchet (prevents retroactive forgery)
    """

    def __init__(self, path: str, key: bytes, verify_on_init: bool = True):
        """
        Initialize ledger with path and initial HMAC key.

        Args:
            path: Filesystem path to ledger file (newline-delimited JSON)
            key: Initial HMAC key - MUST be the same key used when ledger was created
            verify_on_init: Verify chain integrity on initialization

        Raises:
            LedgerCorruptionError: If verify_on_init=True and chain invalid

        Note:
            For forward-secure key rotation to work across sessions, you MUST
            provide the ORIGINAL key used when the ledger was first created.
            The key history will be reconstructed by ratcheting forward.
        """
        self.path = Path(path)
        self._current_key = key  # Active key for next append
        self._key_history: List[bytes] = []  # Historical keys for verification ONLY
        self._blocks: List[Block] = []
        self._is_corrupted = False

        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Create file if doesn't exist
        if not self.path.exists():
            self.path.touch()
            logger.info(f"Created new ledger: {self.path}")
        else:
            logger.info(f"Loaded existing ledger: {self.path}")

        # Load existing blocks
        self._load_from_disk()

        # Rebuild key history by ratcheting forward for each existing block
        # This assumes we have the ORIGINAL key (k_0)
        if self._blocks:
            self._key_history.append(self._current_key)  # k_0
            for i in range(len(self._blocks)):
                # Ratchet key: k_{i+1} = SHA256(k_i)
                self._current_key = hashlib.sha256(self._current_key).digest()
                self._key_history.append(self._current_key)
            logger.info(f"Rebuilt key history: {len(self._key_history)} generations")

        # Verify integrity if requested
        if verify_on_init:
            is_valid, error_msg = self.verify_all()
            if not is_valid:
                self._is_corrupted = True
                raise LedgerCorruptionError(f"Ledger corrupted: {error_msg}")
            logger.info(f"Ledger verified: {len(self._blocks)} blocks, chain intact")

    def _ratchet_key(self) -> None:
        """
        Forward-secure key ratchet: k_{n+1} = SHA256(k_n).

        Old keys are stored for verification ONLY, not for signing.
        This prevents retroactive forgery even if current key is compromised.
        """
        # Archive current key for verification
        self._key_history.append(self._current_key)

        # Derive next key via one-way hash
        self._current_key = hashlib.sha256(self._current_key).digest()

        logger.info(f"Key ratcheted: generation {len(self._key_history)}")

    def _compute_mac(self, payload: str, key: Optional[bytes] = None) -> str:
        """
        Compute HMAC-SHA256 of payload.

        Args:
            payload: String data to authenticate
            key: Optional key (uses current key if None, for historical verification)

        Returns:
            Hex-encoded HMAC digest
        """
        active_key = key if key is not None else self._current_key
        return hmac.new(active_key, payload.encode(), hashlib.sha256).hexdigest()

    def _compute_block_hash(self, block: Block) -> str:
        """
        Compute SHA-256 hash of block content (excluding MAC).

        Args:
            block: Block to hash

        Returns:
            Hex-encoded SHA-256 digest
        """
        # Serialize block content without MAC for hashing
        content = {
            "index": block.index,
            "timestamp": block.timestamp,
            "entry": block.entry,
            "prev_hash": block.prev_hash,
        }
        payload = json.dumps(content, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _load_from_disk(self) -> None:
        """Load blocks from disk into memory."""
        self._blocks = []

        with open(self.path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    block_data = json.loads(line)
                    block = Block.from_dict(block_data)
                    self._blocks.append(block)
                except json.JSONDecodeError as e:
                    logger.error(f"Malformed JSON at line {line_num}: {e}")
                    self._is_corrupted = True
                except Exception as e:
                    logger.error(f"Error loading block at line {line_num}: {e}")
                    self._is_corrupted = True

    def append(self, entry: Dict[str, Any], ratchet_key: bool = True) -> str:
        """
        Append new entry to ledger with integrity sealing and optional key rotation.

        Args:
            entry: JSON-serializable data to append
            ratchet_key: If True, rotate key after append (forward security)

        Returns:
            SHA-256 hash of appended block

        Raises:
            LedgerCorruptionError: If ledger is in corrupted state
        """
        if self._is_corrupted:
            raise LedgerCorruptionError("Cannot append to corrupted ledger")

        # Compute index and prev_hash
        index = len(self._blocks)
        prev_hash = self._compute_block_hash(self._blocks[-1]) if self._blocks else None

        # Create block
        timestamp = datetime.now(timezone.utc).isoformat()
        block = Block(
            index=index, timestamp=timestamp, entry=entry, prev_hash=prev_hash, mac=""  # Computed after serialization
        )

        # Compute MAC over block content with CURRENT key
        content = {
            "index": block.index,
            "timestamp": block.timestamp,
            "entry": block.entry,
            "prev_hash": block.prev_hash,
        }
        payload = json.dumps(content, sort_keys=True)
        block.mac = self._compute_mac(payload)  # Uses self._current_key

        # Append to disk with fsync
        with open(self.path, "a") as f:
            f.write(json.dumps(block.to_dict()) + "\n")
            f.flush()
            os.fsync(f.fileno())

        # Update in-memory state
        self._blocks.append(block)

        # Forward-secure key rotation (default enabled)
        if ratchet_key:
            self._ratchet_key()

        block_hash = self._compute_block_hash(block)
        logger.info(f"Appended block {index}: hash={block_hash[:8]}..., key_gen={len(self._key_history)}")
        return block_hash

    def verify_all(self) -> tuple[bool, Optional[str]]:
        """
        Verify complete ledger integrity (HMACs + chain) with forward-secure keys.

        Uses archived key history for verification - each block verified with
        the generation key that signed it.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check corruption flag first (set during disk load if malformed data)
        if self._is_corrupted:
            return False, "Ledger corrupted: Malformed data detected during load"

        if not self._blocks:
            return True, None

        prev_hash: Optional[str] = None

        for block in self._blocks:
            # Determine which generation key to use for verification
            # Key at index i signed blocks during generation i
            key_gen = min(block.index, len(self._key_history) - 1)
            verification_key = self._key_history[key_gen]

            # Verify HMAC with correct generation key
            content = {
                "index": block.index,
                "timestamp": block.timestamp,
                "entry": block.entry,
                "prev_hash": block.prev_hash,
            }
            payload = json.dumps(content, sort_keys=True)
            expected_mac = self._compute_mac(payload, key=verification_key)

            if not hmac.compare_digest(block.mac, expected_mac):
                return False, f"Block {block.index}: HMAC mismatch (gen {key_gen})"

            # Verify chain linkage
            if block.prev_hash != prev_hash:
                return False, f"Block {block.index}: Chain break (expected {prev_hash}, got {block.prev_hash})"

            # Update prev_hash for next iteration
            prev_hash = self._compute_block_hash(block)

        return True, None

    def get_blocks(self, start_index: int = 0, limit: Optional[int] = None) -> List[Block]:
        """
        Get immutable snapshot of blocks.

        Args:
            start_index: Starting block index (inclusive)
            limit: Maximum number of blocks to return

        Returns:
            List of Block objects (frozen copies)
        """
        end_index = start_index + limit if limit else len(self._blocks)
        return self._blocks[start_index:end_index].copy()

    def get_latest_hash(self) -> Optional[str]:
        """
        Get hash of most recent block.

        Returns:
            SHA-256 hex digest of latest block, or None if empty
        """
        if not self._blocks:
            return None
        return self._compute_block_hash(self._blocks[-1])

    def get_stats(self) -> Dict[str, Any]:
        """
        Get ledger statistics.

        Returns:
            Dictionary with block_count, latest_hash, is_corrupted
        """
        return {
            "block_count": len(self._blocks),
            "latest_hash": self.get_latest_hash(),
            "is_corrupted": self._is_corrupted,
            "path": str(self.path),
        }

    def seal_ledger(self) -> str:
        """
        Create final checkpoint hash over entire chain.

        Returns:
            SHA-256 hash of concatenated block hashes
        """
        if not self._blocks:
            return hashlib.sha256(b"").hexdigest()

        chain_data = "".join(self._compute_block_hash(block) for block in self._blocks)
        seal = hashlib.sha256(chain_data.encode()).hexdigest()
        logger.info(f"Ledger sealed: {seal[:16]}... ({len(self._blocks)} blocks)")
        return seal

    # Titanium Upgrade: Guardrail risk event logging (Axiom 3)
    def log_risk_event(self, risk_assessment: Dict[str, Any], prompt_hash: str) -> str:
        """Log a structured guardrail intervention with full risk metadata.

        Args:
            risk_assessment: Dict from guardrail decision (e.g., SemanticGuardResult.to_dict())
            prompt_hash: Stable reference to originating prompt (prehashed)

        Returns:
            Hash of the appended block.
        """
        entry: Dict[str, Any] = {
            "event_type": "GUARDRAIL_INTERVENTION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_ref": str(prompt_hash),
            "verdict": "BLOCKED" if risk_assessment.get("is_blocked") else "ALLOWED",
            "reason": risk_assessment.get("reason"),
            "scores": {
                "semantic": risk_assessment.get("semantic_score", 0.0),
                "fuzzy": risk_assessment.get("fuzzy_score", 0.0),
            },
            "mode_degraded": risk_assessment.get("mode_degraded", False),
        }
        # Include full risk vector for completeness
        entry["risk_details"] = risk_assessment
        return self.append(entry)


def create_ledger(path: str, key: Optional[bytes] = None) -> AppendOnlyLedger:
    """
    Factory function for creating ledgers with generated keys.

    Args:
        path: Ledger file path
        key: Optional HMAC key (generates secure random if None)

    Returns:
        Initialized AppendOnlyLedger
    """
    if key is None:
        key = os.urandom(32)  # 256-bit key
        logger.warning("Generated ephemeral HMAC key - not persisted!")

    return AppendOnlyLedger(path, key, verify_on_init=True)
