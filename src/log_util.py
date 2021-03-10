from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

FINISHED_LEVEL_NUM = logging.INFO + 5

# Create root logger
logger = logging.getLogger("geo_mapping")


def set_up_logger(file_path: Path = None, log_level: int = logging.DEBUG) -> logging.Logger:
    """Creates and returns a logger with preset options

    :param file_path: file path to output debug log
    :param log_level: log level
    :return: logger object
    """
    import sys

    # Set log level
    logger.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(fmt="{filename} - {levelname} - {message}", style="{")

    # set up a log to file
    if file_path is not None:
        file = logging.FileHandler(file_path, encoding="utf-8", mode="w")
        file.setFormatter(formatter)
        file.setLevel(log_level)
        logger.addHandler(file)

    # set up a log to the console
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(log_level)
    logger.addHandler(console)

    return logger


def _finished_message(self: logging.Logger, message: str, *args, **kwargs):
    import time

    if self.isEnabledFor(FINISHED_LEVEL_NUM):
        name = kwargs.pop("method_name") if kwargs.get("method_name") else None
        start_time = kwargs.pop("start_time")
        ending = f" in {name}." if name else "."
        self._log(FINISHED_LEVEL_NUM, f"{message} finished, {time.time() - start_time:.2f} seconds elapsed{ending}", args, **kwargs)


logging.FINISHED_MESSAGE = FINISHED_LEVEL_NUM  # Create Finished log level
logging.addLevelName(FINISHED_LEVEL_NUM, "INFO")  # Set what will show up as the level in the logs
logging.Logger.finished = _finished_message  # set the custom function
