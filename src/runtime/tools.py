"""Safe Tool Registry for KT Guarded Executor (Level 6 Alpha).

Provides a minimal registry and a secure math tool using strict regex whitelist.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

Tool = Callable[[Dict[str, Any]], Dict[str, Any]]


class ToolRegistry:
    """Registry for safe, auditable tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, name: str, fn: Tool) -> None:
        if not name or fn is None:
            raise ValueError("Invalid tool registration")
        self._tools[name] = fn

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)


def tool_math(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a simple math expression safely via regex whitelist.

    Args:
        payload: Dict with key 'expr' containing the expression string.

    Returns:
        Dict with either {"result": number} or {"error": message}.
    """
    expr = str(payload.get("expr", ""))
    import re

    if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
        return {"error": "SecurityViolation: Invalid characters in expression"}
    try:
        return {"result": eval(expr, {"__builtins__": {}}, {})}
    except Exception as e:  # noqa: BLE001 (explicitly returning error)
        return {"error": str(e)}
