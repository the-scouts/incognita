import random
import time

import geopandas as gpd
import matplotlib.cm
from matplotlib.colors import rgb2hex

from incognita.data.scout_census import load_census_data
from incognita.logger import logger
from incognita.utility import config
from incognita.utility import filter

if __name__ == "__main__":
    start_time = time.time()
    logger.info(f"Starting at {time.strftime('%H:%M:%S', time.localtime(start_time))}")

    county_name = "Central Yorkshire"

    census_data = load_census_data()
    census_data = filter.filter_records(census_data, "Census_ID", {20})
    county_id = census_data.loc[census_data["C_name"] == county_name, "C_ID"].array[0]

    gdf = gpd.read_file(config.SETTINGS.folders.boundaries / "districts-borders-uk.geojson")
    gdf = gdf[gdf["C_ID"] == county_id].copy()

    # https://matplotlib.org/stable/tutorials/colors/colormaps.html
    # cmap = matplotlib.cm.get_cmap('Set1')
    cmap = matplotlib.cm.get_cmap("tab20")
    # cmap = matplotlib.cm.get_cmap('hsv')

    cmap_indicies = (i / (len(gdf.index) - 1) for i in range(len(gdf.index)))  # qualitative colours
    # cmap_indicies = (random.random() for _ in range(len(gdf.index)))  # qualitative colours

    gdf["fill"] = [rgb2hex(cmap(i)) for i in cmap_indicies]
    gdf["stroke-width"] = 0.2

    sanitised_county = county_name.lower().replace(" ", "-")
    gdf.to_file(f"districts-{sanitised_county}.geojson", driver="GeoJSON")
    # geojson.io recognises colours in the format above
