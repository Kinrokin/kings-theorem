"""
Test entropy monitoring and homogenization detection.
"""
import pytest


def test_entropy_high_diversity():
    """Test that diverse outputs have high entropy."""
    from src.kernels.entropy_monitor import EntropyMonitor
    import numpy as np

    monitor = EntropyMonitor(window_size=100, entropy_threshold=0.3, num_bins=10)

    # Generate diverse outputs
    for i in range(100):
        output = {"value": np.random.uniform(0, 10)}
        monitor.record_output("k1", output)

    entropy = monitor.compute_entropy("k1")
    assert entropy > 0.5, f"Diverse outputs should have high entropy, got {entropy}"
    assert not monitor.check_homogenization("k1")


def test_entropy_homogenized():
    """Test that homogenized outputs trigger low entropy flag."""
    from src.kernels.entropy_monitor import EntropyMonitor

    monitor = EntropyMonitor(window_size=100, entropy_threshold=0.5, num_bins=10)

    # Generate nearly identical outputs (homogenized) - truly uniform values
    for i in range(100):
        output = {"value": 5.0}  # Completely uniform
        monitor.record_output("k2", output)

    entropy = monitor.compute_entropy("k2")
    assert entropy < 0.2, f"Homogenized outputs should have very low entropy, got {entropy}"
    assert monitor.check_homogenization("k2")


def test_entropy_report():
    """Test entropy report generation."""
    from src.kernels.entropy_monitor import EntropyMonitor

    monitor = EntropyMonitor(window_size=50, entropy_threshold=0.4)

    for i in range(50):
        monitor.record_output("k3", {"x": i, "y": i * 2})

    report = monitor.get_report("k3")
    assert report["kernel_id"] == "k3"
    assert "entropy" in report
    assert "is_homogenized" in report
    assert report["sample_count"] == 50


def test_entropy_flags():
    """Test that flags are recorded and can be retrieved."""
    from src.kernels.entropy_monitor import EntropyMonitor

    monitor = EntropyMonitor(window_size=100, entropy_threshold=0.5, num_bins=10)

    # Homogenized outputs
    for i in range(100):
        monitor.record_output("k4", {"value": 1.0})

    monitor.check_homogenization("k4")
    flags = monitor.get_flags("k4")
    assert len(flags) > 0
    assert "Low entropy" in flags[0]

    # Clear flags
    monitor.clear_flags("k4")
    assert len(monitor.get_flags("k4")) == 0


def test_entropy_multiple_kernels():
    """Test monitoring multiple kernels independently."""
    from src.kernels.entropy_monitor import EntropyMonitor
    import numpy as np

    monitor = EntropyMonitor(window_size=100, entropy_threshold=0.3)

    # k5: diverse
    for i in range(100):
        monitor.record_output("k5", {"value": np.random.uniform(0, 10)})

    # k6: homogenized
    for i in range(100):
        monitor.record_output("k6", {"value": 5.0})

    assert not monitor.check_homogenization("k5")
    assert monitor.check_homogenization("k6")
