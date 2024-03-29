from pathlib import Path
import sys

import geopandas as gpd
from hypothesis.extra.pandas import column
from hypothesis.extra.pandas import data_frames
from hypothesis.extra.pandas import range_indexes
import hypothesis.strategies as st
import pytest

# https://github.com/pytest-dev/pytest/issues/2421#issuecomment-403724503
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incognita.utility import constants  # NoQA: E402

COLUMN_NAME = "ctry"


@pytest.fixture(scope="module")
def blank_geo_data_frame() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(columns=("id",), geometry=gpd.points_from_xy(x=(0,), y=(0,)), crs=constants.WGS_84)


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
