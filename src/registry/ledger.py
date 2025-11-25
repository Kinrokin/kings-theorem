from __future__ import annotations
import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, Iterator, Optional


@dataclass
class RevocationEvent:
    evidence_id: str
    reason: str
    signed_by: str
    timestamp_utc: float
    prev_hash: str
    event_hash: str
    metadata: Optional[Dict] = None


class RevocationLedger:
    """
    Append-only revocation ledger with hash chaining.

    - Entries are stored one-per-line as JSON (JSONL) at `path`.
    - Each entry includes `prev_hash` and `event_hash` to provide local tamper evidence.
    - `is_revoked(evidence_id)` returns True if any entry matches the given id.
    """

    def __init__(self, path: str = os.path.join("logs", "revocations.jsonl")) -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            open(self.path, "a", encoding="utf-8").close()

    def _last_hash(self) -> str:
        last = ""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    last = obj.get("event_hash", last)
        except FileNotFoundError:
            return ""
        return last

    @staticmethod
    def _compute_event_hash(payload: Dict) -> str:
        h = hashlib.sha256()
        h.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        return h.hexdigest()

    def revoke(
        self,
        evidence_id: str,
        reason: str,
        signed_by: str,
        *,
        metadata: Optional[Dict] = None,
    ) -> RevocationEvent:
        prev = self._last_hash()
        base = {
            "evidence_id": evidence_id,
            "reason": reason,
            "signed_by": signed_by,
            "timestamp_utc": time.time(),
            "prev_hash": prev,
            "metadata": metadata or {},
        }
        event_hash = self._compute_event_hash(base)
        evt = RevocationEvent(
            evidence_id=evidence_id,
            reason=reason,
            signed_by=signed_by,
            timestamp_utc=base["timestamp_utc"],
            prev_hash=prev,
            event_hash=event_hash,
            metadata=metadata or {},
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(evt)) + "\n")
        return evt

    def is_revoked(self, evidence_id: str) -> bool:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    o = json.loads(line)
                    if o.get("evidence_id") == evidence_id:
                        return True
        except FileNotFoundError:
            return False
        return False

    def verify_chain(self) -> bool:
        """Verify the hash chain for local tamper evidence."""
        prev = ""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    o = json.loads(line)
                    if o.get("prev_hash", "") != prev:
                        return False
                    # recompute
                    recompute = self._compute_event_hash({
                        k: o[k] for k in [
                            "evidence_id", "reason", "signed_by", "timestamp_utc", "prev_hash", "metadata"
                        ] if k in o
                    })
                    if recompute != o.get("event_hash"):
                        return False
                    prev = o.get("event_hash", "")
        except FileNotFoundError:
            return True
        return True

    def iter_revocations(self) -> Iterator[RevocationEvent]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    o = json.loads(line)
                    yield RevocationEvent(**o)
        except FileNotFoundError:
            return
