import pydantic


class ONSPostcodeDirectory(pydantic.BaseModel):
    """Used for holding and accessing ONS Postcode Directory data."""

    fields: set[str]  # columns to read from the full csv file
    index_column: str  # column to use as the index when merging. Must contain unique values
    data_types: dict[str, str]  # pandas data types for the columns to load

    PUBLICATION_DATE: str  # ONS Postcode Directory Publication date
    # IMD_MAX: DeprivationMaximums  # Highest IMD rank in each of IMD 2015, WIMD 2014, SIMD 2016, NIMDM2017
    IMD_MAX: dict[str, int]  # Highest ranked Lower Level Super Output Area (or equivalent) in each country
    COUNTRY_CODES: dict[str, str]  # ONS Postcode Directory codes for each country


# https://geoportal.statistics.gov.uk/datasets/ons-postcode-directory-may-2020
ONS_POSTCODE_DIRECTORY_MAY_20 = ONSPostcodeDirectory(
    fields={"lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "lat", "long", "imd", "ctry", "rgn", "pcd", "imd_decile"},
    index_column="pcd",
    data_types={
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
    },  # Int capitalised as this ignores NaNs
    PUBLICATION_DATE="May 2020",
    IMD_MAX={"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890},  # User Guide p. 45
    COUNTRY_CODES={  # User Guide p. 34
        "E92000001": "England",
        "W92000004": "Wales",
        "S92000003": "Scotland",
        "N92000002": "Northern Ireland",
        # "L93000001": "Channel Islands",
        # "M83000003": "Isle of Man"
    },
)
