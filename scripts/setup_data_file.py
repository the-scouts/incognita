"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""
from src.data.scout_census import ScoutCensus
from src.data.scout_data import ScoutData
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    scout_data = ScoutData(merged_csv=False)
    for section in ScoutCensus.column_labels["sections"].keys():
        scout_data.data[f"{section}_total"] = scout_data.data[[f"{section}_f", f"{section}_m", f"{section}_SelfIdentify", f"{section}_PreferNoToSay"]].sum(axis=1).astype("Int16")
    ons_pd = ONSPostcodeDirectoryMay19(scout_data.settings["Full ONS PD location"])
    scout_data.merge_ons_postcode_directory(ons_pd)
    scout_data.close()
