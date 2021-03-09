from itertools import cycle
from pathlib import Path
from typing import Dict, Union

import branca
import folium
import geopandas as gpd
import numpy as np
import pandas as pd

from src.base import Base
from src.data.scout_census import ScoutCensus
from src.data.scout_data import ScoutData
from src.maps.map_plotter import MapPlotter
from src.reports.reports import Reports
import src.utility as utility


class Map(Base):
    def __init__(self, scout_data_object: ScoutData, map_name: str):
        super().__init__(settings=True)

        # Can be set by set_region_of_colour
        self._region_of_colour = None

        self.scout_data = scout_data_object

        self._map_plotter = MapPlotter(Path(self.settings["Output folder"], map_name))

    def add_areas(self, dimension: dict, reports: Reports, show: bool = False, scale: dict = None, threshold: float = 2.5):
        """
        Creates a 2D colouring with geometry specified by the boundary

        :param dict dimension: specifies the column of the data to score against
        :param Reports reports:
        :param bool show: if True the colouring is shown by default
        :param dict scale: Allows a fixed value scale, default is boundaries at
                           0%, 20%, 40%, 60%, 80% and 100%.
        :param float threshold: If an area's value is significant enough to be displayed
        """
        colours = ["#4dac26", "#b8e186", "#f1b6da", "#d01c8b"]
        self._map_plotter.set_boundary(reports)
        self._map_plotter.set_score_col(dimension)
        self._map_plotter.validate_columns()

        non_zero_score_col = self._map_plotter.map_data[dimension["column"]].loc[self._map_plotter.map_data[dimension["column"]] != 0]
        non_zero_score_col = non_zero_score_col.dropna().sort_values(axis=0)

        if not scale:
            colourmap_index = non_zero_score_col.quantile([i / (len(colours) - 1) for i in range(len(colours))]).to_list()
            colourmap_min = self._map_plotter.map_data[dimension["column"]].min()
            colourmap_max = self._map_plotter.map_data[dimension["column"]].max()

            quantiles = [0, 20, 40, 60, 80, 100]
            colourmap_step_index = [np.percentile(non_zero_score_col, q) for q in quantiles]
        else:
            colourmap_index = scale["index"]
            colourmap_min = scale["min"]
            colourmap_max = scale["max"]
            colourmap_step_index = scale["boundaries"]

        colourmap = branca.colormap.LinearColormap(colors=list(reversed(colours)), index=colourmap_index, vmin=colourmap_min, vmax=colourmap_max)
        colourmap = colourmap.to_step(index=colourmap_step_index)
        colourmap.caption = dimension["legend"]

        self.logger.info(f"Colour scale boundary values\n{colourmap_step_index}")
        self.logger.info(f"Colour scale index values\n{colourmap_index}")
        self._map_plotter.add_areas(dimension["legend"], show=show, colourmap=colourmap, col_name=dimension["column"], significance_threshold=threshold)
        # del non_zero_score_col, colourmap_index, colourmap_min, colourmap_max, colourmap_step_index, colourmap

    def add_meeting_places_to_map(self, sections: pd.DataFrame, colour, marker_data: list, layer: dict = None):
        """Adds the sections provided as markers to map with the colour, and data
        indicated by marker_data.

        :param pd.DataFrame sections: Census records relating to Sections with lat and long Columns
        :param str or dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        :param dict layer: Name & properties of layer on map to add meeting places to.
            - Default = {"name"="Sections", "markers_clustered"=False}
        """
        self.logger.info("Adding section markers to map")

        # check that sections dataframe has data
        if sections.empty:
            return

        # Sort sections dataframe
        sections = sections.sort_values("Object_ID").reset_index(drop=True)

        if not self._map_plotter.layers.get(layer["name"]):
            layer = dict(name="Sections", markers_clustered=False) if layer is None else layer
            self._map_plotter.add_layer(layer["name"], layer["markers_clustered"])

        # Sets the map so that it opens in the right area
        valid_points = sections.loc[sections[ScoutCensus.column_labels["VALID_POSTCODE"]] == 1]

        # Sets the map so it opens in the right area
        self._map_plotter.set_bounds([[valid_points["lat"].min(), valid_points["long"].min()], [valid_points["lat"].max(), valid_points["long"].max()]])

        # IDs for finding sections
        district_sections_group_code = -1
        postcodes_ids = sections[ScoutCensus.column_labels["POSTCODE"]]
        district_ids = sections[ScoutCensus.column_labels["id"]["DISTRICT"]]
        # Districts sections have a missing group ID as there is no group, so fill this with a magic reference value
        group_ids = sections[ScoutCensus.column_labels["id"]["GROUP"]].fillna(district_sections_group_code)

        # IDs for iteration
        postcodes = postcodes_ids.drop_duplicates().dropna().astype(str).to_list()

        # Initialise variables
        sections_info_table = pd.DataFrame()

        # Test for if there are any sections
        if not group_ids.dropna().empty or district_ids.dropna().empty:
            unit_type = sections[ScoutCensus.column_labels["UNIT_TYPE"]]
            sections["section"] = utility.section_from_type_vector(unit_type)
            section_names = sections["name"].astype("string")
            sections["yp"] = sections.lookup(sections.index, sections["section"].map(lambda x: ScoutCensus.column_labels["sections"][x]["total"]))
            section_member_info = section_names + " : " + sections["yp"].astype(str) + " " + sections["section"] + "<br>"

            # Awful, awful workaround as Units & Network top awards are lists not strings. Effectivley we only tabluate for groups.
            grp_sects = sections[sections[ScoutCensus.column_labels["UNIT_TYPE"]].isin(["Colony", "Pack", "Troop"])]
            sections["awards"] = pd.Series(
                grp_sects[grp_sects["section"].map(lambda x: ScoutCensus.column_labels["sections"][x]["top_award"])].values.diagonal(), grp_sects.index
            ).astype("Int32")
            sections["eligible"] = pd.Series(
                grp_sects[grp_sects["section"].map(lambda x: ScoutCensus.column_labels["sections"][x]["top_award_eligible"])].values.diagonal(), grp_sects.index
            ).astype("Int32")
            section_awards_info = section_names + " : " + sections["awards"].astype(str) + " Top Awards out of " + sections["eligible"].astype(str) + " eligible<br>"

            if isinstance(colour, dict):
                census_column = colour["census_column"]
                colour_mapping = colour["mapping"]
                sections["marker_colour"] = sections[census_column].map(colour_mapping)
            else:
                sections["marker_colour"] = colour

            # Areas outside the region_of_colour have markers coloured grey
            if self._region_of_colour:
                sections.loc[~sections[self._region_of_colour["column"]].isin(self._region_of_colour["value_list"]), "marker_colour"] = "gray"

            # fmt: off
            sections_info_table = pd.DataFrame({
                "postcode": postcodes_ids,
                "lat": sections["lat"],
                "long": sections["long"],
                "marker_colour": sections["marker_colour"],
                "district_ID": district_ids,
                "group_ID": group_ids,
                "county_name": sections[ScoutCensus.column_labels["name"]["COUNTY"]],
                "district_name": sections[ScoutCensus.column_labels["name"]["DISTRICT"]],
                "group_name": sections[ScoutCensus.column_labels["name"]["GROUP"]],
                "section_name": section_names,
                "member_info": section_member_info,
                "awards_info": section_awards_info,
            })
            # fmt: on
            sections_info_table = sections_info_table.reset_index().set_index(["postcode", "district_ID", "group_ID", "index"], drop=False).drop("index", axis=1)
            sections_info_table = sections_info_table.dropna(subset=["district_ID"]).sort_index(level=[0, 1, 2, 3])

        _sect_info_type = Dict[str, str]
        _group_info_type = Dict[str, Union[str, _sect_info_type]]
        _district_info_type = Dict[str, Union[str, float, _group_info_type]]
        _postcode_info_type = Dict[str, _district_info_type]
        postcode_info: _postcode_info_type = {}
        for postcode in postcodes:
            # Find all the sections with the same postcode
            colocated_sections = sections_info_table.loc[(postcode,)]
            location_row = colocated_sections.iloc[0].to_dict()
            postcode_info[postcode] = {
                "$lat": float(location_row["lat"]),
                "$long": float(location_row["long"]),
                "$marker_colour": str(location_row["marker_colour"]),
            }

            district_ids = colocated_sections["district_ID"].drop_duplicates()
            for district_id in district_ids:
                district_metadata = sections_info_table.loc[(postcode, district_id)]
                county_name = district_metadata["county_name"].to_list()[0]
                district_name = district_metadata["district_name"].to_list()[0]

                # Initialise info dict. Note usage of '$' in the County key, this is as districts must only have letters in their names.
                postcode_info[postcode][district_name] = {"$County": county_name}

                # Loop through sections in group-likes
                group_ids = district_metadata["group_ID"].drop_duplicates()
                for group_id in group_ids:
                    sub_table = sections_info_table.loc[(postcode, district_id, group_id)]
                    group_name = sub_table["group_name"].to_list()[0] if group_id != district_sections_group_code else "District"
                    postcode_info[postcode][district_name][group_name] = {
                        "sect_names": "".join(sub_table["section_name"] + "<br>"),
                        "member_info": "".join(sub_table["member_info"]),
                        "awards_info": "<br>" + "".join(sub_table["awards_info"]),
                    }

        for postcode_name, postcode_dict in postcode_info.items():
            lat = postcode_dict.pop("$lat")
            long = postcode_dict.pop("$long")
            marker_colour = postcode_dict.pop("$marker_colour")
            html = ""

            for district_name, district_dict in postcode_dict.items():
                # Construct the html to form the marker popup
                # District sections first followed by Group sections
                county_name = district_dict.pop("$County")
                html += f"<h3>{district_name} ({county_name})</h3>"

                for child, child_dict in district_dict.items():
                    html += f"<h4>{child}</h4><p align='center'>"
                    html += child_dict["member_info"] if "youth membership" in marker_data else child_dict["sect_names"]
                    if "awards" in marker_data and child != "District":
                        html += child_dict["awards_info"]
                    html += "</p>"

            # Fixes physical size of popup
            popup = folium.Popup(html, max_width=2650)
            self._map_plotter.add_marker(lat, long, popup, marker_colour, layer["name"])

    def add_sections_to_map(self, scout_data_object: ScoutData, colour, marker_data: list, single_section: str = None, layer: str = "Sections", cluster_markers: bool = False):
        """Filter sections and add to map.

        If a single section is specified, plots that section onto the map in
        markers of colour identified by colour, with data indicated by marker_data.

        If else, all sections are plotted from the latest year of data. This
        mesans all Beaver Colonies, Cub Packs, Scout Troops and Explorer Units,
        that have returned in the latest year of the dataset.

        :param ScoutData scout_data_object:
        :param str or dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        :param str single_section: One of Beavers, Cubs, Scouts, Explorers, Network
        :param str layer: The layer of the map that the setions are added to
        :param bool cluster_markers: Should we cluster the markers?
        """
        data: pd.DataFrame = scout_data_object.data
        unit_type_label = ScoutCensus.column_labels["UNIT_TYPE"]

        if single_section:
            filtered_data = data
            section_type = ScoutCensus.column_labels["sections"][single_section]["type"]
            section_types = [section_type]
        else:
            max_year = data["Year"].max()
            latest_year_records = data.loc[data["Year"] == max_year]

            filtered_data = latest_year_records
            section_types = ScoutCensus.get_section_type([ScoutCensus.UNIT_LEVEL_GROUP, ScoutCensus.UNIT_LEVEL_DISTRICT])

        self._map_plotter.add_layer(layer, cluster_markers)
        layer_data = dict(name=layer, markers_clustered=cluster_markers)
        self.add_meeting_places_to_map(filtered_data.loc[filtered_data[unit_type_label].isin(section_types)], colour, marker_data, layer_data)

    def add_custom_data(self, csv_file_path: Path, layer_name: str, location_cols, markers_clustered: bool = False, marker_data: list = None):
        """Function to add custom data as markers on map

        :param str csv_file_path: file path to open csv file
        :param str layer_name: Name of layer that the markers will be added to
        :param str or dict location_cols: Indicates whether adding data with postcodes or co-ordinates
            - if postcodes, str "Postcodes"
            - if co-ordinates, dict of co-ordinate data with keys ["crs", "x", "y"]
        :param bool markers_clustered: Whether to cluster the markers or not
        :param list marker_data: list of strings for values in data that should be in popup
        """

        custom_data = pd.read_csv(csv_file_path)

        if location_cols == "Postcodes":
            # Merge with ONS Postcode Directory to obtain dataframe with lat/long
            ons_pd_data = self.scout_data.ons_pd.data
            custom_data = pd.merge(custom_data, ons_pd_data, how="left", left_on=location_cols, right_index=True, sort=False)
            location_cols = {"crs": utility.WGS_84, "x": "long", "y": "lat"}

        # Create geo data frame with points generated from lat/long or OS
        custom_data = gpd.GeoDataFrame(custom_data, geometry=gpd.points_from_xy(x=custom_data[location_cols["x"]], y=custom_data[location_cols["y"]]))

        # Convert the 'Co-ordinate reference system' (crs) to WGS_84 (i.e. lat/long) if not already
        if location_cols["crs"] != utility.WGS_84:
            custom_data.crs = f"epsg:{location_cols['crs']}"
            custom_data = custom_data.to_crs(f"epsg:{utility.WGS_84}")

        self._map_plotter.add_layer(layer_name, markers_clustered)

        # Plot marker and include marker_data in the popup for every item in custom_data
        def add_popup_data(row):
            if marker_data:
                html = ""
                for marker_col in marker_data:
                    html += f'<p align="center">{row[marker_col]}</p>'
                iframe = folium.IFrame(html=html, width=350, height=100)
                popup = folium.Popup(iframe, max_width=2650)
            else:
                popup = None
            if not np.isnan(row.geometry.x):
                self._map_plotter.add_marker(row.geometry.y, row.geometry.x, popup, colour="green", layer_name=layer_name)

        custom_data.apply(add_popup_data, axis=1)

    def save_map(self):
        self._map_plotter.save()

    def show_map(self):
        self._map_plotter.show()

    def set_region_of_colour(self, column: str, value_list: list):
        self._region_of_colour = {"column": column, "value_list": value_list}

    def generic_colour_mapping(self, grouping_column: str) -> dict:
        # fmt: off
        colours = cycle([
            "cadetblue", "lightblue", "blue", "beige", "red", "darkgreen", "lightgreen", "purple",
            "lightgray", "orange", "pink", "darkblue", "darkpurple", "darkred", "green", "lightred",
        ])
        # fmt: on
        grouping_ids = self.scout_data.data[grouping_column].drop_duplicates()
        mapping = {grouping_id: next(colours) for grouping_id in grouping_ids}
        colour_mapping = {"census_column": grouping_column, "mapping": mapping}
        return colour_mapping

    def district_colour_mapping(self) -> dict:
        return self.generic_colour_mapping(ScoutCensus.column_labels["id"]["DISTRICT"])

    def county_colour_mapping(self) -> dict:
        return self.generic_colour_mapping(ScoutCensus.column_labels["id"]["COUNTY"])
