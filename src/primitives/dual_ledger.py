"""
AID: /src/primitives/dual_ledger.py
Proof ID: PRF-AUDIT-001
Axiom: Axiom 3: Auditability by Design

Titanium X Upgrade:
- CryptographicLedger backend with Merkle Tree integrity
- Tamper-evident hash chain (blockchain-style)
- Immutable scar tissue for Cognitive Immune System
"""

import hashlib
import json
import logging
import time
from typing import Any

from src.primitives.exceptions import LedgerInvariantError
from src.primitives.merkle_ledger import CryptographicLedger

logger = logging.getLogger(__name__)


class DualLedger:
    """
    Dual Ledger with cryptographic integrity.

    Titanium X: Uses CryptographicLedger backend for Merkle Tree integrity.
    This ensures all "Scar Tissue" is immutable and tamper-evident.
    """

    def __init__(self):
        # Legacy chain for backwards compatibility
        self.chain = []
        self._problem_ids: set[str] = set()
        self._sealed = False

        # Titanium X: Cryptographic backend
        self._crypto_ledger = CryptographicLedger()
        logger.info("DualLedger initialized with CryptographicLedger backend")

    def log(self, actor: str, action: str, outcome: Any, problem_id: str | None = None):
        """
        Log entry to dual ledger with cryptographic integrity.

        Titanium X: Also logs to CryptographicLedger for Merkle Tree integrity.
        """
        if self._sealed:
            raise LedgerInvariantError("Cannot append to sealed ledger")

        if problem_id:
            if problem_id in self._problem_ids:
                raise LedgerInvariantError(f"Duplicate problem_id: {problem_id}")
            self._problem_ids.add(problem_id)

        timestamp = time.time()
        entry = {
            "timestamp": timestamp,
            "actor": actor,
            "action": action,
            "outcome": str(outcome),
        }
        if problem_id:
            entry["problem_id"] = problem_id

        entry_str = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_str.encode("utf-8")).hexdigest()
        prev_hash = self.chain[-1]["hash"] if self.chain else "000000"

        block = {"entry": entry, "hash": entry_hash, "prev_hash": prev_hash}
        self.chain.append(block)

        # Titanium X: Log to cryptographic backend
        merkle_root = self._crypto_ledger.add_entry(entry)

        logger.info(
            "[LEDGER] %s | %s | Hash: %s | Merkle: %s",
            actor.ljust(10),
            action.ljust(15),
            entry_hash[:8],
            merkle_root[:8] if merkle_root else "N/A",
        )
        return entry_hash

    def seal(self) -> None:
        """
        Mark ledger as sealed; no further appends allowed.

        Titanium X: Also seals cryptographic ledger with final hash.
        """
        self._sealed = True

        # Titanium X: Seal cryptographic ledger
        seal_hash = self._crypto_ledger.seal_ledger()

        logger.info("[LEDGER] Sealed with %d entries | Seal: %s", len(self.chain), seal_hash[:16])

    def verify_monotonicity(self) -> bool:
        """
        Check chain hashes link correctly (no deletions/tampering).

        Titanium X: Also verifies cryptographic ledger integrity.
        """
        # Check legacy chain
        for i, block in enumerate(self.chain):
            expected_prev = self.chain[i - 1]["hash"] if i > 0 else "000000"
            if block["prev_hash"] != expected_prev:
                logger.error(f"Chain integrity violation at block {i}")
                return False

        # Titanium X: Check cryptographic ledger
        is_valid, reason = self._crypto_ledger.verify_integrity(verbose=True)
        if not is_valid:
            logger.error(f"Merkle integrity violation: {reason}")
            return False

        return True

    def get_merkle_root(self) -> str:
        """Get current Merkle root hash (Titanium X)."""
        if self._crypto_ledger.root_history:
            return self._crypto_ledger.root_history[-1]["root"]
        return "EMPTY"

    def verify_crypto_integrity(self) -> tuple[bool, str | None]:
        """Verify cryptographic ledger integrity (Titanium X)."""
        return self._crypto_ledger.verify_integrity(verbose=True)
