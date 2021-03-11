from __future__ import annotations

from typing import TYPE_CHECKING

import geopandas as gpd
import pandas as pd
import shapely.geometry

from incognita import utility
from incognita.logger import logger

if TYPE_CHECKING:
    from pathlib import Path

    from incognita.data.ons_pd import ONSPostcodeDirectory
    from incognita.data.scout_data import ScoutData


class Geography:
    """Stores information about the (administrative) geography type currently used and methods for selecting and
    excluding regions.

    :var dict Geography.SECTION_AGES: Holds information about scout sections
    """

    def __init__(self, geography_name: str, ons_pd_object: ONSPostcodeDirectory):
        self.geography_metadata_dict = None
        self.geography_region_ids_mapping = None

        self._set_boundary(geography_name, ons_pd_object)

    @property
    def type(self) -> str:
        return self.geography_metadata_dict.get("name")

    @property
    def codes_map_key(self) -> str:
        return self.geography_metadata_dict["codes"]["key"]

    @property
    def codes_map_key_type(self) -> str:
        return self.geography_metadata_dict["codes"]["key_type"]

    @property
    def codes_map_path(self) -> Path:
        return utility.DATA_ROOT / self.geography_metadata_dict["codes"].get("path")

    @property
    def codes_map_name(self) -> str:
        return self.geography_metadata_dict["codes"]["name"]

    @property
    def shapefile_key(self) -> str:
        return self.geography_metadata_dict["boundary"]["key"]

    @property
    def shapefile_name(self) -> str:
        return self.geography_metadata_dict["boundary"]["name"]

    @property
    def shapefile_path(self) -> Path:
        shapefiles_root = utility.DATA_ROOT / utility.SETTINGS["Boundaries folder"]
        return shapefiles_root / self.geography_metadata_dict["boundary"]["shapefile"]

    @property
    def age_profile_path(self) -> Path:
        age_profiles_root = utility.DATA_ROOT / utility.SETTINGS["National Statistical folder"]
        return age_profiles_root / self.geography_metadata_dict["age_profile"].get("path")

    @property
    def age_profile_key(self) -> str:
        return self.geography_metadata_dict["age_profile"].get("key")

    @property
    def age_profile_pivot(self) -> str:
        return self.geography_metadata_dict["age_profile"].get("pivot_key")

    def _set_boundary(self, geography_name: str, ons_pd: ONSPostcodeDirectory):
        """Sets the geography_metadata_dict and geography_region_ids_mapping members

        :param str geography_name: The type of boundary, e.g. lsoa11, pcon etc. Must be a key in ONSPostcodeDirectory.BOUNDARIES.
        :param ONSPostcodeDirectory ons_pd: An ONS Postcode Directory object

        :var dict self.geography_metadata_dict: information about the boundary type
        :var self.geography_region_ids_mapping: table of region codes and human-readable names for those codes

        :returns None: Nothing
        """
        logger.info(f"Setting the boundary to {geography_name}")

        # Combine the ONS and Scout boundaries directories
        boundaries_dict = ons_pd.BOUNDARIES | utility.SETTINGS["Scout Mappings"]
        if geography_name in boundaries_dict.keys():
            self.geography_metadata_dict = boundaries_dict[geography_name]

            # Names & Codes file path
            self.geography_region_ids_mapping = pd.read_csv(self.codes_map_path, dtype={self.codes_map_key: self.codes_map_key_type, self.codes_map_name: "string"})
        else:
            raise Exception(f"{geography_name} is an invalid boundary.\nValid boundaries include: {boundaries_dict.keys()}")

    def _get_ons_codes_from_scout_area(self, scout_data: ScoutData, ons_code: str, column: str, value_list: list) -> list:
        """Produces list of ONS Geographical codes that exist within a subset
        of the Scout Census data.

        :param ScoutData scout_data: ScoutData object with data to operate on
        :param str ons_code: A field of the ONS Postcode Directory
        :param str column: A field of the Scout Census data
        :param list value_list: Values to accept

        :returns list: List of ONS Geographical codes of type ons_code.
        """
        logger.info(f"Finding the ons areas that exist with {column} in {value_list}")

        # Filters scout data to values passed through (values in column `column' in `values_list')
        # Gets associated ons code column from filtered records
        records = scout_data.data.loc[scout_data.data[column].isin(value_list), ons_code].drop_duplicates().dropna()
        logger.debug(f"Found {len(records)} records that match {column} in {value_list}")

        # Removes original ons-census merge errors
        ons_codes = records[records != scout_data.DEFAULT_VALUE].to_list()
        logger.debug(f"Found {len(ons_codes)} clean {ons_code}s that match {column} in {value_list}")

        return ons_codes

    def filter_boundaries_regions_data(self, field: str, value_list: list, ons_pd_object: ONSPostcodeDirectory):
        """Filters the geography_region_ids_mapping table by if the area code is within both value_list and the census_data table.

        Requires _set_boundary to have been called.
        Uses ONS Postcode Directory to find which of set boundaries are within
        the area defined by the value_list.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter
        :param ons_pd_object:

        :returns None: Nothing
        """

        boundary_subset = None
        name = self.type

        # Transforms codes from values_list in column 'field' to codes for the current geography
        # 'field' is the start geography and 'name' is the target geography
        # Returns a list
        logger.info(f"Filtering {len(self.geography_region_ids_mapping)} {name} boundaries by {field} being in {value_list}")
        try:
            ons_records_in_value_list = ons_pd_object.data[field].isin(value_list)
            boundary_subset = ons_pd_object.data.loc[ons_records_in_value_list, name].drop_duplicates().to_list()
        except AttributeError:
            msg = "No data in ONS PD object. Ensure ScoutData object is created with load_ons_pd_data being True"
            logger.exception(msg)
            raise AttributeError(msg) from None
        except KeyError:
            msg = f"{name} not in ONS PD dataframe. \nValid values are: {ons_pd_object.data.columns.to_list()}"
            logger.error(msg)
            raise KeyError(msg) from None
        logger.debug(f"This corresponds to {len(boundary_subset)} {name} boundaries")

        # Filters the boundary names and codes table to only areas within the boundary_subset list
        geog_region_ids_in_boundary_subset = self.geography_region_ids_mapping[self.codes_map_key].isin(boundary_subset)
        self.geography_region_ids_mapping = self.geography_region_ids_mapping.loc[geog_region_ids_in_boundary_subset]
        logger.info(f"Resulting in {len(self.geography_region_ids_mapping)} {name} boundaries")

    def filter_boundaries_by_scout_area(self, scout_data: ScoutData, ons_pd: ONSPostcodeDirectory, boundary: str, column: str, value_list: list):
        """Filters the boundaries, to include only those boundaries which have
        Sections that satisfy the requirement that the column is in the value_list.

        :param ScoutData scout_data: ScoutData object with data to operate on
        :param ONSPostcodeDirectory ons_pd:
        :param str boundary: ONS boundary to filter on
        :param str column: Scout boundary (e.g. C_ID)
        :param list value_list: List of values in the Scout boundary
        """
        ons_value_list = self._get_ons_codes_from_scout_area(scout_data, boundary, column, value_list)
        self.filter_boundaries_regions_data(boundary, ons_value_list, ons_pd)

    def filter_boundaries_near_scout_area(self, scout_data: ScoutData, boundary: str, field: str, value_list: list, distance: int = 3000):
        """Filters boundary list to those boundaries containing a scout unit matching requirements, or boundaries
        partially or fully within three kilometres of the external border (convex hull)

        TODO investigate some method of actually finding a boundary's neighbours.

        :param ScoutData scout_data: ScoutData object with data to operate on
        :param str boundary: ONS boundary to filter on
        :param str field: Scout boundary (e.g. C_ID)
        :param list value_list: List of values in the Scout boundary
        :param int distance: How far to extend the buffer by
        """

        # Reduce columns in dataset to minimum requirements
        reduced_points = scout_data.data[[field, boundary, "lat", "long"]]

        logger.info("Creates geometry")
        data_with_points = gpd.GeoDataFrame(reduced_points, geometry=gpd.points_from_xy(reduced_points.long, reduced_points.lat))
        data_with_points = data_with_points.drop(["lat", "long"], axis=1)

        # Pivots the co-ordinate reference system into OS36 which uses
        # (x-y) coordinates in metres, rather than (long, lat) coordinates.
        data_with_points.crs = f"epsg:{utility.WGS_84}"
        data_with_points = data_with_points.to_crs(f"epsg:{utility.BNG}")
        # TODO work out way to avoid co-ordinate pivot (i.e. convert 3km into GPS co-ordinates)

        logger.info(f"Filters for records that satisfy {field} in {value_list}")
        filtered_points = data_with_points.loc[data_with_points[field].isin(value_list)]
        logger.info(f"Resulting in {len(reduced_points.index)} number of Sections")

        logger.info(f"Creating area of interest")
        # Finds the outer boundary of all selected scout units and extends by `distance` in all directions to
        # incorporate nearby regions
        in_area = shapely.geometry.MultiPoint(filtered_points["geometry"].to_list()).convex_hull.buffer(distance)
        logger.info(f"Is result valid {in_area.geom_type}? {in_area.is_valid}. Area is {in_area.area}")

        logger.info(f"Finding Sections in buffered area of interest")

        nearby_values = data_with_points[data_with_points.geometry.within(in_area)][boundary]
        logger.info(f"Found {len(nearby_values)} Sections nearby")
        nearby_values = nearby_values.drop_duplicates().to_list()
        logger.info(f"Found {nearby_values}")

        self.filter_boundaries_regions_data(boundary, nearby_values, scout_data.ons_pd)
