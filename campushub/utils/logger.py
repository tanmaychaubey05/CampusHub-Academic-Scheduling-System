"""
Centralized logging configuration for CampusHub.
Logs to both console and a rotating log file in the logs/ directory.
"""

import logging
import os
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "campushub.log"


def setup_logger(name: str = "campushub") -> logging.Logger:
    """Configures and returns a domain logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # File Handler
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)  # Keep console clean during standard usage
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        ch.setFormatter(console_formatter)
        logger.addHandler(ch)

    return logger
