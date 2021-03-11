import json
import logging
from numbers import Real

import pandas as pd
import pytest

from incognita import utility
from incognita.data import ons_pd
from incognita.logger import logger
from incognita.utility.utility import time_function


class ONSPostcodeDirectoryStub(ons_pd.ONSPostcodeDirectory):
    def __init__(self):
        super().__init__(load_data=False, ons_pd_csv_path="")
        self.IMD_MAX = {"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890}
        self.COUNTRY_CODES = {"E92000001": "England", "W92000004": "Wales", "S92000003": "Scotland", "N92000002": "Northern Ireland"}


def add(number1: Real, number2: Real) -> Real:
    return number1 + number2


def test_calc_imd_decile():
    data = {"row_1": [1, "E92000001", 32844], "row_2": [2, "W92000004", 1]}
    frame = pd.DataFrame.from_dict(data, orient="index", columns=["id", "ctry", "imd"])

    imd_decile_data: pd.Series = utility.calc_imd_decile(frame["imd"], frame["ctry"], ONSPostcodeDirectoryStub())
    predicted_result = pd.Series(data=[10, 1], index=["row_1", "row_2"], name="imd_decile")

    assert isinstance(imd_decile_data, pd.Series)
    assert imd_decile_data.equals(predicted_result)


def test_settings_are_accurate():
    with open(utility.SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]

    assert utility.SETTINGS == settings


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
