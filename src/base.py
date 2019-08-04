import json
import time
from types import FunctionType

from src.log_util import duration, create_logger, get_logger
from functools import wraps


def wrapper(method):
    @wraps(method)
    def wrapped(self, *args, exec_tm=False, **kwargs):
        if exec_tm:
            start_time = time.time()
            try:
                self.logger.info(f"Calling function {method.__name__}")
            except AttributeError:
                pass

            output = method(self, *args, **kwargs)

            try:
                self.logger.info(f"{method.__name__} took {duration(start_time):.2f} seconds")
            except AttributeError:
                pass

            return output
        else:
            return method(self, *args, **kwargs)
    return wrapped


class BaseMeta(type):
    def __new__(mcs, classname, bases, class_dict):
        new_class_dict = {}
        for attributeName, attribute in class_dict.items():
            if isinstance(attribute, FunctionType):
                # replace it with a wrapped version
                attribute = wrapper(attribute)
            new_class_dict[attributeName] = attribute
        return type.__new__(mcs, classname, bases, new_class_dict)


class Base(metaclass=BaseMeta):
    def __init__(self, settings=False, log_path=None):
        """Acts to manage all functions, providing setup, logging and timing.

        :param bool settings: If true, load settings from the config file
        :param str log_path: Path to store the log. If not set, get the global log

        """
        self.start_time = time.time()
        if settings:
            # Load the settings file
            with open("settings.json", "r") as read_file:
                self.settings = json.load(read_file)["settings"]

        # Facilitates logging
        if log_path:
            # if a logger already exists for script
            self.logger = create_logger('log', log_path)
        else:
            self.logger = get_logger('log')

    def close(self, start_time=None):
        """Outputs the duration of the programme """
        if not start_time:
            start_time = self.start_time
        self.logger.finished(f"Script", start_time=start_time)
