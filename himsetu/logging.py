"""Logging initialization and formatting module for HIMSETU.

Provides colorized console output and structured file logging.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init as colorama_init

from himsetu.config import AppConfig

# Initialize colorama for cross-platform ANSI support
colorama_init(autoreset=True)


class ColorFormatter(logging.Formatter):
    """Custom colorized log formatter for console output."""

    LEVEL_COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, "")
        levelname = f"{color}{record.levelname:<8}{Style.RESET_ALL}"
        record_copy = logging.makeLogRecord(record.__dict__)
        record_copy.levelname = levelname
        return super().format(record_copy)


def setup_logger(
    config: Optional[AppConfig] = None,
    name: str = "himsetu",
    level: Optional[str] = None,
    log_file: Optional[Path | str] = None,
) -> logging.Logger:
    """Initialize and configure a logger instance without creating duplicate handlers.

    Args:
        config: Optional AppConfig instance.
        name: Logger name.
        level: Explicit log level string (overrides config log_level if provided).
        log_file: Explicit log file path (overrides config log_file_path if provided).

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Determine effective log level
    target_level_str = level or (config.log_level if config else "INFO")
    numeric_level = getattr(logging, target_level_str.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Prevent duplicate handlers if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.propagate = False

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_format = "%(asctime)s | %(levelname)s | %(name)s - %(message)s"
    console_formatter = ColorFormatter(fmt=console_format, datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (Optional)
    target_log_file = log_file or (config.log_file_path if config else None)
    if target_log_file:
        file_path = Path(target_log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s - %(message)s"
        file_formatter = logging.Formatter(fmt=file_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
