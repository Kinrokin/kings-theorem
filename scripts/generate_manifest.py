"""
Generate a deployment/manifest.json containing SHA256 hashes of files under src/
and sign the manifest using the operator private key at `keys/operator.pem`.

Usage:
    python scripts/generate_manifest.py

This will write `deployment/manifest.json` with a `files` mapping and a base64 signature.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key


def compute_hashes(root: str) -> Dict[str, str]:
    hashes_map = {}
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(('.pyc', '.pyo')):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace('\\', '/')
            with open(full, 'rb') as f:
                data = f.read()
            h = hashlib.sha256(data).hexdigest()
            hashes_map[rel] = h
    return hashes_map


def load_private_key(path: str):
    with open(path, 'rb') as f:
        key_data = f.read()
    # If the key is password protected, the script would need a passphrase.
    return load_pem_private_key(key_data, password=None)


def sign_manifest(manifest_obj: dict, privkey) -> str:
    # Serialize canonical JSON
    payload = json.dumps(manifest_obj, sort_keys=True, separators=(',', ':')).encode('utf-8')
    # Support multiple key types (RSA and Ed25519).
    try:
        # Attempt RSA-style signature (cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey)
        signature = privkey.sign(
            payload,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except TypeError:
        # Likely an Ed25519/Ed448 key which signs with a single-argument API
        signature = privkey.sign(payload)
    return base64.b64encode(signature).decode('utf-8')


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    src_root = os.path.join(repo_root, 'src')
    keys_dir = os.path.join(repo_root, 'keys')
    privkey_path = os.path.join(keys_dir, 'operator.pem')
    out_path = os.path.join(repo_root, 'deployment', 'manifest.json')

    if not os.path.isdir(src_root):
        print('src/ not found', file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(privkey_path):
        print('Private key not found at', privkey_path, file=sys.stderr)
        sys.exit(1)

    hashes_map = compute_hashes(src_root)

    manifest = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'generator': 'scripts/generate_manifest.py',
        'files': hashes_map,
    }

    privkey = load_private_key(privkey_path)
    signature = sign_manifest(manifest, privkey)
    manifest['signature'] = signature

    # Ensure deployment directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print('Wrote manifest to', out_path)


if __name__ == '__main__':
    main()
