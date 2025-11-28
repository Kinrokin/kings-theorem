"""Federation source attestation for cryptographic provenance.

Provides Ed25519 signing for external theological/philosophical data sources.
Prevents injection of unattested external knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.crypto import sign_json, verify_json


@dataclass
class SourceAttestation:
    """Attestation record for external knowledge source."""

    source_id: str
    source_type: str  # "theological", "philosophical", "axiom", "definition"
    content_hash: str
    attested_by: str
    timestamp: str
    metadata: Dict[str, Any]


class FederationAttestationRegistry:
    """Registry for attesting external knowledge sources."""

    def __init__(self, allowlist_path: Optional[Path] = None) -> None:
        """Initialize registry from allowlist file.

        Args:
            allowlist_path: Path to federation allowlist YAML
        """
        if allowlist_path is None:
            allowlist_path = Path(__file__).resolve().parents[2] / "config" / "federation_allowlist.yml"

        self.allowlist_path = allowlist_path
        self.attestations: Dict[str, SourceAttestation] = {}

        if allowlist_path.exists():
            self._load_allowlist()

    def _load_allowlist(self) -> None:
        """Load federation allowlist from YAML file."""
        import yaml

        with open(self.allowlist_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        for source_id, record in data.get("sources", {}).items():
            attestation = SourceAttestation(
                source_id=source_id,
                source_type=record["source_type"],
                content_hash=record["content_hash"],
                attested_by=record["attested_by"],
                timestamp=record["timestamp"],
                metadata=record.get("metadata", {}),
            )
            self.attestations[source_id] = attestation

    def attest_source(
        self,
        source_id: str,
        source_type: str,
        content: str,
        attested_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SourceAttestation:
        """Attest an external knowledge source.

        Args:
            source_id: Unique identifier for source
            source_type: Type of source (theological, philosophical, etc.)
            content: Source content to attest
            attested_by: Identifier of attestor
            metadata: Optional metadata

        Returns:
            SourceAttestation record
        """
        import hashlib

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        attestation = SourceAttestation(
            source_id=source_id,
            source_type=source_type,
            content_hash=content_hash,
            attested_by=attested_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        self.attestations[source_id] = attestation
        return attestation

    def verify_source(self, source_id: str, content: str) -> bool:
        """Verify source content matches attestation.

        Args:
            source_id: Source identifier to verify
            content: Source content to verify

        Returns:
            True if hash matches attestation, False otherwise
        """
        if source_id not in self.attestations:
            return False

        import hashlib

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        attestation = self.attestations[source_id]

        return content_hash == attestation.content_hash

    def is_source_approved(self, source_id: str) -> bool:
        """Check if source is in approved allowlist.

        Args:
            source_id: Source identifier

        Returns:
            True if approved, False otherwise
        """
        return source_id in self.attestations

    def save_allowlist(self) -> None:
        """Save federation attestations to allowlist YAML."""
        import yaml

        data = {
            "version": 1,
            "sources": {
                source_id: {
                    "source_type": att.source_type,
                    "content_hash": att.content_hash,
                    "attested_by": att.attested_by,
                    "timestamp": att.timestamp,
                    "metadata": att.metadata,
                }
                for source_id, att in self.attestations.items()
            },
        }

        self.allowlist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.allowlist_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)


def sign_federated_data(data: Dict[str, Any], source_id: str, key_id: str = "governance") -> Dict[str, Any]:
    """Sign federated data with Ed25519 signature.

    Args:
        data: Federated data to sign
        source_id: Source identifier
        key_id: Signing key ID (default: governance)

    Returns:
        Signed data with _federation_signature field
    """
    data_with_source = data.copy()
    data_with_source["_federation_source"] = source_id

    return sign_json(data_with_source, key_id)


def verify_federated_data(data: Dict[str, Any]) -> bool:
    """Verify Ed25519 signature on federated data.

    Args:
        data: Signed federated data

    Returns:
        True if signature valid, False otherwise
    """
    if "_federation_signature" not in data and "_signature" not in data:
        return False

    return verify_json(data)


# Global registry
_registry: Optional[FederationAttestationRegistry] = None


def get_registry() -> FederationAttestationRegistry:
    """Get global federation attestation registry (singleton).

    Returns:
        FederationAttestationRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = FederationAttestationRegistry()
    return _registry


def verify_source_or_fail(source_id: str, content: str) -> None:
    """Verify source attestation or raise error.

    Args:
        source_id: Source identifier
        content: Source content

    Raises:
        RuntimeError: If source not approved or hash mismatch
    """
    registry = get_registry()

    if not registry.is_source_approved(source_id):
        raise RuntimeError(
            f"Federation source not approved: {source_id}. " f"Run: python scripts/attest_federation_sources.py"
        )

    if not registry.verify_source(source_id, content):
        raise RuntimeError(
            f"Federation source hash mismatch: {source_id}. " f"Source content has been modified since attestation."
        )
