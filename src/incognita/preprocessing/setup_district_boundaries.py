import time

import geopandas as gpd

from incognita.data.scout_census import load_census_data
from incognita.geographies import district_boundaries
from incognita.logger import logger
from incognita.utility import filter
from incognita.utility import timing

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", {20})

    # low resolution shape data
    world_low_res = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    uk_shape = world_low_res.loc[world_low_res.name == "United Kingdom", "geometry"].array.data[0]
    # # high resolution shape data
    # uk_shape = gpd.read_file(r"S:\Development\incognita\data\UK Shape\GBR_adm0.shp")["geometry"].array.data[0]
    logger.info("UK outline shapefile loaded.")

    district_polygons = district_boundaries.create_district_boundaries(census_data, clip_to=uk_shape)
    logger.info("District boundaries estimated!")

    district_polygons.to_file(f"districts-borders-uk.geojson", driver="GeoJSON")
    logger.info("District boundaries saved.")

    timing.close(start_time)
