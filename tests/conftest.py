import os
import sys

# Ensure repo root and src/ are on sys.path so tests can import the package reliably.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

def _ensure_path(p: str):
    if p and p not in sys.path:
        sys.path.insert(0, p)

_ensure_path(SRC)
_ensure_path(ROOT)

print(f"[conftest] added to sys.path: {SRC}, {ROOT}")
