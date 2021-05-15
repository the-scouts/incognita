"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pandas as pd

from incognita.data import scout_census
from incognita.data.ons_pd_may_19 import ons_postcode_directory_may_19
from incognita.logger import logger
from incognita.logger import set_up_logger
from incognita.preprocessing import census_merge_data
from incognita.utility import config
from incognita.utility import deciles

if TYPE_CHECKING:
    from incognita.data.ons_pd import ONSPostcodeDirectory

# TODO add yp total columns, clean postcode/valid postcode, Asst leaders, SOWA/SOWA eligible, ONS PD fields
# fmt: off
cols_bool = ["postcode_is_valid"]
cols_int_16 = [
    "Year", "Beavers_Units", "Cubs_Units", "Scouts_Units", "Explorers_Units", "Network_Units", "Beavers_f", "Beavers_m", "Cubs_f", "Beavers_total", "Cubs_m", "Cubs_total",
    "Scouts_f", "Scouts_m", "Scouts_total", "Explorers_f", "Explorers_m", "Explorers_total", "Network_f", "Network_m", "Network_total", "Yls", "WaitList_b", "WaitList_c",
    "WaitList_s", "WaitList_e", "Leaders", "AssistantLeaders", "SectAssistants", "OtherAdults", "Chief_Scout_Bronze_Awards", "Chief_Scout_Silver_Awards",
    "Chief_Scout_Gold_Awards", "Chief_Scout_Platinum_Awards", "Chief_Scout_Diamond_Awards", "Duke_Of_Edinburghs_Bronze", "Duke_Of_Edinburghs_Silver",
    "Duke_Of_Edinburghs_Gold", "Young_Leader_Belts", "Explorer_Belts", "Queens_Scout_Awards", "Eligible4Bronze", "Eligible4Silver", "Eligible4Gold", "Eligible4Diamond",
    "Eligible4QSA", "ScoutsOfTheWorldAward", "Eligible4SOWA",
]
cols_int_32 = ["Object_ID", "G_ID", "D_ID", "C_ID", "R_ID", "X_ID", "imd"]
cols_categorical = ["compass", "type", "name", "G_name", "D_name", "C_name", "R_name", "X_name", "postcode", "clean_postcode", "Young_Leader_Unit"]
# fmt: on


def merge_ons_postcode_directory(data: pd.DataFrame, ons_pd: ONSPostcodeDirectory) -> pd.DataFrame:
    """Merges census extract data with ONS data

    Args:
        data: Census data
        ons_pd: A reference to an ONS Postcode Directory model instance

    """
    ons_fields_data_types = {
        "categorical": ["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "ctry", "rgn"],
        "numeric": ["oseast1m", "osnrth1m", "lat", "long", "imd"],
    }

    logger.debug("Initialising merge object")

    logger.info("Cleaning the postcodes")
    census_merge_data.clean_and_verify_postcode(data, scout_census.column_labels.POSTCODE)

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
    data = census_merge_data.merge_data(data, ons_pd_data["ctry"], "clean_postcode")

    # attempt to fix invalid postcodes
    data = census_merge_data.try_fix_invalid_postcodes(data, ons_pd_data["ctry"])

    # fully merge the data
    data = census_merge_data.merge_data(data, ons_pd_data, "clean_postcode")

    # fill unmerged rows with default values
    logger.info("filling unmerged rows")
    data = census_merge_data.fill_unmerged_rows(data, scout_census.column_labels.VALID_POSTCODE, ons_fields_data_types)

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
    data["imd_decile"] = deciles.calc_imd_decile(data["imd"], data["ctry"], ons_pd).astype("UInt8")

    # Set correct types
    data[cols_bool] = data[cols_bool].astype(bool)
    data[cols_int_16] = data[cols_int_16].astype("Int16")
    data[cols_int_32] = data[cols_int_32].astype("Int32")
    data[cols_categorical] = data[cols_categorical].astype("category")

    # Fix ONS errors (https://github.com/mysociety/mapit/issues/341)
    data["osward"] = data["osward"].replace("E05006336", "E05012387")

    # Tidy categories
    for field, dtype in data.dtypes.items():
        if str(dtype) == "category":
            data[field] = data[field].cat.remove_unused_categories()

    return data


def save_merged_data(data: pd.DataFrame, ons_pd_publication_date: str) -> None:
    """Save passed dataframe to csv file.

    Also output list of errors in the merge process to a text file

    Args:
        data: Census data
        ons_pd_publication_date: Refers to the ONS Postcode Directory's publication date

    """
    raw_extract_path = config.SETTINGS.census_extract.original
    output_path = raw_extract_path.parent / f"{raw_extract_path.stem} with {ons_pd_publication_date} fields-new"
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
    # Turn on logging
    set_up_logger()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime())}")
    start_time = time.time()

    # load raw census extract
    dtypes = {key: "bool" for key in cols_bool} | {key: "Int16" for key in cols_int_16} | {key: "Int32" for key in cols_int_32} | {key: "category" for key in cols_categorical}
    census_data = pd.read_csv(config.SETTINGS.census_extract.original, dtype=dtypes, encoding="utf-8")

    # combine all youth membership columns into a single total
    for section_name, section_model in scout_census.column_labels.sections:
        census_data[f"{section_name}_total"] = census_data[section_model.youth_cols].sum(axis=1).astype("Int16")

    # backticks (`) break folium's output as it uses ES2015 template literals in the output file.
    census_data[scout_census.column_labels.name.ITEM] = census_data[scout_census.column_labels.name.ITEM].str.replace("`", "")
    # TODO can we remove this?

    # merge the census extract and ONS postcode directory, and save the data to file
    merged_data = merge_ons_postcode_directory(census_data, ons_postcode_directory_may_19)
    save_merged_data(merged_data, ons_postcode_directory_may_19.PUBLICATION_DATE)

    logger.info(f"Script finished, {time.time() - start_time:.2f} seconds elapsed.")
