"""KT Convenience Package

Exposes the canonical `KTEngine` for `python -m kt.run_engine` flows.
"""

from src.core.kt_engine import KTEngine  # re-export

__all__ = ["KTEngine"]
