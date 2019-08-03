import logging
import time

FINISHED_LEVEL_NUM = logging.INFO + 5

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


def finished_message(self, message, *args, **kwargs):
    if self.isEnabledFor(FINISHED_LEVEL_NUM):
        name = kwargs.pop("name") if kwargs.get("name") else None
        start_time = kwargs.pop("start_time")
        ending = f" in {name}." if name else "."
        self._log(FINISHED_LEVEL_NUM, f"{message} finished, {duration(start_time):.2f} seconds elapsed{ending}", args, **kwargs)


logging.FINISHED_MESSAGE = FINISHED_LEVEL_NUM  # Create Finished log level
logging.addLevelName(FINISHED_LEVEL_NUM, "INFO")  # Set what will show up as the level in the logs
logging.Logger.finished = finished_message  # set the custom function
