import folium
from folium.plugins import MarkerCluster
from folium.map import FeatureGroup
import geopandas as gpd
import webbrowser
import os

from reports.reports import Reports
from src.base import Base
from geographies.geography import Geography

# WGS_84 (World Geodetic System 1984) is a system for global positioning used  in GPS.
# It is used by folium to plot the data.
WGS_84 = '4326'


class MapPlotter(Base):
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

    def __init__(self, out_file):
        super().__init__()

        self.out_file = out_file + ".html"

        # Create folium map
        self.map = folium.Map(location=[53.5, -1.49], zoom_start=6)
        self.SCORE_COL = {}
        self.layers = {}

        self.geo_data = None

    def set_boundary(self, boundary: Geography, reports: Reports):
        """
        Changes the boundary to a new boundary

        :param Geography boundary: contains details about the new boundary
        """
        self.code_name = boundary.shapefile_key

        self.map_data = reports.data
        self.CODE_COL = reports.ons_column_name
        self._filter_shape_file(boundary.shapefile)

        self.logger.info(f"Geography changed to: {self.CODE_COL} ({self.code_name}). Data has columns {self.map_data.columns}.")

    def set_score_col(self, dimension, boundary):
        """
        Sets the SCORE_COL to use for a particular boundary

        :param dict dimension: specifies the score column to use int the data
        :param Geography boundary: specifies the geography to use
        """
        shapefile_name_column = boundary.shapefile_name_column

        self.SCORE_COL[shapefile_name_column] = dimension["column"]
        self.score_col_label = dimension["tooltip"]
        self.logger.info(f"Setting score column to {self.SCORE_COL[shapefile_name_column]} (displayed: {self.score_col_label})")

    def add_layer(self, name, markers_clustered=False, show=True):
        """
        Adds a maker layer to the map

        :param str name: The name of the layer - appears in LayerControl on Map
        :param bool markers_clustered: Whether the markers should cluster or not
        """
        if markers_clustered:
            self.layers[name] = MarkerCluster(name=name, show=show).add_to(self.map)
        else:
            self.layers[name] = FeatureGroup(name=name, show=show).add_to(self.map)

    def _filter_shape_file(self, shape_file_path):
        """Loads, filters and converts shapefiles for later use

        Loads shapefile from path into GeoPandas dataframe
        Filters out unneeded shapes within all shapes loaded
        Converts from British National Grid to WGS84, as Leaflet doesn't understand BNG

        :param str shape_file_path: path to ESRI shapefile with region information
        :return: None
        """

        # Read a shape file
        all_shapes = gpd.GeoDataFrame.from_file(shape_file_path)

        original_number_of_shapes = len(all_shapes.index)
        self.logger.info(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in the {self.CODE_COL} of the map_data")
        self.logger.debug(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in \n{self.map_data[self.CODE_COL]}")

        list_codes = [str(code) for code in self.map_data[self.CODE_COL].tolist()]
        all_shapes = all_shapes[all_shapes[self.code_name].isin(list_codes)]
        self.logger.info(f"Resulting in {len(all_shapes.index)} shapes")

        # Covert shape file to world co-ordinates
        self.geo_data = all_shapes.to_crs({'init': f"epsg:{WGS_84}"})
        # self.logger.debug(f"geo_data\n{self.geo_data}")

    def add_areas(self, name, show, boundary_name, colourmap):
        """Adds features from self.geo_data to map

        :param str name: the name of the Layer, as it will appear in the layer controls
        :param bool show: whether to show the layer by default
        :param str boundary_name: column heading for human-readable region name
        :param colourmap: branca colour map object
        :return: None
        """
        self.logger.info(f"Merging geo_json on {self.code_name} from shapefile with {self.CODE_COL} from boundary report")
        merged_data = self.geo_data.merge(self.map_data, left_on=self.code_name, right_on=self.CODE_COL)
        self.logger.debug(f"Merged_data\n{merged_data}")
        if len(merged_data.index) == 0:
            self.logger.error("Data unsuccesfully merged resulting in zero records")
            raise Exception("Data unsuccesfully merged resulting in zero records")

        folium.GeoJson(
            data=merged_data.to_json(),
            name=name,
            style_function=lambda x: {
               'fillColor': self._map_colourmap(x['properties'], colourmap, boundary_name),
               'color': 'black',
               'fillOpacity': 0.33,
               'weight': 0.5
            },
            tooltip=folium.GeoJsonTooltip(
               fields=[boundary_name, self.SCORE_COL[boundary_name]],
               aliases=['Name', self.score_col_label],
               localize=True
            ),
            show=show
        ).add_to(self.map)
        colourmap.add_to(self.map)

    def _map_colourmap(self, properties, colourmap, boundary_name):
        """Returns colour from colour map function and value

        :param properties: dictionary of properties
        :param colourmap: a Branca Colormap object to calculate the region's colour
        :return str: hexadecimal colour value "#RRGGBB"
        """
        self.logger.debug(f"Colouring {properties} by {self.SCORE_COL[boundary_name]}")
        area_score = properties.get(self.SCORE_COL[boundary_name])
        if area_score is None:
            self.logger.debug("Colouring gray")
            return '#cccccc'
        elif float(area_score) == 0:
            return '#555555'
        else:
            return colourmap(area_score)

    def add_marker(self, lat, long, popup, colour, layer_name='Sections'):
        """Adds a leaflet marker to the map using given values

        :param float lat: latitude of the marker
        :param float long: longitude of the marker
        :param folium.Popup popup: popup text for the marker
        :param string colour: colour for the marker
        :param string layer_name: name of the layer that markers are added to
        :return: None
        """
        folium.Marker(
            location=[lat, long],
            popup=popup,
            icon=folium.Icon(color=colour)
        ).add_to(self.layers[layer_name])

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
