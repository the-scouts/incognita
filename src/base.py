from __future__ import annotations

from functools import wraps
import json
import time
from typing import TYPE_CHECKING

from src.logger import logger
from src.utility import SCRIPTS_ROOT

if TYPE_CHECKING:
    from collections.abc import Callable


def time_function(method: Callable):
    """This method wraps functions to determine the execution time (clock time) for the function

    The function should be of a class with a logger logging object

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
        logger.info(f"Calling function {method.__name__}")

        # call the original method with the passed arguments and keyword arguments, and store the result
        output = method(self, *args, **kwargs)
        logger.info(f"{method.__name__} took {time.time() - start_time:.2f} seconds")

        # return the output of the original function
        return output

    return wrapper


class Base:
    def __init__(self, settings: bool = False):
        """Acts as a base class for most classes. Provides automatic logging, settings creation,
          and common methods

        :param bool settings: If true, load settings from the config file
        """

        # record a class-wide start time
        self.start_time = time.time()

        # Load the settings file
        if settings:
            self.settings = json.loads(SCRIPTS_ROOT.joinpath("settings.json").read_text())["settings"]

    def close(self, start_time: float = None):
        """Outputs the duration of the programme """
        start_time = start_time if start_time else self.start_time
        logger.info(f"Script finished, {time.time() - start_time:.2f} seconds elapsed.")
