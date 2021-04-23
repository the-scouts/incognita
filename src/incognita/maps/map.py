from __future__ import annotations

from itertools import cycle
from pathlib import Path
import time
from string import Template
from typing import Any, Literal, Union
import webbrowser

import geopandas as gpd
import numpy as np
import pandas as pd

from incognita.data import scout_census
from incognita.data.scout_data import ScoutData
from incognita.logger import logger
from incognita.reports.reports import Reports
from incognita.utility import config
from incognita.utility import utility


class Map:
    """This class enables easy plotting of maps with a shape file.

    Attributes:
        map: holds the folium map object

    """
    template = Path(__file__).parent / "template.html"

    def __init__(self, map_name: str, map_title: str):
        """Initialise Map class.

        Args:
            map_name: Filename for the saved map

        """
        logger.info("Initialising leaflet map")
        self.map: dict[str, Any] = {"map_title": map_title}
        self.out_file = config.SETTINGS.folders.output / f"{map_name}.html"

    def add_areas(
        self,
        var_col: str,
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
            var_col: Data column to use for choropleth colour values
            tooltip: Mouseover tooltip for each boundary (e.g. "% Change 6-18")
            layer_name: Legend key for the layer (e.g. "% Change 6-18 (Counties)")
            reports:
            show: If True, show the layer by default
            scale_index: Allows a fixed value scale - colour indices
            scale_step_boundaries: Fixed scale step boundary indices
            significance_threshold: If an area's value is significant enough to be displayed

        """
        if var_col not in reports.data.columns:
            logger.error(f"{var_col} is not a valid column in the data. \n" f"Valid columns include {reports.data.columns}")
            raise KeyError(f"{var_col} is not a valid column in the data.")

        colours = list(reversed(("#4dac26", "#b8e186", "#f1b6da", "#d01c8b")))
        choropleth_data = reports.data[["codes", var_col]].set_index("codes")[var_col]  # contains shapefile paths, and labels for region codes and names
        geo_data = _load_boundary(reports)

        # Set value col properties to use for a particular boundary
        logger.info(f"Setting choropleth column to {var_col} (displayed: {tooltip})")

        non_zero_choropleth_data = choropleth_data[choropleth_data != 0].dropna().sort_values()
        if scale_step_boundaries is None:
            quantiles = (0, 20, 40, 60, 80, 100)
            scale_step_boundaries = [np.percentile(non_zero_choropleth_data, q) for q in quantiles]
        colour_map_id = "0"
        self.map["colour_map"] = _output_colour_scale(colour_map_id, layer_name, colours, domain=(min(non_zero_choropleth_data), max(non_zero_choropleth_data)), classes=scale_step_boundaries)

        logger.info(f"Colour scale boundary values {scale_step_boundaries}")

        logger.info(f"Merging geo_json on shape_codes from shapefile with codes from boundary report")
        merged_data = geo_data.merge(choropleth_data, how="left", left_on="shape_codes", right_index=True).drop_duplicates()
        if len(merged_data.index) == 0:
            logger.error("Data unsuccessfully merged resulting in zero records")
            raise RuntimeError("Data unsuccessfully merged resulting in zero records")

        # TODO layer show/hide by default
        self.map[f"layer_{layer_name}"] = _output_shape_layer(
            legend_key=layer_name,  # the name of the Layer, as it will appear in the layer controls
            colour_data=merged_data.set_index("shape_codes")[var_col].to_dict(),
            api_base="https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_Layer_Super_Output_Areas_DEC_2011_EW_BSC_V3/FeatureServer/0/query?",
            query_params={"outFields": "LSOA11CD,LSOA11NM"},  # TODO where do I get this value from?
            colour_scale_id=colour_map_id,
            threshold=significance_threshold,
            code_col="LSOA11CD",  # TODO where do I get this value from?
            name_col="LSOA11NM",  # TODO where do I get this value from?
            measure_name=tooltip,
        )

    def add_meeting_places_to_map(
        self,
        sections: pd.DataFrame,
        colour: Union[str, dict],
        marker_data: set[str],
        layer_name: str = "Sections",
        cluster_markers: bool = False,
        show_layer: bool = True,
        coloured_region: set[str] = None,
        coloured_region_key: str = "",
    ) -> None:
        """Adds the sections provided as markers to map with the colour, and data
        indicated by marker_data.

        Args:
            sections: Census records relating to Sections with lat and long Columns
            colour: Colour for markers. If str all the same colour, if dict, must have keys that are District IDs
            marker_data: Set of strings which determines content for popup, including:
                - youth membership
                - awards
            layer_name: Name of map layer for meeting places. Default = "Sections"
            cluster_markers: Whether to cluster markers on the map
            show_layer: Whether to show the layer by default
            coloured_region: If specified, markers on the map but not within coloured_region are grey
            coloured_region_key: Column for coloured_region boundary codes

        """
        logger.info("Adding section markers to map")

        # check that sections dataframe has data, and that there are any sections
        if sections.empty or (sections[scout_census.column_labels.id.DISTRICT].dropna().empty and sections[scout_census.column_labels.id.GROUP].dropna().empty):
            return

        # Sort sections dataframe
        sections = sections.sort_values(scout_census.column_labels.id.OBJECT).reset_index(drop=True)

        if layer_name in self.map:
            raise ValueError("Layer already used!")

        # Sets the map so that it opens in the right area
        valid_points = sections.loc[sections[scout_census.column_labels.VALID_POSTCODE] == 1, ["lat", "long"]]
        self.map["bounds"] = _output_fit_bounds(((valid_points.lat.min(), valid_points.long.min()), (valid_points.lat.max(), valid_points.long.max())))

        section_names = sections["name"].astype(str)

        if "youth membership" in marker_data:
            section_type = sections[scout_census.column_labels.UNIT_TYPE].map(utility.section_types)
            yp_total_cols = [section_model.total for section_name, section_model in scout_census.column_labels.sections]
            yp_totals = sections[yp_total_cols].sum(axis=1).astype(int).astype(str)  # Each row only has values for one section type
            sections["sect_overview"] = section_names + " : " + yp_totals + " " + section_type
        else:
            sections["sect_overview"] = section_names

        if "awards" in marker_data:
            # This uses just the first top award - so only Diamond/QSA for Explorers/Network
            top_award_cols = [section_model.top_award[0] for section_name, section_model in scout_census.column_labels.sections]
            awards = sections[top_award_cols].sum(axis=1).astype(int).astype(str)
            award_eligible_cols = [section_model.top_award_eligible[0] for section_name, section_model in scout_census.column_labels.sections]
            eligible = sections[award_eligible_cols].sum(axis=1).astype(int).astype(str)
            sections["awards_info"] = section_names + " : " + awards + " Top Awards out of " + eligible + " eligible"

        sections["marker_colour"] = sections[colour["census_column"]].map(colour["mapping"]) if isinstance(colour, dict) else colour
        if coloured_region_key and coloured_region is not None:
            # Areas outside the region_of_colour have markers coloured grey
            sections.loc[~sections[coloured_region_key].isin(coloured_region), "marker_colour"] = "gray"

        sections["postcode"] = sections[scout_census.column_labels.POSTCODE]
        sections["c_name"] = sections[scout_census.column_labels.name.COUNTY]
        sections["d_name"] = sections[scout_census.column_labels.name.DISTRICT]
        sections["g_name"] = sections[scout_census.column_labels.name.GROUP].astype(str).fillna("District")

        sections_info_cols = ["postcode", "lat", "long", "marker_colour", "c_name", "d_name", "g_name", "sect_overview"]
        if "awards" in marker_data:
            sections_info_cols += ["awards_info"]
        sections_info_table = sections[sections_info_cols].dropna(subset=["d_name"]).dropna(subset=["postcode"])

        # else the final marker would not be added
        last_row = pd.Series(sections_info_table.iloc[0].to_dict() | {"postcode": "~ FINAL"}, name=0)
        sections_info_table = sections_info_table.append(last_row)

        # set and sort index
        sections_info_table = sections_info_table.set_index(["postcode", "d_name", "g_name"], drop=True).sort_index(level=[0, 1, 2])

        # pre-calculate inner loop vars
        include_awards_data = "awards" in marker_data

        # initialise change-detector variables
        old_postcode = sections_info_table.index[0][0]
        old_district_name = ""
        reset_district = False

        # initialise first marker variables
        html = ""
        lat = round(sections_info_table["lat"].array[0], 4)
        long = round(sections_info_table["long"].array[0], 4)
        marker_colour = sections_info_table["marker_colour"].array[0]

        # Find all the sections with the same postcode:
        out = []
        for (postcode, district_name, group_name), sub_table in sections_info_table.groupby(level=[0, 1, 2]):
            if old_postcode != postcode:
                # Add a marker each time the postcode changes.
                out.append({"lat": lat, "lon": long, "col": marker_colour, "html": html})

                old_postcode = postcode  # update the old postcode
                lat = round(sub_table["lat"].array[0], 4)
                long = round(sub_table["long"].array[0], 4)
                marker_colour = sub_table["marker_colour"].array[0]

                # reset HTML string and mark district name for re-adding
                html = ""
                reset_district = True

            if old_district_name != district_name or reset_district:
                old_district_name = district_name
                reset_district = False

                county_name = sub_table["c_name"].array[0]

                # District sections first followed by Group sections
                html += f"<h3>{district_name} ({county_name})</h3>"

            html += f"<h4>{group_name}</h4><p align='center'>"
            html += "<br>".join(sub_table["sect_overview"])
            if include_awards_data and group_name != "District":
                awards_info = "<br>".join(sub_table["awards_info"])
                html += "<br>" + awards_info
            html += "</p>"
        # TODO marker cluster/feature group
        self.map[layer_name] = _output_marker_layer(layer_name, out)

    def add_sections_to_map(
        self,
        scout_data: ScoutData,
        colour: Union[str, dict],
        marker_data: set[str],
        single_section: str = None,
        layer: str = "Sections",
        cluster_markers: bool = False,
        coloured_region: set[str] = None,
        coloured_region_key: str = "",
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
        self.add_meeting_places_to_map(filtered_data, colour, marker_data, layer, cluster_markers, coloured_region=coloured_region, coloured_region_key=coloured_region_key)

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

        # Plot marker and include marker_data in the popup for every item in custom_data
        out = []
        if marker_data:
            x_not_nan = custom_data.geometry.x.notna()
            for row in custom_data[x_not_nan].itertuples():
                out.append(
                    {
                        "lat": round(row.geometry.y, 4),
                        "lon": round(row.geometry.x, 4),
                        "col": "green",
                        "html": "".join(f'<p align="center">{row[marker_col]}</p>' for marker_col in marker_data)
                    }
                )
        else:
            for points in custom_data.geometry[custom_data.geometry.x.notna()].to_list():
                out.append({"lat": round(points.y, 4), "lon": round(points.x, 4), "col": "green", "html": ""})
        self.map[layer_name] = _output_marker_layer(layer_name, out)

    def save_map(self) -> None:
        """Writes the map and saves to a HTML file"""
        template = MapTemplate(Map.template.read_text(encoding="utf-8"))
        map_title = self.map.pop("map_title")
        funcs = "\n" + "".join(self.map.values())
        self.out_file.write_text(template.substitute(title=map_title, functions=funcs), encoding="utf-8")

    def show_map(self) -> None:
        """Show the file at self.out_file in the default browser."""
        webbrowser.open(self.out_file.as_uri())

    @staticmethod
    def district_colour_mapping(scout_data: ScoutData) -> dict[str, Union[str, dict[int, str]]]:
        return _generic_colour_mapping(scout_data, scout_census.column_labels.id.DISTRICT)

    @staticmethod
    def county_colour_mapping(scout_data: ScoutData) -> dict[str, Union[str, dict[int, str]]]:
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
    # Read a shape file. shapefile_path is the path to ESRI shapefile with region information
    logger.info("Loading Shapefile data")
    logger.debug(f"Shapefile path: {reports.geography.metadata.shapefile.path}")
    start_time = time.time()
    all_shapes = gpd.read_file(reports.geography.metadata.shapefile.path)
    logger.info(f"Loading Shapefile data finished, {time.time() - start_time:.2f} seconds elapsed")
    if reports.geography.metadata.shapefile.key not in all_shapes.columns:
        raise KeyError(f"{reports.geography.metadata.shapefile.key} not present in shapefile. Valid columns are: {all_shapes.columns}")

    # Rename columns
    shapes_col_map = {reports.geography.metadata.shapefile.key: "shape_codes", reports.geography.metadata.shapefile.name: "shape_names"}
    all_shapes.columns = [shapes_col_map.get(col, col) for col in all_shapes.columns]

    # Filter and convert GeoDataFrame to world co-ordinates
    logger.info(f"Filtering {len(all_shapes.index)} shapes by shape_codes being in the codes column of the map_data")
    all_codes = set(reports.data["codes"])
    logger.debug(f"All codes list: {all_codes}")
    geo_data = all_shapes.loc[all_shapes["shape_codes"].isin(all_codes), ["geometry", "shape_codes", "shape_names"]].to_crs(epsg=utility.WGS_84)
    logger.info(f"Loaded {len(geo_data.index):,} boundary shapes. Columns now in data: {[*reports.data.columns]}.")
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


def _output_fit_bounds(bounds: tuple[tuple[float, float], tuple[float, float]]) -> str:
    south_west, north_east = bounds
    return f"""
    // Set map bounds
    setBounds({[list(south_west), list(north_east)]})
    """


def _output_colour_scale(unique_id: str, legend_caption: str, colours: list[str], domain: tuple[int, int], classes: list[int]) -> str:
    return f"""
    // Create colour scale
    const colourScale{unique_id} = chroma.scale({colours}).domain({list(domain)}).classes({classes})
    createLegend("{legend_caption}", colourScale{unique_id})
    """


def _output_shape_layer(legend_key: str, colour_data: dict[str, int], api_base: str, query_params: dict[str, str], colour_scale_id, threshold: float, code_col, name_col, measure_name) -> str:
    # query params reference: https://developers.arcgis.com/rest/services-reference/query-feature-service-layer-.htm#GUID-62EE7495-8688-4BD0-B433-89F7E4476673

    return f"""
    // Add boundary shapes
    createShapeLayer(
        "{legend_key}",
        {colour_data},
        "{api_base}",
        {query_params},
        colourScale{colour_scale_id},
        {threshold},
        "{code_col}",
        "{name_col}",
        "{measure_name}",
    )
    """


def _output_marker_layer(legend_key: str, marker_data: list[dict[str, Union[float, str]]]) -> str:
    # marker_data is lists of dicts of lat, lon, colour, html
    return f"""
    // Add location markers
    addMarkers(
        "{legend_key}",
        {marker_data},
    )
    """


class MapTemplate(Template):
    delimiter = "¦"
