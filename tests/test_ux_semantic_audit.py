# tests/test_ux_semantic_audit.py
from src.ux.semantic_audit import SemanticAuditor, SemanticIssue


def test_forbidden_framing_detection():
    """Test detection of absolutist framing patterns."""
    auditor = SemanticAuditor()
    
    text = "This is 100% certain and always correct. It's a proven fact."
    issues = auditor.audit(text)
    
    # Should detect forbidden patterns
    framing_issues = [i for i in issues if i.issue_type == "framing"]
    assert len(framing_issues) > 0, "Should detect absolutist framing"
    assert any("100% certain" in i.description for i in framing_issues)


def test_disclosure_requirement_high_stakes():
    """Test that high-stakes contexts require uncertainty disclosures."""
    auditor = SemanticAuditor()
    
    # Text without any uncertainty disclosure
    text = "This treatment will cure your condition. Use it daily."
    context = {"stakes": "critical", "domain": "medical"}
    
    issues = auditor.audit(text, context)
    
    # Should require disclosure
    omission_issues = [i for i in issues if i.issue_type == "omission"]
    assert len(omission_issues) > 0, "Should require disclosure in high-stakes context"
    assert any("uncertainty" in i.description.lower() for i in omission_issues)


def test_disclosure_not_required_low_stakes():
    """Test that low-stakes contexts don't require disclosures."""
    auditor = SemanticAuditor()
    
    text = "This is a simple statement."
    context = {"stakes": "low"}
    
    issues = auditor.audit(text, context)
    
    # Should not require disclosure for low stakes
    critical_issues = [i for i in issues if i.severity == "critical"]
    assert len(critical_issues) == 0, "Should not require disclosure in low-stakes"


def test_balanced_coverage_benefits_risks():
    """Test detection of imbalanced benefit/risk coverage."""
    auditor = SemanticAuditor()
    
    # Text with multiple 'benefit' keywords should trigger balance check
    text = "The benefit of this solution is clear. Another benefit is speed."
    issues = auditor.audit(text)
    
    bias_issues = [i for i in issues if i.issue_type == "bias"]
    assert len(bias_issues) > 0, "Should detect imbalanced coverage when benefit mentioned without risk/cost/drawback"
    assert any("benefit" in i.description.lower() for i in bias_issues)


def test_balanced_coverage_satisfied():
    """Test that balanced coverage passes audit."""
    auditor = SemanticAuditor()
    
    # Mentions both benefits and risks
    text = "This product has benefits for users, but also has risks and costs to consider."
    issues = auditor.audit(text)
    
    bias_issues = [i for i in issues if i.issue_type == "bias"]
    assert len(bias_issues) == 0, "Should accept balanced coverage"


def test_medical_side_effect_disclosure():
    """Test that medical contexts require side effect disclosure."""
    auditor = SemanticAuditor()
    
    text = "This medication is an effective treatment for the condition."
    context = {"domain": "medical", "stakes": "high"}
    
    issues = auditor.audit(text, context)
    
    omission_issues = [i for i in issues if i.issue_type == "omission" and "side effect" in i.description]
    assert len(omission_issues) > 0, "Should require side effect disclosure for medical treatment"


def test_financial_risk_disclosure():
    """Test that financial contexts require risk disclosure."""
    auditor = SemanticAuditor()
    
    text = "Invest in this product for high returns and profits."
    context = {"domain": "financial", "stakes": "high"}
    
    issues = auditor.audit(text, context)
    
    omission_issues = [i for i in issues if i.issue_type == "omission" and "risk" in i.description]
    assert len(omission_issues) > 0, "Should require risk disclosure for financial products"


def test_contradiction_detection():
    """Test detection of internal contradictions."""
    auditor = SemanticAuditor()
    
    text = "This system always works perfectly. Later it says the system doesn't work and fails often."
    issues = auditor.audit(text)
    
    contradiction_issues = [i for i in issues if i.issue_type == "contradiction"]
    assert len(contradiction_issues) > 0, "Should detect contradictions"


def test_superlative_excess_detection():
    """Test detection of excessive superlatives."""
    auditor = SemanticAuditor()
    
    text = "The best, perfect, ideal, optimal solution that is flawless and perfect."
    issues = auditor.audit(text)
    
    framing_issues = [i for i in issues if i.issue_type == "framing" and "superlative" in i.description]
    assert len(framing_issues) > 0, "Should detect excessive superlatives"


def test_passes_audit_clean_text():
    """Test that clean text passes audit."""
    auditor = SemanticAuditor()
    
    text = "This approach may help in most cases, though results can vary. Consider the tradeoffs carefully."
    context = {"stakes": "medium"}
    
    passes = auditor.passes_audit(text, context, max_severity="high")
    assert passes, "Clean balanced text should pass audit"


def test_fails_audit_critical_issue():
    """Test that text with critical issues fails audit."""
    auditor = SemanticAuditor()
    
    text = "This is 100% guaranteed to work perfectly."
    context = {"stakes": "critical"}
    
    passes = auditor.passes_audit(text, context, max_severity="medium")
    assert not passes, "Text with critical issues should fail audit"


def test_audit_report_generation():
    """Test that audit report is generated correctly."""
    auditor = SemanticAuditor()
    
    text = "Always guaranteed perfect results with zero risk."
    issues = auditor.audit(text)
    
    report = auditor.generate_report(issues)
    
    assert "semantic issue" in report.lower()
    assert len(report) > 50, "Report should contain detailed information"


def test_audit_report_clean():
    """Test report for clean text."""
    auditor = SemanticAuditor()
    
    text = "This may help in some cases."
    issues = auditor.audit(text)
    
    report = auditor.generate_report(issues)
    
    assert "no semantic issues" in report.lower()
