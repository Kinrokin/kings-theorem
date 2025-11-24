# Arbitration Kernel (Lexicographic Meta-Governor) — Design & API

This document specifies the API contract, core data structures, and pseudocode for the Formal Arbitration Kernel used by King's Theorem (KT-v32).

## Goals
- Enforce lexicographic priority of invariants, safety (LTL), ethics, then utility.
- Provide bounded quorum escalation (<= 800 ms) and a regret-minimizing tie-breaker.
- Expose a small API for the DecisionBroker to reserve and resolve warrants.

## Data Structures

Warrant {
  id: str
  agent_id: str
  action: str
  confidence: float
  ethics_score: float
  ltl_assertions: list[str]
  metadata: dict
}

QuorumConfig {
  N: int
  K: int
  correlation_rho: float
}

Resolution {
  chosen_warrant: Warrant
  reason: str
  diagnostics: dict
}

## API

class ArbitrationKernel:
  def propose_warrant(self, warrant: Warrant) -> str
    # returns a short-lived token representing acknowledgement and queue position

  def resolve_conflict(self, tokens: list[str], timeout_ms: int = 800) -> Resolution
    # resolves a set of competing warrants referenced by tokens using lexicographic rules

  def register_module(self, module_id: str, reliability_score: float) -> None
    # modules provide warrants; kernel tracks reliability for regret-minimizing routing

## Pseudocode: resolve_warrant_conflict

1. Gather Warrants from tokens
2. Compute number of satisfied LTL assertions for each Warrant
3. Choose warr with max(LTL_count)
4. If tie on LTL_count: choose by ethics_score
5. If still tied: consult reliability-weighted UCB ranking of modules
6. If perfect symmetry: apply Tie-Break Axiom favoring reversibility

## Quorum Escalation
- If two warrants are high-confidence but conflicting, spawn a bounded quorum vote across authorized signatories using `QuorumConfig`. If quorum not reached within `timeout_ms`, default to safe abstention.

## Integration Points
- DecisionBroker: call `propose_warrant` and, if required, call `resolve_conflict` before precommit.
- IntegrityLedger: receives finalized resolution and audit metadata.

## Notes
- This document is intentionally compact; code skeletons should follow the API here. Unit tests must cover tie scenarios, quorum timeouts, and UCB routing behavior.
