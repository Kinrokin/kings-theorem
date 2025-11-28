import logging

from src.llm_interface import query_qwen

logger = logging.getLogger(__name__)


async def respond(prompt: str) -> str:
    """Creativity capability; explores diverse but safe ideas.

    Args:
        prompt: Creative brief or ideation topic.

    Returns:
        A list of creative, positive, and safe ideas.
    """
    hint = (
        "You are a creative strategist. Generate diverse, positive, and "
        "safe ideas. Avoid sensitive or harmful content."
    )
    composed = f"{hint}\n\nBrief: {prompt}"
    return await query_qwen(composed)
