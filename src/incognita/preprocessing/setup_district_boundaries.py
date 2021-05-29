import time

import geopandas as gpd
import pandas as pd

from incognita.data.scout_census import load_census_data
from incognita.geographies import district_boundaries
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", {20})
    # Remove Jersey, Guernsey, and Isle of Man as they have invalid lat/long coordinates for their postcodes
    census_data = filter.filter_records(census_data, "C_name", {"Bailiwick of Guernsey", "Isle of Man", "Jersey"}, exclude_matching=True)

    # low resolution shape data
    world_low_res = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    uk_shape = world_low_res.loc[world_low_res.name == "United Kingdom", "geometry"].array.data[0]
    # # high resolution shape data
    # uk_shape = gpd.read_file(r"S:\Development\incognita\data\UK Shape\GBR_adm0.shp")["geometry"].array.data[0]
    logger.info("UK outline shapefile loaded.")

    district_polygons = district_boundaries.create_district_boundaries(census_data, clip_to=uk_shape)
    logger.info("District boundaries estimated!")

    location_ids = census_data[["D_ID", "C_ID", "R_ID", "X_ID"]].dropna(subset=["D_ID"]).drop_duplicates().astype("Int64")
    district_polygons = pd.merge(district_polygons, location_ids, how="left", on="D_ID")
    logger.info("Added County, Region & Country location codes.")

    district_polygons.to_file(config.SETTINGS.folders.boundaries / "districts-borders-uk.geojson", driver="GeoJSON")
    logger.info("District boundaries saved.")

    timing.close(start_time)
