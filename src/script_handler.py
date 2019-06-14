from geo_scout.src.scout_map import ScoutMap
from geo_scout.src.census_data import CensusData
from geo_scout.src.ONS_data_May_18 import ONSDataMay18
import time
import json
import src.log_util as log_util


class ScriptHandler:
    def __init__(self, csv_has_ons_data=True):
        """Acts to manage all functions, providing setup, logging and timing

        :param csv_has_ons_data: Whether ONS Postcode Directory has data been added to the census csv
        :type csv_has_ons_data: Bool
        """
        self.start_time = time.time()
        self.logger = log_util.create_logger(__name__, 'logs/geo_scout.log')

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        self.logger.info(f"Finished logging setup, {log_util.duration(self.start_time)} seconds elapsed")

        self.logger.info("Loading Scout Census data")
        self.map = ScoutMap(self.settings["Scout Census location"])
        self.logger.info(f"Finished loading Scout Census data, {log_util.duration(self.start_time)} seconds elapsed")

        if csv_has_ons_data:
            self.logger.info("Loading ONS data")

            if self.map.has_ons_data():
                self.map.ons_data = ONSDataMay18(None, load_data=False)
            else:
                raise Exception(f"The ScoutMap file has no ONS data, because it doesn't have a {CensusData.column_labels['VALID_POSTCODE']} column")

            self.logger.info(f"Finished loading ONS data from {self.map.ons_data.PUBLICATION_DATE}, {log_util.duration(self.start_time)} seconds elapsed")

    def close(self):
        self.logger.info(f"Script took {log_util.duration(self.start_time)} seconds")

    def run(self, function, args=[], file_name=None):
        start_time = time.time()

        self.logger.info(f"Calling function {function.__name__}")
        output = function(self.map, *args)

        if file_name:
            self.logger.info(f"Writing to {file_name}")
            output.to_csv(self.settings["Output folder"] + file_name + ".csv")

        self.logger.info(f"{function.__name__} took {log_util.duration(start_time)} seconds")
        return output

