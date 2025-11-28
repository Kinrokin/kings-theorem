import logging
from typing import Awaitable, Callable, Dict, Optional

from src.agent.capabilities import ai_god, code_god, creativity_god, dev_god, ethics_god, math_god
from src.governance.arbiter_hardened import ArbiterResult, HardenedArbiter

logger = logging.getLogger(__name__)


class KTAgent:
    """Constitutional super-agent that governs domain capabilities via Arbiter.

    The KTAgent provides a simple routing layer from a user query to a selected
    capability module (AI/Math/Code/Ethics/Creativity/Dev). All capability
    executions are vetted by the `HardenedArbiter` using the existing
    doubly-blind, policy-enforced governance pipeline. Ledger provenance and
    integrity are handled by the Arbiter and Ledger subsystems.

    Attributes:
        arbiter: The hardened arbiter instance responsible for governance.
        capabilities: Mapping of mode -> async callable (prompt -> str)
    """

    def __init__(self, arbiter: HardenedArbiter) -> None:
        self.arbiter = arbiter
        self.capabilities: Dict[str, Callable[[str], Awaitable[str]]] = {
            "ai": ai_god.respond,
            "math": math_god.respond,
            "code": code_god.respond,
            "ethics": ethics_god.respond,
            "creative": creativity_god.respond,
            "dev": dev_god.respond,
        }
        logger.info("KTAgent initialized with capabilities: %s", sorted(self.capabilities.keys()))

    async def ask(self, query: str, mode: Optional[str] = None) -> ArbiterResult:
        """Route a query to a capability under Arbiter governance.

        Args:
            query: The user question or instruction.
            mode: Optional capability key (ai|math|code|ethics|creative|dev).

        Returns:
            ArbiterResult: The governed result including provenance.

        Notes:
            - If mode is None or unknown, defaults to AI capability triad.
            - Student and Teacher callables must be zero-arg async callables; we
              capture the prompt via closures to satisfy the executor interface.
        """
        if mode is None or mode not in self.capabilities:
            logger.info("KTAgent routing with default AI capability (triad)")

            async def student() -> str:
                return await ai_god.respond(query)

            async def teacher() -> str:
                return await ai_god.respond(query)

            return await self.arbiter.arbitrate(
                student_fn=student,
                teacher_fn=teacher,
                prompt=query,
            )

        fn = self.capabilities[mode]
        logger.info("KTAgent routing mode '%s'", mode)

        async def student() -> str:
            return await fn(query)

        async def teacher() -> str:
            return await fn(query)

        return await self.arbiter.arbitrate(
            student_fn=student,
            teacher_fn=teacher,
            prompt=query,
        )
