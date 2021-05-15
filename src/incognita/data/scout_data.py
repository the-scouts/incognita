from __future__ import annotations

from pathlib import Path
import time

import geopandas as gpd
import pandas as pd
from pyarrow import feather

from incognita.data.scout_census import column_labels
from incognita.data.ons_pd_may_19 import ons_postcode_directory_may_19
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import filter
from incognita.utility import constants


class ScoutData:
    """Provides access to manipulate and process data."""

    def __init__(self, merged_csv: bool = True, load_census_data: bool = True):
        # record a class-wide start time
        self.start_time = time.time()
        logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime())}")

        # Loads Scout Census Data from disk.
        logger.info("Loading Scout Census data")
        self.census_data = feather.read_feather(config.SETTINGS.census_extract.merged) if load_census_data else pd.DataFrame()
        logger.info(f"Loading Scout Census data finished, {time.time() - self.start_time:.2f} seconds elapsed.")
        self.points_data = gpd.GeoDataFrame()

        # Check if the data has been merged with the ONS postcode directory
        if merged_csv and column_labels.VALID_POSTCODE not in self.census_data.columns:
            raise ValueError(f"The ScoutCensus file has no ONS data, because it doesn't have a {column_labels.VALID_POSTCODE} column")
        self.ons_pd = ons_postcode_directory_may_19
        logger.info(f"Loaded {self.ons_pd.PUBLICATION_DATE} ONS data!")

        # Filterable columns are the ID and name columns of the dataset
        self.filterable_columns: set[str] = {*column_labels.id.__dict__.values(), *column_labels.name.__dict__.values()}

    def filter_records(self, field: str, value_list: set, mask: bool = False, exclusion_analysis: bool = False) -> None:
        """Filters the Census records by any field in ONS PD.

        Args:
            field: The field on which to filter
            value_list: The values on which to filter
            mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
            exclusion_analysis:

        """
        self.census_data = filter.filter_records(self.census_data, field, value_list, mask, exclusion_analysis)

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
            self.points_data = gpd.GeoDataFrame(idx, geometry=gpd.points_from_xy(self.census_data.long, self.census_data.lat), crs=constants.WGS_84)

        if path is not None:
            all_shapes = gpd.read_file(path)
        elif gdf is not None:
            all_shapes = gdf
        else:
            raise ValueError("A path to a shapefile or a GeoDataFrame must be passed")
        shapes = all_shapes[[shapes_key, "geometry"]].to_crs(epsg=constants.WGS_84)

        spatial_merged = gpd.sjoin(self.points_data, shapes, how="left", op="within").set_index("object_index")
        merged = self.census_data.merge(spatial_merged[[shapes_key]], how="left", left_index=True, right_index=True)
        assert self.census_data.equals(merged[self.census_data.columns])
        self.census_data = merged
        if path is not None and uid is not None:
            merged.reset_index(drop=False).to_feather(uid)

    def close(self) -> None:
        """Outputs the duration of the programme"""
        logger.info(f"Script finished, {time.time() - self.start_time:.2f} seconds elapsed.")
