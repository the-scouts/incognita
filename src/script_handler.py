from src.scout_map import ScoutMap
from src.census_data import CensusData
from src.ons_pd_may_19 import ONSPostcodeDirectoryMay19
import time
import json
import src.log_util as log_util


class ScriptHandler:
    def __init__(self, csv_has_ons_data=True, load_ons_data=False):
        """Acts to manage all functions, providing setup, logging and timing.

        :param bool csv_has_ons_data: Whether ONS Postcode Directory has data been added to the census csv
        """
        self.start_time = time.time()
        self.logger = log_util.create_logger(__name__, 'logs/geo_mapping.log')

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        self.logger.info(f"Finished logging setup, {log_util.duration(self.start_time)} seconds elapsed")

        self.logger.info("Loading Scout Census data")
        self.map = ScoutMap(self.settings["Scout Census location"])
        self.logger.info(f"Finished loading Scout Census data, {log_util.duration(self.start_time)} seconds elapsed")

        if csv_has_ons_data:
            self.logger.info("Loading ONS data")
            start_time = time.time()

            if self.map.has_ons_data():
                self.map.ons_data = ONSPostcodeDirectoryMay19(self.settings["ONS PD location"], load_data=load_ons_data)
            else:
                raise Exception(f"The ScoutMap file has no ONS data, because it doesn't have a {CensusData.column_labels['VALID_POSTCODE']} column")

            self.logger.info(f"Finished loading ONS data from {self.map.ons_data.PUBLICATION_DATE}, {log_util.duration(start_time)} seconds elapsed")

    def close(self):
        """Outputs the duration of the programme """
        self.logger.info(f"Script took {log_util.duration(self.start_time)} seconds")

    def run(self, function, args=[], file_name=None):
        """Runs function with self as the ScoutMap object, outputs to file

        :param function: function to run
        :param list args: arguments to pass to the function
        :param file_name: filename to output the result to
        :return: None
        """
        start_time = time.time()

        self.logger.info(f"Calling function {function.__name__}")
        output = function(self.map, *args)

        if file_name:
            self.logger.info(f"Writing to {file_name}")
            output.to_csv(self.settings["Output folder"] + file_name + ".csv")

        self.logger.info(f"{function.__name__} took {log_util.duration(start_time)} seconds")
        return output
