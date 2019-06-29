import pandas as pd
import numpy as np
import re
from src.census_data import CensusData
import src.log_util as log_util


class CensusMergePostcode:
    """Merges input data with CensusData data on a given key

        Outputs a file which is contains the original data, a postcode validity check, and the merged fields appended.
        The output is the original csv with the additional columns 'postcode_is_valid' and those specified in fields

        :param section_data: a CensusData object
        :param output_csv_path: path to a csv where the output is stored.
        """

    def __init__(self, section_data, output_csv_path):
        self.input = section_data
        self.output_file_path = output_csv_path

        self.ERROR_FILE = "error_file.txt"

        # Facilitates logging
        self.logger = log_util.create_logger(__name__, )

    @staticmethod
    def postcode_cleaner(postcode):
        """Cleans postcode to ONS postcode directory format.

        :param postcode: pandas series of postcodes
        :return: cleaned postcode
        """

        # Regular expression to remove whitespace, non-alphanumeric (keep shifted numbers)
        regex_clean = re.compile(r'[\s+]|[^a-zA-Z\d!"£$%^&*()]')

        # If length of postcode is 6 or 5 then insert 1 or 2 spaces.
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

        # Replaces shifted numbers with their number equivalents
        postcode = postcode\
            .str.replace('!', "1", regex=False)\
            .str.replace('"', "2", regex=False)\
            .str.replace('£', "3", regex=False)\
            .str.replace('$', "4", regex=False)\
            .str.replace('%', "5", regex=False)\
            .str.replace('^', "6", regex=False)\
            .str.replace('&', "7", regex=False)\
            .str.replace('*', "8", regex=False)\
            .str.replace('(', "9", regex=False)\
            .str.replace(')', "0", regex=False)
        # TODO: add macOS shift -> numbers conversion

        return postcode

    @staticmethod
    def fill_unmerged_rows(census_data, row_has_merged, fields_data_types):
        """Fills rows that have not merged with default values

        Fills all passed fields in rows where there has been no data merged
        Fills categorical fields with CensusData.DEFAULT_VALUE and numerical fields with 0

        :param census_data: pandas DataFrame with census data
        :param str row_has_merged: column label for column with booleans of if the merge was successful
        :param dict fields_data_types: dict of data types containing lists of fields
        :return: dataframe with filled values
        """
        for field in fields_data_types['categorical']:
            census_data.loc[census_data[row_has_merged] == 0, field] = CensusData.DEFAULT_VALUE
        for field in fields_data_types['int']:
            census_data.loc[census_data[row_has_merged] == 0, field] = 0

        return census_data

    def clean_and_verify_postcode(self, census_data, postcode_column):
        """Cleans postcode data and inserts clean postcodes and validity check

        Cleans postcode data from passed table and index
        Gets index of postcode column, and inserts new columns after postcode column

        :param census_data: table of data with a postcode column
        :param str postcode_column: heading of the postcode column in the table
        :return: None
        """
        # Gets the index of the postcode column, and increments as insertion is from the left.
        # Columns must be inserted in number order otherwise it wont't make sense
        postcode_column_index = census_data.columns.get_loc(postcode_column)  # CensusData.column_labels["POSTCODE"]
        cleaned_postcode_index = postcode_column_index + 1
        valid_postcode_index = postcode_column_index + 2

        # Sets the labels for the columns to be inserted
        cleaned_postcode_label = "clean_postcode"
        valid_postcode_label = CensusData.column_labels['VALID_POSTCODE']

        self.logger.info("Cleaning postcodes")
        cleaned_postcode_column = CensusMergePostcode.postcode_cleaner(census_data[postcode_column])

        self.logger.info("Inserting columns")
        census_data.insert(cleaned_postcode_index, cleaned_postcode_label, cleaned_postcode_column)
        census_data.insert(valid_postcode_index, valid_postcode_label, np.NaN)

    def merge_data(self, census_data, data_to_merge, census_index_column):
        """Merge census data and input data on key and index.

        :param census_data: pandas DataFrame with census data
        :param data_to_merge: pandas DataFrame with index col as index to merge
        :param str census_index_column: column label to merge on in census data

        :return: Dataframe with merged data, and an indicator in each row signifying merge success
        """
        # Column heading denoting a valid postcode in the row
        valid_postcode_label = CensusData.column_labels['VALID_POSTCODE']

        self.logger.info("Merging data")
        census_data = pd.merge(census_data, data_to_merge, how='left', left_on=census_index_column, right_index=True, sort=False)

        # Checks whether ONS data exists for each row and stores in a column
        census_data[valid_postcode_label] = (~census_data['ctry'].isnull()).astype(int)

        return census_data

    def output_data(self, census_data, postcode_merge_column):
        """Save passed dataframe to csv file.

        Also output list of errors in the merge process to a text file

        :param census_data: pandas DataFrame with census data
        :param str postcode_merge_column: column that was used as the merge index, and will have invalid postcodes
        :return:
        """
        # Column heading denoting a valid postcode in the row
        valid_postcode_label = CensusData.column_labels['VALID_POSTCODE']

        # The errors file contains all the postcodes that failed to be looked up in the ONS Postcode Directory
        self.logger.info("Writing merged data")
        census_data.loc[census_data[valid_postcode_label] == 0, postcode_merge_column].dropna().to_csv('error_file.txt', index=False, header=False)
        # Write the new data to a csv file (utf-8-sig only to force excel to use UTF-8)
        census_data.to_csv(self.output_file_path, index=False, encoding='utf-8-sig')
