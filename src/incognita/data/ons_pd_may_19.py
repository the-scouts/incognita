from incognita.data.ons_pd import ONSPostcodeDirectory
from incognita.utility import config

ons_postcode_directory_may_19 = ONSPostcodeDirectory(
    fields={"lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "lat", "long", "imd", "ctry", "rgn", "pcd", "imd_decile", "nys_districts"},
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
    PUBLICATION_DATE="May 2019",
    IMD_MAX={"England": 32844, "Wales": 1909, "Scotland": 6976, "Northern Ireland": 890},
    COUNTRY_CODES={
        "E92000001": "England",
        "W92000004": "Wales",
        "S92000003": "Scotland",
        "N92000002": "Northern Ireland",
        # "L93000001": "Channel Islands",
        # "M83000003": "Isle of Man"
    },
    BOUNDARIES=config.SETTINGS.ons2019,
)
