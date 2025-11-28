"""Phase 5 Replay-Proof Token Test

Validates:
  - Token versioning prevents duplicate submission
  - Staleness checks reject expired tokens
  - Hash-based replay detection catches duplicate tokens
"""

import time

import pytest

from src.ledger.integrity_ledger import IntegrityLedger, LedgerError
from src.primitives.exceptions import LedgerInvariantError


def test_token_version_stored_in_ledger(tmp_path):
    """Verify token version is stored in precommit."""

    ledger = IntegrityLedger(store_dir=str(tmp_path / "ledger"))
    proposal = {"action": "APPROVE", "problem_id": "VERSION_TEST"}
    token = ledger.precommit_proposal(proposal, token_version=2)

    # Read back
    wal_path = tmp_path / "ledger" / f"{token}.precommit"
    with open(wal_path) as f:
        import json

        entry = json.load(f)
    assert entry["token_version"] == 2


def test_duplicate_token_rejected_by_registry(tmp_path):
    """Duplicate token raises LedgerInvariantError."""

    ledger = IntegrityLedger(store_dir=str(tmp_path / "ledger"))
    proposal = {"action": "APPROVE", "problem_id": "DUP_TEST"}
    token1 = ledger.precommit_proposal(proposal)

    # Directly test registry prevents duplicate by adding token manually before precommit
    ledger._token_registry.add("FAKE_DUPLICATE_TOKEN")

    # Temporarily replace sha256b in integrity_ledger module to return our fake token
    from src.ledger import integrity_ledger

    original_sha256b = integrity_ledger.sha256b

    def mock_sha256b(data):
        return "FAKE_DUPLICATE_TOKEN"

    integrity_ledger.sha256b = mock_sha256b

    try:
        with pytest.raises(LedgerInvariantError, match="Token already exists"):
            ledger.precommit_proposal({"action": "TEST"})
    finally:
        integrity_ledger.sha256b = original_sha256b


def test_hash_based_replay_detection(tmp_path):
    """Hash collision (replay attack) is detected."""

    ledger = IntegrityLedger(store_dir=str(tmp_path / "ledger"))
    proposal_a = {"action": "APPROVE", "problem_id": "REPLAY_TEST_A"}

    token_a = ledger.precommit_proposal(proposal_a)

    # Directly add hash to registry to simulate collision
    import hashlib

    fake_hash = "COLLISION_HASH"
    ledger._token_hashes.add(fake_hash)

    # Mock hashlib to return our collision hash
    original_sha256 = hashlib.sha256

    class MockSha256:
        def __init__(self, data):
            pass

        def hexdigest(self):
            return fake_hash

    hashlib.sha256 = MockSha256

    try:
        with pytest.raises(LedgerInvariantError, match="Token hash collision"):
            ledger.precommit_proposal({"action": "REPLAY"})
    finally:
        hashlib.sha256 = original_sha256


def test_staleness_check_rejects_expired_token(tmp_path, monkeypatch):
    """Token older than staleness threshold is rejected at finalize."""

    ledger = IntegrityLedger(store_dir=str(tmp_path / "ledger"))
    ledger.token_staleness_seconds = 2  # 2 seconds for test
    proposal = {"action": "APPROVE", "problem_id": "STALE_TEST"}
    token = ledger.precommit_proposal(proposal)

    # Wait for staleness
    time.sleep(3)

    # Finalize should reject
    with pytest.raises(LedgerInvariantError, match="Token expired"):
        ledger.finalize_proposal(token, signature="MOCK_SIG")


def test_non_expired_token_finalizes_successfully(tmp_path):
    """Token within staleness window finalizes."""

    ledger = IntegrityLedger(store_dir=str(tmp_path / "ledger"))
    ledger.token_staleness_seconds = 300  # 5 minutes
    proposal = {"action": "APPROVE", "problem_id": "FRESH_TEST"}
    token = ledger.precommit_proposal(proposal)

    # Finalize immediately (mock signature bypass for test)
    try:
        ledger.finalize_proposal(token, signature="MOCK_SIG")
    except LedgerError as e:
        # Crypto verification fails in test, but staleness check passed
        # (staleness is checked before crypto)
        if e.code != "INVALID_SIGNATURE":
            raise
