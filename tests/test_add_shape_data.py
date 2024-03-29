from conftest import LocationDataFrame
import geopandas as gpd
import hypothesis
import pandas as pd

from incognita.data import add_shape_data
from incognita.utility import constants


@hypothesis.given(LocationDataFrame)
@hypothesis.settings(deadline=300)  # extend deadline for pip CI testing
def test_add_shape_data_points_data(blank_geo_data_frame: gpd.GeoDataFrame, data: pd.DataFrame):
    census_data = data
    new_data, new_points = add_shape_data.add_shape_data(census_data, "id", gdf=blank_geo_data_frame)

    points_data = gpd.points_from_xy(data.long, data.lat, crs=constants.WGS_84)
    assert points_data.equals(new_points.geometry.array)


@hypothesis.given(LocationDataFrame)
@hypothesis.settings(deadline=450)  # set deadline to 300 milliseconds per run
def test_add_shape_data_merge(blank_geo_data_frame: gpd.GeoDataFrame, data: pd.DataFrame):
    census_data = data
    new_data, new_points = add_shape_data.add_shape_data(census_data, "id", gdf=blank_geo_data_frame)

    points_data = gpd.GeoDataFrame(geometry=gpd.points_from_xy(data.long, data.lat), crs=constants.WGS_84)
    joined = gpd.sjoin(points_data, blank_geo_data_frame, how="left", op="intersects")
    merged = data.merge(joined[["id"]], how="left", left_index=True, right_index=True)
    assert new_data.equals(merged)
