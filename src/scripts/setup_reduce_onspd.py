from data.ons_pd_may_19 import ONSPostcodeDirectoryMay19

print("starting")
ons_pd = ONSPostcodeDirectoryMay19("../../data/ONSPD_MAY_2019_UK/Data/ONSPD_MAY_2019_UK.csv", load_data=True)
a = ons_pd.data
b = a.reset_index(drop=True)
c = b[['oscty', 'oslaua', 'osward', 'ctry', 'rgn', 'pcon', 'lsoa11', 'msoa11', 'imd']].drop_duplicates()
c.to_csv("ONSPD_reduced_no_postcodes_or_co_ordinates.csv", index=False, encoding='utf-8-sig')
