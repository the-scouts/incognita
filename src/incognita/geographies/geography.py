from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pandas as pd
import pyarrow

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import root

if TYPE_CHECKING:
    from incognita.data.scout_data import ScoutData
    from incognita.utility.config import Boundary

# Combine the ONS and Scout boundaries directories
BOUNDARIES_DICT: dict[str, Boundary] = config.SETTINGS.ons2020 | config.SETTINGS.custom_boundaries


class Geography:
    """Stores information about the (administrative) geography type currently
    used and methods for selecting and excluding regions.

    Attributes:
        metadata: incognita.data.ons_pd.Boundary object with geography metadata
        boundary_codes: Table mapping region codes to human-readable names
        geog_key: Human readable ('nice') name for the geography
    """

    def __init__(self, geography_name: str):
        """Instantiates Geography, loads metadata for a given geography type.

        Args:
            geography_name:
                The type of boundary, e.g. "LSOA", "Constituency" etc. Must be
                an ONS or specified custom boundary.

        """
        logger.info(f"Setting the boundary by {geography_name}")
        if geography_name not in BOUNDARIES_DICT:
            raise ValueError(f"{geography_name} is an invalid boundary.\nValid boundaries include: {BOUNDARIES_DICT.keys()}")
        metadata: Boundary = BOUNDARIES_DICT[geography_name]
        codes = metadata.codes

        # Load Names & Codes file
        start_time = time.time()
        codes_map = pd.read_csv(root.DATA_ROOT / codes.path, dtype={codes.key: codes.key_type, codes.name: "string"})
        logger.debug(f"Loaded {geography_name} codes map, {time.time() - start_time:.2f} seconds elapsed")
        # Normalise codes columns
        codes_map.columns = codes_map.columns.map({codes.key: "codes", codes.name: "names"})
        # drop extras e.g. welsh names
        codes_map = codes_map.drop(columns=[col for col in codes_map.columns if col not in {"codes", "names"}])  

        self.boundary_codes: pd.DataFrame = codes_map
        self.geog_key: str = metadata.key  # human readable name
        self.metadata = metadata  # used in Reports, Map

    def filter_ons_boundaries(self, field: str, values: set) -> pd.DataFrame:
        """Filters the boundary_codes table by if the area code is within both value_list and the census_data table.

        Uses ONS Postcode Directory to find which of set boundaries are within
        the area defined by the value_list.

        Args:
            field: The field on which to filter
            values: The values on which to filter

        Returns:
             Filtered self.boundary_codes

        """

        # Transforms codes from values_list in column 'field' to codes for the current geography
        # 'field' is the start geography and 'geog_key' is the target geography
        logger.info(f"Filtering {len(self.boundary_codes)} {self.geog_key} boundaries by {field} being in {values}")
        logger.debug(f"Loading ONS postcode data.")
        try:
            ons_pd_data = pd.read_feather(config.SETTINGS.ons_pd.reduced, columns=[self.geog_key, field])
        except pyarrow.ArrowInvalid:
            # read in the full file to get valid columns
            valid_cols = pd.read_feather(config.SETTINGS.ons_pd.reduced).columns.to_list()
            raise KeyError(f"{self.geog_key} not in ONS PD dataframe. Valid values are: {valid_cols}") from None
        # Finds records in the ONS PD where the given `field` matches with
        # `values`, and constructs a set of the corresponding `geog_key` codes.
        # Then uses those codes to filter the `boundary_codes` table.
        matching_codes = set(ons_pd_data[self.geog_key][ons_pd_data[field].isin(values)].array)
        self.boundary_codes = self.boundary_codes.loc[self.boundary_codes["codes"].isin(matching_codes)]
        logger.info(f"Leaving {len(self.boundary_codes.index)} boundaries after filtering")

        return self.boundary_codes

    def filter_boundaries_by_scout_area(self, census_data: pd.DataFrame, ons_boundary: str, column: str, value_list: set) -> pd.DataFrame:
        """Filters the boundaries, to include only those boundaries which have
        Sections that satisfy the requirement that the column is in the value_list.

        Produces list of ONS Geographical codes that exist within a subset
        of the Scout Census data.

        Then filters boundaries to those intersecting within said ONS codes.

        Args:
            census_data: Census data to operate on
            ons_boundary: ONS boundary to filter on
            column: Scout boundary (e.g. C_ID)
            value_list: Values in the Scout boundary

        """
        logger.info(f"Finding the ons areas that exist with {column} in {value_list}")

        # Filters scout data to values passed through (values in column `column' in `values_list')
        # Gets associated ons code column from filtered records
        # Removes original ons-census merge errors
        ons_boundary_records = census_data[ons_boundary].dropna()
        ons_codes = set(ons_boundary_records[census_data[column].isin(value_list)].array)
        ons_codes.discard(scout_census.DEFAULT_VALUE)
        logger.debug(f"Found {len(ons_codes)} clean {ons_boundary}s that match {column} in {value_list}")

        return self.filter_ons_boundaries(ons_boundary, ons_codes)
