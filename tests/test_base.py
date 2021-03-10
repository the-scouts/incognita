import logging
from numbers import Real

import pytest

from src.base import time_function
from src.logger import logger


def add(number1: Real, number2: Real) -> Real:
    return number1 + number2


class ExampleClassLogger:
    @time_function
    def add(self, number1: Real, number2: Real) -> Real:
        logger.info("Example Function")
        return number1 + number2


def test_time_function_wraps_function():
    assert time_function(add)(2, 2) == add(2, 2)


def test_time_function_raises_exception_on_non_method_arguments():
    with pytest.raises(ValueError):
        time_function("not a function or method")  # NoQA


def test_time_function_logger_output(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO)

    ExampleClassLogger().add(2, 2)

    assert "Calling function add" in caplog.text
    assert "add took 0.0" in caplog.text


def test_base_close_script(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO)

    Base().close()

    assert "Script finished, 0.00 seconds elapsed." in caplog.text
