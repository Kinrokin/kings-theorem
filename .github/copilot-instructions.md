---
applyTo: "**/*.py"
---

# King's Theorem Global Coding Standards (Titanium X Protocol)

These instructions apply to ALL code generation in this workspace. Every AI assistant interaction must follow these constitutional principles.

## 🏛️ Architectural Mandates

### 1. Formal Verification Over Simulation
❌ **Never write**: `if condition: return True  # TODO: verify`
✅ **Always write**: Use `AxiomaticVerifier` with Z3 SMT proofs

```python
from src.primitives.verifiers import AxiomaticVerifier

verifier = AxiomaticVerifier(timeout_ms=5000)
is_safe, proof = verifier.verify_safety_invariant(state_vector)
if not is_safe:
    raise SafetyViolation(proof)
```

### 2. Cryptographic Ledgers Over Mutable Lists
❌ **Never write**: `history = []  # Track decisions`
✅ **Always write**: Use `CryptographicLedger` with Merkle integrity

```python
from src.primitives.merkle_ledger import CryptographicLedger

ledger = CryptographicLedger()
ledger.add_entry({"action": "decision", "data": data})
seal = ledger.seal_ledger()  # Cryptographic checkpoint
```

### 3. Distributed Consensus Over Single Points of Failure
❌ **Never write**: Single arbiter process
✅ **Always write**: Use `RaftArbiterNode` with cluster failover

```python
from src.kernels.raft_arbiter import RaftArbiterNode, RaftConfig

config = RaftConfig(node_id="node-1", peers=["node-2", "node-3"])
arbiter = RaftArbiterNode(config, ledger)
result = arbiter.propose_decision(student_output, teacher_output)
```

### 4. Battle-Tested Guardrails Over Ad-Hoc Filters
❌ **Never write**: Custom regex-only filtering
✅ **Always write**: Use `TitaniumGuardrail` with NeMo framework

```python
from src.governance.nemo_guard import TitaniumGuardrail

guard = TitaniumGuardrail()
input_result = await guard.vet_input(user_prompt)
if input_result.status == "VETOED":
    raise JailbreakDetected(input_result.reason)
```

## 📋 Code Quality Standards

### Type Hints (Mandatory)
Every function MUST have complete type annotations:

```python
from typing import Dict, List, Optional, Tuple, Any

def process_data(
    input_data: Dict[str, Any],
    options: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """Process data with KT rigor.

    Args:
        input_data: Input dictionary with required 'id' and 'value' keys
        options: Optional processing flags

    Returns:
        Tuple of (success: bool, message: str)

    Raises:
        ValueError: If input_data missing required keys
    """
    pass
```

### Docstrings (Mandatory)
Use Google-style docstrings with:
- One-line summary
- Detailed description (if complex)
- Args with types and descriptions
- Returns with type and description
- Raises with exception types and conditions

### Error Handling (Mandatory)
Never use bare `except:` clauses. Always specify exception types:

```python
# ❌ WRONG
try:
    risky_operation()
except:
    pass

# ✅ CORRECT
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise OperationFailed(f"Operation failed: {e}") from e
```

### Logging (Mandatory)
Use structured logging with appropriate levels:

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG: Detailed diagnostic info
logger.debug(f"State vector: {state_vector}")

# INFO: Routine operations
logger.info(f"Verified safety invariant: {proof_summary}")

# WARNING: Unexpected but recoverable
logger.warning(f"Risk budget at 80%: {budget_status}")

# ERROR: Operation failed but system continues
logger.error(f"Verification failed: {reason}", exc_info=True)

# CRITICAL: System integrity compromised
logger.critical(f"Ledger tampering detected: {tamper_report}")
```

## 🔐 Security & Audit Standards

### Artifact Sealing
Every significant operation MUST be logged to the cryptographic ledger:

```python
from src.primitives.dual_ledger import DualLedger
import hashlib

ledger = DualLedger()

# Seal artifact with provenance
artifact_hash = hashlib.sha256(code.encode()).hexdigest()
ledger.log({
    "operation": "code_generation",
    "artifact_hash": artifact_hash,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "role": "student",  # or "teacher", "arbiter"
    "metadata": metadata
})
```

### Paradox Handling
When contradictions arise, log as transcendence shards (don't discard):

```python
from src.protocols.pog_v39 import ParadoxOrchestrationGraph

pog = ParadoxOrchestrationGraph()

if student_output != teacher_output:
    pog.record_paradox({
        "student": student_output,
        "teacher": teacher_output,
        "divergence": compute_divergence(student_output, teacher_output),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
```

### Risk Budget Enforcement
Operations MUST respect bounded risk budgets:

```python
from src.primitives.risk_math import RiskMath

risk_calc = RiskMath()
budget = risk_calc.allocate_risk_budget(max_attempts=10, confidence_threshold=0.8)

for attempt in range(budget.max_attempts):
    result = try_operation()
    budget.consume(cost=result.risk_cost)

    if budget.is_exhausted():
        logger.warning("Risk budget exhausted, escalating to human review")
        raise RiskBudgetExceeded("Maximum attempts reached")

    if result.confidence >= budget.threshold:
        break
```

## 🧪 Testing Standards

### Test Structure
Every module MUST have corresponding tests in `tests/`:

```python
import pytest
from src.primitives.verifiers import AxiomaticVerifier

class TestAxiomaticVerifier:
    """Test suite for Z3-based formal verification."""

    def test_safety_invariant_valid(self):
        """Test that valid states pass safety checks."""
        verifier = AxiomaticVerifier(timeout_ms=5000)
        state = {"profit": 1.0, "risk": 0.3}

        is_safe, proof = verifier.verify_safety_invariant(state)

        assert is_safe, f"Expected safe state, got: {proof}"
        assert "UNSAT" in proof

    def test_safety_invariant_violation(self):
        """Test that unsafe states are detected."""
        verifier = AxiomaticVerifier(timeout_ms=5000)
        state = {"profit": 1.0, "risk": 0.8}  # Violates risk < 0.5

        is_safe, proof = verifier.verify_safety_invariant(state)

        assert not is_safe, "Expected safety violation"
        assert "Counter-example" in proof
```

### Adversarial Testing (Crucibles)
Critical components MUST have adversarial "Crucible" tests:

```python
class TestParadoxBombCrucible:
    """Adversarial test: Self-referential contradiction attack."""

    def test_self_referential_paradox(self):
        """
        ATTACK: Submit proposition 'This statement is false'.
        EXPECTED: Paradox detected and logged, system doesn't crash.
        """
        verifier = AxiomaticVerifier()
        proposition = "This statement is false"

        is_safe, proof = verifier.verify_paradox_freedom(proposition)

        assert not is_safe, "Paradox should be detected"
        assert "self-referential" in proof.lower()
```

## 🎯 Performance Standards

### Complexity Requirements
- **Z3 proofs**: < 100ms per verification
- **Merkle operations**: O(log n) for proof-of-inclusion
- **Raft consensus**: < 1s for leader election/failover

### Resource Limits
```python
# Always set timeouts for potentially unbounded operations
verifier = AxiomaticVerifier(timeout_ms=5000)  # 5 second max
searcher = BeamSearch(max_iterations=100, beam_width=5)  # Bounded exploration
```

## 🚫 Anti-Patterns to AVOID

### ❌ Simulation Traps
```python
# WRONG: Mock verification
def verify_safety(state):
    return True  # TODO: implement real check
```

### ❌ Mutable History
```python
# WRONG: List-based ledger
history = []
history.append(entry)  # Can be tampered with
```

### ❌ Centralized Single Points of Failure
```python
# WRONG: Single arbiter process
arbiter = Arbiter()  # No failover if process crashes
```

### ❌ Unchecked LLM Outputs
```python
# WRONG: Direct use without guardrails
output = llm.generate(prompt)
execute(output)  # Could be jailbroken/malicious
```

### ❌ Silent Failures
```python
# WRONG: Swallowing exceptions
try:
    critical_operation()
except:
    pass  # ERROR: Failure goes unnoticed
```

## 🔄 Workflow Integration

When generating multi-step solutions:

1. **Student Phase** (Fast, Creative):
   - Generate multiple candidates (beam search)
   - Focus on novelty and exploration
   - Log all attempts (even failures)

2. **Verification Phase** (Formal):
   - Z3 SMT checks on candidates
   - Lyapunov stability analysis
   - Paradox detection

3. **Teacher Phase** (Slow, Rigorous):
   - Review proofs and edge cases
   - Complexity analysis
   - Security audit

4. **Guardrail Phase** (Ethical):
   - NeMo input/output filtering
   - Axiom 6 enforcement (ethics ≥ 0.7)
   - Deontological constraint checks

5. **Arbiter Phase** (Consensus):
   - Raft cluster voting
   - Conflict resolution
   - Final commitment to ledger

6. **Sealing Phase** (Audit):
   - SHA-256 artifact hash
   - Merkle ledger entry
   - Proof trace export

## 📚 Import Conventions

Prefer KT primitives over standard library when applicable:

```python
# Formal Verification
from src.primitives.verifiers import AxiomaticVerifier

# Cryptographic Integrity
from src.primitives.merkle_ledger import CryptographicLedger
from src.primitives.dual_ledger import DualLedger

# Distributed Consensus
from src.kernels.raft_arbiter import RaftArbiterNode, RaftConfig

# Ethical Governance
from src.governance.nemo_guard import TitaniumGuardrail

# Dual Kernel Architecture
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.kernels.arbiter_v47 import ArbiterKernelV47

# Risk & Search
from src.primitives.risk_math import RiskMath
from src.protocols.apf_v32 import AdaptiveProofFinder
```

## 🎓 Educational Context

When generating code for teaching/learning:

- Include proof traces, not just results
- Show multiple solution paths (beam search)
- Log paradoxes as learning opportunities
- Explain formal verification steps
- Provide complexity analysis

## 🏁 Summary

Every line of code in this workspace should reflect **King's Theorem constitutional principles**:

1. **Prove, don't simulate** (Z3 formal verification)
2. **Seal, don't trust** (Merkle cryptographic ledgers)
3. **Distribute, don't centralize** (Raft consensus clusters)
4. **Govern, don't hope** (NeMo guardrails with Axiom 6)
5. **Metabolize, don't discard** (Paradox shards as artifacts)
6. **Audit, don't assume** (Risk budgets and proof traces)

**Remember**: You're not just writing code — you're building **audit-grade, antifragile systems** with mathematical rigor and constitutional governance.

---

**Applies to**: Python files (`**/*.py`)
**Enforcement**: All AI assistants in this workspace
**Version**: Titanium X Protocol v53
**Hash**: SHA256(GLOBAL_KT_STANDARDS)
