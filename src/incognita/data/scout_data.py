from __future__ import annotations

import time

import pandas as pd
from pyarrow import feather

from incognita.logger import logger
from incognita.utility import config
from incognita.utility import filter


class ScoutData:
    """Provides access to manipulate and process data."""

    def __init__(self, load_census_data: bool = True):
        # Loads Scout Census Data from disk.
        start_time = time.time()
        self.census_data = feather.read_feather(config.SETTINGS.census_extract.merged) if load_census_data else pd.DataFrame()
        logger.info(f"Loaded Scout Census data, {time.time() - start_time:.2f} seconds elapsed.")

    def filter_records(self, field: str, value_list: set, exclude_matching: bool = False, exclusion_analysis: bool = False) -> None:
        """Filters the Census records by any field in ONS PD.

        Args:
            field: The field on which to filter
            value_list: The values on which to filter
            exclude_matching: If True, exclude the values that match the filter. If False, keep the values that match the filter.
            exclusion_analysis:

        """
        self.census_data = filter.filter_records(self.census_data, field, value_list, exclude_matching, exclusion_analysis)
