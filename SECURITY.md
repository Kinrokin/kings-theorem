# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in King's Theorem, please report it to:
- Email: security@kings-theorem.org (if available) or repository maintainer
- Private disclosure preferred before public announcement

## Security Practices

### 1. Kernel Metadata Signing

All kernel metadata (type, warrant_threshold, veto_power, proof_burden) must be cryptographically signed.

**Production Usage:**
- Use Ed25519 signatures (preferred)
- Store private keys in secure key management system (AWS KMS, Azure Key Vault, HashiCorp Vault)
- Never commit private keys to repository

**Key Generation (Ed25519):**
```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# Generate key pair
private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Serialize private key (STORE SECURELY, DO NOT COMMIT)
private_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PrivateFormat.Raw,
    encryption_algorithm=serialization.NoEncryption()
)

# Serialize public key (safe to commit to repo config)
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)
```

**Signing Kernels:**
```python
from src.kernels.metadata import KernelMetadata, sign_metadata, verify_metadata

# Create metadata
metadata = KernelMetadata(
    kernel_id="arbiter_v1",
    type="META",
    warrant_threshold=0.95,
    veto_power=10,
    proof_burden="formal"
)

# Sign (use your private key)
signed = sign_metadata(metadata, privkey=private_key_bytes)

# Verify (use corresponding public key)
assert verify_metadata(signed, pubkey=public_key_bytes)
```

### 2. Secret Rotation Workflow

**When to Rotate:**
- Immediately if keys are exposed or compromised
- Quarterly for routine maintenance
- After team member departure
- Before major releases

**Rotation Steps:**
1. Generate new Ed25519 key pair
2. Update `config/master_config.yaml` with new public key
3. Re-sign all kernel metadata with new private key
4. Update production key management system
5. Revoke old keys from access control
6. Document rotation in audit log

**Example Rotation Script:**
```python
# scripts/rotate_kernel_keys.py
import yaml
from src.kernels.metadata import KernelMetadata, sign_metadata

def rotate_keys(old_private_key, new_private_key, kernel_configs):
    """Rotate kernel metadata signatures."""
    for config in kernel_configs:
        # Load existing metadata
        metadata = KernelMetadata(**config)
        # Re-sign with new key
        signed = sign_metadata(metadata, privkey=new_private_key)
        # Update config
        config['signature'] = signed.signature
    return kernel_configs
```

### 3. Pre-Commit Secret Scanning

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

### 4. Threat Model

**High Priority Threats:**
1. **Metadata Forgery**: Attacker creates fake kernels with elevated privileges
   - Mitigation: Cryptographic signing with Ed25519
2. **Manifold Bypass**: Adversarial vectors escape ethical bounds
   - Mitigation: Convex QP projection, not axis-clamping
3. **Proof Spoofing**: Circular or invalid proofs accepted as valid
   - Mitigation: DAG cycle detection, structural validation
4. **Counterfactual Blindness**: Low-probability catastrophic paths missed
   - Mitigation: Monte Carlo sampling with dependency awareness

**Medium Priority Threats:**
5. **Timing Attacks**: Kernel orchestration delays manipulated
6. **Homogenization**: Outputs collapse to single "safe" value
7. **Dependency Poisoning**: Malicious packages in supply chain

### 5. Dependency Management

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

### 6. Secure Configuration

**Environment Variables:**
- `KT_METADATA_PRIVKEY`: Path to Ed25519 private key (production)
- `KT_METADATA_PUBKEY`: Path to Ed25519 public key (all environments)
- `KT_HMAC_SECRET`: HMAC secret for dev/test (NOT for production)

**Never commit:**
- Private keys (`*.pem`, `*.key`)
- API tokens
- Database credentials
- HMAC secrets (except test fixtures with known values)

### 7. Incident Response

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

### 8. Compliance & Auditing

**Audit Logs:**
- All kernel invocations logged with provenance
- Metadata verification failures logged
- Projection violations flagged
- Counterfactual violation paths recorded

**Immutable Ledger:**
- Uses Merkle tree in `src/ledger/integrity_ledger.py`
- Cannot retroactively alter decisions
- Cryptographically verifiable chain of custody

### 9. Security Tools in CI/CD

**Automated Scanning:**
- `bandit`: AST-based Python security linter
- `safety`: Dependency vulnerability scanner
- `detect-secrets`: Prevent secret commits
- `ruff`: Fast linter with security rules
- `mypy`: Type safety enforcement

**See:** `.github/workflows/ci.yml` for full pipeline

### 10. Contact & Resources

**Maintainer:** @Kinrokin
**Security Contact:** File issue with `[SECURITY]` prefix
**Documentation:** See `docs/manual/` for architecture details

**External Resources:**
- OWASP: https://owasp.org
- CWE Database: https://cwe.mitre.org
- NIST NVD: https://nvd.nist.gov
