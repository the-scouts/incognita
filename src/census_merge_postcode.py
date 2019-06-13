import pandas as pd
import re
from geo_scout.src.census_data import CensusData
import src.log_util as log_util


class CensusMergePostcode:
    def __init__(self, section_data, output_csv_path):
        """Merges input data with a CensusData object on a given field
        Outputs a file which is contains the original data, a postcode validity check, and the merged fields appended.

        :param section_data: a CensusData object
        :param output_csv_path: path to a csv where the output is stored. The output is the original csv with the additional columns 'postcode_is_valid' and those specified in fields
        """
        self.input = section_data
        self.output_file_path = output_csv_path

        self.ERROR_FILE = "error_file.txt"

        # Facilitates logging
        self.logger = log_util.create_logger(__name__, )

    @staticmethod
    def postcode_cleaner(postcode):
        # Cleans the postcode to lookup in the ONS Postcode Directory.
        # Returns a boolean signifying validity and the cleaned postcode

        # Regular expression to determine a valid postcode
        regex_uk_postcode = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]? {0,2}\d[A-Z]{2}$")
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

    def merge_and_output(self, census_data, data_to_merge, census_index_column, fields_data_types):
        """
        :param census_data: pandas DataFrame with census data
        :param data_to_merge: pandas DataFrame with index col as index to merge
        :param census_index_column: column label to merge on in census data
        :param fields_data_types: dict of data types -> lists of fields
        :return: None
        """

        valid_postcode_label = CensusData.column_labels['VALID_POSTCODE']
        
        self.logger.info("Cleaning postcodes")
        census_data[valid_postcode_label], census_data[census_index_column] = CensusMergePostcode.postcode_cleaner(census_data[census_index_column])
        self.logger.info("Merging data")
        census_data = pd.merge(census_data, data_to_merge, how='left', left_on=census_index_column, right_index=True, sort=False)

        for field in fields_data_types['categorical']:
            census_data.loc[census_data[valid_postcode_label] == 0, field] = CensusData.DEFAULT_VALUE
        for field in fields_data_types['int']:
            census_data.loc[census_data[valid_postcode_label] == 0, field] = 0

        # # Find records that haven't had postcode data attached
        # invalid_postcodes = census_data.loc[census_data["postcode_is_valid"] == 0]
        # invalid_section_postcodes = invalid_postcodes.loc[invalid_postcodes[CensusData.column_labels['UNIT_TYPE']].isin(self.input.section_types())]
        # self.logger.debug(invalid_section_postcodes)
        # self.logger.info("Updating sections with invalid postcodes, in groups with valid")
        # for (row_index, row) in invalid_section_postcodes.iterrows():
        #     self.logger.debug(row_index)
        #     group_id = row[CensusData.column_labels['id']["GROUP"]]
        #     group_records = census_data.loc[census_data[CensusData.column_labels['id']["GROUP"]] == group_id]
        #     valid_postcode = group_records.loc[group_records[CensusData.column_labels['VALID_POSTCODE']] == 1]
        #     if not valid_postcode.empty:
        #         self._write_row(row_index, valid_postcode[self.ons_data.fields])

        # The errors file contains all the postcodes that failed to be looked up in the ONS Postcode Directory
        self.logger.info("Writing merged data")
        census_data.loc[census_data[valid_postcode_label] == 0, census_index_column].dropna().to_csv('error_file.txt', index=False, header=False)
        # Write the new data to a csv file (utf-8-sig only to force excel to use UTF-8)
        census_data.to_csv(self.output_file_path, index=False, encoding='utf-8-sig')
