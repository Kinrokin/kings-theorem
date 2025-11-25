"""Script to attest approved federation sources.

Usage:
    python scripts/attest_federation_sources.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.federation.source_attestation import FederationAttestationRegistry  # noqa: E402


def main() -> None:
    """Attest example federation sources and save allowlist."""
    registry = FederationAttestationRegistry()

    print("🔐 Attesting federation sources...\n")

    # Example sources (in production, these would be real theological/philosophical texts)
    sources = [
        {
            "source_id": "axiom_utility_maximization",
            "source_type": "axiom",
            "content": "The good is that which maximizes aggregate utility.",
            "metadata": {"tradition": "utilitarian", "authority": "bentham_mill"},
        },
        {
            "source_id": "axiom_categorical_imperative",
            "source_type": "axiom",
            "content": "Act only according to that maxim whereby you can at the same time will that it should become a universal law.",
            "metadata": {"tradition": "deontological", "authority": "kant"},
        },
        {
            "source_id": "theological_golden_rule",
            "source_type": "theological",
            "content": "Do unto others as you would have them do unto you.",
            "metadata": {"tradition": "judeo_christian", "authority": "biblical"},
        },
    ]

    for source in sources:
        attestation = registry.attest_source(
            source_id=source["source_id"],
            source_type=source["source_type"],
            content=source["content"],
            attested_by="operator@local",
            metadata=source["metadata"],
        )
        print(f"✅ Attested: {source['source_id']}")
        print(f"   Type: {attestation.source_type}")
        print(f"   Hash: {attestation.content_hash[:16]}...")
        print(f"   Approved by: {attestation.attested_by}")
        print()

    # Save allowlist
    registry.save_allowlist()
    print(f"✅ Allowlist saved: {registry.allowlist_path}")
    print()
    print("⚠️  Next steps:")
    print("   1. Review generated config/federation_allowlist.yml")
    print("   2. Wire source verification into knowledge ingestion pipeline")
    print("   3. Enable KT_VERIFY_FEDERATION=1 in production")


if __name__ == "__main__":
    main()
