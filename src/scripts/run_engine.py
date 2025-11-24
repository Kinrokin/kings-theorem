import os
import sys
import threading
import time

import numpy as np
import uvicorn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging

from src.api.server import app
from src.governance.decision_broker import DecisionBroker
from src.governance.tri_governor import TriGovernor
from src.metrics.anomaly import detect_adaptive_replay_anomaly, detect_adversarial_flood
from src.metrics.spectral_guard import check_spectral_correlation

logger = logging.getLogger(__name__)


def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical")


def main():
    t = threading.Thread(target=run_api, daemon=True)
    t.start()
    time.sleep(2)
    logger.info(">>> KT-v53.6 SOVEREIGN REFLECTOR ONLINE <<<")

    # 1. Adaptive Guards Demo
    stream = np.random.randn(300)
    if detect_adaptive_replay_anomaly(stream):
        logger.warning("! ALERT: Replay Anomaly.")
    else:
        logger.info("[+] Guards: PASS")

    broker = DecisionBroker()
    gov = TriGovernor()

    # 2. Scenario A: Constitutional Singularity
    logger.info("\n[*] Scenario A: Constitutional Singularity (Requires Human Sign-off)")
    prop = {"id": "OP-SING", "tags": ["unethical"], "replay_confidence": 0.4}
    res = gov.adjudicate(prop)
    logger.info("    Verdict: %s", res.get("decision"))
    logger.info("    Flags:   %s", res.get("audit_flags"))

    broker_res = broker.process_request(res, prop)
    if broker_res["status"] == "ESCROWED":
        logger.info("    [!] LOCKED: %s (Use client to sign)", broker_res.get("token"))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown.")


if __name__ == "__main__":
    from src.logging_config import setup_logging

    setup_logging()
    main()
