import logging
import time


def create_logger(name, file_path=None):
    # set up a log to file
    if file_path:
        logging.basicConfig(filename=file_path, level=logging.DEBUG, filemode="w")

    # set up a log to the console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(fmt="%(name)s - %(levelname)s - %(message)s"))

    # creates the main logger
    logger = logging.getLogger(name)
    # add the handler to the root logger
    logger.addHandler(console)

    return logger


def duration(start_time):
    return time.time() - start_time