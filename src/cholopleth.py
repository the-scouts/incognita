import pandas as pd
import folium
from folium.plugins import MarkerCluster
import geopandas
import webbrowser
import branca
import os
import numpy as np
import logging

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
    def __init__(self, shape_files, data_info, out_file, color, scale, legend_label):
        self.logger = logging.getLogger(__name__)

        # define a Handler which writes INFO messages or higher to the sys.stderr
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(fmt="%(name)s - %(levelname)s - %(message)s"))

        # add the handler to the root logger
        self.logger.addHandler(console)

        self.out_file = out_file + ".html"
        self.code_name = shape_files["key"]
        self.map_data = data_info['data']
        self.color = color
        self.scale = scale
        self.legend_label = legend_label
        self.CODE_COL = data_info['code_col']
        self.SCORE_COL = data_info['score_col']
        self.display_score_col = data_info['display_score_col']
        # Create folium map
        self.map = folium.Map(location=[53.5,-1.49],zoom_start=6)

        self.marker_cluster = MarkerCluster(name='Sections').add_to(self.map)
        self.shape_files = shape_files["shapefiles"]
        self.update_shape_file(self.shape_files)

    def update_shape_file(self, shape_files):
        # Read a shape file
        data_frames = []
        for shape in shape_files:
            data_frames.append(geopandas.GeoDataFrame.from_file(shape))

        all_shapes = pd.concat(data_frames,sort=False)
        original_number_of_shapes = len(all_shapes.index)
        self.logger.info(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in the {self.CODE_COL} of the map_data")
        self.logger.debug(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in \n{self.map_data[self.CODE_COL]}")
        list_codes = [str(code) for code in self.map_data[self.CODE_COL].tolist()]
        all_shapes = all_shapes[all_shapes[self.code_name].isin(list_codes)]
        self.logger.info(f"Resulting in {len(all_shapes.index)} shapes")

        # Covert shape file to world co-ordinates
        self.geo_json = all_shapes.to_crs({'init':'epsg:'+str(WGS_84)})
        self.logger.debug(f"geo_json\n{self.geo_json}")

    def update_data(self, data_info):
        self.map_data = data_info['data']
        self.CODE_COL = data_info['code_col']
        self.SCORE_COL = data_info['score_col']
        self.update_shape_file(self.shape_files)

    def update_score_col(self, score_col):
        self.SCORE_COL = score_col

    def set_colormap(self, colormap):
        self.colormap = colormap

    def plot(self, name, show, boundary_name, colormap):
        self.logger.debug(f"Merging geo_json on {self.code_name} with {self.CODE_COL} from boundary report")
        merged_data = self.geo_json.merge(self.map_data, left_on=self.code_name,right_on=self.CODE_COL)
        self.logger.debug(f"Merged_data\n{merged_data}")

        folium.GeoJson(merged_data.to_json(),
                       name=name,
                       style_function=lambda x: {'fillColor':self.my_colormap(x['properties'], colormap), 'color':'black','fillOpacity':0.4, 'weight':0.2},
                       tooltip=folium.GeoJsonTooltip(fields=[boundary_name ,self.SCORE_COL], aliases=['Name', self.display_score_col], localize=True),
                       show=show).add_to(self.map)
        colormap.add_to(self.map)

    def my_colormap(self, properties, colormap):
        area_score = properties[self.SCORE_COL]
        if area_score is None:
            return '#cccccc'
        elif float(area_score) == 0:
            return '#555555'
        else:
            return colormap(area_score)

    def add_marker(self, lat, long, popup, color):
        # folium.Marker(
        #    location=[lat, long],
        #    popup=popup,
        #    icon=folium.Icon(color=color)
        # ).add_to(self.marker_cluster)
        folium.Marker(
            location=[lat, long],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(self.map)

    def save(self):
        # Add layer control to map
        folium.LayerControl(collapsed=False).add_to(self.map)
        self.map.save(self.out_file)

    def show(self):
        webbrowser.open("file://" + os.path.realpath(self.out_file))
