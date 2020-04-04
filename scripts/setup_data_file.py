"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""

from src.data.scout_data import ScoutData
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    scout_data = ScoutData(csv_has_ons_pd_data=False)
    ons_pd = ONSPostcodeDirectoryMay19(scout_data.settings["ONS PD location"])
    scout_data.merge_ons_postcode_directory(ons_pd)
    scout_data.close()
