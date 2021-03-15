import os
from typing import Optional

import pandas as pd

from incognita.data.scout_census import ScoutCensus
from incognita.logger import logger


class ONSPostcodeDirectory:
    """Used for holding and accessing ONS Postcode Directory data

    Args:
        load_data: path to the reduced ONS Postcode Directory file

    Attributes:
        PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
        IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
        COUNTRY_CODES: ONS Postcode Directory codes for each country

    """

    PUBLICATION_DATE = None
    IMD_MAX = {"England": None, "Wales": None, "Scotland": None, "Northern Ireland": None}
    COUNTRY_CODES = {}
    BOUNDARIES = {}  # TODO convert to model

    def __init__(self, *, load_data: Optional[os.PathLike] = None):
        # TODO: Eventually deprecate this, column filtering should happen elsewhere (setup_ons_pd, mainly)
        if load_data is not None:
            logger.debug(f"Loading ONS data from {load_data}.")
            self.data = pd.read_feather(load_data)
