from __future__ import annotations

from pathlib import Path
import time

import geopandas as gpd
import pandas as pd

from incognita.data import scout_census
from incognita.data.ons_pd_may_19 import ons_postcode_directory_may_19
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import utility


class ScoutData:
    """Provides access to manipulate and process data."""

    @property
    def filterable_columns(self) -> set[str]:
        """Returns ID and name columns of the dataset"""
        id_cols = scout_census.column_labels.id.__dict__.values()
        name_cols = scout_census.column_labels.name.__dict__.values()
        return {*id_cols, *name_cols}

    # TODO: Add column name properties (e.g. scout_census.column_labels.VALID_POSTCODE

    def __init__(self, merged_csv: bool = True, census_path: Path = None, load_census_data: bool = True):
        # record a class-wide start time
        self.start_time = time.time()

        now = time.localtime()
        logger.info(f"Starting at {now.tm_hour}:{now.tm_min}:{now.tm_sec}")

        logger.info("Loading Scout Census data")
        # Loads Scout Census Data from a path to a .csv file that contains Scout Census data
        # We assume no custom path has been passed, but allow for one to be used
        census_path = config.SETTINGS.census_extract.merged if census_path is None else census_path
        self.scout_census: scout_census.ScoutCensus = scout_census.ScoutCensus(census_path, load_data=load_census_data)
        self.census_data: pd.DataFrame = self.scout_census.data
        self.points_data: gpd.GeoDataFrame = gpd.GeoDataFrame()
        logger.info(f"Loading Scout Census data finished, {time.time() - self.start_time:.2f} seconds elapsed.")

        if merged_csv:
            logger.info("Loading ONS data")
            start_time = time.time()

            # Check if the data has been merged with the ONS postcode directory
            if scout_census.column_labels.VALID_POSTCODE in self.census_data.columns:
                self.ons_pd = ons_postcode_directory_may_19
            else:
                raise Exception(f"The ScoutCensus file has no ONS data, because it doesn't have a {scout_census.column_labels.VALID_POSTCODE} column")

            logger.info(f"Loading {self.ons_pd.PUBLICATION_DATE} ONS data finished, {time.time() - start_time:.2f} seconds elapsed.")

    def filter_records(self, field: str, value_list: set, mask: bool = False, exclusion_analysis: bool = False) -> None:
        """Filters the Census records by any field in ONS PD.

        Args:
            field: The field on which to filter
            value_list: The values on which to filter
            mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
            exclusion_analysis:

        """
        self.census_data = utility.filter_records(self.census_data, field, value_list, mask, exclusion_analysis)

    def add_shape_data(self, shapes_key: str, path: Path = None, gdf: gpd.GeoDataFrame = None) -> None:
        if path is not None:
            uid = Path(f"{hash(self.census_data.shape)}_{shapes_key}_{path.stem}.feather")
            if uid.is_file():
                data = pd.read_feather(uid).set_index("index")
                assert self.census_data.equals(data[self.census_data.columns])
                self.census_data = data
                return
        else:
            uid = None

        if self.points_data.empty:
            idx = pd.Series(self.census_data.index, name="object_index")
            self.points_data = gpd.GeoDataFrame(idx, geometry=gpd.points_from_xy(self.census_data.long, self.census_data.lat), crs=utility.WGS_84)

        if path is not None:
            all_shapes = gpd.read_file(path)
        elif gdf is not None:
            all_shapes = gdf
        else:
            raise ValueError("A path to a shapefile or a GeoDataFrame must be passed")
        shapes = all_shapes[[shapes_key, "geometry"]].to_crs(epsg=utility.WGS_84)

        spatial_merged = gpd.sjoin(self.points_data, shapes, how="left", op="within").set_index("object_index")
        merged = self.census_data.merge(spatial_merged[[shapes_key]], how="left", left_index=True, right_index=True)
        assert self.census_data.equals(merged[self.census_data.columns])
        self.census_data = merged
        if path is not None and uid is not None:
            merged.reset_index(drop=False).to_feather(uid)

    def close(self) -> None:
        """Outputs the duration of the programme"""
        logger.info(f"Script finished, {time.time() - self.start_time:.2f} seconds elapsed.")
