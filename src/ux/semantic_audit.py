# src/ux/semantic_audit.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Dict, Optional
import re
import logging

logger = logging.getLogger("kt.ux.semantic")
logger.setLevel(logging.INFO)


@dataclass
class SemanticIssue:
    """Represents a detected semantic manipulation issue."""
    issue_type: str  # "framing", "omission", "bias", "contradiction"
    severity: str  # "low", "medium", "high", "critical"
    description: str
    location: str  # where in the text
    suggested_fix: Optional[str] = None


class SemanticAuditor:
    """
    Semantic audit for UX outputs to detect manipulation patterns
    that pass token-level checks but manipulate via framing and omission.
    
    Complements UX token checks with semantic-level analysis.
    """
    
    def __init__(
        self,
        required_disclosures: Set[str] = None,
        forbidden_frames: Set[str] = None,
        balance_keywords: Dict[str, Set[str]] = None
    ):
        # Required disclosures (e.g., "limitations", "uncertainty", "assumptions")
        self.required_disclosures = required_disclosures or {
            "limitation", "assumption", "uncertain", "may not", "could be"
        }
        
        # Forbidden framing patterns (e.g., absolute claims, false authority)
        self.forbidden_frames = forbidden_frames or {
            "always correct", "never wrong", "100% certain", "guaranteed",
            "proven fact", "absolute truth", "indisputable"
        }
        
        # Balance keywords: if discussing A, must also mention B
        # e.g., {"benefit": {"risk", "cost", "tradeoff"}}
        self.balance_keywords = balance_keywords or {
            "benefit": {"risk", "cost", "drawback", "tradeoff", "downside"},
            "advantage": {"disadvantage", "limitation", "constraint"},
            "pro": {"con", "against"},
        }
    
    def audit(self, text: str, context: Dict[str, any] = None) -> List[SemanticIssue]:
        """
        Perform semantic audit on text. Returns list of detected issues.
        context: optional metadata (e.g., topic, audience, stakes)
        """
        issues = []
        text_lower = text.lower()
        
        # 1) Check for forbidden framing
        issues.extend(self._check_forbidden_framing(text, text_lower))
        
        # 2) Check for required disclosures (if high-stakes context)
        if context and context.get("stakes", "low") in ("high", "critical"):
            issues.extend(self._check_disclosures(text, text_lower))
        
        # 3) Check for balanced coverage
        issues.extend(self._check_balance(text, text_lower))
        
        # 4) Check for omission patterns
        issues.extend(self._check_omissions(text, text_lower, context))
        
        # 5) Check for internal contradictions
        issues.extend(self._check_contradictions(text, text_lower))
        
        return issues
    
    def _check_forbidden_framing(self, text: str, text_lower: str) -> List[SemanticIssue]:
        """Detect absolutist or manipulative framing."""
        issues = []
        
        for pattern in self.forbidden_frames:
            if pattern in text_lower:
                # Find location
                match = re.search(re.escape(pattern), text_lower)
                loc = f"char {match.start()}" if match else "unknown"
                
                issues.append(SemanticIssue(
                    issue_type="framing",
                    severity="high",
                    description=f"Forbidden framing pattern detected: '{pattern}'",
                    location=loc,
                    suggested_fix="Use qualified language (e.g., 'likely', 'generally', 'in most cases')"
                ))
        
        # Check for excessive superlatives
        superlatives = re.findall(r'\b(best|worst|perfect|ideal|optimal|flawless)\b', text_lower)
        if len(superlatives) > 3:
            issues.append(SemanticIssue(
                issue_type="framing",
                severity="medium",
                description=f"Excessive superlatives ({len(superlatives)} instances): {set(superlatives)}",
                location="throughout",
                suggested_fix="Use more measured language"
            ))
        
        return issues
    
    def _check_disclosures(self, text: str, text_lower: str) -> List[SemanticIssue]:
        """Check for required uncertainty/limitation disclosures."""
        issues = []
        
        # Check if ANY disclosure keyword is present
        has_disclosure = any(keyword in text_lower for keyword in self.required_disclosures)
        
        if not has_disclosure:
            issues.append(SemanticIssue(
                issue_type="omission",
                severity="critical",
                description="No uncertainty or limitation disclosure found in high-stakes context",
                location="global",
                suggested_fix="Add disclaimer about assumptions, limitations, or uncertainty"
            ))
        
        return issues
    
    def _check_balance(self, text: str, text_lower: str) -> List[SemanticIssue]:
        """Check for balanced coverage of topics (e.g., benefits vs risks)."""
        issues = []
        
        for primary, required_balance in self.balance_keywords.items():
            # Count mentions of primary keyword
            primary_count = len(re.findall(rf'\b{primary}\b', text_lower))
            
            if primary_count > 0:
                # Check if any balance keyword is present
                balance_found = any(
                    re.search(rf'\b{bal}\b', text_lower)
                    for bal in required_balance
                )
                
                if not balance_found:
                    issues.append(SemanticIssue(
                        issue_type="bias",
                        severity="high",
                        description=f"Imbalanced coverage: '{primary}' mentioned {primary_count}x without discussing {required_balance}",
                        location="global",
                        suggested_fix=f"Also discuss: {', '.join(list(required_balance)[:3])}"
                    ))
        
        return issues
    
    def _check_omissions(self, text: str, text_lower: str, context: Dict[str, any] = None) -> List[SemanticIssue]:
        """Detect suspicious omissions based on context."""
        issues = []
        
        # If discussing medical/health, must mention side effects
        if context and context.get("domain") == "medical":
            if "treatment" in text_lower or "medication" in text_lower:
                if "side effect" not in text_lower and "adverse" not in text_lower:
                    issues.append(SemanticIssue(
                        issue_type="omission",
                        severity="critical",
                        description="Medical treatment discussed without side effect disclosure",
                        location="global",
                        suggested_fix="Add side effects and contraindications"
                    ))
        
        # If discussing financial products, must mention risks
        if context and context.get("domain") == "financial":
            if "invest" in text_lower or "return" in text_lower:
                if "risk" not in text_lower and "loss" not in text_lower:
                    issues.append(SemanticIssue(
                        issue_type="omission",
                        severity="critical",
                        description="Financial product discussed without risk disclosure",
                        location="global",
                        suggested_fix="Add risk warnings and disclaimers"
                    ))
        
        return issues
    
    def _check_contradictions(self, text: str, text_lower: str) -> List[SemanticIssue]:
        """Detect internal contradictions in the text."""
        issues = []
        
        # Simple contradiction patterns
        contradiction_pairs = [
            (r'\b(always|never)\b', r'\b(sometimes|occasionally)\b'),
            (r'\b(safe|secure)\b', r'\b(risk|danger|unsafe)\b'),
            (r'\b(effective|works)\b', r'\b(ineffective|doesn\'t work|fails)\b'),
        ]
        
        for pattern_a, pattern_b in contradiction_pairs:
            has_a = bool(re.search(pattern_a, text_lower))
            has_b = bool(re.search(pattern_b, text_lower))
            
            if has_a and has_b:
                issues.append(SemanticIssue(
                    issue_type="contradiction",
                    severity="medium",
                    description=f"Potential contradiction: text contains both '{pattern_a}' and '{pattern_b}' patterns",
                    location="global",
                    suggested_fix="Review for consistency"
                ))
        
        return issues
    
    def passes_audit(self, text: str, context: Dict[str, any] = None, max_severity: str = "medium") -> bool:
        """
        Returns True if text passes audit (no issues above max_severity).
        max_severity: highest allowed severity ("low", "medium", "high", "critical")
        """
        issues = self.audit(text, context)
        
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_level = severity_levels.get(max_severity, 1)
        
        for issue in issues:
            issue_level = severity_levels.get(issue.severity, 0)
            if issue_level > max_level:
                logger.warning(f"Semantic audit failed: {issue.description}")
                return False
        
        return True
    
    def generate_report(self, issues: List[SemanticIssue]) -> str:
        """Generate human-readable audit report."""
        if not issues:
            return "✓ No semantic issues detected"
        
        report_lines = [f"Found {len(issues)} semantic issue(s):\n"]
        
        # Group by severity
        by_severity = {"critical": [], "high": [], "medium": [], "low": []}
        for issue in issues:
            by_severity[issue.severity].append(issue)
        
        for severity in ["critical", "high", "medium", "low"]:
            if by_severity[severity]:
                report_lines.append(f"\n{severity.upper()} ({len(by_severity[severity])}):")
                for issue in by_severity[severity]:
                    report_lines.append(f"  • [{issue.issue_type}] {issue.description}")
                    if issue.suggested_fix:
                        report_lines.append(f"    → Fix: {issue.suggested_fix}")
        
        return "\n".join(report_lines)
