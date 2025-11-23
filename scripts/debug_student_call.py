from src.kernels.student_v42 import StudentKernelV42
import logging
from src.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

class Flakey:
    def __init__(self):
        self.calls = 0
    def __call__(self, **kwargs):
        self.calls += 1
        logger.info('Flakey called, count=%s', self.calls)
        if self.calls < 2:
            raise RuntimeError('transient')
        return 'recovered'

f = Flakey()
sk = StudentKernelV42(llm_call=f, max_retries=2)
logger.info('Calling pipeline...')
res = sk.staged_solve_pipeline({'task':'t'})
logger.info('Result: %s', res)
