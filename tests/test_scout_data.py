import logging

import geopandas as gpd
import hypothesis
from hypothesis.extra.pandas import column
from hypothesis.extra.pandas import data_frames
from hypothesis.extra.pandas import range_indexes
import hypothesis.strategies as st
import pandas as pd
import pytest

from incognita.data import scout_census
from incognita.data.scout_data import ScoutData
from incognita.utility import utility

COLUMN_NAME = "ctry"


@pytest.fixture(scope="module")
def scout_data_factory():
    """Returns a ScoutData factory"""

    def _scout_data_factory(data_df: pd.DataFrame) -> ScoutData:
        sd = ScoutData(load_census_data=False, merged_csv=False)
        sd.census_data = data_df
        return sd

    return _scout_data_factory


@pytest.fixture(scope="module")
def blank_geo_data_frame() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(columns=("id",), geometry=gpd.points_from_xy(x=(0,), y=(0,)), crs=utility.WGS_84)


CountryDataFrame = data_frames(
    columns=[
        column(name=COLUMN_NAME, elements=st.from_regex(r"^[A-Za-z]{2}[0-9]{8}\Z")),
    ],
    index=range_indexes(min_size=2),
)

LocationDataFrame = data_frames(
    columns=[
        column(name="lat", elements=st.floats(min_value=-85, max_value=85)),
        column(name="long", elements=st.floats(min_value=-180, max_value=180)),
    ],
    index=range_indexes(min_size=2),
)


def test_scout_data_columns(scout_data_factory):
    scout_data_stub = scout_data_factory(pd.DataFrame())

    column_labels = scout_census.column_labels
    columns = [*column_labels.id.values(), *column_labels.name.values()]

    assert scout_data_stub.filterable_columns == columns


@hypothesis.given(CountryDataFrame)
def test_filter_records_inclusion(scout_data_factory, data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)
    scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, mask=True, exclusion_analysis=False)

    expected_outcome = data.loc[~(data[COLUMN_NAME] == first_country_code)]
    assert scout_data_stub.census_data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion(scout_data_factory, data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)
    scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, mask=False, exclusion_analysis=False)

    expected_outcome = data.loc[data[COLUMN_NAME] == first_country_code]
    assert scout_data_stub.census_data.equals(expected_outcome)


@hypothesis.given(CountryDataFrame)
def test_filter_records_exclusion_analysis_with_incorrect_columns(scout_data_factory, data: pd.DataFrame):
    first_country_code = data.loc[0, COLUMN_NAME]
    scout_data_stub = scout_data_factory(data)

    with pytest.raises(ValueError):
        scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, mask=False, exclusion_analysis=True)
        scout_data_stub.filter_records(field=COLUMN_NAME, value_list={first_country_code}, mask=True, exclusion_analysis=True)


@hypothesis.given(LocationDataFrame)
@hypothesis.settings(deadline=250)  # extend deadline for pip CI testing
def test_add_shape_data_points_data(scout_data_factory, blank_geo_data_frame: gpd.GeoDataFrame, data: pd.DataFrame):
    sd = scout_data_factory(data)
    sd.add_shape_data("id", gdf=blank_geo_data_frame)

    points_data = gpd.points_from_xy(data.long, data.lat, crs=utility.WGS_84)
    assert points_data.equals(sd.points_data.geometry.array)


@hypothesis.given(LocationDataFrame)
@hypothesis.settings(deadline=300)  # set deadline to 300 milliseconds per run
def test_add_shape_data_merge(scout_data_factory, blank_geo_data_frame: gpd.GeoDataFrame, data: pd.DataFrame):
    sd = scout_data_factory(data)
    sd.add_shape_data("id", gdf=blank_geo_data_frame)

    points_data = gpd.GeoDataFrame(geometry=gpd.points_from_xy(data.long, data.lat), crs=utility.WGS_84)
    joined = gpd.sjoin(points_data, blank_geo_data_frame, how="left", op="intersects")
    merged = data.merge(joined[["id"]], how="left", left_index=True, right_index=True)
    assert sd.census_data.equals(merged)


def test_close_script(caplog: pytest.LogCaptureFixture, scout_data_factory):
    scout_data_stub = scout_data_factory(pd.DataFrame())

    caplog.set_level(logging.INFO)

    scout_data_stub.close()

    assert "Script finished, 0.00 seconds elapsed." in caplog.text
