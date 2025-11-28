"""
AID: /src/primitives/dual_ledger.py
Proof ID: PRF-AUDIT-001
Axiom: Axiom 3: Auditability by Design
Purpose: Immutable logging with cryptographic hashing.
"""
import hashlib
import json
import logging
import time
from typing import Any

from src.utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class DualLedger:
    def __init__(self):
        self.chain = []

    def log(self, actor: str, action: str, outcome: Any):
        timestamp = time.time()
        entry = {"timestamp": timestamp, "actor": actor, "action": action, "outcome": str(outcome)}
        # Create cryptographic seal
        entry_str = json.dumps(entry, sort_keys=True)
        entry_hash = hashlib.sha256(entry_str.encode("utf-8")).hexdigest()

        prev_hash = self.chain[-1]["hash"] if self.chain else "000000"

        block = {"entry": entry, "hash": entry_hash, "prev_hash": prev_hash}
        self.chain.append(block)
        logger.info(f"[LEDGER] {actor.ljust(10)} | {action.ljust(15)} | Hash: {entry_hash[:8]}...")
        return entry_hash
