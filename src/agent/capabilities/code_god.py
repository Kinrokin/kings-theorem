import logging

from src.llm_interface import query_qwen

logger = logging.getLogger(__name__)


async def respond(prompt: str) -> str:
    """Code capability; encourages concise, secure code with docstrings.

    Args:
        prompt: Coding task or refactor request.

    Returns:
        Minimal, typed, and documented code suggestion.
    """
    hint = (
        "You are a senior engineer. Provide minimal, secure code with "
        "type hints and Google-style docstrings. Avoid external deps unless necessary."
    )
    composed = f"{hint}\n\nTask: {prompt}"
    return await query_qwen(composed)
