from src.ONS_data import ONSPostcodeDirectory


class ONSPostcodeDirectoryMay19(ONSPostcodeDirectory):
    """Used for holding and accessing ONS Postcode Directory data

    :param str ons_pd_csv_path: path to the ONS Postcode Directory csv file
    :param bool load_data: whether to load data from the file

    :var list ONSPostcodeDirectoryMay19.fields: columns to read from the csv file
    :var str ONSPostcodeDirectoryMay19.index_column: column to use as the index. Must contain unique values
    :var dict ONSPostcodeDirectoryMay19.data_types: pandas datatypes for the columns to load
    :var str ONSPostcodeDirectoryMay19.PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
    :var dict ONSPostcodeDirectoryMay19.IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
    :var dict ONSPostcodeDirectoryMay19.COUNTRY_CODES: ONS Postcode Directory codes for each country
    """
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

    def __init__(self, ons_pd_csv_path, load_data=True):
        ONSPostcodeDirectory.__init__(self, ons_pd_csv_path, load_data, ONSPostcodeDirectoryMay19.index_column, ONSPostcodeDirectoryMay19.fields, ONSPostcodeDirectoryMay19.data_types)

        # Folder within the ONS Postcode Directory archive holding names and codes files
        self.NAMES_AND_CODES_FILE_LOCATION = self.settings["ONS Names and codes folder"]

        # Paths to all shapefiles within the Boundaries folder
        LAD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Local_Authority_Districts_April_2019_Boundaries_UK_BUC\Local_Authority_Districts_April_2019_Boundaries_UK_BUC.shp"]
        CTY_SHAPEFILE = [self.settings["Boundaries folder"] + r"Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK\Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp"]
        WARD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Wards_May_2019_Boundaries_UK_BSC\Wards_May_2019_Boundaries_UK_BSC.shp"]
        PCON_SHAPEFILE = [self.settings["Boundaries folder"] + r"Westminster_PCON_Dec_2017_Generalised_Clipped_UK\Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp"]
        LSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales\Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales.shp"]
        MSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp"]
        IZ_SHAPEFILE = [self.settings["Boundaries folder"] + r"SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp"]

        # Dictionary holding dictionaries with information for each type of boundary
        self.BOUNDARIES = {
            "lad": {
                # "friendly_name": "Local Authority District",
                "name": "oslaua",
                "codes": {"path": "LA_UA names and codes UK as at 12_19.csv", "key": "LAD19CD", "key_type": "object", "name": "LAD19NM"},
                "boundary": {"shapefiles": LAD_SHAPEFILE, "key": 'lad19cd', "name": 'lad19nm',},
                "age_profile": {"path": "lad_by_age.csv", "key": "Code"},
            },
            "cty": {
                "name": "oslaua",
                "codes": {"path": "LA_UA names and codes UK as at 12_19.csv", "key": "LAD19CD", "key_type": "object", "name": "LAD19NM"},
                "boundary": {"shapefiles": CTY_SHAPEFILE, "key": 'ctyua17cd', "name": 'ctyua17nm',},
                "age_profile": {"path": None, "key": None},
            },
            "osward": {
                "name": "osward",
                "codes": {"path": "Ward names and codes UK as at 05_19_NSPD.csv", "key": "WD19CD", "key_type": "object", "name": "WD19NM"},
                "boundary": {"shapefiles": WARD_SHAPEFILE, "key": 'wd19cd', "name": 'wd19nm',},
                "age_profile": {"path": None, "key": None},
            },
            "pcon": {
                "name": "pcon",
                "codes": {"path": "Westminster Parliamentary Constituency names and codes UK as at 12_14.csv", "key": "PCON14CD", "key_type": "object", "name": "PCON14NM"},
                "boundary": {"shapefiles": PCON_SHAPEFILE, "key": 'pcon17cd', "name": "pcon17nm",},
                "age_profile": {"path": "pcon_by_age.csv", "key": "PCON11CD"},
            },
            "lsoa": {
                "name": "lsoa11",
                "codes": {"path": "LSOA (2011) names and codes UK as at 12_12.csv", "key": "LSOA11CD", "key_type": "object", "name": "LSOA11NM"},
                "boundary": {"shapefiles": LSOA_SHAPEFILE, "key": 'lsoa11cd', "name": 'lsoa11nm',},
                "age_profile": {"path": None, "key": None},
            },
            "msoa": {
                "name": "msoa",
                "codes": {"path": "MSOA (2011) names and codes UK as at 12_12.csv", "key": "MSOA11CD", "key_type": "object","name": "MSOA11NM"},
                "boundary": {"shapefiles": MSOA_SHAPEFILE, "key": 'msoa11cd', "name": None,},
                "age_profile": {"path": None, "key": None},
            },
            "iz": {
                "name": "iz",
                "codes": {"path": None, "key": None, "key_type": "object", "name": None},
                "boundary": {"shapefiles": IZ_SHAPEFILE, "key": 'InterZone', "name": None,},
                "age_profile": {"path": None, "key": None},
            },
        }
