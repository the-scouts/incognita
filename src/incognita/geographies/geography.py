from __future__ import annotations

import time
from typing import TYPE_CHECKING

import geopandas as gpd
import pandas as pd
import shapely.geometry

from incognita.data import scout_census
from incognita.data.ons_pd import Boundary
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import root
from incognita.utility import utility

if TYPE_CHECKING:
    from incognita.data.ons_pd import ONSPostcodeDirectory
    from incognita.data.scout_data import ScoutData


class Geography:
    """Stores information about the (administrative) geography type currently
    used and methods for selecting and excluding regions.

    Attributes:
        metadata: incognita.data.ons_pd.Boundary object with geography metadata
        boundary_codes: Table mapping region codes to human-readable names
        name: Human readable ('nice') name for the geography
    """

    def __init__(self, geography_name: str, ons_pd: ONSPostcodeDirectory):
        """Instantiates Geography, loads metadata for a given geography type.

        Args:
            geography_name:
                The type of boundary, e.g. "LSOA", "Constituency" etc. Must be
                an ONS or specified custom boundary.
            ons_pd:
                An ONSPostcodeDirectory model with boundaries for a given release

        """
        logger.info(f"Setting the boundary by {geography_name}")

        # Combine the ONS and Scout boundaries directories
        boundaries_dict = ons_pd.BOUNDARIES | config.SETTINGS.custom_boundaries
        if geography_name not in boundaries_dict:
            raise ValueError(f"{geography_name} is an invalid boundary.\nValid boundaries include: {boundaries_dict.keys()}")
        self.metadata: Boundary = boundaries_dict[geography_name]
        self.name: str = self.metadata.key  # human readable name

        # Names & Codes file path
        logger.debug(f"Loading {geography_name} codes map")
        boundary_codes_dtypes = {self.metadata.codes.key: self.metadata.codes.key_type, self.metadata.codes.name: "string"}
        start_time = time.time()
        codes_map = pd.read_csv(root.DATA_ROOT / self.metadata.codes.path, dtype=boundary_codes_dtypes)
        logger.debug(f"Loading {geography_name} codes map finished, {time.time() - start_time:.2f} seconds elapsed")
        logger.debug(f"Normalising {geography_name} codes columns")
        codes_map.columns = codes_map.columns.map({self.metadata.codes.key: "codes", self.metadata.codes.name: "names"})
        self.boundary_codes: pd.DataFrame = codes_map

    def filter_ons_boundaries(self, field: str, value_list: set) -> pd.DataFrame:
        """Filters the boundary_codes table by if the area code is within both value_list and the census_data table.

        Uses ONS Postcode Directory to find which of set boundaries are within
        the area defined by the value_list.

        Args:
            field: The field on which to filter
            value_list: The values on which to filter

        Returns:
             Filtered self.boundary_codes

        """

        # Transforms codes from values_list in column 'field' to codes for the current geography
        # 'field' is the start geography and 'metadata.key' is the target geography
        # Returns a list
        logger.info(f"Filtering {len(self.boundary_codes)} {self.name} boundaries by {field} being in {value_list}")
        logger.debug(f"Loading ONS postcode data.")
        ons_pd_data = pd.read_feather(config.SETTINGS.ons_pd.reduced)
        try:
            boundary_subset = ons_pd_data.loc[ons_pd_data[field].isin(value_list), self.metadata.key].drop_duplicates().to_list()
        except KeyError:
            msg = f"{self.metadata.key} not in ONS PD dataframe. \nValid values are: {ons_pd_data.columns.to_list()}"
            logger.error(msg)
            raise KeyError(msg) from None
        logger.debug(f"This corresponds to {len(boundary_subset)} {self.name} boundaries")

        # Filters the boundary names and codes table to only areas within the boundary_subset list
        self.boundary_codes = self.boundary_codes.loc[self.boundary_codes["codes"].isin(set(boundary_subset))]
        logger.info(f"Resulting in {len(self.boundary_codes)} {self.name} boundaries")

        return self.boundary_codes

    def filter_boundaries_by_scout_area(self, scout_data: ScoutData, ons_boundary: str, column: str, value_list: set) -> pd.DataFrame:
        """Filters the boundaries, to include only those boundaries which have
        Sections that satisfy the requirement that the column is in the value_list.

        Produces list of ONS Geographical codes that exist within a subset
        of the Scout Census data.

        Then filters boundaries to those intersecting within said ONS codes.

        Args:
            scout_data: ScoutData object with data to operate on
            ons_boundary: ONS boundary to filter on
            column: Scout boundary (e.g. C_ID)
            value_list: Values in the Scout boundary

        """
        logger.info(f"Finding the ons areas that exist with {column} in {value_list}")

        # Filters scout data to values passed through (values in column `column' in `values_list')
        # Gets associated ons code column from filtered records
        records = scout_data.census_data.loc[scout_data.census_data[column].isin(value_list), ons_boundary].drop_duplicates().dropna()
        logger.debug(f"Found {len(records)} records that match {column} in {value_list}")

        # Removes original ons-census merge errors
        ons_codes = records[records != scout_census.DEFAULT_VALUE].to_list()
        logger.debug(f"Found {len(ons_codes)} clean {ons_boundary}s that match {column} in {value_list}")

        return self.filter_ons_boundaries(ons_boundary, set(ons_codes))

    def filter_boundaries_near_scout_area(self, scout_data: ScoutData, boundary: str, field: str, value_list: set, distance: int = 3_000) -> pd.DataFrame:
        """Filters boundary list to those boundaries containing a scout unit matching requirements, or boundaries
        partially or fully within three kilometres of the external border (convex hull)

        TODO investigate some method of actually finding a boundary's neighbours.

        Args:
            scout_data: ScoutData object with data to operate on
            boundary: ONS boundary to filter on
            field: Scout boundary (e.g. C_ID)
            value_list: Values in the Scout boundary
            distance: How far to extend the buffer by (meters)

        """

        logger.info("Creates geometry")
        # Reduce columns in dataset to minimum requirements
        data_with_points = gpd.GeoDataFrame(
            scout_data.census_data[[field, boundary]],
            geometry=gpd.points_from_xy(scout_data.census_data.long, scout_data.census_data.lat),
            crs=utility.WGS_84,
        )

        # Pivots the co-ordinate reference system into OS36 which uses
        # (x-y) coordinates in metres, rather than (long, lat) coordinates.
        data_with_points = data_with_points.to_crs(epsg=utility.BNG)
        # TODO work out way to avoid co-ordinate pivot (i.e. convert 3km into GPS co-ordinates)

        logger.info(f"Filters for records that satisfy {field} in {value_list}")
        filtered_points = data_with_points.loc[data_with_points[field].isin(value_list)]
        logger.debug(f"Resulting in {len(filtered_points.index)} number of Sections")

        logger.info(f"Creating area of interest")
        # Finds the outer boundary of all selected scout units and extends by `distance` in all directions to
        # incorporate nearby regions
        in_area = shapely.geometry.MultiPoint(filtered_points["geometry"].to_list()).convex_hull.buffer(distance)
        in_area2 = filtered_points.geometry.convex_hull().buffer(distance)  # TODO timings
        logger.debug(f"Is result valid {in_area.geom_type}? {in_area.is_valid}. Area is {in_area.area}")

        logger.info(f"Finding Sections in buffered area of interest")

        nearby_values = data_with_points.loc[data_with_points.geometry.within(in_area), boundary].drop_duplicates().to_list()
        logger.info(f"Found {len(nearby_values)} Sections nearby")
        logger.debug(f"Found {nearby_values}")

        return self.filter_ons_boundaries(boundary, set(nearby_values))
