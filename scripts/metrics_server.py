"""
AID: /scripts/metrics_server.py
Proof ID: PRF-METRICS-001
Axiom: Axiom 3 (Auditability)
Purpose: Prometheus exporter for research loop observability.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

from prometheus_client import Gauge, start_http_server

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Prometheus Gauges
g_current_epoch = Gauge("kt_current_epoch", "Current training epoch")
g_curriculum_level = Gauge("kt_curriculum_level", "Current curriculum difficulty level")
g_best_accuracy = Gauge("kt_best_accuracy", "Best validation accuracy achieved")
g_safety_violations = Gauge("kt_safety_violation_count", "Total safety violations detected")
g_crash_counter = Gauge("kt_crash_counter", "Number of recoverable crashes")
g_last_update = Gauge("kt_last_update_timestamp", "Unix timestamp of last state update")


def read_system_state(state_path: Path) -> Dict[str, Any]:
    """
    Read system state with Lazarus error handling.

    Returns:
        State dict or empty dict if file doesn't exist or is corrupted.
    """
    if not state_path.exists():
        logger.warning(f"State file not found: {state_path}")
        return {}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {state_path}: {e}")
        return {}
    except Exception as e:
        logger.exception(f"Unexpected error reading state: {e}")
        return {}


def update_metrics(state: Dict[str, Any]) -> None:
    """Update Prometheus gauges from state dict."""
    g_current_epoch.set(state.get("epoch", 0))
    g_curriculum_level.set(state.get("level", 1))
    g_best_accuracy.set(state.get("best_metric", 0.0))
    g_safety_violations.set(state.get("safety_violations", 0))
    g_crash_counter.set(state.get("crash_counter", 0))
    g_last_update.set(state.get("last_update_ts", time.time()))


def main() -> None:
    """Main metrics server loop."""
    port = 9100
    state_file = Path(__file__).resolve().parent.parent / "data" / "system_state.json"

    logger.info(f"Starting KT Metrics Server on port {port}")
    logger.info(f"Monitoring state file: {state_file}")

    # Start Prometheus HTTP server
    try:
        start_http_server(port)
        logger.info(f"✅ Metrics endpoint: http://0.0.0.0:{port}/metrics")
    except OSError as e:
        logger.critical(f"Failed to bind port {port}: {e}")
        sys.exit(1)

    # Continuous monitoring loop (Lazarus pattern: never die)
    crash_count = 0
    while True:
        try:
            state = read_system_state(state_file)
            if state:
                update_metrics(state)
                logger.debug(f"Metrics updated: epoch={state.get('epoch', 0)}")
            else:
                logger.debug("Empty state, metrics unchanged")

            time.sleep(10)  # 10-second polling interval

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            break
        except Exception as e:
            crash_count += 1
            logger.exception(f"Metrics loop crash #{crash_count}: {e}")
            g_crash_counter.set(crash_count)
            time.sleep(5)  # Brief pause before retry


if __name__ == "__main__":
    main()
