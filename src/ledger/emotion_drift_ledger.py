from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

LEDGER_PATH = Path("ledger/emotion_drift_ledger.jsonl")
LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def append_drift(tone: str, dominance_ratio: float, alert: bool) -> dict:
    prev = "GENESIS"
    if LEDGER_PATH.exists():
        last = None
        with LEDGER_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                last = line
        if last:
            try:
                prev = json.loads(last).get("record_hash", prev)
            except Exception:
                prev = "CORRUPTED"
    rec = {
        "ts": time.time(),
        "tone": tone,
        "dominance_ratio": dominance_ratio,
        "alert": alert,
        "prev_hash": prev,
    }
    payload = json.dumps(rec, sort_keys=True)
    rec["record_hash"] = _hash(payload)
    LEDGER_PATH.open("a", encoding="utf-8").write(json.dumps(rec) + "\n")
    return rec


def verify_chain() -> bool:
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
            rh = obj.get("record_hash")
            tmp = obj.copy()
            tmp.pop("record_hash", None)
            payload = json.dumps(tmp, sort_keys=True)
            if _hash(payload) != rh:
                return False
            if obj.get("prev_hash") != prev:
                return False
            prev = rh
    return True
