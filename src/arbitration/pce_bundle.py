from dataclasses import dataclass, field
from typing import List, Dict, Any
import hashlib, json, uuid

def hash_blob(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()

@dataclass
class StepResult:
    step_id: str
    verdict: str  # "CONTINUE","EXECUTE","REJECT"
    output_artifact: Dict[str, Any]
    claims: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PCEBundle:
    bundle_id: str
    initial_input_hash: str
    steps: List[StepResult]
    final_output_hash: str

    def is_vetoed_locally(self) -> bool:
        # local veto if any step verdict == REJECT
        return any(s.verdict.upper() == "REJECT" for s in self.steps)

    def get_current_state_hash(self) -> str:
        payload = {
            "bundle_id": self.bundle_id,
            "steps": [ {"id": s.step_id, "verdict": s.verdict, "artifact": s.output_artifact} for s in self.steps ]
        }
        return hash_blob(payload)
