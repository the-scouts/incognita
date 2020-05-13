import json

import src.utility as utility
from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    with open(utility.SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]
    print("Starting")

    ons_pd_location = utility.DATA_ROOT / settings["Full ONS PD location"]

    # Load Full ONS Postcode Directory
    ons_pd = ONSPostcodeDirectoryMay19(ons_pd_location, load_data=True)
    print("Loaded data")

    # Get needed columns and delete duplicate rows
    data = ons_pd.data.reset_index(drop=True)
    reduced_data = data[["oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "imd"]].drop_duplicates()
    del data
    print("Reduced data")

    # Add IMD Decile
    reduced_data["imd_decile"] = utility.calc_imd_decile(reduced_data["imd"], reduced_data["ctry"], ons_pd).astype("UInt8")
    del ons_pd
    print("IMD Deciles added")

    print("Saving data")
    reduced_data.to_csv(ons_pd_location.parent / f"{ons_pd_location.stem} reduced.csv", index=False, encoding="utf-8-sig")
    print("Done")
