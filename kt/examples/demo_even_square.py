"""
Demo: Even Square Theorem

Proves: For all integers n, if n is even then n² is even.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from kt_core.orchestrator import Orchestrator
from kt_core.prover import LLMProver
from kt_core.risk import RiskBudget
from kt_core.telemetry import Telemetry
from kt_core.verifier import Z3Verifier


async def main():
    """Run the even square theorem demo."""
    print("=" * 70)
    print("KING'S THEOREM - NEURO-SYMBOLIC ORCHESTRATOR")
    print("Phoenix Edition v6.0.0")
    print("=" * 70)
    print()

    # Initialize components
    prover = LLMProver()
    verifier = Z3Verifier()
    telemetry = Telemetry(fields={"demo": "even_square"})
    orchestrator = Orchestrator(prover, verifier, telemetry)

    # Define theorem
    theorem = "For all integers n, if n is even then n² is even."
    print(f"THEOREM: {theorem}")
    print()

    # Set resource budget
    budget = RiskBudget(max_depth=6, max_tokens=1000, timeout_sec=5.0)
    print(f"BUDGET: depth={budget.max_depth}, tokens={budget.max_tokens}, timeout={budget.timeout_sec}s")
    print()
    print("-" * 70)
    print()

    # Attempt proof
    status, trace = await orchestrator.solve(theorem, budget)

    # Report results
    print()
    print("=" * 70)
    print(f"FINAL STATUS: {status}")
    print("=" * 70)
    print()

    print(f"PROOF TRACE ({len(trace.steps)} steps):")
    print("-" * 70)
    for i, step in enumerate(trace.steps):
        print(f"\n[{i}] {step.source} (confidence={step.confidence:.2f})")
        print(f"    ID: {step.id}")
        print(f"    Content: {step.content}")
        if step.formal:
            print("    Formal:")
            for line in step.formal.split("\n"):
                print(f"        {line}")

    print()
    print("-" * 70)
    print(f"SEAL CHAIN: {trace.metadata.get('seal_chain', 'N/A')[:80]}...")
    print("-" * 70)
    print()

    print("Resources consumed:")
    print(f"  - Tokens: {budget.tokens_used}/{budget.max_tokens}")
    print(f"  - Depth: {budget.current_depth}/{budget.max_depth}")
    print(f"  - Time: {budget._start:.2f}s")
    print()


if __name__ == "__main__":
    asyncio.run(main())
