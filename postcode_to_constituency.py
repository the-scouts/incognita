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

class PostcodeToArea:

    def __init__(self,data_csv,input_csv,output_csv,fields):
        # data_csv - path to an ONS Postcode directory .csv file
        # input_csv - path to a csv where exactly one column has 'Postcode' as a heading
        #             only supports 'latin-1' character set.
        # output_csv - path to a csv where the output is stored. The output is
        #              the original csv with the additional columns 'clean_postcode'
        #              and those specified in fields
        # fields - a list of strings, which are the headings for the relevant columns
        #          of the ONS Postcode Directory
        self.data = pd.read_csv(data_csv,dtype='str')
        self.input = pd.read_csv(input_csv,encoding='latin1',dtype='str')
        self.output_csv = output_csv
        self.fields = fields

        self.DEFAULT_VALUE = "error"
        self.CLEAN_POSTCODE = "clean_postcode"
        self.input[self.CLEAN_POSTCODE] = self.DEFAULT_VALUE
        for field in self.fields:
            self.input[field] = self.DEFAULT_VALUE

        # Regular expression for determining a valid postcode
        self.postcode_re = re.compile(r"[A-Z]{1,2}[0-9]{1,2}[ ]{0,2}[0-9][A-Z]{2}")

        # The following variables control the details of the class, but are not
        # sufficiently major for the constructor.
        # The new columns are created with a default value, in case of invalid lookup

        self.SECTIONS = ['C','P','T','U','Y']
        self.ONSPD_POSTCODE_FIELD = 'pcd'
        self.CENSUS_GROUP_ID = 'G_ID'
        self.CENSUS_DISTRICT_ID = 'D_ID'
        self.CENSUS_TYPE_GROUP = "G"
        self.CENSUS_TYPE_DISTRICT = "E"
        self.CENSUS_TYPE_ENTITY = [self.CENSUS_TYPE_GROUP, self.CENSUS_TYPE_DISTRICT]
        self.CENSUS_TYPE_HEADING = "Type *"
        self.CENSUS_POSTCODE_HEADING = "Postcode"
        self.ERROR_FILE = "error_file.txt"


    def _write_row(self, row_index, sub_data):
        # Writes the new values of new fields from the ONS PD into the data
        # row_index - the row of the input csv where the new fields will be added
        # sub_data - a one row pandas dataframe which contains the new data
        #            Typically, the one row of the ONS PD that matches a postcode
        for field in self.fields:
            self.input.at[row_index, field] = sub_data[field].iloc[0]

    def _row_from_field(self, field, value):
        # Given a field of the ONS PD and a value, returns all rows that match
        # the criteria. Often used where the field in the postcode column, and
        # the value a postcode. As postcode is unique in the ONS PD returns one
        # row.
        return self.data.loc[self.data[field] == value]

    def postcode_cleaner(self, postcode):
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
        m = self.postcode_re.match(postcode)
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

    def create_output(self):
        # Will contain list of invalid postcodes
        postcode_errors = ""
        # Finds all the sections in the census data
        sections = self.input.loc[self.input[self.CENSUS_TYPE_HEADING].isin(self.SECTIONS)]

        # Attempts to calculate a measure of progress
        number_sections = len(self.input.index)
        increment = number_sections / 100
        old_row_index = 0
        count_percent = 0
        print("The following numbers represent % completion:")
        # Iterate through each Section (ignoring entities like Groups/Districts)
        for (row_index, row) in sections.iterrows():
            # Prints every one percent of sections complete
            if row_index > (old_row_index + increment):
                count_percent += 1
                old_row_index = row_index
                print(count_percent)

            # Clean the postcode into a format the ONS Postcode Directory
            # recognises
            valid, postcode = self.postcode_cleaner(str(row[self.CENSUS_POSTCODE_HEADING]))
            self.input.at[row_index, self.CLEAN_POSTCODE] = postcode
            old_postcode = ""

            if valid and (postcode != "NAN"):
                # Saves looking the postcode up if we've just looked it up for
                # the last Section
                if postcode == old_postcode:
                    self._write_row(row_index, sub_data)
                else:
                    # Finds the row in the ONS PD the postcode relates to
                    sub_data = self._row_from_field(self.ONSPD_POSTCODE_FIELD, postcode)
                    # If the postcode is not recognised, see if any other Groups
                    # have the a postcode and assume that postcode for this Section.
                    # If multiple postcodes are found, just choose the first.
                    if sub_data.empty:
                        group_id = row[self.CENSUS_GROUP_ID]
                        group_sections = self.input.loc[(self.input[self.CENSUS_GROUP_ID] == group_id)]
                        section_postcodes = group_sections[self.CLEAN_POSTCODE].unique().tolist()
                        if self.DEFAULT_VALUE in section_postcodes:
                            section_postcodes.remove(self.DEFAULT_VALUE)
                        if section_postcodes:
                            postcode = section_postcodes[0]
                            sub_data = self._row_from_field(self.ONSPD_POSTCODE_FIELD, postcode)
                        else:
                            # Complete failure, mark as a postcode error
                            postcode_errors += postcode + "\n"

                    # If we have found data then write to output
                    if not sub_data.empty:
                        self._write_row(row_index,sub_data)
                        old_data = sub_data
                        old_postcode = postcode

        # An entity is a organisation item that does not have a point location
        # but is made up from constituent parts which have a point location.
        # These are usually anything that is not a Section.
        entity = self.input.loc[self.input[self.CENSUS_TYPE_HEADING].isin(self.CENSUS_TYPE_ENTITY)]
        for (row_index, row) in entity.iterrows():
            print(row_index)
            # Selects the column that the relevant ID is in
            if row[self.CENSUS_TYPE_HEADING] == self.CENSUS_TYPE_GROUP:
                id_col = self.CENSUS_GROUP_ID
            elif row[self.CENSUS_TYPE_HEADING] == self.CENSUS_TYPE_DISTRICT:
                id_col = self.CENSUS_DISTRICT_ID
            entity_id = row[id_col]
            # Finds all the sections within the Group/District
            entity_sections = self.input.loc[(self.input[id_col] == entity_id)]
            # Finds the postcodes within the Group/District, and produces
            # a unique list of them
            section_postcds = entity_sections[self.CLEAN_POSTCODE].unique().tolist()

            # If the default value exists remove it from the unique list of
            # postcodes, then update the Group/District with all the relevant
            # postcodes of Sections found within it
            if self.DEFAULT_VALUE in section_postcds:
                section_postcds.remove(self.DEFAULT_VALUE)
                if section_postcds:
                    self.input.at[row_index, self.CLEAN_POSTCODE] = section_postcds
            else:
                self.input.at[row_index, self.CLEAN_POSTCODE] = section_postcds

            # For each field gathered from the ONS Postcode Directory, find the
            # unique values from each Section, remove the default value. Then
            # if it's a Group, any Section with an invalid postcode update that
            # Section's records, as it is likely to be the same (or close to)
            # other Section's in the Group.
            for field in self.fields:
                areas = entity_sections[field].unique().tolist()
                if self.DEFAULT_VALUE in areas:
                    areas.remove(self.DEFAULT_VALUE)
                    if areas and (id_col == self.CENSUS_GROUP_ID):
                        section_field = areas[0]
                        for (section_row_id, section) in entity_sections.iterrows():
                            if section[field] == self.DEFAULT_VALUE:
                                self.input.at[section_row_id, field] = section_field
                if areas:
                    self.input.at[row_index, field] = areas

        # Write the new data to a csv file
        self.input.to_csv(self.output_csv)

        # The errors file contains all the postcodes that failed to be looked up
        # in the ONS Postcode Directory
        with open(self.ERROR_FILE,"w",encoding='latin-1') as error_file:
            error_file.write(postcode_errors)
