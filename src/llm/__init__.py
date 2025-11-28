"""LLM abstraction layer for King's Theorem."""

from .qwen_client import generate as qwen_generate, get_status as qwen_status
from .router import generate_prompt, get_backend_status

__all__ = [
    "qwen_generate",
    "qwen_status",
    "generate_prompt",
    "get_backend_status",
]
