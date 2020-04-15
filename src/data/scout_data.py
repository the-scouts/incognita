from datetime import datetime
import time

from src.base import Base
from src.data.scout_census import ScoutCensus
from src.data.census_merge_data import CensusMergeData
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19
import src.utility as utility


class ScoutData(Base):
    """Provides access to manipulate and process data

    """

    @property
    def columns(self):
        id_cols = self.scout_census.column_labels["id"].values()
        name_cols = self.scout_census.column_labels["name"].values()
        return [*id_cols, *name_cols]

    # TODO: Add column name properties (e.g. ScoutCensus.column_labels["valid_postcode"]

    DEFAULT_VALUE = ScoutCensus.DEFAULT_VALUE

    def __init__(self, merged_csv=True, load_ons_pd_data=False, census_path=None):
        super().__init__(settings=True, log_path=str(utility.LOGS_ROOT.joinpath("geo_mapping.log")))
        self.logger.info(f"Starting at {datetime.now().time()}")
        self.logger.finished(f"Logging setup", start_time=self.start_time)

        self.logger.info("Loading Scout Census data")
        # Loads Scout Census Data from a path to a .csv file that contains Scout Census data
        # We assume no custom path has been passed, but allow for one to be used
        census_path = self.settings["Scout Census location"] if not census_path else census_path
        self.scout_census = ScoutCensus(census_path)
        self.data = self.scout_census.data
        self.logger.finished(f"Loading Scout Census data", start_time=self.start_time)

        if merged_csv:
            self.logger.info("Loading ONS data")
            start_time = time.time()

            if self._has_ons_pd_data():
                self.ons_pd = ONSPostcodeDirectoryMay19(self.settings["Reduced ONS PD location"], load_data=load_ons_pd_data)
            else:
                raise Exception(f"The ScoutCensus file has no ONS data, because it doesn't have a {ScoutCensus.column_labels['VALID_POSTCODE']} column")

            self.logger.finished(f"Loading {self.ons_pd.PUBLICATION_DATE} ONS Postcode data ", start_time=start_time)

    def merge_ons_postcode_directory(self, ons_pd):
        """Merges ScoutCensus object with ONSPostcodeDirectory object and outputs to csv

        :param ONSPostcodeDirectoryMay19 ons_pd: Refers to the ONS Postcode Directory
        """
        # Modifies self.census_postcode_data with the ONS fields info, and saves the output
        ons_fields_data_types = {
            "categorical": ["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "ctry", "rgn"],
            "int": ["oseast1m", "osnrth1m", "lat", "long", "imd"],
        }

        self.logger.debug("Initialising merge object")
        merge = CensusMergeData()

        self.logger.info("Cleaning the postcodes")
        merge.clean_and_verify_postcode(self.data, ScoutCensus.column_labels["POSTCODE"])

        self.logger.info("Adding ONS postcode directory data to Census and outputting")

        # initially merge just Country column to test what postcodes can match
        self.data = merge.merge_data(self.data, ons_pd.data["ctry"], "clean_postcode",)

        # attempt to fix invalid postcodes
        self.data = merge.try_fix_invalid_postcodes(self.data, ons_pd.data["ctry"],)

        # fully merge the data
        self.data = merge.merge_data(self.data, ons_pd.data, "clean_postcode",)

        # fill unmerged rows with default values
        self.logger.info("filling unmerged rows")
        self.data = merge.fill_unmerged_rows(self.data, ScoutCensus.column_labels["VALID_POSTCODE"], ons_fields_data_types,)

        # Filter to useful columns
        # fmt: off
        self.data = self.data[[
            "Object_ID", "compass", "type", "name", "G_ID", "G_name", "D_ID", "D_name", "C_ID", "C_name", "R_ID", "R_name", "X_ID", "X_name",
            "postcode", "clean_postcode", "postcode_is_valid", "Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Young_Leader_Unit",
            "Beavers_f", "Beavers_m", "Beavers_total", "Cubs_f", "Cubs_m", "Cubs_total", "Scouts_f", "Scouts_m", "Scouts_total", "Explorers_f", "Explorers_m", "Explorers_total",
            "Network_f", "Network_m", "Network_total", "Yls", "WaitList_b", "WaitList_c", "WaitList_s", "WaitList_e", "Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults",
            "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards", "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards",
            "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "ScoutsOfTheWorldAward", "Queens_Scout_Awards",
            "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond", "Eligible4QSA", "Eligible4SOWA",
            "oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "lat", "long", "imd"
        ]]
        # fmt: on

        # Add IMD decile column
        self.data["imd_decile"] = utility.calc_imd_decile(self.data["imd"], self.data["ctry"], ons_pd).astype("UInt8")

        # save the data to CSV and save invalid postcodes to an error file
        merge.output_data(self.data, self.settings["Scout Census location"][:-4] + f" with {ons_pd.PUBLICATION_DATE} fields.csv", "clean_postcode")

    def _has_ons_pd_data(self):
        """Finds whether ONS data has been added

        :return bool: Whether the Scout Census data has ONS data added
        """
        return ScoutCensus.column_labels["VALID_POSTCODE"] in list(self.data.columns.values)

    def filter_records(self, field, value_list, mask=False, exclusion_analysis=False):
        """Filters the Census records by any field in ONS PD.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter
        :param bool mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
        :param bool exclusion_analysis:

        :returns None: Nothing
        """
        data = self.data
        self.data = utility.filter_records(data, field, value_list, self.logger, mask, exclusion_analysis)
