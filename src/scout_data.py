from datetime import datetime
import time
from typing import List
import pandas as pd

from src.base import Base
from src.scout_census import ScoutCensus
from src.census_merge_data import CensusMergeData
from src.ons_pd_may_19 import ONSPostcodeDirectoryMay19
import src.utility as utility


class ScoutData(Base):
    """Provides access to manipulate and process data

    """

    def __init__(self, csv_has_ons_pd_data=True, load_ons_pd_data=False):
        super().__init__(settings=True, log_path='logs/geo_mapping.log')
        self.logger.info(f"Starting at {datetime.now().time()}")
        self.logger.finished(f"Logging setup", start_time=self.start_time)

        self.logger.info("Loading Scout Census data")
        # Loads Scout Census Data from a path to a .csv file that contains Scout Census data
        self.scout_census = ScoutCensus(self.settings["Scout Census location"])
        self.logger.finished(f"Loading Scout Census data", start_time=self.start_time)

        self.min_year, self.max_year = utility.years_of_return(self.scout_census.data)

        if csv_has_ons_pd_data:
            self.logger.info("Loading ONS data")
            start_time = time.time()

            if self.has_ons_pd_data():
                self.ons_pd = ONSPostcodeDirectoryMay19(self.settings["ONS PD location"], load_data=load_ons_pd_data)
            else:
                raise Exception(f"The ScoutCensus file has no ONS data, because it doesn't have a {ScoutCensus.column_labels['VALID_POSTCODE']} column")

            self.logger.finished(f"Loading {self.ons_pd.PUBLICATION_DATE} ONS Postcode data ", start_time=start_time)

    def merge_ons_postcode_directory(self, ons_pd):
        """Merges ScoutCensus object with ONSPostcodeDirectory object and outputs to csv

        :param ONSPostcodeDirectoryMay19 ons_pd: Refers to the ONS Postcode Directory
        """
        # Modifies self.census_postcode_data with the ONS fields info, and saves the output
        ons_fields_data_types = {
            'categorical': ['lsoa11', 'msoa11', 'oslaua', 'osward', 'pcon', 'oscty', 'ctry', 'rgn'],
            'int': ['oseast1m', 'osnrth1m', 'lat', 'long', 'imd'],
        }

        self.logger.debug("Initialising merge object")
        merge = CensusMergeData()

        self.logger.info("Cleaning the postcodes")
        merge.clean_and_verify_postcode(self.data, ScoutCensus.column_labels['POSTCODE'])

        self.logger.info("Adding ONS postcode directory data to Census and outputting")

        # initially merge just Country column to test what postcodes can match
        self.data = merge.merge_data(
            self.data,
            ons_pd.data['ctry'],
            "clean_postcode", )

        # attempt to fix invalid postcodes
        self.data = merge.try_fix_invalid_postcodes(
            self.data,
            ons_pd.data['ctry'], )

        # fully merge the data
        self.data = merge.merge_data(
            self.data,
            ons_pd.data,
            "clean_postcode", )

        # fill unmerged rows with default values
        self.logger.info("filling unmerged rows")
        self.data = merge.fill_unmerged_rows(
            self.data,
            ScoutCensus.column_labels['VALID_POSTCODE'],
            ons_fields_data_types, )

        # save the data to CSV and save invalid postcodes to an error file
        merge.output_data(
            self.data,
            self.settings["Scout Census location"][:-4] + f" with {ons_pd.PUBLICATION_DATE} fields.csv",
            "clean_postcode", )

    def has_ons_pd_data(self):
        """Finds whether ONS data has been added

        :returns: Whether the Scout Census data has ONS data added
        :rtype: bool
        """
        return self.scout_census.has_ons_pd_data()

    def filter_records(self, field, value_list, mask=False, exclusion_analysis=False):
        """Filters the Census records by any field in ONS PD.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter
        :param bool mask: If True, keep the values that match the filter. If False, keep the values that don't match the filter.
        :param bool exclusion_analysis:

        :returns None: Nothing
        """
        data = self.scout_census.data
        self.scout_census.data = utility.filter_records(data, field, value_list, self.logger, mask, exclusion_analysis)
        self.min_year, self.max_year = utility.years_of_return(self.scout_census.data)

    def add_imd_decile(self):
        self.logger.info("Adding Index of Multiple Deprivation Decile")
        self.scout_census.data["imd_decile"] = utility.calc_imd_decile(self.scout_census.data["imd"], self.scout_census.data["ctry"], self.ons_pd)
        return self.scout_census.data
