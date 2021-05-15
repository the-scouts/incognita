from __future__ import annotations

from functools import wraps
import time
from typing import TYPE_CHECKING

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import config

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

sections_model = scout_census.column_labels.sections
section_types = {section_model.type: section_name for section_name, section_model in sections_model}

# EPSG values for the co-ordinate reference systems that we use
WGS_84 = 4326  # World Geodetic System 1984 (Used in GPS)
BNG = 27700  # British National Grid


def time_function(method: Callable) -> Callable:
    """This method wraps functions to determine the execution time (clock time) for the function

    Incredible wrapping SO answer https://stackoverflow.com/a/1594484 (for future ref)

    The 'wrapped' method is the method that actually replaces all the normal method calls, with the
      normal method call inside

    Args:
        method: method to wrap

    Returns:
        wrapped method with execution time functionality

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


def save_report(report: pd.DataFrame, report_name: str) -> None:
    logger.info(f"Writing to {report_name}")
    report.to_csv(config.SETTINGS.folders.output / f"{report_name}.csv", index=False, encoding="utf-8-sig")
