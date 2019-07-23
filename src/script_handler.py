from src.scout_map import ScoutMap
from src.census_data import CensusData
from src.ONS_data_May_19 import ONSDataMay19
import time
import json
import src.log_util as log_util


class ScriptHandler:
    def __init__(self, csv_has_ons_data=True, load_ons_data=False):
        """Acts to manage all functions, providing setup, logging and timing.

        :param bool csv_has_ons_data: Whether ONS Postcode Directory has data been added to the census csv
        """
        self.logging = log_util.LogUtil(__name__, 'logs/geo_mapping.log')
        self.logger = self.logging.get_logger()

        self.logging.finished_message("Logging setup", __name__)

        with open("settings.json", "r") as read_file:
            self.settings = json.load(read_file)["settings"]

        self.logger.info("Loading Scout Census data")
        self.map = ScoutMap(self.settings["Scout Census location"])
        self.logging.finished_message("Loading Scout Census data", __name__)

        if csv_has_ons_data:
            self.logger.info("Loading ONS data")
            start_time = time.time()

            if self.map.has_ons_data():
                self.map.ons_data = ONSDataMay19(self.settings["ONS PD location"], load_data=load_ons_data)
            else:
                raise Exception(f"The ScoutMap file has no ONS data, because it doesn't have a {CensusData.column_labels['VALID_POSTCODE']} column")

            self.logging.finished_message(f"Loading {self.map.ons_data.PUBLICATION_DATE} ONS data", start_time=start_time)

    def close(self):
        """Outputs the duration of the programme """
        self.logger.info(f"Script took {self.logging.duration():.2f} seconds")

    def run(self, function, args=[], file_name=None, **kwargs):
        """Runs function with self as the ScoutMap object, outputs to file

        :param function: function to run
        :param list args: arguments to pass to the function
        :param file_name: filename to output the result to
        :return: None
        """
        start_time = time.time()

        self.logger.info(f"Calling function {function.__name__}")
        output = function(self.map, *args, **kwargs)

        if file_name:
            self.logger.info(f"Writing to {file_name}")
            output.to_csv(self.settings["Output folder"] + file_name + ".csv")

        self.logging.finished_message(f"{function.__name__}", start_time=start_time)
        return output
