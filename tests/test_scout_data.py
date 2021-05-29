import logging

import hypothesis
import pandas as pd
import pytest

from conftest import COLUMN_NAME
from conftest import CountryDataFrame


@hypothesis.given(CountryDataFrame)
def test_filter_records_inclusion(scout_data_factory, data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)
    scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=True, exclusion_analysis=False)

    expected_outcome = data.loc[~(data[COLUMN_NAME] == first_country_code)]
    assert scout_data_stub.census_data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion(scout_data_factory, data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)
    scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=False, exclusion_analysis=False)

    expected_outcome = data.loc[data[COLUMN_NAME] == first_country_code]
    assert scout_data_stub.census_data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion_analysis_with_incorrect_columns(scout_data_factory, data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)

    with pytest.raises(ValueError):
        scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=False, exclusion_analysis=True)
        scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, exclude_matching=True, exclusion_analysis=True)


def test_close_script(caplog: pytest.LogCaptureFixture, scout_data_factory):
    scout_data_stub = scout_data_factory(pd.DataFrame())

    caplog.set_level(logging.INFO)

    scout_data_stub.close()

    assert "Script finished, 0.00 seconds elapsed." in caplog.text
