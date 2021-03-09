import json

import pandas as pd
import geopandas as gpd

import src.utility as utility
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    print("Starting")
    fields = ["oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "imd", "imd_decile"]
    with open(utility.SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]

    ons_pd_location = utility.DATA_ROOT / settings["Full ONS PD location"]

    # Load Full ONS Postcode Directory

    data = pd.read_csv(ons_pd_location, dtype=ONSPostcodeDirectoryMay19.data_types, encoding="utf-8")
    print("Loaded data")

    # Add IMD Decile
    ons_pd = ONSPostcodeDirectoryMay19("", load_data=False)
    data["imd_decile"] = utility.calc_imd_decile(data["imd"], data["ctry"], ons_pd).astype("UInt8")
    del ons_pd
    print("IMD Deciles added")

    # Save minified full ONS Postcode Directory
    reduced_data_with_lat_long = data[fields + ["lat", "long"]].drop_duplicates().reset_index()
    geo_column = gpd.points_from_xy(reduced_data_with_lat_long.long, reduced_data_with_lat_long.lat)
    reduced_data_with_geo = gpd.GeoDataFrame(reduced_data_with_lat_long, geometry=geo_column)
    del reduced_data_with_lat_long, geo_column
    reduced_data_with_geo = reduced_data_with_geo.drop("lat").drop("long")
    reduced_data_with_geo.crs = utility.WGS_84
    reduced_data_with_geo.to_feather(ons_pd_location.parent / f"{ons_pd_location.stem}-minified.feather")
    del reduced_data_with_geo
    print("Minified data saved")

    # Get needed columns and delete duplicate rows
    reduced_data = data[fields].drop_duplicates()
    del data
    print("Reduced data")

    print("Saving data")
    reduced_data.to_csv(ons_pd_location.parent / f"{ons_pd_location.stem} reduced.csv", index=False, encoding="utf-8-sig")
    print("Done")
