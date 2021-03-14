"""Add Office for National Statistics Postcode Directory data

This script joins a .csv file with a postcode column with the ONS Postcode
Directory.

This script has no command line options.
"""
from incognita.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19
from incognita.data.scout_census import ScoutCensus
from incognita.data.scout_data import ScoutData
from incognita.utility import config

if __name__ == "__main__":
    column_labels = ScoutCensus.column_labels

    # load raw census extract
    scout_data = ScoutData(merged_csv=False, census_path=config.SETTINGS.census_extract.original)

    # combine all youth membership columns into a single total
    for section, section_dict in column_labels["sections"].items():
        scout_data.data[f"{section}_total"] = scout_data.data[section_dict["youth_cols"]].sum(axis=1).astype("Int16")

    # backticks (`) break folium's output as it uses ES2015 template literals in the output file.
    scout_data.data[column_labels["name"]["ITEM"]] = scout_data.data[column_labels["name"]["ITEM"]].str.replace("`", "")

    # load ONS postcode directory
    ons_pd = ONSPostcodeDirectoryMay19(config.SETTINGS.ons_pd.full)

    # merge the census extract and ONS postcode directory, and save the data to file
    scout_data.merge_ons_postcode_directory(ons_pd)
    scout_data.save_merged_data(ons_pd.PUBLICATION_DATE)

    scout_data.close()
