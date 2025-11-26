"""Phoenix Phase 1 LLM Interface Unification

This module now acts as a thin compatibility wrapper around the
robust HTTP implementation in `src.api.llm_interface`.
Existing imports (`from src.llm_interface import query_qwen`) remain valid.
"""

from src.api.llm_interface import DEFAULT_MODEL, check_connection, query_qwen  # re-export

__all__ = ["query_qwen", "check_connection", "DEFAULT_MODEL"]
