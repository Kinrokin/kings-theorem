"""Generate hashed requirements lockfile using pip-compile.

Workflow:
1. Install pip-tools if missing.
2. Run pip-compile --generate-hashes requirements.txt -o requirements.lock
3. Verify all lines contain hashes.

Usage: python scripts/generate_lockfile.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    # Ensure pip-tools installed
    try:
        subprocess.run(["pip-compile", "--version"], check=True, capture_output=True)
    except Exception:
        print("Installing pip-tools...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools"], check=True)

    # Generate hashed lockfile
    print("Generating requirements.lock with hashes...")
    subprocess.run(
        [
            "pip-compile",
            "--generate-hashes",
            "--output-file",
            "requirements.lock",
            "requirements.txt",
        ],
        cwd=ROOT,
        check=True,
    )

    # Verify all non-comment lines have hashes
    lock = ROOT / "requirements.lock"
    errors = []
    for line in lock.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("-") or s.startswith("via"):
            continue
        if "--hash=" not in s:
            errors.append(f"Missing hash: {s}")

    if errors:
        print("Lockfile validation failed:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print(f"✓ Generated {lock} with hashes for all dependencies")


if __name__ == "__main__":
    main()
