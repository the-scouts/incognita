import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.joinpath('src')))

import json
import logging
import pytest

from base import Base, time_function
from utility import LOGS_ROOT, SCRIPTS_ROOT


def example_function(number1, number2):
    return number1 + number2


class ExampleClassLogger(Base):
    def __init__(self, path=True):
        if path:
            super().__init__(log_path=str(LOGS_ROOT.joinpath('tests.log')))
        else:
            super().__init__()

    @time_function
    def example_function(self, number1, number2):
        self.logger.info("Example Function")
        return number1 + number2


class ExampleClassSettings(Base):
    def __init__(self):
        super().__init__(settings=True)


def test_time_function_wraps_function():
    assert time_function(example_function)(2, 2) == example_function(2, 2)


# noinspection PyTypeChecker
def test_time_function_raises_exception_on_non_method_arguments():
    with pytest.raises(ValueError):
        time_function('not a function or method')


def test_time_function_no_logger_entity():
    try:
        time_function(example_function)(2, 2)
    except AttributeError:
        pytest.fail(f"Unexpected AttributeError in base.test_function")


def test_time_function_logger_output(caplog):
    caplog.set_level(logging.INFO)
    ExampleClassLogger().example_function(2, 2)

    assert 'Calling function example_function' in caplog.text
    assert 'example_function took 0.0' in caplog.text


def test_base_open_settings():
    assert isinstance(ExampleClassSettings().settings, dict)


def test_base_settings_are_accurate():
    with open(SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]

    assert ExampleClassSettings().settings == settings


def test_base_logger_creation():
    ec = ExampleClassLogger()
    assert isinstance(ec.logger, logging.Logger)


def test_base_logger_retrieval():
    ec0 = ExampleClassLogger(path=True)
    ec1 = ExampleClassLogger(path=False)

    assert ec1.logger is not None
    assert ec0.logger == ec1.logger


def test_base_close_script(caplog):
    caplog.set_level(logging.INFO)
    ec = ExampleClassLogger()
    ec.close()

    assert 'Script finished, 0.00 seconds elapsed.' in caplog.text
