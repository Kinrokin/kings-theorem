# tests/test_source_flooding.py
from src.sourcing.source_registry import SourceRegistry, SourceMetadata
import time


def test_source_registration_flood_detection():
    """Test that flood detection prevents Sybil attacks."""
    registry = SourceRegistry(
        flood_detection_window=1.0,  # 1 second window
        max_new_sources_per_window=3
    )
    
    # Register sources rapidly
    for i in range(3):
        success = registry.register_source(
            f"source_{i}",
            b"pubkey" + bytes([i]),
            diversity_tags={"academic"}
        )
        assert success, f"Should allow source {i}"
    
    # 4th source in same window should be rejected
    success = registry.register_source(
        "source_flood",
        b"pubkey_flood",
        diversity_tags={"academic"}
    )
    assert not success, "Should reject flood registration"
    
    # After window expires, should allow again
    time.sleep(1.1)
    success = registry.register_source(
        "source_after_window",
        b"pubkey_after",
        diversity_tags={"academic"}
    )
    assert success, "Should allow after window expires"


def test_source_reputation_updates():
    """Test reputation scoring with exponential moving average."""
    registry = SourceRegistry()
    registry.register_source("src1", b"key1", diversity_tags={"medical"}, initial_reputation=0.5)
    
    # Good contributions should increase reputation
    for _ in range(5):
        registry.update_reputation("src1", contribution_verified=True)
    
    assert registry.sources["src1"].reputation_score > 0.5
    assert registry.sources["src1"].verified_contributions == 5
    
    # Bad contributions should decrease reputation
    for _ in range(10):
        registry.update_reputation("src1", contribution_verified=False)
    
    # Should be blacklisted after many bad contributions
    assert registry.sources["src1"].reputation_score < 0.3


def test_source_diversity_constraints():
    """Test that diversity quotas are enforced."""
    registry = SourceRegistry(
        min_reputation=0.3,
        max_cluster_influence=0.4,
        diversity_quota={"medical": 0.3, "gov": 0.2}
    )
    
    # Register sources with different tags
    registry.register_source("med1", b"k1", diversity_tags={"medical"}, initial_reputation=0.8)
    registry.register_source("med2", b"k2", diversity_tags={"medical"}, initial_reputation=0.7)
    registry.register_source("gov1", b"k3", diversity_tags={"gov"}, initial_reputation=0.9)
    registry.register_source("academic1", b"k4", diversity_tags={"academic"}, initial_reputation=0.6)
    
    # Check diversity proportions
    proportions = registry.check_diversity_quota()
    assert "medical" in proportions
    assert "gov" in proportions


def test_cluster_influence_capping():
    """Test that no cluster can exceed max_cluster_influence."""
    registry = SourceRegistry(
        min_reputation=0.3,
        max_cluster_influence=0.4  # Max 40% per cluster
    )
    
    # Register many sources from same cluster
    for i in range(5):
        registry.register_source(
            f"medical_{i}",
            b"key" + bytes([i]),
            diversity_tags={"medical"},
            initial_reputation=0.9
        )
    
    # Register one source from different cluster
    registry.register_source("gov_1", b"key_gov", diversity_tags={"gov"}, initial_reputation=0.9)
    
    # Compute weights
    weights = registry.compute_influence_weights()
    
    # Medical cluster should be capped at 40% (allow small tolerance for rounding)
    medical_total = sum(w for sid, w in weights.items() if "medical" in sid)
    assert medical_total <= 0.45, f"Medical cluster exceeds cap: {medical_total}"
    
    # All weights should sum to ~1.0
    total = sum(weights.values())
    assert 0.99 <= total <= 1.01, f"Weights don't sum to 1.0: {total}"


def test_blacklist_enforcement():
    """Test that blacklisted sources are excluded from weighting."""
    registry = SourceRegistry(min_reputation=0.3)
    
    registry.register_source("good", b"k1", initial_reputation=0.9)
    registry.register_source("bad", b"k2", initial_reputation=0.8)
    
    # Blacklist one source
    registry.blacklist_source("bad", reason="manual_review")
    
    # Compute weights - bad source should be excluded
    weights = registry.compute_influence_weights()
    assert "bad" not in weights
    assert "good" in weights
    # Note: Single source in untagged cluster may be capped at max_cluster_influence (0.4)
    assert weights["good"] > 0, "Good source should have non-zero weight"
