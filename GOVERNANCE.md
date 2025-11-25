# Governance

Code Owners: define reviewers for security-critical paths (manifests, kernels, proofs).
Approval Matrix: at least 1 security approver + 1 maintainer for releases.
Incident Response: security@kings-theorem.org (triage in 24h), emergency Slack channel.
Revocation Authority: Security owner may issue EvidenceID revocation via `scripts/revoke_manifest.py`.
Branch Protection: `main` requires CI pass, signed commits, no force-push.

## Release Gate
Signed manifests only (Ed25519), kernel attestation enforced.
Composition proofs generated and checked.
Adversarial battery passing.
SBOM archived (pip-licenses JSON).
# Governance and Usage Notes

This repository is governed internally. Key points:

- Ownership: Robert King is the project owner and primary maintainer.
- License: Proprietary. Usage must follow project governance and approval.
- Secrets: Never commit keys, logs, `.env`, or large model artifacts. These directories are excluded via `.gitignore`.
- Contributions: All external contributions must be reviewed and approved by project owners before merging.

If you need a formal license, contact the project owner to approve and add the license file.
