import json

from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19
from src.utility import SCRIPTS_ROOT

if __name__ == "__main__":
    with open(SCRIPTS_ROOT.joinpath("settings.json"), "r") as read_file:
        settings = json.load(read_file)["settings"]

    print("Starting")
    ons_pd = ONSPostcodeDirectoryMay19(settings["Full ONS PD location"], load_data=True)
    print("Loaded data")
    data = ons_pd.data.reset_index(drop=True)
    reduced_data = data[["oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "imd"]].drop_duplicates()
    del data, ons_pd
    print("Saving data")
    reduced_data.to_csv(settings["Full ONS PD location"][:-4] + f" reduced.csv", index=False, encoding="utf-8-sig")
    print("Done")
