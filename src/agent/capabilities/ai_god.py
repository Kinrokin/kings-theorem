import logging

from src.llm_interface import query_qwen

logger = logging.getLogger(__name__)


async def respond(prompt: str) -> str:
    """General AI capability using the default LLM.

    Args:
        prompt: User prompt to send to the model.

    Returns:
        Model-generated text response.
    """
    return await query_qwen(prompt)
