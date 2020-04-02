from itertools import cycle
import branca
import folium
import pandas as pd
import geopandas as gpd
import numpy as np

import src.utility as utility
from src.reports.reports import Reports
from src.data.scout_data import ScoutData
from src.base import Base
from src.maps.map_plotter import MapPlotter
from src.data.scout_census import ScoutCensus


class Map(Base):
    def __init__(self, scout_data_object: ScoutData, map_name: str):
        super().__init__(settings=True)

        self.map_plotter = None

        # Can be set by set_region_of_colour
        self.region_of_colour = None

        self.scout_data = scout_data_object

        self.map_plotter = MapPlotter(self.settings["Output folder"] + map_name)

    def add_areas(self, dimension, reports: Reports, show=False, scale=None):
        """
        Creates a 2D colouring with geometry specified by the boundary

        :param dict dimension: specifies the column of the data to score against
        :param Reports reports:
        :param bool show: if True the colouring is shown by default
        :param dict scale: Allows a fixed value scale, default is boundaries at
                           0%, 20%, 40%, 60%, 80% and 100%.
        """
        shapefile_name = reports.shapefile_name
        self.map_plotter.set_boundary(reports)
        self.map_plotter.set_score_col(shapefile_name, dimension)

        non_zero_score_col = self.map_plotter.map_data[self.map_plotter.SCORE_COL[shapefile_name]].loc[self.map_plotter.map_data[self.map_plotter.SCORE_COL[shapefile_name]] != 0]
        non_zero_score_col.dropna(inplace=True)
        min_value = self.map_plotter.map_data[self.map_plotter.SCORE_COL[shapefile_name]].min()
        max_value = self.map_plotter.map_data[self.map_plotter.SCORE_COL[shapefile_name]].max()
        self.logger.info(f"Minimum data value: {min_value}. Maximum data value: {max_value}")

        if not scale:
            colourmap = branca.colormap.LinearColormap(
                colors=["#4dac26", "#b8e186", "#f1b6da", "#d01c8b"], index=non_zero_score_col.quantile([0, 0.25, 0.75, 1]), vmin=min_value, vmax=max_value,
            )

            non_zero_score_col.sort_values(axis=0, inplace=True)
            colourmap = colourmap.to_step(data=non_zero_score_col, quantiles=[0, 0.2, 0.4, 0.6, 0.8, 1])
        else:
            colourmap = branca.colormap.LinearColormap(colors=["#4dac26", "#b8e186", "#f1b6da", "#d01c8b"], index=scale["index"], vmin=scale["min"], vmax=scale["max"],).to_step(
                index=scale["boundaries"]
            )
            colourmap.caption = dimension["legend"] + " (static)"

        self.logger.info(f"Colour scale boundary values\n{non_zero_score_col.quantile([0, 0.2, 0.4, 0.6, 0.8, 1])}")
        colourmap.caption = dimension["legend"]
        self.map_plotter.add_areas(dimension["legend"], show=show, boundary_name=shapefile_name, colourmap=colourmap)

    def add_meeting_places_to_map(self, sections: pd.DataFrame, colour, marker_data: list, layer: str = "Sections", cluster_markers: bool = False):
        """Adds the sections provided as markers to map with the colour, and data
        indicated by marker_data.

        :param pd.DataFrame sections: Census records relating to Sections with lat and long Columns
        :param str or dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        :param str layer: Name of layer on map to add meeting places to
        :param bool cluster_markers: If true markers are clustered
        """
        self.logger.info("Adding section markers to map")

        if not self.map_plotter.layers.get(layer):
            self.map_plotter.add_layer(layer, cluster_markers)

        valid_points = sections.loc[sections[ScoutCensus.column_labels["VALID_POSTCODE"]] == 1]

        # Sets the map so it opens in the right area
        self.map_plotter.set_bounds(
            [[valid_points["lat"].min(), valid_points["long"].min()], [valid_points["lat"].max(), valid_points["long"].max()],]
        )

        postcodes = sections[ScoutCensus.column_labels["POSTCODE"]].drop_duplicates().dropna().astype(str).to_list()

        increment = len(postcodes) / 100
        count = 1
        old_percentage = 0
        for postcode in postcodes:
            new_percentage = round(count / increment)
            if new_percentage > old_percentage:
                self.logger.info(f"{new_percentage}% of sections added to map ")
                old_percentage = new_percentage
            count += 1

            self.logger.debug(postcode)
            # Find all the sections with the same postcode
            colocated_sections: pd.DataFrame = sections.loc[sections[ScoutCensus.column_labels["POSTCODE"]] == postcode]
            colocated_district_sections: pd.DataFrame = colocated_sections.loc[
                colocated_sections[ScoutCensus.column_labels["UNIT_TYPE"]].isin(ScoutCensus.get_section_type("District"))
            ]
            colocated_group_sections: pd.DataFrame = colocated_sections.loc[colocated_sections[ScoutCensus.column_labels["UNIT_TYPE"]].isin(ScoutCensus.get_section_type("Group"))]

            lat = float(colocated_sections.iloc[0]["lat"])
            long = float(colocated_sections.iloc[0]["long"])

            # Construct the html to form the marker popup
            # District sections first followed by Group sections
            html = ""

            districts = colocated_district_sections[ScoutCensus.column_labels["id"]["DISTRICT"]].drop_duplicates()
            for district in districts:
                district_name = colocated_district_sections.iloc[0][ScoutCensus.column_labels["name"]["DISTRICT"]] + " District"
                html += f'<h3 align="center">{district_name}</h3><p align="center">' f"<br>"
                colocated_in_district = colocated_district_sections.loc[colocated_district_sections[ScoutCensus.column_labels["id"]["DISTRICT"]] == district]
                for section_id in colocated_in_district.index:
                    unit_type = colocated_in_district.at[section_id, ScoutCensus.column_labels["UNIT_TYPE"]]
                    section = utility.section_from_type(unit_type)
                    name = colocated_in_district.at[section_id, "name"]

                    html += f"{name} : "
                    if "youth membership" in marker_data:
                        male_yp = int(colocated_in_district.at[section_id, ScoutCensus.column_labels["sections"][section]["male"]])
                        female_yp = int(colocated_in_district.at[section_id, ScoutCensus.column_labels["sections"][section]["female"]])
                        yp = male_yp + female_yp
                        html += f"{yp} {section}<br>"
                html += "</p>"

            groups = colocated_group_sections[ScoutCensus.column_labels["id"]["GROUP"]].drop_duplicates()
            self.logger.debug(groups)
            for group in groups:
                colocated_in_group = colocated_group_sections.loc[colocated_group_sections[ScoutCensus.column_labels["id"]["GROUP"]] == group]
                group_name = colocated_in_group.iloc[0][ScoutCensus.column_labels["name"]["GROUP"]] + " Group"

                html += f'<h3 align="center">{group_name}</h3><p align="center">' f"<br>"
                for section_id in colocated_in_group.index:
                    # district_id = colocated_in_group.at[section_id, ScoutCensus.column_labels['id']["DISTRICT"]]
                    unit_type = colocated_in_group.at[section_id, ScoutCensus.column_labels["UNIT_TYPE"]]
                    section = utility.section_from_type(unit_type)
                    name = colocated_in_group.at[section_id, "name"]

                    html += f"{name} : "
                    if "youth membership" in marker_data:
                        male_yp = int(colocated_in_group.at[section_id, ScoutCensus.column_labels["sections"][section]["male"]])
                        female_yp = int(colocated_in_group.at[section_id, ScoutCensus.column_labels["sections"][section]["female"]])
                        yp = male_yp + female_yp
                        html += f"{yp} {section}<br>"
                    if "awards" in marker_data:
                        awards = int(colocated_in_group.at[section_id, ScoutCensus.column_labels["sections"][section]["top_award"]])
                        eligible = int(colocated_in_group.at[section_id, ScoutCensus.column_labels["sections"][section]["top_award_eligible"]])
                        if section == "Beavers":
                            html += f"{awards} Bronze Awards of {eligible} eligible<br>"

                html += "</p>"

            # Fixes physical size of popup
            popup = folium.Popup(html, max_width=2650)

            if isinstance(colour, dict):
                census_column = colour["census_column"]
                colour_mapping = colour["mapping"]
                value = colocated_sections.iloc[0][census_column]
                marker_colour = colour_mapping[value]
            else:
                marker_colour = colour

            # Areas outside the region_of_colour have markers coloured grey
            if self.region_of_colour:
                if colocated_sections.iloc[0][self.region_of_colour["column"]] not in self.region_of_colour["value_list"]:
                    marker_colour = "gray"

            self.logger.debug(f"Placing {marker_colour} marker at {lat},{long}")
            self.map_plotter.add_marker(lat, long, popup, marker_colour, layer)

    def add_sections_to_map(
        self, scout_data_object: ScoutData, colour, marker_data: list, single_section=None, layer="Sections", cluster_markers: bool = False,
    ):
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

        self.add_meeting_places_to_map(
            filtered_data.loc[filtered_data[unit_type_label].isin(section_types)], colour, marker_data, layer, cluster_markers=cluster_markers,
        )

    def add_custom_data(self, csv_file_path, layer_name, location_cols, markers_clustered=False, marker_data=None):
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
            location_cols = {"crs": 4326, "x": "long", "y": "lat"}

        # Create geo data frame with points generated from lat/long or OS
        custom_data = gpd.GeoDataFrame(custom_data, geometry=gpd.points_from_xy(x=custom_data[location_cols["x"]], y=custom_data[location_cols["y"]]),)

        # Convert the 'Co-ordinate reference system' (crs) to WGS_84 (i.e. lat/long) if not already
        if location_cols["crs"] != 4326:
            custom_data.crs = {"init": f"epsg:{location_cols['crs']}"}
            custom_data = custom_data.to_crs({"init": "epsg:4326"})

        self.map_plotter.add_layer(layer_name, markers_clustered)

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
                self.map_plotter.add_marker(row.geometry.y, row.geometry.x, popup, colour="green", layer_name=layer_name)

        custom_data.apply(add_popup_data, axis=1)

    def save_map(self):
        self.map_plotter.save()

    def show_map(self):
        self.map_plotter.show()

    def set_region_of_colour(self, column, value_list):
        self.region_of_colour = {"column": column, "value_list": value_list}

    def district_colour_mapping(self):
        # fmt: off
        colours = cycle([
            "cadetblue", "lightblue", "blue", "beige", "red",  "darkgreen", "lightgreen", "purple",
            "lightgray", "orange", "pink", "darkblue", "darkpurple", "darkred", "green", "lightred",
        ])
        # fmt: on
        district_ids = self.scout_data.data[ScoutCensus.column_labels["id"]["DISTRICT"]].drop_duplicates()
        mapping = {district_id: next(colours) for district_id in district_ids}
        colour_mapping = {"census_column": ScoutCensus.column_labels["id"]["DISTRICT"], "mapping": mapping}
        return colour_mapping
