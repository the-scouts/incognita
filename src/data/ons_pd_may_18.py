from pathlib import Path

from src.data.ons_pd import ONSPostcodeDirectory


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

    fields = ["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "oseast1m", "osnrth1m", "lat", "long", "imd", "ctry", "rgn", "pcd"]
    index_column = "pcd"
    data_types = {
        "oscty": "category",
        "oslaua": "category",
        "osward": "category",
        "oseast1m": "Int32",
        "osnrth1m": "Int32",
        "ctry": "category",
        "rgn": "category",
        "pcon": "category",
        "lsoa11": "category",
        "msoa11": "category",
        "lat": "float32",
        "long": "float32",
        "imd": "Int32",  # should be uint16 but not atm because the NaN thing
    }  # capitalise Int as of Optional Integer NA Support pandas 24 # Int capitalised as this ignores NaNs

    # Date of ONS postcode directory
    PUBLICATION_DATE = "May 2018"

    # Highest IMD rank in each of IMD 2015, WIMD 2014, SIMD 2016, NIMDM2017
    IMD_MAX = {"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890}

    COUNTRY_CODES = {
        "E92000001": "England",
        "W92000004": "Wales",
        "S92000003": "Scotland",
        "N92000002": "Northern Ireland",
        # "L93000001": "Channel Islands",
        # "M83000003": "Isle of Man"
    }

    def __init__(self, ons_pd_csv_path, load_data=True):
        super().__init__(ons_pd_csv_path, load_data, self.index_column, self.fields, self.data_types)

        # Folder within the ONS Postcode Directory archive holding names and codes files
        names_codes_root = Path(self.settings["ONS Names and codes folder"]).resolve()

        # Paths to all shapefiles within the Boundaries folder
        # fmt: off
        shapefile_paths = {
            "LADs": "Local_Authority_Districts_December_2018_Boundaries_UK_BGC/Local_Authority_Districts_December_2018_Boundaries_UK_BGC.shp",
            "County": "Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK/Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp",
            "Ward": "Wards_May_2018_Boundaries/Wards_May_2018_Boundaries.shp",
            "PCon": "Westminster_PCON_Dec_2017_Generalised_Clipped_UK/Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp",
            "LSOA": "Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales/Lower_Layer_Super_Output_Areas_December_2011_Generalised_Clipped__Boundaries_in_England_and_Wales.shp",
            "MSOA": "Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales/Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp",
            "IZ": "SG_IntermediateZoneBdry_2011/SG_IntermediateZone_Bdry_2011.shp"
        }
        # fmt: on

        # Dictionary holding dictionaries with information for each type of boundary
        # fmt: off
        self.BOUNDARIES = {
            "lad": {
                # Local Authority Districts
                "name": "oslaua",
                "codes": {"path": names_codes_root / "LA_UA names and codes UK as at 12_18.csv", "key": "LAD18CD"},
                "boundary": {"shapefile": shapefile_paths["LADs"], "key": "lad18cd", "name": "lad18nm",},
                "age_profile": {"path": "lad_by_age.csv", "key": "Code"},
            },
            "cty": {
                # Counties
                "name": "oslaua",
                "codes": {"path": names_codes_root / "LA_UA names and codes UK as at 12_18.csv", "key": "LAD18CD"},
                "boundary": {"shapefile": shapefile_paths["County"], "key": "ctyua17cd", "name": "ctyua17nm",},
                "age_profile": {"path": None, "key": None},
            },
            "osward": {
                # Council Wards
                "name": "osward",
                "codes": {"path": names_codes_root / "Ward names and codes UK as at 05_18.csv", "key": "WD18CD"},
                "boundary": {"shapefile": shapefile_paths["Ward"], "key": "wd18cd", "name": "wd18nm",},
                "age_profile": {"path": None, "key": None},
            },
            "pcon": {
                # Parliamentary Constituencies
                "name": "pcon",
                "codes": {"path": names_codes_root / "Westminster Parliamentary Constituency names and codes UK as at 12_14.csv", "key": "None"},
                "boundary": {"shapefile": shapefile_paths["PCon"], "key": "pcon17cd",},
                "age_profile": {"path": None, "key": None},
            },
            "lsoa": {
                # Lower Level Super Output Areas
                "name": "lsoa11",
                "codes": {"path": names_codes_root / "LSOA (2011) names and codes UK as at 12_12.csv", "key": "LSOA11CD"},
                "boundary": {"shapefile": shapefile_paths["LSOA"], "key": "lsoa11cd", "name": "lsoa11nm",},
                "age_profile": {"path": None, "key": None},
            },
            "msoa": {
                # Middle Layer Super Output Areas
                "name": "msoa",
                "codes": {"path": names_codes_root / "MSOA (2011) names and codes UK as at 12_12.csv", "key": "None"},
                "boundary": {"shapefile": shapefile_paths["MSOA"], "key": "msoa11cd",},
                "age_profile": {"path": None, "key": None},
            },
            "iz": {
                # Intermediate Zones (codepages identical to MSOA but different shapefiles)
                "name": "msoa",
                "codes": {"path": names_codes_root / "MSOA (2011) names and codes UK as at 12_12.csv", "key": "None"},
                "boundary": {"shapefile": shapefile_paths["IZ"], "key": "InterZone",},
                "age_profile": {"path": None, "key": None},
            },
        }
        # fmt: on
