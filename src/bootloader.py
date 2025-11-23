"""
Self-Verification Bootloader

Runs before `main.py`. Computes SHA256 of all files in `src/` and compares
against `deployment/manifest.json`. On mismatch, halts the system.
If all files match, imports and launches `src.main.run_system()`.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from typing import Dict
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key

logger = logging.getLogger(__name__)


def compute_hashes(root: str) -> Dict[str, str]:
    hashes = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            # skip compiled python files
            if fn.endswith(('.pyc', '.pyo')):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            with open(full, 'rb') as f:
                data = f.read()
            h = hashlib.sha256(data).hexdigest()
            hashes[rel] = h
    return hashes


def load_manifest(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Manifest not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    # Expect manifest to have a 'files' mapping and a signature
    files = manifest.get('files')
    if not isinstance(files, dict):
        raise ValueError('Manifest missing "files" mapping')
    return manifest


def verify_signature(manifest: dict, pubkey_path: str) -> bool:
    sig_b64 = manifest.get('signature')
    if not sig_b64:
        logger.error('[BOOTLOADER] Manifest missing signature')
        return False
    signature = base64.b64decode(sig_b64)
    # Prepare payload (manifest without signature)
    manifest_copy = {k: v for k, v in manifest.items() if k != 'signature'}
    payload = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':')).encode('utf-8')

    if not os.path.exists(pubkey_path):
        logger.error('[BOOTLOADER] Public key not found: %s', pubkey_path)
        return False

    with open(pubkey_path, 'rb') as f:
        key_data = f.read()

    pubkey = load_pem_public_key(key_data)
    try:
        # Try RSA-style verification
        pubkey.verify(
            signature,
            payload,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except TypeError:
        # Likely an Ed25519 key (single-arg verify)
        try:
            pubkey.verify(signature, payload)
            return True
        except Exception:
            logger.exception('[BOOTLOADER] Signature verification failed (Ed25519)')
            return False
    except Exception:
        logger.exception('[BOOTLOADER] Signature verification failed (RSA)')
        return False


def verify(src_root: str, manifest_path: str) -> bool:
    logger.info("[BOOTLOADER] Computing source hashes for '%s'...", src_root)
    current = compute_hashes(src_root)
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.exception("[BOOTLOADER] Failed to load manifest: %s", e)
        return False

    # Verify manifest signature first
    pubkey_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keys', 'operator.pub'))
    try:
        sig_ok = verify_signature(manifest, pubkey_path)
    except Exception as e:
        logger.exception("[BOOTLOADER] Signature verification raised exception: %s", e)
        sig_ok = False

    if not sig_ok:
        logger.error("[BOOTLOADER] Manifest signature verification failed. Aborting.")
        return False

    expected = manifest.get('files', {})

    # Compare only files recorded in manifest
    mismatch = []
    for rel, exp_hash in expected.items():
        cur_hash = current.get(rel)
        if cur_hash != exp_hash:
            mismatch.append((rel, exp_hash, cur_hash))

    if mismatch:
        logger.error("[BOOTLOADER] Integrity violation detected. Mismatches:")
        for rel, exp, cur in mismatch:
            logger.error("  - %s: expected=%s current=%s", rel, exp, cur)
        return False

    logger.info("[BOOTLOADER] Integrity verified: src/ matches manifest and signature is valid.")
    return True


def main():
    # ensure logger is configured
    from src.logging_config import setup_logging

    setup_logging()
    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'deployment', 'manifest.json'))

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

        mod = importlib.import_module('src.main')
        if hasattr(mod, 'run_system'):
            mod.run_system()
        else:
            logger.error("[BOOTLOADER] src.main has no run_system() entrypoint")
            sys.exit(3)
    except Exception:
        logger.exception("[BOOTLOADER] Failed to launch main")
        sys.exit(4)


if __name__ == '__main__':
    main()
