import json
import time
from functools import wraps

import src.log_util as log_util
from utility import SCRIPTS_ROOT


def time_function(method):
    """This method wraps every .

    Incredible wrapping SO answer https://stackoverflow.com/a/1594484 (for future ref)

    The 'wrapped' method is the method that actually replaces all the normal method calls, with the
      normal method call inside

    :param function method: method to wrap
    :return function: wrapped method with execution time functionality
    """
    if not callable(method):
        raise ValueError("time_function must be called with a function or callable to wrap")

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # record a start time for the function
        start_time = time.time()

        # Try to log calling the function
        try:
            self.logger.info(f"Calling function {method.__name__}")
        except AttributeError:
            pass

        # call the original method with the passed arguments and keyword arguments, and store the result
        output = method(self, *args, **kwargs)

        # Try to log how long the function took
        try:
            self.logger.duration(method.__name__, start_time=start_time)
        except AttributeError:
            pass

        # return the output of the original function
        return output
    return wrapper


class Base:
    def __init__(self, settings=False, log_path=None):
        """Acts as a base class for most classes. Provides automatic logging, settings creation,
          and common methods

        :param bool settings: If true, load settings from the config file
        :param str log_path: Path to store the log. If not set, get the global log
        """

        # record a class-wide start time
        self.start_time = time.time()

        # Load the settings file
        if settings:
            with open(SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
                self.settings = json.load(read_file)["settings"]

        # The global logger is named log, which means there is only ever one instance
        # if passed a path to output the log to, create the logger at that path
        # otherwise retrieve the standard logger
        if log_path:
            self.logger = log_util.create_logger('log', log_path)
        else:
            # if a logger already exists for script
            self.logger = log_util.get_logger('log')

    def close(self, start_time=None):
        """Outputs the duration of the programme """
        start_time = start_time if start_time else self.start_time
        self.logger.finished(f"Script", start_time=start_time)
