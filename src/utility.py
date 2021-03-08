from __future__ import annotations
from pathlib import Path
import pandas as pd
from src.data.scout_census import ScoutCensus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import logging
    from src.data.ons_pd import ONSPostcodeDirectory


sections_dict = ScoutCensus.column_labels["sections"]
section_types = {sections_dict[section]["type"]: section for section in sections_dict.keys()}


def get_proj_root() -> Path:
    return Path(__file__).parent.parent


DATA_ROOT = get_proj_root().joinpath("data")
SCRIPTS_ROOT = get_proj_root().joinpath("scripts")
LOGS_ROOT = get_proj_root().joinpath("scripts/logs")


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
            excluded_data = data.loc[data[field].isin(value_list)]
        data = data.loc[~data[field].isin(value_list)]
    else:
        # Including records that match the filter criteria
        logger.info(f"Selecting records that satisfy {field} in {value_list} from {original_records} records.")
        if exclusion_analysis:
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
            logger.debug(f"Excluded sections\n{excluded_sections}")
            logger.debug(f"Finding number of excluded {section} by summing {members_col}")
            excluded_members = excluded_sections[members_col].sum()
            logger.debug(f"{excluded_members} {section} excluded")

            sections = data.loc[data[ScoutCensus.column_labels["UNIT_TYPE"]] == section_type]
            counted_members = sections[members_col].sum()

            original_members = counted_members + excluded_members

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


def save_report(report: pd.DataFrame, output_path: str, report_name: str, logger: logging.Logger = None):
    if logger:
        logger.info(f"Writing to {report_name}")
    report.to_csv(output_path + report_name + ".csv", index=False, encoding="utf-8-sig")
