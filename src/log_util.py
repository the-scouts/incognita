import logging
import time


def create_logger(name, file_path=None):
    """Creates and returns a logger with preset options

    :param str name: name to give the logger
    :param file_path: file path to output debug log
    :return: logger object
    """
    # set up a log to file
    if file_path:
        logging.basicConfig(filename=file_path, level=logging.DEBUG, filemode="w")

    # set up a log to the console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(fmt="%(filename)s - %(levelname)s - %(message)s"))

    # creates the main logger
    logger = logging.getLogger(name)
    # add the handler to the root logger
    logger.addHandler(console)

    return logger


def get_logger(name):
    return logging.getLogger(name)


def duration(start_time):
    """Returns elapsed time since given start time"""
    return time.time() - start_time
