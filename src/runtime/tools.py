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
    import ast
    import operator
    import re

    if not re.fullmatch(r"[0-9+\-*/(). ]+", expr):
        return {"error": "SecurityViolation: Invalid characters in expression"}

    # Safe evaluation using AST parsing instead of eval()
    # Bandit: S307 - replaced eval with safe AST-based evaluator
    try:

        def safe_eval_expr(node):
            """Recursively evaluate AST nodes for arithmetic only."""
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.USub: operator.neg,
            }
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.BinOp):
                left = safe_eval_expr(node.left)
                right = safe_eval_expr(node.right)
                return ops[type(node.op)](left, right)
            if isinstance(node, ast.UnaryOp):
                operand = safe_eval_expr(node.operand)
                return ops[type(node.op)](operand)
            raise ValueError(f"Unsupported operation: {type(node).__name__}")

        tree = ast.parse(expr, mode="eval")
        result = safe_eval_expr(tree.body)
        return {"result": result}
    except Exception as e:  # noqa: BLE001 (explicitly returning error)
        return {"error": str(e)}
