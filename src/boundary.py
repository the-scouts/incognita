import pandas as pd
import geopandas as gpd
import shapely

from src.base import Base
# For type hints
from src.ons_pd import ONSPostcodeDirectory


# noinspection PyUnresolvedReferences
class Boundary(Base):
    """Stores information about the geography type currently used and methods for manipulation

    :var dict Boundary.SECTION_AGES: Holds information about scout sections
    """

    def __init__(self, geography_name: str, ons_pd_object: ONSPostcodeDirectory):
        super().__init__(settings=True)

        self.boundary_dict = None
        self.boundary_regions_data = None

        self.set_boundary(geography_name, ons_pd_object)

    @property
    def shapefile_key(self):
        return self.boundary_dict["boundary"]["key"].upper()  # TODO TEMP MEASURE DUE TO DATAFILE ERR

    @property
    def shapefile_name_column(self):
        return self.boundary_dict["boundary"]["name"]

    @property
    def shapefile(self):
        return self.boundary_dict["boundary"]["shapefile"]

    def set_boundary(self, geography_name, ons_pd):
        """Sets the boundary_dict and boundary_regions_data members

        :param str geography_name: The type of boundary, e.g. lsoa11, pcon etc. Must be a key in ONSPostcodeDirectory.BOUNDARIES.
        :param ONSPostcodeDirectory ons_pd: An ONS Postcode Directory object

        :var dict self.boundary_dict: information about the boundary type
        :var self.boundary_regions_data: table of region codes and human-readable names for those codes

        :returns None: Nothing
        """
        self.logger.info(f"Setting the boundary to {geography_name}")

        # Combine the ONS and Scout boundaries directories
        boundaries_dict = {**ons_pd.BOUNDARIES, **self.settings["Scout Mappings"]}
        if geography_name in boundaries_dict.keys():
            self.boundary_dict = boundaries_dict[geography_name]
            boundary_codes_dict = self.boundary_dict["codes"]

            self.boundary_regions_data = pd.read_csv(
                boundary_codes_dict.get("path"),  # Names & Codes file path
                dtype={
                    boundary_codes_dict["key"]: boundary_codes_dict["key_type"],
                    boundary_codes_dict["name"]: "object"
                })
        else:
            raise Exception(f"{geography_name} is an invalid boundary.\nValid boundaries include: {boundaries_dict.keys()}")

    def filter_boundaries_regions_data(self, field, value_list, ons_pd_object):
        """Filters the boundary_regions_data table by if the area code is within both value_list and the census_data table.

        Requires set_boundary to have been called.
        Uses ONS Postcode Directory to find which of set boundaries are within
        the area defined by the value_list.

        :param str field: The field on which to filter
        :param list value_list: The values on which to filter

        :returns None: Nothing
        """

        if not self.boundary_dict:
            raise Exception("boundary_dict has not been set, or there is no data in it")  # Has Boundary.set_boundary() been called?

        name = self.boundary_dict["name"]
        codes_key = self.boundary_dict["codes"]["key"]

        self.logger.info(f"Filtering {len(self.boundary_regions_data.index)} {name} boundaries by {field} being in {value_list}")
        # Filters ons data table if field column is in value_list. Returns ndarray of unique area codes
        boundary_subset = ons_pd_object.ons_field_mapping(field, value_list, name)
        self.logger.debug(f"This corresponds to {len(boundary_subset)} {name} boundaries")

        # Filters the boundary names and codes table by areas within the boundary_subset list
        self.boundary_regions_data = self.boundary_regions_data.loc[self.boundary_regions_data[codes_key].isin(boundary_subset)]
        self.logger.info(f"Resulting in {len(self.boundary_regions_data.index)} {name} boundaries")

    def filter_boundaries_by_scout_area(self, scout_data, boundary, column, value_list, ons_pd=None):
        """Filters the boundaries, to include only those boundaries which have
        Sections that satisfy the requirement that the column is in the value_list.

        :param ScoutData scout_data: ScoutData object with data to operate on
        :param str boundary: ONS boundary to filter on
        :param str column: Scout boundary (e.g. C_ID)
        :param list value_list: List of values in the Scout boundary
        """
        ons_pd = scout_data.ons_pd if ons_pd is None else ons_pd  # TODO Remove - Temporary hack
        ons_value_list = self.ons_from_scout_area(scout_data, boundary, column, value_list)
        self.filter_boundaries_regions_data(boundary, ons_value_list, ons_pd)

    def filter_boundaries_near_scout_area(self, scout_data, boundary, field, value_list):
        """Filters boundary list to those boundaries containing a scout unit matching requirements, or boundaries
        partially or fully within three kilometres of the external border (convex hull)

        #TODO investigate some method of actually finding a boundry's neighbours.

        :param ScoutData scout_data: ScoutData object with data to operate on
        :param str boundary: ONS boundary to filter on
        :param str field: Scout boundary (e.g. C_ID)
        :param list value_list: List of values in the Scout boundary
        """
        # Extend by 3000 metres
        distance = 3000

        # Reduce columns in dataset to minimum requirements
        reduced_points = scout_data.data[[field, boundary, "lat", "long"]]

        self.logger.info("Creates geometry")
        data_with_points = gpd.GeoDataFrame(reduced_points, geometry=gpd.points_from_xy(reduced_points.long, reduced_points.lat))
        data_with_points = data_with_points.drop(['lat', 'long'], axis=1)

        # Pivots the co-ordinate reference system into OS36 which uses
        # (x-y) coordinates in metres, rather than (long, lat) coordinates.
        data_with_points.crs = {'init': 'epsg:4326'}
        data_with_points = data_with_points.to_crs({'init': 'epsg:27700'})
        # TODO work out way to avoid co-ordinate pivot (i.e. convert 3km into GPS co-ords)

        self.logger.info(f"Filters for records that satify {field} in {value_list}")
        filtered_points = data_with_points.loc[data_with_points[field].isin(value_list)]
        self.logger.info(f"Resulting in {len(reduced_points.index)} number of Sections")

        self.logger.info(f"Creating area of interest")
        # Finds the outer boundary of all selected scout units and extends by `distance` in all directions to
        # incorporate nearby regions
        in_area = shapely.geometry.MultiPoint(filtered_points["geometry"].to_list()).convex_hull.buffer(distance)
        self.logger.info(f"Is result valid {in_area.geom_type}? {in_area.is_valid}. Area is {in_area.area}")

        self.logger.info(f"Finding Sections in buffered area of interest")

        nearby_values = data_with_points[data_with_points.geometry.within(in_area)][boundary]
        self.logger.info(f"Found {len(nearby_values)} Sections nearby")
        nearby_values = nearby_values.drop_duplicates().to_list()
        self.logger.info(f"Found {nearby_values}")

        self.filter_boundaries_regions_data(boundary, nearby_values, scout_data.ons_pd)

    def ons_from_scout_area(self, scout_data, ons_code, column, value_list):
        """Produces list of ONS Geographical codes that exist within a subset
        of the Scout Census data.

        :param ScoutData scout_data: ScoutData object with data to operate on
        :param str ons_code: A field of the ONS Postcode Directory
        :param str column: A field of the Scout Census data
        :param list value_list: Values to accept

        :returns list: List of ONS Geographical codes of type ons_code.
        """
        self.logger.info(f"Finding the ons areas that exist with {column} in {value_list}")

        records = scout_data.data.loc[scout_data.data[column].isin(value_list)]
        self.logger.debug(f"Found {len(records.index)} records that match {column} in {value_list}")

        records = records[records != scout_data.DEFAULT_VALUE]
        ons_codes = records[ons_code].drop_duplicates().dropna().to_list()
        self.logger.debug(f"Found clean {len(ons_codes)} {ons_code}s that match {column} in {value_list}")

        return ons_codes
