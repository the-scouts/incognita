from __future__ import annotations

from functools import wraps
import time
from typing import TYPE_CHECKING

from src.logger import logger

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
