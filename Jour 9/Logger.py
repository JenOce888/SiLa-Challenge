"""
Logger.py — Centralized logging for the Task Manager.

Usage:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Task created: %s", title)
    log.warning("Task #%d not found", task_id)
    log.error("Database error: %s", str(e))

Log file: task_manager.log (rotates at 1MB, keeps 3 backups)
Console: shows WARNING and above so it's not noisy during dev.
"""

import logging
import logging.handlers
import os

LOG_FILE = "task_manager.log"
LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)-20s — %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _setup_root_logger():
    root = logging.getLogger("taskmanager")
    root.setLevel(logging.DEBUG)  # Capture everything at root level

    # ── File handler: DEBUG and above, rotates at 1 MB ──
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,   # 1 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # ── Console handler: WARNING and above ──
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return root


# Initialize once when this module is first imported
_root_logger = _setup_root_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Returns a child logger namespaced under 'taskmanager'.
    Pass __name__ from each module for automatic naming.

    Example:
        log = get_logger(__name__)   # → taskmanager.models
    """
    return logging.getLogger(f"taskmanager.{name}")
