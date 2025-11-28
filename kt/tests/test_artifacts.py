"""Tests for artifact seal chain integrity."""

from kt_core.context import LogicStatement, ProofTrace


def test_seal_chain_length_and_uniqueness():
    """Test seal chain has correct length and unique hashes."""
    trace = ProofTrace()
    ids = []

    for i in range(3):
        step = LogicStatement.new(
            content=f"step-{i}",
            formal=None,
            source="test",
            confidence=1.0,
        )
        ids.append(step.id)
        trace.add(step)

    chain = trace.metadata.get("seal_chain")
    assert chain is not None

    hashes = chain.split("->")
    assert len(hashes) == 3
    assert len(set(hashes)) == 3  # All unique


def test_seal_chain_empty_trace():
    """Test empty trace has no seal chain."""
    trace = ProofTrace()
    chain = trace.metadata.get("seal_chain")
    assert chain is None


def test_seal_chain_single_step():
    """Test seal chain with single step."""
    trace = ProofTrace()
    step = LogicStatement.new(
        content="single step",
        formal="(assert true)",
        source="test",
        confidence=1.0,
    )
    trace.add(step)

    chain = trace.metadata.get("seal_chain")
    assert chain is not None
    assert "->" not in chain  # Single hash, no arrow
    assert len(chain) == 64  # SHA-256 hex length


def test_seal_chain_deterministic():
    """Test seal chain is deterministic for same content."""
    step1 = LogicStatement(
        id="test123",
        content="same content",
        formal="(assert true)",
        source="test",
        confidence=1.0,
    )

    trace1 = ProofTrace()
    trace1.add(step1)

    trace2 = ProofTrace()
    trace2.add(step1)

    assert trace1.metadata["seal_chain"] == trace2.metadata["seal_chain"]


def test_seal_chain_different_content():
    """Test different content produces different hashes."""
    trace = ProofTrace()

    step1 = LogicStatement.new(
        content="first step",
        formal=None,
        source="test",
        confidence=1.0,
    )
    step2 = LogicStatement.new(
        content="second step",
        formal=None,
        source="test",
        confidence=1.0,
    )

    trace.add(step1)
    chain1 = trace.metadata["seal_chain"]

    trace.add(step2)
    chain2 = trace.metadata["seal_chain"]

    assert chain1 != chain2
    assert chain1 in chain2  # First hash is prefix
    assert "->" in chain2  # Chain has multiple hashes
