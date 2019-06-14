import pandas as pd
import json
from geo_scout.src.census_data import CensusData


class ONSData:
    PUBLICATION_DATE = None
    IMD_MAX = {"England": None, "Wales": None, "Scotland": None, "Northern Ireland": None}
    COUNTRY_CODES = {}

    def __init__(self, csv_data, load_data=True, index_column=None, fields=None, data_types=None):
        self.fields = fields

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        if load_data:
            self.data = pd.read_csv(csv_data, index_col=index_column, usecols=self.fields, dtype=data_types,  encoding='utf-8')

            for field in data_types:
                if data_types[field] == 'category':
                    self.data[field] = self.data[field].cat.add_categories([CensusData.DEFAULT_VALUE])
