from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Create root logger
logger = logging.getLogger("incognita")


def set_up_logger(file_path: Path = None, log_level: int = logging.DEBUG) -> logging.Logger:
    """Creates and returns a logger with preset options

    :param file_path: file path to output debug log
    :param log_level: log level
    :return: logger object
    """
    import sys

    # Create formatter
    formatter = logging.Formatter(fmt="{filename} - {levelname} - {message}", style="{")

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
