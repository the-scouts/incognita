"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""
import json
from src.utility import SCRIPTS_ROOT
from src.data.scout_census import ScoutCensus
from src.data.scout_data import ScoutData
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    with open(SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]
        census_extract_path = settings["Raw Census Extract location"]

    scout_data = ScoutData(merged_csv=False, census_path=census_extract_path)

    for section, section_dict in ScoutCensus.column_labels["sections"].items():
        scout_data.data[f"{section}_total"] = scout_data.data[section_dict["youth_cols"]].sum(axis=1).astype("Int16")

    scout_data.data[scout_data.scout_census.column_labels["name"]["ITEM"]] = scout_data.data[scout_data.scout_census.column_labels["name"]["ITEM"]].str.replace("`", "")

    ons_pd = ONSPostcodeDirectoryMay19(scout_data.settings["Full ONS PD location"])

    #@TODO: The saving of the processed scout_data file should occur separately to the merge_ons_postcode_directory
    #function. In otherwords after e.g. in a scout_data.to_csv method, as the dual purpose of the merge method is
    #confusing.
    scout_data.merge_ons_postcode_directory(ons_pd)

    scout_data.close()
