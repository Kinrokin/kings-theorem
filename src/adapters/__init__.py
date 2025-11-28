"""Model-Agnostic Adapter Layer for KT Proto-AGI

AID: /src/adapters/__init__.py
Purpose: Universal model interface enabling Trinity councils with heterogeneous models

Level 5 Capability: Multi-model governance with epistemic diversity
- Student Council: S₁...Sₙ (diverse models for exploration)
- Teacher Council: T₁...Tₙ (diverse models for verification)
- Arbiter Council: A₁...Aₖ (diverse models for conflict resolution)

Supported Backends:
- Local: Qwen, Mistral, LLaMA, DeepSeek (via transformers/llama.cpp)
- API: OpenAI GPT, Anthropic Claude, Google Gemini
- Hybrid: Fallback chains (local → API)

Constitutional Compliance:
- Axiom 3 (Auditability): All model calls logged to Merkle ledger
- Axiom 6 (Ethical Governance): All outputs pass dual-layer guardrail
- Axiom 2 (Formal Safety): Model failures trigger conservative fallback
"""

from adapters.api import APIModelAdapter
from adapters.base import ModelAdapter, ModelConfig, ModelResponse
from adapters.factory import create_adapter
from adapters.local import LocalModelAdapter

__all__ = [
    "ModelAdapter",
    "ModelConfig",
    "ModelResponse",
    "LocalModelAdapter",
    "APIModelAdapter",
    "create_adapter",
]
