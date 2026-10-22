"""
SYNCHROFLOW AI — Structured Logging Setup
"""

import logging
import sys


def setup_logging():
    log_format = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Suppress verbose websocket debug noise
    logging.getLogger("websockets").setLevel(logging.WARNING)


logger = logging.getLogger("synchroflow")
