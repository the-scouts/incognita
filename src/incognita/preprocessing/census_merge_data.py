"""Merges input data with ScoutCensus data on a given key

Outputs a file which is contains the original data, a postcode validity check, and the merged fields appended.
The output is the original csv with the additional columns 'postcode_is_valid' and those specified in fields
"""

import re
from typing import Union

import numpy as np
import pandas as pd

from incognita.data import scout_census
from incognita.logger import logger

TYPES_FISP_ARGS = tuple[str, int, pd.DataFrame, str, str]


def merge_data(census_data: pd.DataFrame, data_to_merge: Union[pd.DataFrame, pd.Series], census_index_column: str) -> pd.DataFrame:
    """Merge census data and input data on key and index.

    Args:
        census_data: Scout census data
        data_to_merge: DataFrame with index col as index to merge
        census_index_column: column label to merge on in census data

    Returns:
        Dataframe with merged data, and an indicator in each row signifying merge success

    """
    # Column heading denoting a valid postcode in the row
    valid_postcode_label = scout_census.column_labels.VALID_POSTCODE

    logger.info("Merging data")
    census_data = pd.merge(census_data, data_to_merge, how="left", left_on=census_index_column, right_index=True, sort=False)

    # Checks whether ONS data exists for each row and stores in a column
    census_data[valid_postcode_label] = (~census_data["ctry"].isnull()).astype(int)

    return census_data


def _pad_to_seven(single_postcode):  # r'(.*?(?=.{3}$))(.{3}$)' (potential regex)
    """Pad postcode strings

    If length of postcode is 6 or 5 then insert 1 or 2 spaces.
    6 first as more common to speed up execution
    """
    if single_postcode == single_postcode:  # filters out NaNs
        length = len(single_postcode)
        if length == 6 or length == 5:
            single_postcode = single_postcode[:-3] + " " * (7 - length) + single_postcode[-3:]
    return single_postcode


def _postcode_cleaner(postcode: pd.Series) -> pd.Series:
    """Cleans postcode to ONS postcode directory format.

    Args:
        postcode: pandas series of postcodes

    Returns:
        Cleaned postcode

    """

    # Regular expression to remove whitespace, non-alphanumeric (keep shifted numbers)
    regex_clean = re.compile(r'[\s+]|[^a-zA-Z\d!"£$%^&*()]')

    # Remove any whitespace and most non-alphanumeric chars
    # Convert input to uppercase (ONS Postcode Directory uses upper case)
    # Pads length as we use the 7 long version from the Postcode Directory
    postcode = postcode.str.replace(regex_clean, "").str.upper().apply(lambda single_postcode: _pad_to_seven(single_postcode))

    # Replaces shifted numbers with their number equivalents
    postcode = (
        postcode.str.replace("!", "1", regex=False)
        .str.replace('"', "2", regex=False)
        .str.replace("£", "3", regex=False)
        .str.replace("$", "4", regex=False)
        .str.replace("%", "5", regex=False)
        .str.replace("^", "6", regex=False)
        .str.replace("&", "7", regex=False)
        .str.replace("*", "8", regex=False)
        .str.replace("(", "9", regex=False)
        .str.replace(")", "0", regex=False)
    )
    # TODO: add macOS shift -> numbers conversion

    return postcode


def fill_unmerged_rows(census_data: pd.DataFrame, row_has_merged: str, fields_data_types: dict) -> pd.DataFrame:
    """Fills rows that have not merged with default values

    Fills all passed fields in rows where there has been no data merged
    Fills categorical fields with scout_census.DEFAULT_VALUE and numerical fields with 0

    Args:
        census_data: DataFrame with census data
        row_has_merged: column label for column with booleans of if the merge was successful
        fields_data_types: dict of data types containing lists of fields

    Returns:
        dataframe with filled values

    """
    for field in fields_data_types["categorical"]:
        if scout_census.DEFAULT_VALUE not in census_data[field].cat.categories:
            census_data[field] = census_data[field].cat.add_categories([scout_census.DEFAULT_VALUE])
        census_data.loc[census_data[row_has_merged] == 0, field] = scout_census.DEFAULT_VALUE
    for field in fields_data_types["numeric"]:
        census_data.loc[census_data[row_has_merged] == 0, field] = 0

    return census_data


def clean_and_verify_postcode(census_data: pd.DataFrame, postcode_column: str) -> None:
    """Cleans postcode data and inserts clean postcodes and validity check

    Cleans postcode data from passed table and index
    Gets index of postcode column, and inserts new columns after postcode column

    Args:
        census_data: table of data with a postcode column
        postcode_column: heading of the postcode column in the table

    """
    # Gets the index of the postcode column, and increments as insertion is from the left.
    # Columns must be inserted in number order otherwise it wont't make sense
    postcode_column_index = census_data.columns.get_loc(postcode_column)  # scout_census.column_labels.POSTCODE
    cleaned_postcode_index = postcode_column_index + 1
    valid_postcode_index = postcode_column_index + 2

    # Sets the labels for the columns to be inserted
    cleaned_postcode_label = "clean_postcode"
    valid_postcode_label = scout_census.column_labels.VALID_POSTCODE

    logger.info("Cleaning postcodes")
    cleaned_postcode_column = _postcode_cleaner(census_data[postcode_column])

    logger.info("Inserting columns")
    census_data.insert(cleaned_postcode_index, cleaned_postcode_label, cleaned_postcode_column)
    census_data.insert(valid_postcode_index, valid_postcode_label, np.NaN)


def _create_helper_tables(
    data: pd.DataFrame,
    entity_type_list: set[str],
    entity_type_label: str,
    fields_for_postcode_lookup: list[str],
    valid_postcode_label: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Filters records by type and returns a subset of columns to reduce memory usage
    records_filtered_fields = data.loc[data[entity_type_label].isin(entity_type_list), fields_for_postcode_lookup]

    # Creates loookup of all valid postcodes from filtered records, and
    # fully sorts the index to increase performance
    lookup = records_filtered_fields.loc[records_filtered_fields[valid_postcode_label] == 1].sort_index(level=[0, 1, 2, 3])

    return records_filtered_fields, lookup


def _run_fixer(
    data: pd.DataFrame,
    records: pd.DataFrame,
    valid_postcode_label: str,
    merge_test_column: pd.Series,
    column_label: str,
    index_level: int,
    valid_clean_postcodes: pd.Series,
    clean_postcode_label: str,
) -> pd.DataFrame:
    """Runs postcode fixer for given data and parameters.

    Method:
    Gets all records with ID from given column and index level, then clears the indexing
    Returns the first row's postcode. As the index is sorted, this will return the earliest correct year.
    TODO change to use modal result instead of first (If section has no valid postcodes, use most common
        (modal) postcode from sections in group in that year, then try successive years)

    Args:
      data: Census data
      records:
      valid_postcode_label: Label to index for
      merge_test_column:
      column_label Label to index for
      index_level: Level of the MultiIndex to use
      valid_clean_postcodes:
      clean_postcode_label:

    Returns:
        Updated census data

    """
    # Index level: 0=District; 1=Group; 2=Section; 3=Census_ID

    valid_postcodes_start = data[valid_postcode_label].to_numpy().sum()

    # Get all clean postcodes from the lookup table with the same ID as
    # the passed index level. As the census IDs are sorted high -> low,
    # the first item will be the newest possible clean postcode.
    firsts = valid_clean_postcodes.sort_index(ascending=(True, True, True, False)).groupby(level=index_level).first()

    # Map invalid postcodes to valid postcodes by the given ID type/field
    clean_postcodes = records.loc[records[valid_postcode_label] == 0, column_label].map(firsts)

    # Merge in the changed postcodes and overwrite pre-existing postcodes in the Clean Postcode column
    clean_postcodes_not_na = clean_postcodes.loc[clean_postcodes.notna()]  # .update(*) uses not_na filter
    data.loc[clean_postcodes_not_na.index, clean_postcode_label] = clean_postcodes_not_na

    # Delete the Country column from the passed data as having this would prevent merging
    # Pass only the merge test column as a quick way to test that the postcode has merged
    data = merge_data(data, merge_test_column, "clean_postcode").drop(merge_test_column.name, axis=1)
    logger.info(f"change in valid postcodes is: {data[valid_postcode_label].sum() - valid_postcodes_start}")

    return data


def _run_postcode_fix_step(
    census_data: pd.DataFrame, merge_test_column: pd.Series, invalid_type: str, fill_from: str, entity_type_list: set[str], column_label: str, index_level: int
):
    # Helper variables to store field headings for often used fields
    entity_type_label = scout_census.column_labels.UNIT_TYPE
    section_id_label = scout_census.column_labels.id.COMPASS
    group_id_label = scout_census.column_labels.id.GROUP
    district_id_label = scout_census.column_labels.id.DISTRICT
    clean_postcode_label = "clean_postcode"
    valid_postcode_label = scout_census.column_labels.VALID_POSTCODE
    census_id_label = scout_census.column_labels.CENSUS_ID

    # Columns to return to the .apply function to reduce memory usage
    # fmt: off
    fields_for_postcode_lookup = [
        valid_postcode_label, clean_postcode_label, census_id_label,
        # Add to to items below if a new column is used in the fix process
        section_id_label,
        group_id_label,
        district_id_label,
    ]
    # fmt: on

    logger.info(f"Fill invalid {invalid_type} postcodes with valid section postcodes from {fill_from}")
    section_records, valid_postcode_lookup = _create_helper_tables(census_data, entity_type_list, entity_type_label, fields_for_postcode_lookup, valid_postcode_label)
    vpl_cp = valid_postcode_lookup[clean_postcode_label]
    census_data = _run_fixer(census_data, section_records, valid_postcode_label, merge_test_column, column_label, index_level, vpl_cp, clean_postcode_label)
    return census_data


def try_fix_invalid_postcodes(census_data: pd.DataFrame, merge_test_column: pd.Series) -> pd.DataFrame:
    """Uses various methods attempting to provide every record with a valid postcode

    Currently only implemented for sections with youth membership.
    TODO: implement for all entity types

    Methodology:
    - If section has an invalid postcode in 2017 or 2018, use 2019's if valid (all are valid or missing in 2019)
    - If section has no valid postcodes, use most common (mode) postcode from sections in group in that year, then try successive years
    - If group or district has no valid postcode in 2010-2016, use following years (e.g. if 2010 not valid, try 2011, 12, 13 etc.)

    Args:
        census_data: Dataframe of census data including invalid postcodes
        merge_test_column: a column from the ONS Postcode Directory to test validity of the postcode by attempting to merge

    Returns:
        modified data table with more correct postcodes

    """

    logger.info("filling postcodes in sections with invalid postcodes")

    # Helper variables to store field headings for often used fields
    section_id_label = scout_census.column_labels.id.COMPASS
    group_id_label = scout_census.column_labels.id.GROUP
    district_id_label = scout_census.column_labels.id.DISTRICT
    clean_postcode_label = "clean_postcode"
    census_id_label = scout_census.column_labels.CENSUS_ID

    # Lists of entity types to match against in constructing section records tables
    group_section_types_list = scout_census.TYPES_GROUP
    district_section_types_list = scout_census.TYPES_DISTRICT
    section_types_list = group_section_types_list | district_section_types_list
    pre_2017_types_list = {"Group", "District"}

    # Columns to use in constructing the MultiIndex. Larger groups go first towards smaller
    index_cols = [district_id_label, group_id_label, section_id_label, census_id_label]

    # Sets a MultiIndex on the data table to enable fast searching and querying for data
    census_data = census_data.set_index(index_cols, drop=False)

    census_data = census_data.drop(columns=merge_test_column.name)
    census_data = _run_postcode_fix_step(census_data, merge_test_column, "section", "2019", section_types_list, section_id_label, 2)
    census_data = _run_postcode_fix_step(census_data, merge_test_column, "group-section", "same group", group_section_types_list, group_id_label, 1)
    census_data = _run_postcode_fix_step(census_data, merge_test_column, "district-section", "same district", district_section_types_list, district_id_label, 0)
    census_data = _run_postcode_fix_step(census_data, merge_test_column, "pre 2017", "same entity", pre_2017_types_list, section_id_label, 2)

    # normalise missing data
    census_data.loc[census_data[clean_postcode_label].isin({"", "NA", pd.NA, np.NaN}), clean_postcode_label] = float("NaN")

    # Undo the changes made in this method by removing the MultiIndex and
    # removing the merge test column
    census_data = census_data.reset_index(drop=True)
    return census_data
