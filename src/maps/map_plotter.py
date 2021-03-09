from __future__ import annotations
import folium
from folium.plugins import MarkerCluster
from folium.map import FeatureGroup
import geopandas as gpd
import pandas as pd
import webbrowser

from src.reports.reports import Reports
from src.base import Base
import src.utility as utility

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from branca import colormap


class MapPlotter(Base):
    """This class enables easy plotting of maps with a shape file.

    :param Path out_file: path to save the map to

    :var dictionary self.map_data: contains shapefile paths, and labels for region codes and names
    :var str self.CODE_COL: holds the name of the region class, e.g. oslaua, pcon
    :var self.SCORE_COL: holds the column name of the choropleth dimension
    :var self.score_col_label: tooltip label for the self.SCORE_COL value
    :var self.map: holds the folium map object
    """

    def __init__(self, out_file: Path):
        super().__init__()

        self.out_file: Path = out_file.with_suffix(".html").resolve()

        # Create folium map
        self.map: folium.Map = folium.Map(
            location=[53.5, -1.49],
            zoom_start=6,
            attr="Map data &copy; <a href='https://openstreetmap.org'>OpenStreetMap</a>, <a href='https://cartodb.com/attributions'>CARTO</a>",
            # tiles='OpenStreetMap',
            tiles="CartoDB positron nolabels",
            # kwargs to leaflet
            zoomSnap=0.05,
            zoomDelta=0.1,
        )
        # self.map_labels = folium.TileLayer("CartoDB positron onlylabels", overlay=True)
        self.SCORE_COL: dict = {}
        self.layers: dict = {}

        self.score_col_label: str = ""
        self.score_col_key: str = ""
        self.boundary_name: str = ""
        self.code_name: str = ""
        self.CODE_COL: str = ""
        self.map_data: pd.DataFrame = pd.DataFrame()

        self.geo_data = None

    def validate_columns(self):
        if self.SCORE_COL[self.score_col_key] not in self.map_data.columns:
            self.logger.error(f"{self.SCORE_COL[self.score_col_key]} is not a valid column in the data. \n" f"Valid columns include {self.map_data.columns}")
            raise KeyError(f"{self.SCORE_COL[self.score_col_key]} is not a valid column in the data.")

    def set_boundary(self, reports: Reports):
        """
        Changes the boundary to a new boundary

        :param reports:
        """

        self.map_data = reports.data
        self.boundary_name = reports.shapefile_name
        self.code_name = reports.shapefile_key
        self.CODE_COL = reports.geography_type

        # map_data, CODE_COL and code_name all must be set before calling _filter_shape_file()
        self._filter_shape_file(reports.shapefile_path)

        self.logger.info(f"Geography changed to: {self.CODE_COL} ({self.code_name}). Data has columns {self.map_data.columns}.")

    def set_score_col(self, dimension: dict):
        """
        Sets the SCORE_COL to use for a particular boundary

        :param dict dimension: specifies the score column to use int the data
        """
        self.score_col_key = f"{self.boundary_name}_{dimension['column']}"
        self.SCORE_COL[self.score_col_key] = dimension["column"]
        self.score_col_label = dimension["tooltip"]
        self.logger.info(f"Setting score column to {dimension['column']} (displayed: {self.score_col_label})")

    def add_layer(self, name: str, markers_clustered: bool = False, show: bool = True):
        """
        Adds a maker layer to the map

        :param str name: The name of the layer - appears in LayerControl on Map
        :param bool markers_clustered: Whether the markers should cluster or not
        :param bool show:
        """
        if markers_clustered:
            self.layers[name] = MarkerCluster(name=name, show=show).add_to(self.map)
        else:
            self.layers[name] = FeatureGroup(name=name, show=show).add_to(self.map)

    def _filter_shape_file(self, shape_file_path: Path):
        """Loads, filters and converts shapefiles for later use

        Loads shapefile from path into GeoPandas dataframe
        Filters out unneeded shapes within all shapes loaded
        Converts from British National Grid to WGS84, as Leaflet doesn't understand BNG

        :param Path shape_file_path: path to ESRI shapefile with region information
        :return: None
        """

        # Read a shape file
        all_shapes = gpd.GeoDataFrame.from_file(shape_file_path)  # NoQA

        if self.code_name not in all_shapes.columns:
            raise KeyError(f"{self.code_name} not present in shapefile. Valid columns are: {all_shapes.columns}")

        original_number_of_shapes = len(all_shapes.index)
        self.logger.info(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in the {self.CODE_COL} of the map_data")
        self.logger.debug(f"Filtering {original_number_of_shapes} shapes by {self.code_name} being in \n{self.map_data[self.CODE_COL]}")

        list_codes = self.map_data[self.CODE_COL].drop_duplicates().astype(str).to_list()
        filtered_shapes = all_shapes.loc[all_shapes[self.code_name].isin(list_codes)]
        self.logger.info(f"Resulting in {len(filtered_shapes.index)} shapes")

        # Covert shape file to world co-ordinates
        self.geo_data = filtered_shapes[["geometry", self.code_name, self.boundary_name]].to_crs(f"epsg:{utility.WGS_84}")
        # self.logger.debug(f"geo_data\n{self.geo_data}")

    def add_areas(self, name: str, show: bool, colourmap: colormap.ColorMap, col_name: str, significance_threshold: float):
        """Adds features from self.geo_data to map

        :param str name: the name of the Layer, as it will appear in the layer controls
        :param bool show: whether to show the layer by default
        :param colormap.ColorMap colourmap: branca colour map object
        :param str col_name: column of dataframe used. Used for a unique key.
        :param float significance_threshold: If an area's value is significant enough to be displayed
        :return: None
        """
        self.logger.info(f"Merging geo_json on {self.code_name} from shapefile with {self.CODE_COL} from boundary report")
        merged_data = self.geo_data.merge(self.map_data, left_on=self.code_name, right_on=self.CODE_COL).drop_duplicates()
        self.logger.debug(f"Merged_data\n{merged_data}")
        if len(merged_data.index) == 0:
            self.logger.error("Data unsuccesfully merged resulting in zero records")
            raise Exception("Data unsuccesfully merged resulting in zero records")

        boundary_name = f"{self.boundary_name}_{col_name}"

        # fmt: off
        folium.GeoJson(
            data=merged_data.to_json(),
            name=name,
            style_function=lambda x: {
                "fillColor": self._map_colourmap(x["properties"], boundary_name, significance_threshold, colourmap),
                "color": "black",
                "fillOpacity": self._map_opacity(x["properties"], boundary_name, significance_threshold),
                "weight": 0.10,
            },
            tooltip=folium.GeoJsonTooltip(fields=[self.boundary_name, self.SCORE_COL[boundary_name]], aliases=["Name", self.score_col_label], localize=True,),
            show=show,
        ).add_to(self.map)
        # fmt: on
        colourmap.add_to(self.map)
        del merged_data, name

    def _map_colourmap(self, properties: dict, boundary_name: str, threshold: float, colourmap: colormap.ColorMap) -> str:
        """Returns colour from colour map function and value

        :param properties: dictionary of properties
        :param boundary_name:
        :param threshold:
        :param colourmap: a Branca Colormap object to calculate the region's colour
        :return str: hexadecimal colour value "#RRGGBB"
        """
        # self.logger.debug(f"Colouring {properties} by {self.SCORE_COL[boundary_name]}")
        area_score = properties.get(self.SCORE_COL[boundary_name])
        if area_score is None:
            self.logger.debug(f"Colouring gray. key: {boundary_name}, score: {area_score}")
            return "#cccccc"
        elif abs(area_score) < threshold:
            return "#ffbe33"
        elif float(area_score) == 0:
            return "#555555"
        else:
            return colourmap(area_score)

    def _map_opacity(self, properties: dict, boundary_name: str, threshold: float) -> float:
        """Decides if a feature's value is important enough to be shown"""
        default_opacity = 0.33

        if not threshold:
            return default_opacity
        area_score = properties.get(self.SCORE_COL[boundary_name])
        if area_score is None:
            return 1

        return default_opacity if abs(area_score) > threshold else default_opacity / 4

    def add_marker(self, lat: float, long: float, popup: folium.Popup, colour: str, layer_name: str = "Sections"):
        """Adds a leaflet marker to the map using given values

        :param float lat: latitude of the marker
        :param float long: longitude of the marker
        :param folium.Popup popup: popup text for the marker
        :param str colour: colour for the marker
        :param str layer_name: name of the layer that markers are added to
        :return: None
        """
        folium.Marker(location=[round(lat, 4), round(long, 4)], popup=popup, icon=folium.Icon(color=colour)).add_to(self.layers[layer_name])

    def set_bounds(self, bounds: list):
        self.map.fit_bounds(bounds)

    def save(self):
        """Saves the folium map to a HTML file """
        # Add layer control to map
        folium.LayerControl(collapsed=False).add_to(self.map)
        self.map.save(f"{self.out_file}")

    def show(self):
        """Show the file at self.out_file in the default browser. """
        webbrowser.open(self.out_file.as_uri())
