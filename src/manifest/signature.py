# src/manifest/signature.py
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("kt.manifest.signature")
logger.setLevel(logging.INFO)

# Try Ed25519 via cryptography if available
try:
    from cryptography.hazmat.primitives import serialization

    CRYPTO_ED_AVAILABLE = True
except Exception:
    CRYPTO_ED_AVAILABLE = False
    logger.debug("cryptography Ed25519 not available; HMAC fallback will be used.")

# ---------- Helpers ----------


def canonical_payload(obj: Dict[str, Any]) -> bytes:
    """
    Deterministic JSON canonicalization used for signing and hashing.
    For production-level canonicalization, consider RFC8785 canonical JSON.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------- Ed25519 helpers (if cryptography available) ----------


def sign_with_ed25519_pem(privkey_pem: bytes, payload: bytes) -> str:
    """
    privkey_pem: PEM-encoded private key (bytes), e.g., from openssl genpkey -algorithm ed25519 -out key.pem
    returns: hex signature
    """
    if not CRYPTO_ED_AVAILABLE:
        raise RuntimeError("Ed25519 not available in this Python environment.")
    priv = serialization.load_pem_private_key(privkey_pem, password=None)
    sig = priv.sign(payload)
    return sig.hex()


def verify_with_ed25519_pem(pubkey_pem: bytes, payload: bytes, sig_hex: str) -> bool:
    if not CRYPTO_ED_AVAILABLE:
        raise RuntimeError("Ed25519 not available in this Python environment.")
    pub = serialization.load_pem_public_key(pubkey_pem)
    try:
        pub.verify(bytes.fromhex(sig_hex), payload)
        return True
    except Exception:
        return False


# ---------- HMAC fallback (dev only) ----------


def sign_with_hmac(secret: bytes, payload: bytes) -> str:
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()


def verify_with_hmac(secret: bytes, payload: bytes, sig_hex: str) -> bool:
    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig_hex)


# ---------- Manifest API ----------


def sign_manifest(
    manifest: Dict[str, Any],
    privkey_pem: Optional[bytes] = None,
    hmac_secret: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    Return a new manifest dict that contains:
      - "content_hash": sha256 of canonical payload of the manifest content (without signature)
      - "signature": hex signature (Ed25519 or HMAC)
      - "signed_by": metadata string ("ed25519" or "hmac")
    The input manifest is NOT modified in-place.
    """
    # Work on a copy excluding any existing signature fields
    payload_obj = {k: v for k, v in manifest.items() if k not in ("signature", "content_hash", "signed_by")}
    payload = canonical_payload(payload_obj)
    content_hash = sha256_hex(payload)

    if CRYPTO_ED_AVAILABLE and privkey_pem is not None:
        sig = sign_with_ed25519_pem(privkey_pem, payload)
        signed = {
            **payload_obj,
            "content_hash": content_hash,
            "signature": sig,
            "signed_by": "ed25519",
        }
        return signed
    elif hmac_secret is not None:
        sig = sign_with_hmac(hmac_secret, payload)
        signed = {
            **payload_obj,
            "content_hash": content_hash,
            "signature": sig,
            "signed_by": "hmac",
        }
        return signed
    else:
        raise RuntimeError("No signing method provided. Supply privkey_pem (ed25519) or hmac_secret (dev).")


def verify_manifest(
    signed_manifest: Dict[str, Any],
    pubkey_pem: Optional[bytes] = None,
    hmac_secret: Optional[bytes] = None,
) -> Tuple[bool, str]:
    """
    Verify both content hash and signature. Returns (ok, reason).
    """
    # Extract canonical payload (original fields)
    signature = signed_manifest.get("signature")
    content_hash = signed_manifest.get("content_hash")
    signed_by = signed_manifest.get("signed_by")

    if not signature or not content_hash or not signed_by:
        return False, "missing_signature_or_hash"

    payload_obj = {k: v for k, v in signed_manifest.items() if k not in ("signature", "content_hash", "signed_by")}
    payload = canonical_payload(payload_obj)
    computed_hash = sha256_hex(payload)
    if computed_hash != content_hash:
        return False, "content_hash_mismatch"

    if signed_by == "ed25519":
        if not CRYPTO_ED_AVAILABLE:
            return False, "ed25519_not_available"
        if pubkey_pem is None:
            return False, "no_pubkey_provided"
        ok = verify_with_ed25519_pem(pubkey_pem, payload, signature)
        return (ok, "ed25519_verify_ok" if ok else "ed25519_verify_fail")
    elif signed_by == "hmac":
        if hmac_secret is None:
            return False, "no_hmac_secret_provided"
        ok = verify_with_hmac(hmac_secret, payload, signature)
        return (ok, "hmac_verify_ok" if ok else "hmac_verify_fail")
    else:
        return False, "unknown_signature_scheme"
