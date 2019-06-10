from src.scout_map import ScoutMap
from src.census_data import CensusData
from src.ONS_data_May_18 import ONSDataMay18
import time
import logging
import json


class ScriptHandler:
    def __init__(self, ons=True):
        logging.basicConfig(filename='logs/geo_scout.log', level=logging.DEBUG, filemode="w")
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(fmt="%(name)s - %(levelname)s - %(message)s"))
        # add the handler to the root logger
        self.logger.addHandler(console)
        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]
        self.logger.info("Loading Scout Census data")
        self.map = ScoutMap(self.settings["Scout Census location"])
        if ons:
            self.logger.info("Loading ONS data")
            ons_data = ONSDataMay18(self.settings["ONS PD location"])
            if not self.map.has_ons_data():
                raise Exception(f"The ScoutMap file has no ONS data, because it doesn't have a {CensusData.constants['CLEAN_POSTCODE']} column")
            else:
                self.map.ons_data = ons_data
            self.logger.info(f"Finished loading ONS data from {ons_data.PUBLICATION_DATE} in {time.time() - self.start_time}")

    def close(self):
        self.logger.info(f"Script took {time.time() - self.start_time} seconds")

    def run(self, function, args=[], file_name=None):
        start_time = time.time()
        self.logger.info(f"Calling function {function.__name__}")
        output_pd = function(self.map, *args)
        if file_name:
            self.logger.info(f"Writing to {file_name}")
            output_pd.to_csv(self.settings["Output folder"] + file_name + ".csv")
        self.logger.info(f"{function.__name__} took {time.time() - start_time} seconds")
        return output_pd
