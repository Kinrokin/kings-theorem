import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.utils.crypto import generate_keypair
import logging
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    setup_logging()
    if not os.path.exists('keys'): os.makedirs('keys')
    generate_keypair('operator', 'keys')
    generate_keypair('internal_automation', 'keys')
    logger.info('Keys Generated.')
