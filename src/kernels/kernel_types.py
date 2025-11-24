from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict


class KernelType(Enum):
    EPISTEMIC = "epistemic"
    PRUDENTIAL = "prudential"
    ETHICAL = "ethical"
    COMPOSITIONAL = "compositional"
    ADVERSARIAL = "adversarial"
    META = "meta"


class TypedKernel(ABC):
    def __init__(self, kernel_type: KernelType, name: str):
        self.type = kernel_type
        self.name = name
        self.warrant_threshold = self._get_warrant_threshold()
        self.veto_power = self._get_veto_power()
        self.proof_burden = self._get_proof_burden()

    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        raise NotImplementedError()

    def _get_warrant_threshold(self):
        thresholds = {
            KernelType.EPISTEMIC: 0.95,
            KernelType.PRUDENTIAL: 0.85,
            KernelType.ETHICAL: 0.99,
            KernelType.COMPOSITIONAL: 0.90,
            KernelType.ADVERSARIAL: 0.80,
            KernelType.META: 1.0,
        }
        return thresholds[self.type]

    def _get_veto_power(self):
        power = {
            KernelType.EPISTEMIC: 1,
            KernelType.PRUDENTIAL: 2,
            KernelType.COMPOSITIONAL: 3,
            KernelType.ADVERSARIAL: 4,
            KernelType.ETHICAL: 5,
            KernelType.META: 10,
        }
        return power[self.type]

    def _get_proof_burden(self):
        burdens = {
            KernelType.EPISTEMIC: "evidential",
            KernelType.PRUDENTIAL: "risk_assessment",
            KernelType.ETHICAL: "value_alignment",
            KernelType.COMPOSITIONAL: "structural",
            KernelType.ADVERSARIAL: "refutation",
            KernelType.META: "meta_consistency",
        }
        return burdens[self.type]
