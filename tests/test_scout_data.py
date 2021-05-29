import logging
import time

from conftest import COLUMN_NAME
from conftest import CountryDataFrame
import hypothesis
import pandas as pd
import pytest

from incognita.utility import filter
from incognita.utility import timing


@hypothesis.given(CountryDataFrame)
def test_filter_records_inclusion(data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    census_data = data
    census_data = filter.filter_records(census_data, field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=True, exclusion_analysis=False)

    expected_outcome = data.loc[~(data[COLUMN_NAME] == first_country_code)]
    assert census_data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion(data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    census_data = data
    census_data = filter.filter_records(census_data, field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=False, exclusion_analysis=False)

    expected_outcome = data.loc[data[COLUMN_NAME] == first_country_code]
    assert census_data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion_analysis_with_incorrect_columns(data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    census_data = data

    with pytest.raises(ValueError):
        census_data = filter.filter_records(census_data, field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=False, exclusion_analysis=True)
        census_data = filter.filter_records(census_data, field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=True, exclusion_analysis=True)


def test_close_script(caplog: pytest.LogCaptureFixture):
    start_time = time.time()

    caplog.set_level(logging.INFO)

    timing.close(start_time)

    assert "Script finished, 0.00 seconds elapsed." in caplog.text
