import pandas as pd

from incognita.data.scout_census import ScoutCensus
from incognita.logger import logger


class ONSPostcodeDirectory:
    """Used for holding and accessing ONS Postcode Directory data

    :param str ons_pd_csv_path: path to the ONS Postcode Directory csv file
    :param bool load_data: whether to load data from the file
    :param str index_column: column to use as the index. Must contain unique values
    :param list fields: columns to read from the csv file
    :param dict data_types: pandas datatypes for the columns to load

    :var ONSPostcodeDirectory.PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
    :var dict ONSPostcodeDirectory.IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
    :var dict ONSPostcodeDirectory.COUNTRY_CODES: ONS Postcode Directory codes for each country
    """

    PUBLICATION_DATE = None
    IMD_MAX = {"England": None, "Wales": None, "Scotland": None, "Northern Ireland": None}
    COUNTRY_CODES = {}
    BOUNDARIES = {}

    def __init__(self, ons_pd_csv_path, load_data=True, index_column=None, fields=None, data_types=None):
        # TODO: Eventually deprecate this, column filtering should happen elsewhere (setup_ons_pd, mainly)
        def cols_lambda(col):
            return col in fields if fields else True

        if load_data:
            logger.debug(f"Loading ONS data from {ons_pd_csv_path} with the following data:\n{fields}")

            # Handle index column possibly not existing (if the full ONS PD is loaded then the index column will exist, if using the reduced ONS PD it won't so use automatic index)
            try:
                self.data = pd.read_csv(ons_pd_csv_path, index_col=index_column, usecols=cols_lambda, dtype=data_types, encoding="utf-8")
            except ValueError:
                logger.debug(f"Loading ONS data with given index colum ({index_column}) failed, trying with pandas-generated index")
                self.data = pd.read_csv(ons_pd_csv_path, index_col=None, usecols=cols_lambda, dtype=data_types, encoding="utf-8")

            for field in data_types:
                if data_types[field] == "category":
                    self.data[field] = self.data[field].cat.add_categories([ScoutCensus.DEFAULT_VALUE])
