import logging
import time


class LogUtil:
    """Creates and returns a logger with preset options

    :param str name: name to give the logger
    :param file_path: file path to output debug log
    :return: logger object
    """

    def __init__(self, name, file_path=None):

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
        self.logger = logger

        self.start_time = time.time()

    def get_logger(self):
        return self.logger

    def duration(self, start_time=None):
        """Returns elapsed time since given start time"""

        if start_time is None:
            start_time = self.start_time

        return time.time() - start_time

    def message(self, action):
        self.logger.info(f"{action}")

    def finished_message(self, action, name=None, start_time=None):
        ending = f" in {name}." if name else "."
        self.logger.info(f"{action} finished. {self.duration(start_time):.2f} seconds elapsed{ending}")


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
    console.setFormatter(logging.Formatter(fmt="%(name)s - %(levelname)s - %(message)s"))

    # creates the main logger
    logger = logging.getLogger(name)
    # add the handler to the root logger
    logger.addHandler(console)

    return logger


def duration(start_time):
    """Returns elapsed time since given start time"""
    return time.time() - start_time
