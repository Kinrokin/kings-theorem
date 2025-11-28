"""
Self-Verification Bootloader

Runs before `main.py`. Computes SHA256 of all files in `src/` and compares
against `deployment/manifest.json`. On mismatch, halts the system.
If all files match, imports and launches `src.main.run_system()`.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sys
from typing import Any, Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

logger = logging.getLogger(__name__)


def compute_hashes(root: str) -> Dict[str, str]:
    hashes = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            # skip compiled python files
            if fn.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            with open(full, "rb") as f:
                data = f.read()
            h = hashlib.sha256(data).hexdigest()
            hashes[rel] = h
    return hashes


def load_manifest(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Manifest not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    # Two schema types supported:
    # 1) Build manifest with `files` mapping + `signature`
    # 2) Serving manifest with `content_hash` + `_signature`
    if not (isinstance(manifest.get("files"), dict) or manifest.get("content_hash")):
        raise ValueError('Manifest missing required fields: expected "files" or "content_hash"')
    return manifest


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_signature(manifest: dict, pubkey_path: str) -> bool:
    # Support both signature layouts
    sig_b64 = manifest.get("signature")
    sig_block = manifest.get("_signature")
    algorithm = None
    if sig_block and isinstance(sig_block, dict):
        sig_hex = sig_block.get("signature")
        algorithm = (sig_block.get("algorithm") or "").lower()
        if not sig_hex:
            logger.error("[BOOTLOADER] Serving manifest missing _signature.signature")
            return False
        try:
            signature = bytes.fromhex(sig_hex)
        except ValueError:
            logger.error("[BOOTLOADER] Invalid hex in serving signature")
            return False
        # Payload excludes the _signature block
        payload = _canonical_json({k: v for k, v in manifest.items() if k != "_signature"})
    else:
        if not sig_b64:
            logger.error("[BOOTLOADER] Manifest missing signature")
            return False
        try:
            signature = base64.b64decode(sig_b64)
        except Exception:
            logger.error("[BOOTLOADER] Signature is not valid base64")
            return False
        payload = _canonical_json({k: v for k, v in manifest.items() if k != "signature"})

    if not os.path.exists(pubkey_path):
        logger.error("[BOOTLOADER] Public key not found: %s", pubkey_path)
        return False

    with open(pubkey_path, "rb") as f:
        key_data = f.read()

    pubkey = load_pem_public_key(key_data)
    try:
        if algorithm == "ed25519":
            pubkey.verify(signature, payload)
            return True
        # Default: attempt RSA PKCS1v15 + SHA256; also handles RSA keys when algorithm unspecified
        pubkey.verify(signature, payload, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        logger.exception("[BOOTLOADER] Signature verification failed")
        return False


def verify(src_root: str, manifest_path: str) -> bool:
    logger.info("[BOOTLOADER] Computing source hashes for '%s'...", src_root)
    current = compute_hashes(src_root)
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.exception("[BOOTLOADER] Failed to load manifest: %s", e)
        return False

    # Dev overrides
    dev_skip_sig = (
        os.environ.get("KT_BOOTLOADER_DEV", "0") == "1" or os.environ.get("KT_BOOTLOADER_SKIP_SIG", "0") == "1"
    )
    dev_skip_hash = os.environ.get("KT_BOOTLOADER_SKIP_HASH", "0") == "1"

    # Verify manifest signature first (unless dev override)
    pubkey_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "keys", "operator.pub"))
    if dev_skip_sig:
        logger.warning("[BOOTLOADER] DEV MODE: Skipping manifest signature verification.")
        sig_ok = True
    else:
        try:
            sig_ok = verify_signature(manifest, pubkey_path)
        except Exception as e:
            logger.exception("[BOOTLOADER] Signature verification raised exception: %s", e)
            sig_ok = False

        if not sig_ok:
            print("[CRITICAL] SECURITY VIOLATION: MANIFEST TAMPERED")
            logger.critical("[BOOTLOADER] Manifest signature verification failed. Aborting.")
            sys.exit(1)

    files_map = manifest.get("files")
    if isinstance(files_map, dict):
        if dev_skip_hash:
            logger.warning("[BOOTLOADER] DEV MODE: Skipping per-file hash checks.")
        else:
            mismatch = []
            for rel, exp_hash in files_map.items():
                cur_hash = current.get(rel)
                if cur_hash != exp_hash:
                    mismatch.append((rel, exp_hash, cur_hash))
            if mismatch:
                logger.error("[BOOTLOADER] Integrity violation detected. Mismatches:")
                for rel, exp, cur in mismatch:
                    logger.error("  - %s: expected=%s current=%s", rel, exp, cur)
                return False
    else:
        # Serving manifest schema: verify composite content hash over src tree
        if dev_skip_hash:
            logger.warning("[BOOTLOADER] DEV MODE: Skipping content hash validation.")
        else:
            composite = hashlib.sha256(_canonical_json(current)).hexdigest()
            expected_ch = manifest.get("content_hash")
            if composite != expected_ch:
                logger.error("[BOOTLOADER] Content hash mismatch: expected=%s current=%s", expected_ch, composite)
                return False

    logger.info("[BOOTLOADER] Integrity verified: src/ matches manifest and signature is valid.")
    return True


def main():
    # ensure logger is configured
    from src.logging_config import setup_logging

    setup_logging()
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "deployment", "manifest.json"))

    try:
        ok = verify(src_root, manifest_path)
    except Exception as e:
        logger.exception("[BOOTLOADER] Verification raised an exception: %s", e)
        ok = False

    if not ok:
        logger.critical("[BOOTLOADER] HALT: Integrity Violation. System will not start.")
        sys.exit(2)

    # Launch main
    try:
        import importlib

        mod = importlib.import_module("src.main")
        if hasattr(mod, "run_system"):
            mod.run_system()
        else:
            logger.error("[BOOTLOADER] src.main has no run_system() entrypoint")
            sys.exit(3)
    except Exception:
        logger.exception("[BOOTLOADER] Failed to launch main")
        sys.exit(4)


if __name__ == "__main__":
    main()
