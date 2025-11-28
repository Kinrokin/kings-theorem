# src/kernels/metadata.py
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import asdict, dataclass
from typing import Optional

logger = logging.getLogger("kt.kernels.metadata")
logger.setLevel(logging.INFO)

# Try Ed25519 via cryptography if available, else HMAC fallback
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

    CRYPTO_ED25519_AVAILABLE = True
except Exception:
    CRYPTO_ED25519_AVAILABLE = False


@dataclass(frozen=True)
class KernelMetadata:
    kernel_id: str
    type: str
    warrant_threshold: float
    veto_power: int
    proof_burden: str
    signature: Optional[str] = None  # hex str

    def payload(self) -> bytes:
        """Deterministic payload for signing (sorted keys)."""
        d = {
            "kernel_id": self.kernel_id,
            "type": self.type,
            "warrant_threshold": float(self.warrant_threshold),
            "veto_power": int(self.veto_power),
            "proof_burden": self.proof_burden,
        }
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")


# Ed25519 helpers
def sign_with_ed25519(privkey_pem: bytes, payload: bytes) -> str:
    priv = (
        Ed25519PrivateKey.from_private_bytes(privkey_pem)
        if isinstance(privkey_pem, bytes) and len(privkey_pem) == 32
        else Ed25519PrivateKey.from_private_bytes(privkey_pem)
    )
    sig = priv.sign(payload)
    return sig.hex()


def verify_with_ed25519(pubkey_pem: bytes, payload: bytes, sig_hex: str) -> bool:
    try:
        pub = Ed25519PublicKey.from_public_bytes(pubkey_pem)
        pub.verify(bytes.fromhex(sig_hex), payload)
        return True
    except Exception as e:
        logger.debug("Ed25519 verify failed: %s", e)
        return False


# HMAC fallback helpers (insecure for prod — use only if Ed25519 unavailable)
def sign_with_hmac(secret: bytes, payload: bytes) -> str:
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def verify_with_hmac(secret: bytes, payload: bytes, sig_hex: str) -> bool:
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_hex)


# Public API
def sign_metadata(
    metadata: KernelMetadata,
    privkey: Optional[bytes] = None,
    hmac_secret: Optional[bytes] = None,
) -> KernelMetadata:
    payload = metadata.payload()
    if CRYPTO_ED25519_AVAILABLE and privkey:
        sig = sign_with_ed25519(privkey, payload)
        return KernelMetadata(**{**asdict(metadata), "signature": sig})
    elif hmac_secret:
        sig = sign_with_hmac(hmac_secret, payload)
        return KernelMetadata(**{**asdict(metadata), "signature": sig})
    else:
        raise RuntimeError("No signing method available. Provide Ed25519 privkey (preferred) or HMAC secret.")


def verify_metadata(
    metadata: KernelMetadata,
    pubkey: Optional[bytes] = None,
    hmac_secret: Optional[bytes] = None,
) -> bool:
    if not metadata.signature:
        return False
    payload = metadata.payload()
    if CRYPTO_ED25519_AVAILABLE and pubkey:
        return verify_with_ed25519(pubkey, payload, metadata.signature)
    elif hmac_secret:
        return verify_with_hmac(hmac_secret, payload, metadata.signature)
    else:
        raise RuntimeError("No verification method available. Provide Ed25519 pubkey or HMAC secret.")
