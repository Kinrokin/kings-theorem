"""Telemetry and logging for King's Theorem orchestrator."""

from dataclasses import dataclass
from typing import Any, Dict

try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None


@dataclass
class Telemetry:
    """
    Telemetry bus for structured logging.

    Emits events for:
    - verified_step: Step passed verification
    - rejected_step: Step failed verification
    - budget_halt: Stopped due to budget exhaustion
    - prover_error: Prover raised exception
    - verifier_error: Verifier raised exception
    - status_change: Orchestrator status transition
    - backtrack: Backtracking triggered
    """

    fields: Dict[str, Any]

    def __post_init__(self):
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None

    def event(self, name: str, **kv: Any) -> None:
        """
        Log a structured event.

        Args:
            name: Event name
            **kv: Key-value pairs for event data
        """
        event_data = {"event": name, **self.fields, **kv}

        if self.console:
            self.console.log(event_data)
        else:
            # Fallback to print if rich not available
            print(f"[KT] {name}: {kv}")
