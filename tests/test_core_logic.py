"""
AID: /tests/test_core_logic.py
Proof ID: PRF-TEST-001
"""
import unittest
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail

class TestGovernance(unittest.TestCase):
    def setUp(self):
        self.rules = {"RULE_PROTECT_MINORITY": True}
        self.guard = DeontologicalGuardrail(self.rules)

    def test_clean_content(self):
        text = "This is a safe financial strategy."
        passed, _ = self.guard.validate_content(text)
        self.assertTrue(passed)

    def test_forbidden_content_simple(self):
        text = "We should ignore safety to maximize profit."
        passed, reason = self.guard.validate_content(text)
        self.assertFalse(passed)
        self.assertIn("ignore safety", reason)

    def test_forbidden_content_regex(self):
        text = "Let's execute a p-u-m-p and d.u.m.p scheme."
        passed, reason = self.guard.validate_content(text)
        self.assertFalse(passed)
        self.assertIn("pump", reason)

if __name__ == '__main__':
    unittest.main()
