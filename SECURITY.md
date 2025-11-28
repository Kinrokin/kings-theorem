# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in King's Theorem, please report it to:
- Email: security@kings-theorem.org (if available) or repository maintainer
- Private disclosure preferred before public announcement

## Security Practices

### 1. Manifest & EvidenceID Signing

All manifests containing EvidenceIDs must be cryptographically signed to prevent forgery, replay attacks, and tampering.

**Production Usage:**
- Use Ed25519 signatures (preferred) via `cryptography` library
- Store private keys in secure key management system (AWS KMS, Azure Key Vault, HashiCorp Vault)
- Never commit private keys to repository

**Key Generation (Ed25519) - OpenSSL Method:**
```bash
# Generate private key
openssl genpkey -algorithm ed25519 -out ed25519_priv.pem

# Extract public key
openssl pkey -in ed25519_priv.pem -pubout -out ed25519_pub.pem
```

**Key Generation (Ed25519) - Python Method:**
```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# Generate key pair
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Serialize private key as PEM (STORE SECURELY, DO NOT COMMIT)
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Serialize public key as PEM (safe to commit to repo config)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Save to files
with open('ed25519_priv.pem', 'wb') as f:
    f.write(private_pem)
with open('ed25519_pub.pem', 'wb') as f:
    f.write(public_pem)
```

**Signing Manifests:**
```python
from src.manifest.signature import sign_manifest, verify_manifest

# Load private key
with open('ed25519_priv.pem', 'rb') as f:
    privkey_pem = f.read()

# Sign manifest
manifest = {
    "evidence_id": "EVID-2024-001",
    "artifact": "proof",
    "version": "1.0",
    "payload": {"theorem": "safety_invariant"}
}
signed_manifest = sign_manifest(manifest, privkey_pem=privkey_pem)

# signed_manifest now contains: content_hash, signature, signed_by fields
```

**Verifying Manifests:**
```python
from src.manifest.signature import verify_manifest

# Load public key
with open('ed25519_pub.pem', 'rb') as f:
    pubkey_pem = f.read()

# Verify signature and integrity
ok, reason = verify_manifest(signed_manifest, pubkey_pem=pubkey_pem)
if ok:
    print(f"Manifest verified: {reason}")
else:
    raise ValueError(f"Manifest verification failed: {reason}")
```

**CLI Tools:**
```bash
# Sign a manifest
python -m src.manifest.cli sign -i manifest.json -o manifest.signed.json --privkey ed25519_priv.pem

# Verify a manifest
python -m src.manifest.cli verify -i manifest.signed.json --pubkey ed25519_pub.pem

# Registry batch verification
python -m src.registry.cli --dir manifests/ --pubkey ed25519_pub.pem
```

**Dev/Test HMAC Fallback:**
```python
# For local development only (NOT production)
secret = b"dev-test-secret"
signed = sign_manifest(manifest, hmac_secret=secret)
ok, reason = verify_manifest(signed, hmac_secret=secret)
```

### 2. Kernel Metadata Signing

All kernel metadata (type, warrant_threshold, veto_power, proof_burden) must be cryptographically signed.

### 2. Kernel Metadata Signing

All kernel metadata (type, warrant_threshold, veto_power, proof_burden) must be cryptographically signed to prevent kernel identity spoofing and privilege escalation.

**Production Usage:**
- Use same Ed25519 keys as manifest signing (or separate key pair for kernel-specific signing)
- Orchestrator must verify kernel signatures at boot time before allowing execution

**Signing Kernel Metadata:**
```python
from src.manifest.signature import sign_manifest

# Kernel manifest with metadata
kernel_manifest = {
    "kernel_id": "arbiter_v1",
    "type": "Arbiter",
    "veto_power": 10,
    "warrant": 0.95,
    "proof_burden": "formal",
    "image_digest": "sha256:abc123..."  # Container image hash
}

# Sign with Ed25519
with open('ed25519_priv.pem', 'rb') as f:
    privkey = f.read()
signed_kernel = sign_manifest(kernel_manifest, privkey_pem=privkey)
```

**Boot-Time Verification:**
```python
from src.orchestrator.verify_kernels import boot_verify_and_enforce

# Load public key
with open('ed25519_pub.pem', 'rb') as f:
    pubkey = f.read()

# Verify all kernels before orchestrator startup
kernel_manifests = [signed_kernel_1, signed_kernel_2, signed_arbiter]
boot_verify_and_enforce(kernel_manifests, pubkey_pem=pubkey)
# Raises RuntimeError if Arbiter missing or any critical kernel fails verification
```

**Integration in Orchestrator:**
```python
# In your orchestrator startup code (e.g., src/orchestrator/main.py)
import yaml
from src.orchestrator.verify_kernels import boot_verify_and_enforce

# Load kernel configs
with open('config/kernels.yaml') as f:
    kernels = yaml.safe_load(f)['kernels']

# Load verification key from environment or secure storage
pubkey_path = os.getenv('KT_KERNEL_PUBKEY', 'keys/kernel_pub.pem')
with open(pubkey_path, 'rb') as f:
    pubkey = f.read()

# Enforce verification before starting any kernel
boot_verify_and_enforce(kernels, pubkey_pem=pubkey)
print("✓ All kernel signatures verified. Starting orchestrator...")
```

### 3. Secret Rotation Workflow

**When to Rotate:**
- Immediately if keys are exposed or compromised
- Quarterly for routine maintenance
- After team member departure
- Before major releases

**Rotation Steps:**
1. Generate new Ed25519 key pair (see Key Generation above)
2. Re-sign all manifests and kernel metadata with new private key
3. Update `config/master_config.yaml` or environment variables with new public key path
4. Update production key management system with new keys
5. Revoke old keys from access control
6. Document rotation in audit log (`logs/security_audit.log`)

**Example Rotation Script:**
```python
# scripts/rotate_keys.py
import json
import os
from pathlib import Path
from src.manifest.signature import sign_manifest

def rotate_all_manifests(old_priv_path, new_priv_path, manifest_dir):
    """Re-sign all manifests with new key."""
    with open(new_priv_path, 'rb') as f:
        new_privkey = f.read()

    for manifest_file in Path(manifest_dir).rglob('*.json'):
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)

        # Strip old signature fields
        manifest.pop('signature', None)
        manifest.pop('content_hash', None)
        manifest.pop('signed_by', None)

        # Re-sign with new key
        signed = sign_manifest(manifest, privkey_pem=new_privkey)

        # Overwrite
        with open(manifest_file, 'w') as f:
            json.dump(signed, f, indent=2)

        print(f"✓ Re-signed {manifest_file}")

if __name__ == "__main__":
    rotate_all_manifests(
        old_priv_path='keys/old_priv.pem',
        new_priv_path='keys/new_priv.pem',
        manifest_dir='manifests/'
    )
```

### 4. Pre-Commit Secret Scanning

**Setup:**
```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
pre-commit install
```

**Baseline Update:**
```bash
# When adding legitimate secrets to baseline (e.g., test fixtures)
detect-secrets scan --baseline .secrets.baseline
```

**CI Enforcement:**
- Secret scanning runs on every commit via pre-commit hooks
- CI fails if secrets detected (see `.github/workflows/ci.yml`)
- Use `fetch-depth: 0` to scan entire history

### 4. Pre-Commit Secret Scanning

**Setup:**
```bash
pip install detect-secrets pre-commit
detect-secrets scan > .secrets.baseline
pre-commit install
```

**Baseline Update:**
```bash
# When adding legitimate secrets to baseline (e.g., test fixtures)
detect-secrets scan --baseline .secrets.baseline
```

**CI Enforcement:**
- Secret scanning runs on every commit via pre-commit hooks (`.pre-commit-config.yaml`)
- CI fails if secrets detected (see `.github/workflows/ci.yml`)
- Use `fetch-depth: 0` to scan entire history

**Scrubbing Secrets from Git History:**
If secrets are accidentally committed, use `git-filter-repo` (preferred) or `BFG Repo-Cleaner`:
```bash
# Install git-filter-repo
pip install git-filter-repo

# Remove file from history
git filter-repo --path secrets/private.pem --invert-paths

# Force push (coordinate with team!)
git push origin --force --all
```

### 5. Threat Model

### 5. Threat Model

**Critical Threats (Remediated in Phase 3):**
1. **Manifest/EvidenceID Forgery**: Attacker creates fake manifests with copied EvidenceIDs
   - Mitigation: Ed25519 cryptographic signing (`src/manifest/signature.py`)
   - Validation: Registry batch verification (`src/registry/cli.py`)

2. **Kernel Identity Spoofing**: Fake Arbiter kernels with elevated veto_power
   - Mitigation: Kernel metadata signing + boot-time verification (`src/orchestrator/verify_kernels.py`)
   - Enforcement: `boot_verify_and_enforce()` raises on Arbiter failures

3. **Composition Loophole**: Step-wise safe but compositionally dangerous sequences
   - Mitigation: Composition proof obligations (`src/algebra/composer.py`)
   - Validation: Global invariant checking via `ProofChecker`

**High Priority Threats:**
4. **Manifold Bypass**: Adversarial vectors escape ethical bounds
   - Mitigation: Convex QP projection (`src/ethics/manifold.py`)

5. **Proof Spoofing**: Circular or invalid proofs accepted as valid
   - Mitigation: DAG cycle detection (`src/proofs/proof_lang.py`)

6. **Counterfactual Blindness**: Low-probability catastrophic paths missed
   - Mitigation: Monte Carlo sampling (`src/reasoning/counterfactual_engine.py`)

**Medium Priority Threats:**
7. **Timing Attacks**: Kernel orchestration delays manipulated
   - Mitigation: Deterministic tie-breaking (`src/governance/timing_defense.py`)

8. **Homogenization**: Outputs collapse to single "safe" value
   - Mitigation: Entropy monitoring (`src/kernels/entropy_monitor.py`)

9. **Dependency Poisoning**: Malicious packages in supply chain
   - Mitigation: Lockfile enforcement + SCA scanning (see below)

**Medium Priority Threats (Remediated in Phase 4):**
4. **Counterfactual Rare Events**: Low-probability catastrophic composition failures
   - Mitigation: Enhanced counterfactual engine with adversarial heuristics (`src/reasoning/counterfactual_engine.py`)
   - Detection: NaN/Inf checks, extreme values, contradictions, risk-without-safety patterns

5. **Source Flooding**: Adversaries register many fake sources to manipulate consensus
   - Mitigation: Federated source registry with flood detection (`src/sourcing/source_registry.py`)
   - Enforcement: Registration rate limits, reputation scoring, cluster diversity caps

6. **Circular Proof Endorsement**: Proofs that reference themselves or form cycles
   - Mitigation: Proof meta-checker with self-endorsement detection (`src/proofs/proof_lang.py`)
   - Validation: DFS cycle detection, depth limits, invariant verification

7. **UX Manipulation**: Deceptive framing, omissions, and balance violations
   - Mitigation: Semantic audit beyond token checks (`src/ux/semantic_audit.py`)
   - Detection: Forbidden framing patterns, disclosure requirements, balance keywords

**Lower Priority Threats:**
8. **Timing Attacks**: Kernel orchestration delays manipulated
   - Mitigation: Deterministic tie-breaking (`src/governance/timing_defense.py`)

9. **Homogenization**: Outputs collapse to single "safe" value
   - Mitigation: Entropy monitoring (`src/kernels/entropy_monitor.py`)

10. **Dependency Poisoning**: Malicious packages in supply chain
   - Mitigation: Lockfile enforcement + SCA scanning (see below)

### 6. Dependency Management

**SCA (Software Composition Analysis):**
```bash
# Check for CVEs
pip install safety
safety check

# Update dependencies
pip-audit
```

**SBOM Generation:**
```bash
pip install pip-licenses
pip-licenses --format=json > sbom.json
```

**Lockfile Enforcement:**
```bash
# Use requirements.lock for reproducible builds
pip install --require-hashes -r requirements.lock
```

### 6. Dependency Management

**SCA (Software Composition Analysis):**
```bash
# Check for CVEs
pip install safety
safety check

# Update dependencies
pip install pip-audit
pip-audit
```

**SBOM Generation:**
```bash
pip install pip-licenses
pip-licenses --format=json > sbom.json
```

**Lockfile Enforcement:**
```bash
# Generate lockfile with hashes
pip freeze > requirements.lock

# Install with hash verification
pip install --require-hashes -r requirements.lock
```

**CI Integration:**
See `.github/workflows/ci.yml` for automated `safety` and `bandit` scans on every push.

### 7. Secure Configuration

**Environment Variables:**
- `KT_MANIFEST_PRIVKEY`: Path to Ed25519 private key for signing manifests (production only)
- `KT_MANIFEST_PUBKEY`: Path to Ed25519 public key for verifying manifests (all environments)
- `KT_KERNEL_PUBKEY`: Path to Ed25519 public key for verifying kernel metadata (all environments)
- `KT_HMAC_SECRET`: HMAC secret for dev/test (NOT for production - use Ed25519 instead)

**Never commit:**
- Private keys (`*_priv.pem`, `*.key`, `id_rsa`, `id_ed25519`)
- API tokens (`GITHUB_TOKEN`, `OPENAI_API_KEY`)
- Database credentials
- HMAC secrets (except test fixtures with well-known test values like `"dev-test-secret"`)

**Public Key Management:**
- Public keys (`*_pub.pem`) MAY be committed to repo in `keys/` directory
- Pin specific public key hash in CI secrets for additional verification
- Rotate quarterly or when team composition changes

### 8. Incident Response

**If Secret Exposed:**
1. Rotate affected keys immediately
2. Audit logs for unauthorized access
3. Notify affected parties
4. Document in security incident log
5. Update security procedures to prevent recurrence

**Disclosure Timeline:**
- T+0: Private report received
- T+7 days: Acknowledgment to reporter
- T+30 days: Patch released
- T+90 days: Public disclosure (if not critical)

### 8. Incident Response

**If Secret Exposed:**
1. **Immediate**: Rotate affected keys using rotation script (see Section 3)
2. **Audit**: Review logs for unauthorized access or signature verification failures
3. **Notify**: Inform affected parties (users, team members, stakeholders)
4. **Document**: Record incident in `logs/security_incidents.log` with timestamp, impact, and remediation
5. **Postmortem**: Update security procedures to prevent recurrence

**Disclosure Timeline:**
- T+0: Private report received via GitHub Security Advisory or email
- T+7 days: Acknowledgment to reporter
- T+30 days: Patch released and deployed
- T+90 days: Public disclosure (if not critical/actively exploited)

**Emergency Contact:**
- File GitHub issue with `[SECURITY]` prefix for private triage
- Email: (configure security contact in GitHub settings)

### 9. Compliance & Auditing

**Audit Logs:**
- All kernel invocations logged with provenance
- Metadata verification failures logged
- Projection violations flagged
- Counterfactual violation paths recorded

**Immutable Ledger:**
- Uses Merkle tree in `src/ledger/integrity_ledger.py`
- Cannot retroactively alter decisions
- Cryptographically verifiable chain of custody

### 9. Compliance & Auditing

**Audit Logs:**
- All kernel invocations logged with provenance (`logs/golden_dataset.jsonl`)
- Metadata verification failures logged by `src.orchestrator.verify_kernels`
- Projection violations flagged by `src.ethics.manifold`
- Counterfactual violation paths recorded by `src.reasoning.counterfactual_engine`
- Composition proof failures tracked in ledger

**Immutable Ledger:**
- Uses Merkle tree in `src/ledger/integrity_ledger.py`
- Cannot retroactively alter decisions
- Cryptographically verifiable chain of custody
- Root hash published for external verification

**Regulatory Compliance:**
- GDPR: Data minimization via constraint expressions
- SOC 2: Audit trail completeness via integrity ledger
- NIST 800-53: Access control via kernel signing
- ISO 27001: Key management procedures (see Sections 1-3)

### 10. Security Tools in CI/CD

**Automated Scanning:**
- `bandit`: AST-based Python security linter
- `safety`: Dependency vulnerability scanner
- `detect-secrets`: Prevent secret commits
- `ruff`: Fast linter with security rules
- `mypy`: Type safety enforcement

### 10. Security Tools in CI/CD

**Automated Scanning:**
- `bandit`: AST-based Python security linter (B3xx-level issues)
- `safety`: Dependency vulnerability scanner (CVE database)
- `detect-secrets`: Prevent secret commits (pre-commit hook)
- `ruff`: Fast linter with security rules (S1xx, B0xx)
- `mypy`: Type safety enforcement (prevents None errors, type confusion)
- `cryptography`: Ed25519 signature verification in tests

**Test Coverage:**
- **Phase 3 (Critical)**: Manifest signing, kernel verification, composition proofs
  - `tests/test_manifest_signature.py` (Ed25519/HMAC)
  - `tests/test_kernel_metadata_tamper.py` (boot-time verification)
  - `tests/test_composition_proof.py` (global invariants)

- **Phase 4 (Medium Priority)**: Rare events, source flooding, proof cycles, UX manipulation
  - `tests/test_counterfactual_rare_events.py` (8 tests: NaN, contradictions, extreme values)
  - `tests/test_source_flooding.py` (5 tests: flood detection, reputation, diversity)
  - `tests/test_proof_meta_checks.py` (7 tests: cycles, self-endorsement, depth limits)
  - `tests/test_ux_semantic_audit.py` (13 tests: framing, disclosures, balance)

- **Adversarial Battery**: `tests/adversarial/` (37+ tests)

**CI Workflow:** `.github/workflows/ci.yml`
- Pre-commit suite runs on all files
- Security scans (bandit, safety) with JSON reports
- Phase 3 security tests (manifest, kernel, composition)
- Phase 4 security tests (counterfactual, source, proof, UX)
- Adversarial tests run in dedicated step
- Coverage uploaded to Codecov with CI failure on drop

## Rotation Log

- 2025-11-24: Generated new Ed25519 key pair for manifests/kernels.
    - Public key: `keys/ed25519_pub.pem`
    - Fingerprint (SHA-256 of PEM): `514f37f16d673d60e642bfbd5a8efb801ae48d9a85616c605682aca5491d69cf`
    - Actions: Updated local keys; prepared rotation script (`scripts/rotate_keys.py`); collaborators to update env vars `KT_MANIFEST_PUBKEY` and `KT_KERNEL_PUBKEY` as applicable.

### 11. Federated Source Management (Phase 4)

**Registration Procedures:**
- Maximum 10 new sources per 60-second window (configurable via `max_new_sources_per_window`)
- Sources must provide diversity tags (e.g., `{"medical", "journal", "peer_reviewed"}`)
- Initial reputation defaults to 0.7 (configurable via `initial_reputation`)

**Reputation Scoring:**
- Exponential moving average with decay factor 0.3: `new_rep = 0.3 * feedback + 0.7 * old_rep`
- Range: [0.0, 1.0] with minimum threshold enforcement (default 0.3)
- Sources below `min_reputation` excluded from influence weighting

**Diversity Constraints:**
- Clusters detected via shared diversity tags
- Maximum cluster influence capped at 40% (configurable via `max_cluster_influence`)
- Excess weight redistributed proportionally to uncapped clusters
- Prevents single domain from dominating consensus

**Blacklisting:**
- Manual or automated blacklisting with reason tracking
- Blacklisted sources permanently excluded from weighting
- Audit log captures blacklist events with timestamps

**Usage Example:**
```python
from src.sourcing.source_registry import SourceRegistry

registry = SourceRegistry(
    min_reputation=0.3,
    max_cluster_influence=0.4,
    max_new_sources_per_window=10,
    flood_window=60.0
)

# Register sources
registry.register_source("med_journal_1", b"key1", diversity_tags={"medical", "journal"})
registry.register_source("gov_health_1", b"key2", diversity_tags={"gov", "health"})

# Update reputation based on feedback
registry.update_reputation("med_journal_1", 0.9)  # Positive feedback

# Compute influence weights (caps cluster at 40%, redistributes excess)
weights = registry.compute_influence_weights()

# Blacklist compromised source
registry.blacklist_source("bad_actor", reason="manual_review")
```

### 12. UX Semantic Audit (Phase 4)

**Forbidden Framing Patterns:**
- Absolutist language: "always", "never", "impossible", "guaranteed"
- Superlatives: "best", "worst", "only", "perfect"
- False necessity: "must", "need", "required" (context-dependent)
- Detects via regex patterns with word boundaries

**Disclosure Requirements:**
- High-stakes contexts (medical, financial, legal) require uncertainty acknowledgment
- Keywords trigger disclosure check: "diagnose", "invest", "treatment", "portfolio"
- Fails if uncertainty terms absent: "uncertain", "may", "possible", "risk"

**Balance Coverage:**
- Pro/con balance: "benefit" requires "risk", "drawback", or "cost"
- Risk/benefit balance: "risk" requires "benefit" or "advantage"
- Advantage/disadvantage balance: "pro" requires "con" or "against"
- Detects imbalanced coverage when one keyword present without counterpart

**Omission Detection:**
- Medical context: Must mention "side effect" or "risk" or "complication"
- Financial context: Must mention "risk" or "loss" or "volatility"
- Fails if high-stakes context lacks critical omission keywords

**Contradiction Detection:**
- Identifies opposing claims in same response
- Patterns: "safe...dangerous", "effective...ineffective", "increase...decrease"
- Reports pairs of contradictory terms with issue type "contradiction"

**Usage Example:**
```python
from src.ux.semantic_audit import SemanticAuditor

auditor = SemanticAuditor()
text = "This treatment is guaranteed to work. Invest now for perfect results."

issues = auditor.audit(text)
for issue in issues:
    print(f"{issue.issue_type}: {issue.description} at position {issue.position}")
    # Output: framing: Forbidden framing: guaranteed at position 12
    #         framing: Forbidden framing: perfect at position 58
    #         disclosure: High-stakes context (medical) missing uncertainty disclosure
```

**Audit Report Generation:**
```python
report = auditor.generate_report(text)
print(report)
# Output:
# === UX Semantic Audit Report ===
# Text length: 72 characters
# Issues found: 3
# - framing (position 12): Forbidden framing: guaranteed
# - framing (position 58): Forbidden framing: perfect
# - disclosure (position 0): High-stakes context (medical) missing uncertainty disclosure
```

### 13. Contact & Resources

**Maintainer:** @Kinrokin
**Security Contact:** File issue with `[SECURITY]` prefix
**Documentation:** See `docs/manual/` for architecture details

**External Resources:**
- OWASP: https://owasp.org
- CWE Database: https://cwe.mitre.org
- NIST NVD: https://nvd.nist.gov
