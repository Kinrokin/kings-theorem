"""Base Model Adapter Interface

AID: /src/adapters/base.py
Purpose: Abstract interface for all model backends (local, API, hybrid)

All adapters must implement:
- generate(): Synchronous text generation
- generate_async(): Asynchronous text generation
- embed(): Generate embeddings (if supported)
- metadata: Model capabilities (context length, rate limits, etc.)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for model adapter."""

    model_id: str  # e.g., "gpt-4", "llama-3-70b", "claude-3-opus"
    backend: str  # "openai", "anthropic", "local", "llama_cpp"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_path: Optional[str] = None  # For local models
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 60  # seconds
    context_length: int = 8192
    supports_embeddings: bool = False
    supports_function_calling: bool = False
    rate_limit_rpm: Optional[int] = None  # Requests per minute
    cost_per_1k_tokens: Optional[float] = None


@dataclass
class ModelResponse:
    """Standardized response from any model backend."""

    model_id: str
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    finish_reason: str = "stop"  # "stop", "length", "content_filter", "error"
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ModelAdapter(ABC):
    """Abstract base class for all model adapters.

    All concrete adapters (LocalModelAdapter, APIModelAdapter) must inherit
    from this class and implement the required methods.

    Constitutional Guarantees:
    - All generate() calls logged to Merkle ledger
    - All outputs pass through dual-layer guardrail
    - Failures trigger conservative fallback (never silent)
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.call_count = 0
        self.total_tokens = 0
        self.total_latency_ms = 0
        logger.info("ModelAdapter initialized: model=%s backend=%s", config.model_id, config.backend)

    @abstractmethod
    def generate(
        self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs
    ) -> ModelResponse:
        """Generate text completion synchronously.

        Args:
            prompt: Input text
            max_tokens: Override config max_tokens
            temperature: Override config temperature
            **kwargs: Backend-specific parameters

        Returns:
            ModelResponse with content and metadata

        Raises:
            ModelAdapterError: On generation failure
        """
        pass

    @abstractmethod
    async def generate_async(
        self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None, **kwargs
    ) -> ModelResponse:
        """Generate text completion asynchronously."""
        pass

    def embed(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector (if supported).

        Returns:
            Embedding vector or None if not supported
        """
        if not self.config.supports_embeddings:
            logger.warning("Model %s does not support embeddings", self.config.model_id)
            return None

        # Override in subclass
        raise NotImplementedError(f"Embeddings not implemented for {self.config.backend}")

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics for monitoring."""
        return {
            "model_id": self.config.model_id,
            "backend": self.config.backend,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "avg_latency_ms": self.total_latency_ms / max(1, self.call_count),
            "total_latency_ms": self.total_latency_ms,
        }

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.call_count = 0
        self.total_tokens = 0
        self.total_latency_ms = 0
        logger.debug("Reset stats for model %s", self.config.model_id)


class ModelAdapterError(Exception):
    """Base exception for model adapter errors."""

    pass
