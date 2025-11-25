from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

from src.manifest.signature import sign_manifest


def iter_manifests(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.json"):
        # Skip SBOM and coverage and other generated reports
        if p.name in {"sbom.json", "coverage.json"}:
            continue
        yield p


def rotate_all_manifests(new_privkey_pem: bytes, manifest_dir: Path) -> None:
    for mf in iter_manifests(manifest_dir):
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            continue
        data.pop("signature", None)
        data.pop("content_hash", None)
        data.pop("signed_by", None)
        signed = sign_manifest(data, privkey_pem=new_privkey_pem)
        mf.write_text(json.dumps(signed, indent=2), encoding="utf-8")
        print(f"Re-signed {mf}")


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Re-sign all JSON manifests with a new Ed25519 private key")
    ap.add_argument("--privkey", required=True, help="Path to new Ed25519 private key (PEM)")
    ap.add_argument("--dir", default="manifests", help="Directory containing JSON manifests")
    args = ap.parse_args()

    priv_p = Path(args.privkey)
    if not priv_p.exists():
        raise SystemExit(f"Private key not found: {priv_p}")
    with priv_p.open("rb") as f:
        priv = f.read()

    manifest_dir = Path(args.dir)
    if not manifest_dir.exists():
        raise SystemExit(f"Manifest directory not found: {manifest_dir}")

    rotate_all_manifests(priv, manifest_dir)


if __name__ == "__main__":
    main()
