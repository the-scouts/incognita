import logging
import sys
import time

FINISHED_LEVEL_NUM = logging.INFO + 5
DURATION_LEVEL_NUM = logging.INFO + 4


def create_logger(name: str, file_path: str = None) -> logging.Logger:
    """Creates and returns a logger with preset options

    :param str name: name to give the logger
    :param file_path: file path to output debug log
    :return: logger object
    """
    # creates the main logger
    logger = logging.getLogger(name)

    # Set log level
    logger.setLevel(logging.DEBUG)

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

    return logger


def get_logger(name: str) -> logging.Logger:
    """Fetches a logger with the given name"""
    return logging.getLogger(name)


def duration(start_time: float) -> float:
    """Returns elapsed time since given start time"""
    return time.time() - start_time


def _finished_message(self, message: str, *args, **kwargs):
    if self.isEnabledFor(FINISHED_LEVEL_NUM):
        name = kwargs.pop("method_name") if kwargs.get("method_name") else None
        start_time = kwargs.pop("start_time")
        ending = f" in {name}." if name else "."
        self._log(FINISHED_LEVEL_NUM, f"{message} finished, {duration(start_time):.2f} seconds elapsed{ending}", args, **kwargs)


def _duration_message(self, method_name: str, *args, **kwargs):
    if self.isEnabledFor(DURATION_LEVEL_NUM):
        start_time = kwargs.pop("start_time")
        self._log(FINISHED_LEVEL_NUM, f"{method_name} took {duration(start_time):.2f} seconds", args, **kwargs)


logging.FINISHED_MESSAGE = FINISHED_LEVEL_NUM  # Create Finished log level
logging.addLevelName(FINISHED_LEVEL_NUM, "INFO")  # Set what will show up as the level in the logs
logging.Logger.finished = _finished_message  # set the custom function

logging.DURATION_MESSAGE = DURATION_LEVEL_NUM  # Create duration log level (info + 4)
logging.addLevelName(DURATION_LEVEL_NUM, "INFO")  # Set what will show up as the level in the logs ("INFO")
logging.Logger.duration = _duration_message  # set the custom function
