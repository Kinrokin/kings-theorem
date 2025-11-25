from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

LEDGER_PATH = Path("ledger/pceb_ledger.jsonl")
LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _hash_line(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_pceb(bundle_id: str, steps: int, veto: bool, final_hash: str) -> dict:
    """Append a PCEB record to ledger with simple hash chain integrity.
    Structure: {ts, bundle_id, steps, veto, final_hash, prev_hash, record_hash}
    """
    prev_hash = "GENESIS"
    if LEDGER_PATH.exists() and LEDGER_PATH.stat().st_size > 0:
        last = None
        with LEDGER_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                last = line
        if last:
            try:
                obj = json.loads(last)
                prev_hash = obj.get("record_hash", prev_hash)
            except Exception:
                prev_hash = "CORRUPTED"
    record = {
        "ts": time.time(),
        "bundle_id": bundle_id,
        "steps": steps,
        "veto": veto,
        "final_hash": final_hash,
        "prev_hash": prev_hash,
    }
    payload = json.dumps(record, sort_keys=True)
    record_hash = _hash_line(payload)
    record["record_hash"] = record_hash
    LEDGER_PATH.open("a", encoding="utf-8").write(json.dumps(record) + "\n")
    return record


def verify_chain() -> bool:
    """Verify linear hash chaining integrity for the PCEB ledger."""
    if not LEDGER_PATH.exists():
        return True
    prev = "GENESIS"
    with LEDGER_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                return False
            # recompute hash
            tmp = obj.copy()
            rh = tmp.pop("record_hash", None)
            payload = json.dumps(tmp, sort_keys=True)
            if _hash_line(payload) != rh:
                return False
            if obj.get("prev_hash") != prev:
                return False
            prev = rh
    return True
