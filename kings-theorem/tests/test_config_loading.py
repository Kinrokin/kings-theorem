from kings_theorem.config import KTConfig


def test_config_loads():
    cfg = KTConfig()
    assert cfg is not None
