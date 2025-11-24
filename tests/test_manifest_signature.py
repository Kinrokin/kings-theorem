# tests/test_manifest_signature.py
import os
import json
from src.manifest.signature import sign_manifest, verify_manifest, CRYPTO_ED_AVAILABLE

def test_manifest_sign_and_verify_hmac():
    secret = b"dev-test-hmac-secret"
    manifest = {
        "evidence_id": "EVID-0001",
        "artifact": "edu_json",
        "version": "1.0",
        "payload": {"q": "What is KT?"}
    }
    signed = sign_manifest(manifest, hmac_secret=secret)
    ok, reason = verify_manifest(signed, hmac_secret=secret)
    assert ok, f"expected verify ok but got {reason}"

    # mutate content -> verify fails
    mutated = dict(signed)
    mutated["payload"] = {"q": "Tampered"}
    ok2, reason2 = verify_manifest(mutated, hmac_secret=secret)
    assert not ok2 and reason2 == "content_hash_mismatch"

def test_manifest_sign_ed25519_skip_or_run():
    # If cryptography present, test Ed25519 path; otherwise skip
    if not CRYPTO_ED_AVAILABLE:
        import pytest
        pytest.skip("cryptography not installed; skipping Ed25519 test")
    # generate a keypair in-memory (cryptography must be available)
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

    manifest = {"evidence_id":"EVID-ED-1", "artifact":"proof", "payload": {"x":1}}
    signed = sign_manifest(manifest, privkey_pem=priv_pem)
    ok, reason = verify_manifest(signed, pubkey_pem=pub_pem)
    assert ok
    # tamper
    tampered = dict(signed)
    tampered["artifact"] = "bad"
    ok2, reason2 = verify_manifest(tampered, pubkey_pem=pub_pem)
    assert not ok2
