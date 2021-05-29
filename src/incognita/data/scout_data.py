from __future__ import annotations

import time

import pandas as pd
from pyarrow import feather

from incognita.logger import logger
from incognita.utility import config


class ScoutData:
    """Provides access to manipulate and process data."""

    def __init__(self, load_census_data: bool = True):
        # Loads Scout Census Data from disk.
        start_time = time.time()
        self.census_data = feather.read_feather(config.SETTINGS.census_extract.merged) if load_census_data else pd.DataFrame()
        logger.info(f"Loaded Scout Census data, {time.time() - start_time:.2f} seconds elapsed.")
