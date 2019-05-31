import pandas as pd
from geo_scout.ONS_data import ONSData

class ONSDataMay18(ONSData):
    def __init__(self, csv_data):
        ONSData.__init__(self, csv_data)

        self.PUBLICATION_DATE = "May 2016"

        self.IMD_MAX = {}
        self.IMD_MAX["England"] = 32844
        self.IMD_MAX["Wales"] = 1909
        self.IMD_MAX["Scotland"] = 6505
        self.IMD_MAX["Northern Ireland"] = 5022

        self.fields = ['lsoa11','msoa11','oslaua','osward','pcon','oscty','oseast1m','osnrth1m','lat','long','imd','ctry','gor']
