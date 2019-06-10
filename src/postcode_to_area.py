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
import csv
import re
import numpy as np
import logging

class PostcodeToArea:

    def __init__(self,ons_data,section_data,output_csv,fields):
        # ons_data - an ONSData object
        # input_csv - a CensusData object
        # output_csv - path to a csv where the output is stored. The output is
        #              the original csv with the additional columns 'clean_postcode'
        #              and those specified in fields
        # fields - a list of strings, which are the headings for the relevant columns
        #          of the ONS Postcode Directory
        self.ons_data = ons_data
        self.input = section_data
        self.output_file_path = output_csv
        self.fields = fields

        self.input.sections_postcode_data[self.input.CLEAN_POSTCODE] = self.input.DEFAULT_VALUE
        for field in self.fields:
            self.input.sections_postcode_data[field] = self.input.DEFAULT_VALUE
        self.input.sections_postcode_data["postcode_is_valid"] = 0

        self.ERROR_FILE = "error_file.txt"

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(fmt="%(name)s - %(levelname)s - %(message)s"))
        # add the handler to the root logger
        self.logger.addHandler(console)


    def _write_row(self, row_index, sub_data):
        # Writes the new values of new fields from the ONS PD into the data
        # row_index - the row of the input csv where the new fields will be added
        # sub_data - a one row pandas dataframe which contains the new data
        #            Typically, the one row of the ONS PD that matches a postcode
        for field in self.fields:
            self.input.sections_postcode_data.at[row_index, field] = sub_data[field].iloc[0]
        self.input.sections_postcode_data.at[row_index, "postcode_is_valid"] = 1

    def _row_from_field(self, field, value):
        # Given a field of the ONS PD and a value, returns all rows that match
        # the criteria. Often used where the field in the postcode column, and
        # the value a postcode. As postcode is unique in the ONS PD returns one
        # row.
        return self.ons_data.data.loc[self.ons_data.data[field] == value]

    @staticmethod
    def postcode_cleaner(postcode):
        # Cleans the postcode to lookup in the ONS PD. Returns two values, the
        # first determines if postcode is valid or not, the second the cleaned
        # postcode

        # As the ONS PD stores postcodes in upper case, convert input to uppercase
        postcode = postcode.upper()
        # Remove any whitespace
        postcode = re.sub(r'[\s+]', '', postcode)

        # If the length of the trimmed postcode is 5, then insert two spaces to
        # fit the standard 7 length postcode field in the ONS PD.
        # If the length of the trimmed postcode is 6, then insert one space to
        # fit the standard 7 length postcode field in the ONS PD.
        length = len(postcode)
        if length == 5:
            # e.g. S11AA
            postcode = postcode[:2] + "  " + postcode[2:]
        elif length == 6:
            # e.g. S111AA
            postcode = postcode[:3] + " " + postcode[3:]

        # See if the postcode matches the correct format. If it doesn't make
        # potential improvements.

        # Regular expression for determining a valid postcode
        postcode_re = re.compile(r"[A-Z]{1,2}[0-9][0-9,A-Z]??[ ]{0,2}[0-9][A-Z]{2}")
        m = postcode_re.match(postcode)
        if m:
            valid = True
        else:
            valid = False
            if (length <= 7) and (length >= 5):
                # A small correction for an 'O' instead of a 0 at the beginning
                # of the trailing three characters.
                if postcode[-3] == "O":
                    postcode = postcode[:-3] + "0" + postcode[-2:]

        return valid, postcode

    def merge_and_output(self):
        self.logger.info("Cleaning postcodes")
        self.input.sections_postcode_data['postcode_is_valid'], self.input.sections_postcode_data[self.constants['CENSUS_POSTCODE_HEADING']] = PostcodeToArea.postcode_cleaner(self.input.sections_postcode_data[self.constants['CENSUS_POSTCODE_HEADING']])
        self.input.sections_postcode_data[self.input.CLEAN_POSTCODE] = self.input.sections_postcode_data[self.constants['CENSUS_POSTCODE_HEADING']]
        self.logger.info("Merging")
        self.input.sections_postcode_data = pd.merge(self.input.sections_postcode_data, self.ons_data.data, how='left', left_on=self.constants['CENSUS_POSTCODE_HEADING'], right_index=True, sort=False)

        for field in ['lsoa11', 'msoa11', 'oslaua', 'osward', 'pcon', 'oscty', 'ctry', 'rgn']:
            self.input.sections_postcode_data.loc[self.input.sections_postcode_data['postcode_is_valid'] == 0, field] = self.constants['DEFAULT_VALUE']
        for field in ['oseast1m', 'osnrth1m', 'lat', 'long', 'imd', "postcode_is_valid"]:
            self.input.sections_postcode_data.loc[self.input.sections_postcode_data['postcode_is_valid'] == 0, field] = 0

        # Find records that haven't had postcode data attached
        invalid_postcodes = self.input.sections_postcode_data.loc[self.input.sections_postcode_data["postcode_is_valid"] == 0]
        invalid_section_postcodes = invalid_postcodes.loc[invalid_postcodes[self.input.CENSUS_TYPE_HEADING].isin(self.input.section_types())]
        self.logger.debug(invalid_section_postcodes)
        self.logger.info("Updating sections with invalid postcodes, in groups with valid")
        for (row_index, row) in invalid_section_postcodes.iterrows():
            self.logger.debug(row_index)
            group_id = row[self.input.CENSUS_GROUP_ID]
            group_records = self.input.sections_postcode_data.loc[self.input.sections_postcode_data[self.input.CENSUS_GROUP_ID] == group_id]
            valid_postcode = group_records.loc[group_records[self.input.CENSUS_VALID_POSTCODE] == 1]
            if not valid_postcode.empty:
                self._write_row(row_index, valid_postcode[self.ons_data.fields])

        # The errors file contains all the postcodes that failed to be looked up in the ONS Postcode Directory
        self.input.sections_postcode_data.loc[self.input.sections_postcode_data['postcode_is_valid'] == 0, self.constants['CENSUS_POSTCODE_HEADING']].dropna().to_csv('error_file.txt', index=False, header=False)
        # Write the new data to a csv file
        self.input.sections_postcode_data.to_csv(self.output_file_path, index=False, encoding='utf-8-sig') #utf-8-sig inserts a bom (literally only to force excel to use UTF-8)
