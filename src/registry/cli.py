# src/registry/cli.py
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Optional

from src.manifest.signature import verify_manifest
from src.metrics.metrics import record_manifest_verification
from src.registry.ledger import RevocationLedger

logger = logging.getLogger(__name__)


def verify_dir(
    path: str,
    pubkey_path: Optional[str] = None,
    hmac_secret: Optional[str] = None,
    revocations_path: Optional[str] = None,
) -> int:
    pubkey = None
    if pubkey_path:
        pubkey = open(pubkey_path, "rb").read()
    files = []
    for root, _, fnames in os.walk(path):
        for fn in fnames:
            if fn.lower().endswith(".json"):
                files.append(os.path.join(root, fn))
    if not files:
        print("No JSON files found under", path)
        return 1
    failures = []
    rev_ledger = None
    # Allow env var override for revocations file
    rev_path = revocations_path or os.getenv("KT_REVOCATIONS_PATH")
    if rev_path:
        rev_ledger = RevocationLedger(rev_path)
    for f in files:
        try:
            m = json.load(open(f, "r", encoding="utf-8"))
        except Exception as e:
            logger.exception("Failed to read manifest %s", f)
            print(f"ERR reading {f}: {e}")
            failures.append((f, "read_error"))
            continue
        if pubkey:
            ok, reason = verify_manifest(m, pubkey_pem=pubkey)
        elif hmac_secret:
            ok, reason = verify_manifest(m, hmac_secret=hmac_secret.encode("utf-8"))
        else:
            print(
                "Error: supply --pubkey or --hmac-secret for registry verification",
                file=sys.stderr,
            )
            return 2

        # Optional: revocation check
        if ok and rev_ledger is not None:
            # try multiple id keys
            mid = m.get("evidence_id") or m.get("manifest_id") or m.get("id")
            if mid and rev_ledger.is_revoked(str(mid)):
                ok = False
                reason = f"REVOKED:{mid}"
        if not ok:
            print(f"FAIL {f}: {reason}")
            failures.append((f, reason))
            try:
                record_manifest_verification(False)
            except Exception:
                logger.exception("Failed to record manifest verification failure for %s", f)
        else:
            print(f"OK   {f}: {reason}")
            try:
                record_manifest_verification(True)
            except Exception:
                logger.exception("Failed to record manifest verification success for %s", f)
    if failures:
        print(f"Verification failed for {len(failures)} files")
        return 3
    print("All manifests verified.")
    return 0


def build_parser():
    p = argparse.ArgumentParser("kt-registry")
    p.add_argument("--dir", "-d", required=True, help="Directory containing manifests (json)")
    p.add_argument("--pubkey", help="Public key PEM for Ed25519 verification")
    p.add_argument("--hmac-secret", help="HMAC secret (dev only)")
    p.add_argument("--revocations", help="Path to JSONL revocation ledger (optional)")
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)
    return verify_dir(
        args.dir,
        pubkey_path=args.pubkey,
        hmac_secret=args.hmac_secret,
        revocations_path=args.revocations,
    )


if __name__ == "__main__":
    sys.exit(main())
