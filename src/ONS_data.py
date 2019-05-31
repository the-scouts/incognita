import pandas as pd
import json

class ONSData:
    def __init__(self, csv_data):
        self.PUBLICATION_DATE = None

        self.IMD_MAX = {}
        self.IMD_MAX["England"] = None
        self.IMD_MAX["Wales"] = None
        self.IMD_MAX["Scotland"] = None
        self.IMD_MAX["Northern Ireland"] = None

        self.COUNTRY_CODES = {}
        self.COUNTRY_CODES["E92000001"] = "England"
        self.COUNTRY_CODES["W92000004"] = "Wales"
        self.COUNTRY_CODES["S92000005"] = "Scotland"
        self.COUNTRY_CODES["N92000002"] = "Northern Ireland"
        self.fields = None

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        self.data = pd.read_csv(csv_data, encoding='latin-1',dtype='str')
        self.data["imd"] = pd.to_numeric(self.data["imd"])
        self.data["lat"] = pd.to_numeric(self.data["lat"])
        self.data["long"] = pd.to_numeric(self.data["long"])
