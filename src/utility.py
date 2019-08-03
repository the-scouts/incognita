import pandas as pd
from src.census_data import CensusData

sections_dict = CensusData.column_labels['sections']
section_types = {sections_dict[section]["type"]: section for section in sections_dict.keys()}


def filter_records(data, field, value_list, logger, mask=False, exclusion_analysis=False):
    """Filters the Census records by any field in ONS PD.

    :param data:
    :param str field: The field on which to filter
    :param list value_list: The values on which to filter
    :param logger:
    :param bool mask: If True, keep the values that match the filter. If False, keep the values that don't match the filter.
    :param bool exclusion_analysis:

    :returns None: Nothing
    """
    # Count number of rows
    original_records = len(data.index)
    excluded_data = None

    # Filter records
    if not mask:
        logger.info(f"Selecting records that satisfy {field} in {value_list} from {original_records} records.")
        if exclusion_analysis:
            excluded_data = data.loc[~data[field].isin(value_list)]
        data = data.loc[data[field].isin(value_list)]
    else:
        logger.info(f"Selecting records that satisfy {field} not in {value_list} from {original_records} records.")
        if exclusion_analysis:
            excluded_data = data.loc[data[field].isin(value_list)]
        data = data.loc[~data[field].isin(value_list)]

    remaining_records = len(data.index)
    logger.info(f"Resulting in {remaining_records} records remaining.")

    if exclusion_analysis:
        # Calculate the number of records that have been filtered out
        excluded_records = original_records - remaining_records
        logger.info(f"{excluded_records} records were removed ({excluded_records / original_records * 100}% of total)")

        # Prints number of members and % of members filtered out for each section
        for section in sections_dict.keys():
            logger.debug(f"Analysis of {section} member exclusions")
            section_type = sections_dict[section]["type"]
            members_cols = [sections_dict[section]["male"], sections_dict[section]["female"]]

            excluded_sections = excluded_data.loc[excluded_data[CensusData.column_labels['UNIT_TYPE']] == section_type]
            logger.debug(f"Excluded sections\n{excluded_sections}")
            logger.debug(f"Finding number of excluded {section} by summing {' and '.join(members_cols)}")
            excluded_members = excluded_sections[members_cols].to_numpy().sum()
            logger.debug(f"{excluded_members} {section} excluded")

            sections = data.loc[data[CensusData.column_labels['UNIT_TYPE']] == section_type]
            counted_members = sections[members_cols].to_numpy().sum()

            original_members = counted_members + excluded_members

            if original_members > 0:
                logger.info(
                    f"{excluded_members} {section} members were removed ({excluded_members / original_members * 100}%) of total")
            else:
                logger.info(f"There are no {section} members present in data")

    return data


def years_of_return(records: pd.Series):
    """

    :param pd.Series records: a pandas series containing integer years
    :return:
    """
    return records.min(), records.max()


def section_from_type(section_type):
    """returns section from section types lookup dict"""
    return section_types[section_type]


def calc_imd_decile(imd_ranks, country_codes, ons_object):
    """

    :param pd.Series imd_ranks:
    :param pd.Series or str country_codes:
    :param ons_object:

    :var pd.Series country_names:
    :var pd.Series country_codes:
    :var pd.Series imd_max:
    :var pd.Series imd_deciles:

    :return:
    """

    # to handle the one country case
    if type(country_codes) is str:
        temp_df = pd.DataFrame(imd_ranks)
        temp_df["country"] = country_codes
        country_codes = temp_df["country"]
        del temp_df

    country_names = country_codes.map(ons_object.COUNTRY_CODES)
    imd_max = country_names.map(ons_object.IMD_MAX)

    # One of the two series must be of a 'normal' int dtype - excluding the new ones that can deal with NAs
    imd_max = try_downcast(imd_max)
    imd_ranks = try_downcast(imd_ranks)

    if not imd_max.empty:
        # upside down floor division to get ceiling
        # https://stackoverflow.com/a/17511341
        imd_deciles = -((-imd_ranks * 10).floordiv(imd_max))
        return imd_deciles
    else:
        raise Exception("No IMD values found to calculate deciles from")


def try_downcast(series):
    try:
        uint_series = series.astype('uint16')
        if series.equals(uint_series):
            return uint_series
        else:
            return series
    except ValueError:
        return series


def country_add_imd_decile(data, country, ons_object):
    """Used to add IMD data to DataFrames that aren't the core census data

    For example used to add IMD deciles to Lower Super Output Area boundary
    reports.

    All boundaries must be from the same country.

    :param DataFrame data: Data to add IMD decile to. Must have 'imd' column
    :param str country: Country code
    :param ons_object:

    :returns DataFrame: Original DataFrame with extra imd_decile column
    """
    data["imd_decile"] = calc_imd_decile(data["imd"], country, ons_object)
    return data


def save_report(report, output_path, report_name, logger=None):
    if logger:
        logger.info(f"Writing to {report_name}")
    report.to_csv(output_path + report_name + ".csv", index=False, encoding='utf-8-sig')
