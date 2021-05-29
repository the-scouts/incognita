import geopandas as gpd
import pandas as pd

from incognita.data.ons_pd import ONS_POSTCODE_DIRECTORY_MAY_20 as ONS_PD
from incognita.logger import logger
from incognita.logger import set_up_logger
from incognita.utility import config
from incognita.utility import constants
from incognita.utility import deciles

if __name__ == "__main__":
    set_up_logger()

    logger.info("Starting")
    to_keep = ("oscty", "oslaua", "osward", "ctry", "rgn", "pcon", "lsoa11", "msoa11", "imd", "imd_decile")  # 'lat', 'long', 'nys_districts', 'pcd'
    fields = [f for f in to_keep if f in ONS_PD.fields]

    # Load Full ONS Postcode Directory
    data = pd.read_csv(config.SETTINGS.ons_pd.full, dtype=ONS_PD.data_types, encoding="utf-8")
    logger.info("Loaded data")

    orig = data.copy()
    logger.info("DEBUG - copied original data")

    # Add IMD Decile
    data["imd_decile"] = deciles.calc_imd_decile(data["imd"], data["ctry"], ONS_PD).astype("UInt8")
    logger.info("IMD Deciles added")

    # Save minified full ONS Postcode Directory
    reduced_data_with_coords = data[fields + ["lat", "long"]].copy()
    # reduced_data_with_coords[["lat", "long"]] = reduced_data_with_coords[["lat", "long"]].round(4)  # Limit to 3dp (~100m resolution)
    reduced_data_with_coords = reduced_data_with_coords.drop_duplicates().reset_index()
    reduced_data_with_geo = gpd.GeoDataFrame(
        reduced_data_with_coords,
        geometry=gpd.points_from_xy(reduced_data_with_coords.long, reduced_data_with_coords.lat),
        crs=constants.WGS_84,
    ).drop(columns=["lat", "long"])
    del reduced_data_with_coords
    reduced_data_with_geo.to_feather(config.SETTINGS.ons_pd.minified)
    del reduced_data_with_geo
    logger.info("Minified data saved")

    # Get needed columns and delete duplicate rows
    reduced_data = data[fields].drop_duplicates().reset_index(drop=True)
    del data
    logger.info("Reduced data")

    logger.info("Saving data")
    reduced_data.to_csv(config.SETTINGS.ons_pd.reduced.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    reduced_data.to_feather(config.SETTINGS.ons_pd.reduced.with_suffix(".feather"))
    logger.info("Done")
