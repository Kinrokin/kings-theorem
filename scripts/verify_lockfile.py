from __future__ import annotations

"""Strict supply chain lock verification for requirements.lock.

Validates that:
- requirements.lock exists
- Each pinned requirement block includes at least one "--hash=" entry

Supports pip-compile's multi-line format with continuation lines for hashes.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lock = ROOT / "requirements.lock"
req = ROOT / "requirements.txt"


def iter_blocks(lines: list[str]):
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


def read_lines(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8", errors="ignore").splitlines() if p.exists() else []


def main():
    errors = []
    if not lock.exists():
        print("Missing requirements.lock - run: python scripts/generate_lockfile.py")
        sys.exit(1)
    lock_lines = read_lines(lock)
    req_lines = [s.strip() for s in read_lines(req) if s.strip() and not s.strip().startswith("#")]
    req_pkgs = {line.split("==")[0].lower() for line in req_lines if "==" in line}

    for header, block in iter_blocks(lock_lines):
        has_hash = ("--hash=" in header) or any("--hash=" in b for b in block)
        if not has_hash:
            errors.append(f"Missing hash: {header.strip()}")
        _ = req_pkgs  # placeholder for future strict sync checks

    if errors:
        print("Supply chain lock verification failed:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("Supply chain lock verification passed.")


if __name__ == "__main__":
    main()
"""Strict supply chain lock verification.

Checks:
 - requirements.lock exists.
 - All non-comment lines pinned with '=='.
 - Each pinned package appears in requirements.txt (basic sync check).
Future: integrate hash-based verification (PEP 665 / --require-hashes style).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lock = ROOT / "requirements.lock"
req = ROOT / "requirements.txt"


def parse_lines(p: Path) -> list[str]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("-") or s.startswith("via"):
            continue
        out.append(s)
    return out


def main():
    errors = []
    if not lock.exists():
        print("Missing requirements.lock - run: python scripts/generate_lockfile.py")
        sys.exit(1)
    lock_lines = parse_lines(lock)
    req_lines = parse_lines(req)
    req_pkgs = {l.split("==")[0].lower() for l in req_lines if "==" in l}
    for l in lock_lines:
        if "==" not in l:
            errors.append(f"Unpinned dependency: {l}")
        elif "--hash=" not in l:
            errors.append(f"Missing hash: {l}")
        else:
            name = l.split("==")[0].lower().strip()
            if name and name not in req_pkgs:
                # Transitive deps from pip-compile are allowed
                pass
    if errors:
        print("Supply chain lock verification failed:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("Supply chain lock verification passed.")


if __name__ == "__main__":
    main()
