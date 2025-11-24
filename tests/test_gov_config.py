from src.utils.gov_config import GovernanceConfig, gov_config


def test_gov_config_loads_defaults_and_values():
    # gov_config should load the file we committed earlier
    assert isinstance(gov_config.get_warrant_threshold(), float)
    assert isinstance(gov_config.get_spectral_limit(), float)
    assert isinstance(gov_config.get_critical_sig_count(), int)
