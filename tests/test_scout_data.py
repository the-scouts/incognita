import pandas as pd
import geopandas as gpd

import pytest
import hypothesis
import hypothesis.strategies as st
from hypothesis.extra.pandas import data_frames, column, range_indexes

from data.scout_census import ScoutCensus
from src.data.scout_data import ScoutData


COLUMN_NAME = "ctry"


@pytest.fixture(scope="module")
def scout_data_factory():
    """Returns a ScoutData factory"""

    def _scout_data_factory(data_df: pd.DataFrame):
        sd = ScoutData(load_census_data=False, load_ons_pd_data=False, merged_csv=False)
        sd.data = data_df
        return sd

    return _scout_data_factory


@pytest.fixture(scope="module")
def blank_geo_data_frame():
    gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(*zip([0] * 2)))
    gdf["id"] = 0
    gdf.crs = 4326
    return gdf


CountryDataFrame = data_frames(columns=[column(name=COLUMN_NAME, elements=st.from_regex(r"^[A-Za-z]{2}[0-9]{8}\Z"))], index=range_indexes(min_size=2),)

LocationDataFrame = data_frames(
    columns=[column(name="lat", elements=st.floats(min_value=-85, max_value=85)), column(name="long", elements=st.floats(min_value=-180, max_value=180)),],
    index=range_indexes(min_size=2),
)


def test_scout_data_columns(scout_data_factory):
    scout_data_stub = scout_data_factory(pd.DataFrame())

    column_labels = ScoutCensus.column_labels
    columns = [*column_labels["id"].values(), *column_labels["name"].values()]

    assert scout_data_stub.columns == columns


@hypothesis.given(CountryDataFrame)
def test_filter_records_inclusion(scout_data_factory, data):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)
    scout_data_stub.filter_records(field=COLUMN_NAME, value_list=[first_country_code], mask=True, exclusion_analysis=False)

    expected_outcome = data.loc[~(data[COLUMN_NAME] == first_country_code)]
    assert scout_data_stub.data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion(scout_data_factory, data):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)
    scout_data_stub.filter_records(field=COLUMN_NAME, value_list=[first_country_code], mask=False, exclusion_analysis=False)

    expected_outcome = data.loc[data[COLUMN_NAME] == first_country_code]
    assert scout_data_stub.data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion_analysis_with_incorrect_columns(scout_data_factory, data):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)

    with pytest.raises(ValueError):
        scout_data_stub.filter_records(field=COLUMN_NAME, value_list=[first_country_code], mask=False, exclusion_analysis=True)
        scout_data_stub.filter_records(field=COLUMN_NAME, value_list=[first_country_code], mask=True, exclusion_analysis=True)
