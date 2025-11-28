"""Economic Scenarios Package

Phase 5 adversarial finance scenario generator for resilience testing.
"""

from .econ_scenarios import (
    SCENARIOS,
    adversarial_pricing_pumpanddump,
    adverse_selection_insurance,
    asymmetric_information_scenario,
    catastrophe_insurance_moral_hazard,
    ethical_finance_paradox,
    generate_scenario,
    multi_actor_collusion,
)

__all__ = [
    "SCENARIOS",
    "ethical_finance_paradox",
    "asymmetric_information_scenario",
    "adversarial_pricing_pumpanddump",
    "catastrophe_insurance_moral_hazard",
    "adverse_selection_insurance",
    "multi_actor_collusion",
    "generate_scenario",
]
