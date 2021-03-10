import json
import logging
from numbers import Real

import pytest

from src.base import Base
from src.base import time_function
from src.log_util import logger
from src.utility import SCRIPTS_ROOT


def add(number1: Real, number2: Real) -> Real:
    return number1 + number2


class ExampleClassLogger(Base):
    @time_function
    def add(self, number1: Real, number2: Real) -> Real:
        logger.info("Example Function")
        return number1 + number2


def test_time_function_wraps_function():
    assert time_function(add)(2, 2) == add(2, 2)


# noinspection PyTypeChecker
def test_time_function_raises_exception_on_non_method_arguments():
    with pytest.raises(ValueError):
        time_function("not a function or method")


def test_base_open_settings():
    assert isinstance(Base(settings=True).settings, dict)


def test_base_settings_are_accurate():
    with open(SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]

    assert Base(settings=True).settings == settings


def test_time_function_no_logger_entity():
    try:
        time_function(add)(2, 2)
    except AttributeError:
        pytest.fail(f"Unexpected AttributeError in base.test_function")


def test_time_function_logger_output(caplog):
    caplog.set_level(logging.INFO)
    ExampleClassLogger().add(2, 2)

    assert "Calling function add" in caplog.text
    assert "add took 0.0" in caplog.text


def test_base_close_script(caplog):
    caplog.set_level(logging.INFO)
    Base().close()

    assert "Script finished, 0.00 seconds elapsed." in caplog.text
