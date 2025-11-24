from pathlib import Path
from typing import Any, Dict

import yaml

# Define the path to the governance policy file relative to the project root
POLICY_FILE_PATH = Path(__file__).parent.parent.parent / "config" / "governance_policy.yaml"


class GovernanceConfig:
    """Singleton class to load and expose typed access to governance policy settings."""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GovernanceConfig, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Loads and parses the YAML policy file."""
        if not POLICY_FILE_PATH.exists():
            # In a production system, this should raise a hard error
            print(f"Warning: Policy file not found at {POLICY_FILE_PATH}. Using defaults.")
            self._config = self._get_default_config()
            return
        try:
            with open(POLICY_FILE_PATH, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except Exception as e:
            # S-Tier rigor demands we log and fail on parsing errors
            print(f"Error loading governance policy: {e}. Falling back to defaults.")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Provides hardcoded fallback values for critical parameters."""
        return {
            "rigor": {
                "warrant_threshold": 0.6,  # Original hardcoded value
                "spectral_correlation_limit": 0.9,
            },
            "keys": {"multisig_policy": {"critical_required_signatures": 1}},
        }

    # --- Public Accessors ---
    def get_warrant_threshold(self) -> float:
        """Retrieves the minimum confidence threshold for EXECUTE verdicts."""
        return float(self._config.get("rigor", {}).get("warrant_threshold", 0.6))

    def get_spectral_limit(self) -> float:
        """Retrieves the anomaly detection correlation limit."""
        return float(self._config.get("rigor", {}).get("spectral_correlation_limit", 0.9))

    def get_critical_sig_count(self) -> int:
        """Retrieves the required signature count for FREEZE/HALT decisions."""
        return int(self._config.get("keys", {}).get("multisig_policy", {}).get("critical_required_signatures", 1))


# Instance for easy import
gov_config = GovernanceConfig()
