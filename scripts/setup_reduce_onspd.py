from src.data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

if __name__ == "__main__":
    print("Starting")
    ons_pd = ONSPostcodeDirectoryMay19("../data/ONSPD_MAY_2019_UK/Data/ONSPD_MAY_2019_UK.csv", load_data=True)
    print("Loaded data")
    data = ons_pd.data.reset_index(drop=True)
    reduced_data = data[["oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "imd"]].drop_duplicates()
    print("Saving data")
    reduced_data.to_csv("ONSPD_reduced_no_postcodes_or_co_ordinates.csv", index=False, encoding="utf-8-sig")
