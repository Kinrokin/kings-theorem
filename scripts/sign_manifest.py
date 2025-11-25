"""Script to sign deployment manifest with Ed25519 operator key.

Usage:
    python scripts/sign_manifest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.crypto import sign_json  # noqa: E402


def main() -> None:
    """Sign deployment manifest with operator key."""
    manifest_path = Path(__file__).resolve().parents[1] / "deployment" / "serving_manifest.json"

    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        sys.exit(1)

    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Check if already signed with new format
    if "_signature" in manifest:
        print("⚠️  Manifest already signed. Re-signing will invalidate previous signature.")
        response = input("Continue? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)
        # Remove old signature
        manifest = {k: v for k, v in manifest.items() if k != "_signature"}

    # Remove legacy signature fields if present
    legacy_fields = ["signature", "signed_by"]
    for field in legacy_fields:
        if field in manifest:
            print(f"⚠️  Removing legacy field: {field}")
            manifest.pop(field)

    # Sign with operator key
    try:
        signed_manifest = sign_json(manifest, "operator")
    except FileNotFoundError:
        print("❌ Operator key not found. Run: python scripts/keygen.py operator")
        sys.exit(1)

    # Write back to file
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(signed_manifest, f, indent=2)
        f.write("\n")

    print(f"✅ Manifest signed successfully: {manifest_path}")
    print(f"   Signature key: {signed_manifest['_signature']['key_id']}")
    print(f"   Timestamp: {signed_manifest['_signature']['timestamp']}")


if __name__ == "__main__":
    main()
