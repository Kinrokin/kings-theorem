"""Model registry for KT AGI Substrate.

Provides a simple in-memory registry keyed by adapter name.
"""

from __future__ import annotations

from typing import Dict

from .adapters import KTModelAdapter


class ModelRegistry:
    """In-memory adapter registry keyed by adapter name."""

    def __init__(self) -> None:
        self._models: Dict[str, KTModelAdapter] = {}

    def register(self, adapter: KTModelAdapter) -> None:
        """Register an adapter instance."""
        self._models[adapter.name] = adapter

    def get(self, name: str) -> KTModelAdapter:
        """Retrieve a registered adapter by name.

        Raises:
            KeyError: If the adapter name is not registered.
        """
        return self._models[name]
