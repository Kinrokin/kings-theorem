import os
import sys


def pytest_configure(config):
    config.addinivalue_line("markers", "kt_bias: Bias coverage / tradition diversity tests")
    config.addinivalue_line("markers", "kt_emotion: Emotional palette invariants")
    config.addinivalue_line("markers", "kt_composition: Composition safety and theorem checks")


# Ensure repo root and src/ are on sys.path so tests can import the package reliably.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

# Also detect embedded project folders (e.g., a nested 'kings-theorem' workspace)
nested_srcs = []
for entry in os.listdir(ROOT):
    candidate = os.path.join(ROOT, entry)
    if os.path.isdir(candidate):
        possible_src = os.path.join(candidate, "src")
        if os.path.isdir(possible_src) and os.path.isdir(os.path.join(possible_src, "kings_theorem")):
            nested_srcs.append(possible_src)


def _ensure_path(p: str):
    if p and p not in sys.path:
        sys.path.insert(0, p)


_ensure_path(SRC)
_ensure_path(ROOT)
for ns in nested_srcs:
    _ensure_path(ns)

if nested_srcs:
    print(f"[conftest] added nested src paths: {nested_srcs}")

print(f"[conftest] added to sys.path: {SRC}, {ROOT}")
