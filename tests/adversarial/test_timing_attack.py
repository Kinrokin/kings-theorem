"""
Test timing attack defenses and timeout enforcement.
"""
import time


def test_timing_defense_within_timeout():
    """Test that functions within timeout execute normally."""
    from src.governance.timing_defense import TimingConfig, TimingDefense

    config = TimingConfig(default_timeout=1.0)
    defense = TimingDefense(config)

    def fast_func():
        time.sleep(0.1)
        return "success"

    result, timed_out = defense.execute_with_timeout("k1", fast_func)
    assert result == "success"
    assert not timed_out

    stats = defense.get_stats("k1")
    assert stats.total_calls == 1
    assert stats.timeout_count == 0


def test_timing_defense_timeout_detection():
    """Test that timeouts are detected."""
    from src.governance.timing_defense import TimingConfig, TimingDefense

    config = TimingConfig(default_timeout=0.2)
    defense = TimingDefense(config)

    def slow_func():
        time.sleep(0.5)
        return "too slow"

    result, timed_out = defense.execute_with_timeout("k2", slow_func)
    assert timed_out
    assert result == "too slow"  # Still returns result but flagged

    stats = defense.get_stats("k2")
    assert stats.timeout_count == 1
    assert stats.consecutive_timeouts == 1


def test_timing_defense_blacklist():
    """Test that repeated timeouts trigger blacklisting."""
    from src.governance.timing_defense import TimeoutStrategy, TimingConfig, TimingDefense

    config = TimingConfig(default_timeout=0.1, strategy=TimeoutStrategy.BLACKLIST, blacklist_threshold=3)
    defense = TimingDefense(config)

    def slow_func():
        time.sleep(0.2)
        return "slow"

    # First 3 timeouts
    for i in range(3):
        defense.execute_with_timeout("k3", slow_func)

    stats = defense.get_stats("k3")
    assert stats.is_blacklisted
    assert "consecutive timeouts" in stats.blacklist_reason

    # Next call should be rejected
    result, timed_out = defense.execute_with_timeout("k3", slow_func)
    assert result is None
    assert timed_out


def test_timing_defense_reset_on_success():
    """Test that consecutive timeout counter resets on success."""
    from src.governance.timing_defense import TimingConfig, TimingDefense

    config = TimingConfig(default_timeout=0.2)
    defense = TimingDefense(config)

    def slow_func():
        time.sleep(0.3)
        return "slow"

    def fast_func():
        time.sleep(0.05)
        return "fast"

    # Timeout
    defense.execute_with_timeout("k4", slow_func)
    stats = defense.get_stats("k4")
    assert stats.consecutive_timeouts == 1

    # Success should reset
    defense.execute_with_timeout("k4", fast_func)
    stats = defense.get_stats("k4")
    assert stats.consecutive_timeouts == 0


def test_deterministic_tiebreaker():
    """Test deterministic tie-breaking with equal warrants."""
    from src.governance.timing_defense import TimingDefense

    defense = TimingDefense()

    candidates = [
        ("arbiter", 0.95, "hash3"),
        ("student", 0.95, "hash1"),
        ("teacher", 0.95, "hash2"),
    ]

    # Should be deterministic: same input always yields same output
    winner1 = defense.deterministic_tiebreaker(candidates)
    winner2 = defense.deterministic_tiebreaker(candidates)
    assert winner1 == winner2

    # Should sort by kernel_id when warrants are equal
    assert winner1 == "arbiter"  # Alphabetically first


def test_timing_stats_tracking():
    """Test that timing statistics are accurately tracked."""
    from src.governance.timing_defense import TimingConfig, TimingDefense

    config = TimingConfig(default_timeout=1.0)
    defense = TimingDefense(config)

    def variable_func(duration):
        time.sleep(duration)
        return "done"

    # Execute multiple times with varying durations
    durations = [0.1, 0.2, 0.15, 0.3]
    for d in durations:
        defense.execute_with_timeout("k5", variable_func, args=(d,))

    stats = defense.get_stats("k5")
    assert stats.total_calls == 4
    assert stats.avg_execution_time > 0.1
    assert stats.max_execution_time >= 0.3


def test_unblacklist():
    """Test manual unblacklisting of kernels."""
    from src.governance.timing_defense import TimeoutStrategy, TimingConfig, TimingDefense

    config = TimingConfig(default_timeout=0.1, strategy=TimeoutStrategy.BLACKLIST, blacklist_threshold=2)
    defense = TimingDefense(config)

    def slow_func():
        time.sleep(0.2)
        return "slow"

    # Trigger blacklist
    for i in range(2):
        defense.execute_with_timeout("k6", slow_func)

    stats = defense.get_stats("k6")
    assert stats.is_blacklisted

    # Unblacklist
    defense.unblacklist("k6")
    stats = defense.get_stats("k6")
    assert not stats.is_blacklisted
    assert stats.consecutive_timeouts == 0
