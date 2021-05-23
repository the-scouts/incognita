from typing import Union

import geopandas as gpd
import shapely.geometry
from geopandas.array import GeometryArray
import geovoronoi
import geovoronoi.plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pygeos
from scipy.spatial import Voronoi

from incognita.data import scout_census
from incognita.logger import logger
from incognita.utility import constants

TYPES_SHAPELY_POLY = Union[shapely.geometry.Polygon, shapely.geometry.MultiPolygon]


def clip_voronoi_polygons(polys: pygeos.Geometry, multipoint: pygeos.Geometry) -> pygeos.Geometry:
    convex_hull = pygeos.buffer(pygeos.convex_hull(multipoint), 2)

    inner = pygeos.multipolygons(pygeos.intersection(convex_hull, polys))
    edge = pygeos.difference(convex_hull, pygeos.union_all(inner))
    if pygeos.is_empty(edge):
        return inner
    result = pygeos.multipolygons(pygeos.get_parts([inner, edge]))
    return result


def create_voronoi_pygeos(points: GeometryArray) -> None:
    mp = pygeos.multipoints(points.data)
    polys = pygeos.get_parts(pygeos.voronoi_polygons(mp))
    result = clip_voronoi_polygons(polys, mp)

    plot_mpl(result, points)


def create_voronoi_scipy(points: GeometryArray) -> None:
    vor = Voronoi(pygeos.get_coordinates(points.data))

    boundary_vertices = [vor.vertices[line] for line in vor.ridge_vertices if -1 not in line]
    polys = pygeos.get_parts(pygeos.polygonize(pygeos.linestrings(boundary_vertices)))
    result = clip_voronoi_polygons(polys, pygeos.multipoints(points.data))

    plot_mpl(result, points)


def plot_mpl(polys: pygeos.Geometry, points: GeometryArray) -> None:
    fig, ax = plt.subplots()

    coords = pygeos.get_coordinates(points.data).T
    ax.plot(coords[0, :], coords[1, :], 'ko')
    sorted_polys = sorted(pygeos.get_parts(polys), key=lambda p: tuple(pygeos.get_coordinates(pygeos.centroid(p))[0]))
    sorted_polys = sorted_polys
    for r in sorted_polys:
        x_coords, y_coords = pygeos.get_coordinates(r)[:-1].T
        ax.fill(tuple(x_coords), tuple(y_coords), alpha=0.4)


def create_voronoi_geovoronoi(points: GeometryArray) -> None:
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    uk = world.loc[world.name == "United Kingdom", "geometry"].to_crs(constants.BNG)
    gb_shape = uk.array[0][1]

    coords = np.array([p.coords[0] for p in points])

    polys, pts = geovoronoi.voronoi_regions_from_coords(coords, gb_shape, per_geom=False)
    plot_geovoronoi(polys, pts, coords, gb_shape)


def plot_geovoronoi(polys: dict[int, TYPES_SHAPELY_POLY], points: dict[int, list[int]], coords: np.ndarray, area_shape: shapely.geometry.Polygon) -> None:
    fig, ax = geovoronoi.plotting.subplot_for_map()
    geovoronoi.plotting.plot_voronoi_polys_with_points_in_area(ax, area_shape, polys, coords, points)


def create_district_boundaries(census_data: pd.DataFrame) -> None:
    """Creates a GeoJSON file for the District Boundaries of the Scout Census.

    Aims to create a circular boundary around every section of maximal size
    that doesn't overlap or leave gaps between Districts.
    """

    # Find all the District IDs and names
    districts = census_data[[scout_census.column_labels.id.DISTRICT, scout_census.column_labels.name.DISTRICT]].drop_duplicates()

    # Finds all the records with valid postcodes in the Scout Census
    all_locations = census_data.loc[census_data[scout_census.column_labels.VALID_POSTCODE], ["D_ID", "D_name", "lat", "long", "clean_postcode", "Object_ID"]].drop_duplicates(subset=["lat", "long"]).reset_index(drop=True)

    # Create points from lat / long co-ordinates above
    points = gpd.points_from_xy(all_locations["long"], all_locations["lat"])

    # create a GeoDataFrame and converts the co-ordinate reference system into
    # OS36. This is uses (x-y) coordinates in metres, rather than (long, lat)
    # coordinates, meaning that we can operate in metres from now on.
    all_points = gpd.GeoDataFrame(all_locations, geometry=points, crs=constants.WGS_84).to_crs(epsg=constants.BNG)

    create_voronoi_pygeos(all_points["geometry"].array)
    create_voronoi_scipy(all_points["geometry"].array)
    create_voronoi_geovoronoi(all_points["geometry"])
    plt.show()

    logger.info(f"Found {len(all_points.index)} different Section points")

    # Get geometries and form a square matrix from repeating the array. Keep
    # the upper triangle, so that we don't duplicate distance calculations.
    geoms = all_points["geometry"].array.data
    geoms_sq_tri = np.triu(np.tile(geoms, (geoms.size, 1)))

    # Calculate distances and re-cast to a numpy array. Create a square matrix
    # from the upper triangle and (transposed) lower triangle
    distances_tri = np.array([[(col and pygeos.distance(col, geoms[i])) for col in row] for i, row in enumerate(geoms_sq_tri)])
    distances = np.array(distances_tri) + np.array(distances_tri).T

    # Calculates all the other points within twice the distance of the
    # closest point from a neighbouring district
    all_points["nearest_points"] = all_points.apply(lambda row: _nearest_other_points(row, all_points, distances), axis=1)
    triple_distance = all_points["nearest_points"].apply(lambda r: r[0]["Distance"]) * 3

    td_sq = pd.DataFrame(np.tile(triple_distance.to_numpy()[:, np.newaxis], (1, triple_distance.size)))
    valid_distances = pd.DataFrame(distances) < td_sq
    vdf = (valid_distances * valid_distances.columns)[valid_distances].fillna(-1).astype(valid_distances.columns.dtype)

    # Get index of all points within 3 times the distance of the closest point.
    # (This is the maximal set of points that could affect the buffer distance
    # of this point)
    all_points["indexes_of_interest"] = vdf.apply(lambda r: pd.Index(i for i in r if i > -1), axis=1)

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
        logger.debug(f"The following points do not have buffer distances defined:\n{all_points.index[all_points['buffer_distance'] == 0]}")

    # Create the GeoDataFrame that will form the GeoJSON
    output_data = []
    district_nu = 0
    for district in districts.itertuples():
        if pd.isna(district.D_ID):
            continue

        district_nu += 1
        logger.info(f"{district_nu}/{len(districts)} calculating boundary of {district.D_name}")

        # For each of the points in the district, produces a polygon to
        # represent the buffered point from the buffer distances
        # calculated above. Then Unify the polygons created from each
        # point in the District into one polygon for the District.
        district_points = all_points.loc[all_points["D_ID"] == district.D_ID]
        district_polygon = gpd.GeoSeries([row.geometry.buffer(row.buffer_distance) for row in district_points.itertuples()]).geometry.array.unary_union()

        data = {
            "id": district.D_ID,
            "name": district.D_name,
            "geometry": district_polygon,
        }
        output_data.append(data)

    # Convert co-ordinates back to WGS84, which uses latitude and longitude
    # output_gpd = pd.concat(output_frames)
    output_gpd = gpd.GeoDataFrame(output_data, crs=constants.BNG).to_crs(epsg=constants.WGS_84)

    output_gpd["id"] = pd.to_numeric(output_gpd["id"], errors="coerce")
    logger.debug(f"output gpd\n{output_gpd}")
    output_gpd.to_file("districts_buffered-2.geojson", driver="GeoJSON")


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
    if point_details["buffer_distance"] != 0:
        return point_details["buffer_distance"]

    distance = 0

    # Nearest points to given point
    nearest_points = point_details["nearest_points"]
    points_of_interest = all_points.loc[point_details["indexes_of_interest"]]

    for nearby_point in nearest_points:
        nearby_point_details = points_of_interest.loc[nearby_point["Index"], ["buffer_distance", "nearest_points"]]

        buffer = nearby_point_details["buffer_distance"]
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
                nearest_to_nearby = nearby_point_details["nearest_points"]
                nearest_to_nearby_indexes = [p["Index"] for p in nearest_to_nearby]
                nearest_to_nearby_details = all_points.loc[nearest_to_nearby_indexes, :]
                unset_nearby = nearest_to_nearby_details.loc[nearest_to_nearby_details["buffer_distance"] == 0]

                if not unset_nearby.empty:
                    closest_buffer_unset = next(p for p in nearest_to_nearby if p["Index"] in unset_nearby.index)

                    # Closer points with defined buffers
                    closer_buffer_set = [p for p in nearest_to_nearby if p["Distance"] < closest_buffer_unset["Distance"]]

                    if closer_buffer_set:
                        buffers = nearest_to_nearby_details.loc[[p["Index"] for p in closer_buffer_set], "buffer_distance"]

                        if (not buffers.empty) and (max(buffers) > nearby_point["Distance"] / 2):
                            return 0  # not valid

                    if points_of_interest.loc[closest_buffer_unset["Index"]].name == point_details.name:
                        # The closest unset point to this near point we are considering is the original point
                        distance = nearby_point["Distance"] / 2
                    else:
                        return 0  # not valid
    return distance


def _nearest_other_points(row: pd.Series, all_points: gpd.GeoDataFrame, distances: np.ndarray) -> list[dict[str, object]]:
    """Given a row of a GeoDataFrame and a subset of a GeoDataFrame returns
    the points and corresponding distances for all points with twice
    the minimum distance from the row to the subset.

    Args:
        row: Data for specific point
        all_points:

    Returns:
        Sorted list of dictionaries containing points and distances

    """
    # # TODO use pygeos 0.10 nearest(*) func (not released 2021-05-17)

    other_indicies = all_points.index[all_points["D_ID"] != row["D_ID"]]
    distance_row = distances[row.name]
    distance = distance_row[other_indicies].min() * 2

    points = [{"Point": all_points["geometry"][i], "Distance": distance_row[i], "Index": i} for i in other_indicies if distance_row[i] < distance]

    points.sort(key=lambda i: i["Distance"])

    return points
