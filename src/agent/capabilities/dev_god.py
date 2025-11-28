import logging

from src.llm_interface import query_qwen

logger = logging.getLogger(__name__)


async def respond(prompt: str) -> str:
    """Developer operations capability; focuses on tooling and reliability.

    Args:
        prompt: DevOps/SRE request or troubleshooting scenario.

    Returns:
        Reliable, least-privilege, and auditable steps.
    """
    hint = (
        "Act as a DevOps/SRE. Provide reliable, secure, and auditable steps. "
        "Prefer least privilege and immutable infrastructure patterns."
    )
    composed = f"{hint}\n\nRequest: {prompt}"
    return await query_qwen(composed)
