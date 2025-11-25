"""Strict supply chain lock verification for requirements.lock.

Validates:
- requirements.lock exists
- Each pinned requirement includes at least one "--hash=" entry

Understands pip-compile multi-line hash continuation format.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "requirements.lock"


def _iter_requirement_blocks(lines: list[str]):
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "==" not in line:
            continue
        header = line
        block = []
        while i < n:
            nxt = lines[i]
            if nxt.startswith(" ") or nxt.startswith("\t") or nxt.strip().startswith("--hash="):
                block.append(nxt.rstrip())
                i += 1
            else:
                break
        yield header, block


def main() -> None:
    if not LOCK_PATH.exists():
        print("Missing requirements.lock - run: python scripts/generate_lockfile.py")
        raise SystemExit(1)

    lines = LOCK_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    errors: list[str] = []
    for header, block in _iter_requirement_blocks(lines):
        has_hash = ("--hash=" in header) or any("--hash=" in b for b in block)
        if not has_hash:
            errors.append(f"Missing hash: {header.strip()}")

    if errors:
        print("Supply chain lock verification failed:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)

    print("Supply chain lock verification passed.")


if __name__ == "__main__":
    main()
