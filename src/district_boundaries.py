import pandas as pd
import geopandas as gpd
import shapely

from src.base import Base
from src.scout_census import ScoutCensus


class DistrictBoundaries(Base):
    def __init__(self, scout_data_object):
        super().__init__()

        self.census_data = scout_data_object.census_data
        self.ons_pd = scout_data_object.ons_pd

    # utility method
    def has_ons_pd_data(self):
        """Finds whether ONS data has been added

        :returns: Whether the Scout Census data has ONS data added
        :rtype: bool
        """
        return self.census_data.has_ons_pd_data()

    def create_district_boundaries(self):
        """
        Creates a GeoJSON file for the District Boundaries of the Scout Census.

        Aims to create a circular boundary around every section of maximal size
        that doesn't overlap or leave gaps between Districts.
        """

        if not self.has_ons_pd_data():
            raise Exception("Must have ons data added before creating district boundaries")

        # Find all the District IDs and names
        districts = self.census_data.data[[ScoutCensus.column_labels['id']["DISTRICT"], ScoutCensus.column_labels['name']["DISTRICT"]]].drop_duplicates()

        # Finds all the records with valid postcodes in the Scout Census
        valid_locations = self.census_data.data.loc[self.census_data.data[ScoutCensus.column_labels['VALID_POSTCODE']] == 1]

        # Creates a new dataframe with a subset of columns resulting in
        # each location being a distinct row
        all_locations = pd.DataFrame(columns=["D_ID", "D_name", "lat", "long"])
        all_locations[["D_name", "Object_ID"]] = valid_locations[["D_name", "Object_ID"]]
        all_locations[["D_ID", "lat", "long"]] = valid_locations[["D_ID", "lat", "long"]].apply(pd.to_numeric, errors='coerce')
        all_locations.drop_duplicates(subset=["lat", "long"], inplace=True)

        # Uses the lat and long co-ords from above to create a GeoDataFrame
        all_points = gpd.GeoDataFrame(all_locations, geometry=gpd.points_from_xy(all_locations.long, all_locations.lat))
        all_points.crs = {'init': 'epsg:4326'}

        # Converts the co-ordinate reference system into OS36 which uses
        # (x-y) coordinates in metres, rather than (long, lat) coordinates.
        all_points = all_points.to_crs({'init': 'epsg:27700'})
        all_points.reset_index(inplace=True)

        self.logger.info(f"Found {len(all_points.index)} different Section points")

        # Calculates all the other points within twice the distance of the
        # closest point from a neighbouring district
        all_points["nearest_points"] = all_points.apply(
            lambda row: self.nearest_other_points(row, all_points.loc[all_points["D_ID"] != row["D_ID"]]), axis=1)
        all_points["buffer_distance"] = 0

        # Initial calcuation of the buffer distances
        self.logger.info(
            "Calculating buffer distances of " + str(all_points["buffer_distance"].value_counts().iloc[0]) + " points")
        all_points["buffer_distance"] = all_points.apply(lambda row: self.buffer_distance(row, all_points), axis=1)
        self.logger.info("On first pass " + str(all_points["buffer_distance"].value_counts().iloc[0]) + " missing buffer distance")

        old_number = all_points["buffer_distance"].value_counts().iloc[0]
        new_number = 0
        # The algorithm is iterative, so stop when no more points have their
        # buffers identified
        while new_number < old_number:
            old_number = all_points["buffer_distance"].value_counts().iloc[0]
            all_points["buffer_distance"] = all_points.apply(lambda row: self.buffer_distance(row, all_points), axis=1)
            new_number = all_points["buffer_distance"].value_counts().iloc[0]
            self.logger.info(f"On next pass {new_number} missing buffer distance")
            _ = all_points.loc[all_points["buffer_distance"] == 0]
            self.logger.debug(f"The following points do not have buffer distances defined:\n{_}")

        # Create the GeoDataFrame that will form the GeoJSON
        output_columns = ["id", "name"]
        output_gpd = gpd.GeoDataFrame(columns=output_columns)
        district_nu = 0
        for count, district in districts.iterrows():
            if str(district["D_ID"]) != "nan":
                district_nu += 1
                data = {
                    "id": [district["D_ID"]],
                    "name": [district["D_name"]]
                }
                self.logger.info(f"{district_nu}/{len(districts)} calculating boundary of {district['D_name']}")

                district_points = all_points.loc[all_points["D_ID"] == district["D_ID"]]

                # For each of the points in the district, produces a polygon to
                # represent the buffered point from the buffer distances
                # calculated above
                buffered_points = district_points.apply(lambda row: row["geometry"].buffer(row["buffer_distance"]), axis=1)

                # Unifies the polygons created from each point in the District
                # into one polygon for the District.
                district_polygon = shapely.ops.unary_union(buffered_points)

                data_df = gpd.GeoDataFrame(data, columns=output_columns, geometry=[district_polygon])
                output_gpd = gpd.GeoDataFrame(pd.concat([output_gpd, data_df], axis=0, sort=False))

        output_gpd.crs = {'init': 'epsg:27700'}

        # Convert co-ordinates back to WGS84, which uses latitude and longditude
        output_gpd = output_gpd.to_crs({'init': 'epsg:4326'})
        output_gpd.reset_index(drop=True, inplace=True)

        self.logger.debug(f"output gpd\n{output_gpd}")
        output_gpd[["id"]] = output_gpd[["id"]].apply(pd.to_numeric, errors='coerce')
        self.logger.debug(f"output gpd\n{output_gpd}")
        output_gpd.to_file("districts_buffered.geojson", driver='GeoJSON')

    def buffer_distance(self, point_details, all_points):
        obj_id = point_details["Object_ID"]
        self.logger.debug(f"Finding buffer distance of {point_details.index} with object ID {obj_id}")
        distance = 0
        nearest_points = point_details["nearest_points"]
        if point_details["buffer_distance"] == 0:
            valid = True
            for nearby_point in nearest_points:
                point_obj = nearby_point["Point"]
                buffer = self.buffer_distance_from_point(point_obj, all_points)
                if buffer != 0:
                    new_distance = nearby_point["Distance"] - buffer
                    if distance == 0:
                        distance = new_distance
                    elif new_distance < distance:
                        distance = new_distance
                else:
                    if (distance == 0) or (distance > (nearby_point["Distance"] / 2)):
                        # Decide if these two points are a 'pair'.
                        # I.e. if the restricting factor is just their
                        # mutual closeness.
                        nearby_point_details = all_points.loc[all_points["geometry"] == point_obj]
                        nearest_to_nearby = nearby_point_details["nearest_points"].iloc[0]
                        unset_nearby = [p["Point"] for p in nearest_to_nearby if self.buffer_distance_from_point(p["Point"], all_points) == 0]
                        if unset_nearby:
                            closer_set = []
                            ii = 0
                            while nearest_to_nearby[ii]["Point"] != unset_nearby[0]:
                                closer_set.append(nearest_to_nearby[ii])
                                ii += 1
                            buffers = [self.buffer_distance_from_point(p["Point"], all_points) for p in closer_set]
                            if 0 in buffers:
                                # Means that there is a closer point with no buffer defined
                                valid = False
                            elif buffers and (max(buffers) > nearby_point["Distance"] / 2):
                                # Means that there is closer point with a buffer big enough to make a difference
                                valid = False
                            else:
                                if unset_nearby[0] == point_details["geometry"]:
                                    # The closest unset point to this near point we are considering is the original point
                                    distance = nearby_point["Distance"] / 2
                                else:
                                    valid = False
            if not valid:
                distance = 0
        else:
            distance = point_details["buffer_distance"]
        return distance

    @staticmethod
    def buffer_distance_from_point(point, all_points):
        """
        Find the distance recorded using the point as the key

        :param shapely.Point point: Point interested in
        :param GeoDataFrame all_points: DataFrame containing 'buffer_distance' column

        :returns float: Distance recorded as buffer from point
        """
        point_details = all_points.loc[all_points["geometry"] == point]
        buffer = point_details["buffer_distance"].iloc[0]
        return buffer

    def nearest_other_points(self, row, other_data):
        """
        Given a row of a GeoDataFrame and a subset of a GeoDataFrame returns
        the points and corresponding distances for all points with twice
        the minimum distance from the row to the subset.

        :param DataSeries row: Row of a GeoDataFrame
        :param DataFrame other_data: Other rows of a GeoDataFrame

        :returns list: Sorted list of dictionaries containing points and distances
        """
        point = row["geometry"]
        self.logger.debug("nearest_other_points:" + str(row.index))
        other_points = shapely.geometry.MultiPoint(other_data["geometry"].tolist())
        distance = point.distance(other_points)*2
        points = [{"Point": p, "Distance": point.distance(p)} for p in other_points if point.distance(p) < distance]
        points.sort(key=lambda i: i["Distance"])
        self.logger.debug(points)
        return points
