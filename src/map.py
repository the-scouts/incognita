from itertools import cycle
import branca
import folium
import pandas as pd
import geopandas as gpd
import numpy as np

import src.utility as utility
from src.base import Base
from src.map_plotter import MapPlotter
from src.scout_census import ScoutCensus


class Map(Base):
    def __init__(self, scout_data_object, boundary_object, dimension, map_name, **kwargs):
        super().__init__(settings=True)

        self.map_plotter = None

        # Can be set by set_region_of_colour
        self.region_of_colour = None

        self.census_data = scout_data_object.census_data
        self.ons_pd = scout_data_object.ons_pd

    def create_map(self, score_col, display_score_col, name, legend_label, static_scale=None, cluster_markers=False):
        self.logger.info(f"Creating map from {score_col} with name {name}")

        data_codes = {
            "data": self.boundary_report[self.boundary_dict["name"]],
            "code_col": self.boundary_dict["name"],
            "score_col": score_col,
            "score_col_label": display_score_col
        }

        if not (score_col in list(data_codes["data"].columns)):
            raise Exception(f"The column {score_col} does not exist in data.\nValid columns are {list(data_codes['data'].columns)}")

        self.map = MapPlotter(self.boundary_dict["boundary"],
                                        data_codes,
                                        self.settings["Output folder"] + name,
                                        cluster_markers)

        non_zero_score_col = data_codes["data"][score_col].loc[data_codes["data"][score_col] != 0]
        non_zero_score_col.dropna(inplace=True)
        min_value = data_codes["data"][score_col].min()
        max_value = data_codes["data"][score_col].max()
        self.logger.info(f"Minimum data value: {min_value}. Maximum data value: {max_value}")
        colormap = branca.colormap.LinearColormap(colors=['#ca0020', '#f4a582', '#92c5de', '#0571b0'],
                                                  index=non_zero_score_col.quantile([0, 0.25, 0.75, 1]),
                                                  vmin=min_value,
                                                  vmax=max_value)
        non_zero_score_col.sort_values(axis=0, inplace=True)
        colormap = colormap.to_step(data=non_zero_score_col, quantiles=[0, 0.2, 0.4, 0.6, 0.8, 1])
        self.logger.info(f"Colour scale boundary values\n{non_zero_score_col.quantile([0, 0.2, 0.4, 0.6, 0.8, 1])}")
        colormap.caption = legend_label
        self.map.plot(legend_label, show=True, boundary_name=self.boundary_dict["boundary"]["name"], colormap=colormap)

        if static_scale:
            colormap_static = branca.colormap.LinearColormap(colors=['#ca0020', '#f7f7f7', '#0571b0'],
                                                             index=static_scale["index"],
                                                             vmin=static_scale["min"],
                                                             vmax=static_scale["max"])\
                .to_step(index=static_scale["boundaries"])
            colormap_static.caption = legend_label + " (static)"
            self.map.plot(legend_label + " (static)", show=False, boundary_name=self.boundary_dict["boundary"]["name"], colormap=colormap_static)

    def add_all_sections_to_map(self, colour, marker_data):
        """Adds sections from latest year of data as markers on map

        Plots all Beaver Colonies, Cub Packs, Scout Troops and Explorer Units,
        who have returned in the latest year of the dataset.

        :param str/dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        """
        min_year, max_year = self.years_of_return(self.census_data.data)
        latest_year_records = self.census_data.data.loc[self.census_data.data["Year"] == max_year]
        self.add_sections_to_map(latest_year_records.loc[latest_year_records[ScoutCensus.column_labels['UNIT_TYPE']].isin(self.census_data.get_section_type([ScoutCensus.UNIT_LEVEL_GROUP, ScoutCensus.UNIT_LEVEL_DISTRICT]))], colour, marker_data)

    def add_single_section_to_map(self, section, colour, marker_data):
        """Plots the section specified by section onto the map, in markers of
        colour identified by colour, with data indicated by marker_data.

        :param str section: One of Beavers, Cubs, Scouts, Explorers, Network
        :param str/dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        """
        self.add_sections_to_map(self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['UNIT_TYPE']] == ScoutCensus.column_labels['sections'][section]["type"]], colour, marker_data)

    def add_sections_to_map(self, sections, colour, marker_data):
        """Adds the sections provided as markers to map with the colour, and data
        indicated by marker_data.

        :param DataFrame sections: Census records relating to Sections with lat and long Columns
        :param str/dict colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
        :param list marker_data: List of strings which determines content for popup, including:
            - youth membership
            - awards
        """
        self.logger.info("Adding section markers to map")

        valid_points = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['VALID_POSTCODE']] == 1]

        # Sets the map so it opens in the right area
        self.map.set_bounds([[valid_points["lat"].min(), valid_points["long"].min()],
                              [valid_points["lat"].max(), valid_points["long"].max()]])

        postcodes = sections[ScoutCensus.column_labels['POSTCODE']].unique()
        postcodes = [str(postcode) for postcode in postcodes]
        if "nan" in postcodes:
            postcodes.remove("nan")

        increment = len(postcodes) / 100
        count = 1
        old_percentage = 0
        for postcode in postcodes:
            new_percentage = round(count / increment)
            if new_percentage > old_percentage:
                self.logger.info(f"% of sections added to map {new_percentage}")
                old_percentage = new_percentage
            count += 1

            self.logger.debug(postcode)
            # Find all the sections with the same postcode
            colocated_sections = sections.loc[sections[ScoutCensus.column_labels['POSTCODE']] == postcode]
            colocated_district_sections = colocated_sections.loc[colocated_sections[ScoutCensus.column_labels['UNIT_TYPE']].isin(self.census_data.get_section_type('District'))]
            colocated_group_sections = colocated_sections.loc[colocated_sections[ScoutCensus.column_labels['UNIT_TYPE']].isin(self.census_data.get_section_type('Group'))]

            lat = float(colocated_sections.iloc[0]['lat'])
            long = float(colocated_sections.iloc[0]['long'])

            # Construct the html to form the marker popup
            # District sections first followed by Group sections
            html = ""

            districts = colocated_district_sections[ScoutCensus.column_labels['id']["DISTRICT"]].unique()
            for district in districts:
                district_name = colocated_district_sections.iloc[0][ScoutCensus.column_labels['name']["DISTRICT"]] + " District"
                html += (f"<h3 align=\"center\">{district_name}</h3><p align=\"center\">"
                         f"<br>")
                colocated_in_district = colocated_district_sections.loc[colocated_district_sections[ScoutCensus.column_labels['id']["DISTRICT"]] == district]
                for section_id in colocated_in_district.index:
                    type = colocated_in_district.at[section_id, ScoutCensus.column_labels['UNIT_TYPE']]
                    name = colocated_in_district.at[section_id, 'name']
                    html += f"{name} : "
                    section = self.section_from_type(type)
                    if "youth membership" in marker_data:
                        male_yp = int(colocated_in_district.at[section_id, ScoutCensus.column_labels['sections'][section]["male"]])
                        female_yp = int(colocated_in_district.at[section_id, ScoutCensus.column_labels['sections'][section]["female"]])
                        yp = male_yp + female_yp
                        html += f"{yp} {section}<br>"
                html += "</p>"

            groups = colocated_group_sections[ScoutCensus.column_labels['id']["GROUP"]].unique()
            self.logger.debug(groups)
            for group in groups:
                colocated_in_group = colocated_sections.loc[colocated_sections[ScoutCensus.column_labels['id']["GROUP"]] == group]
                group_name = colocated_in_group.iloc[0][ScoutCensus.column_labels['name']["GROUP"]] + " Group"

                html += (f"<h3 align=\"center\">{group_name}</h3><p align=\"center\">"
                         f"<br>")
                for section_id in colocated_in_group.index:
                    type = colocated_in_group.at[section_id, ScoutCensus.column_labels['UNIT_TYPE']]
                    name = colocated_in_group.at[section_id, 'name']
                    section = self.section_from_type(type)
                    district_id = colocated_in_group.at[section_id, ScoutCensus.column_labels['id']["DISTRICT"]]

                    html += f"{name} : "
                    if "youth membership" in marker_data:
                        male_yp = int(colocated_in_group.at[section_id, ScoutCensus.column_labels['sections'][section]["male"]])
                        female_yp = int(colocated_in_group.at[section_id, ScoutCensus.column_labels['sections'][section]["female"]])
                        yp = male_yp + female_yp
                        html += f"{yp} {section}<br>"
                    if "awards" in marker_data:
                        awards = int(colocated_in_group.at[section_id, ScoutCensus.column_labels['sections'][section]["top_award"]])
                        eligible = int(colocated_in_group.at[section_id, ScoutCensus.column_labels['sections'][section]["top_award_eligible"]])
                        if section == "Beavers":
                            html += f"{awards} Bronze Awards of {eligible} eligible<br>"

                html += "</p>"

            # Fixes physical size of popup
            if len(groups) == 1:
                height = 120
            else:
                height = 240
            iframe = folium.IFrame(html=html, width=350, height=100)
            popup = folium.Popup(iframe, max_width=2650)

            if isinstance(colour, dict):
                census_column = colour["census_column"]
                colour_mapping = colour["mapping"]
                value = colocated_sections.iloc[0][census_column]
                marker_colour = colour_mapping[value]
            else:
                marker_colour = colour

            # Areas outside the region_of_color have markers coloured grey
            if self.region_of_color:
                if colocated_sections.iloc[0][self.region_of_color["column"]] not in self.region_of_color["value_list"]:
                    marker_colour = 'gray'

            self.logger.debug(f"Placing {marker_colour} marker at {lat},{long}")
            self.map.add_marker(lat, long, popup, marker_colour)

    def add_custom_data(self, csv_file_path, name, location_type="Postcodes", location_cols=None, markers_clustered=False, marker_data=None):
        """Function to add custom data as markers on map

        Note that the create_map function must have been called first, to
        populate self.map object.

        :param str csv_file_path: file path to open csv file
        :param str name: Name of layer that the markers will be added to
        :param str location_type: Either "Postcodes" or "Co-ordinates"
        :param str/dict location_cols: If "Co-ordinates" requires a dict {"crs": , "x": , "y": }
                                   If "Postcodes" the column name of the Postcode columm
        :param bool markers_clustered: Whether to cluster the markers or not
        :param list marker_data: list of strings for values in data that should be in popup
        """

        data = pd.read_csv(csv_file_path)

        if location_type == "Postcodes":
            # Merge with ONS Postcode Directory to obtain dataframe with lat/long
            data = pd.merge(data, self.ons_data.data, how='left', left_on=location_cols, right_index=True, sort=False)
            location_cols = {"crs": '4326', "x": "long", "y": "lat"}

        # Create geo data frame with points generated from lat/long or OS
        data = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data[location_cols["x"]], data[location_cols["y"]]))

        # Convert the 'Co-ordinate reference system' (crs) to WGS_84 (i.e. lat/long) if not already
        data.crs = {'init': f"epsg:{location_cols['crs']}"}
        data = data.to_crs({'init': 'epsg:4326'})

        self.map.add_layer(name, markers_clustered)

        # For each point plot marker, and include marker_data in the popup
        for index, row in data.iterrows():
            if marker_data:
                html = ""
                for data in marker_data:
                    html += f"<p align=\"center\">{row[data]}<p align=\"center\">"
                iframe = folium.IFrame(html=html, width=350, height=100)
                popup = folium.Popup(iframe, max_width=2650)
            else:
                popup = None
            if not np.isnan(row.geometry.x):
                self.map.add_marker(row.geometry.y, row.geometry.x, popup, 'green', name)

    def save_map(self):
        self.map.save()

    def show_map(self):
        self.map.show()

    def set_region_of_color(self, column, value_list):
        self.region_of_color = {"column": column, "value_list": value_list}

    def district_color_mapping(self):
        colors = cycle(['cadetblue', 'lightblue', 'blue', 'beige', 'red', 'darkgreen', 'lightgreen', 'purple', 'lightgrayblack',
                'orange', 'pink', 'white', 'darkblue', 'darkpurple', 'darkred', 'green', 'lightred'])
        district_ids = self.census_data.data[ScoutCensus.column_labels['id']["DISTRICT"]].unique()
        mapping = {}
        for district_id in district_ids:
            mapping[district_id] = next(colors)
        colour_mapping = {"census_column": ScoutCensus.column_labels['id']["DISTRICT"], "mapping": mapping}
        return colour_mapping
