import pandas as pd
import folium
# from folium.plugins import MarkerCluster
import geopandas
import webbrowser
import os
import src.log_util as log_util

# WGS_84 (World Geodetic System 1984) is a system for global positioning used  in GPS.
# It is used by folium to plot the data.
WGS_84 = '4326'

# ------------------------------------------------------------------------------
# Class ChoroplethMapPlotter
#
# This class enables easy plotting of maps with a shape file. It makes the
# following assumptions:
#
# The inputted csv_file must have the first column 'Geo_code' and the second
# column 'Score'. The 'Geo_code' column must have values which match with the
# 'code' property of the GeoJSON (which has been converted from the shape file)
#
# ------------------------------------------------------------------------------


class ChoroplethMapPlotter:
    def __init__(self, shape_files, data_info, out_file):
        # Facilitates logging
        self.logger = log_util.create_logger(__name__,)

        self.out_file = out_file + ".html"
        self.code_name = shape_files["key"]

        self.map_data = data_info['data']
        self.CODE_COL = data_info['code_col']
        self.SCORE_COL = data_info['score_col']
        self.display_score_col = data_info['display_score_col']

        # Create folium map
        self.map = folium.Map(location=[53.5,-1.49],zoom_start=6)

        # self.marker_cluster = MarkerCluster(name='Sections').add_to(self.map)
        self.shape_file_paths = shape_files["shapefiles"]
        self.geo_data = None

        self.filter_shape_file(self.shape_file_paths)

    def filter_shape_file(self, shape_file_paths):
        # Load ShapeFiles
        # Convert data from National Grid easting/northing to WGS84 co-ords
        # output data to geoJSON

        # Read a shape file
        data_frames = []
        for shape_file_path in shape_file_paths:
            data_frames.append(geopandas.GeoDataFrame.from_file(shape_file_path))

        all_shapes = pd.concat(data_frames,sort=False)

        original_number_of_shapes = len(all_shapes.index)
        self.logger.info(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in the {self.CODE_COL} of the map_data")
        # self.logger.debug(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in \n{self.map_data[self.CODE_COL]}")

        list_codes = [str(code) for code in self.map_data[self.CODE_COL].tolist()]
        all_shapes = all_shapes[all_shapes[self.code_name].isin(list_codes)]
        self.logger.info(f"Resulting in {len(all_shapes.index)} shapes")

        # Covert shape file to world co-ordinates
        self.geo_data = all_shapes.to_crs({'init': f"epsg:{WGS_84}"})
        # self.logger.debug(f"geo_data\n{self.geo_data}")

    def plot(self, name, show, boundary_name, colormap):
        # self.logger.debug(f"Merging geo_json on {self.code_name} with {self.CODE_COL} from boundary report")
        merged_data = self.geo_data.merge(self.map_data, left_on=self.code_name, right_on=self.CODE_COL)
        # self.logger.debug(f"Merged_data\n{merged_data}")

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
        folium.Marker(
            location=[lat, long],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(self.map)
        # ).add_to(self.marker_cluster)

    def save(self):
        # Add layer control to map
        folium.LayerControl(collapsed=False).add_to(self.map)
        self.map.save(self.out_file)

    def show(self):
        webbrowser.open("file://" + os.path.realpath(self.out_file))
