"""Script to sign risk budget configuration with Ed25519 governance key.

Usage:
    python scripts/sign_risk_budget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.crypto import sign_json  # noqa: E402


def main() -> None:
    """Sign risk budget YAML with governance key."""
    budget_path = Path(__file__).resolve().parents[1] / "config" / "risk_budget.yml"

    if not budget_path.exists():
        print(f"❌ Risk budget not found: {budget_path}")
        sys.exit(1)

    # Load risk budget YAML
    with open(budget_path, "r", encoding="utf-8") as f:
        budget = yaml.safe_load(f)

    # Check if already signed
    if "_signature" in budget:
        print("⚠️  Risk budget already signed. Re-signing will invalidate previous signature.")
        response = input("Continue? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)
        # Remove old signature
        budget = {k: v for k, v in budget.items() if k != "_signature"}

    # Sign with governance key
    try:
        signed_budget = sign_json(budget, "governance")
    except FileNotFoundError:
        print("❌ Governance key not found. Run: python scripts/keygen.py governance")
        sys.exit(1)

    # Write back to YAML file
    with open(budget_path, "w", encoding="utf-8") as f:
        yaml.dump(signed_budget, f, sort_keys=False, default_flow_style=False)

    print(f"✅ Risk budget signed successfully: {budget_path}")
    print(f"   Signature key: {signed_budget['_signature']['key_id']}")
    print(f"   Timestamp: {signed_budget['_signature']['timestamp']}")


if __name__ == "__main__":
    main()
