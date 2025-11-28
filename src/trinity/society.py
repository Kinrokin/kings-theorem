"""Trinity Society (Level 5): councils for Student/Teacher/Arbiter.

Each council wraps multiple `KTModelAdapter` members and provides methods to
propose, evaluate, and decide. Arbiter aggregations default to simple majority.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.models.adapters import KTModelAdapter


class StudentCouncil:
    """Council of student models to propose outputs."""

    def __init__(self, members: List[KTModelAdapter]):
        self.members = members

    def propose(self, prompt: str) -> List[Dict[str, Any]]:
        outputs: List[Dict[str, Any]] = []
        for m in self.members:
            text = m.generate(prompt)
            outputs.append({"member": m.name, "output": text})
        return outputs


class TeacherCouncil:
    """Council of teacher models to evaluate proposals."""

    def __init__(self, members: List[KTModelAdapter]):
        self.members = members

    def evaluate(self, prompt: str, proposals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        evals: List[Dict[str, Any]] = []
        for m in self.members:
            teacher_prompt = (
                "You are a Teacher in a governing council. "
                "Evaluate each proposal for correctness, safety, and coherence.\n\n"
                f"Prompt:\n{prompt}\n\nProposals:\n{proposals}"
            )
            text = m.generate(teacher_prompt)
            evals.append({"member": m.name, "evaluation": text})
        return evals


class ArbiterCouncil:
    """Council of arbiters to decide constitutionality and safety."""

    def __init__(self, members: List[KTModelAdapter]):
        self.members = members

    def decide(
        self,
        prompt: str,
        proposals: List[Dict[str, Any]],
        teacher_evals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        decisions: List[Dict[str, Any]] = []
        for m in self.members:
            arbiter_prompt = (
                "You are an Arbiter in a constitutional council. "
                "Given the prompt, proposals, and teacher evaluations, decide:\n"
                '{ "vetoed": bool, "reason": str }\n\n'
                f"Prompt:\n{prompt}\n\nProposals:\n{proposals}\n\nTeacher evaluations:\n{teacher_evals}"
            )
            text = m.generate(arbiter_prompt)
            decisions.append({"member": m.name, "raw_decision": text})
        return self._aggregate_decisions(decisions)

    def _aggregate_decisions(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        votes: List[Dict[str, Any]] = []
        for d in decisions:
            try:
                parsed = json.loads(d["raw_decision"].strip("`json \n"))
            except Exception:
                parsed = {"vetoed": False, "reason": "PARSE_FAIL"}
            votes.append(parsed)

        veto_count = sum(1 for v in votes if v.get("vetoed"))
        total = len(votes) or 1
        vetoed = veto_count > total / 2
        reasons = [v.get("reason", "") for v in votes]
        return {"vetoed": vetoed, "votes": votes, "reasons": reasons}
