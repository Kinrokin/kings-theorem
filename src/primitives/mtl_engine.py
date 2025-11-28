"""Formal MTL (Metric Temporal Logic) Engine - Titanium X Protocol

AID: /src/primitives/mtl_engine.py
Proof ID: PRF-PHOENIX-MTL-001
Adversarial Response: Section 2.1 "The Rigor Gap"

This module implements a mathematically rigorous MTL engine with:
- Typed AST nodes for all supported operators
- Recursive descent parser for MTL formulas
- Formal evaluator against event traces
- Three-valued logic: SATISFIED, VIOLATED, VACUOUS

Supported Operators:
- G (Globally/Always): G[a,b](φ) - φ holds at all times in [a,b]
- F (Eventually/Finally): F[a,b](φ) - φ holds at some time in [a,b]
- U (Until): φ U[a,b] ψ - φ holds until ψ, with ψ occurring in [a,b]
- X (Next): X(φ) - φ holds at the next time step
- Boolean: And, Or, Not, Implies
- Atomic: predicates like "risk < 0.5", "ethics >= 0.7"

Event Model:
    Event = {"type": str, "timestamp": float, "payload": Dict[str, Any]}
    Trace = List[Event] sorted by timestamp

Usage:
    from src.primitives.mtl_engine import MTLEngine, parse_mtl

    engine = MTLEngine()
    formula = parse_mtl("G[0,10](risk < 0.5)")
    result = engine.evaluate(formula, trace, horizon=10.0)
    # result.status in {SATISFIED, VIOLATED, VACUOUS, UNKNOWN}
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# =============================================================================
# Result Types
# =============================================================================


class MTLStatus(Enum):
    """Three-valued MTL evaluation result."""

    SATISFIED = auto()  # Formula definitely holds
    VIOLATED = auto()  # Formula definitely does not hold
    VACUOUS = auto()  # Formula is vacuously true (antecedent never triggered)
    UNKNOWN = auto()  # Cannot determine (insufficient data or unsupported)


@dataclass
class MTLResult:
    """Result of MTL evaluation with diagnostic info."""

    status: MTLStatus
    formula: str
    message: str = ""
    witness_time: Optional[float] = None  # Time of violation/satisfaction
    trace_coverage: float = 0.0  # Fraction of trace examined

    def __bool__(self) -> bool:
        return self.status == MTLStatus.SATISFIED


# =============================================================================
# AST Node Types
# =============================================================================


@dataclass
class MTLNode(ABC):
    """Base class for MTL AST nodes."""

    @abstractmethod
    def to_string(self) -> str:
        """Convert to canonical string representation."""
        pass

    def __str__(self) -> str:
        return self.to_string()


@dataclass
class Atomic(MTLNode):
    """Atomic proposition: variable op value (e.g., "risk < 0.5")."""

    variable: str
    operator: str  # '<', '<=', '>', '>=', '==', '!='
    value: float

    def to_string(self) -> str:
        return f"{self.variable} {self.operator} {self.value}"


@dataclass
class Not(MTLNode):
    """Negation: ¬φ"""

    child: MTLNode

    def to_string(self) -> str:
        return f"!({self.child.to_string()})"


@dataclass
class And(MTLNode):
    """Conjunction: φ ∧ ψ"""

    left: MTLNode
    right: MTLNode

    def to_string(self) -> str:
        return f"({self.left.to_string()} & {self.right.to_string()})"


@dataclass
class Or(MTLNode):
    """Disjunction: φ ∨ ψ"""

    left: MTLNode
    right: MTLNode

    def to_string(self) -> str:
        return f"({self.left.to_string()} | {self.right.to_string()})"


@dataclass
class Implies(MTLNode):
    """Implication: φ → ψ"""

    left: MTLNode
    right: MTLNode

    def to_string(self) -> str:
        return f"({self.left.to_string()} -> {self.right.to_string()})"


@dataclass
class Globally(MTLNode):
    """Globally/Always: G[a,b](φ) - φ holds at all times in interval [a,b]."""

    child: MTLNode
    lower_bound: float = 0.0
    upper_bound: Optional[float] = None  # None = unbounded (to horizon)

    def to_string(self) -> str:
        if self.upper_bound is not None:
            return f"G[{self.lower_bound},{self.upper_bound}]({self.child.to_string()})"
        return f"G({self.child.to_string()})"


@dataclass
class Eventually(MTLNode):
    """Eventually/Finally: F[a,b](φ) - φ holds at some time in interval [a,b]."""

    child: MTLNode
    lower_bound: float = 0.0
    upper_bound: Optional[float] = None

    def to_string(self) -> str:
        if self.upper_bound is not None:
            return f"F[{self.lower_bound},{self.upper_bound}]({self.child.to_string()})"
        return f"F({self.child.to_string()})"


@dataclass
class Until(MTLNode):
    """Until: φ U[a,b] ψ - φ holds until ψ occurs, with ψ in interval [a,b]."""

    left: MTLNode  # φ (must hold until)
    right: MTLNode  # ψ (must eventually hold)
    lower_bound: float = 0.0
    upper_bound: Optional[float] = None

    def to_string(self) -> str:
        if self.upper_bound is not None:
            return f"({self.left.to_string()} U[{self.lower_bound},{self.upper_bound}] {self.right.to_string()})"
        return f"({self.left.to_string()} U {self.right.to_string()})"


@dataclass
class Next(MTLNode):
    """Next: X(φ) - φ holds at the next time step."""

    child: MTLNode

    def to_string(self) -> str:
        return f"X({self.child.to_string()})"


# =============================================================================
# Parser (Recursive Descent)
# =============================================================================


class MTLParseError(Exception):
    """Error during MTL formula parsing."""

    pass


class MTLParser:
    """Recursive descent parser for MTL formulas.

    Grammar (informal):
        formula := implication
        implication := disjunction ('->' implication)?
        disjunction := conjunction ('|' disjunction)?
        conjunction := unary ('&' conjunction)?
        unary := '!' unary | temporal | atomic | '(' formula ')'
        temporal := ('G' | 'F') bounds? '(' formula ')' |
                    '(' formula ')' 'U' bounds? '(' formula ')' |
                    'X' '(' formula ')'
        bounds := '[' number ',' number ']'
        atomic := identifier op number
        op := '<' | '<=' | '>' | '>=' | '==' | '!='
    """

    def __init__(self, text: str):
        self.text = text.strip()
        self.pos = 0
        self.length = len(self.text)

    def parse(self) -> MTLNode:
        """Parse the formula and return AST root."""
        result = self._parse_implication()
        self._skip_whitespace()
        if self.pos < self.length:
            raise MTLParseError(f"Unexpected characters at position {self.pos}: '{self.text[self.pos:]}'")
        return result

    def _skip_whitespace(self) -> None:
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1

    def _peek(self, n: int = 1) -> str:
        return self.text[self.pos : self.pos + n]

    def _consume(self, expected: str) -> None:
        self._skip_whitespace()
        if self.text[self.pos : self.pos + len(expected)] != expected:
            raise MTLParseError(f"Expected '{expected}' at position {self.pos}, got '{self._peek(len(expected))}'")
        self.pos += len(expected)

    def _try_consume(self, expected: str) -> bool:
        self._skip_whitespace()
        if self.text[self.pos : self.pos + len(expected)] == expected:
            self.pos += len(expected)
            return True
        return False

    def _parse_implication(self) -> MTLNode:
        left = self._parse_disjunction()
        self._skip_whitespace()
        if self._try_consume("->"):
            right = self._parse_implication()
            return Implies(left, right)
        return left

    def _parse_disjunction(self) -> MTLNode:
        left = self._parse_conjunction()
        self._skip_whitespace()
        if self._try_consume("|"):
            right = self._parse_disjunction()
            return Or(left, right)
        return left

    def _parse_conjunction(self) -> MTLNode:
        left = self._parse_unary()
        self._skip_whitespace()
        if self._try_consume("&"):
            right = self._parse_conjunction()
            return And(left, right)
        return left

    def _parse_unary(self) -> MTLNode:
        self._skip_whitespace()

        # Negation
        if self._try_consume("!"):
            child = self._parse_unary()
            return Not(child)

        # Temporal operators
        if self._try_consume("G"):
            return self._parse_globally()
        if self._try_consume("F"):
            return self._parse_eventually()
        if self._try_consume("X"):
            return self._parse_next()

        # Parenthesized expression (possibly with Until)
        if self._peek() == "(":
            self._consume("(")
            left = self._parse_implication()
            self._consume(")")

            # Check for Until operator
            self._skip_whitespace()
            if self._try_consume("U"):
                bounds = self._parse_bounds()
                self._consume("(")
                right = self._parse_implication()
                self._consume(")")
                return Until(left, right, bounds[0], bounds[1])

            return left

        # Atomic proposition
        return self._parse_atomic()

    def _parse_bounds(self) -> Tuple[float, Optional[float]]:
        """Parse optional metric bounds [a,b]."""
        self._skip_whitespace()
        if self._try_consume("["):
            lower = self._parse_number()
            self._consume(",")
            upper = self._parse_number()
            self._consume("]")
            return (lower, upper)
        return (0.0, None)

    def _parse_globally(self) -> Globally:
        bounds = self._parse_bounds()
        self._consume("(")
        child = self._parse_implication()
        self._consume(")")
        return Globally(child, bounds[0], bounds[1])

    def _parse_eventually(self) -> Eventually:
        bounds = self._parse_bounds()
        self._consume("(")
        child = self._parse_implication()
        self._consume(")")
        return Eventually(child, bounds[0], bounds[1])

    def _parse_next(self) -> Next:
        self._consume("(")
        child = self._parse_implication()
        self._consume(")")
        return Next(child)

    def _parse_atomic(self) -> Atomic:
        """Parse atomic proposition: variable op value."""
        self._skip_whitespace()

        # Parse variable name
        var_match = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", self.text[self.pos :])
        if not var_match:
            raise MTLParseError(f"Expected variable name at position {self.pos}")
        variable = var_match.group()
        self.pos += len(variable)

        self._skip_whitespace()

        # Parse operator
        op = None
        for candidate in ["<=", ">=", "==", "!=", "<", ">"]:
            if self._try_consume(candidate):
                op = candidate
                break
        if op is None:
            raise MTLParseError(f"Expected comparison operator at position {self.pos}")

        self._skip_whitespace()

        # Parse value
        value = self._parse_number()

        return Atomic(variable, op, value)

    def _parse_number(self) -> float:
        """Parse a numeric literal."""
        self._skip_whitespace()
        match = re.match(r"-?\d+(\.\d+)?", self.text[self.pos :])
        if not match:
            raise MTLParseError(f"Expected number at position {self.pos}")
        self.pos += len(match.group())
        return float(match.group())


def parse_mtl(formula: str) -> MTLNode:
    """Parse an MTL formula string into an AST.

    Args:
        formula: MTL formula string (e.g., "G[0,10](risk < 0.5)")

    Returns:
        Root node of the AST

    Raises:
        MTLParseError: If the formula is syntactically invalid
    """
    parser = MTLParser(formula)
    return parser.parse()


# =============================================================================
# Evaluator
# =============================================================================


@dataclass
class Event:
    """Timestamped event in a trace."""

    timestamp: float
    values: Dict[str, float] = field(default_factory=dict)
    event_type: str = "state"
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        return cls(
            timestamp=d.get("timestamp", d.get("time", 0.0)),
            values=d.get("values", {}),
            event_type=d.get("type", "state"),
            payload=d.get("payload", {}),
        )


class MTLEngine:
    """Formal MTL evaluator with three-valued semantics.

    Evaluates MTL formulas against event traces using standard
    discrete-time semantics with metric intervals.
    """

    def __init__(self, default_horizon: float = 100.0):
        """Initialize engine.

        Args:
            default_horizon: Default time horizon for unbounded operators
        """
        self.default_horizon = default_horizon

    def evaluate(
        self,
        formula: MTLNode,
        trace: List[Union[Event, Dict[str, Any]]],
        horizon: Optional[float] = None,
        start_time: float = 0.0,
    ) -> MTLResult:
        """Evaluate formula against trace.

        Args:
            formula: Parsed MTL formula (AST root)
            trace: List of events (sorted by timestamp)
            horizon: Time horizon for evaluation (default: self.default_horizon)
            start_time: Reference time for interval bounds

        Returns:
            MTLResult with status and diagnostics
        """
        if horizon is None:
            horizon = self.default_horizon

        # Normalize trace to Event objects
        events = []
        for item in trace:
            if isinstance(item, Event):
                events.append(item)
            elif isinstance(item, dict):
                events.append(Event.from_dict(item))
            else:
                raise ValueError(f"Invalid trace element type: {type(item)}")

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        if not events:
            return MTLResult(
                status=MTLStatus.VACUOUS,
                formula=formula.to_string(),
                message="Empty trace - vacuously satisfied",
                trace_coverage=0.0,
            )

        try:
            satisfied, witness = self._eval(formula, events, 0, horizon, start_time)

            if satisfied is None:
                status = MTLStatus.VACUOUS
                message = "Formula is vacuously true (antecedent never triggered)"
            elif satisfied:
                status = MTLStatus.SATISFIED
                message = "Formula holds over the trace"
            else:
                status = MTLStatus.VIOLATED
                message = f"Formula violated at time {witness}" if witness else "Formula violated"

            return MTLResult(
                status=status, formula=formula.to_string(), message=message, witness_time=witness, trace_coverage=1.0
            )

        except Exception as e:
            logger.exception("MTL evaluation error")
            return MTLResult(
                status=MTLStatus.UNKNOWN,
                formula=formula.to_string(),
                message=f"Evaluation error: {e}",
                trace_coverage=0.0,
            )

    def _eval(
        self, node: MTLNode, events: List[Event], idx: int, horizon: float, base_time: float
    ) -> Tuple[Optional[bool], Optional[float]]:
        """Recursive evaluation.

        Returns:
            (satisfied, witness_time)
            - satisfied: True/False/None (None = vacuous)
            - witness_time: Time of violation (if any)
        """
        if idx >= len(events):
            # Past end of trace - depends on operator context
            return None, None

        current = events[idx]
        current_time = current.timestamp

        if isinstance(node, Atomic):
            return self._eval_atomic(node, current), None

        elif isinstance(node, Not):
            result, witness = self._eval(node.child, events, idx, horizon, base_time)
            if result is None:
                return None, None
            return not result, witness

        elif isinstance(node, And):
            left_result, left_witness = self._eval(node.left, events, idx, horizon, base_time)
            right_result, right_witness = self._eval(node.right, events, idx, horizon, base_time)

            if left_result is False:
                return False, left_witness
            if right_result is False:
                return False, right_witness
            if left_result is None or right_result is None:
                return None, None
            return True, None

        elif isinstance(node, Or):
            left_result, left_witness = self._eval(node.left, events, idx, horizon, base_time)
            right_result, right_witness = self._eval(node.right, events, idx, horizon, base_time)

            if left_result is True:
                return True, None
            if right_result is True:
                return True, None
            if left_result is None or right_result is None:
                return None, None
            return False, left_witness or right_witness

        elif isinstance(node, Implies):
            # φ → ψ ≡ ¬φ ∨ ψ
            left_result, _ = self._eval(node.left, events, idx, horizon, base_time)

            if left_result is False:
                return True, None  # Antecedent false → implication true
            if left_result is None:
                return None, None  # Vacuous

            return self._eval(node.right, events, idx, horizon, base_time)

        elif isinstance(node, Globally):
            return self._eval_globally(node, events, idx, horizon, base_time)

        elif isinstance(node, Eventually):
            return self._eval_eventually(node, events, idx, horizon, base_time)

        elif isinstance(node, Until):
            return self._eval_until(node, events, idx, horizon, base_time)

        elif isinstance(node, Next):
            if idx + 1 >= len(events):
                return None, None
            return self._eval(node.child, events, idx + 1, horizon, base_time)

        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    def _eval_atomic(self, node: Atomic, event: Event) -> bool:
        """Evaluate atomic proposition against event."""
        value = event.values.get(node.variable)
        if value is None:
            # Variable not present - treat as false
            return False

        ops = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
        }

        return ops[node.operator](value, node.value)

    def _eval_globally(
        self, node: Globally, events: List[Event], idx: int, horizon: float, base_time: float
    ) -> Tuple[Optional[bool], Optional[float]]:
        """G[a,b](φ): φ must hold at all times in [base_time + a, base_time + b]."""
        lower = base_time + node.lower_bound
        upper = base_time + (node.upper_bound if node.upper_bound is not None else horizon)

        any_in_range = False

        for i in range(idx, len(events)):
            t = events[i].timestamp
            if t < lower:
                continue
            if t > upper:
                break

            any_in_range = True
            result, witness = self._eval(node.child, events, i, horizon, t)

            if result is False:
                return False, t

        if not any_in_range:
            return None, None  # Vacuous - no events in range

        return True, None

    def _eval_eventually(
        self, node: Eventually, events: List[Event], idx: int, horizon: float, base_time: float
    ) -> Tuple[Optional[bool], Optional[float]]:
        """F[a,b](φ): φ must hold at some time in [base_time + a, base_time + b]."""
        lower = base_time + node.lower_bound
        upper = base_time + (node.upper_bound if node.upper_bound is not None else horizon)

        any_in_range = False

        for i in range(idx, len(events)):
            t = events[i].timestamp
            if t < lower:
                continue
            if t > upper:
                break

            any_in_range = True
            result, _ = self._eval(node.child, events, i, horizon, t)

            if result is True:
                return True, None

        if not any_in_range:
            return None, None  # Vacuous

        return False, lower  # Violated - never found satisfying event

    def _eval_until(
        self, node: Until, events: List[Event], idx: int, horizon: float, base_time: float
    ) -> Tuple[Optional[bool], Optional[float]]:
        """φ U[a,b] ψ: φ holds until ψ, with ψ occurring in [base_time + a, base_time + b]."""
        lower = base_time + node.lower_bound
        upper = base_time + (node.upper_bound if node.upper_bound is not None else horizon)

        # First, check that φ holds until some point where ψ holds
        for i in range(idx, len(events)):
            t = events[i].timestamp

            # Check if we're in the target interval for ψ
            if lower <= t <= upper:
                right_result, _ = self._eval(node.right, events, i, horizon, t)
                if right_result is True:
                    # ψ holds - until is satisfied
                    return True, None

            # Outside the interval, φ must hold
            left_result, witness = self._eval(node.left, events, i, horizon, t)
            if left_result is False:
                # φ failed before ψ held
                return False, t

            if t > upper:
                # Passed the interval without ψ holding
                break

        # ψ never held in the interval
        return False, upper

    def check_spec(
        self, spec: Dict[str, Any], trace: List[Union[Event, Dict[str, Any]]], horizon: Optional[float] = None
    ) -> Dict[str, MTLResult]:
        """Check a specification (multiple named formulas) against a trace.

        Args:
            spec: Dict mapping property names to formula strings
            trace: Event trace
            horizon: Time horizon

        Returns:
            Dict mapping property names to results
        """
        results = {}
        for name, formula_str in spec.items():
            try:
                formula = parse_mtl(formula_str)
                results[name] = self.evaluate(formula, trace, horizon)
            except MTLParseError as e:
                results[name] = MTLResult(status=MTLStatus.UNKNOWN, formula=formula_str, message=f"Parse error: {e}")
        return results


# =============================================================================
# Spec File Loader
# =============================================================================


def load_spec_file(path: str) -> Dict[str, str]:
    """Load MTL specification from YAML or JSON file.

    Args:
        path: Path to spec file

    Returns:
        Dict mapping property names to formula strings
    """
    import json

    with open(path, "r") as f:
        if path.endswith(".yaml") or path.endswith(".yml"):
            try:
                import yaml

                return yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML required for YAML spec files")
        else:
            return json.load(f)


# =============================================================================
# Convenience Functions
# =============================================================================


def globally(child: MTLNode, lower: float = 0.0, upper: Optional[float] = None) -> Globally:
    """Create Globally node."""
    return Globally(child, lower, upper)


def eventually(child: MTLNode, lower: float = 0.0, upper: Optional[float] = None) -> Eventually:
    """Create Eventually node."""
    return Eventually(child, lower, upper)


def until(left: MTLNode, right: MTLNode, lower: float = 0.0, upper: Optional[float] = None) -> Until:
    """Create Until node."""
    return Until(left, right, lower, upper)


def next_op(child: MTLNode) -> Next:
    """Create Next node."""
    return Next(child)


def atomic(variable: str, op: str, value: float) -> Atomic:
    """Create Atomic node."""
    return Atomic(variable, op, value)


def and_op(left: MTLNode, right: MTLNode) -> And:
    """Create And node."""
    return And(left, right)


def or_op(left: MTLNode, right: MTLNode) -> Or:
    """Create Or node."""
    return Or(left, right)


def not_op(child: MTLNode) -> Not:
    """Create Not node."""
    return Not(child)


def implies(left: MTLNode, right: MTLNode) -> Implies:
    """Create Implies node."""
    return Implies(left, right)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Status and Result
    "MTLStatus",
    "MTLResult",
    # AST Nodes
    "MTLNode",
    "Atomic",
    "Not",
    "And",
    "Or",
    "Implies",
    "Globally",
    "Eventually",
    "Until",
    "Next",
    # Parser
    "MTLParser",
    "MTLParseError",
    "parse_mtl",
    # Evaluator
    "Event",
    "MTLEngine",
    # Spec Loading
    "load_spec_file",
    # Convenience
    "globally",
    "eventually",
    "until",
    "next_op",
    "atomic",
    "and_op",
    "or_op",
    "not_op",
    "implies",
]
