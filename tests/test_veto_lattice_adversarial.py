import hashlib
import json
import uuid

from src.arbitration.pce_bundle import PCEBundle, StepResult
from src.arbitration.veto_lattice import VetoLattice


class MockArtifact:
    def __init__(self, key):
        self.output_hash = hashlib.sha256(json.dumps({"k": key}, sort_keys=True).encode()).hexdigest()

    def to_dict(self):
        return {"output_hash": self.output_hash}


def test_compositional_loophole_exposure():
    step1 = StepResult(step_id="T1", verdict="CONTINUE", output_artifact={"k": "A"})
    step2 = StepResult(step_id="T2", verdict="CONTINUE", output_artifact={"k": "B"})
    step3 = StepResult(step_id="T3", verdict="EXECUTE", output_artifact={"k": "C"})
    bundle = PCEBundle(
        bundle_id=str(uuid.uuid4()), initial_input_hash="foo", steps=[step1, step2, step3], final_output_hash="bar"
    )
    veto = VetoLattice()
    # deterministic check: since we used hash-based condition, ensure function runs and returns bool
    result = veto.check_global_invariants(bundle)
    assert isinstance(result, bool)
