import os
from typing import Optional

import pandas as pd

from incognita.data.scout_census import ScoutCensus
from incognita.logger import logger


class ONSPostcodeDirectory:
    """Used for holding and accessing ONS Postcode Directory data

    Attributes:
        PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
        IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
        COUNTRY_CODES: ONS Postcode Directory codes for each country

    """

    PUBLICATION_DATE = None
    IMD_MAX = {"England": None, "Wales": None, "Scotland": None, "Northern Ireland": None}
    COUNTRY_CODES = {}
    BOUNDARIES = {}  # TODO convert to model
