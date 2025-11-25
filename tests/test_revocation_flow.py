import os
import tempfile
import json
from pathlib import Path

from src.registry.ledger import RevocationLedger
from src.registry.cli import verify_dir


def test_revocation_basic_toggle(tmp_path: Path):
    ledger_path = tmp_path / "revocations.jsonl"
    ledger = RevocationLedger(str(ledger_path))
    assert ledger.verify_chain() is True

    # Initially not revoked
    assert ledger.is_revoked("EVID-1") is False

    # Revoke
    evt = ledger.revoke("EVID-1", reason="compromised", signed_by="ops")
    assert ledger.is_revoked("EVID-1") is True
    assert ledger.verify_chain() is True


def test_registry_cli_respects_revocation(tmp_path: Path):
    # Create manifest dir with one signed-like manifest (we won't verify signature here)
    mdir = tmp_path / "manifests"
    mdir.mkdir()
    manifest = {"evidence_id": "EVID-2", "artifact": "proof", "payload": {}}
    with open(mdir / "m.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    # Create ledger and revoke EVID-2
    ledger_path = tmp_path / "revocations.jsonl"
    ledger = RevocationLedger(str(ledger_path))
    ledger.revoke("EVID-2", reason="test", signed_by="ops")

    # Use HMAC path for verification since no real signature available
    code = verify_dir(str(mdir), hmac_secret="dev-test", revocations_path=str(ledger_path))
    # Should fail because the evidence_id is revoked
    assert code != 0
