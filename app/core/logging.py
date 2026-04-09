"""
CryptoGuard-R - Centralized Logging
Configure application-wide logging with file and console handlers.
Security: Do not log sensitive data (passwords, keys, tokens).
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Import config after it's defined - avoid circular import by lazy load
def _get_settings():
    from app.core.config import settings
    return settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure application logging.
    Uses config settings when available; falls back to defaults.
    """
    settings = _get_settings()

    level_str = log_level or ("DEBUG" if settings.debug else "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Create logs directory if file logging enabled
    if log_file is None:
        log_dir = settings.project_root.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "cryptoguard-r.log"

    # Root logger
    root_logger = logging.getLogger("cryptoguard_r")
    root_logger.setLevel(level)

    # Avoid duplicate handlers on reload
    if root_logger.handlers:
        return root_logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt)
    root_logger.addHandler(console)

    # File handler (append mode)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
            file_handler.setLevel(level)
            file_handler.setFormatter(fmt)
            root_logger.addHandler(file_handler)
        except OSError:
            root_logger.warning("Could not create log file %s; using console only", log_file)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a module. Prefer this over logging.getLogger()."""
    return logging.getLogger("cryptoguard_r").getChild(name)
