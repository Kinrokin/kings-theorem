import base64
import logging
import os
import random
import sys
import time

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

logger = logging.getLogger(__name__)


def sign_and_submit(token, rationale, retries=5):
    with open("keys/operator.pem", "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)

    # Ed25519 direct signing, hash is internal to the process
    sig = priv.sign(token.encode())
    sig_b64 = base64.b64encode(sig).decode("utf-8")

    payload = {"token": token, "signature": sig_b64, "rationale": rationale}
    headers = {"x-api-key": os.environ.get("KT_API_KEY", "kthitl_dev")}

    logger.info("--- Submitting Token %s... ---", token[:12])
    for i in range(retries):
        try:
            res = requests.post("http://localhost:8000/approve", json=payload, headers=headers, timeout=5)
            logger.info("Status: %s | Response: %s", res.status_code, res.json())
            return
        except requests.exceptions.ConnectionError:
            logger.error("Connection refused. Is the engine running (run_engine.py)?")
            sys.exit(1)
        except Exception as e:
            delay = (2**i) + random.uniform(0, 0.5)
            logger.warning("Retry %d in %.2fs: %s", i + 1, delay, e)
            time.sleep(delay)


if __name__ == "__main__":
    from src.logging_config import setup_logging

    setup_logging()
    if len(sys.argv) < 3:
        logger.error("Usage: python src/scripts/operator_client.py <TOKEN> <RATIONALE>")
        sys.exit(1)
    sign_and_submit(sys.argv[1], sys.argv[2])
