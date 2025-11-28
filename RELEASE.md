# Release Process

## Gold Release Checklist
- [ ] All manifests verified (Ed25519) against production pubkey
- [ ] Kernel attestation enforced at boot
- [ ] Composition proof generated for flagship pipeline
- [ ] Adversarial battery green (nightly + PR)
- [ ] CI gates: pre-commit, bandit, safety, mypy
- [ ] SBOM generated and archived
- [ ] Governance sign-offs collected

## Steps
1. Run full test suite: `pytest -q`
2. Verify registry: `python -m src.registry.cli --dir deployment/manifests --pubkey keys/ed25519_pub.pem --revocations logs/revocations.jsonl`
3. Tag and release: `git tag -a vX.Y.Z -m "Gold" && git push --tags`
4. Archive artifacts: SBOM, coverage, proofs, revocations
