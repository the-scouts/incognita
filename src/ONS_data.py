import pandas as pd
import json
from src.census_data import CensusData


class ONSData:
    """Used for holding and accessing ONS Postcode Directory data

    :param str ons_pd_csv_path: path to the ONS Postcode Directory csv file
    :param bool load_data: whether to load data from the file
    :param str index_column: column to use as the index. Must contain unique values
    :param list fields: columns to read from the csv file
    :param dict data_types: pandas datatypes for the columns to load

    :var ONSData.PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
    :var dict ONSData.IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
    :var dict ONSData.COUNTRY_CODES: ONS Postcode Directory codes for each country
    """
    PUBLICATION_DATE = None
    IMD_MAX = {"England": None, "Wales": None, "Scotland": None, "Northern Ireland": None}
    COUNTRY_CODES = {}

    def __init__(self, ons_pd_csv_path, load_data=True, index_column=None, fields=None, data_types=None):
        self.fields = fields

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        if load_data:
            self.data = pd.read_csv(ons_pd_csv_path, index_col=index_column, usecols=self.fields, dtype=data_types, encoding='utf-8')

            for field in data_types:
                if data_types[field] == 'category':
                    self.data[field] = self.data[field].cat.add_categories([CensusData.DEFAULT_VALUE])
