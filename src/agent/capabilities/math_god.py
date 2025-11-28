import logging

from src.llm_interface import query_qwen

logger = logging.getLogger(__name__)


async def respond(prompt: str) -> str:
    """Math-focused capability; hints model to prefer formal math style.

    Args:
        prompt: Math problem or theorem statement.

    Returns:
        A rigorous, proof-oriented answer from the model.
    """
    system_hint = "Answer as a rigorous mathematician. Prefer proofs and derivations."
    composed = f"{system_hint}\n\nProblem: {prompt}"
    return await query_qwen(composed)
