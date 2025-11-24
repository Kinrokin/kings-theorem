import base64
import os
import tempfile
from pathlib import Path

from src.utils.crypto import generate_keypair
from src.utils.multisig import verify_multisig


def test_verify_multisig_success():
    td = Path(tempfile.mkdtemp())
    keys_dir = td / "keys"
    keys_dir.mkdir()

    # generate two keypairs
    generate_keypair("k1", key_dir=str(keys_dir))
    generate_keypair("k2", key_dir=str(keys_dir))

    # load private keys for signing
    from cryptography.hazmat.primitives import serialization

    with open(keys_dir / "k1.pem", "rb") as f:
        priv1 = serialization.load_pem_private_key(f.read(), password=None)
    with open(keys_dir / "k2.pem", "rb") as f:
        priv2 = serialization.load_pem_private_key(f.read(), password=None)

    token = "test-token-123"
    sig1 = base64.b64encode(priv1.sign(token.encode())).decode("utf-8")
    sig2 = base64.b64encode(priv2.sign(token.encode())).decode("utf-8")

    signatures = [
        {"key_id": "k1.pub", "signature": sig1},
        {"key_id": "k2.pub", "signature": sig2},
    ]

    assert verify_multisig(token, signatures, required_count=2, policy_status="FREEZE", keys_dir=str(keys_dir)) is True


def test_verify_multisig_failure_insufficient():
    td = Path(tempfile.mkdtemp())
    keys_dir = td / "keys"
    keys_dir.mkdir()

    generate_keypair("k1", key_dir=str(keys_dir))

    from cryptography.hazmat.primitives import serialization

    with open(keys_dir / "k1.pem", "rb") as f:
        priv1 = serialization.load_pem_private_key(f.read(), password=None)

    token = "test-token-abc"
    sig1 = base64.b64encode(priv1.sign(token.encode())).decode("utf-8")

    signatures = [
        {"key_id": "k1.pub", "signature": sig1},
    ]

    try:
        verify_multisig(token, signatures, required_count=2, policy_status="FREEZE", keys_dir=str(keys_dir))
        assert False, "Expected MultisigPolicyError"
    except Exception:
        # expected
        pass
