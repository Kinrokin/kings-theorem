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
from dataclasses import dataclass, field
from typing import Any, Dict, List

import src.config as config
from src.algebra import constraint_lattice
from src.governance.decision_broker import DecisionBroker
from src.governance.nemo_guard import DeontologicalGuardrail
from src.governance.risk_budget import RiskThresholds, load_risk_budget
from src.governance.tri_governor import TriGovernor
from src.governance.verification import RollingVerifier
from src.kernels.arbiter_v47 import ArbiterKernelV47
from src.kernels.student_v42 import StudentKernelV42
from src.kernels.teacher_v45 import TeacherKernelV45
from src.primitives import risk_math
from src.primitives.merkle_ledger import MerkleLedger
from src.utils.gov_config import gov_config

logger = logging.getLogger(__name__)


@dataclass
class EpisodeTraceEvent:
    phase: str
    name: str
    status: str
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EpisodeState:
    problem_id: str
    problem_graph: Dict[str, Any]
    student_out: Dict[str, Any] = field(default_factory=dict)
    teacher_out: Dict[str, Any] = field(default_factory=dict)
    guardrail_decision: Dict[str, Any] = field(default_factory=dict)
    lattice_info: Dict[str, Any] = field(default_factory=dict)
    trigovernor_decision: Dict[str, Any] = field(default_factory=dict)
    broker_decision: Dict[str, Any] = field(default_factory=dict)
    risk_components: Dict[str, float] = field(default_factory=dict)
    risk_aggregate: float = 0.0
    risk_tier: str = "LOW"
    trace: List[EpisodeTraceEvent] = field(default_factory=list)


class KTEngine:
    def __init__(self) -> None:
        # Core primitives
        self.ledger = MerkleLedger()
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
        self.risk_thresholds: RiskThresholds = load_risk_budget()
        self.risk_weights = dict(self.risk_thresholds.weights)
        logger.info("[ENGINE] KTEngine initialized (Phoenix Phase 1 stub).")

    def _record_trace_event(
        self,
        episode: EpisodeState,
        phase: str,
        name: str,
        status: str,
        meta: Dict[str, Any] | None = None,
    ) -> None:
        episode.trace.append(EpisodeTraceEvent(phase=phase, name=name, status=status, meta=dict(meta or {})))

    def _derive_constraint_tension(self, lattice_constraints: Dict[str, Any]) -> float:
        bounds = lattice_constraints.get("risk_bounds", [])
        if not bounds:
            return 0.0
        return max(0.0, min(1.0, min(bounds) / 100.0))

    def _collect_metrics(self, problem_graph: Dict[str, Any]) -> Dict[str, Any]:
        tags = [str(tag).lower() for tag in problem_graph.get("metadata", {}).get("tags", [])]
        components = {
            "anomaly_replay": 1.0 if "replay_alert" in tags else 0.0,
            "anomaly_flood": 1.0 if "flood_alert" in tags else 0.0,
            "spectral_correlation": 1.0 if "spectral_alert" in tags else 0.0,
        }
        events: List[EpisodeTraceEvent] = []
        for name, score in components.items():
            if score:
                events.append(
                    EpisodeTraceEvent(
                        phase="METRICS",
                        name=name,
                        status="ALERT",
                        meta={"score": score},
                    )
                )
        return {"risk_components": components, "trace_events": events}

    @staticmethod
    def _risk_tier(risk_score: float) -> str:
        if risk_score >= 0.8:
            return "CATASTROPHIC"
        if risk_score >= 0.4:
            return "SEVERE"
        if risk_score >= 0.2:
            return "MODERATE"
        return "LOW"

    def _enforce_risk_budget(self, episode: EpisodeState, decision: Dict[str, Any]) -> Dict[str, Any]:
        updated = dict(decision)
        risk = episode.risk_aggregate
        cat_limit = self.risk_thresholds.catastrophic.get("max_prob", 1.0)
        sev_limit = self.risk_thresholds.severe.get("max_prob", 1.0)
        if risk >= cat_limit:
            updated["decision"] = "TIER_5_HALT"
            updated["reason"] = "Catastrophic risk budget exceeded"
            self._record_trace_event(
                episode,
                phase="RISK",
                name="Budget",
                status="TIER_5_HALT",
                meta={"risk": risk},
            )
            return updated
        if risk >= sev_limit and updated.get("decision") == "EXECUTE":
            updated["decision"] = "FREEZE"
            updated["reason"] = "Severe risk budget threshold"
            self._record_trace_event(
                episode,
                phase="RISK",
                name="Budget",
                status="FREEZE",
                meta={"risk": risk},
            )
        return updated

    @staticmethod
    def _export_trace(episode: EpisodeState) -> List[Dict[str, Any]]:
        return [{"phase": ev.phase, "name": ev.name, "status": ev.status, "meta": ev.meta} for ev in episode.trace]

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

        episode = EpisodeState(
            problem_id=str(problem_graph.get("problem_id", "UNKNOWN")),
            problem_graph=problem_graph,
        )

        lattice_constraints = self.constraint_lattice.parse(problem_graph)
        composable = self.constraint_lattice.is_composable([lattice_constraints])
        lattice_report = {"constraints": lattice_constraints, "composable": composable}
        episode.lattice_info = lattice_report
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
                "risk": {"components": {}, "aggregate": 0.0, "tier": "LOW"},
                "trace": self._export_trace(episode),
            }
        self.ledger.log("KTEngine", "Constraints", lattice_report)

        arbiter_result = self.arbiter.adjudicate(problem_graph)
        source = str(arbiter_result.get("source", "Student"))
        data_blob = arbiter_result.get("data") or {}
        if source.lower().startswith("student"):
            episode.student_out = data_blob
            student_status = data_blob.get("status", "PASS")
            self._record_trace_event(
                episode,
                phase="STUDENT",
                name=source,
                status=student_status,
                meta={"model": data_blob.get("model_used")},
            )
        else:
            episode.student_out = {}
            self._record_trace_event(
                episode,
                phase="STUDENT",
                name="StudentKernelV42",
                status="SIT",
                meta={},
            )
            episode.teacher_out = data_blob
            self._record_trace_event(
                episode,
                phase="TEACHER",
                name=source,
                status=data_blob.get("status", "SALVAGEABLE"),
                meta={},
            )

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

        guardrail_status = "PASS" if guardrail_pass else "VETO"
        episode.guardrail_decision = {"ok": guardrail_pass, "reason": arbiter_result.get("reason")}
        self._record_trace_event(
            episode,
            phase="GUARDRAIL",
            name="DeontologicalGuardrail",
            status=guardrail_status,
            meta={"reason": episode.guardrail_decision.get("reason")},
        )
        episode.risk_components["guardrail_violation"] = 0.0 if guardrail_pass else 1.0

        constraint_tension = self._derive_constraint_tension(lattice_constraints)
        episode.risk_components["constraint_tension"] = constraint_tension

        metrics_info = self._collect_metrics(problem_graph)
        episode.risk_components.update(metrics_info.get("risk_components", {}))
        for ev in metrics_info.get("trace_events", []):
            self._record_trace_event(episode, ev.phase, ev.name, ev.status, ev.meta)

        proposal = self._build_governance_proposal(arbiter_result)

        warrant_score = float(proposal.get("warrant", 1.0))
        warrant_threshold = max(1e-6, gov_config.get_warrant_threshold())
        warrant_deficit = max(0.0, warrant_threshold - warrant_score)
        normalized_warrant_risk = min(1.0, warrant_deficit / warrant_threshold)
        episode.risk_components["low_warrant"] = normalized_warrant_risk

        episode.risk_aggregate = risk_math.aggregate_risk(episode.risk_components, self.risk_weights)
        episode.risk_tier = self._risk_tier(episode.risk_aggregate)

        proposal.update(
            {
                "constraint_tension": constraint_tension,
                "aggregate_risk": episode.risk_aggregate,
                "risk_tier": episode.risk_tier,
            }
        )

        gov_decision = self.tri_governor.adjudicate(proposal)
        self._record_trace_event(
            episode,
            phase="TRIGOVERNOR",
            name="TriGovernor",
            status=gov_decision.get("decision", "UNKNOWN"),
            meta={"risk_score": gov_decision.get("risk_score")},
        )

        gov_decision = self._enforce_risk_budget(episode, gov_decision)
        episode.trigovernor_decision = gov_decision

        halted_by_risk = gov_decision.get("decision") in {"TIER_5_HALT", "HALT"}
        if halted_by_risk:
            broker_out = {
                "status": "SKIPPED",
                "reason": "Risk budget enforced halt",
                "tier": gov_decision.get("decision"),
            }
            episode.broker_decision = broker_out
            self._record_trace_event(
                episode,
                phase="BROKER",
                name="DecisionBroker",
                status="SKIPPED",
                meta={"reason": broker_out["reason"], "tier": broker_out["tier"]},
            )
        else:
            broker_payload = dict(proposal)
            broker_payload["problem"] = problem_graph
            broker_out = self.decision_broker.process_request(gov_decision, broker_payload)
            episode.broker_decision = broker_out
            self._record_trace_event(
                episode,
                phase="BROKER",
                name="DecisionBroker",
                status=broker_out.get("status", "ESCROWED"),
                meta={"tier": broker_out.get("tier"), "token": broker_out.get("token")},
            )

        # Build execution trace for verification
        trace_tuples = [(ev.phase, ev.status) for ev in episode.trace]
        trace_valid = self.verifier.verify_trace(trace_tuples)
        if not trace_valid:
            self.ledger.log("Verifier", "InvalidTrace", {"len": len(trace_tuples)})
            arbiter_result = {
                "outcome": "VETOED",
                "reason": "Trace verification failed",
            }
            self._record_trace_event(
                episode,
                phase="VERIFIER",
                name="RollingVerifier",
                status="HALT_TRACE",
                meta={"reason": "Trace verification failed"},
            )

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
            "risk": {
                "components": dict(episode.risk_components),
                "aggregate": episode.risk_aggregate,
                "tier": episode.risk_tier,
            },
            "trace": self._export_trace(episode),
        }
        self.ledger.log(
            "KTEngine",
            "Finalize",
            {"status": response["status"], "decision": gov_decision.get("decision")},
        )
        return response
