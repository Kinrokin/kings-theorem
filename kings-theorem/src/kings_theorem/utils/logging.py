"""Project logging utilities placeholder.

Replace with structured logger configuration (json-log, handlers, formatters).
"""
import logging


def configure_logging(level=logging.INFO):
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
