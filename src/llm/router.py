"""
LLM Router - Unified Interface for Multiple Backends

Routes generation requests to appropriate backend based on configuration.

Supported backends:
- qwen: Qwen3 8B (HTTP or local)
- openai: OpenAI API (GPT-4, etc.)
- anthropic: Claude API
- google: Gemini API

Configuration:
- KT_BACKEND: Backend to use (default: "qwen")
"""

from __future__ import annotations

import os
from typing import Optional

# Import backend clients
from .qwen_client import generate as qwen_generate, get_status as qwen_status

# Optional: Import other backends if available
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

KT_BACKEND = os.getenv("KT_BACKEND", "qwen")


# ═══════════════════════════════════════════════════════════════════════════
# BACKEND IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════


def _generate_qwen(prompt: str, max_tokens: int, temperature: float) -> str:
    """Generate using Qwen backend."""
    return qwen_generate(prompt, max_tokens, temperature)


def _generate_openai(prompt: str, max_tokens: int, temperature: float) -> str:
    """
    Generate using OpenAI API.
    
    Requires:
        - openai library
        - OPENAI_API_KEY environment variable
    """
    if not HAS_OPENAI:
        raise RuntimeError("OpenAI backend requires 'openai' library. Install with: pip install openai")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    
    client = openai.OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    
    return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════


def generate_prompt(prompt: str, max_tokens: int = 512, temperature: float = 1.0) -> str:
    """
    Generate text using configured backend.
    
    Args:
        prompt: Input prompt
        max_tokens: Max output tokens (default: 512)
        temperature: Sampling temperature (default: 1.0)
        
    Returns:
        Generated text
        
    Raises:
        ValueError: If KT_BACKEND is invalid
        RuntimeError: If backend is not available or fails
    """
    if KT_BACKEND == "qwen":
        return _generate_qwen(prompt, max_tokens, temperature)
    
    elif KT_BACKEND == "openai":
        return _generate_openai(prompt, max_tokens, temperature)
    
    # Add more backends as needed:
    # elif KT_BACKEND == "anthropic":
    #     return _generate_anthropic(prompt, max_tokens, temperature)
    # elif KT_BACKEND == "google":
    #     return _generate_google(prompt, max_tokens, temperature)
    
    else:
        raise ValueError(
            f"Invalid KT_BACKEND={KT_BACKEND!r}. "
            f"Supported backends: qwen, openai"
        )


def get_backend_status() -> dict[str, Any]:
    """
    Get status of current backend.
    
    Returns:
        Dict with backend info and availability
    """
    if KT_BACKEND == "qwen":
        return qwen_status()
    
    elif KT_BACKEND == "openai":
        return {
            "backend": "openai",
            "ok": HAS_OPENAI and bool(os.getenv("OPENAI_API_KEY")),
            "error": None if (HAS_OPENAI and os.getenv("OPENAI_API_KEY")) else "Missing openai library or OPENAI_API_KEY",
            "config": {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            }
        }
    
    else:
        return {
            "backend": KT_BACKEND,
            "ok": False,
            "error": f"Unknown backend: {KT_BACKEND}",
            "config": {}
        }
