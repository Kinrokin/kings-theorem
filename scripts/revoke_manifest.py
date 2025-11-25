"""
CLI to append a revocation event to the revocation ledger.

Usage (PowerShell):
  python -m scripts.revoke_manifest --id EVID-123 --reason compromised --signed-by operator.pub --ledger logs/revocations.jsonl
"""
from __future__ import annotations
import argparse
import sys
from src.registry.ledger import RevocationLedger


def build_parser():
    p = argparse.ArgumentParser("kt-revoke")
    p.add_argument("--id", required=True, help="Evidence/Manifest ID to revoke")
    p.add_argument("--reason", required=True, help="Reason for revocation")
    p.add_argument("--signed-by", required=True, help="Signer identity (e.g., key id or operator)")
    p.add_argument("--ledger", default="logs/revocations.jsonl", help="Path to revocation ledger JSONL")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    ledger = RevocationLedger(args.ledger)
    evt = ledger.revoke(args.id, args.reason, args.signed_by)
    print(f"Revoked {evt.evidence_id}: {evt.reason} (hash={evt.event_hash[:12]}..., prev={evt.prev_hash[:12]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
