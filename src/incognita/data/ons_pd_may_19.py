from pathlib import Path

from incognita import utility
from incognita.data.ons_pd import ONSPostcodeDirectory

# Folder within the ONS Postcode Directory archive holding names and codes files
names_codes_root = Path(utility.SETTINGS["ONS Names and codes folder"]).resolve()

# Paths to all shapefiles within the Boundaries folder
# fmt: off
shapefile_paths = {
    "LADs": "Local_Authority_Districts__December_2019__Boundaries_UK_BUC/Local_Authority_Districts__December_2019__Boundaries_UK_BUC.shp",
    "County": "Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK/Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp",
    "Ward": "Wards_December_2019_Boundaries_UK_BGC/Wards_December_2019_Boundaries_UK_BGC.shp",
    "PCon": "Westminster_PCON_Dec_2017_Generalised_Clipped_UK/Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp",
    "LSOA": "Lower_Layer_Super_Output_Areas_December_2011_Boundaries_EW_BSC/Lower_Layer_Super_Output_Areas_December_2011_Boundaries_EW_BSC.shp",
    "MSOA": "Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales/Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp",
    "IZ": "SG_IntermediateZoneBdry_2011/SG_IntermediateZone_Bdry_2011.shp",
}
# fmt: on


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

    fields = ["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "lat", "long", "imd", "ctry", "rgn", "pcd", "imd_decile", "nys_districts"]
    index_column = "pcd"
    data_types = {
        "oscty": "category",
        "oslaua": "category",
        "osward": "category",
        "ctry": "category",
        "rgn": "category",
        "pcon": "category",
        "lsoa11": "category",
        "msoa11": "category",
        "lat": "float32",
        "long": "float32",
        "imd": "UInt16",  # should be uint16 but not atm because the NaN thing
        "imd_decile": "UInt8",  # should be uint8 but not atm because the NaN thing
    }  # capitalise Int as of Optional Integer NA Support pandas 24 # Int capitalised as this ignores NaNs

    # Date of ONS postcode directory
    PUBLICATION_DATE = "May 2019"

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

    # Dictionary holding dictionaries with information for each type of boundary
    # fmt: off
    BOUNDARIES = {
        "lad": {
            # Local Authority Districts
            "name": "oslaua",
            "codes": {
                "path": names_codes_root / "LA_UA names and codes UK as at 12_19.csv",
                "key": "LAD19CD", "key_type": "string",
                "name": "LAD19NM",
            },
            "boundary": {"shapefile": shapefile_paths["LADs"], "key": "lad19cd", "name": "lad19nm", },
            "age_profile": {"path": "lad_by_age.csv", "key": "Code"},
        },
        "cty": {
            # Counties
            "name": "oslaua",
            "codes": {
                "path": names_codes_root / "LA_UA names and codes UK as at 12_19.csv",
                "key": "LAD19CD", "key_type": "string",
                "name": "LAD19NM",
            },
            "boundary": {"shapefile": shapefile_paths["County"], "key": "ctyua17cd", "name": "ctyua17nm", },
            "age_profile": {"path": None, "key": None},
        },
        "osward": {
            # Council Wards
            "name": "osward",
            "codes": {
                "path": names_codes_root / "Ward names and codes UK as at 05_19_NSPD.csv",
                "key": "WD19CD", "key_type": "string",
                "name": "WD19NM",
            },
            "boundary": {"shapefile": shapefile_paths["Ward"], "key": "WD19CD", "name": "WD19NM", },
            "age_profile": {"path": "osward_by_age_mid_2018_population_may_2019_wards.csv", "key": "Ward Code"},
        },
        "pcon": {
            # Parliamentary Constituencies
            "name": "pcon",
            "codes": {
                "path": names_codes_root / "Westminster Parliamentary Constituency names and codes UK as at 12_14.csv",
                "key": "PCON14CD", "key_type": "string",
                "name": "PCON14NM",
            },
            "boundary": {"shapefile": shapefile_paths["PCon"], "key": "pcon17cd", "name": "pcon17nm", },
            "age_profile": {"path": "pcon_by_age.csv", "key": "PCON11CD"},
        },
        "lsoa": {
            # Lower Level Super Output Areas
            "name": "lsoa11",
            "codes": {
                "path": names_codes_root / "LSOA (2011) names and codes UK as at 12_12.csv",
                "key": "LSOA11CD", "key_type": "string",
                "name": "LSOA11NM",
            },
            "boundary": {"shapefile": shapefile_paths["LSOA"], "key": "LSOA11CD", "name": "LSOA11NM", },
            "age_profile": {"path": None, "key": None},
        },
        "msoa": {
            # Middle Layer Super Output Areas
            "name": "msoa11",
            "codes": {
                "path": names_codes_root / "MSOA (2011) names and codes UK as at 12_12.csv",
                "key": "MSOA11CD", "key_type": "string",
                "name": "MSOA11NM",
            },
            "boundary": {"shapefile": shapefile_paths["MSOA"], "key": "msoa11cd", "name": None, },
            "age_profile": {"path": None, "key": None},
        },
        "iz": {
            # Intermediate Zones (codepages identical to MSOA but different shapefiles)
            "name": "msoa11",
            "codes": {
                "path": names_codes_root / "MSOA (2011) names and codes UK as at 12_12.csv",
                "key": "MSOA11CD", "key_type": "string",
                "name": "MSOA11NM",
            },
            "boundary": {"shapefile": shapefile_paths["IZ"], "key": "InterZone", "name": None, },
            "age_profile": {"path": None, "key": None},
        },
    }
    # fmt: on

    def __init__(self, ons_pd_csv_path, load_data=True):
        super().__init__(ons_pd_csv_path, load_data, self.index_column, data_types=self.data_types)
