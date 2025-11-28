from typing import Any, Dict, List

from src.algebra.constraint_lattice import ConstraintLattice
from src.arbitration.pce_bundle import PCEBundle, StepResult
from src.arbitration.veto_lattice import VetoLattice
from src.ethics.manifold import ManifoldProjector


class KernelOrchestrator:
    def __init__(
        self,
        kernels: List[Any],
        constraint_lattice: ConstraintLattice,
        manifold: ManifoldProjector,
    ):
        self.kernels = kernels
        self.lattice = constraint_lattice
        self.manifold = manifold
        self.veto = VetoLattice()

    def run_dialectic(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        # Run kernels in staged order: epistemic -> adversarial -> prudential -> ethical -> compositional -> meta
        steps = []
        current = user_input
        for kernel in self.kernels:
            r = kernel.process(current)
            steps.append(
                StepResult(
                    step_id=kernel.name,
                    verdict=r.get("verdict", "CONTINUE"),
                    output_artifact=r.get("artifact", {}),
                    claims=r.get("claims", []),
                )
            )
            # update current for next step
            current = r.get("artifact", current)
        bundle = PCEBundle(
            bundle_id="pce-" + user_input.get("id", "0"),
            initial_input_hash="init",
            steps=steps,
            final_output_hash="final",
        )
        # Local veto check
        if bundle.is_vetoed_locally():
            return {"status": "rejected", "reason": "local veto triggered"}
        # Global invariants
        ok = self.veto.check_global_invariants(bundle)
        if not ok:
            return {
                "status": "rejected",
                "reason": "global invariant failed",
                "veto_history": self.veto.veto_history,
            }
        # Ethical projection attempt (example)
        # For demonstration assume artifact contains ethical vector
        final = steps[-1].output_artifact
        if "ethical_vector" in final:
            projected, ok = self.manifold.project(final["ethical_vector"])
            final["ethical_projected"] = projected
            final["ethical_ok"] = ok
        return {"status": "accepted", "final": final}
