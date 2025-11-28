from __future__ import annotations

from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except Exception:
    raise SystemExit("cryptography is required: pip install cryptography")


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Generate Ed25519 key pair (PEM) into keys/ directory")
    ap.add_argument("--name", default="ed25519", help="Base filename prefix (default: ed25519)")
    ap.add_argument("--out", default="keys", help="Output directory (default: keys)")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    priv_path = out / f"{args.name}_priv.pem"
    pub_path = out / f"{args.name}_pub.pem"

    key = Ed25519PrivateKey.generate()
    pub = key.public_key()

    priv_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path.write_bytes(priv_pem)
    pub_path.write_bytes(pub_pem)
    print(f"Wrote private key: {priv_path}")
    print(f"Wrote public key : {pub_path}")


if __name__ == "__main__":
    main()
