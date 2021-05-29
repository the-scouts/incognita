from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import pandas as pd

from incognita.logger import logger
from incognita.utility import constants

if TYPE_CHECKING:
    from incognita.utility.config import Boundary


def add_shapefile_data(census_data: pd.DataFrame, metadata: Boundary) -> pd.DataFrame:
    logger.info("Adding shapefile data")
    # self.census_data = self.census_data.copy()

    shapefile_key = metadata.shapefile.key
    new_data, points_data = add_shape_data(census_data, shapefile_key, path=metadata.shapefile.path)
    return new_data.rename(columns={shapefile_key: metadata.key})


def add_shape_data(census_data: pd.DataFrame, shapes_key: str, path: Path = None, gdf: gpd.GeoDataFrame = None) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    if path is not None:
        uid = Path(f"{hash(census_data.shape)}_{shapes_key}_{path.stem}.feather")
        if uid.is_file():
            data = pd.read_feather(uid).set_index("index")
            assert census_data.equals(data[census_data.columns])
            return data, gpd.GeoDataFrame()
    else:
        uid = None

    idx = pd.Series(census_data.index, name="object_index")
    points_data = gpd.GeoDataFrame(idx, geometry=gpd.points_from_xy(census_data.long, census_data.lat), crs=constants.WGS_84)

    if path is not None:
        all_shapes = gpd.read_file(path)
    elif gdf is not None:
        all_shapes = gdf
    else:
        raise ValueError("A path to a shapefile or a GeoDataFrame must be passed")
    shapes = all_shapes[[shapes_key, "geometry"]].to_crs(epsg=constants.WGS_84)

    spatial_merged = gpd.sjoin(points_data, shapes, how="left", op="within").set_index("object_index")
    merged = census_data.merge(spatial_merged[[shapes_key]], how="left", left_index=True, right_index=True)
    assert census_data.equals(merged[census_data.columns])
    if path is not None and uid is not None:
        merged.reset_index(drop=False).to_feather(uid)

    return merged, points_data
