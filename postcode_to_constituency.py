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
        # input_csv - a SectionData object
        # output_csv - path to a csv where the output is stored. The output is
        #              the original csv with the additional columns 'clean_postcode'
        #              and those specified in fields
        # fields - a list of strings, which are the headings for the relevant columns
        #          of the ONS Postcode Directory
        self.ons_data = ons_data
        self.input = section_data
        self.output_csv = output_csv
        self.fields = fields

        self.input.sections_pd[self.input.CLEAN_POSTCODE] = self.input.DEFAULT_VALUE
        for field in self.fields:
            self.input.sections_pd[field] = self.input.DEFAULT_VALUE
        self.input.sections_pd["postcode_is_valid"] = 0

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
            self.input.sections_pd.at[row_index, field] = sub_data[field].iloc[0]
        self.input.sections_pd.at[row_index, "postcode_is_valid"] = 1

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

    @staticmethod
    def add_cleaned_postcode_column(df, col="Postcode"):
        df['clean_Postcode'] = df.apply(lambda row: PostcodeToArea.postcode_cleaner(str(row[col]))[1], axis=1)

    def create_output(self):
        # Will contain list of invalid postcodes
        postcode_errors = ""
        # Attempts to calculate a measure of progress
        increment = len(self.input.sections_pd.index) / 100
        old_percent = 0
        self.logger.info("The following numbers represent % completion of Sections:")
        # Iterate through each Section (ignoring entities like Groups/Districts)
        for (row_index, row) in self.input.sections_pd.iterrows():
            # Prints every one percent of sections complete
            new_percent = row_index // increment
            if new_percent > old_percent:
                self.logger.info(new_percent)
                old_percent = new_percent

            # Clean the postcode into a format the ONS Postcode Directory
            # recognises
            valid, postcode = self.postcode_cleaner(str(row[self.input.CENSUS_POSTCODE_HEADING]))
            self.input.sections_pd.at[row_index, self.input.CLEAN_POSTCODE] = postcode
            old_postcode = ""

            if valid:
                # Saves looking the postcode up if we've just looked it up for
                # the last Section
                if postcode == old_postcode:
                    self._write_row(row_index, sub_data)
                else:
                    self.logger.debug(postcode)
                    # Finds the row in the ONS PD the postcode relates to
                    sub_data = self._row_from_field(self.input.ONSPD_POSTCODE_FIELD, postcode)

                    if not sub_data.empty:
                        self._write_row(row_index,sub_data)
                        old_data = sub_data
                        old_postcode = postcode
            else:
                if postcode != "NAN":
                    postcode_errors += postcode + "\n"

        # Find records that haven't had postcode data attached
        invalid_postcodes = self.input.sections_pd.loc[self.input.sections_pd["postcode_is_valid"] == 0]
        invalid_section_postcodes = invalid_postcodes.loc[invalid_postcodes[self.input.CENSUS_TYPE_HEADING].isin(self.input.section_types())]
        self.logger.info("Updating sections with invalid postcodes, in groups with valid")
        for (row_index, row) in invalid_section_postcodes.iterrows():
            self.logger.debug(row_index)
            group_id = row[self.input.CENSUS_GROUP_ID]
            group_records = self.input.sections_pd.loc[self.input.sections_pd[self.input.CENSUS_GROUP_ID] == group_id]
            valid_postcode = group_records.loc[group_records[self.input.CENSUS_VALID_POSTCODE] == 1]
            if not valid_postcode.empty:
                self._write_row(row_index, valid_postcode[self.ons_data.fields])

        # Write the new data to a csv file
        self.input.sections_pd.to_csv(self.output_csv)

        # The errors file contains all the postcodes that failed to be looked up
        # in the ONS Postcode Directory
        with open(self.ERROR_FILE,"w",encoding='latin-1') as error_file:
            error_file.write(postcode_errors)
