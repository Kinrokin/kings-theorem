# King's Theorem Formal Proofs

This directory contains formal specifications and proofs for King's Theorem's safety properties using the Lean 4 theorem prover.

## Files

- `kt_safety.lean` - Core lattice properties, closure, monotonicity, and safety invariants

## Setup

### Install Lean 4

**macOS/Linux:**
```bash
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
```

**Windows:**
```powershell
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.ps1 -OutFile elan-init.ps1
.\elan-init.ps1
```

### Install Mathlib

```bash
cd theorem
lake init kt_proofs
lake update
```

### Verify Proofs

```bash
lean --version
lake build
```

## Formalized Properties

Currently formalized (with proof skeletons):

✅ **Lattice Properties:**
- Idempotence: `meet(c, c) = c`
- Commutativity: `meet(c1, c2) = meet(c2, c1)`
- Associativity: `meet(meet(c1, c2), c3) = meet(c1, meet(c2, c3))`
- Absorption laws

✅ **Closure:**
- Meet/Join operations preserve constraint set membership

✅ **Monotonicity:**
- Strength ordering preserved under meet

✅ **Safety Invariants:**
- Constraint strength always in [0.0, 1.0]

## Future Work

### High Priority (Q1 2026)
1. Complete proof implementations (replace `sorry` with actual proofs)
2. Formalize constraint expression AST
3. Add conflict detection proofs
4. Prove composability transitivity

### Medium Priority (Q2 2026)
1. Ethical manifold convex projection correctness
2. Minimal distance property for projection
3. Proof system meta-properties (no cycles, DAG structure)
4. Counterfactual engine completeness

### Long Term
1. Full system correctness theorem
2. Byzantine fault tolerance proofs
3. Probabilistic safety bounds
4. Integration with TLA+ for concurrent properties

## Contributing

When adding new theorems:
1. Add type signatures first
2. Write informal proof sketch in comments
3. Implement formal proof
4. Add unit tests in `kt_safety_test.lean` (future)
5. Update this README

## References

- [Lean 4 Documentation](https://leanprover.github.io/lean4/doc/)
- [Mathlib 4 Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Theorem Proving in Lean 4](https://leanprover.github.io/theorem_proving_in_lean4/)

## License

MIT License - See LICENSE file in repository root
