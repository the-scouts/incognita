from src.ONS_data import ONSPostcodeDirectory


class ONSPostcodeDirectoryMay18(ONSPostcodeDirectory):
    """Used for holding and accessing ONS Postcode Directory data

    :param str ons_pd_csv_path: path to the ONS Postcode Directory csv file
    :param bool load_data: whether to load data from the file

    :var list ONSPostcodeDirectoryMay18.fields: columns to read from the csv file
    :var str ONSPostcodeDirectoryMay18.index_column: column to use as the index. Must contain unique values
    :var dict ONSPostcodeDirectoryMay18.data_types: pandas datatypes for the columns to load
    :var str ONSPostcodeDirectoryMay18.PUBLICATION_DATE: Date of publication of the ONS Postcode Directory data
    :var dict ONSPostcodeDirectoryMay18.IMD_MAX: Highest ranked Lower Level Super Output Area (or equivalent) in each country
    :var dict ONSPostcodeDirectoryMay18.COUNTRY_CODES: ONS Postcode Directory codes for each country
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
    PUBLICATION_DATE = "May 2018"

    # Highest IMD rank in each of IMD 2015, WIMD 2014, SIMD 2016, NIMDM2017
    IMD_MAX = {"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890}

    COUNTRY_CODES = {"E92000001": "England", "W92000004": "Wales", "S92000003": "Scotland", "N92000002": "Northern Ireland", }
    # "L93000001": "Channel Islands", "M83000003": "Isle of Man"

    def __init__(self, ons_pd_csv_path, load_data=True):
        ONSPostcodeDirectory.__init__(self, ons_pd_csv_path, load_data, ONSPostcodeDirectoryMay18.index_column, ONSPostcodeDirectoryMay18.fields, ONSPostcodeDirectoryMay18.data_types)

        # Folder within the ONS Postcode Directory archive holding names and codes files
        self.NAMES_AND_CODES_FILE_LOCATION = self.settings["ONS Names and codes folder"]

        # Paths to all shapefiles within the Boundaries folder
        LAD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Local_Authority_Districts_December_2018_Boundaries_UK_BGC\Local_Authority_Districts_December_2018_Boundaries_UK_BGC.shp"]
        CTY_SHAPEFILE = [self.settings["Boundaries folder"] + r"Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK\Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp"]
        WARD_SHAPEFILE = [self.settings["Boundaries folder"] + r"Wards_May_2018_Boundaries\Wards_May_2018_Boundaries.shp"]
        PCON_SHAPEFILE = [self.settings["Boundaries folder"] + r"Westminster_PCON_Dec_2017_Generalised_Clipped_UK\Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp"]
        LSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales\Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales.shp"]
        MSOA_SHAPEFILE = [self.settings["Boundaries folder"] + r"Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales\Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp"]
        IZ_SHAPEFILE = [self.settings["Boundaries folder"] + r"SG_IntermediateZoneBdry_2011\SG_IntermediateZone_Bdry_2011.shp"]

        # Dictionary holding dictionaries with information for each type of boundary
        self.BOUNDARIES = {
            "lad": {
                "name": "oslaua",
                "codes": {"path": "LA_UA names and codes UK as at 12_18.csv", "key": "LAD18CD"},
                # "codes": "LA_UA names and codes UK as at 12_18.csv", "code_col_name": "LAD18CD",
                "boundary": {"shapefiles": LAD_SHAPEFILE, "key": 'lad18cd', "name": 'lad18nm',},
                "age_profile": {"path": "lad_by_age.csv", "key": "Code"},
                # "age_profile": "lad_by_age.csv", "age_profile_code_col": "Code",
            },
            "cty": {
                "name": "oslaua",
                "codes": "LA_UA names and codes UK as at 12_18.csv", "code_col_name": "LAD18CD",
                "boundary": {"shapefiles": CTY_SHAPEFILE, "key": 'ctyua17cd', "name": 'ctyua17nm',},
                "age_profile": None, "age_profile_code_col": None,
            },
            "osward": {
                "name": "osward",
                "codes": 'Ward names and codes UK as at 05_18.csv', "code_col_name": "WD18CD",
                "boundary": {"shapefiles": WARD_SHAPEFILE, "key": 'wd18cd', "name": 'wd18nm',},
                "age_profile": None, "age_profile_code_col": None,
            },
            "pcon": {
                "name": "pcon",
                "codes": 'Westminster Parliamentary Constituency names and codes UK as at 12_14.csv', "code_col_name": None,
                "boundary": {"shapefiles": PCON_SHAPEFILE, "key": 'pcon17cd',},
                "age_profile": None, "age_profile_code_col": None,
            },
            "lsoa": {
                "name": "lsoa11",
                "codes": 'LSOA (2011) names and codes UK as at 12_12.csv', "code_col_name": "LSOA11CD",
                "boundary": {"shapefiles": LSOA_SHAPEFILE, "key": 'lsoa11cd', "name": 'lsoa11nm',},
                "age_profile": None, "age_profile_code_col": None,
            },
            "msoa": {
                "name": "msoa",
                "codes": 'MSOA (2011) names and codes UK as at 12_12.csv', "code_col_name": None,
                "boundary": {"shapefiles": MSOA_SHAPEFILE, "key": 'msoa11cd',},
                "age_profile": None, "age_profile_code_col": None,
            },
            "iz": {
                "name": "iz",
                "codes": None, "code_col_name": None,
                "boundary": {"shapefiles": IZ_SHAPEFILE, "key": 'InterZone',},
                "age_profile": None, "age_profile_code_col": None,
            },
        }
