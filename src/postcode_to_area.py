# ------------------------------------------------------------------------------
# Class PostcodeToArea
#
# The purpose of this class is to allow easy scripting of generating the
# corresponding administrative areas from a postcode using the ONS postcode
# directory. It outputs a file which is contains the original data, with the
# administrative regions appended.
# ------------------------------------------------------------------------------

# This class has been tested in in Python 3.7.0 and using pandas 0.23.3
# csv and re are distributed with standard Python
import pandas as pd
import re
import logging
from src.census_data import CensusData


class PostcodeToArea:
    def __init__(self, ons_data, section_data, output_csv_path, fields):
        # ons_data      - an ONSData object
        # input_csv     - a CensusData object
        # output_csv    - path to a csv where the output is stored. The output is the original csv with the additional columns 'clean_postcode' and those specified in fields
        # fields        - a list of strings, which are the headings for the relevant columns of the ONS Postcode Directory
        self.ons_data = ons_data
        self.input = section_data
        self.output_file_path = output_csv_path
        self.fields = fields

        self.ERROR_FILE = "error_file.txt"

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(fmt="%(name)s - %(levelname)s - %(message)s"))
        # add the handler to the root logger
        self.logger.addHandler(console)

    @staticmethod
    def postcode_cleaner(postcode):
        # Cleans the postcode to lookup in the ONS Postcode Directory.
        # Returns a boolean signifying validity and the cleaned postcode

        # Regular expression to determine a valid postcode
        regex_uk_postcode = re.compile(r"[A-Z]{1,2}\d[A-Z\d]? {0,2}\d[A-Z]{2}")
        # RegExp to remove whitespace, non-alphanumeric (keep shifted numbers)
        regex_clean = re.compile(r'[\s+]|[^a-zA-Z\d!"£$%^&*()]')

        # If length of postcode is 6 or 5 then inert 1 or 2 spaces.
        # 6 first as more common to speed up execution
        def pad_to_seven(single_postcode):  # r'(.*?(?=.{3}$))(.{3}$)' (potential regex)
            if single_postcode == single_postcode:  # filters out NaNs
                length = len(single_postcode)
                if length == 6 or length == 5:
                    single_postcode = single_postcode[:-3] + " " * (7 - length) + single_postcode[-3:]
            return single_postcode

        # Remove any whitespace and most non-alphanumeric chars
        # Convert input to uppercase (ONS Postcode Directory uses upper case)
        # Pads length as we use the 7 long version from the Postcode Directory
        postcode = postcode \
            .str.replace(regex_clean, '') \
            .str.upper() \
            .apply(lambda single_postcode: pad_to_seven(single_postcode))

        # Checks validity against regex, returns truthy/falsy as int (0 or 1)
        m = postcode \
            .str.match(regex_uk_postcode, na=False) \
            .astype(int)
        return m, postcode

    def merge_and_output(self):
        self.logger.info("Cleaning postcodes")
        self.input.sections_postcode_data['postcode_is_valid'], self.input.sections_postcode_data[CensusData.constants['CENSUS_POSTCODE_HEADING']] = PostcodeToArea.postcode_cleaner(self.input.sections_postcode_data[CensusData.constants['CENSUS_POSTCODE_HEADING']])
        self.input.sections_postcode_data[CensusData.constants['CLEAN_POSTCODE']] = self.input.sections_postcode_data[CensusData.constants['CENSUS_POSTCODE_HEADING']]
        self.logger.info("Merging")
        self.input.sections_postcode_data = pd.merge(self.input.sections_postcode_data, self.ons_data.data, how='left', left_on=CensusData.constants['CENSUS_POSTCODE_HEADING'], right_index=True, sort=False)

        for field in ['lsoa11', 'msoa11', 'oslaua', 'osward', 'pcon', 'oscty', 'ctry', 'rgn', CensusData.constants['CLEAN_POSTCODE']]:
            self.input.sections_postcode_data.loc[self.input.sections_postcode_data['postcode_is_valid'] == 0, field] = CensusData.constants['DEFAULT_VALUE']
        for field in ['oseast1m', 'osnrth1m', 'lat', 'long', 'imd']:
            self.input.sections_postcode_data.loc[self.input.sections_postcode_data['postcode_is_valid'] == 0, field] = 0

        # # Find records that haven't had postcode data attached
        # invalid_postcodes = self.input.sections_postcode_data.loc[self.input.sections_postcode_data["postcode_is_valid"] == 0]
        # invalid_section_postcodes = invalid_postcodes.loc[invalid_postcodes[CensusData.CENSUS_TYPE_HEADING].isin(self.input.section_types())]
        # self.logger.debug(invalid_section_postcodes)
        # self.logger.info("Updating sections with invalid postcodes, in groups with valid")
        # for (row_index, row) in invalid_section_postcodes.iterrows():
        #     self.logger.debug(row_index)
        #     group_id = row[CensusData.CENSUS_GROUP_ID]
        #     group_records = self.input.sections_postcode_data.loc[self.input.sections_postcode_data[CensusData.CENSUS_GROUP_ID] == group_id]
        #     valid_postcode = group_records.loc[group_records[CensusData.CENSUS_VALID_POSTCODE] == 1]
        #     if not valid_postcode.empty:
        #         self._write_row(row_index, valid_postcode[self.ons_data.fields])

        # The errors file contains all the postcodes that failed to be looked up in the ONS Postcode Directory
        self.input.sections_postcode_data.loc[self.input.sections_postcode_data['postcode_is_valid'] == 0, CensusData.constants['CENSUS_POSTCODE_HEADING']].dropna().to_csv('error_file.txt', index=False, header=False)
        # Write the new data to a csv file (utf-8-sig only to force excel to use UTF-8)
        self.input.sections_postcode_data.to_csv(self.output_file_path, index=False, encoding='utf-8-sig')
