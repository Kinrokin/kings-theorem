import logging
from dataclasses import dataclass

from src.governance.guardrail_v2 import PrefilterCache, get_baseline_policy_pack, score_text
from src.primitives.risk_math import aggregate_risk

logger = logging.getLogger(__name__)


@dataclass
class TrinityScores:
    """Composite evaluation across three dimensions.

    Attributes:
        divergence: Semantic divergence (0=same, 1=very different)
        epistemic: Internal consistency (0=poor, 1=strong)
        risk: Governance risk proxy (0=safe, 1=critical)
        composite: Aggregated risk using weighted complement product
    """

    divergence: float
    epistemic: float
    risk: float
    composite: float


def _token_set(text: str) -> set:
    return set(w.lower() for w in text.split())


def compute_trinity(student_text: str, teacher_text: str) -> TrinityScores:
    """Compute Trinity Multi-Vector scores using lightweight heuristics.

    - Divergence: Jaccard distance over token sets
    - Epistemic: Penalize when teacher contradicts student length/structure drastically
    - Risk: Use guardrail score as proxy (max of student/teacher)
    - Composite: Aggregate via complement-product with tuned weights
    """
    # Divergence (Jaccard distance)
    s_set, t_set = _token_set(student_text), _token_set(teacher_text)
    if not s_set and not t_set:
        divergence = 0.0
    else:
        inter = len(s_set & t_set)
        union = max(1, len(s_set | t_set))
        divergence = 1.0 - (inter / union)

    # Epistemic (very rough): favor similar lengths; clamp to [0,1]
    sl, tl = max(1, len(student_text)), max(1, len(teacher_text))
    ratio = min(sl, tl) / max(sl, tl)
    epistemic = max(0.0, min(1.0, ratio))

    # Risk via guardrail score
    pack = get_baseline_policy_pack()
    pre = PrefilterCache()
    s_score, _, _ = score_text(student_text, pack, prefilter=pre)
    t_score, _, _ = score_text(teacher_text, pack, prefilter=pre)
    risk = max(s_score, t_score)

    # Aggregate
    composite = aggregate_risk(
        {"divergence": divergence, "epistemic": 1.0 - epistemic, "risk": risk},
        {"divergence": 0.25, "epistemic": 0.25, "risk": 0.6},
    )

    logger.info(
        "Trinity: divergence=%.3f epistemic=%.3f risk=%.3f composite=%.3f",
        divergence,
        epistemic,
        risk,
        composite,
    )
    return TrinityScores(divergence, epistemic, risk, composite)
