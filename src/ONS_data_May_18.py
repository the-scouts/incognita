import pandas as pd
from geo_scout.ONS_data import ONSData

class ONSDataMay18(ONSData):
    def __init__(self, csv_data):
        ONSData.__init__(self, csv_data)
        self.PUBLICATION_DATE = "May 2018"

        self.IMD_MAX = {}
        self.IMD_MAX["England"] = 32844
        self.IMD_MAX["Wales"] = 1909
        self.IMD_MAX["Scotland"] = 6976
        self.IMD_MAX["Northern Ireland"] = 890

        self.COUNTRY_CODES = {}
        self.COUNTRY_CODES["E92000001"] = "England"
        self.COUNTRY_CODES["W92000004"] = "Wales"
        self.COUNTRY_CODES["S92000003"] = "Scotland"
        self.COUNTRY_CODES["N92000002"] = "Northern Ireland"
        #self.COUNTRY_CODES["L93000001"] = "Channel Islands"
        #self.COUNTRY_CODES["M83000003"] = "Isle of Man"

        self.NAMES_AND_CODES_FILE_LOCATION = self.settings["ONS Names and codes folder"]
        PCON_SHAPEFILE = [self.settings["Boundaries folder"] + r"Westminster_PCON_Dec_2017_Generalised_Clipped_UK\Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp"]
        LAD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Local_Authority_Districts_December_2018_Boundaries_UK_BGC\Local_Authority_Districts_December_2018_Boundaries_UK_BGC.shp"]
        CTY_SHAPEFILE = [self.settings["Boundaries folder"] + r"Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK\Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp"]
        MSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp"]
        IZ_SHAPEFILE = [self.settings["Boundaries folder"] + r"SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp"]
        WARD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Wards_May_2018_Boundaries\Wards_May_2018_Boundaries.shp"]
        LSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales\Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales.shp"]

        LAD_SHAPE = {"shapefiles": LAD_SHAPEFILE, "key": 'lad18cd', "name": 'lad18nm'}
        CTY_SHAPE = {"shapefiles": CTY_SHAPEFILE, "key": 'ctyua17cd', "name": 'ctyua17nm'}
        PCON_SHAPE = {"shapefiles": PCON_SHAPEFILE, "key": 'pcon17cd'}
        MSOA_SHAPE = {"shapefiles": MSOA_SHAPEFILE, "key": 'msoa11cd'}
        OSWARD_SHAPE = {"shapefiles": WARD_SHAPEFILE, "key": 'wd18cd', "name": 'wd18nm'}
        IZ_SHAPE = {"shapefiles": IZ_SHAPEFILE, "key": 'InterZone'}
        LSOA_SHAPE = {"shapefiles": LSOA_SHAPEFILE, "key": 'lsoa11cd', "name": 'lsoa11nm'}

        LAD = {"name": "oslaua", "codes": "LA_UA names and codes UK as at 12_18.csv", "code_col_name": "LAD18CD", "boundary": LAD_SHAPE, "age_profile": "lad_by_age.csv", "age_profile_code_col": "Code"}
        PCON = {"name": "pcon","codes": 'Westminster Parliamentary Constituency names and codes UK as at 12_14.csv', "boundary": PCON_SHAPE, "age_profile": None, "age_profile_code_col": None}
        OSWARD = {"name": "osward","codes": 'Ward names and codes UK as at 05_18.csv', "code_col_name":"WD18CD", "boundary": OSWARD_SHAPE, "age_profile": None, "age_profile_code_col": None}
        CTY = {"name": "oslaua", "codes": "LA_UA names and codes UK as at 12_18.csv", "code_col_name": "LAD18CD", "boundary": CTY_SHAPE, "age_profile": None, "age_profile_code_col": None}
        MSOA = {"name": "msoa","codes": 'MSOA (2011) names and codes UK as at 12_12.csv', "boundary": MSOA_SHAPE, "age_profile": None, "age_profile_code_col": None}
        IZ = {"name": "iz","codes": None, "boundary": IZ_SHAPE, "age_profile": None, "age_profile_code_col": None}
        LSOA = {"name": "lsoa11","codes": 'LSOA (2011) names and codes UK as at 12_12.csv', "code_col_name": "LSOA11CD", "boundary": LSOA_SHAPE, "age_profile": None, "age_profile_code_col": None}

        self.BOUNDARIES = {
        "lad" : LAD,
        "pcon": PCON,
        "osward": OSWARD,
        "msoa": MSOA,
        "iz": IZ,
        "lsoa": LSOA,
        "cty": CTY
        }

        self.fields = ['lsoa11','msoa11','oslaua','osward','pcon','oscty','oseast1m','osnrth1m','lat','long','imd','ctry','rgn']
