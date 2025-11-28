def test_math_tool_execution():
    from src.runtime.tools import ToolRegistry, tool_math

    reg = ToolRegistry()
    reg.register("math", tool_math)

    # Safe expression
    res = tool_math({"expr": "2 + 2"})
    assert res["result"] == 4

    # Unsafe attempt
    res_bad = tool_math({"expr": "__import__('os').system('dir')"})
    assert "SecurityViolation" in res_bad.get("error", "")
