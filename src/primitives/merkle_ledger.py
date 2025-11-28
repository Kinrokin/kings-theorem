"""Merkle Ledger - Titanium X Protocol

AID: /src/primitives/merkle_ledger.py
Proof ID: PRF-AXIOM3-TX-001
Axiom: Axiom 3 (Cryptographic Auditability via Merkle Trees)

Titanium X Upgrades:
- Pure Python implementation (no merklelib dependency)
- Simple binary tree with SHA-256 hashing
- Deterministic canonical JSON serialization
- Immutable ledger with tamper detection
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


class MerkleLedger:
    """Immutable cryptographic audit ledger.

    Uses binary Merkle tree for tamper-evident history tracking.
    Each entry is canonicalized (sorted JSON) before hashing.

    Security Properties:
    - Immutability: Cannot modify history without detection
    - Integrity: Root hash commits to all entries
    - Auditability: Complete proof chain from entry to root
    """

    def __init__(self):
        """Initialize empty ledger.

        Adds dual root history tracking for legacy test compatibility:
        - _root_history: list of root hashes (strings) for internal chain ops
        - _root_history_dicts: list of {'index': int, 'root': str} for tests expecting dict access
        """
        self._data_blocks: List[str] = []
        self._root_history: List[str] = []  # internal string roots
        self._root_history_dicts: List[Dict[str, Any]] = []  # compatibility dict form

    @staticmethod
    def _canonical(entry: Dict[str, Any]) -> str:
        """Convert entry to canonical JSON string (deterministic).

        TITANIUM UPGRADE: Recursive canonicalization.
        Ensures complex objects (like risk assessments) hash deterministically.

        Args:
            entry: Dictionary to canonicalize

        Returns:
            JSON string with sorted keys, no whitespace

        Notes:
            - 'default=str' handles objects that aren't natively serializable
              (e.g., numpy floats, complex nested objects)
            - 'sort_keys=True' is critical for Merkle consistency
        """
        return json.dumps(entry, sort_keys=True, separators=(",", ":"), default=str)

    @staticmethod
    def _hash_data(data: str) -> str:
        """Compute SHA-256 hash of data.

        Args:
            data: String to hash

        Returns:
            Hex-encoded hash digest
        """
        return hashlib.sha256(data.encode()).hexdigest()

    def _build_merkle_tree(self, blocks: List[str]) -> str:
        """Build Merkle tree from blocks and return root hash.

        Args:
            blocks: List of canonical JSON strings

        Returns:
            Merkle root hash (hex-encoded)
        """
        if not blocks:
            return self._hash_data("EMPTY_TREE")

        # Hash each block
        hashes = [self._hash_data(block) for block in blocks]

        # Build tree bottom-up
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                parent = self._hash_data(left + right)
                next_level.append(parent)
            hashes = next_level

        return hashes[0]

    def log(self, *args: Any, **kwargs: Any) -> str:
        """Add entry to ledger and return Merkle root.

        Supports two signatures:
        1. log(dict_entry)
        2. log(actor: str, action: str, data: Any)

        Args:
            *args: Either (entry_dict,) or (actor, action, data)
            **kwargs: Ignored (reserved for future metadata)

        Returns:
            Hex-encoded Merkle root hash
        """
        if len(args) == 1 and isinstance(args[0], dict):
            entry: Dict[str, Any] = args[0]
        elif len(args) >= 3:
            actor = str(args[0])
            action = str(args[1])
            data = args[2]
            entry = {"actor": actor, "action": action, "data": data}
        else:
            raise ValueError("Invalid log() signature. Use log(dict) or log(actor, action, data)")

        block = self._canonical(entry)
        self._data_blocks.append(block)

        # Rebuild Merkle tree
        root = self._build_merkle_tree(self._data_blocks)

        # Chain roots for temporal integrity
        self._root_history.append(root)
        self._root_history_dicts.append({"index": len(self._data_blocks) - 1, "root": root})

        print(f"[LEDGER] Merkle Root: {root[:16]}... (Entry #{len(self._data_blocks)})")

        return root

    def add_entry(self, entry: Dict[str, Any]) -> str:
        """Alias for log(dict_entry)."""
        return self.log(entry)

    def verify_integrity(self) -> tuple[bool, str | None]:
        """Verify ledger has not been tampered with.

        Returns:
            (is_valid, reason)
            - is_valid: True if ledger intact
            - reason: None if valid, else diagnostic message containing 'INTEGRITY VIOLATION'
        """
        if not self._data_blocks:
            return True, None  # Empty ledger is trivially valid

        computed_root = self._build_merkle_tree(self._data_blocks)
        recorded_root = self._root_history[-1]

        if computed_root != recorded_root:
            return False, "INTEGRITY VIOLATION: Merkle root mismatch (possible tamper/deletion/reorder)"
        # Cross-check dict history last entry for consistency
        if self._root_history_dicts and self._root_history_dicts[-1]["root"] != recorded_root:
            return False, "INTEGRITY VIOLATION: Root history dict mismatch"
        return True, None

    def seal_ledger(self) -> str:
        """Create final cryptographic seal.

        Returns:
            SHA-256 hash of final root + entry count
        """
        if not self._root_history:
            return "EMPTY_LEDGER"

        final_root = self._root_history[-1]
        entry_count = len(self._data_blocks)

        seal_data = f"{final_root}|{entry_count}"
        seal_hash = hashlib.sha256(seal_data.encode()).hexdigest()

        return seal_hash

    def get_root_history(self) -> List[str]:
        """Get complete chain of Merkle roots (string form)."""
        return self._root_history.copy()

    def __len__(self) -> int:
        """Return number of entries in ledger."""
        return len(self._data_blocks)

    def __repr__(self) -> str:
        """String representation for debugging."""
        root_preview = self._root_history[-1][:16] if self._root_history else "none"
        return f"MerkleLedger(entries={len(self._data_blocks)}, root={root_preview}...)"

    # ------------------------------------------------------------------
    # Legacy compatibility accessors (tests expect public lists)
    # ------------------------------------------------------------------
    @property
    def data_blocks(self) -> List[str]:
        """Legacy: expose underlying canonical JSON blocks list.

        WARNING: Mutating elements simulates tampering and should cause
        verify_integrity() to fail. Do NOT append via this interface in
        production code; use log()/add_entry() instead.
        """
        return self._data_blocks

    @property
    def root_history(self) -> List[Dict[str, Any]]:
        """Legacy compatibility: expose list of dict entries with root metadata.

        Tests expect: ledger.root_history[-1]["root"]
        """
        return list(self._root_history_dicts)

    @property
    def chain(self) -> List[Dict[str, Any]]:
        """Legacy: expose ledger entries as dictionary chain.

        Returns list of entries with structure:
        [{"root": merkle_root, "data": canonical_json}, ...]
        """
        chain = []
        for i, (data, root) in enumerate(zip(self._data_blocks, self._root_history)):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                parsed = {"raw": data}
            chain.append({"root": root, "data": parsed, "index": i})
        return chain


__all__ = ["MerkleLedger"]

# Legacy compatibility aliases
CryptographicLedger = MerkleLedger
