# src/manifest/cli.py
from __future__ import annotations
import argparse
import sys
import json
import os
from typing import Optional
from src.manifest.signature import sign_manifest, verify_manifest, CRYPTO_ED_AVAILABLE

def load_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def cmd_sign(args):
    manifest = json.load(open(args.input, "r", encoding="utf-8"))
    if args.privkey:
        priv = load_bytes(args.privkey)
        signed = sign_manifest(manifest, privkey_pem=priv)
    elif args.hmac_secret:
        secret = args.hmac_secret.encode("utf-8")
        signed = sign_manifest(manifest, hmac_secret=secret)
    else:
        print("Error: provide --privkey <path> (ed25519 PEM) or --hmac-secret <secret>", file=sys.stderr)
        sys.exit(2)
    json.dump(signed, open(args.output, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Wrote signed manifest to {args.output}")

def cmd_verify(args):
    manifest = json.load(open(args.input, "r", encoding="utf-8"))
    if args.pubkey:
        pub = load_bytes(args.pubkey)
        ok, reason = verify_manifest(manifest, pubkey_pem=pub)
    elif args.hmac_secret:
        secret = args.hmac_secret.encode("utf-8")
        ok, reason = verify_manifest(manifest, hmac_secret=secret)
    else:
        print("Error: provide --pubkey <path> (ed25519 PEM) or --hmac-secret <secret>", file=sys.stderr)
        sys.exit(2)
    if ok:
        print("OK:", reason)
        return 0
    else:
        print("FAIL:", reason)
        return 3

def build_parser():
    p = argparse.ArgumentParser("kt-manifest")
    sp = p.add_subparsers(dest="cmd")
    ssign = sp.add_parser("sign", help="Sign a manifest (ed25519 PEM or hmac secret)")
    ssign.add_argument("--input", "-i", required=True)
    ssign.add_argument("--output", "-o", required=True)
    ssign.add_argument("--privkey", help="PEM file containing Ed25519 private key")
    ssign.add_argument("--hmac-secret", help="HMAC secret (dev only)", dest="hmac_secret")
    ssign.set_defaults(func=cmd_sign)

    sver = sp.add_parser("verify", help="Verify a signed manifest")
    sver.add_argument("--input", "-i", required=True)
    sver.add_argument("--pubkey", help="PEM file containing Ed25519 public key")
    sver.add_argument("--hmac-secret", help="HMAC secret (dev only)", dest="hmac_secret")
    sver.set_defaults(func=cmd_verify)
    return p

def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
