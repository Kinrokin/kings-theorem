# S-Tier Upgrade Roadmap — King's Theorem v53

**Status**: Post-kernel tuning, baseline regeneration, and governance gate hardening complete
**Current Catastrophic Risk**: ~0.59% (512 samples)
**Branch**: `kt/harden-api-v1`
**Owner**: Kinrokin
**Repository**: https://github.com/Kinrokin/kings-theorem

---

## Executive Summary

This roadmap defines the path to **S-tier governance**, where unsafe operations are structurally impossible, forensic traces are immutable, and every decision carries cryptographic proof. The system enforces safety through:

- **Runtime enforcement**: Risk budgets, theorem proofs, and composition gates block unsafe paths at decision time.
- **CI hardening**: Multi-stage gates (lint, secrets, hashes, theorems, risk budgets) prevent merges that violate invariants.
- **Supply-chain cryptography**: Signed manifests, lockfile hashes, and optional HSM integration ensure provenance.
- **Observability**: Structured logs, OCSF events, and audit trails provide forensic reconstruction.

---

## Phase 1: Runtime Enforcement (Structural Safety)

**Goal**: Make unsafe decisions unrepresentable at runtime.

### 1.1 Risk Budget Gating (✅ Complete)

- **Status**: Arbiter integrates `RiskBudget` loader and `finalize_decision()` enforcement.
- **Evidence**:
  - `src/risk/budget.py`: RiskBudget with optional signature verification.
  - `src/risk/guard.py`: `finalize_decision()` returns safe fallback if budget exceeded.
  - `scripts/check_risk_budget.py`: CI enforcement script.
  - Catastrophic risk: 0.59% (below 5% budget).

### 1.2 DSL Theorem Gating (✅ Complete)

- **Status**: Proof DSL with JSON artifact export; CI gate on theorem FAIL.
- **Evidence**:
  - `src/proofs/dsl.py`: `evaluate_to_json()` emits machine-readable theorems with certificate hash.
  - `scripts/ci_dsl_theorems.py`: CI script gates on all_pass.
  - `audit/dsl_theorems.json`: Artifact includes theorem status, constraints, and certificate.

### 1.3 PCEB Ledger (✅ Complete)

- **Status**: Post-Composition Evidence Bundle ledger with hash-chain integrity.
- **Evidence**:
  - `src/ledger/pceb_ledger.py`: Append/verify hash-chain for PCEB events.
  - `src/kernels/arbiter_v47.py`: Appends PCEB after composition.
  - `scripts/kt_audit.py`: Reports `pceb_chain_ok`.

### 1.4 Emotion Drift Ledger (✅ Complete)

- **Status**: Hash-chain ledger for emotion drift events.
- **Evidence**:
  - `src/ledger/emotion_drift_ledger.py`: Append/verify hash-chain.
  - `src/ux/emotion_drift.py`: Emotion drift detector.
  - `scripts/kt_audit.py`: Reports `emotion_drift_chain_ok`.

### 1.5 Revocation Ledger (✅ Complete)

- **Status**: Merkle tree for manifest revocation; runtime enforcement TBD.
- **Evidence**:
  - `src/ledger/revocation_ledger.py`: Merkle tree with Ed25519 signatures.
  - `scripts/verify_revocation_chain.py`: Chain integrity CI check.
  - **TODO**: Wire revocation checks into Arbiter decision gate.

### 1.6 Composition Invariants (✅ Complete)

- **Status**: Counterfactual Engine with CVaR-based violation classes.
- **Evidence**:
  - `src/reasoning/counterfactual_engine.py`: Violation scoring with diminishing returns, safety damping, thresholds (CRITICAL/HIGH/MEDIUM/LOW).
  - `src/registry/kernel_registry.py`: Adversarial kernels (RiskAction, Amplifier, Composition) with calibrated tail probabilities.
  - Risk profiles include `violation_class` and `cvar_estimate`.

---

## Phase 2: CI Hardening (Merge-Time Gates)

**Goal**: Every merge must pass all invariants or be structurally blocked.

### 2.1 Pre-Commit Hooks (✅ Complete)

- **Status**: Active hooks for formatting, secrets, hashes.
- **Evidence**:
  - `.pre-commit-config.yaml`:
    - `detect-secrets` (v1.5.0, baseline at `.secrets.baseline`, baseline excluded from scan)
    - `ruff`, `ruff-format`, `black`, `isort` (style/lint)
    - `bandit` (security linter)
    - `hash-enforcement` (lockfile hash verification via `scripts/pre_commit_hash_check.py`)
  - **Passing**: detect-secrets, hash-enforcement, bandit, isort.
  - **Reformatting on commit**: ruff-format, black (expected behavior).

### 2.2 CI Pipeline Gates (✅ Complete)

- **Status**: GitHub Actions workflow with multi-stage enforcement.
- **Evidence**:
  - `.github/workflows/ci.yml`:
    - **Lint/Format**: ruff, black, isort, mypy.
    - **Security**: bandit, safety, detect-secrets.
    - **Supply Chain**: `scripts/verify_lockfile.py` (hash enforcement), SBOM generation.
    - **Invariants**: `scripts/ci_bias_invariants.py` (kt_bias/kt_emotion/kt_composition markers, tradition diversity).
    - **Theorems**: `scripts/ci_dsl_theorems.py` (DSL theorem gating).
    - **Risk Budget**: `scripts/check_risk_budget.py` (catastrophic probability enforcement).
    - **Revocation**: `scripts/verify_revocation_chain.py` (chain integrity).

### 2.3 Supply Chain Lockfile (✅ Complete)

- **Status**: `requirements.lock` with pip-compile hashes; verification scripts.
- **Evidence**:
  - `scripts/generate_lockfile.py`: `pip-compile --generate-hashes` to produce `requirements.lock`.
  - `scripts/verify_lockfile.py`: Multi-line aware hash verification.
  - `scripts/pre_commit_hash_check.py`: Pre-commit enforcement.
  - CI step in workflow validates lockfile.

### 2.4 Signed Artifacts (🔶 Partial)

- **Status**: Risk budget supports optional signature verification; manifests have Ed25519 signing infrastructure.
- **Evidence**:
  - `src/risk/budget.py`: `load_risk_budget()` checks env var `KT_VERIFY_RISK_BUDGET_SIGNATURE` for optional sig verification.
  - `src/ledger/revocation_ledger.py`: Ed25519 signing for revocation events.
  - **TODO**:
    - Sign `risk_budget.yml` artifact in CI; store public key in `keys/`.
    - Sign DSL theorem artifacts (`audit/dsl_theorems.json`).
    - Sign SBOM/manifest artifacts.

---

## Phase 3: Cryptographic Supply Chain

**Goal**: All artifacts, dependencies, and configurations carry cryptographic proof of integrity and provenance.

### 3.1 Manifest Signing (🔶 Partial)

- **Current**:
  - `deployment/manifest.json` exists with "certificate" field containing SHA256 hash.
  - `src/ledger/revocation_ledger.py` supports Ed25519 signing.
- **TODO**:
  - Generate Ed25519 keypair for manifest signing (store private key securely, public key in `keys/manifest.pub`).
  - Add `--sign-manifest` flag to deployment scripts; sign manifest with private key.
  - Add CI step to verify manifest signature before deployment.
  - Wire manifest revocation checks into Arbiter runtime (reject revoked manifests).

### 3.2 Lockfile Hash Verification (✅ Complete)

- **Status**: `requirements.lock` with hashes; verification in CI and pre-commit.
- **Next**:
  - Add `--require-hashes` enforcement to pip install commands in CI/deployment.
  - Add subresource integrity (SRI) hashes for any frontend assets if applicable.

### 3.3 HSM Integration Prep (⏱️ Future)

- **Goal**: Store signing keys in Hardware Security Module (HSM) or cloud KMS (AWS KMS, GCP KMS, Azure Key Vault).
- **Steps**:
  - Abstract signing interface in `src/utils/crypto.py`:
    - `sign(data: bytes, key_id: str) -> bytes`
    - `verify(data: bytes, signature: bytes, key_id: str) -> bool`
  - Implement HSM backend (e.g., `pkcs11` library for local HSM, boto3/google-cloud-kms for cloud).
  - Update `load_risk_budget()`, manifest signing, and revocation ledger to use HSM interface.
  - Add env vars: `KT_HSM_ENABLED`, `KT_HSM_KEY_ID`.

### 3.4 Reproducible Builds (⏱️ Future)

- **Goal**: Deterministic builds with verifiable hashes.
- **Steps**:
  - Pin all transitive dependencies with exact hashes.
  - Use `SOURCE_DATE_EPOCH` for reproducible timestamps.
  - Generate build provenance metadata (SLSA framework).
  - Store build hashes in ledger; CI verifies artifact hashes match.

---

## Phase 4: DSL & Theorem Expansion

**Goal**: Expand proof DSL to cover more complex safety invariants and generate formal verification artifacts.

### 4.1 Enhanced DSL Syntax (⏱️ Future)

- **Current**: Minimal DSL with constraints, theorems, and basic logical operators (`&`, `|`, `!`, `->`).
- **Enhancements**:
  - **Quantifiers**: `forall`, `exists` (e.g., `forall kernel: kernel.safety_score > 0.5`).
  - **Temporal operators**: `always`, `eventually`, `until` (e.g., `always(risk < 0.1)`).
  - **Arithmetic constraints**: `sum(safety_scores) >= threshold`.
  - **Composition predicates**: `composable(A, B)`, `consistent(state)`.
- **Example**:
  ```
  constraint C1: forall decision: decision.risk < 0.1
  constraint C2: always(composition_path.length <= 5)
  theorem T1: C1 & C2 -> SYSTEM_SAFE
  ```

### 4.2 Formal Verification Integration (⏱️ Future)

- **Goal**: Export DSL theorems to formal verification tools (Z3, Coq, Lean).
- **Steps**:
  - Add `--export-z3` flag to DSL CLI; emit SMT-LIB2 format.
  - Add `--export-coq` flag; emit Coq tactics.
  - CI step: run Z3 solver on exported theorems; fail if unsat.
  - Store solver output in `audit/formal_verification.json`.

### 4.3 Runtime Theorem Enforcement (⏱️ Future)

- **Goal**: Arbiter checks theorems before finalizing decisions.
- **Steps**:
  - Load DSL program in Arbiter initialization.
  - Before `finalize_decision()`, evaluate theorems with current decision evidence.
  - If any theorem FAIL, return safe fallback (or refusal).
  - Log theorem evaluation to PCEB ledger.

---

## Phase 5: Observability & Forensics

**Goal**: Every decision, composition, and gate enforcement leaves an immutable, queryable trace.

### 5.1 Structured Logging (🔶 Partial)

- **Current**:
  - `src/logging_config.py`: Structured logging with JSON formatting.
  - `logs/golden_dataset.jsonl`: JSONL logs for audit.
- **Enhancements**:
  - Add OCSF (Open Cybersecurity Schema Framework) event formatting via `src/utils/ocsf.py`.
  - Emit OCSF events for:
    - Decision finalization (risk profile, theorem status, budget compliance).
    - Composition paths (kernel order, violation scores).
    - Gate enforcement (pre-commit, CI, runtime).
  - Store OCSF events in `logs/ocsf_events.jsonl`.

### 5.2 Audit Dashboard (⏱️ Future)

- **Goal**: Web UI for querying audit logs, ledger chains, and theorem status.
- **Steps**:
  - Build FastAPI endpoint to serve audit data:
    - `/api/audit/pceb` → PCEB ledger chain.
    - `/api/audit/theorems` → DSL theorem history.
    - `/api/audit/risk` → Risk budget compliance over time.
  - Build React/Vue dashboard:
    - Timeline view of decisions.
    - Ledger integrity visualization.
    - Theorem pass/fail trends.
  - Deploy dashboard as read-only service.

### 5.3 Anomaly Detection (🔶 Partial)

- **Current**:
  - `src/metrics/anomaly.py`: Placeholder for anomaly detection.
  - `src/metrics/spectral_guard.py`: Spectral analysis stub.
- **Enhancements**:
  - Implement statistical anomaly detection on risk profiles:
    - Track moving average/stddev of catastrophic probability.
    - Alert if current sample > 3σ from mean.
  - Implement spectral analysis on composition paths:
    - Detect unusual kernel orderings via frequency analysis.
  - Log anomalies to OCSF events.

### 5.4 Forensic Reconstruction (⏱️ Future)

- **Goal**: Given a decision ID, reconstruct full causal chain from ledgers.
- **Steps**:
  - Implement `forensic_trace(decision_id)`:
    - Query PCEB ledger for decision.
    - Follow composition path back to input kernels.
    - Fetch theorem evaluations, risk profiles.
    - Return full causal graph.
  - Add CLI: `python -m src.scripts.forensic_trace <decision_id>`.

---

## Phase 6: Governance Hardening

**Goal**: Make governance policy enforcement cryptographically verifiable and auditable.

### 6.1 Constitution as Code (🔶 Partial)

- **Current**:
  - `GOVERNANCE.md`: Human-readable governance policy.
- **Enhancements**:
  - Formalize governance rules in DSL:
    - `constraint G1: catastrophic_risk <= 0.05`
    - `constraint G2: all_theorems_pass == true`
    - `theorem GOV1: G1 & G2 -> MERGE_ALLOWED`
  - CI enforces governance theorems; block merges if GOV theorem FAIL.
  - Sign governance DSL file; verify signature in CI.

### 6.2 Multi-Party Approval (⏱️ Future)

- **Goal**: Critical changes require N-of-M signatures from operators.
- **Steps**:
  - Store operator public keys in `keys/operator_*.pub`.
  - Add `--require-approvals N` flag to deployment/merge scripts.
  - Collect Ed25519 signatures from N operators on artifact hash.
  - CI verifies N valid signatures before allowing merge/deploy.

### 6.3 Audit Trail Immutability (⏱️ Future)

- **Goal**: Ledger chains are write-once, append-only; tampering is detectable.
- **Steps**:
  - Add Merkle tree roots to ledger headers.
  - Periodically publish Merkle roots to blockchain or timestamping service (e.g., OpenTimestamps).
  - CI verifies Merkle root consistency across commits.

---

## Phase 7: Performance & Scale

**Goal**: Maintain S-tier governance at production scale without latency regressions.

### 7.1 Counterfactual Sampling Optimization (⏱️ Future)

- **Current**: 512 samples via Monte Carlo; deterministic seed for audit.
- **Enhancements**:
  - Implement importance sampling: bias toward high-risk compositions.
  - Cache kernel outputs for repeated compositions.
  - Parallelize sampling across multiple threads/processes.
  - Target: <100ms for risk estimation at 1024 samples.

### 7.2 Ledger Compaction (⏱️ Future)

- **Goal**: Prevent unbounded ledger growth.
- **Steps**:
  - Implement periodic compaction: collapse old entries into Merkle checkpoints.
  - Store checkpoints in `ledger/store/checkpoints/`.
  - CI verifies checkpoint integrity.

### 7.3 Theorem Caching (⏱️ Future)

- **Goal**: Avoid re-evaluating theorems on unchanged evidence.
- **Steps**:
  - Hash evidence dict; cache theorem results by hash.
  - Invalidate cache on DSL program changes.
  - Store cache in `audit/theorem_cache.json`.

---

## Implementation Priority

### Immediate (Sprint 1-2 weeks)

1. **Wire revocation checks into Arbiter** (Phase 1.5): Runtime enforcement of manifest revocation.
2. **Sign risk_budget.yml** (Phase 2.4): Generate keypair, sign artifact, verify in CI.
3. **OCSF event logging** (Phase 5.1): Emit structured events for decisions/compositions.
4. **Governance DSL** (Phase 6.1): Formalize governance rules; CI enforcement.

### Short-Term (Sprint 2-4 weeks)

5. **Manifest signing** (Phase 3.1): Ed25519 signing for deployment manifests; CI verification.
6. **Enhanced DSL syntax** (Phase 4.1): Add quantifiers, temporal operators.
7. **Anomaly detection** (Phase 5.3): Statistical outlier detection on risk profiles.
8. **Forensic reconstruction CLI** (Phase 5.4): `forensic_trace(decision_id)` command.

### Mid-Term (1-2 months)

9. **HSM integration prep** (Phase 3.3): Abstract signing interface; implement KMS backend.
10. **Formal verification** (Phase 4.2): Export theorems to Z3; CI solver integration.
11. **Audit dashboard** (Phase 5.2): Web UI for querying ledgers/theorems.
12. **Multi-party approval** (Phase 6.2): N-of-M operator signatures for critical changes.

### Long-Term (2-6 months)

13. **Reproducible builds** (Phase 3.4): SLSA provenance; deterministic artifact hashes.
14. **Runtime theorem enforcement** (Phase 4.3): Arbiter checks theorems before decisions.
15. **Blockchain timestamping** (Phase 6.3): Publish Merkle roots to immutable timestamping service.
16. **Performance optimization** (Phase 7): Importance sampling, ledger compaction, theorem caching.

---

## Success Metrics

- **Governance**: 100% of merges pass all gates (no manual overrides).
- **Risk**: Catastrophic probability consistently < 5% (target: < 2%).
- **Supply Chain**: 100% of dependencies have verified hashes; 100% of artifacts signed.
- **Forensics**: Any decision can be reconstructed from ledgers within 5 seconds.
- **Observability**: All decisions logged with OCSF events; anomaly detection active.
- **Theorems**: 100% of critical theorems PASS in CI; runtime enforcement active.

---

## Open Questions

1. **HSM vs. Cloud KMS**: Preference for local HSM (FIPS 140-2) or cloud KMS (AWS/GCP/Azure)?
2. **Blockchain timestamping**: Use OpenTimestamps (Bitcoin) or Ethereum-based service?
3. **Formal verification tooling**: Prefer Z3 (SMT solver) or Coq/Lean (proof assistants)?
4. **Audit dashboard deployment**: Self-hosted or integrate with existing monitoring (Grafana/Datadog)?
5. **Multi-party threshold**: N-of-M for critical changes? (e.g., 2-of-3, 3-of-5?)

---

## Appendix: Current State Summary

- **Branch**: `kt/harden-api-v1`
- **Catastrophic Risk**: 0.59% (512 samples, deterministic seed 99)
- **Pre-Commit Hooks**: detect-secrets (v1.5.0), ruff, black, isort, bandit, hash-enforcement
- **CI Gates**: lint, security, supply-chain, invariants, theorems, risk budget, revocation chain
- **Ledgers**: PCEB (hash-chain), emotion drift (hash-chain), revocation (Merkle tree)
- **DSL**: Minimal proof DSL with constraints/theorems; JSON artifact export
- **Risk Budget**: YAML with optional signature verification; Arbiter enforces with safe fallback
- **Supply Chain**: requirements.lock with pip-compile hashes; multi-line aware verification
- **Kernels**: Adversarial kernels (RiskAction, Amplifier, Composition) with calibrated tail probabilities
- **PCE**: Counterfactual Engine with CVaR-based violation classes, diminishing returns, safety damping

---

**End of Roadmap**
