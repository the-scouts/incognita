"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory published in May 2018.

This script has no command line options.
"""

from src.scout_data import ScoutData
from ons_pd_may_19 import ONSPostcodeDirectoryMay19
import json

if __name__ == "__main__":
    scout_data = ScoutData(csv_has_ons_pd_data=False)

    with open("settings.json", "r") as read_file:
        settings = json.load(read_file)["settings"]
    ons_pd = ONSPostcodeDirectoryMay19(settings["ONS PD location"])
    scout_data.merge_ons_postcode_directory(ons_pd)
