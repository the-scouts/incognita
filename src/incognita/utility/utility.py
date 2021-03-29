from __future__ import annotations

from functools import wraps
import time
from typing import TYPE_CHECKING

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import config

if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from incognita.data.ons_pd import ONSPostcodeDirectory


sections_model = scout_census.column_labels.sections
section_types = {section_model.type: section_name for section_name, section_model in sections_model}

# EPSG values for the co-ordinate reference systems that we use
WGS_84 = 4326  # World Geodetic System 1984 (Used in GPS)
BNG = 27700  # British National Grid


def time_function(method: Callable) -> Callable:
    """This method wraps functions to determine the execution time (clock time) for the function

    Incredible wrapping SO answer https://stackoverflow.com/a/1594484 (for future ref)

    The 'wrapped' method is the method that actually replaces all the normal method calls, with the
      normal method call inside

    Args:
        method: method to wrap

    Returns:
        wrapped method with execution time functionality

    """
    if not callable(method):
        raise ValueError("time_function must be called with a function or callable to wrap")

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # record a start time for the function
        start_time = time.time()
        logger.info(f"Calling function {method.__name__}")

        # call the original method with the passed arguments and keyword arguments, and store the result
        output = method(self, *args, **kwargs)
        logger.info(f"{method.__name__} took {time.time() - start_time:.2f} seconds")

        # return the output of the original function
        return output

    return wrapper


def filter_records(data: pd.DataFrame, field: str, value_list: set, mask: bool = False, exclusion_analysis: bool = False) -> pd.DataFrame:
    """Filters the Census records by any field in ONS PD.

    Args:
        data:
        field: The field on which to filter
        value_list: The values on which to filter
        mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
        exclusion_analysis:

    Returns:
        Filtered data

    """
    # Count number of rows
    original_records = len(data.index)
    excluded_data = original_data = None

    # Filter records
    if mask:
        # Excluding records that match the filter criteria
        logger.info(f"Selecting records that satisfy {field} not in {value_list} from {original_records} records.")
        if exclusion_analysis:
            original_data = data.copy()
            excluded_data = data.loc[data[field].isin(value_list)]
        data = data.loc[~data[field].isin(value_list)]
    else:
        # Including records that match the filter criteria
        logger.info(f"Selecting records that satisfy {field} in {value_list} from {original_records} records.")
        if exclusion_analysis:
            original_data = data.copy()
            excluded_data = data.loc[~data[field].isin(value_list)]
        data = data.loc[data[field].isin(value_list)]

    remaining_records = len(data.index)
    logger.info(f"Resulting in {remaining_records} records remaining.")

    if exclusion_analysis:
        cols = [scout_census.column_labels.UNIT_TYPE] + [section_model.total for section, section_model in sections_model]
        if not all([col in data.columns for col in cols]):
            raise ValueError("Required columns are not in dataset!\n" f"Required columns are: {cols}.\n" f"Your columns are: {data.columns.to_list()}")

        # Calculate the number of records that have been filtered out
        excluded_records = original_records - remaining_records
        logger.info(f"{excluded_records} records were removed ({excluded_records / original_records * 100}% of total)")

        # Prints number of members and % of members filtered out for each section
        for section_name, section_model in sections_model:
            logger.debug(f"Analysis of {section_name} member exclusions")
            section_type = section_model.type
            members_col = section_model.total

            excluded_sections = excluded_data.loc[excluded_data[scout_census.column_labels.UNIT_TYPE] == section_type]
            excluded_members = 0
            if not excluded_sections.empty:
                logger.debug(f"Excluded sections\n{excluded_sections}")
                logger.debug(f"Finding number of excluded {section_name} by summing {members_col}")
                excluded_members = excluded_sections[members_col].sum()
                logger.debug(f"{excluded_members} {section_name} excluded")

            original_members = original_data.loc[original_data[scout_census.column_labels.UNIT_TYPE] == section_type, members_col].sum()

            if original_members > 0:
                logger.info(f"{excluded_members} {section_name} members were removed ({excluded_members / original_members * 100}%) of total")
            else:
                logger.info(f"There are no {section_name} members present in data")

    return data


def calc_imd_decile(imd_ranks: pd.Series, country_codes: pd.Series, ons_object: ONSPostcodeDirectory) -> pd.Series:
    """Calculate IMD decile from ranks, country codes and ONS metadata.

    Args:
        imd_ranks:
        country_codes:
        ons_object:

    """

    # Map country codes to maximum IMD rank in each country, and broadcast to the array
    code_imd_map = {code: ons_object.IMD_MAX[country] for code, country in ons_object.COUNTRY_CODES.items()}
    imd_max = country_codes.map(code_imd_map).astype("Int32")

    # One of the two series must be of a 'normal' int dtype - excluding the new ones that can deal with NAs
    imd_max = _try_downcast(imd_max)
    imd_ranks = _try_downcast(imd_ranks)

    if not imd_max.empty:
        # upside down floor division to get ceiling
        # https://stackoverflow.com/a/17511341
        return -((-imd_ranks * 10).floordiv(imd_max))
    else:
        raise Exception("No IMD values found to calculate deciles from")


def _try_downcast(series: pd.Series) -> pd.Series:
    try:
        int_series = series.astype("int32")
        if series.eq(int_series).all():
            return int_series
        else:
            return series
    except ValueError:
        return series


def save_report(report: pd.DataFrame, report_name: str) -> None:
    logger.info(f"Writing to {report_name}")
    report.to_csv(config.SETTINGS.folders.output / f"{report_name}.csv", index=False, encoding="utf-8-sig")
