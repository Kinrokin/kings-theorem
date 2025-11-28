"""KT Agent package.

Provides the constitutional super-agent interface that routes queries to
domain capability modules under the governance of the Hardened Arbiter.
"""

from .kt_agent import KTAgent  # re-export

__all__ = ["KTAgent"]
