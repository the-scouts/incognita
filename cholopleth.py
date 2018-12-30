import pandas as pd
import folium
from folium.plugins import MarkerCluster
import geopandas
from json import dumps
import pandas as pd
import webbrowser
import branca.colormap as cm

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
#
# ------------------------------------------------------------------------------

class CholoplethMapPlotter:
    def __init__(self, shape_files, data, out_file, color, scale, legend_label):
        self.shape_files = shape_files[0]
        self.out_file = out_file
        self.code_name = shape_files[1]
        self.map_data = data
        self.color = color
        self.scale = scale
        self.legend_label = legend_label
        self.CODE_COL = 'Geo_code'
        self.SCORE_COL = 'Score'
        # Create folium map
        self.map = folium.Map(location=[53.5,-1.49],zoom_start=6)
        self.marker_cluster = MarkerCluster(name='Sections').add_to(self.map)

    def convert_shape_to_geojson(self):
        # Read a shape file
        data_frames = []
        for shape in self.shape_files:
            data_frames.append(geopandas.GeoDataFrame.from_file(shape))

        all_shapes = pd.concat(data_frames,sort=False)
        all_shapes = all_shapes[all_shapes[self.code_name].isin(self.map_data[self.CODE_COL])]

        # Covert shape file to GeoJSON
        self.geo_json = all_shapes.to_crs(epsg=WGS_84).to_json()

    def plot(self):
        self.convert_shape_to_geojson()

        # Create choropleth data
        folium.Choropleth(geo_data=self.geo_json,
                     data=self.map_data,
                     columns=[self.CODE_COL,self.SCORE_COL],
                     key_on='feature.properties.' + self.code_name,
                     fill_color=self.color,
                     fill_opacity=0.6,
                     line_opacity=0.2,
                     threshold_scale=self.scale,
                     legend_name=self.legend_label,
                     name='Colour Scale',
                     nan_fill_color='purple').add_to(self.map)

        # Add layer control to map
        folium.LayerControl().add_to(self.map)

        # Save map as html document
        self.save()

    def add_marker(self, lat, long, popup, color):
        folium.Marker(
            location=[lat, long],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(self.marker_cluster)

    def save(self):
        self.map.save(self.out_file)

    def show(self):
        webbrowser.open("file://" + self.out_file)
