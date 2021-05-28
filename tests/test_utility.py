import logging
from numbers import Real

import pandas as pd
from pandas.testing import assert_series_equal
import pytest
import toml

from incognita.data import ons_pd
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import deciles
from incognita.utility import root
from incognita.utility.timing import time_function

ons_postcode_directory_stub = ons_pd.ONSPostcodeDirectory(
    fields=set(),
    index_column="",
    data_types={},
    PUBLICATION_DATE="",
    IMD_MAX={"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890},
    COUNTRY_CODES={"E92000001": "England", "W92000004": "Wales", "S92000003": "Scotland", "N92000002": "Northern Ireland"},
)


def add(number1: Real, number2: Real) -> Real:
    return number1 + number2


def test_calc_imd_decile():
    data = {"row_1": [1, "E92000001", 32844], "row_2": [2, "W92000004", 1]}
    frame = pd.DataFrame.from_dict(data, orient="index", columns=["id", "ctry", "imd"])

    imd_decile_data: pd.Series = deciles.calc_imd_decile(frame["imd"], frame["ctry"], ons_postcode_directory_stub)
    predicted_result = pd.Series(data=[10, 1], index=["row_1", "row_2"])

    assert isinstance(imd_decile_data, pd.Series)
    assert_series_equal(imd_decile_data, predicted_result, check_dtype=False)


def test_settings_are_accurate():
    with open(root.PROJECT_ROOT.joinpath("incognita-config.toml"), "r") as read_file:
        settings = toml.load(read_file)

    assert config._SETTINGS_TOML == settings


def test_settings_model_is_accurate():
    with open(root.PROJECT_ROOT.joinpath("incognita-config.toml"), "r") as read_file:
        settings = toml.load(read_file)

    assert config.SETTINGS == config._create_settings(settings)


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
