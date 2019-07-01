import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium.map import FeatureGroup
import geopandas
import webbrowser
import os
import src.log_util as log_util

# WGS_84 (World Geodetic System 1984) is a system for global positioning used  in GPS.
# It is used by folium to plot the data.
WGS_84 = '4326'


class ChoroplethMapPlotter:
    """This class enables easy plotting of maps with a shape file.

    :param dict shape_files_dict: dictionary of properties about the needed shapefiles
    :param data_info: dictionary of information about the data and colourings on the map
    :param str out_file: path to save the map to
    :param bool sections_clustered: If True, section markers cluster on the map.

    :var dictionary self.map_data: contains shapefile paths, and labels for region codes and names
    :var str self.CODE_COL: holds the name of the region class, e.g. oslaua, pcon
    :var self.SCORE_COL: holds the column name of the choropleth dimension
    :var self.score_col_label: tooltip label for the self.SCORE_COL value
    :var self.map: holds the folium map object
    """

    def __init__(self, shape_files_dict, data_info, out_file, sections_clustered=False):
        # Facilitates logging
        self.logger = log_util.create_logger(__name__,)

        self.out_file = out_file + ".html"
        self.code_name = shape_files_dict["key"]
        self.logger.info(f"Creating map of {data_info['code_col']}s against {data_info['score_col']} using the following data\n{data_info['data']}")
        self.map_data = data_info['data']
        self.CODE_COL = data_info['code_col']
        self.SCORE_COL = data_info['score_col']
        self.score_col_label = data_info["score_col_label"]

        # Create folium map
        self.map = folium.Map(location=[53.5, -1.49], zoom_start=6)

        if sections_clustered:
            self.section_layer = MarkerCluster(name='Sections').add_to(self.map)
        else:
            self.section_layer = FeatureGroup(name='Sections').add_to(self.map)

        self.shape_file_paths = shape_files_dict["shapefiles"]
        self.geo_data = None

        self.filter_shape_file(self.shape_file_paths)

    def filter_shape_file(self, shape_file_paths):
        """Loads, filters and converts shapefiles for later use

        Loads shapefiles from paths into GeoPandas dataframe
        Filters out unneeded shapes within all shapes loaded
        Converts from British National Grid to WGS84, as Leaflet doesn't understand BNG

        :param list shape_file_paths: list of paths to ESRI shapefile files with region information
        :return: None
        """

        # Read a shape file
        data_frames = []
        for shape_file_path in shape_file_paths:
            data_frames.append(geopandas.GeoDataFrame.from_file(shape_file_path))

        all_shapes = pd.concat(data_frames, sort=False)

        original_number_of_shapes = len(all_shapes.index)
        self.logger.info(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in the {self.CODE_COL} of the map_data")
        self.logger.debug(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in \n{self.map_data[self.CODE_COL]}")

        list_codes = [str(code) for code in self.map_data[self.CODE_COL].tolist()]
        all_shapes = all_shapes[all_shapes[self.code_name].isin(list_codes)]
        self.logger.info(f"Resulting in {len(all_shapes.index)} shapes")

        # Covert shape file to world co-ordinates
        self.geo_data = all_shapes.to_crs({'init': f"epsg:{WGS_84}"})
        # self.logger.debug(f"geo_data\n{self.geo_data}")

    def plot(self, name, show, boundary_name, colormap):
        """Adds features from self.geo_data to map

        :param str name: the name of the Layer, as it will appear in the layer controls
        :param bool show: whether to show the layer by default
        :param str boundary_name: column heading for human-readable region name
        :param colormap: branca colour map object
        :return: None
        """
        self.logger.debug(f"Merging geo_json on {self.code_name} with {self.CODE_COL} from boundary report")
        merged_data = self.geo_data.merge(self.map_data, left_on=self.code_name, right_on=self.CODE_COL)
        self.logger.debug(f"Merged_data\n{merged_data}")
        if len(merged_data.index) == 0:
            self.logger.error("Data unsuccesfully merged resulting in zero records")
            raise Exception("Data unsuccesfully merged resulting in zero records")

        folium.GeoJson(
            data=merged_data.to_json(),
            name=name,
            style_function=lambda x: {
               'fillColor': self.my_colormap(x['properties'], colormap),
               'color': 'black',
               'fillOpacity': 0.4,
               'weight': 0.2
            },
            tooltip=folium.GeoJsonTooltip(
               fields=[boundary_name, self.SCORE_COL],
               aliases=['Name', self.score_col_label],
               localize=True
            ),
            show=show
        ).add_to(self.map)
        colormap.add_to(self.map)

    def my_colormap(self, properties, colormap):
        """Returns colour from colour map function and value

        :param properties: dictionary of properties
        :param colormap: a Branca Colormap object to calculate the region's colour
        :return str: hexadecimal colour value "#RRGGBB"
        """
        area_score = properties[self.SCORE_COL]
        if area_score is None:
            return '#cccccc'
        elif float(area_score) == 0:
            return '#555555'
        else:
            return colormap(area_score)

    def add_marker(self, lat, long, popup, color):
        """Adds a leaflet marker to the map using given values

        :param float lat: latitude of the marker
        :param float long: longitude of the marker
        :param folium.Popup popup: popup text for the marker
        :param string color: colour for the marker
        :return: None
        """
        folium.Marker(
            location=[lat, long],
            popup=popup,
            icon=folium.Icon(color=color)
        ).add_to(self.section_layer)

    def set_bounds(self, bounds):
        self.map.fit_bounds(bounds)

    def save(self):
        """Saves the folium map to a HTML file """
        # Add layer control to map
        folium.LayerControl(collapsed=False).add_to(self.map)
        self.map.save(self.out_file)

    def show(self):
        """Show the file at self.out_file in the default browser. """
        webbrowser.open("file://" + os.path.realpath(self.out_file))
