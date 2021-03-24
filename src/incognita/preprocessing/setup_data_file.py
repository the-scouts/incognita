"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from incognita.data import scout_census
from incognita.data.ons_pd_may_19 import ons_postcode_directory_may_19
from incognita.data.scout_data import ScoutData
from incognita.logger import logger
from incognita.preprocessing.census_merge_data import CensusMergeData
from incognita.utility import config
from incognita.utility import utility

if TYPE_CHECKING:
    import pandas as pd

    from incognita.data.ons_pd import ONSPostcodeDirectory


def merge_ons_postcode_directory(data: pd.DataFrame, ons_pd: ONSPostcodeDirectory) -> pd.DataFrame:
    """Merges census extract data with ONS data

    Args:
        data: Census data
        ons_pd: A reference to an ONS Postcode Directory model instance

    """
    ons_fields_data_types = {
        "categorical": ["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "ctry", "rgn"],
        "int": ["oseast1m", "osnrth1m", "lat", "long", "imd"],
    }

    logger.debug("Initialising merge object")
    merge = CensusMergeData()

    logger.info("Cleaning the postcodes")
    merge.clean_and_verify_postcode(data, scout_census.column_labels.POSTCODE)

    logger.info(f"Loading ONS postcode data.")
    ons_pd_data = pd.read_csv(
        config.SETTINGS.ons_pd.full,
        index_col=ons_pd.index_column,
        dtype=ons_pd.data_types,
        usecols=[*ons_pd.fields],
        encoding="utf-8",
    )

    logger.info("Adding ONS postcode directory data to Census and outputting")

    # initially merge just Country column to test what postcodes can match
    data = merge.merge_data(data, ons_pd_data["ctry"], "clean_postcode")

    # attempt to fix invalid postcodes
    data = merge.try_fix_invalid_postcodes(data, ons_pd_data["ctry"])

    # fully merge the data
    data = merge.merge_data(data, ons_pd_data, "clean_postcode")

    # fill unmerged rows with default values
    logger.info("filling unmerged rows")
    data = merge.fill_unmerged_rows(data, scout_census.column_labels.VALID_POSTCODE, ons_fields_data_types)

    # Filter to useful columns
    # fmt: off
    data = data[[
        "Object_ID", "compass", "type", "name", "G_ID", "G_name", "D_ID", "D_name", "C_ID", "C_name", "R_ID", "R_name", "X_ID", "X_name",
        "postcode", "clean_postcode", "postcode_is_valid", "Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Young_Leader_Unit",
        "Beavers_f", "Beavers_m", "Beavers_total", "Cubs_f", "Cubs_m", "Cubs_total", "Scouts_f", "Scouts_m", "Scouts_total", "Explorers_f", "Explorers_m", "Explorers_total",
        "Network_f", "Network_m", "Network_total", "Yls", "WaitList_b", "WaitList_c", "WaitList_s", "WaitList_e", "Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults",
        "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards", "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards",
        "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver", "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "ScoutsOfTheWorldAward", "Queens_Scout_Awards",
        "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond", "Eligible4QSA", "Eligible4SOWA",
        "oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "lat", "long", "imd"
    ]]
    # fmt: on

    # Add IMD decile column
    data["imd_decile"] = utility.calc_imd_decile(data["imd"], data["ctry"], ons_pd).astype("UInt8")

    return data


def save_merged_data(data: pd.DataFrame, ons_pd_publication_date: str) -> None:
    """Save passed dataframe to csv file.

    Also output list of errors in the merge process to a text file

    Args:
        data: Census data
        ons_pd_publication_date: Refers to the ONS Postcode Directory's publication date

    """
    raw_extract_path = config.SETTINGS.census_extract.original
    output_path = raw_extract_path.parent / f"{raw_extract_path.stem} with {ons_pd_publication_date} fields"
    error_output_path = config.SETTINGS.folders.output / "error_file.csv"

    valid_postcode_label = scout_census.column_labels.VALID_POSTCODE
    postcode_merge_column = "clean_postcode"
    original_postcode_label = scout_census.column_labels.POSTCODE
    compass_id_label = scout_census.column_labels.id.COMPASS

    # The errors file contains all the postcodes that failed to be looked up in the ONS Postcode Directory
    error_output_fields = [postcode_merge_column, original_postcode_label, compass_id_label, "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "Year"]
    data.loc[data[valid_postcode_label] == 0, error_output_fields].to_csv(error_output_path, index=False, encoding="utf-8-sig")

    # Write the new data to a csv file (utf-8-sig only to force excel to use UTF-8)
    logger.info("Writing merged data")
    data.to_csv(output_path.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    data.to_feather(output_path.with_suffix(".feather"))


if __name__ == "__main__":
    # load raw census extract
    scout_data = ScoutData(merged_csv=False, census_path=config.SETTINGS.census_extract.original)

    # combine all youth membership columns into a single total
    for section_name, section_model in scout_census.column_labels.sections:
        scout_data.census_data[f"{section_name}_total"] = scout_data.census_data[section_model.youth_cols].sum(axis=1).astype("Int16")

    # backticks (`) break folium's output as it uses ES2015 template literals in the output file.
    scout_data.census_data[scout_census.column_labels.name.ITEM] = scout_data.census_data[scout_census.column_labels.name.ITEM].str.replace("`", "")

    # merge the census extract and ONS postcode directory, and save the data to file
    data = merge_ons_postcode_directory(scout_data.census_data, ons_postcode_directory_may_19)
    save_merged_data(data, ons_postcode_directory_may_19.PUBLICATION_DATE)

    scout_data.close()
