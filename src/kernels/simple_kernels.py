from typing import Any, Dict

from src.algebra.constraint_lattice import Constraint, ConstraintType
from src.kernels.kernel_types import KernelType, TypedKernel


class EpistemicKernel(TypedKernel):
    def __init__(self, name="epistemic"):
        super().__init__(KernelType.EPISTEMIC, name)

    def process(self, input_data: Any) -> Dict[str, Any]:
        # produce a claim and an artifact
        artifact = {
            "text": f"interpreted({input_data.get('prompt','')})",
            "ethical_vector": {"fairness": 0.6, "non_maleficence": 0.7},
        }
        claims = [{"id": "c1", "type": "epistemic", "expression": "truth-like", "strength": 0.9, "domain": "nlp"}]
        return {"verdict": "CONTINUE", "artifact": artifact, "claims": claims}


class AdversarialKernel(TypedKernel):
    def __init__(self, name="adversarial"):
        super().__init__(KernelType.ADVERSARIAL, name)

    def process(self, input_data: Any) -> Dict[str, Any]:
        # Pretend to try to find contradictions; here we always continue
        artifact = input_data
        return {"verdict": "CONTINUE", "artifact": artifact, "claims": []}
