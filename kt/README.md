# King's Theorem - Phoenix Edition

**Version 6.0.0** - Production-ready neuro-symbolic theorem proving orchestrator

## Overview

King's Theorem is a rigorous theorem proving engine that separates three concerns:

1. **Prover** (Creative/LLM) - Generates candidate proof steps
2. **Verifier** (Symbolic/Z3) - Validates logical correctness
3. **Supervisor** (Risk Management) - Enforces resource budgets

This architecture ensures:
- **Creativity** from LLMs without hallucination risk
- **Rigor** from symbolic verification (Z3/Lean)
- **Safety** from strict resource budgets and backtracking

## Architecture

```
kt/
├─ src/kt_core/          # Core engine modules
│  ├─ orchestrator.py    # Central nervous system
│  ├─ prover.py          # LLM interface (stub)
│  ├─ verifier.py        # Z3 symbolic verifier
│  ├─ context.py         # Logic statements & trace
│  ├─ risk.py            # Budget enforcement
│  ├─ artifacts.py       # Status types
│  └─ telemetry.py       # Structured logging
├─ tests/                # Comprehensive test suite
├─ examples/             # Demo scripts
└─ pyproject.toml        # Package configuration
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with optional dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
import asyncio
from kt_core import Orchestrator, LLMProver, Z3Verifier, RiskBudget

async def main():
    # Initialize components
    prover = LLMProver()
    verifier = Z3Verifier()
    orch = Orchestrator(prover, verifier)

    # Set resource budget
    budget = RiskBudget(max_depth=6, max_tokens=1000, timeout_sec=5.0)

    # Attempt proof
    status, trace = await orch.solve(
        "For all integers n, if n is even then n² is even.",
        budget
    )

    print(f"Status: {status}")
    print(f"Steps: {len(trace.steps)}")

asyncio.run(main())
```

## Running the Demo

```bash
python examples/demo_even_square.py
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_verifier_z3.py -v

# Run with coverage
pytest --cov=kt_core
```

## Key Features

### 1. Risk Budget Enforcement
Prevents infinite loops and resource waste:
- `max_tokens`: LLM token limit
- `max_depth`: Recursion depth limit
- `timeout_sec`: Wall-clock time limit

### 2. Cryptographic Seal Chain
Every proof step is hashed (SHA-256) and chained for tamper-evident provenance.

### 3. Symbolic Verification
All proof steps must pass Z3 SAT checks before acceptance - no hallucinations.

### 4. Backtracking
Rejects invalid steps and backtracks on repeated failures.

### 5. Structured Telemetry
Rich console logging with event tracking:
- `verified_step`
- `rejected_step`
- `budget_halt`
- `prover_error`
- `verifier_error`

## Status Types

```python
ProofStatus = Literal[
    "PENDING",         # Not started
    "GENERATING",      # Prover generating steps
    "VERIFYING",       # Verifier checking validity
    "PROVEN",          # Successfully completed
    "REFUTED",         # Found contradiction
    "HALTED_BUDGET",   # Resource limit exceeded
    "ERROR",           # Runtime error
]
```

## Test Coverage

- ✅ `test_verifier_z3.py` - SAT/UNSAT verification
- ✅ `test_risk.py` - Budget exhaustion (tokens, depth, timeout)
- ✅ `test_artifacts.py` - Seal chain integrity
- ✅ `test_orchestrator.py` - End-to-end proof attempts

## Future Roadmap

- [ ] Lean 4 integration for math-heavy proofs
- [ ] Heuristic search strategies (A*, beam search)
- [ ] Real LLM API integration (OpenAI, Anthropic)
- [ ] Distributed orchestration (Ray/Kubernetes)
- [ ] Interactive proof assistant mode
- [ ] Crucible runner for paradox metabolism

## Architecture Principles

1. **Separation of Concerns** - Prover, Verifier, Supervisor are independent
2. **Type Safety** - Pydantic models and type hints throughout
3. **Immutability** - LogicStatements are frozen dataclasses
4. **Testability** - All interfaces have working stubs
5. **No Network** - Pure in-memory prototype (for now)

## License

Proprietary - King's Theorem Project

## Contact

For questions or contributions, contact the Architect.
