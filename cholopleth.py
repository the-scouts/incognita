import pandas as pd
import folium
import geopandas
from json import dumps
import webbrowser

# WGS_84 (World Geodetic System 1984) is a system for global positioning used
# in GPS. It is used by folium to plot the data.
WGS_84 = '4326'

# ------------------------------------------------------------------------------
# Class CholorplethMapPlotter
#
# This class enables easy plotting of maps with a shape file. It makes the
# following assumptions:
#
# The inputted csv_file must have the first column 'Geo_code' and the second
# column 'Score'. The 'Geo_code' column must have values which match with the
# 'code' property of the GeoJSON (which has been converted from the shape file)
# ------------------------------------------------------------------------------

class CholoplethMapPlotter:
    def __init__(shape_file, csv_file, out_file):
        self.shape_file = shape_file
        self.csv_file = csv_file
        self.out_file = out_file

    def convert_shape_to_geojson():
        # Read a shape file
        shape_file = geopandas.GeoDataFrame.from_file(self.shape_file)
        # Covert shape file to GeoJSON
        self.geo_json = shape_file.to_crs(epsg=WGS_84).to_json()

    def plot():
        gjson = self.convert_shape_to_geojson(self.shape_file)

        # Create folium map
        map = folium.Map(location=[53.5,-1.49],zoom_start=8)

        # Read comma separated values file
        map_data = pd.read_csv(csv_file)

        # Create choropleth data
        map.choropleth(geo_data=gjson,
                     data=map_data,
                     columns=['Geo_code','Score'],
                     key_on='feature.properties.code',
                     fill_color='YlOrRd',
                     fill_opacity=0.6,
                     line_opacity=0.2,
                     legend_name='Scouting %')

        # Add layer control to map
        folium.LayerControl().add_to(map)

        # Save map as html document
        map.save(outfile)

    def show():
        webbrowser.open("file://" + self.out_file)
