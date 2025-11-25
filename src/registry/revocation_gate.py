"""Revocation Gate Utilities

Loads revocation ledger JSONL (hash-chained) and provides helper to check
whether an EvidenceID or manifest id has been revoked.

Ledger record format (expected minimal fields):
{"timestamp": ..., "revoked_id": "EVID-123", "reason": "compromised"}

This is intentionally lightweight; future versions may verify hash chain integrity.
"""
from __future__ import annotations
from pathlib import Path
from typing import Set
import json


def load_revocations(ledger_path: Path) -> Set[str]:
    revoked: Set[str] = set()
    if not ledger_path.exists():
        return revoked
    for line in ledger_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        rid = rec.get("revoked_id") or rec.get("evidence_id") or rec.get("manifest_id")
        if rid:
            revoked.add(str(rid))
    return revoked


def is_revoked(identifier: str, ledger_path: Path) -> bool:
    return identifier in load_revocations(ledger_path)
