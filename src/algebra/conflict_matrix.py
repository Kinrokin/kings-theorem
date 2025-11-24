"""Conflict matrix for constraint domains.

This module provides a simple mapping of domain pairs to conflict severity.
"""

from typing import Dict, Tuple

# Keys are (domain_a, domain_b) where domain names are lowercase strings
CONFLICT_MATRIX: Dict[Tuple[str, str], str] = {
    ("safety", "reckless"): "incompatible",
    ("ethical", "malicious"): "forbidden",
}


def check_conflict(domain_a: str, domain_b: str) -> str:
    """Return conflict label or empty string if no conflict."""
    a = domain_a.lower() if domain_a else ""
    b = domain_b.lower() if domain_b else ""
    # check both orders
    res = CONFLICT_MATRIX.get((a, b)) or CONFLICT_MATRIX.get((b, a))
    return res or ""
