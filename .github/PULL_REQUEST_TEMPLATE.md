## Summary

Describe the change and its purpose. Link to any related issues.

## Changes
- [ ] Security: provenance, attestation, revocation
- [ ] Observability: /metrics, counters
- [ ] CI/CD: bandit, safety, mypy, SBOM, pre-commit
- [ ] Tests: unit/integration/adversarial
- [ ] Docs: GOVERNANCE, SECURITY, RELEASE, notices

## Checklist
- [ ] All tests pass locally
- [ ] CI green (bandit, safety, mypy, SBOM)
- [ ] Secret scanning clean (`detect-secrets` baseline updated if needed)
- [ ] No breaking API changes
- [ ] Post-merge actions prepared (announce, env vars, tag)

## Post-merge Actions
- [ ] Announce history rewrite (if applicable) and re-clone steps
- [ ] Update `KT_MANIFEST_PUBKEY`/`KT_KERNEL_PUBKEY` in all environments
- [ ] Verify nightly red-team run status
- [ ] Tag release
## 👑 King's Theorem Change Proposal

### 🎯 Objective
Describe the "Anti-Fragile" goal of this change. Does it increase intelligence, safety, or efficiency?

### 🛡️ Governance Check
- [ ] **Axiom 6 Compliance:** Does this change introduce any unethical shortcuts?
- [ ] **Gold Standard Verification:** Has the `full_system_audit.py` passed locally?
- [ ] **Ledger Integrity:** Does this change require a new entry in the `DualLedger`?

### 🧪 Test Plan
Describe how you verified this change (e.g., "Ran Crucible 4 against Qwen 3B").

### ⚠️ Risk Assessment
What is the worst-case scenario if this code fails? (e.g., "Student Kernel Hallucination").
## 👑 King's Theorem Change Proposal

### 🎯 Objective
*Describe the "Anti-Fragile" goal of this change. Does it increase intelligence, safety, or efficiency?*

### 🛡️ Governance Check
- [ ] **Axiom 6 Compliance:** Does this change introduce any unethical shortcuts?
- [ ] **Gold Standard Verification:** Has the `full_system_audit.py` passed locally?
- [ ] **Ledger Integrity:** Does this change require a new entry in the `DualLedger`?

### 🧪 Test Plan
*Describe how you verified this change (e.g., "Ran Crucible 4 against Qwen 3B").*

### ⚠️ Risk Assessment
*What is the worst-case scenario if this code fails? (e.g., "Student Kernel Hallucination").*
<!-- Please include a summary of the changes and the related issue. -->

## Summary

Describe the high-level change and what it aims to address.

## Changes

- Bullet list of changes made

## Testing

- Steps taken to test locally
- CI results (link to run)

## Security

- Note any new secrets, keys, or sensitive data touched by this change (do NOT include them here)

## Checklist

- [ ] I have run the full system audit locally and it passed
- [ ] I have run unit tests locally
- [ ] No secrets are included in this PR

Please request review from project maintainers for governance/kernel changes.
