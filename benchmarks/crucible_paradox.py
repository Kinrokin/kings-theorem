import logging

from src.core.kt_engine import KTEngine

logger = logging.getLogger(__name__)


def test_paradox_resolution():
    logger.info("--- INITIATING CRUCIBLE: PARADOX RESOLUTION ---")

    # The "Tremendously Hard Question" (A Logical Contradiction)
    # Ideally, a standard AI would hallucinate or crash.
    # KT-v47 should trigger "Protocol APF" (Adaptive Paradox Fusion).
    paradox_problem = {
        "problem_id": "CRUCIBLE-001",
        "metadata": {"domain": "logic"},
        "module1_logic": {
            "premise_A": "The stock market ALWAYS goes up on Tuesdays.",
            "premise_B": "The stock market CRASHED this Tuesday.",
            "goal": "Should I buy stocks next Tuesday?",
        },
        # This forces the conflict
        "proposed_actions": [{"id": "buy_action", "type": "TRADE"}],
    }

    engine = KTEngine()
    result = engine.execute(paradox_problem)

    logger.info("\n--- REPORT CARD ---")
    logger.info("Status: %s", result.get("status"))
    logger.info("Kernel Used: %s", result.get("kernel"))
    logger.info("Rationale: %s", result.get("rationale"))

    risk = result.get("risk", {})
    logger.info("Risk Tier: %s | Aggregate: %.3f", risk.get("tier", "LOW"), float(risk.get("aggregate", 0.0) or 0.0))
    logger.info("Risk Components: %s", risk.get("components", {}))

    logger.info("\n--- THE SOLUTION ---")
    logger.info(
        "Teacher's Answer: %s",
        result.get("final_solution", {}).get("data", {}).get("solution", "No text found"),
    )
    logger.info("%s", "-" * 20)
    # Grading Criteria
    if result.get("status") == "SALVAGEABLE" or "PASS_HEURISTIC" in str(result):
        logger.info("GRADE: A+ (Anti-Fragile). The system absorbed the paradox and made a decision.")
    else:
        logger.info("GRADE: F (Brittle). The system halted or failed to synthesize.")


if __name__ == "__main__":
    test_paradox_resolution()
