"""Canonical KTEngine

Phoenix Phase 1: Core Engine Unification.

Wires together the Student, Teacher, Arbiter kernels plus governance &
ledger components into a single orchestration surface. Provides a single
`execute(problem_graph)` entrypoint expected by API, benchmarks, and CLI.

Phase 2 will deepen ConstraintLattice / verification logic; for now we
include a lightweight stub to keep the spine intact.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import src.config as config
from src.algebra import constraint_lattice
from src.governance.decision_broker import DecisionBroker
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail
from src.governance.tri_governor import TriGovernor
from src.governance.verification import RollingVerifier
from src.kernels.arbiter_v47 import ArbiterKernelV47
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.primitives.dual_ledger import DualLedger

logger = logging.getLogger(__name__)


class KTEngine:
    def __init__(self) -> None:
        # Core primitives
        self.ledger = DualLedger()
        self.guardrail = DeontologicalGuardrail(config.DEONTOLOGICAL_RULES)
        self.student = StudentKernelV42(guardrail=self.guardrail)
        self.teacher = TeacherKernelV45()
        # Arbiter coordinates student/teacher & applies manifold + risk gating
        self.arbiter = ArbiterKernelV47(self.guardrail, self.ledger, self.student, self.teacher)
        # Governance layer components
        self.tri_governor = TriGovernor()
        # DecisionBroker manages a separate integrity ledger; do not pass DualLedger
        self.decision_broker = DecisionBroker()
        # Constraint lattice + verifier
        self.constraint_lattice = constraint_lattice
        self.verifier = RollingVerifier()
        logger.info("[ENGINE] KTEngine initialized (Phoenix Phase 1 stub).")

    def _build_governance_proposal(self, arbiter_result: Dict[str, Any]) -> Dict[str, Any]:
        """Derive a minimal governance proposal from arbiter output.

        Heuristic mapping until richer trace & verification implemented.
        """
        outcome = arbiter_result.get("outcome", "UNKNOWN")
        veto = outcome == "VETOED"
        proposal = {
            "tags": ["unethical"] if veto else [],
            "integrity_violation": veto,
            # Simple replay confidence placeholder (Phase 2: real trace checks)
            "replay_confidence": 0.9 if not veto else 0.4,
            # Warrant heuristic: lower if veto, higher if solved
            "warrant": 0.85 if outcome == "SOLVED" else (0.5 if veto else 0.7),
        }
        return proposal

    def execute(self, problem_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Primary orchestration method.

        Steps:
          1. Constraint lattice pre-check
          2. Arbiter adjudication (student/teacher, manifold, risk gating)
          3. Deontological guardrail structured validation
          4. TriGovernor adjudication
          5. DecisionBroker processing (commit or escrow)
        """
        if not isinstance(problem_graph, dict):
            raise ValueError("problem_graph must be a dict")

        lattice_constraints = self.constraint_lattice.parse(problem_graph)
        composable = self.constraint_lattice.is_composable([lattice_constraints])
        lattice_report = {"constraints": lattice_constraints, "composable": composable}
        if not composable:
            self.ledger.log("KTEngine", "ConstraintContradiction", lattice_constraints.get("raw"))
            return {
                "status": "CONSTRAINT_CONTRADICTION",
                "kernel": "Arbiter",
                "rationale": "Constraints are not composable",
                "final_solution": {},
                "teacher_artifact": None,
                "governance": {},
                "broker": {},
                "constraints": lattice_report,
            }
        self.ledger.log("KTEngine", "Constraints", lattice_report)

        arbiter_result = self.arbiter.adjudicate(problem_graph)

        # Structured guardrail validation (legacy tag-based) over the full arbiter result
        guardrail_pass = self.guardrail.validate(
            {"type": problem_graph.get("proposed_actions", [{}])[0].get("type")}
        ) and self.guardrail.validate_solution(problem_graph)
        if not guardrail_pass and arbiter_result.get("outcome") != "VETOED":
            arbiter_result = {
                "outcome": "VETOED",
                "reason": "Structured guardrail veto",
            }
            self.ledger.log("Guardrail", "StructuredVeto", arbiter_result.get("reason"))

        proposal = self._build_governance_proposal(arbiter_result)
        gov_decision = self.tri_governor.adjudicate(proposal)
        broker_out = self.decision_broker.process_request(gov_decision, proposal)

        # Build execution trace for verification
        trace = []
        # Student step placeholder (actual detailed result internal to Arbiter)
        student_source = arbiter_result.get("source", "Student")
        student_status = "SIT" if student_source.startswith("Teacher") else "PASS"
        trace.append({"type": "student_step", "data": {"status": student_status}})
        if student_source.startswith("Teacher"):
            trace.append(
                {
                    "type": "teacher_step",
                    "data": {"status": arbiter_result.get("data", {}).get("status", "SALVAGEABLE")},
                }
            )
        trace.append({"type": "arbiter_ruling", "data": arbiter_result})
        trace.append({"type": "governance_decision", "data": gov_decision})
        trace_valid = self.verifier.verify_trace(trace)
        if not trace_valid:
            self.ledger.log("Verifier", "InvalidTrace", {"len": len(trace)})
            arbiter_result = {
                "outcome": "VETOED",
                "reason": "Trace verification failed",
            }

        # Lattice verification on solution/governance risk
        lattice_ok = self.constraint_lattice.verify(
            {"governance": gov_decision, "outcome": arbiter_result.get("outcome")},
            lattice_constraints,
        )
        if not lattice_ok and arbiter_result.get("outcome") != "VETOED":
            arbiter_result = {"outcome": "VETOED", "reason": "Risk bound violation"}
            self.ledger.log("KTEngine", "RiskBoundVeto", lattice_constraints.get("risk_bounds"))

        # Assemble canonical response surface expected by API / benchmarks
        response = {
            "status": arbiter_result.get("outcome", "UNKNOWN"),
            "kernel": "Arbiter",
            "rationale": arbiter_result.get("reason") or gov_decision.get("decision"),
            "final_solution": arbiter_result,
            "teacher_artifact": None,
            "governance": gov_decision,
            "broker": broker_out,
            "constraints": lattice_report,
            "trace_valid": trace_valid,
            "lattice_ok": lattice_ok,
        }
        self.ledger.log(
            "KTEngine",
            "Finalize",
            {"status": response["status"], "decision": gov_decision.get("decision")},
        )
        return response
