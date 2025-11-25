"""Minimal Proof DSL Skeleton

Supports declaring constraints and a simple theorem form:

constraint C1: fairness >= 0.7
constraint C2: traditions >= 2
theorem T1: C1 & C2 -> COMPOSITION_SAFE

Evaluation checks provided evidence dict for required constraint satisfaction.
This is a placeholder to evolve into a richer DSL.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

CONSTRAINT_RE = re.compile(r"^constraint\s+(?P<cid>[A-Za-z0-9_]+):\s*(?P<body>.+)$")
THEOREM_RE = re.compile(r"^theorem\s+(?P<tid>[A-Za-z0-9_]+):\s*(?P<body>.+)$")


@dataclass
class Constraint:
    cid: str
    expr: str  # e.g. fairness >= 0.7

    def evaluate(self, evidence: Dict[str, float]) -> bool:
        # VERY minimal parser: metric OP value
        m = re.match(
            r"^(?P<metric>[A-Za-z0-9_]+)\s*(>=|<=|>|<|==)\s*(?P<val>[0-9]*\.?[0-9]+)$",
            self.expr,
        )
        if not m:
            return False
        metric = m.group("metric")
        op = m.group(2)
        val = float(m.group("val"))
        actual = float(evidence.get(metric, 0.0))
        if op == ">=":
            return actual >= val
        if op == "<=":
            return actual <= val
        if op == ">":
            return actual > val
        if op == "<":
            return actual < val
        if op == "==":
            return abs(actual - val) < 1e-9
        return False


@dataclass
class Theorem:
    tid: str
    antecedents: List[str]  # constraint ids
    consequent: str  # symbolic label only

    def check(self, constraints: Dict[str, Constraint], evidence: Dict[str, float]) -> bool:
        return all(constraints[cid].evaluate(evidence) for cid in self.antecedents)


@dataclass
class ProofProgram:
    constraints: Dict[str, Constraint]
    theorems: Dict[str, Theorem]

    def evaluate(self, evidence: Dict[str, float]) -> Dict[str, bool]:
        results = {}
        for tid, th in self.theorems.items():
            results[tid] = th.check(self.constraints, evidence)
        return results

    def evaluate_to_json(self, evidence: Dict[str, float]) -> dict:
        """Produce machine-readable JSON artifact for CI gating."""
        import hashlib
        import json
        import time

        results = self.evaluate(evidence)
        theorems_output = []
        for tid, passed in results.items():
            th = self.theorems[tid]
            theorems_output.append(
                {
                    "theorem": tid,
                    "status": "PASS" if passed else "FAIL",
                    "antecedents": th.antecedents,
                    "consequent": th.consequent,
                    "evidence": evidence,
                }
            )
        artifact = {
            "timestamp": time.time(),
            "theorems": theorems_output,
            "all_pass": all(results.values()),
        }
        payload = json.dumps(artifact, sort_keys=True)
        artifact["certificate"] = hashlib.sha256(payload.encode()).hexdigest()
        return artifact


def parse(source: str) -> ProofProgram:
    constraints: Dict[str, Constraint] = {}
    theorems: Dict[str, Theorem] = {}
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        mc = CONSTRAINT_RE.match(line)
        if mc:
            cid = mc.group("cid")
            body = mc.group("body")
            constraints[cid] = Constraint(cid, body)
            continue
        mt = THEOREM_RE.match(line)
        if mt:
            tid = mt.group("tid")
            body = mt.group("body")
            # parse simple form: C1 & C2 -> LABEL
            if "->" not in body:
                continue
            antecedent_part, consequent_part = body.split("->", 1)
            antecedents = [a.strip() for a in antecedent_part.split("&")]
            theorems[tid] = Theorem(tid, antecedents, consequent_part.strip())
    return ProofProgram(constraints, theorems)


def quick_demo():
    src = """\nconstraint C1: fairness >= 0.7\nconstraint C2: traditions >= 2\ntheorem T1: C1 & C2 -> COMPOSITION_SAFE\n"""
    program = parse(src)
    evidence = {"fairness": 0.75, "traditions": 3}
    return program.evaluate(evidence)


if __name__ == "__main__":
    print(quick_demo())
