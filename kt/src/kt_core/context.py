"""Context and trace structures for King's Theorem proofs."""

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LogicStatement:
    """
    Immutable atomic unit of logic or lemma.

    Attributes:
        id: Unique identifier
        content: Natural language or formal syntax
        formal: Z3/Lean/SMT2 syntax representation
        source: Origin (human, llm, axiom, etc.)
        confidence: Score in [0,1] from prover
    """

    id: str
    content: str
    formal: Optional[str]
    source: str
    confidence: float

    @staticmethod
    def new(
        content: str,
        formal: Optional[str],
        source: str = "human",
        confidence: float = 0.0,
    ) -> "LogicStatement":
        """
        Factory method to create a LogicStatement with auto-generated ID.

        Args:
            content: Statement content (natural language or formal)
            formal: Formal representation (SMT2/Z3/Lean syntax)
            source: Origin of statement
            confidence: Confidence score from prover

        Returns:
            New LogicStatement instance
        """
        return LogicStatement(
            id=str(uuid.uuid4())[:8],
            content=content,
            formal=formal,
            source=source,
            confidence=confidence,
        )


@dataclass
class ProofTrace:
    """
    Immutable history of a reasoning chain with cryptographic seal.

    The seal_chain in metadata provides tamper-evident provenance:
    Each step's hash is chained: hash1 -> hash2 -> hash3 ...
    """

    steps: List[LogicStatement] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def add(self, step: LogicStatement) -> None:
        """
        Add a step to the trace and update seal chain.

        Args:
            step: LogicStatement to append
        """
        self.steps.append(step)

        # Compute SHA-256 hash of step
        step_data = f"{step.id}|{step.content}|{step.formal}|{step.source}|{step.confidence}"
        h = hashlib.sha256(step_data.encode()).hexdigest()

        # Chain with previous hash
        chain = self.metadata.get("seal_chain", "")
        self.metadata["seal_chain"] = f"{chain}->{h}" if chain else h


@dataclass
class ProofContext:
    """
    Context for a proof attempt.

    Attributes:
        goal: The theorem or statement to prove
        symbols: Symbol table mapping names to types
        assumptions: List of assumed facts
    """

    goal: str
    symbols: Dict[str, str] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
