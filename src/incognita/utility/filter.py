from __future__ import annotations

from typing import TYPE_CHECKING

from incognita.data import scout_census
from incognita.logger import logger

if TYPE_CHECKING:
    import pandas as pd

sections_model = scout_census.column_labels.sections


def filter_records(data: pd.DataFrame, field: str, value_list: set, exclude_matching: bool = False, exclusion_analysis: bool = False) -> pd.DataFrame:
    """Filters the Census records by any field in ONS PD.

    Args:
        data:
        field: The field on which to filter
        value_list: The values on which to filter
        exclude_matching: If True, exclude the values that match the filter. If False, keep the values that match the filter.
        exclusion_analysis:

    Returns:
        Filtered data

    """
    # Count number of rows
    original_records = data.index.size
    matching_records = data[field].isin(value_list)
    if exclude_matching:
        # Excluding records that match the filter criteria
        filter_mask = ~matching_records
        logger.info(f"Selecting records that satisfy {field} not in {value_list} from {original_records} records.")
    else:
        # Including records that match the filter criteria
        filter_mask = matching_records
        logger.info(f"Selecting records that satisfy {field} in {value_list} from {original_records} records.")

    filtered = data.loc[filter_mask]
    logger.debug(f"Resulting in {filtered.index.size} records remaining.")

    if exclusion_analysis:
        excluded = data.loc[~filter_mask]
        _exclusion_analysis(data, filtered, excluded)

    return filtered


def _exclusion_analysis(original: pd.DataFrame, filtered: pd.DataFrame, excluded: pd.DataFrame):
    cols = {scout_census.column_labels.UNIT_TYPE, *(section_model.total for section, section_model in sections_model)}
    if not set(original.columns) >= cols:
        o_cols = original.columns.to_list()
        raise ValueError("Required columns are not in dataset!\n" f"Required columns are: {cols}.\n" f"Your columns are: {o_cols}")

    # Calculate the number of records that have been filtered out
    original_records = original.index.size
    excluded_records = original_records - filtered.index.size
    logger.info(f"{excluded_records} records were removed ({excluded_records / original_records * 100}% of total)")

    # Prints number of members and % of members filtered out for each section
    for section_name, section_model in sections_model:
        logger.debug(f"Analysis of {section_name} member exclusions")
        section_type = section_model.type
        members_col = section_model.total

        excluded_sections = excluded.loc[excluded[scout_census.column_labels.UNIT_TYPE] == section_type]
        excluded_members = 0
        if not excluded_sections.empty:
            logger.debug(f"Excluded sections\n{excluded_sections}")
            logger.debug(f"Finding number of excluded {section_name} by summing {members_col}")
            excluded_members = excluded_sections[members_col].sum()
            logger.debug(f"{excluded_members} {section_name} excluded")

        original_members = original.loc[original[scout_census.column_labels.UNIT_TYPE] == section_type, members_col].sum()
        if original_members > 0:
            logger.info(f"{excluded_members} {section_name} members were removed ({excluded_members / original_members * 100}%) of total")
        else:
            logger.info(f"There are no {section_name} members present in data")
