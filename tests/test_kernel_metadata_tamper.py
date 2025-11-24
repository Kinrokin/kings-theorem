# tests/test_kernel_metadata_tamper.py
import json
from src.manifest.signature import sign_manifest
from src.orchestrator.verify_kernels import verify_kernel_metadata_list
from src.manifest.signature import CRYPTO_ED_AVAILABLE

def test_kernel_metadata_hmac_flow():
    # dev HMAC flow
    secret = b"dev-hmac-kernel"
    kernel_manifest = {
        "kernel_id": "arbiter-01",
        "type": "Arbiter",
        "veto_power": 10,
        "warrant": 0.99,
        "image_digest": "sha256:deadbeef"
    }
    signed = sign_manifest(kernel_manifest, hmac_secret=secret)
    results = verify_kernel_metadata_list([signed], hmac_secret=secret)
    assert results["arbiter-01"]["ok"]

    # tamper veto_power
    tampered = dict(signed)
    tampered["veto_power"] = 1000
    results2 = verify_kernel_metadata_list([tampered], hmac_secret=secret)
    assert not results2["arbiter-01"]["ok"]

def test_kernel_metadata_ed25519_skip_or_run():
    if not CRYPTO_ED_AVAILABLE:
        import pytest
        pytest.skip("cryptography not installed; skipping Ed25519 kernel test")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub = priv.public_key()
    pub_pem = pub.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

    kernel_manifest = {
        "kernel_id": "arbiter-ed",
        "type": "Arbiter",
        "veto_power": 10,
        "warrant": 0.99,
        "image_digest": "sha256:feedface"
    }
    signed = sign_manifest(kernel_manifest, privkey_pem=priv_pem)
    results = verify_kernel_metadata_list([signed], pubkey_pem=pub_pem)
    assert results["arbiter-ed"]["ok"]

    tampered = dict(signed)
    tampered["image_digest"] = "sha256:bad"
    results2 = verify_kernel_metadata_list([tampered], pubkey_pem=pub_pem)
    assert not results2["arbiter-ed"]["ok"]
