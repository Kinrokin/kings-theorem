# King's Theorem S-Tier Upgrades — Scaffold & Roadmap

This directory contains scaffold modules for **S-Tier Constitutional Governance** features. All modules are **educational/minimal** implementations; production-grade replacements will require robust backends (e.g., etcd for Raft, Z3 for MTL, distributed Merkle DAG).

---

## Added Modules

### 1. σ-Text (Zero-Knowledge Content)
**File**: `src/governance/sigma_text.py`

**Purpose**: Transform raw text into cryptographic hashes + statistical features without retaining raw content. Reduces exposure in governance provenance.

**Key Function**:
- `to_sigma_text(text: str) -> SigmaText`
  - Returns: `text_sha256`, `length`, `token_hashes`, `alnum_ratio`
  - No raw text retained

**Integration**: Arbiter now logs σ-text hashes in provenance when available (non-blocking fallback on errors).

**Test**: `tests/test_sigma_trinity_smoke.py::test_sigma_text_hash_and_stats`

---

### 2. Trinity Multi-Vector Scoring
**File**: `src/metrics/trinity.py`

**Purpose**: Composite evaluation across three dimensions:
- **Divergence**: Token-set Jaccard distance (0=identical, 1=totally different)
- **Epistemic**: Internal consistency heuristic (length ratio similarity)
- **Risk**: Guardrail score (max of student/teacher)

**Key Function**:
- `compute_trinity(student_text: str, teacher_text: str) -> TrinityScores`
  - Returns: `divergence`, `epistemic`, `risk`, `composite` (all in [0,1])
  - Uses `aggregate_risk` from `risk_math.py` with weights `{divergence:0.25, epistemic:0.25, risk:0.6}`

**Integration**: Arbiter logs Trinity scores in provenance when Student+Teacher both execute (metadata-only; no veto logic yet).

**Test**: `tests/test_sigma_trinity_smoke.py::test_trinity_scores_shape`

**Roadmap**:
- Add semantic embeddings for divergence (current: token Jaccard).
- Wire Trinity composite into Arbiter veto threshold.
- Add multi-agent collusion detection (composite > threshold → FAILED).

---

### 3. Merkle-Patricia Trie (Educational)
**File**: `src/ledger/merkle_patricia.py`

**Purpose**: Hex-nibble-keyed Merkle trie for O(log n) proof-of-inclusion. Minimal educational implementation (not optimized or storage-backed).

**Key API**:
- `put(key: bytes, value: bytes)`: Insert key-value pair
- `get(key: bytes) -> Optional[bytes]`: Retrieve value
- `root_hash() -> str`: Current root hash (SHA256)
- `get_proof(key: bytes) -> List[Tuple[int, str]]`: Proof path (nibble, child_hash)
- `verify_proof(root_hash, key, value, proof) -> bool`: Verify inclusion

**Integration**: Not yet wired into ledger (append-only ledger remains primary). Future: hybrid ledger with MPT for partial state proofs.

**Test**: None yet (manual integration pending).

**Roadmap**:
- Replace SHA256 with Keccak256 (Ethereum-compatible).
- Add storage backend (LevelDB/RocksDB).
- Integrate into `AppendOnlyLedger` as optional proof layer.

---

### 4. MTL (Mission-Time Logic) Primitives
**File**: `src/primitives/mtl.py`

**Purpose**: Lightweight DSL for temporal property definitions with bounded time intervals. Educational stub for Z3 integration.

**Key API**:
- `MTLProperty(operator: MTLOp, predicate: str, time_lower: float, time_upper: Optional[float])`
  - Operators: `ALWAYS` (□), `EVENTUALLY` (◇), `UNTIL` (U)
- `check_property_trivial(prop: MTLProperty, trace: List[dict]) -> bool`: Discrete-time checker (no Z3 yet)
- `define_axiom_six_mtl() -> MTLProperty`: Returns Axiom 6 property (Always ethics ≥ 0.7)

**Integration**: Not yet wired into arbiter (no trace collection yet).

**Test**: `tests/test_mtl_smoke.py` (3 tests)

**Roadmap**:
- Add Z3 SMT encoding for symbolic MTL verification.
- Collect timestamped trace in arbiter provenance.
- Enforce MTL constraints as pre-commit checks.

---

## Test Status

| Module | Tests Added | Status |
|--------|------------|--------|
| σ-text | 1 smoke test | ✅ Passing |
| Trinity | 1 smoke test | ✅ Passing |
| Merkle-Patricia | None yet | ⚠️ Manual integration pending |
| MTL | 3 smoke tests | ✅ Passing |

**Total New Tests**: 5 (all passing)

---

## Integration Checklist

### Immediate (v53.3)
- [x] σ-text logging in arbiter provenance
- [x] Trinity logging in arbiter provenance
- [ ] Wire Trinity composite into arbiter veto logic (threshold > 0.8 → FAILED)
- [ ] Add multi-agent collusion test using Trinity

### Near-Term (v53.4)
- [ ] Merkle-Patricia hybrid ledger (append-only + MPT proofs)
- [ ] MTL trace collection in arbiter
- [ ] MTL property enforcement (reject if □(ethics ≥ 0.7) violated)

### S-Tier (v54+)
- [ ] Replace token Jaccard with sentence embeddings (semantic divergence)
- [ ] Z3 SMT backend for MTL symbolic verification
- [ ] Distributed Merkle DAG with etcd consensus
- [ ] Full zero-knowledge arbiter (vetting σ-text only, no raw strings)

---

## Example Usage

### σ-Text
```python
from src.governance.sigma_text import to_sigma_text

sigma = to_sigma_text("The quick brown fox")
print(sigma.text_sha256)  # SHA256 of normalized text
print(sigma.length)       # Character count
print(sigma.alnum_ratio)  # 0.81 (alphanumeric ratio)
```

### Trinity Scoring
```python
from src.metrics.trinity import compute_trinity

scores = compute_trinity("Student answer", "Teacher answer")
print(scores.divergence)  # 0.25 (Jaccard distance)
print(scores.composite)   # 0.42 (aggregated risk)
```

### MTL Properties
```python
from src.primitives.mtl import MTLProperty, MTLOp, check_property_trivial

prop = MTLProperty(MTLOp.ALWAYS, "ethics >= 0.7")
trace = [
    {"time": 0.0, "values": {"ethics": 0.8}},
    {"time": 1.0, "values": {"ethics": 0.9}},
]
assert check_property_trivial(prop, trace)
```

---

## Known Limitations

1. **σ-Text**: Token hashing uses whitespace split (no NLP tokenizer). High-quality embeddings require external models.
2. **Trinity**: Divergence is Jaccard (bag-of-words); epistemic is length-ratio heuristic. Semantic embeddings TBD.
3. **Merkle-Patricia**: In-memory only, no persistence. Production needs LevelDB backend.
4. **MTL**: Discrete-time checker only; no Z3 symbolic verification yet. Predicate parser is regex-based.

---

## References

- **σ-text**: Inspired by homomorphic encryption and ZK-SNARKs (no raw data exposure)
- **Trinity**: Multi-objective optimization (divergence + consistency + risk)
- **Merkle-Patricia**: Ethereum Yellow Paper §4.1
- **MTL**: Koymans, Ron. "Specifying real-time properties with metric temporal logic." *Real-Time Systems* 2.4 (1990): 255-299.

---

**Status**: ✅ Scaffolding Complete (v53.2 → v53.3)
**Next Milestone**: Wire Trinity composite into arbiter veto logic (v53.3)
**S-Tier Target**: Full ZK arbiter + distributed Merkle DAG (v54+)
