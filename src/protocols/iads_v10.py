def detect_asymmetry(source_a: float, source_b: float, tolerance: float = 0.05) -> bool:
    return abs(source_a - source_b) > tolerance
