# Audit Artifacts

- `logs/revocations.jsonl`: Append-only revocation ledger
- `docs/PHASE_4_COMPLETION.md`: Phase 4 security completion report
- `sbom.json`: Software Bill of Materials (generated in CI)
- Sample manifests: `deployment/manifest.json`

## Verification Commands
- Verify manifests (with revocation):
  `python -m src.registry.cli --dir deployment --pubkey keys/ed25519_pub.pem --revocations logs/revocations.jsonl`

- Check revocation chain:
  Python: `from src.registry.ledger import RevocationLedger; RevocationLedger().verify_chain()`
