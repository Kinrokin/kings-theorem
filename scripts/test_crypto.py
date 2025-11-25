"""Test cryptographic signing primitives."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Test imports
from src.crypto import generate_keypair, save_keypair, sign_json, verify_json  # noqa: E402


def test_generate_keypair() -> None:
    """Test keypair generation."""
    keypair = generate_keypair("test")
    assert keypair.key_id == "test"
    assert keypair.private_key is not None
    assert keypair.public_key is not None
    print("✅ Keypair generation successful")


def test_sign_verify_bytes() -> None:
    """Test byte-level signing and verification."""
    # Generate test keypair and save before signing
    keypair = generate_keypair("test_bytes")
    temp_dir = Path(__file__).resolve().parents[1] / "keys" / ".test"
    temp_dir.mkdir(parents=True, exist_ok=True)
    save_keypair(keypair, temp_dir)

    # Sign some bytes (must load from saved location)
    test_data = b"This is a test message for signing."
    # Pass base_dir to load from .test subdirectory
    from src.crypto.keys import load_private_key

    private_key = load_private_key("test_bytes", base_dir=temp_dir)
    from datetime import datetime, timezone

    from src.crypto.signing import Signature

    signature_bytes = private_key.sign(test_data)
    signature = Signature(
        signature_bytes=signature_bytes,
        key_id="test_bytes",
        timestamp=datetime.now(timezone.utc).isoformat(),
        algorithm="ed25519",
    )

    # Verify signature (must load public key from .test)
    from src.crypto.keys import load_public_key

    public_key = load_public_key("test_bytes", base_dir=temp_dir)
    from cryptography.exceptions import InvalidSignature

    try:
        public_key.verify(signature.signature_bytes, test_data)
        is_valid = True
    except InvalidSignature:
        is_valid = False

    assert is_valid, "Signature verification failed"
    print("✅ Byte signing/verification successful")

    # Test tampered data
    tampered_data = b"This is a TAMPERED message for signing."
    try:
        public_key.verify(signature.signature_bytes, tampered_data)
        is_valid_tampered = True
    except InvalidSignature:
        is_valid_tampered = False

    assert not is_valid_tampered, "Tampered data incorrectly verified"
    print("✅ Tamper detection successful")

    # Cleanup
    (temp_dir / "test_bytes.pem").unlink()
    (temp_dir / "test_bytes.pub").unlink()


def test_sign_verify_json() -> None:
    """Test JSON signing and verification."""
    # Generate test keypair and save
    keypair = generate_keypair("test_json")
    temp_dir = Path(__file__).resolve().parents[1] / "keys" / ".test"
    temp_dir.mkdir(parents=True, exist_ok=True)
    save_keypair(keypair, temp_dir)

    # Sign JSON object manually (sign_json expects key in default location)
    import hashlib
    from datetime import datetime, timezone

    from src.crypto.signing import Signature

    test_data = {
        "model": "Teacher_v45",
        "risk_budget": 0.05,
        "kernel": "RiskActionKernel",
        "timestamp": "2025-06-15T12:00:00Z",
    }

    # Compute canonical hash
    canonical_bytes = json.dumps(test_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    data_hash = hashlib.sha256(canonical_bytes).digest()

    # Sign with private key from .test
    from src.crypto.keys import load_private_key

    private_key = load_private_key("test_json", base_dir=temp_dir)
    signature_bytes = private_key.sign(data_hash)
    signature = Signature(
        signature_bytes=signature_bytes,
        key_id="test_json",
        timestamp=datetime.now(timezone.utc).isoformat(),
        algorithm="ed25519",
    )

    # Embed signature
    signed_data = test_data.copy()
    signed_data["_signature"] = signature.to_dict()

    # Verify signature exists
    assert "_signature" in signed_data
    assert signed_data["_signature"]["key_id"] == "test_json"
    assert signed_data["_signature"]["algorithm"] == "ed25519"
    print("✅ JSON signing successful")

    # Verify signature manually
    from cryptography.exceptions import InvalidSignature

    from src.crypto.keys import load_public_key

    signature_dict = signed_data["_signature"]
    signature_obj = Signature.from_dict(signature_dict)
    original_data = {k: v for k, v in signed_data.items() if k != "_signature"}
    canonical_bytes = json.dumps(original_data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    data_hash = hashlib.sha256(canonical_bytes).digest()

    public_key = load_public_key("test_json", base_dir=temp_dir)
    try:
        public_key.verify(signature_obj.signature_bytes, data_hash)
        is_valid = True
    except InvalidSignature:
        is_valid = False

    assert is_valid, "JSON signature verification failed"
    print("✅ JSON verification successful")

    # Test tampered JSON
    tampered_data = signed_data.copy()
    tampered_data["risk_budget"] = 0.99  # Attacker tries to change budget
    tampered_original = {k: v for k, v in tampered_data.items() if k != "_signature"}
    tampered_canonical = json.dumps(tampered_original, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tampered_hash = hashlib.sha256(tampered_canonical).digest()

    try:
        public_key.verify(signature_obj.signature_bytes, tampered_hash)
        is_valid_tampered = True
    except InvalidSignature:
        is_valid_tampered = False

    assert not is_valid_tampered, "Tampered JSON incorrectly verified"
    print("✅ JSON tamper detection successful")

    # Cleanup
    (temp_dir / "test_json.pem").unlink()
    (temp_dir / "test_json.pub").unlink()


def test_manifest_signing_workflow() -> None:
    """Test realistic manifest signing workflow."""
    # Load actual operator key (generated by keygen.py)
    from src.crypto import load_private_key, load_public_key

    try:
        _ = load_private_key("operator")
        _ = load_public_key("operator")
        print("✅ Operator keypair loaded successfully")
    except FileNotFoundError:
        print("⚠️  Run 'python scripts/keygen.py operator' first")
        return

    # Simulate manifest
    manifest = {
        "version": "1.0.0",
        "models": {
            "teacher": {"class": "Teacher_v45", "risk_profile": "cautious"},
            "student": {"class": "Student_v42", "risk_profile": "balanced"},
            "arbiter": {"class": "Arbiter_v47", "risk_profile": "strict"},
        },
        "risk_budget": {"catastrophic_max": 0.05, "min_samples": 512},
    }

    # Sign with operator key
    signed_manifest = sign_json(manifest, "operator")
    print("✅ Manifest signed with operator key")

    # Verify signature
    is_valid = verify_json(signed_manifest)
    assert is_valid, "Manifest signature verification failed"
    print("✅ Manifest signature verified")

    # Pretty print signed manifest
    print("\n📄 Signed Manifest:")
    print(json.dumps(signed_manifest, indent=2))


if __name__ == "__main__":
    print("🔐 Testing cryptographic signing infrastructure...\n")
    test_generate_keypair()
    test_sign_verify_bytes()
    test_sign_verify_json()
    test_manifest_signing_workflow()
    print("\n✅ All cryptographic tests passed!")
