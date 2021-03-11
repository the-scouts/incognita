from __future__ import annotations

from functools import wraps
import json
from pathlib import Path
import time
from typing import TYPE_CHECKING

import pandas as pd

from incognita.data.scout_census import ScoutCensus
from incognita.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable
    import logging

    from incognita.data.ons_pd import ONSPostcodeDirectory


sections_dict = ScoutCensus.column_labels["sections"]
section_types = {sections_dict[section]["type"]: section for section in sections_dict.keys()}

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
LOGS_ROOT = PROJECT_ROOT / "scripts/logs"

SETTINGS = json.loads(SCRIPTS_ROOT.joinpath("settings.json").read_text())["settings"]
OUTPUT_FOLDER = PROJECT_ROOT.joinpath(SETTINGS["Output folder"]).absolute()

# EPSG values for the co-ordinate reference systems that we use
WGS_84 = 4326  # World Geodetic System 1984 (Used in GPS)
BNG = 27700  # British National Grid


def ensure_roots_exist() -> None:
    """Ensure root dirs exist."""
    for root_path in (DATA_ROOT, SCRIPTS_ROOT, LOGS_ROOT):
        root_path.mkdir(parents=True, exist_ok=True)


def time_function(method: Callable):
    """This method wraps functions to determine the execution time (clock time) for the function

    Incredible wrapping SO answer https://stackoverflow.com/a/1594484 (for future ref)

    The 'wrapped' method is the method that actually replaces all the normal method calls, with the
      normal method call inside

    :param function method: method to wrap
    :return function: wrapped method with execution time functionality
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


def filter_records(data: pd.DataFrame, field: str, value_list: list, logger: logging.Logger, mask: bool = False, exclusion_analysis: bool = False) -> pd.DataFrame:
    """Filters the Census records by any field in ONS PD.

    :param pd.DataFrame data:
    :param str field: The field on which to filter
    :param list value_list: The values on which to filter
    :param logging.Logger logger:
    :param bool mask: If True, exclude the values that match the filter. If False, keep the values that match the filter.
    :param bool exclusion_analysis:

    :returns pd.DataFrame: Nothing
    """
    # Count number of rows
    original_records = len(data.index)
    excluded_data = None

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
        cols = [ScoutCensus.column_labels["UNIT_TYPE"]] + [sections_dict[section]["total"] for section in sections_dict.keys()]
        if not all([col in data.columns for col in cols]):
            raise ValueError("Required columns are not in dataset!\n" f"Required columns are: {cols}.\n" f"Your columns are: {data.columns.to_list()}")

        # Calculate the number of records that have been filtered out
        excluded_records = original_records - remaining_records
        logger.info(f"{excluded_records} records were removed ({excluded_records / original_records * 100}% of total)")

        # Prints number of members and % of members filtered out for each section
        for section in sections_dict.keys():
            logger.debug(f"Analysis of {section} member exclusions")
            section_type = sections_dict[section]["type"]
            members_col = sections_dict[section]["total"]

            excluded_sections = excluded_data.loc[excluded_data[ScoutCensus.column_labels["UNIT_TYPE"]] == section_type]
            excluded_members = 0
            if not excluded_sections.empty:
                logger.debug(f"Excluded sections\n{excluded_sections}")
                logger.debug(f"Finding number of excluded {section} by summing {members_col}")
                excluded_members = excluded_sections[members_col].sum()
                logger.debug(f"{excluded_members} {section} excluded")

            original_members = original_data.loc[original_data[ScoutCensus.column_labels["UNIT_TYPE"]] == section_type, members_col].sum()

            if original_members > 0:
                logger.info(f"{excluded_members} {section} members were removed ({excluded_members / original_members * 100}%) of total")
            else:
                logger.info(f"There are no {section} members present in data")

    return data


def section_from_type(section_type: str) -> str:
    """returns section from section types lookup dict"""
    return section_types[section_type]


def section_from_type_vector(section_type: pd.Series) -> pd.Series:
    return section_type.map(section_types)


def calc_imd_decile(imd_ranks: pd.Series, country_codes: pd.Series, ons_object: ONSPostcodeDirectory) -> pd.Series:

    """

    :param pd.Series imd_ranks:
    :param pd.Series country_codes:
    :param ONSPostcodeDirectory ons_object:

    :var pd.Series country_names:
    :var pd.Series imd_max:
    :var pd.Series imd_deciles:

    :return:
    """

    country_names = country_codes.map(ons_object.COUNTRY_CODES)
    imd_max = country_names.map(ons_object.IMD_MAX)

    # One of the two series must be of a 'normal' int dtype - excluding the new ones that can deal with NAs
    imd_max = _try_downcast(imd_max)
    imd_ranks = _try_downcast(imd_ranks)

    if not imd_max.empty:
        # upside down floor division to get ceiling
        # https://stackoverflow.com/a/17511341
        imd_deciles = -((-imd_ranks * 10).floordiv(imd_max))
        return imd_deciles
    else:
        raise Exception("No IMD values found to calculate deciles from")


def _try_downcast(series: pd.Series) -> pd.Series:
    try:
        uint_series = series.astype("uint16")
        if series.equals(uint_series):
            return uint_series
        else:
            return series
    except ValueError:
        return series


def save_report(report: pd.DataFrame, report_name: str):
    logger.info(f"Writing to {report_name}")
    report.to_csv(OUTPUT_FOLDER / f"{report_name}.csv", index=False, encoding="utf-8-sig")


ensure_roots_exist()
