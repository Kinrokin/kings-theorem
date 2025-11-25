"""CLI tool for generating and managing Ed25519 signing keys.

Usage:
    # Generate operator keypair (for production manifests/risk budgets)
    python scripts/keygen.py operator

    # Generate manifest keypair (for deployment artifact signing)
    python scripts/keygen.py manifest

    # Generate governance keypair (for DSL theorem/ledger signing)
    python scripts/keygen.py governance
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.crypto import generate_keypair, save_keypair  # noqa: E402


def main() -> None:
    """Generate Ed25519 keypair and save to keys/ directory."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/keygen.py <key_id>")
        print("Example: python scripts/keygen.py operator")
        sys.exit(1)

    key_id = sys.argv[1]
    print(f"Generating Ed25519 keypair for: {key_id}")

    # Generate keypair
    keypair = generate_keypair(key_id)

    # Save to keys/ directory (private key unencrypted - use KMS in production!)
    base_dir = Path(__file__).resolve().parents[1] / "keys"
    save_keypair(keypair, base_dir)

    print("✅ Keypair saved:")
    print(f"   Private: {base_dir / f'{key_id}.pem'} (chmod 600)")
    print(f"   Public:  {base_dir / f'{key_id}.pub'}")
    print()
    print("⚠️  WARNING: Private key is unencrypted. For production:")
    print("   1. Use HSM/KMS for key storage")
    print("   2. Load from environment: KT_PRIVATE_KEY_{KEY_ID}")
    print("   3. Never commit private keys to git")


if __name__ == "__main__":
    main()
