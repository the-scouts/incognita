"""Merges ONS postcode data with census data

Outputs a file which is contains the original census data, a postcode validity
check, and the merged data.

The output fields are those in the census and ONS data, and the additional
fields 'postcode_is_valid' and 'clean_postcode'.
"""

import re

import pandas as pd

from incognita.data import scout_census
from incognita.logger import logger

CLEAN_POSTCODE_LABEL = "clean_postcode"


def merge_with_postcode_directory(census_data: pd.DataFrame, ons_pd_data: pd.DataFrame, ons_fields_data_types: dict[str, list[str]]) -> pd.DataFrame:
    logger.info("Cleaning the postcodes")
    _clean_and_verify_postcode(census_data)

    # attempt to fix invalid postcodes
    logger.info("Adding ONS postcode directory data to Census and outputting")
    data = _try_fix_invalid_postcodes(census_data, ons_pd_data.index)

    # fully merge the data
    logger.info("Merging data")
    data = pd.merge(data, ons_pd_data, how="left", left_on="clean_postcode", right_index=True, sort=False)

    # fill unmerged rows with default values
    logger.info("filling unmerged rows")
    data = _fill_unmerged_rows(data, ons_fields_data_types)

    return data


def _clean_and_verify_postcode(census_data: pd.DataFrame) -> None:
    """Cleans postcode data and inserts clean postcodes and validity check

    Cleans postcode data from passed table and index
    Gets index of postcode column, and inserts new columns after postcode column

    Args:
        census_data: table of data with a postcode column

    """
    # Gets the index of the postcode column, and increments as insertion is from the left.
    # Columns must be inserted in number order otherwise it wont't make sense
    postcode_column = scout_census.column_labels.POSTCODE  # heading of the postcode column in the table
    postcode_column_index = census_data.columns.get_loc(postcode_column)  # scout_census.column_labels.POSTCODE
    cleaned_postcode_index = postcode_column_index + 1
    valid_postcode_index = postcode_column_index + 2

    # Sets the labels for the columns to be inserted
    valid_postcode_label = scout_census.column_labels.VALID_POSTCODE

    logger.info("Cleaning postcodes")
    cleaned_postcode_column = _postcode_cleaner(census_data[postcode_column])

    logger.info("Inserting columns")
    census_data.insert(cleaned_postcode_index, CLEAN_POSTCODE_LABEL, cleaned_postcode_column)
    census_data.insert(valid_postcode_index, valid_postcode_label, float("NaN"))


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


def _try_fix_invalid_postcodes(census_data: pd.DataFrame, all_valid_postcodes: pd.Index) -> pd.DataFrame:
    """Uses various methods attempting to provide every record with a valid postcode

    Currently only implemented for sections with youth membership.
    TODO: implement for all entity types

    Methodology:
    - If section has an invalid postcode in 2017 or 2018, use 2019's if valid (all are valid or missing in 2019)
    - If section has no valid postcodes, use most common (mode) postcode from sections in group in that year, then try successive years
    - If group or district has no valid postcode in 2010-2016, use following years (e.g. if 2010 not valid, try 2011, 12, 13 etc.)

    Args:
        census_data: Dataframe of census data including invalid postcodes
        all_valid_postcodes: All valid postcodes from the ONS Postcode Directory

    Returns:
        modified data table with more correct postcodes

    """

    logger.info("filling postcodes in sections with invalid postcodes")

    # Helper variables to store field headings for often used fields
    section_id_label = scout_census.column_labels.id.COMPASS
    group_id_label = scout_census.column_labels.id.GROUP
    district_id_label = scout_census.column_labels.id.DISTRICT

    # Lists of entity types to match against in constructing section records tables
    group_section_types = scout_census.TYPES_GROUP
    district_section_types = scout_census.TYPES_DISTRICT
    section_types = group_section_types | district_section_types
    pre_2017_types = {"Group", "District"}

    # Columns to use in constructing the MultiIndex. Larger groups go first towards smaller
    index_cols = [district_id_label, group_id_label, section_id_label, scout_census.column_labels.CENSUS_ID]

    # Find which postcodes are valid
    census_data[scout_census.column_labels.VALID_POSTCODE] = census_data[CLEAN_POSTCODE_LABEL].isin(all_valid_postcodes)

    # Sets a MultiIndex on the data table to enable fast searching and querying for data
    census_data = census_data.set_index(index_cols, drop=False)

    census_data = _run_postcode_fix_step(census_data, all_valid_postcodes, "section", "latest Census", section_types, section_id_label, 2)
    census_data = _run_postcode_fix_step(census_data, all_valid_postcodes, "group-section", "same group", group_section_types, group_id_label, 1)
    census_data = _run_postcode_fix_step(census_data, all_valid_postcodes, "district-section", "same district", district_section_types, district_id_label, 0)
    census_data = _run_postcode_fix_step(census_data, all_valid_postcodes, "pre 2017", "same entity", pre_2017_types, section_id_label, 2)

    # Undo the changes made in this method by removing the MultiIndex and
    # removing the merge test column
    census_data = census_data.reset_index(drop=True)
    return census_data


def _fill_unmerged_rows(census_data: pd.DataFrame, fields_data_types: dict) -> pd.DataFrame:
    """Fills rows that have not merged with default values

    Fills all passed fields in rows where there has been no data merged
    Fills categorical fields with scout_census.DEFAULT_VALUE and numerical fields with 0

    Args:
        census_data: DataFrame with census data
        fields_data_types: dict of data types containing lists of fields

    Returns:
        dataframe with filled values

    """
    row_has_merged = scout_census.column_labels.VALID_POSTCODE  # column label for column with booleans of if the merge was successful
    for field in fields_data_types["categorical"]:
        if scout_census.DEFAULT_VALUE not in census_data[field].cat.categories:
            census_data[field] = census_data[field].cat.add_categories([scout_census.DEFAULT_VALUE])
        census_data.loc[~census_data[row_has_merged], field] = scout_census.DEFAULT_VALUE
    for field in fields_data_types["numeric"]:
        census_data.loc[~census_data[row_has_merged], field] = 0

    return census_data


def _run_postcode_fix_step(
    data: pd.DataFrame, all_valid_postcodes: pd.Index, invalid_type: str, fill_from: str, entity_types: set[str], column_label: str, index_level: int
) -> pd.DataFrame:
    """Runs postcode fixer for given data and parameters.

    Method:
    Gets all records with ID from given column and index level, then clears the indexing
    Returns the first row's postcode. As the index is sorted, this will return the earliest correct year.
    TODO change to use modal result instead of first (If section has no valid postcodes, use most common
        (modal) postcode from sections in group in that year, then try successive years)

    Args:
        data: Census data
        all_valid_postcodes: Index of all valid postcodes in the ONS postcode directory
        invalid_type: Which type of issue are we fixing (for log message)
        fill_from: Where are we pulling valid postcodes from (for log message)
        entity_types: Entity types to filter the fixing on (e.g. Colony, Group, Network, District)
        column_label: Name of the index level being used
        index_level: Level of the MultiIndex to filter on

    Returns:
        Updated census data

    """
    # Index level: 0=District; 1=Group; 2=Section; 3=Census_ID

    logger.info(f"Fill invalid {invalid_type} postcodes with valid section postcodes from {fill_from}")

    entity_type_label = scout_census.column_labels.UNIT_TYPE
    valid_postcode_label = scout_census.column_labels.VALID_POSTCODE

    # Gets all entity records matching the given criteria, and returns a
    # minimal set of fields for memory optimisation
    records = data.loc[data[entity_type_label].isin(entity_types), [valid_postcode_label, column_label, CLEAN_POSTCODE_LABEL]]

    valid_postcodes_start = data[valid_postcode_label].to_numpy().sum()

    # Get all valid clean postcodes from the filtered records. Then sort the
    # index with census IDs high -> low. Then group the data by the passed
    # index level. As the census IDs are sorted descending, the first item will
    # be the newest possible clean postcode, indexed by the passed level.
    firsts = records.loc[records[valid_postcode_label], CLEAN_POSTCODE_LABEL].sort_index(ascending=(True, True, True, False)).groupby(level=index_level).first()

    # Map invalid postcodes to valid postcodes by the given ID type/field
    clean_postcodes = records.loc[~records[valid_postcode_label], column_label].map(firsts)

    # Merge in the changed postcodes and overwrite pre-existing postcodes in the Clean Postcode column
    clean_postcodes_not_na = clean_postcodes.loc[clean_postcodes.notna()]  # .update(*) uses not_na filter
    data.loc[clean_postcodes_not_na.index, CLEAN_POSTCODE_LABEL] = clean_postcodes_not_na

    # Update valid postcode status
    data[valid_postcode_label] = data[CLEAN_POSTCODE_LABEL].isin(all_valid_postcodes)

    logger.info(f"change in valid postcodes is: {data[valid_postcode_label].to_numpy().sum() - valid_postcodes_start}")

    return data
