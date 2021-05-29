from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Create root logger
logger = logging.getLogger("incognita")


def set_up_logger(file_path: Path = None, log_level: int = logging.DEBUG) -> logging.Logger:
    """Creates and returns a logger with preset options

    Args:
        file_path: file path to output debug log
        log_level: log level

    Returns:
        logger object

    """
    import sys

    # Create formatter
    formatter = logging.Formatter(fmt="{asctime}.{msecs:03.0f} ({levelname}): {message}", datefmt="%Y-%m-%d %H:%M:%S", style="{")

    # set up a log to file
    if file_path is not None:
        file = logging.FileHandler(file_path, encoding="utf-8", mode="w")
        file.setFormatter(formatter)
        logger.addHandler(file)

    # set up a log to the console
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Set log level
    for log_filterer in (logger, *logger.handlers):
        log_filterer.setLevel(log_level)

    return logger


set_up_logger()
