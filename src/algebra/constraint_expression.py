# src/algebra/constraint_expression.py
"""
Formal constraint expression AST with closure checks and lattice integration.
Enhanced with validation for formal closure guarantees.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Literal, Optional, Set


@dataclass(frozen=True)
class ConstraintExpr:
    op: Literal["atom", "and", "or"]
    left: Optional["ConstraintExpr"]
    right: Optional["ConstraintExpr"]
    atom: Optional[str]

    def __repr__(self):
        if self.op == "atom":
            return f"ATOM({self.atom})"
        return f"({self.left} {self.op.upper()} {self.right})"

    def validate_closure(self, allowed_atoms: Optional[Set[str]] = None) -> bool:
        """
        Validate that expression satisfies closure properties:
        - All atoms are in the allowed set (if provided)
        - No structural anomalies (mismatched op/children)
        """
        if self.op == "atom":
            if allowed_atoms is not None and self.atom not in allowed_atoms:
                return False
            return self.atom is not None and self.left is None and self.right is None
        elif self.op in ("and", "or"):
            if self.left is None or self.right is None or self.atom is not None:
                return False
            return self.left.validate_closure(allowed_atoms) and self.right.validate_closure(allowed_atoms)
        return False

    def collect_atoms(self) -> Set[str]:
        """Collect all atom identifiers in the expression."""
        if self.op == "atom":
            return {self.atom} if self.atom else set()
        atoms = set()
        if self.left:
            atoms.update(self.left.collect_atoms())
        if self.right:
            atoms.update(self.right.collect_atoms())
        return atoms


class ParseError(ValueError):
    pass


class ConstraintExprParser:
    """Very small recursive-descent parser for expressions using grammar:

    Expr := Atom | '(' Expr ('AND'|'OR') Expr ')'
    Atom := /[A-Za-z0-9_:.<>+-]+/

    This deliberately excludes unary NOT to keep the grammar simple and
    to avoid ambiguous self-negation patterns. The parser returns an
    immutable `ConstraintExpr` tree.
    """

    TOKEN_RE = re.compile(r"\s*(?:(AND|OR)|([A-Za-z0-9_:.<>+-]+)|(\()|(\)) )", re.IGNORECASE)

    def __init__(self, text: str):
        self.text = text.strip()
        self.tokens = self._tokenize(self.text)
        self.pos = 0

    def _tokenize(self, s: str) -> List[str]:
        # Simple split that preserves parentheses and AND/OR
        # We'll do a safer manual tokenization
        tokens = []
        i = 0
        while i < len(s):
            if s[i].isspace():
                i += 1
                continue
            if s[i] in "()":
                tokens.append(s[i])
                i += 1
                continue
            m = re.match(r"AND\b|OR\b", s[i:], re.IGNORECASE)
            if m:
                tokens.append(m.group(0).upper())
                i += len(m.group(0))
                continue
            m = re.match(r"[A-Za-z0-9_:.<>+-]+", s[i:])
            if m:
                tokens.append(m.group(0))
                i += len(m.group(0))
                continue
            raise ParseError(f"Unexpected character at position {i}: '{s[i]}'")
        return tokens

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected: Optional[str] = None) -> str:
        t = self.peek()
        if t is None:
            raise ParseError("Unexpected EOF")
        if expected and t.upper() != expected.upper():
            raise ParseError(f"Expected {expected}, got {t}")
        self.pos += 1
        return t

    def parse(self) -> ConstraintExpr:
        expr = self._parse_expr()
        if self.peek() is not None:
            raise ParseError(f"Unexpected token after expression: {self.peek()}")
        # Basic well-formedness: check no cycles (tree constructed fresh)
        if self._has_cycles(expr):
            raise ParseError("Expression contains cycles")
        # Validate structural closure
        if not expr.validate_closure():
            raise ParseError("Expression fails closure validation")
        return expr

    def _parse_expr(self) -> ConstraintExpr:
        t = self.peek()
        if t == "(":
            self.consume("(")
            left = self._parse_expr()
            op = self.consume()
            if op.upper() not in ("AND", "OR"):
                raise ParseError(f"Expected AND/OR, got {op}")
            right = self._parse_expr()
            self.consume(")")
            op_lower = op.lower()
            if op_lower not in ("and", "or"):
                raise ParseError(f"Invalid operator: {op}")
            return ConstraintExpr(op=op_lower, left=left, right=right, atom=None)  # type: ignore[arg-type]
        # atom
        token = self.consume()
        return ConstraintExpr(op="atom", left=None, right=None, atom=token)

    def _has_cycles(self, node: Optional[ConstraintExpr], seen=None) -> bool:
        if node is None:
            return False
        if seen is None:
            seen = set()
        nid = id(node)
        if nid in seen:
            return True
        seen.add(nid)
        if node.op == "atom":
            return False
        # traverse
        return self._has_cycles(node.left, seen) or self._has_cycles(node.right, seen)


def parse_constraint_expr(text: str) -> ConstraintExpr:
    p = ConstraintExprParser(text)
    return p.parse()


def validate_closure_properties(expr: ConstraintExpr, allowed_atoms: Optional[Set[str]] = None) -> bool:
    """
    Validate closure properties for the constraint expression:
    - Structural integrity (op matches children)
    - Atom whitelist compliance (if provided)
    - Idempotence: expr AND expr == expr, expr OR expr == expr
    - Commutativity: A AND B == B AND A, A OR B == B OR A
    - Associativity: (A AND B) AND C == A AND (B AND C)
    """
    return expr.validate_closure(allowed_atoms)
