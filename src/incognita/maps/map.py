from __future__ import annotations

from itertools import cycle
from typing import Literal, TYPE_CHECKING, Union
import webbrowser

import branca
import folium
from folium.map import FeatureGroup
from folium.plugins import MarkerCluster
import geopandas as gpd
import numpy as np
import pandas as pd

from incognita.data import scout_census
from incognita.data.scout_data import ScoutData
from incognita.logger import logger
from incognita.reports.reports import Reports
from incognita.utility import config
from incognita.utility import utility

if TYPE_CHECKING:
    from pathlib import Path

    from branca import colormap


class Map:
    """This class enables easy plotting of maps with a shape file.

    Attributes:
        map: holds the folium map object

    """

    def __init__(self, map_name: str):
        """Initialise Map class.

        Args:
            map_name: Filename for the saved map

        """
        # kwargs to leaflet
        leaflet_kwargs = dict(
            zoomSnap=0.05,
            zoomDelta=0.1,
        )
        # Create folium map
        self.map: folium.Map = folium.Map(
            location=[53.5, -1.49],
            zoom_start=6,
            attr="Map data &copy; <a href='https://openstreetmap.org'>OpenStreetMap</a>, <a href='https://cartodb.com/attributions'>CARTO</a>",
            # tiles='OpenStreetMap',
            tiles="CartoDB positron nolabels",
            **leaflet_kwargs,
        )
        # self.map_labels = folium.TileLayer("CartoDB positron onlylabels", overlay=True)
        self.map.add_child(folium.LayerControl(collapsed=False))  # Add layer control to map

        self.out_file = config.SETTINGS.folders.output / f"{map_name}.html"

    def add_areas(
        self,
        value_col: str,
        tooltip: str,
        layer_name: str,
        reports: Reports,
        show: bool = False,
        scale_index: list[int] = None,
        scale_step_boundaries: list[int] = None,
        significance_threshold: float = 2.5,
    ) -> None:
        """Creates a 2D colouring with geometry specified by the boundary

        Args:
            value_col: Data column to use for choropleth colour values
            tooltip: Mouseover tooltip for each boundary (e.g. "% Change 6-18")
            layer_name: Legend key for the layer (e.g. "% Change 6-18 (Counties)")
            reports:
            show: If True, show the layer by default
            scale_index: Allows a fixed value scale - colour indices
            scale_step_boundaries: Fixed scale step boundary indices
            significance_threshold: If an area's value is significant enough to be displayed

        """
        colours = list(reversed(("#4dac26", "#b8e186", "#f1b6da", "#d01c8b")))
        map_data = reports.data  # contains shapefile paths, and labels for region codes and names
        code_col = reports.geography.metadata.key  # holds the name of the region class, e.g. oslaua, pcon
        geo_data = _load_boundary(reports)

        # Set score col properties to use for a particular boundary
        logger.info(f"Setting score column to {value_col} (displayed: {tooltip})")

        if value_col not in map_data.columns:
            logger.error(f"{value_col} is not a valid column in the data. \n" f"Valid columns include {map_data.columns}")
            raise KeyError(f"{value_col} is not a valid column in the data.")

        non_zero_value_col = map_data[value_col][map_data[value_col] != 0].dropna().sort_values()
        if scale_index is None:
            scale_index = non_zero_value_col.quantile([i / (len(colours) - 1) for i in range(len(colours))]).to_list()
        if scale_step_boundaries is None:
            quantiles = (0, 20, 40, 60, 80, 100)
            scale_step_boundaries = [np.percentile(non_zero_value_col, q) for q in quantiles]
        colour_map = branca.colormap.LinearColormap(colors=colours, index=scale_index, vmin=min(scale_index), vmax=max(scale_index)).to_step(index=scale_step_boundaries)
        colour_map.caption = layer_name

        logger.info(f"Colour scale boundary values\n{scale_step_boundaries}")
        logger.info(f"Colour scale index values\n{scale_index}")

        logger.info(f"Merging geo_json on shape_codes from shapefile with {code_col} from boundary report")
        merged_data = geo_data.merge(map_data, left_on="shape_codes", right_on=code_col).drop_duplicates()
        logger.debug(f"Merged_data\n{merged_data}")
        if len(merged_data.index) == 0:
            logger.error("Data unsuccessfully merged resulting in zero records")
            raise Exception("Data unsuccessfully merged resulting in zero records")

        # fmt: off
        self.map.add_child(
            folium.GeoJson(
                data=merged_data.to_json(),
                name=layer_name,  # the name of the Layer, as it will appear in the layer controls,
                style_function=lambda x: {
                    "fillColor": _map_colour_map(x["properties"], value_col, significance_threshold, colour_map),
                    "color": "black",
                    "fillOpacity": _map_opacity(x["properties"], value_col, significance_threshold),
                    "weight": 0.10,
                },
                tooltip=folium.GeoJsonTooltip(fields=["shape_names", value_col], aliases=["Name", tooltip], localize=True),
                show=show,
            )
        )
        # fmt: on
        self.map.add_child(colour_map)

    def add_meeting_places_to_map(self, sections: pd.DataFrame, colour: Union[str, dict], marker_data: list[str], layer_name: str = "Sections", cluster_markers: bool = False, show_layer: bool = True, coloured_region: set[str] = None, coloured_region_key: str = "", ) -> None:
        """Adds the sections provided as markers to map with the colour, and data
        indicated by marker_data.

        Args:
            sections: Census records relating to Sections with lat and long Columns
            colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
            marker_data: List of strings which determines content for popup, including:
                - youth membership
                - awards
            layer_name: Name of map layer for meeting places. Default = "Sections"
            cluster_markers: Whether to cluster markers on the map
            show_layer: Whether to show the layer by default
            coloured_region: If specified, markers on the map but not within coloured_region are grey
            coloured_region_key: Column for coloured_region boundary codes

        """
        logger.info("Adding section markers to map")

        # check that sections dataframe has data
        if sections.empty:
            return

        # Sort sections dataframe
        sections = sections.sort_values("Object_ID").reset_index(drop=True)

        if layer_name in self.map._children:  # NoQA
            raise ValueError("Layer already used!")
        layer_type = MarkerCluster if cluster_markers else FeatureGroup
        layer = layer_type(name=layer_name, show=show_layer).add_to(self.map)

        # Sets the map so that it opens in the right area
        valid_points = sections.loc[sections[scout_census.column_labels.VALID_POSTCODE] == 1]

        # Sets the map so it opens in the right area
        self.map.fit_bounds([[valid_points["lat"].min(), valid_points["long"].min()], [valid_points["lat"].max(), valid_points["long"].max()]])

        # IDs for finding sections
        district_sections_group_code = -1
        postcodes_ids = sections[scout_census.column_labels.POSTCODE]
        district_ids = sections[scout_census.column_labels.id.DISTRICT]
        # Districts sections have a missing group ID as there is no group, so fill this with a magic reference value
        group_ids = sections[scout_census.column_labels.id.GROUP].fillna(district_sections_group_code)

        # IDs for iteration
        postcodes = postcodes_ids.drop_duplicates().dropna().astype(str).to_list()

        # Initialise variables
        sections_info_table = pd.DataFrame()

        # Test for if there are any sections
        if not group_ids.dropna().empty or district_ids.dropna().empty:
            unit_type = sections[scout_census.column_labels.UNIT_TYPE]
            sections["section"] = utility.section_from_type_vector(unit_type)
            section_names = sections["name"].astype("string")
            sections["yp"] = sections.lookup(sections.index, sections["section"].map(lambda x: getattr(scout_census.column_labels.sections, x).total))
            section_member_info = section_names + " : " + sections["yp"].astype(str) + " " + sections["section"] + "<br>"

            # Awful, awful workaround as Units & Network top awards are lists not strings. Effectively we only tabulate for groups.
            grp_sects = sections[sections[scout_census.column_labels.UNIT_TYPE].isin(["Colony", "Pack", "Troop"])]
            sections["awards"] = pd.Series(
                grp_sects[grp_sects["section"].map(lambda x: getattr(scout_census.column_labels.sections, x).top_award)].values.diagonal(), grp_sects.index
            ).astype("Int32")
            sections["eligible"] = pd.Series(
                grp_sects[grp_sects["section"].map(lambda x: getattr(scout_census.column_labels.sections, x).top_award_eligible)].values.diagonal(), grp_sects.index
            ).astype("Int32")
            section_awards_info = section_names + " : " + sections["awards"].astype(str) + " Top Awards out of " + sections["eligible"].astype(str) + " eligible<br>"

            if isinstance(colour, dict):
                census_column = colour["census_column"]
                colour_mapping = colour["mapping"]
                sections["marker_colour"] = sections[census_column].map(colour_mapping)
            else:
                sections["marker_colour"] = colour

            # Areas outside the region_of_colour have markers coloured grey
            if coloured_region_key and coloured_region is not None:
                sections.loc[~sections[coloured_region_key].isin(coloured_region), "marker_colour"] = "gray"

            # fmt: off
            sections_info_table = pd.DataFrame({
                "postcode": postcodes_ids,
                "lat": sections["lat"],
                "long": sections["long"],
                "marker_colour": sections["marker_colour"],
                "district_ID": district_ids,
                "group_ID": group_ids,
                "county_name": sections[scout_census.column_labels.name.COUNTY],
                "district_name": sections[scout_census.column_labels.name.DISTRICT],
                "group_name": sections[scout_census.column_labels.name.GROUP],
                "section_name": section_names,
                "member_info": section_member_info,
                "awards_info": section_awards_info,
            })
            # fmt: on
            sections_info_table = sections_info_table.reset_index().set_index(["postcode", "district_ID", "group_ID", "index"], drop=False).drop("index", axis=1)
            sections_info_table = sections_info_table.dropna(subset=["district_ID"]).sort_index(level=[0, 1, 2, 3])

        _sect_info_type = dict[str, str]
        _group_info_type = dict[str, Union[str, _sect_info_type]]
        _district_info_type = dict[str, Union[str, float, _group_info_type]]
        _postcode_info_type = dict[str, _district_info_type]
        postcode_info: _postcode_info_type = {}
        for postcode in postcodes:
            # Find all the sections with the same postcode
            colocated_sections = sections_info_table.loc[(postcode,)]
            location_row = colocated_sections.iloc[0].to_dict()
            postcode_info[postcode] = {
                "$lat": round(location_row["lat"], 4),
                "$long": round(location_row["long"], 4),
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
            layer.add_child(folium.Marker(location=[lat, long], popup=popup, icon=folium.Icon(color=marker_colour)))

    def add_sections_to_map(
        self, scout_data: ScoutData, colour: Union[str, dict], marker_data: list, single_section: str = None, layer: str = "Sections", cluster_markers: bool = False, coloured_region: set[str] = None, coloured_region_key: str = "",
    ) -> None:
        """Filter sections and add to map.

        If a single section is specified, plots that section onto the map in
        markers of colour identified by colour, with data indicated by marker_data.

        If else, all sections are plotted from the latest year of data. This
        means all Beaver Colonies, Cub Packs, Scout Troops and Explorer Units,
        that have returned in the latest year of the dataset.

        Args:
            scout_data:
            colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
            marker_data: List of strings which determines content for popup, including:
                - youth membership
                - awards
            single_section: One of Beavers, Cubs, Scouts, Explorers, Network
            layer: The layer of the map that the sections are added to
            cluster_markers: Should we cluster the markers?
            coloured_region: If specified, markers on the map but not within coloured_region are grey
            coloured_region_key: Column for coloured_region boundary codes

        """
        if single_section:
            filtered_data = scout_data.census_data
            section_types = {getattr(scout_census.column_labels.sections, single_section).type}
        else:
            filtered_data = scout_data.census_data.loc[scout_data.census_data["Year"] == scout_data.census_data["Year"].max()]
            section_types = scout_census.TYPES_GROUP | scout_census.TYPES_DISTRICT
        filtered_data = filtered_data.loc[filtered_data[scout_census.column_labels.UNIT_TYPE].isin(section_types)]
        self.add_meeting_places_to_map(filtered_data, colour, marker_data, layer_name=layer, cluster_markers=cluster_markers, coloured_region=coloured_region, coloured_region_key=coloured_region_key)

    def add_custom_data(self, csv_file_path: Path, layer_name: str, location_cols: Union[Literal["Postcodes"], dict], marker_data: list = None) -> None:
        """Function to add custom data as markers on map

        Args:
            csv_file_path: file path to open csv file
            layer_name: Name of layer that the markers will be added to
            location_cols: Indicates whether adding data with postcodes or co-ordinates
                - if postcodes, str "Postcodes"
                - if co-ordinates, dict of co-ordinate data with keys ["crs", "x", "y"]
            marker_data: list of strings for values in data that should be in popup

        """

        custom_data = pd.read_csv(csv_file_path)

        if location_cols == "Postcodes":
            # Merge with ONS Postcode Directory to obtain dataframe with lat/long
            logger.debug(f"Loading ONS postcode data.")
            ons_pd_data = pd.read_feather(config.SETTINGS.ons_pd.reduced)
            custom_data = pd.merge(custom_data, ons_pd_data, how="left", left_on=location_cols, right_index=True, sort=False)
            location_cols = {"crs": utility.WGS_84, "x": "long", "y": "lat"}

        # Create geo data frame with points generated from lat/long or OS
        custom_data = gpd.GeoDataFrame(custom_data, geometry=gpd.points_from_xy(x=custom_data[location_cols["x"]], y=custom_data[location_cols["y"]]), crs=location_cols["crs"])

        # Convert the 'Co-ordinate reference system' (crs) to WGS_84 (i.e. lat/long) if not already
        if location_cols["crs"] != utility.WGS_84:
            custom_data = custom_data.to_crs(epsg=utility.WGS_84)

        if layer_name in self.map._children:  # NoQA
            raise ValueError("Layer already used!")
        layer = FeatureGroup(name=layer_name, show=True).add_to(self.map)

        # Plot marker and include marker_data in the popup for every item in custom_data
        icon = folium.Icon(color="green")
        if marker_data:
            def add_popup_data(row):
                if not np.isnan(row.geometry.x):
                    layer.add_child(folium.Marker(
                            location=[round(row.geometry.y, 4), round(row.geometry.x, 4)],
                            popup=folium.Popup(html="".join(f'<p align="center">{row[marker_col]}</p>' for marker_col in marker_data), max_width=2650),
                            icon=icon
                    ))
            custom_data.apply(add_popup_data, axis=1)
        else:
            for points in custom_data.geometry[custom_data.geometry.x.notna()].to_list():
                layer.add_child(folium.Marker(location=[round(points.y, 4), round(points.x, 4)], popup=None, icon=icon))

    def save_map(self) -> None:
        """Saves the folium map to a HTML file"""
        self.map.save(f"{self.out_file}")

    def show_map(self) -> None:
        """Show the file at self.out_file in the default browser."""
        webbrowser.open(self.out_file.as_uri())

    def district_colour_mapping(self, scout_data: ScoutData) -> dict[str, Union[str, dict[int, str]]]:
        return _generic_colour_mapping(scout_data, scout_census.column_labels.id.DISTRICT)

    def county_colour_mapping(self, scout_data: ScoutData) -> dict[str, Union[str, dict[int, str]]]:
        return _generic_colour_mapping(scout_data, scout_census.column_labels.id.COUNTY)


def _load_boundary(reports: Reports) -> gpd.GeoDataFrame:
    """Loads a given boundary from a Reports object.

    Loads shapefile from path into GeoPandas dataframe
    Filters out unneeded shapes within all shapes loaded
    Converts from British National Grid to WGS84, as Leaflet doesn't understand BNG

    Args:
        reports: A Reports object with data. This contains shapefile paths, and labels for region codes and names

    Returns:
        GeoDataFrame with filtered and CRS transformed shapes

    """
    code_col = reports.geography.metadata.key  # holds the name of the region class, e.g. oslaua, pcon

    # Read a shape file. shapefile_path is the path to ESRI shapefile with region information
    all_shapes = gpd.read_file(reports.geography.metadata.shapefile.path)
    if reports.geography.metadata.shapefile.key not in all_shapes.columns:
        raise KeyError(f"{reports.geography.metadata.shapefile.key} not present in shapefile. Valid columns are: {all_shapes.columns}")

    # Rename columns
    shapes_col_map = {reports.geography.metadata.shapefile.key: "shape_codes", reports.geography.metadata.shapefile.name: "shape_names"}
    all_shapes.columns = [shapes_col_map.get(col, col) for col in all_shapes.columns]

    # Filter and convert GeoDataFrame to world co-ordinates
    logger.info(f"Filtering {len(all_shapes.index)} shapes by shape_codes being in the {code_col} column of the map_data")
    all_codes = set(reports.data[code_col])
    logger.debug(f"All codes list: \n{all_codes}")
    geo_data = all_shapes.loc[all_shapes["shape_codes"].isin(all_codes), ["geometry", "shape_codes", "shape_names"]].to_crs(epsg=utility.WGS_84)
    logger.info(f"Loaded {len(geo_data.index):,} {code_col} boundary shapes. Columns now in data: {reports.data.columns}.")
    return geo_data


def _generic_colour_mapping(scout_data: ScoutData, grouping_column: str) -> dict[str, Union[str, dict[int, str]]]:
    # fmt: off
    colours = cycle((
        "cadetblue", "lightblue", "blue", "beige", "red", "darkgreen", "lightgreen", "purple",
        "lightgray", "orange", "pink", "darkblue", "darkpurple", "darkred", "green", "lightred",
    ))
    # fmt: on
    grouping_ids = scout_data.census_data[grouping_column].drop_duplicates()
    mapping = {grouping_id: next(colours) for grouping_id in grouping_ids}
    return {"census_column": grouping_column, "mapping": mapping}


def _map_colour_map(properties: dict, column: str, threshold: float, colour_map: colormap.ColorMap) -> str:
    """Returns colour from colour map function and value

    Returns:
        hexadecimal colour value "#RRGGBB"

    """
    area_score = properties.get(column)
    if area_score is None:
        return "#cccccc"  # grey
    if abs(area_score) < threshold:
        return "#ffbe33"  # light yellow
    return colour_map(area_score)


def _map_opacity(properties: dict, column: str, threshold: float) -> float:
    """Decides if a feature's value is important enough to be shown"""
    area_score = properties.get(column)
    if area_score is None:
        return 1
    return 1/3 if abs(area_score) >= threshold else 1/12
