import geopandas as gpd
import pandas as pd
import pygeos.constructive
import shapely.geometry
import shapely.ops

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import constants


def create_district_boundaries(census_data: pd.DataFrame) -> None:
    """Creates a GeoJSON file for the District Boundaries of the Scout Census.

    Aims to create a circular boundary around every section of maximal size
    that doesn't overlap or leave gaps between Districts.
    """

    # Find all the District IDs and names
    districts = census_data[[scout_census.column_labels.id.DISTRICT, scout_census.column_labels.name.DISTRICT]].drop_duplicates()

    # Finds all the records with valid postcodes in the Scout Census
    all_locations = census_data.loc[census_data[scout_census.column_labels.VALID_POSTCODE], ["D_ID", "D_name", "lat", "long", "clean_postcode", "Object_ID"]].drop_duplicates(subset=["lat", "long"]).reset_index(drop=True)

    # Uses the lat and long co-ordinates from above to create a GeoDataFrame
    points = gpd.points_from_xy(all_locations["long"], all_locations["lat"])
    all_points = gpd.GeoDataFrame(all_locations, geometry=points, crs=constants.WGS_84)

    # Converts the co-ordinate reference system into OS36 which uses
    # (x-y) coordinates in metres, rather than (long, lat) coordinates.
    all_points = all_points.to_crs(epsg=constants.BNG)

    logger.info(f"Found {len(all_points.index)} different Section points")

    # Calculates all the other points within twice the distance of the
    # closest point from a neighbouring district
    all_points["nearest_points"] = all_points.apply(lambda row: _nearest_other_points(row, all_points), axis=1)
    all_points["indexes_of_interest"] = all_points.apply(lambda row: _indexes_of_interest(row, all_points), axis=1)
    all_points["buffer_distance"] = 0

    # Initial calculation of the buffer distances
    logger.info(f"Calculating buffer distances of {sum(all_points['buffer_distance'] == 0)} points")
    all_points["buffer_distance"] = all_points.apply(lambda row: _buffer_distance(row, all_points), axis=1)
    logger.info(f"On first pass {sum(all_points['buffer_distance'] == 0)} missing buffer distance")

    old_number = sum(all_points["buffer_distance"] == 0)
    new_number = 1
    # The algorithm is iterative, so stop when no more points have their
    # buffers identified
    while (new_number < old_number) and (new_number > 0):
        old_number = sum(all_points["buffer_distance"] == 0)
        all_points["buffer_distance"] = all_points.apply(lambda row: _buffer_distance(row, all_points), axis=1)
        new_number = sum(all_points["buffer_distance"] == 0)
        logger.info(f"On next pass {new_number} missing buffer distance")
        logger.debug(f"The following points do not have buffer distances defined:\n{all_points.loc[all_points['buffer_distance'] == 0]}")

    # Create the GeoDataFrame that will form the GeoJSON
    output_columns = ["id", "name"]
    output_gpd = gpd.GeoDataFrame(columns=output_columns, crs=constants.BNG)
    district_nu = 0
    for count, district in districts.iterrows():
        if str(district["D_ID"]) != "nan":
            district_nu += 1
            data = {
                "id": [district["D_ID"]],
                "name": [district["D_name"]],
            }
            logger.info(f"{district_nu}/{len(districts)} calculating boundary of {district['D_name']}")

            district_points = all_points.loc[all_points["D_ID"] == district["D_ID"]]

            # For each of the points in the district, produces a polygon to
            # represent the buffered point from the buffer distances
            # calculated above
            buffered_points = district_points.apply(lambda row: row["geometry"].buffer(row["buffer_distance"]), axis=1)

            # Unifies the polygons created from each point in the District
            # into one polygon for the District.
            district_polygon = shapely.ops.unary_union(buffered_points)
            district_polygon2 = buffered_points.unary_union()

            data_df = gpd.GeoDataFrame(data, columns=output_columns, geometry=[district_polygon])
            output_gpd = gpd.GeoDataFrame(pd.concat([output_gpd, data_df], axis=0, sort=False))

    # Convert co-ordinates back to WGS84, which uses latitude and longitude
    output_gpd = output_gpd.to_crs(epsg=constants.WGS_84)
    output_gpd.reset_index(drop=True, inplace=True)

    logger.debug(f"output gpd\n{output_gpd}")
    output_gpd[["id"]] = output_gpd[["id"]].apply(pd.to_numeric, errors="coerce")
    logger.debug(f"output gpd\n{output_gpd}")
    output_gpd.to_file("districts_buffered.geojson", driver="GeoJSON")


def _buffer_distance(point_details: pd.Series, all_points: gpd.GeoDataFrame) -> int:
    """Calculates the buffer distance of a point. Sometimes is inconclusive
    as requires the results of the buffer distance of other points, and
    in this case returns 0.

    Args:
        point_details:
        all_points: Contains all points.

    Returns:
        Distance

    """
    if point_details["buffer_distance"] == 0:
        distance = 0
        valid = True

        # Nearest points to given point
        nearest_points = point_details["nearest_points"]
        points_of_interest = all_points.loc[point_details["indexes_of_interest"]]

        for nearby_point in nearest_points:

            nearby_point_details = points_of_interest.loc[nearby_point["Index"], :]

            buffer = nearby_point_details["buffer_distance"].iloc[0]
            if buffer != 0:
                new_distance = nearby_point["Distance"] - buffer
                if distance == 0:
                    distance = new_distance
                elif new_distance < distance:
                    distance = new_distance
            else:
                if (distance == 0) or (distance > (nearby_point["Distance"] / 2)):
                    # Decide if these two points are a 'pair'.
                    # I.e. if the restricting factor is just their mutual closeness
                    nearest_to_nearby = nearby_point_details["nearest_points"].iloc[0]

                    nearest_to_nearby_indexes = [p["Index"][0] for p in nearest_to_nearby]

                    nearest_to_nearby_details = points_of_interest.loc[nearest_to_nearby_indexes, :]

                    unset_nearby = nearest_to_nearby_details.loc[nearest_to_nearby_details["buffer_distance"] == 0]

                    if not unset_nearby.empty:
                        closest_unset = [p for p in nearest_to_nearby if p["Index"][0] in unset_nearby.index][0]

                        # Closer points with defined buffers
                        closer_set = [p for p in nearest_to_nearby if p["Distance"] < closest_unset["Distance"]]

                        if closer_set:
                            buffers = nearest_to_nearby_details.loc[[p["Index"][0] for p in closer_set], :]["buffer_distance"]

                            if (not buffers.empty) and (max(buffers) > nearby_point["Distance"] / 2):
                                valid = False

                        if points_of_interest.loc[closest_unset["Index"], :]["index"].iloc[0] == point_details["index"]:
                            # The closest unset point to this near point we are considering is the original point
                            distance = nearby_point["Distance"] / 2
                        else:
                            valid = False
        if not valid:
            distance = 0
    else:
        distance = point_details["buffer_distance"]
    return distance


def _nearest_other_points(row: pd.Series, all_points: gpd.GeoDataFrame) -> list:
    """Given a row of a GeoDataFrame and a subset of a GeoDataFrame returns
    the points and corresponding distances for all points with twice
    the minimum distance from the row to the subset.

    Args:
        row: Data for specific point
        all_points:

    Returns:
        Sorted list of dictionaries containing points and distances

    """
    point = row["geometry"]

    other_data = all_points.loc[all_points["D_ID"] != row["D_ID"]]
    other_points = shapely.geometry.MultiPoint(other_data["geometry"].tolist())
    other_points2 = pygeos.constructive.extract_unique_points(other_data.geometry)

    nearest_points = shapely.ops.nearest_points(point, other_points)
    nearest_other_point = nearest_points[1]  # [0] refers to self
    distance = point.distance(nearest_other_point) * 2

    points = [{"Point": p, "Distance": point.distance(p), "Index": other_data.loc[other_data["geometry"] == p].index} for p in other_points if point.distance(p) < distance]

    points.sort(key=lambda i: i["Distance"])

    return points


def _indexes_of_interest(row: pd.Series, all_points: gpd.GeoDataFrame) -> pd.Index:
    """Provides index of all points within 3 times the distance of the
    closest point.

    (This is the maximal set of points that could affect the buffer distance
    of this point)

    Args:
        row: Row of a GeoDataFrame - requires a 'nearest_points' column
        all_points: All the points to be considered.

    Returns:
        Indexes of interest

    """

    # Indexes distance
    distance = row["nearest_points"][0]["Distance"]
    point = row["geometry"]

    indexes_of_interest = [all_points.loc[all_points["geometry"] == p].index for p in all_points["geometry"] if point.distance(p) < (distance * 3)]

    resultant_indexes = indexes_of_interest[0]
    for index in indexes_of_interest[1:]:
        resultant_indexes = resultant_indexes.union(index)

    return resultant_indexes
