import base64
import tempfile
from pathlib import Path

from src.governance.decision_broker import DecisionBroker
from src.ledger.integrity_ledger import IntegrityLedger
from src.utils.crypto import generate_keypair


def test_finalize_token_expired():
    td = Path(tempfile.mkdtemp())
    keys_dir = td / "keys"
    keys_dir.mkdir()
    store_dir = td / "store"
    store_dir.mkdir()

    generate_keypair("k1", key_dir=str(keys_dir))
    generate_keypair("k2", key_dir=str(keys_dir))

    ledger = IntegrityLedger(store_dir=str(store_dir), keys_dir=str(keys_dir))
    # Force short TTL so token expires immediately
    ledger.ttl_sec = 0

    broker = DecisionBroker(ledger=ledger)
    governance_result = {"decision": "HALT", "risk_score": 0.9}
    proposal = {"action": "TEST_ACTION"}

    resp = broker.process_request(governance_result, proposal)
    token = resp["token"]

    # sign with valid keys
    from cryptography.hazmat.primitives import serialization

    with open(keys_dir / "k1.pem", "rb") as f:
        priv1 = serialization.load_pem_private_key(f.read(), password=None)
    with open(keys_dir / "k2.pem", "rb") as f:
        priv2 = serialization.load_pem_private_key(f.read(), password=None)

    sig1 = base64.b64encode(priv1.sign(token.encode())).decode("utf-8")
    sig2 = base64.b64encode(priv2.sign(token.encode())).decode("utf-8")
    signatures = [{"key_id": "k1.pub", "signature": sig1}, {"key_id": "k2.pub", "signature": sig2}]

    fin = broker.finalize_with_signatures(token, signatures, rationale="HUMAN_OK")
    assert fin["status"] == "ERROR"


def test_chain_divergence_detected():
    td = Path(tempfile.mkdtemp())
    keys_dir = td / "keys"
    keys_dir.mkdir()
    store_dir = td / "store"
    store_dir.mkdir()

    generate_keypair("k1", key_dir=str(keys_dir))
    generate_keypair("k2", key_dir=str(keys_dir))

    ledger = IntegrityLedger(store_dir=str(store_dir), keys_dir=str(keys_dir))
    broker = DecisionBroker(ledger=ledger)
    governance_result = {"decision": "HALT", "risk_score": 0.9}
    proposal = {"action": "TEST_ACTION"}

    resp = broker.process_request(governance_result, proposal)
    token = resp["token"]

    # Simulate tail moving (chain divergence)
    ledger.last_hash = "deadbeef" * 8

    from cryptography.hazmat.primitives import serialization

    with open(keys_dir / "k1.pem", "rb") as f:
        priv1 = serialization.load_pem_private_key(f.read(), password=None)
    with open(keys_dir / "k2.pem", "rb") as f:
        priv2 = serialization.load_pem_private_key(f.read(), password=None)

    sig1 = base64.b64encode(priv1.sign(token.encode())).decode("utf-8")
    sig2 = base64.b64encode(priv2.sign(token.encode())).decode("utf-8")
    signatures = [{"key_id": "k1.pub", "signature": sig1}, {"key_id": "k2.pub", "signature": sig2}]

    fin = broker.finalize_with_signatures(token, signatures, rationale="HUMAN_OK")
    assert fin["status"] == "ERROR"
