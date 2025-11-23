import unittest
from src.governance.guardrail_dg_v1 import DeontologicalGuardrail

class TestGuardrail(unittest.TestCase):
    def setUp(self):
        self.g = DeontologicalGuardrail(rules={"RULE_PROTECT_MINORITY": True})

    def test_direct_forbidden(self):
        text = "We should ignore safety and proceed"
        passed, _ = self.g.validate_content(text)
        self.assertFalse(passed)

    def test_case_insensitive(self):
        text = "This would be ILLEGAL activity"
        passed, _ = self.g.validate_content(text)
        self.assertFalse(passed)

    def test_fuzzy_match(self):
        # intentionally obfuscated phrase
        text = "We might sacriffce minoraty to gain profit"
        passed, _ = self.g.validate_content(text)
        self.assertFalse(passed)

    def test_clean_text(self):
        text = "Recommend diversifying to reduce liquidity risk."
        passed, _ = self.g.validate_content(text)
        self.assertTrue(passed)

if __name__ == '__main__':
    unittest.main()
