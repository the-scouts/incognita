from incognita.data.ons_pd import ONSPostcodeDirectory
from incognita.data.ons_pd import Boundary
from incognita.data.ons_pd import BoundaryAgeProfile
from incognita.data.ons_pd import BoundaryCodes
from incognita.data.ons_pd import BoundaryShapeFile
from incognita.utility import config


ons_postcode_directory_may_19 = ONSPostcodeDirectory(
    fields=["lsoa11", "msoa11", "oslaua", "osward", "pcon", "oscty", "lat", "long", "imd", "ctry", "rgn", "pcd", "imd_decile", "nys_districts"],
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
    BOUNDARIES={
        "lad": Boundary(
            # Local Authority Districts
            name="oslaua",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "LA_UA names and codes UK as at 12_19.csv",
                key="LAD19CD",
                key_type="string",
                name="LAD19NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "Local_Authority_Districts__December_2019__Boundaries_UK_BUC/Local_Authority_Districts__December_2019__Boundaries_UK_BUC.shp",
                key="lad19cd",
                name="lad19nm",
            ),
            age_profile=BoundaryAgeProfile(
                path="lad_by_age.csv",
                key="Code",
            ),
        ),
        "cty": Boundary(
            # Counties
            name="oslaua",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "LA_UA names and codes UK as at 12_19.csv",
                key="LAD19CD",
                key_type="string",
                name="LAD19NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK/Counties_and_Unitary_Authorities_December_2017_Generalised_Clipped_Boundaries_in_UK.shp",
                key="ctyua17cd",
                name="ctyua17nm",
            ),
        ),
        "osward": Boundary(
            # Council Wards
            name="osward",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "Ward names and codes UK as at 05_19_NSPD.csv",
                key="WD19CD",
                key_type="string",
                name="WD19NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "Wards_December_2019_Boundaries_UK_BGC/Wards_December_2019_Boundaries_UK_BGC.shp",
                key="WD19CD",
                name="WD19NM",
            ),
            age_profile=BoundaryAgeProfile(
                path="osward_by_age_mid_2018_population_may_2019_wards.csv",
                key="Ward Code",
            ),
        ),
        "pcon": Boundary(
            # Parliamentary Constituencies
            name="pcon",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "Westminster Parliamentary Constituency names and codes UK as at 12_14.csv",
                key="PCON14CD",
                key_type="string",
                name="PCON14NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "Westminster_PCON_Dec_2017_Generalised_Clipped_UK/Westminster_Parliamentary_Constituencies_December_2017_Generalised_Clipped_Boundaries_in_the_UK.shp",
                key="pcon17cd",
                name="pcon17nm",
            ),
            age_profile=BoundaryAgeProfile(
                path="pcon_by_age.csv",
                key="PCON11CD",
            ),
        ),
        "lsoa": Boundary(
            # Lower Level Super Output Areas
            name="lsoa11",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "LSOA (2011) names and codes UK as at 12_12.csv",
                key="LSOA11CD",
                key_type="string",
                name="LSOA11NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "Lower_Layer_Super_Output_Areas_December_2011_Boundaries_EW_BSC/Lower_Layer_Super_Output_Areas_December_2011_Boundaries_EW_BSC.shp",
                key="LSOA11CD",
                name="LSOA11NM",
            ),
        ),
        "msoa": Boundary(
            # Middle Layer Super Output Areas
            name="msoa11",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "MSOA (2011) names and codes UK as at 12_12.csv",
                key="MSOA11CD",
                key_type="string",
                name="MSOA11NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales/Middle_Layer_Super_Output_Areas_December_2011_Full_Clipped_Boundaries_in_England_and_Wales.shp",
                key="msoa11cd",
                name=None,
            ),
        ),
        "iz": Boundary(
            # Intermediate Zones (codepages identical to MSOA but different shapefiles)
            name="msoa11",
            codes=BoundaryCodes(
                path=config.SETTINGS.folders.ons_pd_names_codes / "MSOA (2011) names and codes UK as at 12_12.csv",
                key="MSOA11CD",
                key_type="string",
                name="MSOA11NM",
            ),
            shapefile=BoundaryShapeFile(
                path=config.SETTINGS.folders.boundaries / "SG_IntermediateZoneBdry_2011/SG_IntermediateZone_Bdry_2011.shp",
                key="InterZone",
                name=None,
            ),
        ),
    },
)
