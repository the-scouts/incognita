import pandas as pd
import json
from src.census_data import CensusData


class ONSData:
    def __init__(self, csv_data, index_column=None, fields=None, data_types=None):
        self.fields = fields
        self.PUBLICATION_DATE = None

        self.IMD_MAX = {"England": None, "Wales": None, "Scotland": None, "Northern Ireland": None}

        self.COUNTRY_CODES = {}

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        self.data = pd.read_csv(csv_data, index_col=index_column, usecols=self.fields, dtype=data_types,  encoding='utf-8')

        for field in data_types:
            if data_types[field] == 'category':
                self.data[field] = self.data[field].cat.add_categories([CensusData.constants['DEFAULT_VALUE']])
