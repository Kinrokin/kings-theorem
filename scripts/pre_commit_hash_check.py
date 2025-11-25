"""Pre-commit hook for hash enforcement.

Ensures requirements.lock exists and contains hashes before commit.
Install: ln -s ../../scripts/pre_commit_hash_check.py .git/hooks/pre-commit
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lock = ROOT / "requirements.lock"


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


def main():
    if not lock.exists():
        print("pre-commit FAILED: requirements.lock missing")
        print("Run: python scripts/generate_lockfile.py")
        sys.exit(1)

    missing_hash = False
    lines = lock.read_text(encoding="utf-8").splitlines()
    for header, block in iter_blocks(lines):
        has_hash = ("--hash=" in header) or any("--hash=" in b for b in block)
        if not has_hash:
            print(f"pre-commit FAILED: Missing hash in {lock.name}")
            print(f"Entry: {header.strip()}")
            missing_hash = True

    if missing_hash:
        print("   Run: python scripts/generate_lockfile.py")
        sys.exit(1)

    print("pre-commit: requirements.lock hash enforcement PASS")


if __name__ == "__main__":
    main()
