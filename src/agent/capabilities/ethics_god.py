import logging

from src.llm_interface import query_qwen

logger = logging.getLogger(__name__)


async def respond(prompt: str) -> str:
    """Ethics capability; emphasizes policy, safety, and alternatives.

    Args:
        prompt: Scenario or proposal requiring ethical analysis.

    Returns:
        Safety-focused guidance with mitigations and alternatives.
    """
    hint = (
        "Respond as an ethics and safety reviewer. Identify potential harms, "
        "suggest safer alternatives, and enforce high ethical standards."
    )
    composed = f"{hint}\n\nCase: {prompt}"
    return await query_qwen(composed)
