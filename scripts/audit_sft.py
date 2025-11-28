"""Quick audit of SFT dataset in logs/golden_dataset.jsonl.

Metrics reported:
- Record count
- Status distribution
- Prompt length stats
- Completion length stats
- Lines containing potentially sensitive terms (heuristic scan)
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import statistics as st

DATA_PATH = Path("logs/golden_dataset.jsonl")
UNSAFE_TERMS = ["sacrifice_minority", "destroy", "harm"]


def audit(path: Path = DATA_PATH) -> dict:
    lines = path.read_text().splitlines() if path.exists() else []
    statuses: list[str] = []
    prompt_lens: list[int] = []
    completion_lens: list[int] = []
    sensitive: list[int] = []

    for i, l in enumerate(lines, 1):
        try:
            rec = json.loads(l)
        except Exception:
            continue
        prompt = rec.get("prompt", "")
        completion_raw = rec.get("completion", "")
        prompt_lens.append(len(prompt))
        completion_lens.append(len(completion_raw))
        try:
            inner = json.loads(completion_raw)
            status = inner.get("status", "UNKNOWN")
            txt = json.dumps(inner).lower()
        except Exception:
            status = "UNKNOWN"
            txt = completion_raw.lower()
        statuses.append(status)
        if any(t in txt for t in UNSAFE_TERMS):
            sensitive.append(i)

    summary = {
        "records": len(lines),
        "status_distribution": Counter(statuses),
        "prompt_len": {
            "mean": st.mean(prompt_lens) if prompt_lens else 0,
            "min": min(prompt_lens) if prompt_lens else 0,
            "max": max(prompt_lens) if prompt_lens else 0,
        },
        "completion_len": {
            "mean": st.mean(completion_lens) if completion_lens else 0,
            "min": min(completion_lens) if completion_lens else 0,
            "max": max(completion_lens) if completion_lens else 0,
        },
        "potential_sensitive_lines": sensitive,
    }
    return summary


def main() -> None:
    summary = audit()
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
