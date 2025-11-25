"""Ed25519 key management for artifact signing.

Loads signing keys from environment or secure key storage.
Never commit private keys to the repository.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


@dataclass
class KeyPair:
    """Ed25519 keypair for signing and verification."""

    private_key: ed25519.Ed25519PrivateKey
    public_key: ed25519.Ed25519PublicKey
    key_id: str


def generate_keypair(key_id: str = "default") -> KeyPair:
    """Generate a new Ed25519 keypair for signing.

    Args:
        key_id: Identifier for this keypair (e.g., "operator", "manifest", "governance")

    Returns:
        KeyPair with private and public keys
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return KeyPair(private_key=private_key, public_key=public_key, key_id=key_id)


def save_keypair(keypair: KeyPair, base_dir: Path, passphrase: Optional[bytes] = None) -> None:
    """Save keypair to disk (private key with optional encryption, public key plaintext).

    WARNING: Only use for development/testing. Production should use HSM/KMS.

    Args:
        keypair: KeyPair to save
        base_dir: Directory to store keys (e.g., keys/)
        passphrase: Optional passphrase to encrypt private key
    """
    base_dir.mkdir(parents=True, exist_ok=True)

    # Save private key (encrypted if passphrase provided)
    private_path = base_dir / f"{keypair.key_id}.pem"
    encryption_algorithm = (
        serialization.BestAvailableEncryption(passphrase) if passphrase else serialization.NoEncryption()
    )
    private_pem = keypair.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption_algorithm,
    )
    private_path.write_bytes(private_pem)
    private_path.chmod(0o600)  # Restrict to owner read/write only

    # Save public key
    public_path = base_dir / f"{keypair.key_id}.pub"
    public_pem = keypair.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_path.write_bytes(public_pem)


def load_private_key(
    key_id: str, base_dir: Optional[Path] = None, passphrase: Optional[bytes] = None
) -> ed25519.Ed25519PrivateKey:
    """Load private key from disk or environment.

    Priority:
    1. Environment variable KT_PRIVATE_KEY_{KEY_ID}
    2. File at {base_dir}/{key_id}.pem
    3. Raise error if not found

    Args:
        key_id: Key identifier (e.g., "operator", "manifest")
        base_dir: Directory containing keys (default: keys/)
        passphrase: Optional passphrase to decrypt private key

    Returns:
        Ed25519PrivateKey

    Raises:
        FileNotFoundError: If key not found in env or filesystem
    """
    env_key = f"KT_PRIVATE_KEY_{key_id.upper()}"
    if env_key in os.environ:
        pem_data = os.environ[env_key].encode("utf-8")
        return serialization.load_pem_private_key(pem_data, password=passphrase)

    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[2] / "keys"

    key_path = base_dir / f"{key_id}.pem"
    if not key_path.exists():
        raise FileNotFoundError(
            f"Private key not found: {key_path}. " f"Set {env_key} environment variable or generate keypair."
        )

    pem_data = key_path.read_bytes()
    return serialization.load_pem_private_key(pem_data, password=passphrase)


def load_public_key(key_id: str, base_dir: Optional[Path] = None) -> ed25519.Ed25519PublicKey:
    """Load public key from disk or environment.

    Priority:
    1. Environment variable KT_PUBLIC_KEY_{KEY_ID}
    2. File at {base_dir}/{key_id}.pub

    Args:
        key_id: Key identifier
        base_dir: Directory containing keys (default: keys/)

    Returns:
        Ed25519PublicKey

    Raises:
        FileNotFoundError: If key not found
    """
    env_key = f"KT_PUBLIC_KEY_{key_id.upper()}"
    if env_key in os.environ:
        pem_data = os.environ[env_key].encode("utf-8")
        return serialization.load_pem_public_key(pem_data)

    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[2] / "keys"

    key_path = base_dir / f"{key_id}.pub"
    if not key_path.exists():
        raise FileNotFoundError(f"Public key not found: {key_path}")

    pem_data = key_path.read_bytes()
    return serialization.load_pem_public_key(pem_data)
