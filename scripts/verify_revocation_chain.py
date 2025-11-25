"""Standalone revocation chain audit hardening script.

Verifies hash-chain integrity of revocation ledger; exits non-zero if invalid.
"""
from __future__ import annotations

import sys

from src.registry.ledger import RevocationLedger


def main():
    ledger = RevocationLedger()
    if not ledger.verify_chain():
        print("Revocation hash chain INVALID", file=sys.stderr)
        sys.exit(1)
    print("Revocation hash chain verified")


if __name__ == "__main__":
    main()
