"""Distributed primitives: immutable node identity for Level 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KTNodeIdentity:
    """Immutable identity for a KT node.

    Args:
        node_id: Unique node identifier.
        role: One of "EXECUTOR", "ARBITER", "OBSERVER".
        region: Optional region or zone.
        public_key: Optional public key (PEM or fingerprint).
    """

    node_id: str
    role: str  # "EXECUTOR", "ARBITER", "OBSERVER"
    region: Optional[str] = None
    public_key: Optional[str] = None
