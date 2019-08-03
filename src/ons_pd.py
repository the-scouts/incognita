import pandas as pd

from src.base import Base
from src.census_data import CensusData


class ONSPostcodeDirectory(Base):
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

    def __init__(self, ons_pd_csv_path, load_data=True, index_column=None, fields=None, data_types=None):
        super().__init__(settings=True)

        self.fields = fields

        if load_data:
            self.logger.debug(f"Loading ONS data from {ons_pd_csv_path} with the following data:\n{self.fields}")
            self.data = pd.read_csv(ons_pd_csv_path, index_col=index_column, usecols=self.fields, dtype=data_types, encoding='utf-8')

            for field in data_types:
                if data_types[field] == 'category':
                    self.data[field] = self.data[field].cat.add_categories([CensusData.DEFAULT_VALUE])

    def ons_field_mapping(self, start_geography, start_values, target_geography):
        """Used to convert between ONS geographies.

        E.g. can find all Lower Super Output Areas within a local authority

        :param str start_geography: must be a field in the ONS PD
        :param list start_values: list of values in the ONS PD
        :param str target_geography: must be a field in the ONS PD

        :return: DataSeries of codes in the target_geography
        """
        # Maps the start geography to target geography
        areas_mapped = self.data.loc[self.data[start_geography].isin(start_values), target_geography].drop_duplicates()
        return areas_mapped
