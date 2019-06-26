from src.ONS_data import ONSData


class ONSDataMay19(ONSData):
    fields = ['lsoa11', 'msoa11', 'oslaua', 'osward', 'pcon', 'oscty', 'oseast1m', 'osnrth1m', 'lat', 'long', 'imd', 'ctry', 'rgn', 'pcd']
    index_column = 'pcd'
    data_types = {
        'oscty': 'category',
        'oslaua': 'category',
        'osward': 'category',
        'oseast1m': 'Int32',
        'osnrth1m': 'Int32',
        'ctry': 'category',
        'rgn': 'category',
        'pcon': 'category',
        'lsoa11': 'category',
        'msoa11': 'category',
        'lat': 'float32',
        'long': 'float32',
        'imd': 'Int32',  # should be uint16 but not atm because the NaN thing
    }  # capitalise Int as of Optional Integer NA Support pandas 24 # Int capitalised as this ignores NaNs

    # Date of ONS postcode directory
    PUBLICATION_DATE = "May 2019"

    # Highest IMD rank in each of IMD 2015, WIMD 2014, SIMD 2016, NIMDM2017
    IMD_MAX = {"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890}

    COUNTRY_CODES = {"E92000001": "England", "W92000004": "Wales", "S92000003": "Scotland", "N92000002": "Northern Ireland", }
    # "L93000001": "Channel Islands", "M83000003": "Isle of Man"

    def __init__(self, csv_data, load_data=True):
        ONSData.__init__(self, csv_data, load_data, ONSDataMay19.index_column, ONSDataMay19.fields, ONSDataMay19.data_types)

        self.NAMES_AND_CODES_FILE_LOCATION = self.settings["ONS Names and codes folder"]
        LAD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Local_Authority_Districts_December_2018_Boundaries_UK_BGC\Local_Authority_Districts_December_2018_Boundaries_UK_BGC.shp"]
        CTY_SHAPEFILE = [self.settings["Boundaries folder"] + r"Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK\Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp"]
        WARD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Wards_May_2018_Boundaries\Wards_May_2018_Boundaries.shp"]
        PCON_SHAPEFILE = [self.settings["Boundaries folder"] + r"Westminster_PCON_Dec_2017_Generalised_Clipped_UK\Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp"]
        LSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales\Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales.shp"]
        MSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp"]
        IZ_SHAPEFILE = [self.settings["Boundaries folder"] + r"SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp"]

        self.BOUNDARIES = {
            "lad": {
                # "friendly_name": "Local Authority District",
                "name": "oslaua",
                "codes": {"path": "LA_UA names and codes UK as at 12_19.csv", "key": "LAD19CD", "name": "LAD19NM"},
                "boundary": {"shapefiles": LAD_SHAPEFILE, "key": 'lad18cd', "name": 'lad18nm',},
                "age_profile": {"path": "lad_by_age.csv", "key": "Code"},
            },
            "cty": {
                "name": "oslaua",
                "codes": {"path": "LA_UA names and codes UK as at 12_19.csv", "key": "LAD19CD", "name": "LAD19NM"},
                "boundary": {"shapefiles": CTY_SHAPEFILE, "key": 'ctyua17cd', "name": 'ctyua17nm',},
                "age_profile": {"path": None, "key": None},
            },
            "osward": {
                "name": "osward",
                "codes": {"path": "Ward names and codes UK as at 05_19_NSPD.csv", "key": "WD19CD", "name": "WD19NM"},
                "boundary": {"shapefiles": WARD_SHAPEFILE, "key": 'wd18cd', "name": 'wd18nm',},
                "age_profile": {"path": None, "key": None},
            },
            "pcon": {
                "name": "pcon",
                "codes": {"path": "Westminster Parliamentary Constituency names and codes UK as at 12_14.csv", "key": "PCON14CD", "name": "PCON14NM"},
                "boundary": {"shapefiles": PCON_SHAPEFILE, "key": 'pcon17cd', "name": "pcon17nm",},
                "age_profile": {"path": "pcon_by_age.csv", "key": "PCON11CD"},
            },
            "lsoa": {
                "name": "lsoa11",
                "codes": {"path": "LSOA (2011) names and codes UK as at 12_12.csv", "key": "LSOA11CD", "name": "LSOA11NM"},
                "boundary": {"shapefiles": LSOA_SHAPEFILE, "key": 'lsoa11cd', "name": 'lsoa11nm',},
                "age_profile": {"path": None, "key": None},
            },
            "msoa": {
                "name": "msoa",
                "codes": {"path": "MSOA (2011) names and codes UK as at 12_12.csv", "key": "MSOA11CD", "name": "MSOA11NM"},
                "boundary": {"shapefiles": MSOA_SHAPEFILE, "key": 'msoa11cd', "name": None,},
                "age_profile": {"path": None, "key": None},
            },
            "iz": {
                "name": "iz",
                "codes": {"path": None, "key": None, "name": None},
                "boundary": {"shapefiles": IZ_SHAPEFILE, "key": 'InterZone', "name": None,},
                "age_profile": {"path": None, "key": None},
            },
        }
