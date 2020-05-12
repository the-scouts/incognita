"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""
import json
from src.utility import SCRIPTS_ROOT, DATA_ROOT
from src.data.scout_census import ScoutCensus
from src.data.scout_data import ScoutData
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    column_labels = ScoutCensus.column_labels

    # get census extract path
    with open(SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]
        census_extract_path = settings["Raw Census Extract location"]

    # load census extract
    scout_data = ScoutData(merged_csv=False, census_path=census_extract_path)

    # combine all youth membership columns into a single total
    for section, section_dict in column_labels["sections"].items():
        scout_data.data[f"{section}_total"] = scout_data.data[section_dict["youth_cols"]].sum(axis=1).astype("Int16")

    # backticks (`) break folium's output as it uses ES2015 template literals in the output file.
    scout_data.data[column_labels["name"]["ITEM"]] = scout_data.data[column_labels["name"]["ITEM"]].str.replace("`", "")

    # load ONS postcode directory
    ons_pd = ONSPostcodeDirectoryMay19(DATA_ROOT / scout_data.settings["Full ONS PD location"])

    # merge the census extract and ONS postcode directory, and save the data to file
    scout_data.merge_ons_postcode_directory(ons_pd)
    scout_data.save_merged_data(ons_pd)

    scout_data.close()
