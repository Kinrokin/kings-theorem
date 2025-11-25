"""Ed25519 signing and verification for artifact integrity.

Provides sign/verify primitives for:
- Manifest files (deployment/serving_manifest.json)
- Risk budgets (config/risk_budget.yml)
- DSL theorem artifacts (audit/dsl_theorems.json)
- Ledger hash chains (PCEB, emotion drift, revocation)
- Kernel attestation records
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.exceptions import InvalidSignature

from src.crypto.keys import load_private_key, load_public_key


@dataclass
class Signature:
    """Cryptographic signature with metadata."""

    signature_bytes: bytes
    key_id: str
    timestamp: str
    algorithm: str = "ed25519"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize signature to dict for JSON embedding."""
        return {
            "signature": self.signature_bytes.hex(),
            "key_id": self.key_id,
            "timestamp": self.timestamp,
            "algorithm": self.algorithm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Signature:
        """Deserialize signature from JSON dict."""
        return cls(
            signature_bytes=bytes.fromhex(data["signature"]),
            key_id=data["key_id"],
            timestamp=data["timestamp"],
            algorithm=data.get("algorithm", "ed25519"),
        )


def sign_bytes(data: bytes, key_id: str, passphrase: Optional[bytes] = None) -> Signature:
    """Sign arbitrary bytes with Ed25519 private key.

    Args:
        data: Raw bytes to sign
        key_id: Identifier of key to use (e.g., "operator", "manifest")
        passphrase: Optional passphrase if private key is encrypted

    Returns:
        Signature with raw signature bytes and metadata

    Raises:
        FileNotFoundError: If private key not found
    """
    private_key = load_private_key(key_id, passphrase=passphrase)
    signature_bytes = private_key.sign(data)
    timestamp = datetime.now(timezone.utc).isoformat()

    return Signature(
        signature_bytes=signature_bytes,
        key_id=key_id,
        timestamp=timestamp,
        algorithm="ed25519",
    )


def verify_bytes(data: bytes, signature: Signature) -> bool:
    """Verify Ed25519 signature on raw bytes.

    Args:
        data: Original bytes that were signed
        signature: Signature to verify

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        public_key = load_public_key(signature.key_id)
        public_key.verify(signature.signature_bytes, data)
        return True
    except (InvalidSignature, FileNotFoundError):
        return False


def sign_json(data: Dict[str, Any], key_id: str, passphrase: Optional[bytes] = None) -> Dict[str, Any]:
    """Sign JSON object by computing canonical hash and signing.

    Args:
        data: JSON-serializable dict to sign
        key_id: Key identifier for signing
        passphrase: Optional passphrase for encrypted private key

    Returns:
        New dict with original data + "_signature" field
    """
    # Compute canonical hash (deterministic JSON encoding)
    canonical_bytes = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    data_hash = hashlib.sha256(canonical_bytes).digest()

    # Sign the hash
    signature = sign_bytes(data_hash, key_id, passphrase)

    # Embed signature in new dict
    signed_data = data.copy()
    signed_data["_signature"] = signature.to_dict()
    return signed_data


def verify_json(signed_data: Dict[str, Any]) -> bool:
    """Verify signature on signed JSON object.

    Args:
        signed_data: Dict with "_signature" field from sign_json()

    Returns:
        True if signature is valid, False otherwise
    """
    if "_signature" not in signed_data:
        return False

    # Extract signature and original data
    signature_dict = signed_data["_signature"]
    signature = Signature.from_dict(signature_dict)

    # Recreate canonical hash from original data (without signature)
    original_data = {k: v for k, v in signed_data.items() if k != "_signature"}
    canonical_bytes = json.dumps(original_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    data_hash = hashlib.sha256(canonical_bytes).digest()

    # Verify signature
    return verify_bytes(data_hash, signature)


def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of file contents for attestation.

    Args:
        filepath: Path to file to hash

    Returns:
        Hex-encoded SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
